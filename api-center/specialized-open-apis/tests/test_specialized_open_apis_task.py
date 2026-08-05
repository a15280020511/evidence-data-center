from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "specialized_open_apis_task", HERE / "specialized_open_apis_task.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SpecializedOpenApisTests(unittest.TestCase):
    def test_catalog_schema_operation_parity(self) -> None:
        catalog = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
        schema = json.loads((HERE / "ticket.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        provider = catalog["providers"][0]
        self.assertEqual(
            {row["operation_id"] for row in provider["operations"]},
            set(schema["properties"]["operation"]["enum"]),
        )
        self.assertEqual(provider["limits"]["requests_per_ticket_max"], 1)
        self.assertIs(provider["limits"]["arbitrary_query_languages_allowed"], False)

    def test_nhm_request(self) -> None:
        url, method, params, body, kind, _ = MODULE.build_request(
            "nhm-dataset-search", {"query": "fossil insects", "limit": 10}
        )
        self.assertEqual(url, "https://data.nhm.ac.uk/api/3/action/package_search")
        self.assertEqual(method, "GET")
        self.assertIsNone(body)
        self.assertEqual(kind, "nhm-ckan")
        self.assertEqual(dict(params)["rows"], "10")

    def test_optimade_request_and_filter_safety(self) -> None:
        url, method, params, body, kind, _ = MODULE.build_request(
            "optimade-structures",
            {"provider": "mc3d-pbe-v1", "elements": ["Si", "O"], "limit": 5},
        )
        self.assertEqual(
            url,
            "https://optimade.materialscloud.org/main/mc3d-pbe-v1/v1/structures",
        )
        self.assertEqual(method, "GET")
        self.assertIsNone(body)
        self.assertEqual(kind, "optimade")
        values = dict(params)
        self.assertEqual(values["page_limit"], "5")
        self.assertEqual(values["filter"], 'elements HAS ALL "Si","O"')
        with self.assertRaises(ValueError):
            MODULE.build_request(
                "optimade-structures",
                {"provider": "other", "elements": ["Si"], "limit": 5},
            )
        with self.assertRaises(ValueError):
            MODULE.build_request(
                "optimade-structures",
                {"provider": "mc3d-pbe-v1", "elements": ["Si OR true"], "limit": 5},
            )

    def test_gov_uk_request(self) -> None:
        url, _, params, _, kind, _ = MODULE.build_request(
            "gov-uk-search", {"query": "artificial intelligence regulation", "limit": 15}
        )
        self.assertEqual(url, "https://www.gov.uk/api/search.json")
        values = dict(params)
        self.assertEqual(values["count"], "15")
        self.assertEqual(values["start"], "0")
        self.assertEqual(kind, "gov-uk-search")

    def test_rijksmuseum_request(self) -> None:
        url, _, params, _, kind, _ = MODULE.build_request(
            "rijksmuseum-collection-search",
            {"field": "creator", "query": "Rembrandt", "image_available": True},
        )
        self.assertEqual(url, "https://data.rijksmuseum.nl/search/collection")
        values = dict(params)
        self.assertEqual(values["creator"], "Rembrandt")
        self.assertEqual(values["imageAvailable"], "true")
        self.assertEqual(kind, "rijksmuseum")

    def test_bgs_request(self) -> None:
        url, _, params, _, kind, _ = MODULE.build_request("bgs-collections", {})
        self.assertEqual(url, "https://ogcapi.bgs.ac.uk/collections")
        self.assertEqual(dict(params)["f"], "json")
        self.assertEqual(kind, "bgs-collections")

    def test_response_contracts(self) -> None:
        self.assertEqual(
            MODULE.validate_response(
                "nhm-ckan", {"success": True, "result": {"results": [{}]}}
            ),
            1,
        )
        self.assertEqual(
            MODULE.validate_response("optimade", {"data": [{"id": "x"}], "meta": {}}),
            1,
        )
        self.assertEqual(MODULE.validate_response("gov-uk-search", {"results": []}), 0)
        self.assertEqual(
            MODULE.validate_response(
                "rijksmuseum", {"orderedItems": [{"id": "x"}], "partOf": {}}
            ),
            1,
        )
        self.assertEqual(MODULE.validate_response("bgs-collections", {"collections": []}), 0)

    def test_local_operations_and_matrix(self) -> None:
        self.assertEqual(
            MODULE.build_request("catalog-capabilities", {}),
            (None, "LOCAL", [], None, "catalog", "application/json"),
        )
        self.assertEqual(
            MODULE.build_request("source-access-matrix", {}),
            (None, "LOCAL", [], None, "matrix", "application/json"),
        )
        matrix = json.loads((HERE / "source-access-matrix.json").read_text(encoding="utf-8"))
        pending = {row["source_id"] for row in matrix["production_pending_live_acceptance"]}
        self.assertEqual(
            pending,
            {
                "nhm-data-portal",
                "materials-cloud-optimade",
                "gov-uk-search-api",
                "rijksmuseum-search",
                "bgs-opengeoscience",
            },
        )
        self.assertIs(matrix["governance"]["arbitrary_optimade_filters_allowed"], False)


if __name__ == "__main__":
    unittest.main()
