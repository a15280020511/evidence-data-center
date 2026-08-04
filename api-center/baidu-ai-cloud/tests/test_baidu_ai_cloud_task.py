from __future__ import annotations

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
    def __init__(self, payload=None, status_code=200):
        self.content = json.dumps(payload or {}, ensure_ascii=False).encode("utf-8")
        self.status_code = status_code
        self.headers = {"Content-Type": "application/json"}
        self.is_redirect = 300 <= status_code < 400


class BaiduAICloudTaskTests(unittest.TestCase):
    def ticket(self, operation="catalog-capabilities", parameters=None):
        return {
            "task_id": "baidu-ai-test-0001",
            "provider": "baidu-ai-cloud",
            "operation": operation,
            "objective": "validate bounded Baidu web search",
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

    def test_catalog_registers_eight_verified_operations(self):
        module.validate_ticket(
            self.ticket(),
            schema_path=module.SCHEMA_PATH,
            catalog_path=module.CATALOG_PATH,
        )
        provider = module.provider_row(module.CATALOG_PATH)
        operation_ids = {
            row["operation_id"] for row in provider["operations"]
        }
        self.assertEqual(
            operation_ids,
            {"catalog-capabilities", "quota-policy", "web-search", "web-summary", "baike-lemma-list", "baike-lemma-content", "baike-starmap-list", "baike-starmap-detail"},
        )
        self.assertEqual(len(provider["operations"]), 8)
        limits = provider["limits"]
        self.assertEqual(limits["fixed_api_hosts"], ["qianfan.baidubce.com", "appbuilder.baidu.com"])
        self.assertEqual(limits["fixed_paths"], ["/v2/ai_search/web_search", "/v2/ai_search/web_summary", "/v2/baike/lemma/get_list_by_title", "/v2/baike/lemma/get_content", "/v2/tools/baike/starmap/get_starmap_by_title", "/v2/tools/baike/starmap/get_starmap_by_id"])
        self.assertFalse(limits["paid_fallback_authorized"])
        self.assertFalse(limits["generative_model_chat_allowed"])
        self.assertFalse(limits["nlp_operations_allowed"])
        self.assertFalse(limits["ocr_operations_allowed"])
        self.assertFalse(limits["image_recognition_operations_allowed"])

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
            payload, metadata = module._post_web_search(
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
        self.assertFalse(captured["allow_redirects"])
        self.assertNotIn(
            "backend-unified-key",
            json.dumps(module._redact(payload), ensure_ascii=False),
        )
        self.assertEqual(metadata["requests_per_ticket"], 1)
        redacted = module._redact(payload)
        self.assertIn("[REDACTED_PHONE]", redacted["references"][0]["content"])
        self.assertIn("[REDACTED_EMAIL]", redacted["references"][0]["content"])


    def test_web_summary_uses_fixed_endpoint_and_counts_one_model_call(self):
        captured = {}

        def fake_post(url, **kwargs):
            captured["url"] = url
            captured.update(kwargs)
            return FakeResponse(
                {
                    "request_id": "r-summary",
                    "choices": [{"message": {"role": "assistant", "content": "公开资料摘要"}}],
                    "references": [{"title": "来源", "url": "https://example.com/source"}],
                }
            )

        with mock.patch.dict(
            os.environ,
            {module.API_KEY_ENV: "backend-unified-key"},
            clear=True,
        ), mock.patch.object(module.requests, "post", side_effect=fake_post):
            payload, metadata = module._post_web_summary(
                {"query": "福建经济数据", "top_k": 3},
                timeout=20,
                max_bytes=500000,
            )
        self.assertEqual(
            captured["url"],
            "https://qianfan.baidubce.com/v2/ai_search/web_summary",
        )
        self.assertEqual(captured["headers"]["Authorization"], "Bearer backend-unified-key")
        self.assertFalse(captured["allow_redirects"])
        self.assertFalse(captured["json"]["stream"])
        self.assertEqual(metadata["requests_per_ticket"], 1)
        self.assertEqual(metadata["model_calls"], 1)
        self.assertIn("choices", payload)

    def test_baike_operations_use_fixed_get_endpoints_without_model_calls(self):
        captured = []

        def fake_get(url, **kwargs):
            captured.append((url, kwargs))
            if url.endswith("get_list_by_title"):
                return FakeResponse({"code": "0", "result": [{"lemma_id": 1, "lemma_title": "福州"}]})
            if url.endswith("get_content"):
                return FakeResponse({"code": "0", "result": {"lemma_id": 1, "lemma_title": "福州"}})
            if url.endswith("get_starmap_by_title"):
                return FakeResponse({"code": "0", "list": [{"encodeId": "abc", "name": "节日"}]})
            return FakeResponse({"code": "0", "list": [{"lemmaId": 1}]})

        cases = [
            ("baike-lemma-list", {"lemma_title": "福州", "top_k": 3}),
            ("baike-lemma-content", {"search_type": "lemmaTitle", "search_key": "福州"}),
            ("baike-starmap-list", {"starmap_title": "节日", "page": 1}),
            ("baike-starmap-detail", {"starmap_id": "abc", "page": 1}),
        ]
        with mock.patch.dict(os.environ, {module.API_KEY_ENV: "backend-unified-key"}, clear=True), mock.patch.object(module.requests, "get", side_effect=fake_get):
            for operation, parameters in cases:
                payload, metadata = module._get_baike(operation, parameters, timeout=20, max_bytes=500000)
                self.assertIsInstance(payload, dict)
                self.assertEqual(metadata["requests_per_ticket"], 1)
                self.assertEqual(metadata["model_calls"], 0)
        self.assertEqual(len(captured), 4)
        self.assertTrue(all(row[1]["headers"]["Authorization"] == "Bearer backend-unified-key" for row in captured))
        self.assertTrue(all(row[1]["allow_redirects"] is False for row in captured))

    def test_local_operations_need_no_network_or_secret(self):
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

    def test_quota_error_fails_closed(self):
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

    def test_removed_operations_are_rejected(self):
        for operation in (
            "deep-search",
            "intelligent-search",
            "deep-research-lite",
            "nlp-sentiment",
            "ocr-general-basic",
            "image-general-scene",
        ):
            with self.subTest(operation=operation), self.assertRaises(Exception):
                module.validate_ticket(
                    self.ticket(operation, {"query": "test"}),
                    schema_path=module.SCHEMA_PATH,
                    catalog_path=module.CATALOG_PATH,
                )


if __name__ == "__main__":
    unittest.main()
