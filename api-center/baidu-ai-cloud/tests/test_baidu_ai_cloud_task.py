from __future__ import annotations

import base64
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "baidu_ai_cloud_task_tests",
    ROOT / "baidu_ai_cloud_task.py",
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class FakeResponse:
    def __init__(self, payload=None, status_code=200, sse_lines=None):
        self.content = json.dumps(payload or {}, ensure_ascii=False).encode("utf-8")
        self.status_code = status_code
        self.headers = {"Content-Type": "application/json"}
        self.is_redirect = 300 <= status_code < 400
        self._sse_lines = sse_lines or []

    def iter_lines(self, decode_unicode=False):
        del decode_unicode
        yield from self._sse_lines


class BaiduAICloudTaskTests(unittest.TestCase):
    def ticket(self, operation="catalog-capabilities", parameters=None):
        return {
            "task_id": "baidu-ai-test-0001",
            "provider": "baidu-ai-cloud",
            "operation": operation,
            "objective": "validate bounded Baidu AI Cloud free-quota access",
            "parameters": parameters or {},
            "data_policy": {
                "classification": "public",
                "contains_personal_data": False,
                "contains_confidential_data": False,
            },
            "acceptance": {
                "timeout_seconds": 30,
                "max_response_bytes": 500000,
                "max_rows": 20,
            },
        }

    def test_catalog_registers_41_safe_operations(self):
        module.validate_ticket(
            self.ticket(),
            schema_path=module.SCHEMA_PATH,
            catalog_path=module.CATALOG_PATH,
        )
        provider = module.provider_row(module.CATALOG_PATH)
        operations = provider["operations"]
        self.assertEqual(len(operations), 41)
        operation_ids = {row["operation_id"] for row in operations}
        self.assertIn("deep-search", operation_ids)
        self.assertIn("deep-research-lite", operation_ids)
        self.assertIn("nlp-short-similarity", operation_ids)
        self.assertIn("ocr-table-v2", operation_ids)
        self.assertIn("image-general-scene", operation_ids)
        limits = provider["limits"]
        self.assertEqual(limits["requests_per_ticket_max"], 1)
        self.assertEqual(limits["max_deep_search_queries"], 3)
        self.assertFalse(limits["paid_fallback_authorized"])
        self.assertFalse(limits["face_or_biometric_operations_allowed"])
        self.assertFalse(limits["identity_document_ocr_allowed"])
        self.assertFalse(limits["speech_operations_allowed"])
        self.assertFalse(limits["write_operations_allowed"])

    def test_gated_search_requires_free_quota_confirmation(self):
        with self.assertRaises(module.BaiduAICloudError) as ctx:
            module._intelligent_search_body(
                "deep-search",
                {
                    "query": "研究福建制造业",
                    "model": "deepseek-v4-flash",
                    "paid_fallback_authorized": False,
                },
            )
        self.assertEqual(ctx.exception.code, "BAIDU_FREE_QUOTA_NOT_CONFIRMED")

    def test_deep_search_is_bounded_to_three_subqueries(self):
        body = module._intelligent_search_body(
            "deep-search",
            {
                "query": "研究福建制造业",
                "model": "deepseek-v4-flash",
                "top_k": 5,
                "max_search_query_num": 3,
                "free_quota_confirmed": True,
                "paid_fallback_authorized": False,
            },
        )
        self.assertTrue(body["enable_deep_search"])
        self.assertEqual(body["max_search_query_num"], 3)
        self.assertFalse(body["stream"])
        self.assertFalse(body["enable_followup_query"])

    def test_web_search_uses_fixed_host_and_unified_bearer(self):
        captured = {}

        def fake_post(url, **kwargs):
            captured["url"] = url
            captured.update(kwargs)
            return FakeResponse(
                {
                    "request_id": "r1",
                    "references": [
                        {
                            "title": "公开资料",
                            "url": "https://example.com/a",
                            "content": "联系电话13800138000，邮箱person@example.com",
                        }
                    ],
                }
            )

        with mock.patch.dict(
            os.environ,
            {module.API_KEY_ENV: "backend-unified-key"},
            clear=True,
        ), mock.patch.object(module.requests, "post", side_effect=fake_post):
            payload, metadata = module._post(
                "web-search",
                {"query": "福建经济数据", "top_k": 5},
                timeout=20,
                max_bytes=500000,
            )
        self.assertEqual(
            captured["url"],
            "https://qianfan.baidubce.com/v2/ai_search/web_search",
        )
        self.assertEqual(
            captured["headers"]["Authorization"],
            "Bearer backend-unified-key",
        )
        self.assertNotIn(
            "backend-unified-key",
            json.dumps(module._redact(payload), ensure_ascii=False),
        )
        self.assertEqual(metadata["requests_per_ticket"], 1)
        redacted = module._redact(payload)
        self.assertIn("[REDACTED_PHONE]", redacted["references"][0]["content"])
        self.assertIn("[REDACTED_EMAIL]", redacted["references"][0]["content"])

    def test_form_operation_uses_image_not_remote_url(self):
        image = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"x" * 64).decode()
        body = module._form_body(
            {
                "image_base64": image,
                "detect_direction": True,
            }
        )
        self.assertEqual(body["image"], image)
        self.assertEqual(body["detect_direction"], "true")
        self.assertNotIn("url", body)

    def test_sse_deep_research_is_bounded_and_no_followup(self):
        response = FakeResponse(
            sse_lines=[
                b'data: {"status":"running","conversation_id":"c1"}',
                b'data: {"status":"interrupt","interrupt_id":"i1"}',
                b"data: [DONE]",
            ]
        )
        payload = module._parse_sse(response, max_bytes=500000)
        self.assertEqual(payload["event_count"], 2)
        self.assertTrue(payload["interrupt_returned"])
        self.assertFalse(payload["completed_in_single_request"])

    def test_quota_and_catalog_local_execution_need_no_network_or_secret(self):
        for operation in ("catalog-capabilities", "quota-policy"):
            with self.subTest(operation=operation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                ticket_path = root / "ticket.json"
                output = root / "out"
                ticket_path.write_text(
                    json.dumps(self.ticket(operation), ensure_ascii=False),
                    encoding="utf-8",
                )
                with mock.patch.object(
                    module.requests,
                    "post",
                    side_effect=AssertionError("network not allowed"),
                ):
                    self.assertEqual(module.execute(ticket_path, output), 0)
                diagnostics = json.loads(
                    (output / "diagnostics.json").read_text(encoding="utf-8")
                )
                self.assertEqual(
                    diagnostics["status"],
                    "INTEL_BAIDU_AI_COMPLETED",
                )
                self.assertFalse(diagnostics["secret_values_exposed"])

    def test_business_quota_error_fails_closed(self):
        response = FakeResponse(
            {"error_code": 17, "error_msg": "Open api daily request limit reached"}
        )
        payload = module._decode_json(response, max_bytes=500000)
        with self.assertRaises(module.BaiduAICloudError) as ctx:
            module._check_http(response, payload)
        self.assertEqual(
            ctx.exception.code,
            "BAIDU_FREE_QUOTA_OR_RATE_LIMIT_REACHED",
        )

    def test_schema_rejects_paid_fallback_true(self):
        ticket = self.ticket(
            "web-summary",
            {
                "query": "政策",
                "free_quota_confirmed": True,
                "paid_fallback_authorized": True,
            },
        )
        with self.assertRaises(Exception):
            module.validate_ticket(
                ticket,
                schema_path=module.SCHEMA_PATH,
                catalog_path=module.CATALOG_PATH,
            )


if __name__ == "__main__":
    unittest.main()
