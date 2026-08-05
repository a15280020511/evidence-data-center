from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("institutional_open_knowledge_task", HERE / "institutional_open_knowledge_task.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class InstitutionalOpenKnowledgeTests(unittest.TestCase):
    def test_catalog_schema_and_matrix(self) -> None:
        catalog = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
        schema = json.loads((HERE / "ticket.schema.json").read_text(encoding="utf-8"))
        matrix = json.loads((HERE / "source-access-matrix.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        provider = catalog["providers"][0]
        self.assertEqual({row["operation_id"] for row in provider["operations"]}, set(schema["properties"]["operation"]["enum"]))
        self.assertEqual(matrix["active_source_count"], len(matrix["sources"]))
        self.assertIs(provider["limits"]["resumption_token_following_allowed"], False)
        self.assertIs(provider["limits"]["redirects_allowed"], False)
        self.assertIs(matrix["governance"]["restricted_file_retrieval_allowed"], False)
        self.assertIs(catalog["secret_values_exposed"], False)

    def test_fixed_contracts(self) -> None:
        url, method, _, query, source = MODULE.build_request("fraser-oai-identify", {})
        self.assertEqual(url, "https://fraser.stlouisfed.org/oai")
        self.assertEqual(method, "GET")
        self.assertEqual(query, [("verb", "Identify")])
        self.assertEqual(source, "fraser-oai")

        url, _, _, query, source = MODULE.build_request("osdr-dataset-metadata", {"accession":"OSD-48"})
        self.assertEqual(url, "https://visualization.osdr.nasa.gov/biodata/api/v2/dataset/OSD-48/")
        self.assertEqual(query, [("format", "json")])
        self.assertEqual(source, "nasa-osdr-biodata")

        url, _, _, query, source = MODULE.build_request("japan-indicator-search", {"query":"total population"})
        self.assertEqual(url, "https://dashboard.e-stat.go.jp/api/1.0/Json/getIndicatorInfo")
        self.assertIn(("Lang", "EN"), query)
        self.assertIn(("SearchIndicatorWord", "total population"), query)
        self.assertEqual(source, "japan-statistics-dashboard")

    def test_bounds_and_security(self) -> None:
        with self.assertRaises(ValueError):
            MODULE.build_request("osdr-dataset-metadata", {"accession":"../../etc"})
        with self.assertRaises(ValueError):
            MODULE.build_request("japan-indicator-data", {"indicator_code":"abc","cycle":3,"regional_rank":2})
        with self.assertRaises(ValueError):
            MODULE.build_request("fraser-oai-identify", {"url":"https://example.com"})
        with self.assertRaises(ValueError):
            MODULE.build_request("japan-indicator-search", {"query":"\u0000bad"})

    def test_kegg_is_not_active(self) -> None:
        matrix = json.loads((HERE / "source-access-matrix.json").read_text(encoding="utf-8"))
        active = {row["source_id"] for row in matrix["sources"]}
        conditional = {row["source_id"] for row in matrix["conditional_candidates"]}
        self.assertNotIn("kegg-rest", active)
        self.assertIn("kegg-rest", conditional)


if __name__ == "__main__":
    unittest.main()
