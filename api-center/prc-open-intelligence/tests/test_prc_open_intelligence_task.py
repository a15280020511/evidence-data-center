from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "prc_open_intelligence_task", ROOT / "prc_open_intelligence_task.py"
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class PRCOpenIntelligenceTaskTests(unittest.TestCase):
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
                "max_response_bytes": 1000000,
            },
        }

    def test_provider_operation_pairs_are_strict(self) -> None:
        ticket = self.ticket("sinofacts", "company-snapshot", {"query": "Huawei"})
        with self.assertRaises(ValueError):
            module.validate_ticket(ticket)

    def test_paid_and_personal_fields_are_removed(self) -> None:
        payload = {
            "companyName": "示例公司",
            "creditCode": "9135",
            "legalRepresentative": "张三",
            "phone": "123",
            "purchase_url": "https://paid.invalid",
            "nested": {"staffSize": 20, "value": 1},
        }
        self.assertEqual(
            module.sanitize_company_payload(payload),
            {
                "companyName": "示例公司",
                "creditCode": "9135",
                "nested": {"value": 1},
            },
        )

    def test_sse_json_parser(self) -> None:
        parsed = module._parse_json_or_sse(
            b"event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"ok\":true}}\n\n"
        )
        self.assertTrue(parsed["result"]["ok"])

    def test_http_403_is_hard_stop(self) -> None:
        headers = {"Content-Type": "text/plain"}
        error = urllib.error.HTTPError(
            module.CHINA_CHECK_ENDPOINT,
            403,
            "Forbidden",
            headers,
            io.BytesIO(b"Forbidden"),
        )
        with mock.patch.object(module.urllib.request, "urlopen", side_effect=error):
            with self.assertRaises(module.ProviderStop) as ctx:
                module._http_bytes(
                    module.CHINA_CHECK_ENDPOINT,
                    timeout=5,
                    max_bytes=1000,
                )
        self.assertEqual(ctx.exception.code, "AUTHORIZATION_DENIED")
        self.assertFalse(ctx.exception.retryable)

    def test_sinofacts_search_is_bounded(self) -> None:
        fake = {
            "source": "SinoFacts",
            "license": "CC BY 4.0 — attribution required",
            "count": 3,
            "generated_at": "2026-08-06T00:00:00Z",
            "companies": [
                {"slug": "a", "domain": "a.cn", "name_en": "Alpha", "name_zh": "阿尔法"},
                {"slug": "b", "domain": "b.cn", "name_en": "Alpha Two", "name_zh": "阿尔法二"},
                {"slug": "c", "domain": "c.cn", "name_en": "Alpha Three", "name_zh": "阿尔法三"},
            ],
        }
        with mock.patch.object(
            module,
            "_fetch_json",
            return_value=(fake, {"http_status": 200}),
        ):
            data, metadata = module._sinofacts_search(
                {"query": "Alpha", "max_results": 2}, 10, 100000
            )
        self.assertEqual(len(data["matches"]), 2)
        self.assertEqual(metadata["license"], "CC BY 4.0")
        self.assertFalse(metadata["full_database_mirrored"])

    def test_china_check_uses_only_published_tool(self) -> None:
        tool_reply = {
            "jsonrpc": "2.0",
            "id": 3,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "companies": [
                                    {
                                        "nameZh": "示例公司",
                                        "registrationNo": "9135",
                                        "legalPersonName": "张三",
                                    }
                                ]
                            },
                            ensure_ascii=False,
                        ),
                    }
                ]
            },
        }
        with mock.patch.object(
            module,
            "_mcp_initialize",
            return_value=(
                "session",
                {"search_chinese_company", "get_company_snapshot"},
                [{"http_status": 200}],
            ),
        ), mock.patch.object(
            module,
            "_mcp_post",
            return_value=(tool_reply, {"http_status": 200, "request_origin": "www.china-check.com", "request_path": "/api/mcp/mcp"}),
        ) as post:
            data, metadata = module._china_check(
                "company-search", {"query": "示例", "language": "zh"}, 10, 100000
            )
        self.assertEqual(post.call_args.args[0]["params"]["name"], "search_chinese_company")
        self.assertNotIn("legalPersonName", data["companies"][0])
        self.assertEqual(metadata["auth"], "none")
        self.assertFalse(metadata["paid_upgrade_used"])

    def test_catalog_operation_needs_no_secret(self) -> None:
        ticket = self.ticket("sinofacts", "catalog-capabilities", {})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            ticket_path.write_text(json.dumps(ticket, ensure_ascii=False), encoding="utf-8")
            rc = module.execute(ticket_path, root / "out")
            self.assertEqual(rc, 0)
            snapshot = json.loads(
                (root / "out/prc-open-snapshot.json").read_text(encoding="utf-8")
            )
            self.assertEqual(snapshot["status"], "API_PRC_OPEN_COMPLETED")
            self.assertFalse(snapshot["security"]["secret_values_included"])
            self.assertFalse(snapshot["security"]["proxy_rotation_allowed"])


if __name__ == "__main__":
    unittest.main()
