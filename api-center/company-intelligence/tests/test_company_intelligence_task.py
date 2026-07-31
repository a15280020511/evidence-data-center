from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "company_intelligence_task", ROOT / "company_intelligence_task.py"
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class CompanyIntelligenceTaskTests(unittest.TestCase):
    def ticket(self, operation: str, parameters: dict) -> dict:
        return {
            "task_id": f"test-tianyancha-{operation}",
            "provider": "tianyancha",
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

    def test_removed_qichacha_ticket_is_rejected(self) -> None:
        ticket = self.ticket("company-basic", {"keyword": "腾讯"})
        ticket["provider"] = "qichacha"
        with self.assertRaises(ValueError):
            module.validate_ticket(ticket)

    def test_sensitive_contact_and_identity_fields_are_removed(self) -> None:
        payload = {
            "Name": "示例公司",
            "PhoneNumber": "123",
            "OperName": "张三",
            "nested": {"email": "a@example.com", "value": 1},
        }
        self.assertEqual(
            module.sanitize_payload(payload),
            {"Name": "示例公司", "nested": {"value": 1}},
        )

    def test_missing_tianyancha_secret_is_structured_block(self) -> None:
        ticket = self.ticket("company-basic", {"keyword": "腾讯"})
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(
            os.environ, {module.TIANYANCHA_TOKEN_ENV: ""}, clear=False
        ):
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            ticket_path.write_text(json.dumps(ticket, ensure_ascii=False), encoding="utf-8")
            rc = module.execute(ticket_path, root / "out")
            self.assertEqual(rc, 1)
            snapshot = json.loads(
                (root / "out/company-snapshot.json").read_text(encoding="utf-8")
            )
            self.assertEqual(snapshot["status"], "API_COMPANY_BLOCKED")
            self.assertEqual(
                snapshot["failure"]["code"], "COMPANY_CREDENTIALS_MISSING"
            )

    def test_catalog_operation_needs_no_secret(self) -> None:
        ticket = self.ticket("catalog-capabilities", {})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            ticket_path.write_text(json.dumps(ticket, ensure_ascii=False), encoding="utf-8")
            rc = module.execute(ticket_path, root / "out")
            self.assertEqual(rc, 0)
            snapshot = json.loads(
                (root / "out/company-snapshot.json").read_text(encoding="utf-8")
            )
            self.assertEqual(snapshot["status"], "API_COMPANY_COMPLETED")
            self.assertEqual(snapshot["provider"], "tianyancha")
            self.assertFalse(snapshot["security"]["secret_values_included"])


if __name__ == "__main__":
    unittest.main()
