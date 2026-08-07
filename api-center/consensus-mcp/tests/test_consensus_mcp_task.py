from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import consensus_mcp_task as task  # noqa: E402


class ConsensusMcpTests(unittest.TestCase):
    def sample_ticket(self) -> dict:
        return {
            "task_id": "consensus-test-001",
            "provider": "consensus-mcp",
            "operation": "search",
            "objective": "test search",
            "parameters": {
                "query": "causal inference",
                "year_min": 2020,
                "year_max": 2026,
                "exclude_preprints": True,
            },
            "data_policy": {
                "classification": "public",
                "contains_personal_data": False,
            },
            "acceptance": {
                "timeout_seconds": 30,
                "max_response_bytes": 1000000,
                "max_rows": 3,
            },
        }

    def test_catalog_is_fixed_read_only_oauth_bridge(self) -> None:
        provider = task.provider_catalog()
        self.assertEqual(provider["provider_id"], "consensus-mcp")
        self.assertEqual(provider["official_endpoint"], "https://mcp.consensus.app/mcp")
        self.assertEqual(provider["runtime_status"], "oauth-bridge-ready-awaiting-secret")
        self.assertFalse(provider["production_search_ready"])
        self.assertIsNone(provider["required_secret_environment_variable"])
        self.assertIn("CONSENSUS_MCP_REFRESH_TOKEN", provider["optional_secret_environment_variables"])
        self.assertIn("CONSENSUS_MCP_BEARER_TOKEN", provider["optional_secret_environment_variables"])
        self.assertTrue(provider["authentication"]["resource_requires_bearer"])
        self.assertEqual(provider["authentication"]["verified_unauthenticated_http_status"], 401)
        self.assertTrue(provider["authentication"]["authorization_code_supported"])
        self.assertTrue(provider["authentication"]["refresh_token_supported"])
        self.assertFalse(provider["authentication"]["client_credentials_supported"])
        self.assertEqual(provider["authentication"]["token_endpoint_auth_method"], "none")
        self.assertEqual(provider["authentication"]["pkce_method"], "S256")
        self.assertEqual(provider["authentication"]["public_client_id"], "ee123d14-833d-428c-bc28-e796c2e4b25f")
        self.assertEqual(provider["authentication"]["refresh_secret"], "CONSENSUS_MCP_REFRESH_TOKEN")
        self.assertFalse(provider["limits"]["arbitrary_jsonrpc_methods_allowed"])
        self.assertFalse(provider["limits"]["arbitrary_mcp_tool_names_allowed"])
        self.assertFalse(provider["limits"]["write_operations_allowed"])
        self.assertFalse(provider["limits"]["web_scraping_allowed"])
        remote_tools = {
            row.get("execution", {}).get("mcp_tool_name")
            for row in provider["operations"]
            if row.get("execution", {}).get("mcp_tool_name")
        }
        self.assertEqual(remote_tools, {"search"})
        remote_ops = [row for row in provider["operations"] if not row.get("execution", {}).get("local")]
        self.assertTrue(all(row["credential_mode"] == "oauth-bearer-or-refresh-bridge" for row in remote_ops))

    def test_ticket_validation(self) -> None:
        ticket = self.sample_ticket()
        task.validate_ticket(ticket)
        ticket["parameters"]["year_min"] = 2027
        ticket["parameters"]["year_max"] = 2026
        with self.assertRaisesRegex(ValueError, "year_min"):
            task.validate_ticket(ticket)

    def test_unknown_operation_rejected(self) -> None:
        ticket = self.sample_ticket()
        ticket["operation"] = "arbitrary-tool"
        with self.assertRaises(ValueError):
            task.validate_ticket(ticket)

    def test_sse_payload_parser(self) -> None:
        payload = b'event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"ok":true}}\n\n'
        parsed = task.parse_mcp_payload(payload, "text/event-stream")
        self.assertTrue(parsed["result"]["ok"])

    def test_extract_and_cap_papers(self) -> None:
        result = {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({"papers": [{"title": "a"}, {"title": "b"}, {"title": "c"}]})
                }
            ]
        }
        structured = task.extract_structured_result(result)
        capped = task.truncate_papers(structured, 2)
        self.assertEqual(len(capped["papers"]), 2)
        self.assertEqual(capped["returned_papers_after_local_cap"], 2)


if __name__ == "__main__":
    unittest.main()
