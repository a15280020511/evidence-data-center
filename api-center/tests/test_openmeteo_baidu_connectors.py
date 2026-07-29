from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

API_CENTER = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "api_center_new_connector_test", API_CENTER / "build_config.py"
)
assert SPEC and SPEC.loader
build_config = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = build_config
SPEC.loader.exec_module(build_config)


class OpenMeteoAndBaiduConnectorTests(unittest.TestCase):
    def test_openmeteo_is_enabled_secretless_and_bounded(self) -> None:
        config, rows, env_names = build_config.build()
        row_map = {row["id"]: row for row in rows}
        row = row_map["openmeteo-forecast"]
        self.assertTrue(row["enabled"])
        self.assertEqual(row["backend_host"], "https://api.open-meteo.com")
        self.assertIsNone(row["secret_environment_variable"])
        self.assertTrue(row["backend_rate_limit"])
        self.assertNotIn("OPENMETEO_API_KEY", env_names)
        connector = build_config.load_json(API_CENTER / row["file"])
        self.assertTrue(connector["response_contract"]["success_when_data_present"])
        self.assertEqual(
            set(connector["response_contract"]["any_data_paths"]),
            {"current", "hourly", "daily"},
        )

    def test_baidu_connectors_share_backend_only_secret(self) -> None:
        config, rows, env_names = build_config.build()
        row_map = {row["id"]: row for row in rows}
        expected = {
            "baidu-geocode",
            "baidu-place-search",
            "baidu-direction-driving",
        }
        self.assertTrue(expected.issubset(row_map))
        self.assertIn("BAIDU_MAP_API_KEY", env_names)
        for connector_id in expected:
            row = row_map[connector_id]
            self.assertTrue(row["enabled"])
            self.assertEqual(row["backend_host"], "https://api.map.baidu.com")
            self.assertEqual(row["secret_environment_variable"], "BAIDU_MAP_API_KEY")
            self.assertEqual(row["secret_injection"], "query")
            connector = build_config.load_json(API_CENTER / row["file"])
            self.assertNotIn("ak", connector["input_query_strings"])
            self.assertEqual(connector["secret_query"]["name"], "ak")
            self.assertEqual(connector["response_contract"]["success_values"], [0])
        endpoint_paths = {item["endpoint"] for item in config["endpoints"]}
        self.assertIn("/data/baidu/geocode", endpoint_paths)
        self.assertIn("/data/baidu/place/search", endpoint_paths)
        self.assertIn("/data/baidu/direction/driving", endpoint_paths)


if __name__ == "__main__":
    unittest.main()
