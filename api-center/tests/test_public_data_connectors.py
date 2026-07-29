from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

API_CENTER = Path(__file__).resolve().parents[1]


def load_module():
    spec = importlib.util.spec_from_file_location(
        "api_center_public_data_contract_test", API_CENTER / "build_config.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


build_config = load_module()


class PublicDataConnectorContractTests(unittest.TestCase):
    def test_wikidata_connector_is_enabled_secretless_and_bounded(self) -> None:
        config, rows, env_names = build_config.build()
        row_map = {row["id"]: row for row in rows}
        endpoint_map = {row["endpoint"]: row for row in config["endpoints"]}
        row = row_map["wikidata-entity-search"]
        self.assertTrue(row["enabled"])
        self.assertEqual(row["method"], "GET")
        self.assertEqual(row["backend_host"], "https://www.wikidata.org")
        self.assertIsNone(row["secret_environment_variable"])
        self.assertTrue(row["backend_rate_limit"])
        self.assertIn("/data/wikidata/entity/search", endpoint_map)
        self.assertNotIn("WIKIDATA_TOKEN", env_names)

        connector = build_config.load_json(API_CENTER / row["file"])
        contract = connector["response_contract"]
        self.assertEqual(contract["status_path"], "success")
        self.assertEqual(contract["success_values"], [1])
        self.assertEqual(contract["any_data_paths"], ["search"])
        exposed = {str(item).casefold() for item in connector["input_query_strings"]}
        self.assertTrue({"url", "token", "api_key", "authorization"}.isdisjoint(exposed))
        self.assertIn("action", connector["input_query_strings"])
        self.assertIn("format", connector["input_query_strings"])
        self.assertEqual(connector["backend"]["url_pattern"], "/w/api.php")

    def test_replaced_connectors_are_absent(self) -> None:
        _, rows, _ = build_config.build()
        installed = {row["id"] for row in rows}
        self.assertTrue({
            "gdelt-doc-articles",
            "nasa-black-marble-granules",
            "worldpop-population-stats",
        }.isdisjoint(installed))


if __name__ == "__main__":
    unittest.main()
