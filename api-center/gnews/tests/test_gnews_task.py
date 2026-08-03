from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("gnews_task", ROOT / "gnews_task.py")
assert SPEC and SPEC.loader
task = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(task)


class FakeResponse:
    status_code = 200
    headers = {"Content-Type": "application/json"}
    is_redirect = False
    content = json.dumps({
        "totalArticles": 1,
        "articles": [{
            "title": "Example",
            "description": "Example article",
            "content": "Truncated",
            "url": "https://example.com/article",
            "image": None,
            "publishedAt": "2026-08-03T00:00:00Z",
            "source": {"name": "Example", "url": "https://example.com"},
        }],
    }).encode("utf-8")


class GNewsTests(unittest.TestCase):
    def ticket(self, operation="catalog-capabilities", parameters=None):
        return {
            "task_id": "gnews-test-001",
            "provider": "gnews",
            "operation": operation,
            "objective": "test bounded GNews provider",
            "parameters": parameters or {},
            "data_policy": {
                "classification": "public",
                "contains_personal_data": False,
                "contains_confidential_data": False,
            },
            "acceptance": {
                "timeout_seconds": 30,
                "max_response_bytes": 1000000,
                "max_rows": 10,
            },
        }

    def test_catalog_and_schema_are_fixed(self):
        catalog = json.loads((ROOT / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "gnews")
        self.assertEqual(provider["ticket_prefix"], "[intel-gnews]")
        self.assertEqual(provider["required_secret_environment_variable"], "GNEWS_API_KEY")
        self.assertEqual(len(provider["operations"]), 3)
        self.assertEqual(provider["limits"]["fixed_api_host"], "gnews.io")
        self.assertEqual(provider["limits"]["free_plan_requests_per_day"], 100)
        self.assertTrue(provider["limits"]["free_plan_noncommercial_development_testing_only"])
        self.assertFalse(provider["limits"]["automatic_pagination_allowed"])
        task.validate_ticket(self.ticket(), schema_path=task.SCHEMA_PATH, catalog_path=task.CATALOG_PATH)

    def test_request_builder_uses_only_fixed_paths_and_free_safe_limits(self):
        url, query, metadata = task.build_request("search-news", {
            "q": "China economy",
            "lang": "zh",
            "country": "cn",
            "max": 10,
            "page": 1,
            "in": ["title", "description"],
            "sortby": "publishedAt",
        })
        self.assertEqual(url, "https://gnews.io/api/v4/search")
        self.assertEqual(query["max"], "10")
        self.assertEqual(query["in"], "title,description")
        self.assertNotIn("apikey", query)
        self.assertEqual(metadata["credential_mode"], "x-api-key-header-backend-only")
        with self.assertRaises(ValueError):
            task.build_request("search-news", {"q": "x", "max": 11})
        with self.assertRaises(ValueError):
            task.build_request("search-news", {
                "q": "x",
                "from": "2026-01-01T00:00:00Z",
                "to": "2026-03-01T00:00:00Z",
            })

    def test_local_catalog_execution_needs_no_secret_or_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            ticket = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket.write_text(json.dumps(self.ticket()), encoding="utf-8")
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(task.execute(ticket, out), 0)
            diagnostics = json.loads((out / "diagnostics.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostics["status"], "INTEL_GNEWS_COMPLETED")
            self.assertFalse(diagnostics["metadata"]["upstream_called"])

    def test_mocked_upstream_uses_header_key_once(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch.dict(os.environ, {"GNEWS_API_KEY": "test-key-123456"}, clear=True), \
             patch.object(task.requests, "get", return_value=FakeResponse()) as get:
            ticket = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket.write_text(json.dumps(self.ticket("top-headlines", {
                "category": "business", "lang": "en", "max": 1
            })), encoding="utf-8")
            self.assertEqual(task.execute(ticket, out), 0)
            self.assertEqual(get.call_count, 1)
            kwargs = get.call_args.kwargs
            self.assertEqual(kwargs["headers"]["X-Api-Key"], "test-key-123456")
            self.assertNotIn("apikey", kwargs["params"])
            self.assertFalse(kwargs["allow_redirects"])
            diagnostics = json.loads((out / "diagnostics.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostics["status"], "INTEL_GNEWS_COMPLETED")
            self.assertEqual(diagnostics["metadata"]["row_count"], 1)

    def test_missing_secret_fails_closed_without_leak(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            ticket = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket.write_text(json.dumps(self.ticket("search-news", {"q": "test"})), encoding="utf-8")
            self.assertEqual(task.execute(ticket, out), 1)
            diagnostics = json.loads((out / "diagnostics.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostics["status"], "INTEL_GNEWS_FAILED")
            self.assertEqual(diagnostics["failure"]["code"], "GNEWS_API_KEY_MISSING")


if __name__ == "__main__":
    unittest.main()
