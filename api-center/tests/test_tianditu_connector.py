from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


api_ticket = load_module("api_ticket_tianditu_tests", ROOT / "api_ticket.py")
api_task = load_module("api_task_tianditu_tests", ROOT / "api_task.py")
build_config = load_module("build_config_tianditu_tests", ROOT / "build_config.py")


def packet(parameters: dict):
    return {
        "task_id": "connector-test-tianditu-place-search",
        "objective": "validate Tianditu connector",
        "data_policy": {"classification": "public", "contains_personal_data": False},
        "requests": [{"request_id": "request-1", "connector_id": "tianditu-place-search", "parameters": parameters}],
        "acceptance": {"require_all": True, "minimum_successful_requests": 1},
    }


class TiandituConnectorTests(unittest.TestCase):
    def connector(self):
        return json.loads((ROOT / "connectors/tianditu-place-search.connector.json").read_text(encoding="utf-8"))

    def test_compiler_registers_route_and_secret_boundary(self):
        config, rows, env_names = build_config.build()
        row_map = {row["id"]: row for row in rows}
        self.assertEqual(
            len(config["endpoints"]),
            sum(bool(row["enabled"]) for row in rows),
        )
        expected_env_names = sorted({
            str(row["secret_environment_variable"])
            for row in rows
            if row.get("enabled") and row.get("secret_environment_variable")
        })
        self.assertEqual(env_names, expected_env_names)
        self.assertEqual(row_map["tianditu-place-search"]["secret_environment_variable"], "TIANDITU_API_KEY")
        self.assertNotIn("gdelt-doc-articles", row_map)
        self.assertTrue(
            {"baidu-geocode", "baidu-place-search", "baidu-direction-driving"}.issubset(row_map)
        )

    def test_ticket_forwards_only_poststr_and_type(self):
        post_str = '{"keyWord":"福州宝龙城市广场","level":12,"mapBound":"119.20,25.95,119.45,26.20","queryType":1,"start":0,"count":10}'
        plan = api_ticket._validate_and_plan(packet({"postStr": post_str, "type": "query"}), ROOT)
        row = plan["requests"][0]
        self.assertEqual(row["parameters"], {"postStr": post_str, "type": "query"})
        self.assertEqual(plan["required_secret_environment_variables"], ["TIANDITU_API_KEY"])
        connector = self.connector()
        self.assertNotIn("tk", connector["input_query_strings"])
        self.assertEqual(connector["secret_query"], {"name": "tk", "env": "TIANDITU_API_KEY"})

    def test_response_contract_accepts_documented_shape(self):
        connector = self.connector()
        payload = {
            "resultType": 1,
            "pois": [{"name": "福州宝龙城市广场", "lonlat": "119.292,26.063"}],
            "status": {"infocode": 1000, "cndesc": "OK"},
        }
        self.assertTrue(
            api_task.evaluate_response_contract(
                payload, connector["response_contract"], allow_empty=False
            )["success"]
        )


if __name__ == "__main__":
    unittest.main()
