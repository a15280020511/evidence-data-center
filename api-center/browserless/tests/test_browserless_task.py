from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("browserless_task", HERE / "browserless_task.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def ticket(operation: str, parameters: dict) -> dict:
    return {
        "task_id": "browserless-test-001",
        "provider": "browserless",
        "operation": operation,
        "objective": "test bounded Browserless provider",
        "parameters": parameters,
        "data_policy": {"classification": "public", "contains_personal_data": False},
        "acceptance": {"timeout_seconds": 30, "max_response_bytes": 1000000},
    }


class BrowserlessTaskTests(unittest.TestCase):
    def test_catalog_contains_expected_safe_operations(self) -> None:
        provider = module.provider_catalog()
        self.assertEqual(provider["required_secret_environment_variable"], "BROWSERLESS_TOKEN")
        self.assertEqual({row["operation_id"] for row in provider["operations"]}, {"catalog-capabilities", "content", "scrape", "screenshot", "pdf", "performance", "search", "map"})
        self.assertFalse(provider["limits"]["arbitrary_code_allowed"])
        self.assertFalse(provider["limits"]["captcha_or_unblock_allowed"])
        self.assertFalse(provider["limits"]["profiles_allowed"])

    @mock.patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("93.184.216.34", 443))])
    def test_public_https_url_is_normalized(self, _resolver: mock.Mock) -> None:
        self.assertEqual(module.validate_public_https_url("https://example.com"), "https://example.com/")

    def test_private_and_credential_urls_are_rejected(self) -> None:
        for value in ("http://example.com", "https://127.0.0.1/", "https://user:pass@example.com/"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                module.validate_public_https_url(value)

    def test_unknown_parameter_is_rejected_by_operation_schema(self) -> None:
        value = ticket("content", {"url": "https://example.com", "headers": {"x": "y"}})
        with self.assertRaises(ValueError):
            module.validate_ticket(value)

    def test_binary_result_is_written_as_artifact_not_json_payload(self) -> None:
        value = ticket("screenshot", {"url": "https://example.com", "image_type": "png"})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            ticket_path.write_text(json.dumps(value), encoding="utf-8")
            with mock.patch.object(module, "validate_public_https_url", return_value="https://example.com/"), mock.patch.object(module, "call_upstream", return_value=(200, b"\x89PNG\r\n", "image/png")):
                self.assertEqual(module.execute(ticket_path, root), 0)
            snapshot = json.loads((root / "snapshot.json").read_text(encoding="utf-8"))
            self.assertEqual(snapshot["artifact_file"], "result.png")
            self.assertTrue((root / "result.png").is_file())
            self.assertNotIn("content", snapshot)

    def test_catalog_execution_succeeds_without_secret(self) -> None:
        value = ticket("catalog-capabilities", {})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            ticket_path.write_text(json.dumps(value), encoding="utf-8")
            with mock.patch.dict("os.environ", {}, clear=True):
                self.assertEqual(module.execute(ticket_path, root), 0)
            diagnostics = json.loads((root / "diagnostics.json").read_text(encoding="utf-8"))
            manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostics["status"], "API_BROWSERLESS_COMPLETED")
            self.assertEqual(manifest["status"], "API_BROWSERLESS_COMPLETED")
            self.assertFalse(diagnostics["metadata"]["upstream_called"])
            self.assertEqual(diagnostics["metadata"]["credential_mode"], "none")
            self.assertIsNone(diagnostics["failure"])

    def test_missing_secret_fails_without_exposing_value(self) -> None:
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "BROWSERLESS_TOKEN"):
                module.token()


if __name__ == "__main__":
    unittest.main()
