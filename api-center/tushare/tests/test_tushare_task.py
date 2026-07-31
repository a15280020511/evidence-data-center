from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("tushare_task", ROOT / "tushare_task.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class DummyResponse:
    def __init__(self, payload: dict, status: int = 200) -> None:
        self.status = status
        self.headers = {"Content-Type": "application/json; charset=utf-8"}
        self.raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, size: int = -1) -> bytes:
        return self.raw if size < 0 else self.raw[:size]


class TushareTaskTests(unittest.TestCase):
    def ticket(self, operation: str = "daily-quotes", parameters: dict | None = None) -> dict:
        return {
            "task_id": "tushare-test-001",
            "provider": "tushare",
            "operation": operation,
            "objective": "test bounded Tushare read",
            "parameters": parameters or {},
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "acceptance": {"timeout_seconds": 20, "max_response_bytes": 1000000},
        }

    def test_catalog_and_execution_map_are_identical(self) -> None:
        operation_ids = {
            row["operation_id"] for row in module.provider_catalog()["operations"]
        }
        self.assertEqual(
            operation_ids - {"catalog-capabilities"},
            set(module.OPERATION_API_NAMES),
        )
        self.assertEqual(len(operation_ids), 20)
        self.assertEqual(module.provider_catalog()["required_secret_environment_variable"], "TUSHARE_API_TOKEN")
        self.assertFalse(module.provider_catalog()["limits"]["arbitrary_api_names_allowed"])
        self.assertFalse(module.provider_catalog()["limits"]["trading_or_order_execution_allowed"])

    def test_ticket_rejects_unknown_parameter(self) -> None:
        with self.assertRaises(ValueError):
            module.validate_ticket(self.ticket(parameters={"ts_code": "000001.SZ", "url": "https://example.com"}))

    def test_successful_query_uses_https_and_never_returns_token(self) -> None:
        captured: dict = {}

        def opener(request, timeout):
            captured["url"] = request.full_url
            captured["method"] = request.get_method()
            captured["body"] = json.loads(request.data.decode("utf-8"))
            captured["timeout"] = timeout
            return DummyResponse({
                "code": 0,
                "msg": None,
                "data": {
                    "fields": ["ts_code", "trade_date", "close"],
                    "items": [["000001.SZ", "20260731", 10.25]],
                },
            })

        with patch.dict(os.environ, {"TUSHARE_API_TOKEN": "secret-token-value"}, clear=False):
            result, metadata = module.query_tushare(
                "daily-quotes",
                {"ts_code": "000001.SZ", "start_date": "20260701", "end_date": "20260731"},
                timeout=20,
                max_bytes=1000000,
                opener=opener,
                sleeper=lambda _: None,
            )
        self.assertEqual(captured["url"], "https://api.tushare.pro")
        self.assertEqual(captured["method"], "POST")
        self.assertEqual(captured["body"]["api_name"], "daily")
        self.assertEqual(captured["body"]["token"], "secret-token-value")
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(result["rows"][0]["close"], 10.25)
        self.assertTrue(metadata["upstream_called"])
        serialized = json.dumps({"result": result, "metadata": metadata}, ensure_ascii=False)
        self.assertNotIn("secret-token-value", serialized)

    def test_permission_error_is_structured_and_redacted(self) -> None:
        def opener(request, timeout):
            return DummyResponse({"code": 2002, "msg": "没有权限 secret-token-value", "data": None})

        with patch.dict(os.environ, {"TUSHARE_API_TOKEN": "secret-token-value"}, clear=False):
            with self.assertRaises(module.TushareError) as captured:
                module.query_tushare(
                    "daily-quotes", {}, timeout=20, max_bytes=1000000,
                    opener=opener, sleeper=lambda _: None,
                )
        self.assertEqual(captured.exception.code, "TUSHARE_PERMISSION_DENIED")
        self.assertNotIn("secret-token-value", str(captured.exception))
        self.assertIn("[REDACTED]", str(captured.exception))

    def test_catalog_operation_needs_no_secret_or_upstream(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            ticket_path.write_text(
                json.dumps(self.ticket("catalog-capabilities"), ensure_ascii=False),
                encoding="utf-8",
            )
            with patch.dict(os.environ, {}, clear=True):
                status = module.execute(ticket_path, root / "out")
            self.assertEqual(status, 0)
            snapshot = json.loads((root / "out/tushare-snapshot.json").read_text(encoding="utf-8"))
            self.assertFalse(snapshot["metadata"]["upstream_called"])
            self.assertEqual(snapshot["metadata"]["operation_count"], 20)


if __name__ == "__main__":
    unittest.main()
