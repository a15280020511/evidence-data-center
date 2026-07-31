from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("baostock_task", ROOT / "baostock_task.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class Result:
    error_code = "0"
    error_msg = "success"
    fields = ["calendar_date", "is_trading_day"]
    def __init__(self) -> None:
        self.rows = [["2026-07-01", "1"], ["2026-07-02", "1"]]
        self.index = -1
    def next(self) -> bool:
        self.index += 1
        return self.index < len(self.rows)
    def get_row_data(self):
        return self.rows[self.index]


class Login:
    error_code = "0"
    error_msg = "success"


class BaoStockTests(unittest.TestCase):
    def ticket(self, operation="trade-dates"):
        parameters = {"start_date": "2026-07-01", "end_date": "2026-07-02"} if operation == "trade-dates" else {}
        return {
            "task_id": "baostock-test-001", "provider": "baostock", "operation": operation,
            "objective": "test", "parameters": parameters,
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "acceptance": {"timeout_seconds": 10, "max_response_bytes": 100000, "max_rows": 100},
        }

    def test_catalog_has_fixed_readonly_surface(self):
        provider = module.provider_catalog()
        self.assertEqual(provider["provider_id"], "baostock")
        self.assertEqual(len(provider["operations"]), 20)
        self.assertEqual(provider["required_secret_environment_variable"], "")
        self.assertFalse(provider["limits"]["arbitrary_functions_allowed"])
        self.assertFalse(provider["limits"]["trading_or_order_execution_allowed"])

    def test_rejects_arbitrary_parameters(self):
        ticket = self.ticket()
        ticket["parameters"]["host"] = "example.com"
        with self.assertRaises(ValueError):
            module.validate_ticket(ticket)

    def test_mocked_upstream_execution(self):
        calls = []
        fake = types.SimpleNamespace(
            login=lambda: Login(),
            logout=lambda: calls.append("logout"),
            query_trade_dates=lambda **kwargs: (calls.append(kwargs) or Result()),
        )
        old = sys.modules.get("baostock")
        sys.modules["baostock"] = fake
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                ticket_path = root / "ticket.json"
                ticket_path.write_text(json.dumps(self.ticket()), encoding="utf-8")
                self.assertEqual(module.execute(ticket_path, root), 0)
                snapshot = json.loads((root / "baostock-snapshot.json").read_text())
                self.assertEqual(snapshot["status"], "API_BAOSTOCK_COMPLETED")
                self.assertEqual(snapshot["result"]["row_count"], 2)
                self.assertFalse(snapshot["credentials_required"])
                self.assertIn("logout", calls)
        finally:
            if old is None:
                sys.modules.pop("baostock", None)
            else:
                sys.modules["baostock"] = old

    def test_catalog_execution_needs_no_package_or_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            ticket_path.write_text(json.dumps(self.ticket("catalog-capabilities")), encoding="utf-8")
            self.assertEqual(module.execute(ticket_path, root), 0)
            snapshot = json.loads((root / "baostock-snapshot.json").read_text())
            self.assertFalse(snapshot["metadata"]["upstream_called"])


if __name__ == "__main__":
    unittest.main()
