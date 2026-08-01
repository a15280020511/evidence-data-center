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
    "miaoxiang_mcp_task", ROOT / "miaoxiang_mcp_task.py"
)
assert SPEC and SPEC.loader
mx = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mx)


class MiaoxiangMcpTaskTests(unittest.TestCase):
    def ticket(self, operation: str = "ashare-finance-data", parameters=None) -> dict:
        if parameters is None:
            parameters = (
                {}
                if operation in {"catalog-capabilities", "mcp-tools-list"}
                else {"query": "贵州茅台最新价"}
            )
        return {
            "task_id": "mx-mcp-test-001",
            "provider": "miaoxiang-mcp",
            "operation": operation,
            "objective": "test managed read-only MCP execution",
            "parameters": parameters,
            "data_policy": {
                "classification": "public",
                "contains_personal_data": False,
            },
            "acceptance": {
                "timeout_seconds": 30,
                "max_response_bytes": 500000,
                "max_rows": 100,
            },
        }

    def test_catalog_registers_exact_fixed_readonly_surface(self) -> None:
        catalog = json.loads(
            (ROOT / "provider-catalog.json").read_text(encoding="utf-8")
        )
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "miaoxiang-mcp")
        self.assertEqual(
            provider["required_secret_environment_variable"], "EM_API_KEY"
        )
        self.assertEqual(
            provider["official_endpoint"],
            "https://mxapi.eastmoney.com/mxds/mcp",
        )
        self.assertEqual(provider["mcp_protocol_version"], "2025-11-25")
        self.assertEqual(len(provider["operations"]), 13)
        tool_names = {
            row.get("mcp_tool_name")
            for row in provider["operations"]
            if row.get("mcp_tool_name")
        }
        self.assertEqual(
            tool_names,
            {
                "mx_us_finance_data",
                "mx_hk_finance_data",
                "mx_comprehensive_finance_data",
                "mx_macro_data",
                "mx_stocks_screener",
                "mx_finance_search_news",
                "mx_finance_search_notice",
                "mx_ashare_finance_data",
                "mx_fund_finance_data",
                "mx_bond_finance_data",
                "mx_index_block_finance_data",
            },
        )
        limits = provider["limits"]
        self.assertEqual(limits["fixed_mcp_tool_count"], 11)
        self.assertFalse(limits["arbitrary_jsonrpc_methods_allowed"])
        self.assertFalse(limits["arbitrary_mcp_tool_names_allowed"])
        self.assertFalse(limits["write_operations_allowed"])
        self.assertFalse(limits["trading_or_order_execution_allowed"])

    def test_validates_operation_specific_parameters(self) -> None:
        mx.validate_ticket(self.ticket())
        mx.validate_ticket(self.ticket("mcp-tools-list"))
        with self.assertRaises(ValueError):
            mx.validate_ticket(
                self.ticket(parameters={"query": "x", "tool": "anything"})
            )
        with self.assertRaises(ValueError):
            mx.validate_ticket(self.ticket(parameters={"query": "x" * 501}))

    def test_prepare_accepts_only_managed_prefix_and_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            event = root / "event.json"
            output = root / "out"
            event.write_text(
                json.dumps(
                    {
                        "issue": {
                            "title": "[api-mx-mcp] test",
                            "body": json.dumps(self.ticket()),
                        }
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(mx.prepare(event, output), 0)
            status = json.loads(
                (output / "ticket-status.json").read_text(encoding="utf-8")
            )
            self.assertTrue(status["accepted"])
            self.assertFalse(status["secret_values_exposed"])

    def test_api_key_requires_independent_em_prefix(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(mx.MiaoxiangMcpError) as caught:
                mx.api_key()
            self.assertEqual(
                caught.exception.code,
                "MIAOXIANG_MCP_API_KEY_MISSING",
            )
        with patch.dict(os.environ, {"EM_API_KEY": "mkt_wrong"}, clear=True):
            with self.assertRaises(mx.MiaoxiangMcpError) as caught:
                mx.api_key()
            self.assertEqual(
                caught.exception.code,
                "MIAOXIANG_MCP_API_KEY_FORMAT_INVALID",
            )
        with patch.dict(os.environ, {"EM_API_KEY": "em_valid"}, clear=True):
            self.assertEqual(mx.api_key(), "em_valid")

    def test_parses_plain_json_and_sse(self) -> None:
        plain = mx.parse_mcp_payload(
            b'{"jsonrpc":"2.0","id":1,"result":{}}',
            "application/json",
        )
        self.assertEqual(plain["id"], 1)
        sse = mx.parse_mcp_payload(
            b'event: message\ndata: {"jsonrpc":"2.0","id":2,"result":{"tools":[]}}\n\n',
            "text/event-stream",
        )
        self.assertEqual(sse["id"], 2)

    def test_remote_tool_call_uses_fixed_protocol_sequence(self) -> None:
        responses = [
            (
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": {
                        "protocolVersion": "2025-11-25",
                        "serverInfo": {
                            "name": "mx-ds-mcp",
                            "version": "1.0.0",
                        },
                        "capabilities": {"tools": {}},
                    },
                },
                {"http_status": 200},
                None,
            ),
            ({}, {"http_status": 200}, None),
            (
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "result": {
                        "content": [{"type": "text", "text": "ok"}],
                        "isError": False,
                    },
                },
                {"http_status": 200},
                None,
            ),
        ]
        with patch.object(mx, "mcp_post", side_effect=responses) as mocked:
            result, metadata = mx.remote_tool_call(
                "mx_ashare_finance_data",
                {"query": "贵州茅台最新价"},
                key="em_test",
                timeout=30,
                max_bytes=500000,
            )
        self.assertEqual(result["content"][0]["text"], "ok")
        self.assertEqual(metadata["request_count"], 3)
        self.assertEqual(
            metadata["mcp_tool_name"],
            "mx_ashare_finance_data",
        )
        self.assertEqual(mocked.call_args_list[0].args[0]["method"], "initialize")
        self.assertEqual(
            mocked.call_args_list[1].args[0]["method"],
            "notifications/initialized",
        )
        self.assertEqual(mocked.call_args_list[2].args[0]["method"], "tools/call")

    def test_execute_blocks_missing_key_without_leakage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {},
            clear=True,
        ):
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            output = root / "out"
            ticket_path.write_text(json.dumps(self.ticket()), encoding="utf-8")
            self.assertEqual(mx.execute(ticket_path, output), 1)
            diagnostics = json.loads(
                (output / "miaoxiang-mcp-diagnostics.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                diagnostics["status"],
                "API_MIAOXIANG_MCP_BLOCKED",
            )
            self.assertEqual(
                diagnostics["error"]["code"],
                "MIAOXIANG_MCP_API_KEY_MISSING",
            )

    def test_execute_success_redacts_accidental_key_echo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {"EM_API_KEY": "em_secret_value"},
            clear=True,
        ):
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            output = root / "out"
            ticket_path.write_text(json.dumps(self.ticket()), encoding="utf-8")
            fake_result = {
                "content": [
                    {"type": "text", "text": "result em_secret_value"}
                ],
                "isError": False,
            }
            fake_meta = {
                "upstream_called": True,
                "protocol_version": "2025-11-25",
                "mcp_tool_name": "mx_ashare_finance_data",
            }
            with patch.object(
                mx,
                "remote_tool_call",
                return_value=(fake_result, fake_meta),
            ):
                self.assertEqual(mx.execute(ticket_path, output), 0)
            text = (output / "miaoxiang-mcp-snapshot.json").read_text(
                encoding="utf-8"
            )
            self.assertNotIn("em_secret_value", text)
            self.assertIn("[REDACTED]", text)
            snapshot = json.loads(text)
            self.assertEqual(
                snapshot["status"],
                "API_MIAOXIANG_MCP_COMPLETED",
            )
            self.assertFalse(snapshot["security"]["secret_values_exposed"])


if __name__ == "__main__":
    unittest.main()
