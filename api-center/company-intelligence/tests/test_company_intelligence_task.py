from __future__ import annotations

import hashlib
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
    def ticket(self, provider: str, operation: str, parameters: dict) -> dict:
        return {
            "task_id": f"test-{provider}-{operation}",
            "provider": provider,
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

    def test_qichacha_signature_matches_official_formula(self) -> None:
        timespan, token = module._qcc_auth("app", "secret", 123456)
        self.assertEqual(timespan, "123456")
        self.assertEqual(
            token,
            hashlib.md5(b"app123456secret").hexdigest().upper(),
        )

    def test_provider_operation_pair_is_enforced(self) -> None:
        with self.assertRaisesRegex(ValueError, "not available"):
            module.validate_ticket(
                self.ticket("tianyancha", "company-search", {"keyword": "腾讯"})
            )

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

    def test_missing_qichacha_secret_is_structured_block(self) -> None:
        ticket = self.ticket("qichacha", "company-search", {"keyword": "腾讯"})
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(
            os.environ, {module.QICHACHA_CREDENTIALS_ENV: ""}, clear=False
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

    def test_missing_tianyancha_secret_is_structured_block(self) -> None:
        ticket = self.ticket("tianyancha", "company-basic", {"keyword": "腾讯"})
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

    def test_catalog_operations_need_no_secret(self) -> None:
        ticket = self.ticket("qichacha", "catalog-capabilities", {})
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
            self.assertFalse(snapshot["security"]["secret_values_included"])


if __name__ == "__main__":
    unittest.main()
