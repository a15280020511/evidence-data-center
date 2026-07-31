from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("provider_task", HERE / "provider_task.py")
assert SPEC and SPEC.loader
provider_task = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(provider_task)


class FakeHeaders(dict):
    def get(self, key, default=None):
        return super().get(key, default)


class FakeResponse:
    def __init__(self, body: bytes, status: int = 200, content_type: str = "application/json"):
        self.body = body
        self.status = status
        self.headers = FakeHeaders({"Content-Type": content_type})

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, amount=-1):
        return self.body if amount < 0 else self.body[:amount]


class ProviderTaskTests(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
        self.providers = {row["provider_id"]: row for row in self.catalog["providers"]}

    def test_catalog_contract(self):
        self.assertEqual(set(self.providers), {"wolframalpha", "llamaparse"})
        self.assertEqual(len(self.providers["wolframalpha"]["operations"]), 5)
        self.assertEqual(len(self.providers["llamaparse"]["operations"]), 4)
        self.assertEqual(
            self.providers["wolframalpha"]["required_secret_environment_variable"],
            "WOLFRAMALPHA_APP_ID",
        )
        self.assertEqual(
            self.providers["llamaparse"]["required_secret_environment_variable"],
            "LLAMA_CLOUD_API_KEY",
        )
        self.assertFalse(self.catalog["secret_values_exposed"])

    def test_ticket_provider_operation_pairing(self):
        ticket = {
            "task_id": "test-001",
            "provider": "wolframalpha",
            "operation": "llm-query",
            "objective": "calculate",
            "parameters": {"input": "2+2", "maxchars": 500},
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "acceptance": {"timeout_seconds": 20, "max_response_bytes": 200000},
        }
        provider_task.validate_ticket(ticket)
        ticket["operation"] = "get-parse-result"
        with self.assertRaises(ValueError):
            provider_task.validate_ticket(ticket)

    def test_source_url_rejects_private_address(self):
        with patch.object(
            provider_task.socket,
            "getaddrinfo",
            return_value=[(2, 1, 6, "", ("127.0.0.1", 443))],
        ):
            with self.assertRaises(provider_task.ProviderError) as ctx:
                provider_task.validate_public_https_url("https://example.test/file.pdf")
        self.assertEqual(ctx.exception.code, "LLAMAPARSE_SOURCE_URL_REJECTED")

    def test_source_url_accepts_public_https(self):
        with patch.object(
            provider_task.socket,
            "getaddrinfo",
            return_value=[(2, 1, 6, "", ("93.184.216.34", 443))],
        ):
            value = provider_task.validate_public_https_url("https://example.com/file.pdf")
        self.assertEqual(value, "https://example.com/file.pdf")

    def test_wolfram_llm_uses_bearer_and_never_returns_secret(self):
        observed = {}

        def opener(request, timeout):
            observed["authorization"] = request.headers.get("Authorization")
            observed["url"] = request.full_url
            return FakeResponse(b"4", content_type="text/plain")

        with patch.dict(os.environ, {"WOLFRAMALPHA_APP_ID": "secret-app-id"}, clear=False):
            result, metadata = provider_task.query_wolfram(
                "llm-query", {"input": "2+2", "maxchars": 500},
                timeout=10, max_bytes=10000, opener=opener,
            )
        self.assertEqual(result["text"], "4")
        self.assertEqual(observed["authorization"], "Bearer secret-app-id")
        self.assertNotIn("secret-app-id", observed["url"])
        self.assertFalse(metadata["secret_value_exposed"])

    def test_llamaparse_get_result_uses_bearer(self):
        observed = {}

        def opener(request, timeout):
            observed["authorization"] = request.headers.get("Authorization")
            observed["url"] = request.full_url
            return FakeResponse(b'{"job":{"id":"job-1","status":"COMPLETED"}}')

        with patch.dict(os.environ, {"LLAMA_CLOUD_API_KEY": "llx-secret"}, clear=False):
            result, metadata = provider_task.query_llamaparse(
                "get-parse-result",
                {"job_id": "job-1", "expand": ["markdown", "items"]},
                timeout=10, max_bytes=10000, opener=opener,
            )
        self.assertEqual(result["job"]["status"], "COMPLETED")
        self.assertEqual(observed["authorization"], "Bearer llx-secret")
        self.assertIn("expand=markdown%2Citems", observed["url"])
        self.assertFalse(metadata["secret_value_exposed"])

    def test_prepare_requires_matching_prefix(self):
        ticket = {
            "task_id": "test-002",
            "provider": "llamaparse",
            "operation": "list-parse-jobs",
            "objective": "list jobs",
            "parameters": {"page_size": 10},
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "acceptance": {"timeout_seconds": 20, "max_response_bytes": 200000},
        }
        event = {"issue": {"title": "[api-wolframalpha] wrong prefix", "body": json.dumps(ticket)}}
        with tempfile.TemporaryDirectory() as temp:
            event_path = Path(temp) / "event.json"
            output_dir = Path(temp) / "out"
            event_path.write_text(json.dumps(event), encoding="utf-8")
            self.assertEqual(provider_task.prepare(event_path, output_dir), 1)
            status = json.loads((output_dir / "ticket-status.json").read_text(encoding="utf-8"))
        self.assertFalse(status["accepted"])
        self.assertIn("[api-llamaparse]", status["reason"])


if __name__ == "__main__":
    unittest.main()
