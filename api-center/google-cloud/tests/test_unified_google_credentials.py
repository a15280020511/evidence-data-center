from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "unified_google_credentials", ROOT / "unified_google_credentials.py"
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class UnifiedGoogleCredentialsTests(unittest.TestCase):
    def bundle(self) -> str:
        return json.dumps(
            {
                "service_account": {
                    "type": "service_account",
                    "project_id": "valid-project-123",
                    "private_key_id": "test-key-id",
                    "private_key": "test-placeholder-not-a-real-key",
                    "client_email": "service@example.invalid",
                    "token_uri": "https://oauth2.googleapis.com/token",
                },
                "data_commons_api_key": "test-placeholder-key",
            }
        )

    def test_parse_bundle_returns_shared_service_account_and_api_key(self) -> None:
        service_account, api_key = module.parse_bundle(self.bundle())
        self.assertEqual(service_account["project_id"], "valid-project-123")
        self.assertEqual(api_key, "test-placeholder-key")

    def test_missing_bundle_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "GOOGLE_CREDENTIALS_JSON"):
            module.parse_bundle("")

    def test_missing_data_commons_key_is_rejected(self) -> None:
        value = json.loads(self.bundle())
        value["data_commons_api_key"] = ""
        with self.assertRaisesRegex(RuntimeError, "data_commons_api_key"):
            module.parse_bundle(json.dumps(value))

    def test_export_runtime_writes_three_ephemeral_variables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "github-env"
            module.export_runtime(self.bundle(), target)
            text = target.read_text(encoding="utf-8")
            self.assertIn("BIGQUERY_SERVICE_ACCOUNT_JSON<<", text)
            self.assertIn("EARTH_ENGINE_SERVICE_ACCOUNT_JSON<<", text)
            self.assertIn("GOOGLE_DATA_COMMONS_API_KEY<<", text)
            self.assertNotIn("GOOGLE_CREDENTIALS_JSON=", text)


if __name__ == "__main__":
    unittest.main()
