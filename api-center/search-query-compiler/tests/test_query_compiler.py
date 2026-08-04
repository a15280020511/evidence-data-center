from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

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


def test_tavily_uses_domain_filter_not_google_operators() -> None:
    compiled = MODULE.compile_query("tavily", REQUEST)
    parameters = compiled["parameters"]
    assert parameters["include_domains"] == ["open-contracting.org", "europa.eu"]
    assert "site:" not in parameters["query"]


def test_exa_uses_semantic_query() -> None:
    query = MODULE.compile_query("exa", REQUEST)["parameters"]["query"]
    assert "Official sources" in query
    assert "site:" not in query


def test_google_uses_bounded_site_clauses() -> None:
    query = MODULE.compile_query("serpapi-google", REQUEST)["parameters"]["query"]
    assert "site:open-contracting.org" in query
    assert "site:europa.eu" in query
    assert len(query) <= 1000


def test_baidu_removes_google_operators() -> None:
    request = dict(REQUEST)
    request["objective"] = "site:gov.cn 开放数据 OR API (接口)"
    query = MODULE.compile_query("baidu", request)["parameters"]["query"]
    assert "site:" not in query.lower()
    assert " OR " not in query
    assert len(query) <= 256


def test_rejects_invalid_domains_and_provider() -> None:
    bad = dict(REQUEST)
    bad["official_domains"] = ["https://example.com/private/path"]
    with pytest.raises(ValueError):
        MODULE.compile_query("tavily", bad)
    with pytest.raises(ValueError):
        MODULE.compile_query("unknown", REQUEST)
