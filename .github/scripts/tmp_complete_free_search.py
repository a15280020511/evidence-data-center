from __future__ import annotations

from pathlib import Path


def replace_one(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: {label}: expected one match, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_market_runtime() -> None:
    path = Path("api-center/market-search/market_search_task.py")
    replace_one(
        path,
        '''def optional_code(value: Any, name: str) -> str:
    text = str(value or "").strip().lower()
    if text and (len(text) != 2 or not text.isalpha()):
        raise ValueError(f"{name} must be a two-letter code")
    return text
''',
        '''def optional_country_code(value: Any, name: str) -> str:
    text = str(value or "").strip().lower()
    if text and (len(text) != 2 or not text.isalpha()):
        raise ValueError(f"{name} must be a two-letter country code")
    return text


def optional_language_code(value: Any, name: str) -> str:
    text = str(value or "").strip().lower()
    if text and not re.fullmatch(r"[a-z]{2}(?:-[a-z]{2})?", text):
        raise ValueError(f"{name} must be a supported language code")
    return text
''',
        "split country and language validation",
    )
    replace_one(path, 'hl = optional_code(parameters.get("hl"), "hl")', 'hl = optional_language_code(parameters.get("hl"), "hl")', "language validation")
    text = path.read_text(encoding="utf-8")
    count = text.count('gl = optional_code(parameters.get("gl"), "gl")')
    if count != 2:
        raise SystemExit(f"{path}: country validation: expected two matches, found {count}")
    path.write_text(text.replace('gl = optional_code(parameters.get("gl"), "gl")', 'gl = optional_country_code(parameters.get("gl"), "gl")'), encoding="utf-8")


def patch_market_tests() -> None:
    path = Path("api-center/market-search/tests/test_market_search_task.py")
    marker = '''    def test_execute_missing_secret_is_structured_failure(self):
'''
    addition = '''    def test_serpapi_accepts_simplified_chinese_language_tag(self):
        captured = []

        def fake_urlopen(request, timeout):
            captured.append(request.full_url)
            return FakeResponse({
                "search_metadata": {"status": "Success"},
                "organic_results": [{"title": "example"}],
                "news_results": [{"title": "news"}],
            })

        with patch.dict(os.environ, {"SERPAPI_API_KEY": "serp-secret"}, clear=False), patch.object(MODULE.urllib.request, "urlopen", side_effect=fake_urlopen):
            MODULE.serpapi_query("google-search", {"query": "福州", "gl": "cn", "hl": "zh-cn"}, 30, 1000000)
            MODULE.serpapi_query("google-news", {"query": "福州", "gl": "cn", "hl": "zh-cn"}, 30, 1000000)
        self.assertEqual(len(captured), 2)
        self.assertTrue(all("hl=zh-cn" in url for url in captured))
        self.assertTrue(any("engine=google&" in url or "engine=google%26" in url for url in captured))
        self.assertTrue(any("engine=google_news" in url for url in captured))

'''
    replace_one(path, marker, addition + marker, "insert SerpAPI Chinese regression")


def patch_baidu_catalog_builder() -> None:
    path = Path("api-center/baidu-ai-cloud/build_free_catalog.py")
    replace_one(path, '"""Generate frozen Baidu AI Search and model-summary provider contracts."""', '"""Generate frozen Baidu search, model-summary, and Baike provider contracts."""', "module description")
    old_tail = '''        operation(
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
    ]
    assert len(rows) == 4
'''
    new_tail = '''        operation(
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
        operation(
            "baike-lemma-list",
            "按词条名查询百度百科义项列表，返回词条ID、名称、义项说明和公开URL。",
            [
                ("lemma_title", text(200), True),
                ("top_k", integer(1, 20, 5), False),
            ],
            origin="https://appbuilder.baidu.com",
            path="/v2/baike/lemma/get_list_by_title",
            method="GET",
            content_type="application/json",
            credential_mode="unified-api-key-bearer",
        ),
        operation(
            "baike-lemma-content",
            "按词条名或词条ID读取百度百科结构化正文、摘要、基本信息和关系。",
            [
                ("search_type", enum(["lemmaTitle", "lemmaId"], "lemmaTitle"), True),
                ("search_key", text(200), True),
            ],
            origin="https://appbuilder.baidu.com",
            path="/v2/baike/lemma/get_content",
            method="GET",
            content_type="application/json",
            credential_mode="unified-api-key-bearer",
        ),
        operation(
            "baike-starmap-list",
            "按主题查询百度百科星图列表，返回星图ID和主题名。",
            [
                ("starmap_title", text(200), False),
                ("page", integer(1, 100, 1), False),
            ],
            origin="https://qianfan.baidubce.com",
            path="/v2/tools/baike/starmap/get_starmap_by_title",
            method="GET",
            content_type="application/json",
            credential_mode="unified-api-key-bearer",
        ),
        operation(
            "baike-starmap-detail",
            "按星图ID读取百度百科星图详情和分页实体关系。",
            [
                ("starmap_id", text(128), True),
                ("page", integer(1, 100, 1), False),
            ],
            origin="https://qianfan.baidubce.com",
            path="/v2/tools/baike/starmap/get_starmap_by_id",
            method="GET",
            content_type="application/json",
            credential_mode="unified-api-key-bearer",
        ),
    ]
    assert len(rows) == 8
'''
    replace_one(path, old_tail, new_tail, "append Baike operations")
    replace_one(path, '"schema_version": "baidu-ai-cloud-free-quota-policy-v2",', '"schema_version": "baidu-ai-cloud-free-quota-policy-v3",', "quota schema")
    replace_one(path, '"operator_action": "仅调用已实测通过的百度网页搜索和智能搜索生成；百度控制台不得启用按量后付费。",', '"operator_action": "仅调用已实测通过的百度网页搜索、智能摘要和百科结构化读取；百度控制台不得启用按量后付费。",', "quota operator action")
    family_marker = '''            {
                "family": "baidu-ai-search",
                "operations": ["web-search", "web-summary"],
                "quota": "使用百度账户当前网页搜索与智能搜索生成免费额度；官方页面口径可能调整，以控制台为最终依据。",
                "reset": "daily_or_control_plane_defined",
                "verified_with_current_key": True,
            }
'''
    family_replacement = family_marker + '''            ,{
                "family": "baidu-baike",
                "operations": ["baike-lemma-list", "baike-lemma-content", "baike-starmap-list", "baike-starmap-detail"],
                "quota": "百度百科正文常规免费额度1500次/月；词条义项和百科星图常规免费额度100次/天，以控制台为最终依据。",
                "reset": "daily_or_control_plane_defined",
                "verified_with_current_key": True,
            }
'''
    replace_one(path, family_marker, family_replacement, "add Baike quota family")
    replace_one(path, '"schema_version": "baidu-ai-cloud-provider-catalog-v4",', '"schema_version": "baidu-ai-cloud-provider-catalog-v5",', "provider schema")
    replace_one(path, '"display_name": "百度AI搜索与模型摘要",', '"display_name": "百度AI搜索、模型摘要与百科",', "display name")
    replace_one(path, '"description": "当前统一API Key已真实验证可用的百度公开网页搜索与模型搜索摘要。",', '"description": "当前统一API Key已真实验证可用的百度公开网页搜索、模型搜索摘要与百科结构化知识。",', "description")
    replace_one(path, '                    "web-summary": ["BAIDU_AI_CLOUD_API_KEY"],\n                    "local-governance": [],', '                    "web-summary": ["BAIDU_AI_CLOUD_API_KEY"],\n                    "baike-lemma-list": ["BAIDU_AI_CLOUD_API_KEY"],\n                    "baike-lemma-content": ["BAIDU_AI_CLOUD_API_KEY"],\n                    "baike-starmap-list": ["BAIDU_AI_CLOUD_API_KEY"],\n                    "baike-starmap-detail": ["BAIDU_AI_CLOUD_API_KEY"],\n                    "local-governance": [],', "credential matrix")
    replace_one(path, '"catalog_policy": "只开放当前Key已实测通过的2项上游高价值能力和2项本地治理能力。",', '"catalog_policy": "只开放当前Key已实测通过的6项上游高价值能力和2项本地治理能力。",', "catalog policy")
    replace_one(path, '"execution_policy": "每张票据一个操作、最多一次固定HTTPS请求；网页搜索为零模型调用，模型摘要固定记1次模型调用；禁止重试和付费兜底。",', '"execution_policy": "每张票据一个操作、最多一次固定HTTPS请求；网页搜索和百科读取为零模型调用，模型摘要固定记1次模型调用；禁止重试和付费兜底。",', "execution policy")
    replace_one(path, '"official_origins": ["https://qianfan.baidubce.com"],', '"official_origins": ["https://qianfan.baidubce.com", "https://appbuilder.baidu.com"],', "official origins")
    replace_one(path, '"fixed_api_hosts": ["qianfan.baidubce.com"],', '"fixed_api_hosts": ["qianfan.baidubce.com", "appbuilder.baidu.com"],', "fixed hosts")
    replace_one(path, '"fixed_paths": ["/v2/ai_search/web_search", "/v2/ai_search/web_summary"],', '"fixed_paths": ["/v2/ai_search/web_search", "/v2/ai_search/web_summary", "/v2/baike/lemma/get_list_by_title", "/v2/baike/lemma/get_content", "/v2/tools/baike/starmap/get_starmap_by_title", "/v2/tools/baike/starmap/get_starmap_by_id"],', "fixed paths")
    replace_one(path, '                    "model_calls_per_web_summary": 1,', '                    "model_calls_per_web_summary": 1,\n                    "baike_structured_read_allowed": True,\n                    "baike_video_allowed": False,', "Baike flags")
    replace_one(path, '"title": "baidu ai search managed free read-only ticket",', '"title": "baidu search and baike managed free read-only ticket",', "ticket title")


def patch_baidu_runtime() -> None:
    path = Path("api-center/baidu-ai-cloud/baidu_ai_cloud_task.py")
    replace_one(path, '"""Bounded execution for verified Baidu web search and model-search summary."""', '"""Bounded execution for verified Baidu search, model-summary, and Baike reads."""', "module description")
    replace_one(path, 'QIANFAN_ORIGIN = "https://qianfan.baidubce.com"\nWEB_SEARCH_PATH', 'QIANFAN_ORIGIN = "https://qianfan.baidubce.com"\nAPPBUILDER_ORIGIN = "https://appbuilder.baidu.com"\nWEB_SEARCH_PATH', "appbuilder origin")
    replace_one(path, 'WEB_SUMMARY_PATH = "/v2/ai_search/web_summary"\nAPI_KEY_ENV', 'WEB_SUMMARY_PATH = "/v2/ai_search/web_summary"\nBAIKE_LEMMA_LIST_PATH = "/v2/baike/lemma/get_list_by_title"\nBAIKE_LEMMA_CONTENT_PATH = "/v2/baike/lemma/get_content"\nBAIKE_STARMAP_LIST_PATH = "/v2/tools/baike/starmap/get_starmap_by_title"\nBAIKE_STARMAP_DETAIL_PATH = "/v2/tools/baike/starmap/get_starmap_by_id"\nAPI_KEY_ENV', "Baike path constants")
    marker = '''\n\ndef _truncate(payload: Mapping[str, Any], max_rows: int) -> Mapping[str, Any]:\n'''
    functions = '''

def _get_baike(
    operation: str,
    parameters: Mapping[str, Any],
    *,
    timeout: int,
    max_bytes: int,
) -> tuple[Mapping[str, Any], dict[str, Any]]:
    contracts = {
        "baike-lemma-list": (APPBUILDER_ORIGIN, BAIKE_LEMMA_LIST_PATH),
        "baike-lemma-content": (APPBUILDER_ORIGIN, BAIKE_LEMMA_CONTENT_PATH),
        "baike-starmap-list": (QIANFAN_ORIGIN, BAIKE_STARMAP_LIST_PATH),
        "baike-starmap-detail": (QIANFAN_ORIGIN, BAIKE_STARMAP_DETAIL_PATH),
    }
    origin, path = contracts[operation]
    row = _operation_row(operation)
    execution = row.get("execution") or {}
    if execution.get("official_origin") != origin or execution.get("path_template") != path:
        raise ValueError("provider catalog endpoint is not approved")
    if operation == "baike-lemma-list":
        title = str(parameters.get("lemma_title") or "").strip()
        if not title or len(title) > 200:
            raise ValueError("lemma_title must contain 1 to 200 characters")
        query = {"lemma_title": title, "top_k": bounded_int(parameters.get("top_k"), default=5, minimum=1, maximum=20, name="top_k")}
    elif operation == "baike-lemma-content":
        search_type = str(parameters.get("search_type") or "lemmaTitle")
        if search_type not in {"lemmaTitle", "lemmaId"}:
            raise ValueError("search_type is not allowed")
        search_key = str(parameters.get("search_key") or "").strip()
        if not search_key or len(search_key) > 200:
            raise ValueError("search_key must contain 1 to 200 characters")
        query = {"search_type": search_type, "search_key": search_key}
    elif operation == "baike-starmap-list":
        title = str(parameters.get("starmap_title") or "").strip()
        if len(title) > 200:
            raise ValueError("starmap_title is too long")
        query = {"page": bounded_int(parameters.get("page"), default=1, minimum=1, maximum=100, name="page")}
        if title:
            query["starmap_title"] = title
    else:
        starmap_id = str(parameters.get("starmap_id") or "").strip()
        if not starmap_id or len(starmap_id) > 128:
            raise ValueError("starmap_id must contain 1 to 128 characters")
        query = {"starmap_id": starmap_id, "page": bounded_int(parameters.get("page"), default=1, minimum=1, maximum=100, name="page")}
    key = _secret()
    try:
        response = requests.get(
            origin + path,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {key}",
                "User-Agent": "evidence-intelligence-center-baidu-baike/1",
            },
            params=query,
            timeout=timeout,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        raise BaiduAICloudError("BAIDU_CONNECTION_FAILED", type(exc).__name__, retryable=True) from exc
    decoded = _decode_json(response, max_bytes=max_bytes)
    _check_http(response, decoded)
    if not isinstance(decoded, Mapping):
        raise BaiduAICloudError("BAIDU_RESULT_INVALID", "upstream response must be a JSON object")
    return decoded, {
        "request_origin": origin.removeprefix("https://"),
        "request_path": path,
        "http_method": "GET",
        "credential_mode": "unified-api-key-bearer-backend-only",
        "credential_environment_variable": API_KEY_ENV,
        "http_status": response.status_code,
        "response_bytes": len(response.content),
        "requests_per_ticket": 1,
        "upstream_called": True,
        "paid_fallback_authorized": False,
        "model_calls": 0,
        "secret_values_exposed": False,
    }
'''
    replace_one(path, marker, functions + marker, "insert Baike runtime")
    replace_one(path, '    for key in ("references", "items", "results"):', '    for key in ("references", "items", "results", "list", "result"):', "truncate Baike lists")
    replace_one(path, '        "fixed_hosts": ["qianfan.baidubce.com"],', '        "fixed_hosts": ["qianfan.baidubce.com", "appbuilder.baidu.com"],', "runtime fixed hosts")
    branch = '''        elif operation in {"baike-lemma-list", "baike-lemma-content", "baike-starmap-list", "baike-starmap-detail"}:
            payload, request_metadata = _get_baike(
                operation,
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
    replace_one(path, '        else:\n            raise ValueError(f"unsupported Baidu operation: {operation}")', branch + '        else:\n            raise ValueError(f"unsupported Baidu operation: {operation}")', "add Baike execution branch")
    replace_one(path, '            display_name="百度AI搜索与模型摘要",', '            display_name="百度AI搜索、模型摘要与百科",', "runtime display name")


def patch_baidu_tests() -> None:
    path = Path("api-center/baidu-ai-cloud/tests/test_baidu_ai_cloud_task.py")
    replace_one(path, '    def test_catalog_registers_four_verified_operations(self):', '    def test_catalog_registers_eight_verified_operations(self):', "test name")
    replace_one(path, '{"catalog-capabilities", "quota-policy", "web-search", "web-summary"},', '{"catalog-capabilities", "quota-policy", "web-search", "web-summary", "baike-lemma-list", "baike-lemma-content", "baike-starmap-list", "baike-starmap-detail"},', "operation set")
    replace_one(path, '        self.assertEqual(len(provider["operations"]), 4)', '        self.assertEqual(len(provider["operations"]), 8)', "operation count")
    replace_one(path, '        self.assertEqual(limits["fixed_api_hosts"], ["qianfan.baidubce.com"])', '        self.assertEqual(limits["fixed_api_hosts"], ["qianfan.baidubce.com", "appbuilder.baidu.com"])', "hosts")
    replace_one(path, '        self.assertEqual(limits["fixed_paths"], ["/v2/ai_search/web_search", "/v2/ai_search/web_summary"])', '        self.assertEqual(limits["fixed_paths"], ["/v2/ai_search/web_search", "/v2/ai_search/web_summary", "/v2/baike/lemma/get_list_by_title", "/v2/baike/lemma/get_content", "/v2/tools/baike/starmap/get_starmap_by_title", "/v2/tools/baike/starmap/get_starmap_by_id"])', "paths")
    marker = '''    def test_local_operations_need_no_network_or_secret(self):
'''
    addition = '''    def test_baike_operations_use_fixed_get_endpoints_without_model_calls(self):
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

'''
    replace_one(path, marker, addition + marker, "insert Baike tests")


def main() -> None:
    patch_market_runtime()
    patch_market_tests()
    patch_baidu_catalog_builder()
    patch_baidu_runtime()
    patch_baidu_tests()


if __name__ == "__main__":
    main()
