from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("market_search_task", ROOT / "market_search_task.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FakeResponse:
    def __init__(self, payload: dict, status: int = 200):
        self.status = status
        self.raw = json.dumps(payload).encode("utf-8")
        self.headers = {"Content-Type": "application/json"}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, amount: int) -> bytes:
        return self.raw[:amount]


def ticket(provider: str, operation: str, parameters: dict) -> dict:
    return {
        "task_id": f"test-{provider}-{operation}",
        "provider": provider,
        "operation": operation,
        "objective": "deterministic validation",
        "parameters": parameters,
        "data_policy": {"classification": "public", "contains_personal_data": False},
        "acceptance": {"timeout_seconds": 30, "max_response_bytes": 1000000},
    }


class MarketSearchTaskTests(unittest.TestCase):
    def test_catalog_contract(self):
        catalog = MODULE.load_json(ROOT / "provider-catalog.json")
        providers = {row["provider_id"]: row for row in catalog["providers"]}
        self.assertEqual(set(providers), {"tickflow", "serpapi"})
        self.assertEqual(providers["tickflow"]["required_secret_environment_variable"], "TICKFLOW_API_KEY")
        self.assertEqual(providers["serpapi"]["required_secret_environment_variable"], "SERPAPI_API_KEY")
        self.assertEqual(len(providers["tickflow"]["operations"]), 5)
        self.assertEqual(len(providers["serpapi"]["operations"]), 4)

    def test_rejects_cross_provider_operation(self):
        with self.assertRaisesRegex(ValueError, "not available"):
            MODULE.validate_ticket(ticket("tickflow", "google-search", {"query": "x"}))

    def test_prepare_requires_provider_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            event = Path(tmp) / "event.json"
            out = Path(tmp) / "out"
            event.write_text(json.dumps({"issue": {"title": "[api-serpapi] wrong", "body": json.dumps(ticket("tickflow", "quotes", {"symbols": ["600000.SH"]}))}}), encoding="utf-8")
            self.assertEqual(MODULE.prepare(event, out), 1)
            status = MODULE.load_json(out / "ticket-status.json")
            self.assertFalse(status["accepted"])
            self.assertIn("[api-tickflow]", status["reason"])

    def test_tickflow_quotes_uses_header_and_fixed_endpoint(self):
        captured = {}

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            captured["key"] = request.headers.get("X-api-key")
            return FakeResponse({"data": [{"symbol": "600000.SH", "last_price": 10.0}]})

        with patch.dict(os.environ, {"TICKFLOW_API_KEY": "tickflow-secret"}, clear=False), patch.object(MODULE.urllib.request, "urlopen", side_effect=fake_urlopen):
            data, metadata, secret_name = MODULE.tickflow_query("quotes", {"symbols": ["600000.SH"]}, 30, 1000000)
        self.assertEqual(secret_name, "TICKFLOW_API_KEY")
        self.assertEqual(captured["key"], "tickflow-secret")
        self.assertTrue(captured["url"].startswith("https://api.tickflow.org/v1/quotes?"))
        self.assertNotIn("tickflow-secret", json.dumps(data))
        self.assertEqual(metadata["request_path"], "/v1/quotes")

    def test_serpapi_scrubs_key_and_fixes_engine(self):
        captured = {}

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            return FakeResponse({
                "search_metadata": {"status": "Success"},
                "organic_results": [{"title": "example", "serpapi_link": "https://serpapi.com/search?api_key=serp-secret"}],
            })

        with patch.dict(os.environ, {"SERPAPI_API_KEY": "serp-secret"}, clear=False), patch.object(MODULE.urllib.request, "urlopen", side_effect=fake_urlopen):
            data, metadata, secret_name = MODULE.serpapi_query("google-search", {"query": "OpenAI", "gl": "us"}, 30, 1000000)
        query = captured["url"]
        self.assertIn("engine=google", query)
        self.assertIn("api_key=serp-secret", query)
        self.assertIn("async=false", query)
        self.assertNotIn("serp-secret", json.dumps(data))
        self.assertEqual(secret_name, "SERPAPI_API_KEY")
        self.assertNotIn("query", metadata)

    def test_execute_missing_secret_is_structured_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            ticket_path.write_text(json.dumps(ticket("serpapi", "google-news", {"query": "markets"})), encoding="utf-8")
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(MODULE.execute(ticket_path, root), 1)
            status = MODULE.load_json(root / "execution-status.json")
            self.assertEqual(status["status"], "API_MARKET_SEARCH_FAILED")
            self.assertIn("SERPAPI_API_KEY", status["failure"]["message"])
            self.assertFalse(status["secret_values_exposed"])


if __name__ == "__main__":
    unittest.main()
