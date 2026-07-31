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

    def ticket(self, provider: str, operation: str) -> dict:
        return {
            "task_id": f"test-{provider}-{operation}",
            "provider": provider,
            "operation": operation,
            "objective": "credential diagnostic test",
            "parameters": {},
            "data_policy": {
                "classification": "public",
                "contains_personal_data": False,
            },
        }

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

    def test_gcp_missing_bundle_generates_structured_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "out"
            ticket_path = root / "ticket.json"
            ticket = self.ticket("bigquery", "query-readonly")
            ticket_path.write_text(json.dumps(ticket), encoding="utf-8")
            module.generate_blocked_artifact(
                ticket_path=ticket_path,
                output_dir=output,
                target="gcp",
                raw_bundle="",
            )
            snapshot = json.loads(
                (output / "gcp-snapshot.json").read_text(encoding="utf-8")
            )
            diagnostics = json.loads(
                (output / "gcp-diagnostics.json").read_text(encoding="utf-8")
            )
            self.assertEqual(snapshot["status"], "API_GCP_BLOCKED")
            self.assertEqual(
                snapshot["failure"]["code"],
                "GOOGLE_CREDENTIALS_BUNDLE_INVALID",
            )
            self.assertIn("GOOGLE_CREDENTIALS_JSON", snapshot["failure"]["message"])
            self.assertEqual(
                diagnostics["credential_secret_name"],
                "GOOGLE_CREDENTIALS_JSON",
            )
            self.assertFalse(diagnostics["credential_secret_value_exposed"])

    def test_data_commons_missing_bundle_generates_structured_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "out"
            ticket_path = root / "ticket.json"
            ticket = self.ticket("data-commons", "resolve-place")
            ticket_path.write_text(json.dumps(ticket), encoding="utf-8")
            module.generate_blocked_artifact(
                ticket_path=ticket_path,
                output_dir=output,
                target="data-commons",
                raw_bundle="",
            )
            snapshot = json.loads(
                (output / "data-commons-snapshot.json").read_text(
                    encoding="utf-8"
                )
            )
            manifest = json.loads(
                (output / "artifact-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(snapshot["status"], "API_DATA_COMMONS_BLOCKED")
            self.assertEqual(
                snapshot["failure"]["code"],
                "GOOGLE_CREDENTIALS_BUNDLE_INVALID",
            )
            self.assertIn("data-commons-snapshot.json", manifest["files"])
            self.assertFalse(manifest["secret_values_included"])


if __name__ == "__main__":
    unittest.main()
