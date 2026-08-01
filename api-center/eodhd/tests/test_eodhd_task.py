from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("eodhd_task", ROOT / "eodhd_task.py")
assert SPEC and SPEC.loader
eodhd = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(eodhd)


class FakeResponse:
    status = 200
    headers = {"Content-Type": "application/json"}

    def __init__(self, payload: object) -> None:
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, limit: int) -> bytes:
        return self.payload[:limit]


class EodhdTests(unittest.TestCase):
    def ticket(self, operation: str, parameters: dict) -> dict:
        return {
            "task_id": "eodhd-test-001",
            "provider": "eodhd",
            "operation": operation,
            "objective": "test bounded read-only EODHD provider",
            "parameters": parameters,
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "acceptance": {"timeout_seconds": 10, "max_response_bytes": 100000, "max_rows": 100},
        }

    def test_catalog_has_fixed_readonly_surface(self) -> None:
        provider = eodhd.provider_catalog()
        self.assertEqual(provider["required_secret_environment_variable"], "EODHD_API_TOKEN")
        self.assertEqual(len(provider["operations"]), 25)
        self.assertFalse(provider["limits"]["arbitrary_urls_allowed"])
        self.assertFalse(provider["limits"]["trading_or_order_execution_allowed"])

    def test_rejects_arbitrary_parameters_and_bad_screener(self) -> None:
        with self.assertRaises(ValueError):
            eodhd.validate_ticket(self.ticket("eod-history", {"symbol": "AAPL.US", "url": "https://evil.test"}))
        with self.assertRaises(ValueError):
            eodhd.validate_ticket(self.ticket("screener", {"filters_json": '[["unknown",">",1]]'}))

    def test_build_request_injects_token_without_metadata_leak(self) -> None:
        request, metadata = eodhd.build_request(
            "eod-history",
            {"symbol": "AAPL.US", "from_date": "2026-07-01", "to_date": "2026-07-31"},
            "secret-token",
        )
        parsed = urllib.parse.urlsplit(request.full_url)
        query = urllib.parse.parse_qs(parsed.query)
        self.assertEqual(parsed.netloc, "eodhd.com")
        self.assertEqual(parsed.path, "/api/eod/AAPL.US")
        self.assertEqual(query["api_token"], ["secret-token"])
        self.assertEqual(query["fmt"], ["json"])
        self.assertNotIn("secret-token", json.dumps(metadata))

    def test_mocked_upstream_execution_and_catalog_mode(self) -> None:
        with mock.patch.dict(os.environ, {"EODHD_API_TOKEN": "secret-token"}, clear=False):
            result, metadata = eodhd.query_eodhd(
                "eod-history",
                {"symbol": "AAPL.US"},
                timeout=10,
                max_bytes=100000,
                max_rows=100,
                opener=lambda *_args, **_kwargs: FakeResponse([{"date": "2026-07-31", "close": 1.0}]),
                sleeper=lambda _: None,
            )
        self.assertEqual(len(result), 1)
        self.assertEqual(metadata["row_count"], 1)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            ticket_path.write_text(json.dumps(self.ticket("catalog-capabilities", {})), encoding="utf-8")
            self.assertEqual(eodhd.execute(ticket_path, root / "out"), 0)
            snapshot = json.loads((root / "out/eodhd-snapshot.json").read_text(encoding="utf-8"))
            self.assertFalse(snapshot["metadata"]["upstream_called"])


if __name__ == "__main__":
    unittest.main()
