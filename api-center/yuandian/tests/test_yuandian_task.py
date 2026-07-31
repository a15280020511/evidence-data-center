from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("yuandian_task_tests", ROOT / "yuandian_task.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class YuanDianTaskTests(unittest.TestCase):
    def ticket(self, operation="catalog-capabilities", parameters=None):
        return {
            "task_id": "yuandian-test-0001",
            "provider": "yuandian-law",
            "operation": operation,
            "objective": "validate maximum-safe YuanDian legal data access",
            "parameters": parameters or {},
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "acceptance": {"timeout_seconds": 30, "max_response_bytes": 500000},
        }

    def test_catalog_registers_all_frozen_readonly_apis(self):
        module.validate_ticket(self.ticket())
        provider = module.PROVIDER
        self.assertEqual(provider["discovered_readonly_tool_count"], 37)
        self.assertEqual(len(module.SNAPSHOT["apis"]), 37)
        self.assertEqual(len(provider["operations"]), 40)
        self.assertEqual(
            provider["discovered_readonly_tools_by_server"],
            {"法律法规": 5, "案例文书": 4, "企业信息": 27, "幻觉检测": 1},
        )
        self.assertFalse(provider["limits"]["arbitrary_urls_allowed"])
        self.assertFalse(provider["limits"]["write_operations_allowed"])
        self.assertFalse(provider["limits"]["secret_values_exposed"])

    def test_unknown_operation_and_request_control_fields_are_rejected(self):
        bad = self.ticket(); bad["operation"] = "arbitrary-endpoint"
        with self.assertRaisesRegex(ValueError, "unsupported"):
            module.validate_ticket(bad)
        with self.assertRaisesRegex(ValueError, "forbidden"):
            module.validate_ticket(self.ticket("yuandian-rh-fg-search", {
                "arguments": {"url": "https://example.com"}
            }))
        with self.assertRaisesRegex(ValueError, "unsafe argument"):
            module.validate_ticket(self.ticket("yuandian-rh-fg-search", {
                "arguments": {"bad key": "x"}
            }))

    def test_only_canonical_yuandian_secret_is_accepted(self):
        with mock.patch.dict(os.environ, {"YUANDIAN_API_KEY": "canonical-key"}, clear=True):
            self.assertEqual(module._resolve_api_key(), "canonical-key")
        with mock.patch.dict(os.environ, {"YD" + "_API_KEY": "legacy-key"}, clear=True):
            self.assertEqual(module._resolve_api_key(), "")

    def test_fixed_operation_uses_fixed_origin_header_and_redacts_direct_identifiers(self):
        payload = {
            "code": 200,
            "status": "success",
            "data": {
                "联系电话": "13800138000",
                "email": "person@example.com",
                "身份证号": "110101199001011234",
                "name": "示例公司",
            },
        }
        captured = {}

        def fake_request(method, url, *, api_key="", arguments=None, timeout=0, max_bytes=0):
            captured.update({
                "method": method, "url": url, "api_key": api_key,
                "arguments": arguments, "timeout": timeout, "max_bytes": max_bytes,
            })
            return payload

        with mock.patch.dict(os.environ, {"YUANDIAN_API_KEY": "secret-value"}, clear=False), \
             mock.patch.object(module, "_request_json", side_effect=fake_request):
            result = module._execute_operation("yuandian-rh-company-info", {
                "arguments": {"name": "贵州茅台", "num": 2},
                "timeout_seconds": 20,
                "max_response_bytes": 200000,
            })
        self.assertEqual(captured["method"], "GET")
        self.assertEqual(captured["url"], "https://open.chineselaw.com/open/rh_company_info")
        self.assertEqual(captured["api_key"], "secret-value")
        self.assertNotIn("secret-value", json.dumps(result, ensure_ascii=False))
        self.assertEqual(result["response"]["data"]["联系电话"], "[REDACTED]")
        self.assertEqual(result["response"]["data"]["email"], "[REDACTED]")
        self.assertEqual(result["response"]["data"]["身份证号"], "[REDACTED]")

    def test_generic_invoke_requires_current_official_catalog_membership(self):
        live = [{
            "route_key": "future_readonly_api", "http_method": "POST",
            "name": "future", "read_only": True,
        }]
        with mock.patch.object(module, "fetch_live_catalog", return_value=live), \
             mock.patch.object(module, "_resolve_api_key", return_value="key"), \
             mock.patch.object(module, "_request_json", return_value={"code": 200, "data": {"ok": True}}) as call:
            result = module._execute_operation("invoke-readonly-api", {
                "route_key": "future_readonly_api", "arguments": {"query": "test"}
            })
        self.assertTrue(result["upstream_called"])
        call.assert_called_once()
        with mock.patch.object(module, "fetch_live_catalog", return_value=live):
            with self.assertRaisesRegex(ValueError, "not present"):
                module._execute_operation("invoke-readonly-api", {
                    "route_key": "unlisted_api", "arguments": {}
                })

    def test_live_catalog_normalizes_only_safe_get_post_routes(self):
        payload = {"data": {"records": [
            {"id": 1, "name": "A", "categoryName": "法律法规", "routeKey": "safe_api", "httpMethod": "POST"},
            {"id": 2, "name": "B", "routeKey": "unsafe/path", "httpMethod": "GET"},
            {"id": 3, "name": "C", "routeKey": "write_api", "httpMethod": "DELETE"},
        ]}}
        with mock.patch.object(module, "_request_json", return_value=payload):
            rows = module.fetch_live_catalog()
        self.assertEqual([row["route_key"] for row in rows], ["safe_api"])

    def test_execute_local_catalog_needs_no_network_or_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            output = root / "out"
            ticket_path.write_text(json.dumps(self.ticket()), encoding="utf-8")
            with mock.patch.object(module, "_request_json", side_effect=AssertionError("network not allowed")):
                self.assertEqual(module.execute(ticket_path, output), 0)
            snapshot = json.loads((output / "yuandian-snapshot.json").read_text(encoding="utf-8"))
            manifest = json.loads((output / "artifact-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(snapshot["status"], "API_YUANDIAN_COMPLETED")
            self.assertEqual(snapshot["data"]["readonly_api_snapshot"]["documented_api_count"], 37)
            self.assertTrue(manifest["files"])
            self.assertFalse(snapshot["security"]["arbitrary_urls_allowed"])

    def test_business_error_code_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "business code 401"):
            module._business_success({"code": 401, "message": "invalid key"})


if __name__ == "__main__":
    unittest.main()
