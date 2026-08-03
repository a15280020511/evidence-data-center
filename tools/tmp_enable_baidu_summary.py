#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def patch_build_catalog() -> None:
    path = Path("api-center/baidu-ai-cloud/build_free_catalog.py")
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '"""Generate the frozen Baidu AI Search-only provider contracts."""',
        '"""Generate frozen Baidu AI Search and model-summary provider contracts."""',
        "build docstring",
    )
    summary_operation = '''        operation(
            "web-summary",
            "百度智能搜索生成高性能版：实时检索公开网页，由模型生成摘要并返回引用。",
            [
                ("query", text(256), True),
                ("top_k", integer(1, 10, 3), False),
                ("instruction", text(4000), False),
            ],
            origin="https://qianfan.baidubce.com",
            path="/v2/ai_search/web_summary",
            method="POST",
            content_type="application/json",
            credential_mode="unified-api-key-bearer",
        ),
'''
    text = replace_once(
        text,
        "    ]\n    assert len(rows) == 3\n",
        summary_operation + "    ]\n    assert len(rows) == 4\n",
        "insert summary operation",
    )
    replacements = [
        ('"reviewed_at": "2026-08-03"', '"reviewed_at": "2026-08-04"', "review date"),
        (
            '"operator_action": "仅调用已实测通过的百度网页搜索；百度控制台不得启用按量后付费。"',
            '"operator_action": "仅调用已实测通过的百度网页搜索和智能搜索生成；百度控制台不得启用按量后付费。"',
            "operator action",
        ),
        ('"operations": ["web-search"]', '"operations": ["web-search", "web-summary"]', "quota operations"),
        (
            '"quota": "使用百度账户当前网页搜索免费额度；官方页面口径可能调整，以控制台为最终依据。"',
            '"quota": "使用百度账户当前网页搜索与智能搜索生成免费额度；官方页面口径可能调整，以控制台为最终依据。"',
            "quota text",
        ),
        (
            '"family": "intelligent-search-deep-search-web-summary-deep-research",\n                "reason": "当前Key未完成免费且可用的真实验收，并存在模型或按次计费风险。"',
            '"family": "deep-search-deep-research-and-arbitrary-model-search",\n                "reason": "未完成免费且可用的真实验收，或可能产生多次搜索及额外模型费用。"',
            "excluded family",
        ),
        ('"display_name": "百度AI网页搜索"', '"display_name": "百度AI搜索与模型摘要"', "display name"),
        (
            '"description": "当前统一API Key已真实验证可用的百度公开网页搜索。"',
            '"description": "当前统一API Key已真实验证可用的百度公开网页搜索与模型搜索摘要。"',
            "provider description",
        ),
        (
            '"web-search": ["BAIDU_AI_CLOUD_API_KEY"],\n                    "local-governance": []',
            '"web-search": ["BAIDU_AI_CLOUD_API_KEY"],\n                    "web-summary": ["BAIDU_AI_CLOUD_API_KEY"],\n                    "local-governance": []',
            "credential matrix",
        ),
        (
            '"catalog_policy": "只开放当前Key已实测通过的1项上游高价值能力和2项本地治理能力。"',
            '"catalog_policy": "只开放当前Key已实测通过的2项上游高价值能力和2项本地治理能力。"',
            "catalog policy",
        ),
        (
            '"execution_policy": "每张票据一个操作、最多一次固定HTTPS请求；零模型调用、零付费兜底。"',
            '"execution_policy": "每张票据一个操作、最多一次固定HTTPS请求；网页搜索为零模型调用，模型摘要固定记1次模型调用；禁止重试和付费兜底。"',
            "execution policy",
        ),
        (
            '"fixed_paths": ["/v2/ai_search/web_search"]',
            '"fixed_paths": ["/v2/ai_search/web_search", "/v2/ai_search/web_summary"]',
            "fixed paths",
        ),
        (
            '"generative_model_chat_allowed": False,',
            '"generative_model_chat_allowed": False,\n                    "generative_search_summary_allowed": True,\n                    "model_calls_per_web_summary": 1,',
            "summary limits",
        ),
    ]
    for old, new, label in replacements:
        text = replace_once(text, old, new, label)
    path.write_text(text, encoding="utf-8")


def patch_runtime() -> None:
    path = Path("api-center/baidu-ai-cloud/baidu_ai_cloud_task.py")
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '"""Bounded execution for the currently verified Baidu AI web-search capability."""',
        '"""Bounded execution for verified Baidu web search and model-search summary."""',
        "runtime docstring",
    )
    text = replace_once(
        text,
        'WEB_SEARCH_PATH = "/v2/ai_search/web_search"\nAPI_KEY_ENV',
        'WEB_SEARCH_PATH = "/v2/ai_search/web_search"\nWEB_SUMMARY_PATH = "/v2/ai_search/web_summary"\nAPI_KEY_ENV',
        "summary constant",
    )
    insert = '''

def _web_summary_body(parameters: Mapping[str, Any]) -> dict[str, Any]:
    query = str(parameters.get("query") or "").strip()
    if not query:
        raise ValueError("query must not be empty")
    top_k = bounded_int(
        parameters.get("top_k"),
        default=3,
        minimum=1,
        maximum=10,
        name="top_k",
    )
    instruction = str(
        parameters.get("instruction")
        or "仅基于公开网页生成简明、可核验的事实摘要，并保留引用。"
    ).strip()
    if not instruction or len(instruction) > 4000:
        raise ValueError("instruction must contain 1 to 4000 characters")
    return {
        "instruction": instruction,
        "messages": [{"content": query, "role": "user"}],
        "stream": False,
        "resource_type_filter": [{"type": "web", "top_k": top_k}],
        "enable_full_content": False,
    }


def _post_web_summary(
    parameters: Mapping[str, Any],
    *,
    timeout: int,
    max_bytes: int,
) -> tuple[Mapping[str, Any], dict[str, Any]]:
    row = _operation_row("web-summary")
    execution = row.get("execution") or {}
    if execution.get("official_origin") != QIANFAN_ORIGIN:
        raise ValueError("provider catalog origin is not approved")
    if execution.get("path_template") != WEB_SUMMARY_PATH:
        raise ValueError("provider catalog path is not approved")
    key = _secret()
    try:
        response = requests.post(
            QIANFAN_ORIGIN + WEB_SUMMARY_PATH,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "User-Agent": "evidence-intelligence-center-baidu-summary/1",
            },
            json=_web_summary_body(parameters),
            timeout=timeout,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        raise BaiduAICloudError(
            "BAIDU_CONNECTION_FAILED",
            type(exc).__name__,
            retryable=True,
        ) from exc
    decoded = _decode_json(response, max_bytes=max_bytes)
    _check_http(response, decoded)
    if not isinstance(decoded, Mapping):
        raise BaiduAICloudError(
            "BAIDU_RESULT_INVALID",
            "upstream response must be a JSON object",
        )
    choices = decoded.get("choices")
    content = ""
    if isinstance(choices, list) and choices:
        first = choices[0] if isinstance(choices[0], Mapping) else {}
        message = first.get("message") if isinstance(first.get("message"), Mapping) else {}
        content = str(message.get("content") or "")
    if not content.strip():
        raise BaiduAICloudError(
            "BAIDU_RESULT_INVALID",
            "model-search response contained no generated content",
        )
    return decoded, {
        "request_origin": "qianfan.baidubce.com",
        "request_path": WEB_SUMMARY_PATH,
        "http_method": "POST",
        "credential_mode": "unified-api-key-bearer-backend-only",
        "credential_environment_variable": API_KEY_ENV,
        "http_status": response.status_code,
        "response_bytes": len(response.content),
        "requests_per_ticket": 1,
        "upstream_called": True,
        "paid_fallback_authorized": False,
        "model_calls": 1,
        "secret_values_exposed": False,
    }
'''
    text = replace_once(
        text,
        "\n\ndef _truncate(payload: Mapping[str, Any], max_rows: int) -> Mapping[str, Any]:",
        insert + "\n\ndef _truncate(payload: Mapping[str, Any], max_rows: int) -> Mapping[str, Any]:",
        "insert summary runtime",
    )
    old_branch = '''        elif operation == "web-search":
            payload, request_metadata = _post_web_search(
                parameters,
                timeout=timeout,
                max_bytes=max_bytes,
            )
            metadata.update(request_metadata)
            snapshot = {
                "provider": "baidu-ai-cloud",
                "operation": operation,
                "data": _redact(_truncate(payload, max_rows)),
            }
        else:
'''
    new_branch = '''        elif operation == "web-search":
            payload, request_metadata = _post_web_search(
                parameters,
                timeout=timeout,
                max_bytes=max_bytes,
            )
            metadata.update(request_metadata)
            snapshot = {
                "provider": "baidu-ai-cloud",
                "operation": operation,
                "data": _redact(_truncate(payload, max_rows)),
            }
        elif operation == "web-summary":
            payload, request_metadata = _post_web_summary(
                parameters,
                timeout=timeout,
                max_bytes=max_bytes,
            )
            metadata.update(request_metadata)
            snapshot = {
                "provider": "baidu-ai-cloud",
                "operation": operation,
                "data": _redact(_truncate(payload, max_rows)),
            }
        else:
'''
    text = replace_once(text, old_branch, new_branch, "execute summary branch")
    text = replace_once(
        text,
        'display_name="百度AI网页搜索"',
        'display_name="百度AI搜索与模型摘要"',
        "runtime display",
    )
    path.write_text(text, encoding="utf-8")


def patch_tests() -> None:
    path = Path("api-center/baidu-ai-cloud/tests/test_baidu_ai_cloud_task.py")
    text = path.read_text(encoding="utf-8")
    replacements = [
        (
            "def test_catalog_registers_only_three_verified_operations(self):",
            "def test_catalog_registers_four_verified_operations(self):",
            "test name",
        ),
        (
            '{"catalog-capabilities", "quota-policy", "web-search"}',
            '{"catalog-capabilities", "quota-policy", "web-search", "web-summary"}',
            "test operations",
        ),
        (
            'self.assertEqual(len(provider["operations"]), 3)',
            'self.assertEqual(len(provider["operations"]), 4)',
            "test count",
        ),
        (
            'self.assertEqual(limits["fixed_paths"], ["/v2/ai_search/web_search"])',
            'self.assertEqual(limits["fixed_paths"], ["/v2/ai_search/web_search", "/v2/ai_search/web_summary"])',
            "test fixed paths",
        ),
    ]
    for old, new, label in replacements:
        text = replace_once(text, old, new, label)
    summary_test = '''
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

'''
    text = replace_once(
        text,
        "    def test_local_operations_need_no_network_or_secret(self):",
        summary_test + "    def test_local_operations_need_no_network_or_secret(self):",
        "insert summary test",
    )
    path.write_text(text, encoding="utf-8")


def patch_expected_counts() -> None:
    for path_text in (
        "api-center/build_catalog_market_search.py",
        "api-center/tests/test_api_catalog.py",
        "api-center/tests/test_capability_maximization.py",
    ):
        path = Path(path_text)
        text = path.read_text(encoding="utf-8")
        old = '"baidu-ai-cloud": 3'
        if old not in text:
            raise SystemExit(f"{path_text}: expected Baidu operation count")
        path.write_text(text.replace(old, '"baidu-ai-cloud": 4'), encoding="utf-8")


def main() -> None:
    patch_build_catalog()
    patch_runtime()
    patch_tests()
    patch_expected_counts()


if __name__ == "__main__":
    main()
