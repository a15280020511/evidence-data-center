from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("data_commons_key_validation_tests", ROOT / "data_commons_task.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class DataCommonsKeyValidationTests(unittest.TestCase):
    def ticket(self) -> dict:
        return {
            "task_id": "dc-invalid-key-test",
            "provider": "data-commons",
            "operation": "resolve-place",
            "objective": "validate key handling",
            "parameters": {"nodes_json": '["Fuzhou"]'},
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "acceptance": {"timeout_seconds": 30, "max_response_bytes": 500000},
        }

    def test_visible_ascii_key_is_accepted(self) -> None:
        self.assertEqual(module._validate_api_key("AIza_valid-key_123"), "AIza_valid-key_123")

    def test_non_ascii_placeholder_is_blocked_before_http(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "visible ASCII"):
            module._validate_api_key("你的Data Commons API Key")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            output_dir = root / "out"
            ticket_path.write_text(json.dumps(self.ticket()), encoding="utf-8")
            with mock.patch.dict(os.environ, {module.API_KEY_ENV: "你的Data Commons API Key"}, clear=True), mock.patch.object(
                module.requests, "post"
            ) as post:
                rc = module.execute(ticket_path, output_dir)
            self.assertEqual(rc, 1)
            post.assert_not_called()
            snapshot = json.loads((output_dir / "data-commons-snapshot.json").read_text(encoding="utf-8"))
            self.assertEqual(snapshot["status"], "API_DATA_COMMONS_BLOCKED")
            self.assertEqual(snapshot["failure"]["code"], "DATA_COMMONS_API_KEY_INVALID")
            self.assertFalse(snapshot["failure"]["retryable"])


if __name__ == "__main__":
    unittest.main()
