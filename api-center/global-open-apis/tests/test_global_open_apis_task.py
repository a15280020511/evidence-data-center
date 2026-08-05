from __future__ import annotations

import importlib.util
import json
import os
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "global_open_apis_task", HERE / "global_open_apis_task.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class GlobalOpenApisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.old_key = os.environ.get("GOOGLE_PUBLIC_INTELLIGENCE_API_KEY")
        os.environ["GOOGLE_PUBLIC_INTELLIGENCE_API_KEY"] = "A" * 32

    def tearDown(self) -> None:
        if self.old_key is None:
            os.environ.pop("GOOGLE_PUBLIC_INTELLIGENCE_API_KEY", None)
        else:
            os.environ["GOOGLE_PUBLIC_INTELLIGENCE_API_KEY"] = self.old_key

    def test_catalog_schema_and_operation_parity(self) -> None:
        catalog = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
        schema = json.loads((HERE / "ticket.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        provider = catalog["providers"][0]
        catalog_ops = {row["operation_id"] for row in provider["operations"]}
        schema_ops = set(schema["properties"]["operation"]["enum"])
        self.assertEqual(catalog_ops, schema_ops)
        self.assertEqual(provider["limits"]["requests_per_ticket_max"], 1)
        self.assertIs(provider["limits"]["redirects_allowed"], False)
        self.assertIs(catalog["secret_values_exposed"], False)

    def test_google_requests_are_fixed_and_keyed(self) -> None:
        url, method, params, body, kind, credentials = MODULE.build_request(
            "google-knowledge-entities",
            {"query": "Fuzhou", "limit": 5, "languages": "zh,en", "entity_type": "Place"},
        )
        self.assertEqual(url, "https://kgsearch.googleapis.com/v1/entities:search")
        self.assertEqual(method, "GET")
        self.assertIsNone(body)
        self.assertEqual(kind, "google-kg")
        self.assertEqual(credentials, ["GOOGLE_PUBLIC_INTELLIGENCE_API_KEY"])
        self.assertIn(("types", "Place"), params)
        self.assertIn(("key", "A" * 32), params)

        url, method, params, _, kind, _ = MODULE.build_request("google-civic-elections", {})
        self.assertEqual(url, "https://www.googleapis.com/civicinfo/v2/elections")
        self.assertEqual(method, "GET")
        self.assertEqual(kind, "google-civic-elections")
        self.assertIn(("key", "A" * 32), params)

    def test_open_book_uses_current_rest_not_oai(self) -> None:
        url, method, params, body, kind, credentials = MODULE.build_request(
            "open-book-search", {"source_id": "oapen", "query": "economic development"}
        )
        self.assertEqual(url, "https://library.oapen.org/rest/search")
        self.assertEqual(method, "GET")
        self.assertIsNone(body)
        self.assertEqual(kind, "open-book-oapen")
        self.assertEqual(credentials, [])
        self.assertIn(("expand", "metadata"), params)

        url, _, _, _, kind, _ = MODULE.build_request(
            "open-book-search", {"source_id": "doab", "query": "public policy"}
        )
        self.assertEqual(url, "https://directory.doabooks.org/rest/search")
        self.assertEqual(kind, "open-book-doab")

    def test_bounded_global_sources(self) -> None:
        url, _, params, _, kind, _ = MODULE.build_request(
            "gbif-occurrence-search",
            {"taxon_key": 212, "country": "CN", "year": 2025, "limit": 10},
        )
        self.assertEqual(url, "https://api.gbif.org/v1/occurrence/search")
        self.assertEqual(kind, "gbif-results")
        values = dict(params)
        self.assertEqual(values["taxon_key"], "212")
        self.assertEqual(values["country"], "CN")
        self.assertEqual(values["limit"], "10")

        url, _, params, _, kind, _ = MODULE.build_request(
            "wellcome-works-search", {"query": "influenza", "limit": 25}
        )
        self.assertEqual(url, "https://api.wellcomecollection.org/catalogue/v2/works")
        self.assertEqual(kind, "wellcome-results")
        self.assertEqual(dict(params)["pageSize"], "25")

        url, method, params, body, kind, _ = MODULE.build_request(
            "data-europa-dataset-search", {"query": "energy prices", "limit": 20}
        )
        self.assertEqual(url, "https://data.europa.eu/api/hub/search/search")
        self.assertEqual(method, "POST")
        self.assertEqual(params, [])
        self.assertEqual(body["filters"], ["dataset"])
        self.assertEqual(kind, "data-europa")

    def test_query_sanitization_and_local_operations(self) -> None:
        self.assertEqual(MODULE.safe_plain_query('energy AND price:*'), "energy price")
        self.assertEqual(
            MODULE.build_request("catalog-capabilities", {}),
            (None, "LOCAL", [], None, "catalog", []),
        )
        self.assertEqual(
            MODULE.build_request("source-access-matrix", {}),
            (None, "LOCAL", [], None, "matrix", []),
        )
        with self.assertRaises(ValueError):
            MODULE.build_request("google-civic-elections", {"query": "x"})
        with self.assertRaises(ValueError):
            MODULE.build_request("open-book-search", {"source_id": "other", "query": "x"})

    def test_response_contracts(self) -> None:
        self.assertEqual(MODULE.validate_response("google-kg", {"itemListElement": []}), 0)
        self.assertEqual(MODULE.validate_response("google-civic-elections", {"elections": [{}]}), 1)
        self.assertEqual(MODULE.validate_response("google-civic-divisions", {"results": [{}]}), 1)
        self.assertEqual(MODULE.validate_response("gbif-results", {"results": [{}, {}]}), 2)
        self.assertEqual(MODULE.validate_response("wellcome-results", {"results": [{}]}), 1)
        self.assertEqual(MODULE.validate_response("open-book-oapen", []), 0)
        self.assertIsNone(MODULE.validate_response("data-europa", {"total": 0}))
        with self.assertRaises(RuntimeError):
            MODULE.validate_response("gbif-results", {"results": {}})

    def test_matrix_exposes_production_enablement_and_key_conditions(self) -> None:
        matrix = json.loads((HERE / "source-access-matrix.json").read_text(encoding="utf-8"))
        production = {row["source_id"] for row in matrix["production_sources"]}
        self.assertTrue(
            {"oapen-rest", "doab-rest", "gbif", "wellcome-catalogue", "data-europa-eu"}.issubset(production)
        )
        blocked = {
            row["source_id"]: row["required_action"]
            for row in matrix["implemented_pending_external_enablement"]
        }
        self.assertIn("kgsearch.googleapis.com", blocked["google-knowledge-graph-search"])
        self.assertIn("civicinfo.googleapis.com", blocked["google-civic-information"])
        key_candidates = {
            row["source_id"]: row["credential_mode"]
            for row in matrix["free_key_or_registration_candidates"]
        }
        self.assertEqual(key_candidates["nara-catalog"], "free API key required")
        self.assertIs(matrix["governance"]["address_level_voter_queries_allowed"], False)


if __name__ == "__main__":
    unittest.main()
