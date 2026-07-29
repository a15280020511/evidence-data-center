from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

API_CENTER = Path(__file__).resolve().parents[1]


def load_module():
    spec = importlib.util.spec_from_file_location(
        "api_center_amap_contract_test", API_CENTER / "build_config.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


build_config = load_module()


class AMapConnectorContractTests(unittest.TestCase):
    def test_all_expected_amap_routes_are_enabled(self) -> None:
        config, rows, env_names = build_config.build()
        amap_rows = [row for row in rows if row["id"].startswith("amap-")]
        amap_endpoints = [
            endpoint for endpoint in config["endpoints"]
            if endpoint["endpoint"].startswith("/data/amap/")
        ]
        self.assertEqual(len(amap_rows), 7)
        self.assertEqual(len(amap_endpoints), 7)
        self.assertTrue(all(row["enabled"] for row in amap_rows))
        self.assertTrue(all(row["method"] == "GET" for row in amap_rows))
        self.assertTrue(all(row["backend_host"] == "https://restapi.amap.com" for row in amap_rows))
        self.assertTrue(all(row["secret_environment_variable"] == "AMAP_API_KEY" for row in amap_rows))
        self.assertTrue(all(row["secret_injection"] == "query" for row in amap_rows))
        self.assertIn("AMAP_API_KEY", env_names)

    def test_amap_key_is_backend_only(self) -> None:
        config, _, _ = build_config.build()
        amap_endpoints = [
            endpoint for endpoint in config["endpoints"]
            if endpoint["endpoint"].startswith("/data/amap/")
        ]
        self.assertEqual(len(amap_endpoints), 7)
        for endpoint in amap_endpoints:
            self.assertNotIn("key", endpoint.get("input_query_strings", []))
            modifier = endpoint["backend"][0]["extra_config"]["modifier/martian"]
            query = modifier["querystring.Modifier"]
            self.assertEqual(query["name"], "key")
            self.assertEqual(query["value"], "__API_CENTER_ENV_AMAP_API_KEY__")


if __name__ == "__main__":
    unittest.main()
