from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "agent_toolbelt_task", ROOT / "agent_toolbelt_task.py"
)
assert SPEC and SPEC.loader
task = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(task)

STOCK_OPERATIONS = {
    "stock-thesis",
    "earnings-analysis",
    "insider-signal",
    "valuation-snapshot",
    "bear-vs-bull",
    "compare-stocks",
    "moat-analysis",
    "watchlist-scan",
}


class FakeRaw:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def read(self, size: int, decode_content: bool = True) -> bytes:
        return self.payload[:size]


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.raw = FakeRaw(raw)
        self.status_code = status_code
        self.headers = {"Content-Type": "application/json"}
        self.is_redirect = False


class AgentToolbeltTests(unittest.TestCase):
    def ticket(self, operation="catalog-capabilities", parameters=None):
        return {
            "task_id": "agent-toolbelt-test-001",
            "provider": "agent-toolbelt",
            "operation": operation,
            "objective": "test bounded Agent Toolbelt provider",
            "parameters": parameters or {},
            "data_policy": {
                "classification": "public",
                "contains_personal_data": False,
            },
            "acceptance": {
                "timeout_seconds": 30,
                "max_response_bytes": 1_000_000,
            },
        }

    def test_catalog_and_schema_exclude_stock_research(self):
        catalog = json.loads((ROOT / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "agent-toolbelt")
        self.assertEqual(provider["required_secret_environment_variable"], "AGENT_TOOLBELT_KEY")
        self.assertEqual(len(provider["operations"]), 21)
        operation_ids = {row["operation_id"] for row in provider["operations"]}
        self.assertFalse(STOCK_OPERATIONS & operation_ids)
        self.assertIn("context-window-packer", operation_ids)
        self.assertIn("token-counter", operation_ids)
        self.assertNotIn("create-watchlist", operation_ids)
        self.assertEqual(provider["limits"]["fixed_upstream_tool_count"], 20)
        self.assertFalse(provider["limits"]["stock_research_tools_allowed"])
        self.assertFalse(provider["limits"]["us_equity_research_allowed"])
        self.assertEqual(provider["limits"]["fixed_api_host"], "www.agenttoolbelt.live")
        self.assertFalse(provider["limits"]["arbitrary_tool_names_allowed"])
        self.assertFalse(provider["limits"]["watchlist_crud_allowed"])
        self.assertFalse(provider["limits"]["write_operations_allowed"])
        self.assertFalse(provider["limits"]["trading_or_order_execution_allowed"])
        task.validate_ticket(self.ticket(), schema_path=task.SCHEMA_PATH, catalog_path=task.CATALOG_PATH)

    def test_request_builder_keeps_fixed_origin_and_no_credentials(self):
        url, encoded, metadata = task.build_request(
            "token-counter", {"text": "公开证据包", "models": ["gpt-4o"]}
        )
        self.assertEqual(url, "https://www.agenttoolbelt.live/api/tools/token-counter")
        self.assertEqual(json.loads(encoded), {"text": "公开证据包", "models": ["gpt-4o"]})
        self.assertNotIn("Authorization", metadata)
        self.assertEqual(metadata["request_origin"], "www.agenttoolbelt.live")
        self.assertEqual(metadata["http_method"], "POST")

    def test_credentials_are_backend_only_and_prefixed(self):
        with patch.dict(os.environ, {"AGENT_TOOLBELT_KEY": "atb_test_key_12345"}, clear=False):
            self.assertEqual(task.api_key(), "atb_test_key_12345")
        with patch.dict(os.environ, {"AGENT_TOOLBELT_KEY": "wrong-key"}, clear=False):
            with self.assertRaises(task.AgentToolbeltError):
                task.api_key()

    def test_url_guard_rejects_private_and_allows_public_https(self):
        for value in (
            "http://example.com",
            "https://localhost/test",
            "https://127.0.0.1/test",
            "https://10.0.0.1/test",
            "https://169.254.169.254/latest/meta-data",
            "https://user:pass@example.com/",
        ):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    task.validate_public_https_url(value)
        task.validate_public_https_url("https://example.com/path?q=1")

    def test_ticket_schema_rejects_all_stock_operations(self):
        for operation in sorted(STOCK_OPERATIONS):
            with self.subTest(operation=operation):
                with self.assertRaises(ValueError):
                    task.validate_ticket(
                        self.ticket(operation, {"ticker": "AAPL"}),
                        schema_path=task.SCHEMA_PATH,
                        catalog_path=task.CATALOG_PATH,
                    )
        with self.assertRaises(ValueError):
            task.validate_ticket(
                self.ticket("create-watchlist", {}),
                schema_path=task.SCHEMA_PATH,
                catalog_path=task.CATALOG_PATH,
            )

    def test_local_catalog_execution_needs_no_credentials(self):
        with tempfile.TemporaryDirectory() as tmp:
            ticket_path = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket_path.write_text(json.dumps(self.ticket()), encoding="utf-8")
            self.assertEqual(task.execute(ticket_path, out), 0)
            diagnostics = json.loads((out / "diagnostics.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostics["status"], "API_AGENT_TOOLBELT_COMPLETED")
            self.assertFalse(diagnostics["metadata"]["upstream_called"])

    def test_mocked_general_tool_call_succeeds_and_never_persists_key(self):
        payload = {
            "success": True,
            "tool": "token-counter",
            "result": {"characterCount": 5, "results": {"gpt-4o": {"tokens": 3}}},
        }
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ, {"AGENT_TOOLBELT_KEY": "atb_test_key_12345"}, clear=False
        ), patch.object(task.requests, "post", return_value=FakeResponse(payload)):
            ticket_path = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket_path.write_text(
                json.dumps(self.ticket("token-counter", {"text": "公开文本", "models": ["gpt-4o"]})),
                encoding="utf-8",
            )
            self.assertEqual(task.execute(ticket_path, out), 0)
            diagnostics = json.loads((out / "diagnostics.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostics["status"], "API_AGENT_TOOLBELT_COMPLETED")
            self.assertTrue(diagnostics["metadata"]["upstream_called"])
            for path in out.iterdir():
                if path.is_file():
                    self.assertNotIn(b"atb_test_key_12345", path.read_bytes())


if __name__ == "__main__":
    unittest.main()
