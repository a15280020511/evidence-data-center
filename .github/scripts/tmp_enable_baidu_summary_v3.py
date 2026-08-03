from __future__ import annotations

from pathlib import Path


def replace_one(path: Path, label: str, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: {label}: expected one match, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def update_build_catalog() -> None:
    path = Path("api-center/baidu-ai-cloud/build_free_catalog.py")
    replace_one(
        path,
        "module description",
        '"""Generate the frozen Baidu AI Search-only provider contracts."""',
        '"""Generate frozen Baidu AI search and model-summary contracts."""',
    )
    marker = "    ]\n    assert len(rows) == 3\n"
    insertion = '''        operation(
            "web-summary",
            "百度智能搜索生成高性能版：检索公开网页并由模型生成带来源引用的摘要。",
            [
                ("query", text(256), True),
                ("top_k", integer(1, 10, 3), False),
            ],
            origin="https://qianfan.baidubce.com",
            path="/v2/ai_search/web_summary",
            method="POST",
            content_type="application/json",
            credential_mode="unified-api-key-bearer",
        ),
    ]
    assert len(rows) == 4
'''
    replace_one(path, "operation insertion", marker, insertion)
    replacements = (
        (
            "operator policy",
            '"operator_action": "仅调用已实测通过的百度网页搜索；百度控制台不得启用按量后付费。",',
            '"operator_action": "仅调用已实测通过的百度网页搜索与智能搜索摘要；百度控制台不得启用按量后付费。",',
        ),
        (
            "quota operations",
            '"operations": ["web-search"],',
            '"operations": ["web-search", "web-summary"],',
        ),
        (
            "quota description",
            '"quota": "使用百度账户当前网页搜索免费额度；官方页面口径可能调整，以控制台为最终依据。",',
            '"quota": "web-search每月1500次按天发放；web-summary每日100次。额度以百度控制台为最终依据。",',
        ),
        (
            "excluded family",
            '"family": "intelligent-search-deep-search-web-summary-deep-research",',
            '"family": "intelligent-search-deep-search-deep-research",',
        ),
        (
            "excluded reason",
            '"reason": "当前Key未完成免费且可用的真实验收，并存在模型或按次计费风险。",',
            '"reason": "尚未完成当前Key的免费且可用真实验收，继续保持关闭。",',
        ),
        (
            "display name",
            '"display_name": "百度AI网页搜索",',
            '"display_name": "百度AI搜索与智能摘要",',
        ),
        (
            "provider description",
            '"description": "当前统一API Key已真实验证可用的百度公开网页搜索。",',
            '"description": "当前统一API Key已真实验证可用的百度公开网页搜索与模型搜索摘要。",',
        ),
        (
            "credential matrix",
            '"web-search": ["BAIDU_AI_CLOUD_API_KEY"],\n                    "local-governance": [],',
            '"web-search": ["BAIDU_AI_CLOUD_API_KEY"],\n                    "web-summary": ["BAIDU_AI_CLOUD_API_KEY"],\n                    "local-governance": [],',
        ),
        (
            "catalog policy",
            '"catalog_policy": "只开放当前Key已实测通过的1项上游高价值能力和2项本地治理能力。",',
            '"catalog_policy": "只开放当前Key已实测通过的2项上游高价值能力和2项本地治理能力。",',
        ),
        (
            "execution policy",
            '"execution_policy": "每张票据一个操作、最多一次固定HTTPS请求；零模型调用、零付费兜底。",',
            '"execution_policy": "每张票据一个操作、最多一次固定HTTPS请求；web-search模型调用0次，web-summary模型调用1次；零付费兜底。",',
        ),
        (
            "fixed paths",
            '"fixed_paths": ["/v2/ai_search/web_search"],',
            '"fixed_paths": ["/v2/ai_search/web_search", "/v2/ai_search/web_summary"],',
        ),
        (
            "model search flag",
            '"generative_model_chat_allowed": False,',
            '"model_search_summary_allowed": True,\n                    "generative_model_chat_allowed": False,',
        ),
    )
    for label, old, new in replacements:
        replace_one(path, label, old, new)


def update_runtime() -> None:
    path = Path("api-center/baidu-ai-cloud/baidu_ai_cloud_task.py")
    replace_one(
        path,
        "module description",
        '"""Bounded execution for the currently verified Baidu AI web-search capability."""',
        '"""Bounded execution for verified Baidu AI search and model-summary capabilities."""',
    )
    replace_one(
        path,
        "summary path constant",
        'WEB_SEARCH_PATH = "/v2/ai_search/web_search"\nAPI_KEY_ENV',
        'WEB_SEARCH_PATH = "/v2/ai_search/web_search"\nWEB_SUMMARY_PATH = "/v2/ai_search/web_summary"\nAPI_KEY_ENV',
    )
    text = path.read_text(encoding="utf-8")
    function_marker = "\n\ndef _truncate(payload: Mapping[str, Any], max_rows: int) -> Mapping[str, Any]:\n"
    if text.count(function_marker) != 1:
        raise SystemExit("runtime: summary function marker mismatch")
    functions = '''

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
    return {
        "instruction": "仅根据公开网页生成简明事实摘要，保留来源引用，不推断个人敏感信息。",
        "messages": [{"role": "user", "content": query}],
        "stream": False,
        "resource_type_filter": [{"type": "web", "top_k": top_k}],
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
                "User-Agent": "evidence-intelligence-center-baidu-model-search/1",
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
    text = text.replace(function_marker, functions + function_marker, 1)
    start = text.index('        elif operation == "web-search":')
    else_marker = '        else:\n            raise ValueError(f"unsupported Baidu operation: {operation}")'
    position = text.index(else_marker, start)
    branch = '''        elif operation == "web-summary":
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
'''
    text = text[:position] + branch + text[position:]
    if text.count('display_name="百度AI网页搜索",') != 1:
        raise SystemExit("runtime: display name marker mismatch")
    text = text.replace(
        'display_name="百度AI网页搜索",',
        'display_name="百度AI搜索与智能摘要",',
        1,
    )
    path.write_text(text, encoding="utf-8")


def update_tests() -> None:
    path = Path("api-center/baidu-ai-cloud/tests/test_baidu_ai_cloud_task.py")
    replacements = (
        (
            "test name",
            "def test_catalog_registers_only_three_verified_operations(self):",
            "def test_catalog_registers_four_verified_operations(self):",
        ),
        (
            "operation set",
            '{"catalog-capabilities", "quota-policy", "web-search"},',
            '{"catalog-capabilities", "quota-policy", "web-search", "web-summary"},',
        ),
        (
            "operation count",
            'self.assertEqual(len(provider["operations"]), 3)',
            'self.assertEqual(len(provider["operations"]), 4)',
        ),
        (
            "fixed paths",
            'self.assertEqual(limits["fixed_paths"], ["/v2/ai_search/web_search"])',
            'self.assertEqual(limits["fixed_paths"], ["/v2/ai_search/web_search", "/v2/ai_search/web_summary"])',
        ),
        (
            "model flag",
            'self.assertFalse(limits["generative_model_chat_allowed"])',
            'self.assertTrue(limits["model_search_summary_allowed"])\n        self.assertFalse(limits["generative_model_chat_allowed"])',
        ),
    )
    for label, old, new in replacements:
        replace_one(path, label, old, new)
    text = path.read_text(encoding="utf-8")
    marker = "    def test_local_operations_need_no_network_or_secret(self):\n"
    if text.count(marker) != 1:
        raise SystemExit("tests: insertion marker mismatch")
    test = '''    def test_web_summary_uses_fixed_model_search_endpoint(self):
        captured = {}

        def fake_post(url, **kwargs):
            captured["url"] = url
            captured.update(kwargs)
            return FakeResponse(
                {
                    "content": "公开信息摘要",
                    "references": [
                        {"title": "来源", "url": "https://example.com"}
                    ],
                }
            )

        with mock.patch.dict(
            os.environ,
            {module.API_KEY_ENV: "backend-unified-key"},
            clear=True,
        ), mock.patch.object(module.requests, "post", side_effect=fake_post):
            payload, metadata = module._post_web_summary(
                {"query": "福州政务公开", "top_k": 2},
                timeout=20,
                max_bytes=500000,
            )
        self.assertEqual(
            captured["url"],
            "https://qianfan.baidubce.com/v2/ai_search/web_summary",
        )
        self.assertEqual(
            captured["headers"]["Authorization"],
            "Bearer backend-unified-key",
        )
        self.assertFalse(captured["allow_redirects"])
        self.assertFalse(captured["json"]["stream"])
        self.assertEqual(metadata["model_calls"], 1)
        self.assertEqual(metadata["requests_per_ticket"], 1)
        self.assertNotIn(
            "backend-unified-key",
            json.dumps(payload, ensure_ascii=False),
        )

'''
    path.write_text(text.replace(marker, test + marker, 1), encoding="utf-8")


def update_expected_counts() -> None:
    for name in (
        "api-center/build_catalog_market_search.py",
        "api-center/tests/test_api_catalog.py",
    ):
        replace_one(
            Path(name),
            "Baidu operation count",
            '"baidu-ai-cloud": 3,',
            '"baidu-ai-cloud": 4,',
        )


def main() -> None:
    update_build_catalog()
    update_runtime()
    update_tests()
    update_expected_counts()


if __name__ == "__main__":
    main()
