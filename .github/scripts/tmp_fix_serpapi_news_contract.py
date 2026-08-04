from __future__ import annotations

import json
from pathlib import Path


def replace_one(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: {label}: expected one match, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_catalog() -> None:
    path = Path("api-center/market-search/provider-catalog.json")
    catalog = json.loads(path.read_text(encoding="utf-8"))
    serpapi = next(row for row in catalog["providers"] if row["provider_id"] == "serpapi")
    news = next(row for row in serpapi["operations"] if row["operation_id"] == "google-news")
    if news["parameters"].count("sort_by_date") != 1:
        raise SystemExit("google-news sort_by_date parameter count mismatch")
    news["parameters"].remove("sort_by_date")
    properties = news["parameter_schema"]["properties"]
    if properties.pop("sort_by_date", None) != {"type": "boolean"}:
        raise SystemExit("google-news sort_by_date schema mismatch")
    news["description"] = "执行同步 Google News 关键词搜索并返回结构化 JSON 结果；时间范围使用 time_range，禁止与关键词不兼容的 so 排序参数。"
    path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_runtime() -> None:
    path = Path("api-center/market-search/market_search_task.py")
    replace_one(
        path,
        '''        if bool(parameters.get("sort_by_date", False)):
            query["so"] = "1"
        time_range = str(parameters.get("time_range") or "")
''',
        '''        time_range = str(parameters.get("time_range") or "")
''',
        "remove invalid Google News q plus so combination",
    )


def patch_tests() -> None:
    path = Path("api-center/market-search/tests/test_market_search_task.py")
    marker = '''    def test_execute_missing_secret_is_structured_failure(self):
'''
    addition = '''    def test_google_news_rejects_sort_by_date_and_never_sends_so(self):
        provider = next(row for row in MODULE.load_json(MODULE.CATALOG_PATH)["providers"] if row["provider_id"] == "serpapi")
        news = next(row for row in provider["operations"] if row["operation_id"] == "google-news")
        self.assertNotIn("sort_by_date", news["parameters"])
        self.assertNotIn("sort_by_date", news["parameter_schema"]["properties"])

        ticket = {
            "task_id": "serpapi-news-invalid-sort-20260804",
            "provider": "serpapi",
            "operation": "google-news",
            "objective": "reject unsupported sort parameter",
            "parameters": {"query": "福州", "hl": "zh-cn", "sort_by_date": True},
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "acceptance": {"timeout_seconds": 30, "max_response_bytes": 1000000},
        }
        with self.assertRaisesRegex(ValueError, "sort_by_date"):
            MODULE.validate_ticket(ticket)

        captured = []
        def fake_urlopen(request, timeout):
            captured.append(request.full_url)
            return FakeResponse({"search_metadata": {"status": "Success"}, "news_results": [{"title": "news"}]})

        with patch.dict(os.environ, {"SERPAPI_API_KEY": "serp-secret"}, clear=False), patch.object(MODULE.urllib.request, "urlopen", side_effect=fake_urlopen):
            MODULE.serpapi_query("google-news", {"query": "福州 政务", "gl": "cn", "hl": "zh-cn", "time_range": "week"}, 30, 1000000)
        self.assertEqual(len(captured), 1)
        parsed = MODULE.urllib.parse.parse_qs(MODULE.urllib.parse.urlsplit(captured[0]).query)
        self.assertEqual(parsed["engine"], ["google_news"])
        self.assertEqual(parsed["hl"], ["zh-cn"])
        self.assertNotIn("so", parsed)
        self.assertIn("when:1w", parsed["q"][0])

'''
    replace_one(path, marker, addition + marker, "insert Google News query contract test")


def main() -> None:
    patch_catalog()
    patch_runtime()
    patch_tests()


if __name__ == "__main__":
    main()
