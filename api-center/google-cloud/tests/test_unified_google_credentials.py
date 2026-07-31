from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("unified_google_credentials", ROOT / "unified_google_credentials.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class UnifiedGoogleCredentialsTests(unittest.TestCase):
    def service_account(self) -> dict:
        return {
            "type": "service_account",
            "project_id": "valid-project-123",
            "private_key_id": "test-key-id",
            "private_key": "test-placeholder-not-a-real-key",
            "client_email": "service@example.invalid",
            "token_uri": "https://oauth2.googleapis.com/token",
        }

    def bundle(self) -> str:
        return json.dumps({"service_account": self.service_account(), "retired_field": "ignored"})

    def test_parse_nested_bundle_returns_service_account(self) -> None:
        service_account = module.parse_bundle(self.bundle())
        self.assertEqual(service_account["project_id"], "valid-project-123")
        self.assertNotIn("retired_field", service_account)

    def test_parse_compact_service_account(self) -> None:
        service_account = module.parse_bundle(json.dumps(self.service_account()))
        self.assertEqual(service_account["client_email"], "service@example.invalid")

    def test_missing_bundle_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "GOOGLE_CLOUD_SERVICE_ACCOUNT_JSON"):
            module.parse_bundle("")

    def test_export_runtime_writes_only_two_ephemeral_variables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "github-env"
            module.export_runtime(self.bundle(), target)
            text = target.read_text(encoding="utf-8")
            self.assertIn("BIGQUERY_SERVICE_ACCOUNT_JSON<<", text)
            self.assertIn("EARTH_ENGINE_SERVICE_ACCOUNT_JSON<<", text)
            self.assertEqual(text.count("<<GOOGLE_BUNDLE_"), 2)


if __name__ == "__main__":
    unittest.main()
