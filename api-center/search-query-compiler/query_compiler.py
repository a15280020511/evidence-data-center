#!/usr/bin/env python3
"""Compile one bounded discovery objective for different search providers."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping

PROVIDERS = {"tavily", "exa", "serpapi-google", "baidu"}
DOMAIN_RE = re.compile(r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$", re.I)
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
GOOGLE_OPERATOR_RE = re.compile(
    r"\b(?:site|filetype|intitle|inurl|allintitle|allinurl):\S+|\b(?:AND|OR|NOT)\b|[()]",
    re.I,
)


def clean_text(value: Any, *, name: str, maximum: int) -> str:
    text = " ".join(str(value or "").split())
    if not text or len(text) > maximum or CONTROL_RE.search(text):
        raise ValueError(f"{name} must contain 1 to {maximum} safe characters")
    return text


def clean_list(value: Any, *, name: str, maximum_items: int, maximum_length: int) -> list[str]:
    if value in (None, ""):
        return []
    if not isinstance(value, list) or len(value) > maximum_items:
        raise ValueError(f"{name} must be an array with at most {maximum_items} items")
    result: list[str] = []
    for item in value:
        text = clean_text(item, name=name, maximum=maximum_length)
        if text.casefold() not in {entry.casefold() for entry in result}:
            result.append(text)
    return result


def clean_domains(value: Any) -> list[str]:
    domains = clean_list(value, name="official_domains", maximum_items=20, maximum_length=253)
    result: list[str] = []
    for domain in domains:
        normalized = domain.casefold().removeprefix("https://").removeprefix("http://").strip("/.")
        if "/" in normalized or not DOMAIN_RE.fullmatch(normalized):
            raise ValueError(f"invalid official domain: {domain}")
        if normalized not in result:
            result.append(normalized)
    return result


def baidu_safe(text: str) -> str:
    stripped = GOOGLE_OPERATOR_RE.sub(" ", text)
    return " ".join(stripped.replace('"', " ").split())


def compile_query(provider: str, request: Mapping[str, Any]) -> dict[str, Any]:
    if provider not in PROVIDERS:
        raise ValueError(f"unsupported provider: {provider}")
    objective = clean_text(request.get("objective"), name="objective", maximum=500)
    concepts = clean_list(request.get("concepts"), name="concepts", maximum_items=12, maximum_length=100)
    domains = clean_domains(request.get("official_domains"))
    language = str(request.get("language") or "en").strip().lower()
    if not re.fullmatch(r"[a-z]{2}(?:-[a-z]{2})?", language):
        raise ValueError("language is invalid")
    terms = concepts or [objective]

    if provider == "tavily":
        query = "；".join([objective, "重点：" + "、".join(terms)]) if language.startswith("zh") else "; ".join([objective, "Focus: " + ", ".join(terms)])
        return {
            "provider": provider,
            "operation": "search",
            "parameters": {
                "query": query[:1000],
                "search_depth": "advanced",
                "topic": "general",
                "max_results": 10,
                "include_domains": domains,
                "include_raw_content": False,
            },
        }

    if provider == "exa":
        domain_phrase = " Official sources: " + ", ".join(domains) + "." if domains else ""
        query = f"{objective}. Relevant concepts: {', '.join(terms)}.{domain_phrase} Return official documentation, data catalogs, API specifications, licences, and access conditions."
        return {
            "provider": provider,
            "operation": "search",
            "parameters": {
                "query": query[:1000],
                "num_results": 10,
                "search_type": "auto",
                "content_mode": "highlights",
                "max_characters": 20000,
            },
        }

    if provider == "serpapi-google":
        site_clause = " OR ".join(f"site:{domain}" for domain in domains[:8])
        short_terms = " ".join(f'"{term}"' if " " in term else term for term in terms[:8])
        query_parts = []
        if site_clause:
            query_parts.append(f"({site_clause})")
        query_parts.extend([short_terms, '"API"', '(documentation OR data OR download)'])
        query = " ".join(part for part in query_parts if part).strip()
        return {
            "provider": provider,
            "operation": "google-search",
            "parameters": {
                "query": query[:1000],
                "gl": "cn" if language.startswith("zh") else "us",
                "hl": "zh-cn" if language.startswith("zh") else "en",
                "start": 0,
                "device": "desktop",
                "safe": "active",
            },
        }

    chinese_suffix = " 官方 开放数据 API 接口文档 数据目录 下载 免费 使用条件"
    source_terms = [baidu_safe(objective), *(baidu_safe(term) for term in terms)]
    host_names = [domain.split(".")[-2] for domain in domains if len(domain.split(".")) >= 2]
    query = " ".join(dict.fromkeys([*source_terms, *host_names])).strip() + chinese_suffix
    return {
        "provider": provider,
        "operation": "web-search",
        "parameters": {
            "query": query[:256],
            "top_k": 20,
            "edition": "standard",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("provider", choices=sorted(PROVIDERS))
    parser.add_argument("request", type=Path, help="JSON request file")
    args = parser.parse_args()
    request = json.loads(args.request.read_text(encoding="utf-8"))
    if not isinstance(request, Mapping):
        raise ValueError("request must be a JSON object")
    print(json.dumps(compile_query(args.provider, request), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
