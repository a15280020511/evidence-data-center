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


api_ticket = load_module("api_ticket_newsapi_tests", ROOT / "api_ticket.py")
api_task = load_module("api_task_newsapi_tests", ROOT / "api_task.py")
build_config = load_module("build_config_newsapi_tests", ROOT / "build_config.py")


def packet(connector_id: str, parameters: dict):
    return {
        "task_id": f"connector-test-{connector_id}",
        "objective": "validate NewsAPI public news metadata connector",
        "data_policy": {
            "classification": "public",
            "contains_personal_data": False,
            "notes": "public article metadata only",
        },
        "requests": [
            {
                "request_id": "request-1",
                "connector_id": connector_id,
                "parameters": parameters,
                "allow_empty": False,
            }
        ],
        "acceptance": {
            "require_all": True,
            "minimum_successful_requests": 1,
            "timeout_seconds": 20,
            "max_attempts": 1,
            "max_response_bytes_per_request": 500000,
        },
    }


class NewsApiConnectorTests(unittest.TestCase):
    def connector(self, name: str):
        return json.loads(
            (ROOT / "connectors" / f"{name}.connector.json").read_text(
                encoding="utf-8"
            )
        )

    def test_compiler_registers_all_newsapi_routes_with_one_backend_credential(self):
        config, rows, env_names = build_config.build()
        row_map = {row["id"]: row for row in rows}
        for connector_id in (
            "newsapi-everything",
            "newsapi-top-headlines",
            "newsapi-sources",
        ):
            self.assertTrue(row_map[connector_id]["enabled"])
            self.assertEqual(
                row_map[connector_id]["secret_environment_variable"],
                "NEWSAPI_API_KEY",
            )
            self.assertEqual(row_map[connector_id]["secret_injection"], "header")
        self.assertIn("NEWSAPI_API_KEY", env_names)
        self.assertEqual(
            len(config["endpoints"]),
            sum(bool(row["enabled"]) for row in rows),
        )

    def test_everything_ticket_forwards_only_allowlisted_query_parameters(self):
        plan = api_ticket._validate_and_plan(
            packet(
                "newsapi-everything",
                {
                    "q": "Fuzhou AND business",
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": 20,
                    "page": 1,
                },
            ),
            ROOT,
        )
        row = plan["requests"][0]
        self.assertEqual(row["endpoint"], "/data/newsapi/everything")
        self.assertEqual(row["parameters"]["pageSize"], 20)
        self.assertEqual(
            plan["required_secret_environment_variables"],
            ["NEWSAPI_API_KEY"],
        )
        connector = self.connector("newsapi-everything")
        self.assertNotIn("X-Api-Key", connector.get("input_headers", []))
        self.assertEqual(
            connector["secret_header"],
            {"name": "X-Api-Key", "env": "NEWSAPI_API_KEY"},
        )

    def test_client_cannot_supply_backend_credential_parameter(self):
        request = packet("newsapi-everything", {"q": "Fuzhou"})
        request["requests"][0]["parameters"]["apiKey"] = "forbidden-value"
        with self.assertRaisesRegex(ValueError, "non-allowlisted"):
            api_ticket._validate_and_plan(request, ROOT)

    def test_documented_success_and_error_shapes(self):
        everything = self.connector("newsapi-everything")
        sources = self.connector("newsapi-sources")
        self.assertTrue(
            api_task.evaluate_response_contract(
                {
                    "status": "ok",
                    "totalResults": 1,
                    "articles": [{"title": "Example", "url": "https://example.com"}],
                },
                everything["response_contract"],
                allow_empty=False,
            )["success"]
        )
        self.assertTrue(
            api_task.evaluate_response_contract(
                {
                    "status": "ok",
                    "sources": [{"id": "example", "name": "Example"}],
                },
                sources["response_contract"],
                allow_empty=False,
            )["success"]
        )
        failed = api_task.evaluate_response_contract(
            {"status": "error", "code": "apiKeyInvalid", "message": "invalid"},
            everything["response_contract"],
            allow_empty=False,
        )
        self.assertFalse(failed["success"])
        self.assertEqual(failed["business_code"], "apiKeyInvalid")


if __name__ == "__main__":
    unittest.main()
