
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("akshare_task_tests", ROOT / "akshare_task.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class FakeFrame:
    columns = ["代码", "名称", "最新价"]

    def __init__(self, rows):
        self.rows = rows

    def head(self, count):
        return FakeFrame(self.rows[:count])

    def to_dict(self, orient):
        assert orient == "records"
        return self.rows


class AkshareTaskTests(unittest.TestCase):
    def ticket(self, operation="catalog-capabilities", parameters=None, provider="akshare"):
        return {
            "task_id": "akshare-test-0001",
            "provider": provider,
            "operation": operation,
            "objective": "validate fixed public financial data adapter",
            "parameters": parameters or {},
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "acceptance": {"timeout_seconds": 30, "max_response_bytes": 500000},
        }

    def test_catalog_and_allowlist(self):
        module.validate_ticket(self.ticket())
        bad = self.ticket()
        bad["operation"] = "arbitrary-python"
        with self.assertRaisesRegex(ValueError, "unsupported"):
            module.validate_ticket(bad)

    def test_history_calls_only_fixed_function(self):
        fake = types.SimpleNamespace(
            stock_zh_a_hist=mock.Mock(return_value=FakeFrame([{"日期": "2026-01-01", "收盘": 10.0}]))
        )
        with mock.patch.dict(sys.modules, {"akshare": fake}):
            data = module._execute_operation(
                "stock-a-share-history",
                {
                    "symbol": "000001",
                    "period": "daily",
                    "start_date": "20260101",
                    "end_date": "20260131",
                    "adjust": "qfq",
                    "max_rows": 10,
                    "timeout_seconds": 20,
                },
            )
        self.assertEqual(data["row_count"], 1)
        fake.stock_zh_a_hist.assert_called_once()

    def test_provider_operation_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "belongs to provider"):
            module.validate_ticket(
                self.ticket(
                    operation="ashare-get-price", provider="akshare",
                    parameters={"symbol": "sh600000", "frequency": "1d", "count": 10},
                )
            )

    def test_ashare_tencent_normalization(self):
        payload = {"data": {"sh600000": {"qfqday": [["2026-01-02", "10", "10.5", "10.8", "9.9", "1000"]]}}}
        with mock.patch.object(module, "_http_json", return_value=payload):
            data = module._execute_operation(
                "ashare-get-price",
                {"symbol": "sh600000", "frequency": "1d", "count": 10, "source": "tencent"},
            )
        self.assertEqual(data["provider"], "ashare")
        self.assertEqual(data["source_used"], "tencent")
        self.assertEqual(data["rows"][0]["close"], 10.5)

    def test_ashare_auto_falls_back_to_sina(self):
        sina = [{"day": "2026-01-02", "open": "10", "close": "10.5", "high": "10.8", "low": "9.9", "volume": "1000"}]
        def side_effect(url, timeout):
            if "gtimg" in url:
                raise OSError("controlled Tencent failure")
            return sina
        with mock.patch.object(module, "_http_json", side_effect=side_effect):
            data = module._execute_operation(
                "ashare-get-price",
                {"symbol": "sh600000", "frequency": "1d", "count": 10, "source": "auto"},
            )
        self.assertEqual(data["source_used"], "sina")
        self.assertTrue(data["fallback_used"])

    def test_execute_catalog_needs_no_network_or_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            output = root / "out"
            ticket_path.write_text(json.dumps(self.ticket()), encoding="utf-8")
            self.assertEqual(module.execute(ticket_path, output), 0)
            snapshot = json.loads((output / "akshare-snapshot.json").read_text(encoding="utf-8"))
            self.assertEqual(snapshot["status"], "API_AKSHARE_COMPLETED")
            self.assertFalse(snapshot["security"]["brokerage_execution_allowed"])


if __name__ == "__main__":
    unittest.main()
