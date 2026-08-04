from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "strategic_intelligence_task", HERE / "strategic_intelligence_task.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class StrategicIntelligenceTests(unittest.TestCase):
    def test_catalog_and_schema_are_valid(self) -> None:
        catalog = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
        schema = json.loads((HERE / "ticket.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        self.assertIs(catalog["secret_values_exposed"], False)
        provider = catalog["providers"][0]
        operation_ids = {item["operation_id"] for item in provider["operations"]}
        self.assertEqual(operation_ids, set(schema["properties"]["operation"]["enum"]))
        self.assertEqual(provider["limits"]["requests_per_ticket_max"], 1)
        self.assertIs(provider["limits"]["redirects_allowed"], False)

    def test_openfema_request_is_fixed_and_bounded(self) -> None:
        url, query, kind = MODULE.build_request(
            "openfema-disaster-declarations",
            {"state": "CA", "year_from": 2020, "year_to": 2026, "top": 25},
        )
        self.assertEqual(
            url,
            "https://www.fema.gov/api/open/v1/DisasterDeclarationsSummaries",
        )
        self.assertEqual(kind, "openfema")
        values = dict(query)
        self.assertEqual(values["$top"], "25")
        self.assertIn("state eq 'CA'", values["$filter"])

    def test_ripestat_resources_are_structurally_validated(self) -> None:
        url, query, kind = MODULE.build_request(
            "ripestat-network-info", {"resource": "8.8.8.8"}
        )
        self.assertEqual(url, "https://stat.ripe.net/data/network-info/data.json")
        self.assertEqual(query, [("resource", "8.8.8.8")])
        self.assertEqual(kind, "ripestat")
        with self.assertRaises(ValueError):
            MODULE.build_request("ripestat-network-info", {"resource": "example.com"})
        with self.assertRaises(ValueError):
            MODULE.build_request(
                "ripestat-prefix-overview", {"resource": "8.8.8.8;rm"}
            )

    def test_peeringdb_rejects_arbitrary_object_types(self) -> None:
        url, query, kind = MODULE.build_request(
            "peeringdb-search", {"object_type": "net", "name": "Google", "limit": 10}
        )
        self.assertEqual(url, "https://www.peeringdb.com/api/net")
        self.assertEqual(dict(query)["limit"], "10")
        self.assertEqual(kind, "peeringdb")
        with self.assertRaises(ValueError):
            MODULE.build_request(
                "peeringdb-search", {"object_type": "../../admin", "name": "x"}
            )

    def test_local_operations_make_no_upstream_request(self) -> None:
        self.assertEqual(
            MODULE.build_request("catalog-capabilities", {}),
            (None, [], "catalog"),
        )
        self.assertEqual(
            MODULE.build_request("source-access-matrix", {}),
            (None, [], "source-matrix"),
        )

    def test_response_contracts(self) -> None:
        self.assertIsNone(
            MODULE.validate_response(
                "ripestat", {"status": "ok", "data": {"asns": [15169]}}
            )
        )
        self.assertEqual(MODULE.validate_response("peeringdb", {"data": [{"id": 1}]}), 1)
        self.assertEqual(
            MODULE.validate_response(
                "openfema", {"DisasterDeclarationsSummaries": []}
            ),
            0,
        )
        self.assertEqual(
            MODULE.validate_response("mitre-index", {"collections": [{"id": "x"}]}),
            1,
        )
        with self.assertRaises(RuntimeError):
            MODULE.validate_response("peeringdb", {"data": {}})

    def test_source_matrix_does_not_hide_conditions(self) -> None:
        matrix = json.loads((HERE / "source-access-matrix.json").read_text(encoding="utf-8"))
        conditions = {
            item["source_id"]: item["condition"]
            for item in matrix["conditional_sources"]
        }
        self.assertEqual(conditions["ucdp"], "free_token_required")
        self.assertEqual(
            conditions["global-fishing-watch"],
            "token_required_and_noncommercial_only",
        )
        self.assertEqual(
            conditions["opensanctions"],
            "noncommercial_or_separate_license",
        )
        self.assertIs(matrix["governance"]["write_operations_allowed"], False)


if __name__ == "__main__":
    unittest.main()
