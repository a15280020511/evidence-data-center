from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("miaoxiang_task", ROOT / "miaoxiang_task.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class MiaoxiangTaskTests(unittest.TestCase):
    def ticket(self, operation: str, parameters: dict) -> dict:
        return {
            "task_id": f"test-miaoxiang-{operation}",
            "provider": "miaoxiang",
            "operation": operation,
            "objective": "test",
            "parameters": parameters,
            "data_policy": {
                "classification": "public",
                "contains_personal_data": False,
            },
            "acceptance": {
                "timeout_seconds": 10,
                "max_response_bytes": 100000,
            },
        }

    def test_financial_data_body_uses_tool_query(self) -> None:
        self.assertEqual(
            module.build_body("financial-data", {"query": "贵州茅台最新市盈率"}),
            {"toolQuery": "贵州茅台最新市盈率"},
        )

    def test_stock_screen_body_is_bounded(self) -> None:
        body = module.build_body(
            "stock-screen",
            {"keyword": "市盈率低于20且净利润增长", "page_no": 2, "page_size": 50},
        )
        self.assertEqual(body["pageNo"], 2)
        self.assertEqual(body["pageSize"], 50)
        with self.assertRaisesRegex(ValueError, "page_size"):
            module.build_body(
                "stock-screen", {"keyword": "测试", "page_size": 101}
            )

    def test_missing_api_key_is_structured_block(self) -> None:
        ticket = self.ticket("financial-search", {"query": "A股市场"})
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(
            os.environ, {module.API_KEY_ENV: ""}, clear=False
        ):
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            ticket_path.write_text(json.dumps(ticket, ensure_ascii=False), encoding="utf-8")
            rc = module.execute(ticket_path, root / "out")
            self.assertEqual(rc, 1)
            snapshot = json.loads(
                (root / "out/miaoxiang-snapshot.json").read_text(encoding="utf-8")
            )
            self.assertEqual(snapshot["status"], "API_MIAOXIANG_BLOCKED")
            self.assertEqual(snapshot["failure"]["code"], "MIAOXIANG_API_KEY_MISSING")

    def test_catalog_needs_no_key_and_exposes_no_write_operation(self) -> None:
        ticket = self.ticket("catalog-capabilities", {})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            ticket_path.write_text(json.dumps(ticket, ensure_ascii=False), encoding="utf-8")
            rc = module.execute(ticket_path, root / "out")
            self.assertEqual(rc, 0)
            snapshot = json.loads(
                (root / "out/miaoxiang-snapshot.json").read_text(encoding="utf-8")
            )
            operations = {row["operation_id"] for row in snapshot["data"]["operations"]}
            self.assertEqual(
                operations,
                {"catalog-capabilities", "financial-search", "financial-data", "stock-screen"},
            )
            self.assertFalse(snapshot["security"]["write_operations_allowed"])
            self.assertFalse(snapshot["security"]["simulated_trading_allowed"])

    def test_unknown_parameters_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            module.validate_ticket(
                self.ticket("financial-search", {"query": "市场", "url": "https://example.com"})
            )


if __name__ == "__main__":
    unittest.main()
