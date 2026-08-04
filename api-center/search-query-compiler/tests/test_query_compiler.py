from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("query_compiler", HERE / "query_compiler.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

REQUEST = {
    "objective": "发现官方公共采购API",
    "concepts": ["public procurement", "contracts", "API documentation"],
    "official_domains": ["open-contracting.org", "europa.eu"],
    "language": "zh-cn",
}


class QueryCompilerTests(unittest.TestCase):
    def test_tavily_uses_domain_filter_not_google_operators(self) -> None:
        compiled = MODULE.compile_query("tavily", REQUEST)
        parameters = compiled["parameters"]
        self.assertEqual(
            parameters["include_domains"],
            ["open-contracting.org", "europa.eu"],
        )
        self.assertNotIn("site:", parameters["query"])

    def test_exa_uses_semantic_query(self) -> None:
        query = MODULE.compile_query("exa", REQUEST)["parameters"]["query"]
        self.assertIn("Official sources", query)
        self.assertNotIn("site:", query)

    def test_google_uses_bounded_site_clauses(self) -> None:
        query = MODULE.compile_query("serpapi-google", REQUEST)["parameters"]["query"]
        self.assertIn("site:open-contracting.org", query)
        self.assertIn("site:europa.eu", query)
        self.assertLessEqual(len(query), 1000)

    def test_baidu_removes_google_operators(self) -> None:
        request = dict(REQUEST)
        request["objective"] = "site:gov.cn 开放数据 OR API (接口)"
        query = MODULE.compile_query("baidu", request)["parameters"]["query"]
        self.assertNotIn("site:", query.lower())
        self.assertNotIn(" OR ", query)
        self.assertLessEqual(len(query), 256)

    def test_rejects_invalid_domains_and_provider(self) -> None:
        bad = dict(REQUEST)
        bad["official_domains"] = ["https://example.com/private/path"]
        with self.assertRaises(ValueError):
            MODULE.compile_query("tavily", bad)
        with self.assertRaises(ValueError):
            MODULE.compile_query("unknown", REQUEST)


if __name__ == "__main__":
    unittest.main()
