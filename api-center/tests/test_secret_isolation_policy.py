from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


api_ticket = load_module("api_ticket_secret_policy", ROOT / "api_ticket.py")


class SecretIsolationPolicyTests(unittest.TestCase):
    def connector(self, connector_id: str, env_name: str | None) -> dict:
        connector = {
            "id": connector_id,
            "enabled": True,
            "endpoint": f"/data/{connector_id}",
            "method": "GET",
            "path_parameters": {},
            "input_query_strings": [],
            "response_contract": {
                "success_when_data_present": True,
                "any_data_paths": [],
            },
        }
        if env_name:
            connector["secret_header"] = {
                "name": "X-Api-Key",
                "env": env_name,
            }
        return connector

    def packet(self, connector_ids: list[str]) -> dict:
        return {
            "task_id": "secret-isolation-test",
            "objective": "verify independent API credentials",
            "data_policy": {
                "classification": "public",
                "contains_personal_data": False,
            },
            "requests": [
                {
                    "request_id": f"request-{index}",
                    "connector_id": connector_id,
                    "parameters": {},
                }
                for index, connector_id in enumerate(connector_ids, 1)
            ],
            "acceptance": {
                "require_all": True,
                "minimum_successful_requests": len(connector_ids),
            },
        }

    def write_catalog(self, root: Path, connectors: list[dict]) -> None:
        rows = []
        connectors_dir = root / "connectors"
        connectors_dir.mkdir(parents=True)
        for connector in connectors:
            filename = f"{connector['id']}.connector.json"
            (connectors_dir / filename).write_text(
                json.dumps(connector), encoding="utf-8"
            )
            rows.append({
                "id": connector["id"],
                "file": f"connectors/{filename}",
            })
        (root / "connector-manifest.json").write_text(
            json.dumps({"connectors": rows}), encoding="utf-8"
        )

    def test_allows_multiple_endpoints_sharing_one_api_key(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_catalog(
                root,
                [
                    self.connector("news-everything", "NEWSAPI_API_KEY"),
                    self.connector("news-headlines", "NEWSAPI_API_KEY"),
                ],
            )
            plan = api_ticket._validate_and_plan(
                self.packet(["news-everything", "news-headlines"]), root
            )
            self.assertEqual(
                plan["required_secret_environment_variable"], "NEWSAPI_API_KEY"
            )
            self.assertEqual(
                plan["required_secret_environment_variables"], ["NEWSAPI_API_KEY"]
            )
            self.assertEqual(
                plan["secret_isolation_policy"], "one-keyed-upstream-per-ticket"
            )

    def test_rejects_two_keyed_api_services_in_one_ticket(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_catalog(
                root,
                [
                    self.connector("amap-geocode", "AMAP_API_KEY"),
                    self.connector("baidu-geocode", "BAIDU_MAP_API_KEY"),
                ],
            )
            with self.assertRaisesRegex(
                ValueError, "only one keyed upstream API service"
            ):
                api_ticket._validate_and_plan(
                    self.packet(["amap-geocode", "baidu-geocode"]), root
                )

    def test_allows_keyless_and_one_keyed_service_together(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_catalog(
                root,
                [
                    self.connector("open-meteo", None),
                    self.connector("amap-weather", "AMAP_API_KEY"),
                ],
            )
            plan = api_ticket._validate_and_plan(
                self.packet(["open-meteo", "amap-weather"]), root
            )
            self.assertEqual(
                plan["required_secret_environment_variables"], ["AMAP_API_KEY"]
            )


if __name__ == "__main__":
    unittest.main()
