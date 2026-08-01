from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "alpha_vantage_task", ROOT / "alpha_vantage_task.py"
)
assert SPEC and SPEC.loader
av = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(av)


class FakeResponse:
    def __init__(self, status_code: int, payload, headers=None):
        self.status_code = status_code
        self.content = json.dumps(payload).encode("utf-8")
        self.headers = headers or {"Content-Type": "application/json"}


class AlphaVantageTests(unittest.TestCase):
    def ticket(self, operation="stock-daily", parameters=None):
        return {
            "task_id": "av-test-001",
            "provider": "alpha-vantage",
            "operation": operation,
            "parameters": parameters or (
                {"symbol": "IBM", "outputsize": "compact"}
                if operation == "stock-daily"
                else {}
            ),
            "acceptance": {
                "timeout_seconds": 30,
                "max_response_bytes": 1000000,
            },
            "data_policy": {
                "public_data_only": True,
                "no_personal_data": True,
                "no_secret_values": True,
            },
        }

    def test_catalog_is_fixed_and_secret_safe(self):
        provider = av.provider_catalog()
        self.assertEqual(provider["provider_id"], "alpha-vantage")
        self.assertEqual(provider["ticket_prefix"], "[api-alpha-vantage]")
        self.assertEqual(
            provider["required_secret_environment_variable"],
            "ALPHA_VANTAGE_API_KEY",
        )
        self.assertEqual(len(provider["operations"]), 66)
        self.assertFalse(provider["limits"]["arbitrary_functions_allowed"])
        self.assertFalse(provider["limits"]["client_supplied_api_key_allowed"])
        self.assertEqual(provider["limits"]["requests_per_ticket_max"], 1)
        serialized = json.dumps(provider, ensure_ascii=False)
        self.assertNotIn("demo", serialized)
        self.assertNotIn("apikey=", serialized)

    def test_validate_rejects_client_supplied_apikey(self):
        ticket = self.ticket(parameters={"symbol": "IBM", "apikey": "forbidden"})
        with self.assertRaisesRegex(ValueError, "Additional properties"):
            av.validate_ticket(ticket)

    def test_query_injects_fixed_function_and_scrubs_secret(self):
        calls = []

        def requester(url, **kwargs):
            calls.append((url, kwargs))
            return FakeResponse(
                200,
                {
                    "Meta Data": {"1. Information": "Daily Prices"},
                    "Time Series (Daily)": {
                        "2026-07-31": {"4. close": "123.45"},
                    },
                    "echo": "secret-test-key",
                },
            )

        with patch.dict(os.environ, {"ALPHA_VANTAGE_API_KEY": "secret-test-key"}):
            result, metadata = av.query_alpha_vantage(
                "stock-daily",
                {"symbol": "IBM", "outputsize": "compact"},
                timeout=30,
                max_bytes=1000000,
                requester=requester,
            )
        self.assertEqual(len(calls), 1)
        url, kwargs = calls[0]
        self.assertEqual(url, "https://www.alphavantage.co/query")
        self.assertEqual(kwargs["params"]["function"], "TIME_SERIES_DAILY")
        self.assertEqual(kwargs["params"]["apikey"], "secret-test-key")
        self.assertEqual(kwargs["params"]["datatype"], "json")
        self.assertFalse(kwargs["allow_redirects"])
        self.assertEqual(result["echo"], "[REDACTED]")
        self.assertNotIn("secret-test-key", json.dumps(metadata))
        self.assertEqual(metadata["transport_attempts"], 1)

    def test_information_payload_becomes_structured_quota_error(self):
        def requester(url, **kwargs):
            return FakeResponse(
                200,
                {"Information": "Our standard API rate limit is 25 requests per day."},
            )

        with patch.dict(os.environ, {"ALPHA_VANTAGE_API_KEY": "secret"}):
            with self.assertRaises(av.AlphaVantageError) as ctx:
                av.query_alpha_vantage(
                    "market-status",
                    {},
                    timeout=30,
                    max_bytes=1000000,
                    requester=requester,
                )
        self.assertEqual(ctx.exception.code, "ALPHA_VANTAGE_RATE_OR_ENTITLEMENT")
        self.assertFalse(ctx.exception.retryable)

    def test_http_failure_is_not_retried(self):
        counter = {"calls": 0}

        def requester(url, **kwargs):
            counter["calls"] += 1
            return FakeResponse(503, {"message": "down"})

        with patch.dict(os.environ, {"ALPHA_VANTAGE_API_KEY": "secret"}):
            with self.assertRaises(av.AlphaVantageError) as ctx:
                av.query_alpha_vantage(
                    "market-status",
                    {},
                    timeout=30,
                    max_bytes=1000000,
                    requester=requester,
                )
        self.assertEqual(counter["calls"], 1)
        self.assertTrue(ctx.exception.retryable)

    def test_local_catalog_execute_does_not_require_secret(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            ticket_path = temp_path / "ticket.json"
            ticket_path.write_text(
                json.dumps(self.ticket("catalog-capabilities", {})),
                encoding="utf-8",
            )
            output = temp_path / "out"
            with patch.dict(os.environ, {}, clear=True):
                code = av.execute(ticket_path, output)
            self.assertEqual(code, 0)
            snapshot = json.loads(
                (output / "alpha-vantage-snapshot.json").read_text(encoding="utf-8")
            )
            self.assertEqual(snapshot["status"], "API_ALPHA_VANTAGE_COMPLETED")
            self.assertFalse(snapshot["metadata"]["upstream_called"])
            self.assertEqual(snapshot["metadata"]["operation_count"], 66)

    def test_prepare_requires_fixed_issue_prefix(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            event = {
                "issue": {
                    "title": "[api] wrong",
                    "body": json.dumps(self.ticket()),
                }
            }
            event_path = temp_path / "event.json"
            event_path.write_text(json.dumps(event), encoding="utf-8")
            output = temp_path / "out"
            self.assertEqual(av.prepare(event_path, output), 1)
            status = json.loads(
                (output / "ticket-status.json").read_text(encoding="utf-8")
            )
            self.assertFalse(status["accepted"])
            self.assertIn("[api-alpha-vantage]", status["reason"])


if __name__ == "__main__":
    unittest.main()
