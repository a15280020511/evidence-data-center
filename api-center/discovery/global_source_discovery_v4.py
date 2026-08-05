#!/usr/bin/env python3
"""Four-radar, platform-aware global discovery entrypoint.

This planner replaces the former five-axis conjunction with short modular
query families. Google Trends is used only as a bounded auxiliary vocabulary
signal; registry coverage and stale capability gaps remain authoritative.
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Any, Mapping

import global_source_discovery_v2 as runtime

HERE = Path(__file__).resolve().parent
QUERY_PREFIXES = {
    "source", "protocol", "institution", "publication", "regional_source",
    "intelligence_tool", "compute_tool", "incumbent_change", "multilingual",
    "trend",
}


def load_json(path: Path) -> Mapping[str, Any]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, Mapping) else {}


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def stride_for(length: int, preferred: int) -> int:
    if length <= 1:
        return 1
    for candidate in (preferred, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        candidate %= length
        if candidate and math.gcd(candidate, length) == 1:
            return candidate
    return 1


def pick(values: list[str], index: int, preferred: int) -> str:
    if not values:
        return ""
    return values[(index * stride_for(len(values), preferred)) % len(values)]


def tool_documents() -> tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]]:
    return (
        load_json(HERE / "intelligence-tool-keywords.json"),
        load_json(HERE / "compute-tool-keywords.json"),
        load_json(HERE / "local-language-expansion-v2.json"),
    )


def intelligence_terms(document: Mapping[str, Any]) -> tuple[list[str], list[str], list[tuple[str, str]]]:
    capabilities = string_list(document.get("capabilities"))
    surfaces = string_list(document.get("surfaces"))
    local_rows: list[tuple[str, str]] = []
    local = document.get("local_language_terms")
    if isinstance(local, Mapping):
        for language, terms in local.items():
            for term in string_list(terms):
                local_rows.append((str(language), term))
    return capabilities, surfaces, local_rows


def expanded_local_terms(document: Mapping[str, Any]) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    languages = document.get("languages")
    if isinstance(languages, Mapping):
        for language, terms in languages.items():
            for term in string_list(terms):
                rows.append((str(language), term))
    return rows


def trend_terms(config: Mapping[str, Any]) -> list[str]:
    trend_cfg = config.get("google_trends") if isinstance(config.get("google_trends"), Mapping) else {}
    if not bool(trend_cfg.get("enabled", False)):
        return []
    path = Path(os.getenv("TREND_SIGNALS_PATH") or HERE / "trend-signals.json")
    document = load_json(path)
    maximum = min(int(trend_cfg.get("max_terms_per_run") or 20), 50)
    rows: list[str] = []
    for item in document.get("terms") or []:
        term = item.get("term") if isinstance(item, Mapping) else item
        text = " ".join(str(term or "").split()).strip()
        if 2 <= len(text) <= 160 and not text.casefold().startswith(("http://", "https://")):
            rows.append(text)
    return list(dict.fromkeys(rows))[:maximum]


def query_set(
    config: Mapping[str, Any],
    cursor: int,
    limit: int,
    regions: list[str],
) -> tuple[list[str], int]:
    intelligence_doc, compute_doc, language_doc = tool_documents()
    intelligence_capabilities, intelligence_surfaces, original_local = intelligence_terms(intelligence_doc)
    local_terms = original_local + expanded_local_terms(language_doc)
    compute_capabilities = string_list(compute_doc.get("capabilities"))
    compute_ecosystems = string_list(compute_doc.get("ecosystems"))

    protocols = string_list(config.get("protocol_keywords"))
    institutions = string_list(config.get("institution_keywords"))
    sectors = string_list(config.get("sector_keywords"))
    publications = string_list(config.get("publication_keywords"))
    incumbents = string_list(config.get("incumbent_tool_keywords"))
    changes = string_list(config.get("change_keywords")) or [
        "release", "changelog", "deprecated", "breaking change", "security advisory"
    ]
    trends = trend_terms(config)
    region_values = string_list(regions) or string_list(config.get("regional_language_keywords"))

    required = [protocols, institutions, sectors, publications, intelligence_capabilities, compute_capabilities]
    if not all(required):
        return [], cursor

    queries: list[str] = []
    family_count = 10
    for offset in range(limit):
        absolute = cursor + offset
        family = absolute % family_count
        cycle = absolute // family_count
        sector = pick(sectors, cycle + family, 11)

        if family == 0:
            query = f"source::{sector} dataset open data"
        elif family == 1:
            query = f"protocol::{pick(protocols, cycle, 7)} {sector}"
        elif family == 2:
            query = f"institution::{pick(institutions, cycle, 13)} {sector} data portal"
        elif family == 3:
            query = f"publication::{sector} {pick(publications, cycle, 17)}"
        elif family == 4:
            query = f"regional_source::{sector} {pick(region_values, cycle, 19)} open data"
        elif family == 5:
            capability = pick(intelligence_capabilities, cycle, 23)
            surface = pick(intelligence_surfaces, cycle, 29) or "library"
            query = f"intelligence_tool::{capability} {surface}"
        elif family == 6:
            capability = pick(compute_capabilities, cycle, 31)
            ecosystem = pick(compute_ecosystems, cycle, 37) or "Python"
            query = f"compute_tool::{capability} {ecosystem}"
        elif family == 7:
            if incumbents:
                query = f"incumbent_change::{pick(incumbents, cycle, 17)} {pick(changes, cycle, 23)}"
            else:
                query = f"incumbent_change::{pick(intelligence_capabilities, cycle, 17)} {pick(changes, cycle, 23)}"
        elif family == 8:
            if local_terms:
                language, term = local_terms[(cycle * stride_for(len(local_terms), 31)) % len(local_terms)]
                anchor = pick(["API", "open source", "dataset", "library", "MCP"], cycle, 3)
                query = f"multilingual::{term} {anchor} {language}"
            else:
                query = f"intelligence_tool::{pick(intelligence_capabilities, cycle, 31)} open source"
        else:
            if trends:
                anchor = pick(["API", "dataset", "open source", "MCP", "library"], cycle, 3)
                query = f"trend::{pick(trends, cycle, 7)} {anchor}"
            else:
                query = f"compute_tool::{pick(compute_capabilities, cycle + 1, 31)} open source"
        queries.append(query)

    return queries, cursor + limit


def split_query(query: str) -> tuple[str, str]:
    if "::" not in query:
        return "source", query.strip()
    kind, raw = query.split("::", 1)
    kind = kind.strip()
    return (kind if kind in QUERY_PREFIXES else "source"), raw.strip()


def github_query(kind: str, raw: str) -> str:
    tokens = re.findall(r"[\w.+#/-]+", raw, flags=re.UNICODE)
    stop = {"or", "and", "the", "a", "an", "official", "maintained", "free"}
    compact: list[str] = []
    for token in tokens:
        if token.casefold() in stop:
            continue
        if token not in compact:
            compact.append(token)
        if len(compact) >= 7:
            break
    suffix = {
        "source": ["data"],
        "protocol": ["API"],
        "institution": ["data"],
        "publication": ["dataset"],
        "regional_source": ["data"],
        "intelligence_tool": ["library"],
        "compute_tool": ["package"],
        "incumbent_change": ["release"],
        "multilingual": ["API"],
        "trend": ["API"],
    }.get(kind, [])
    for token in suffix:
        if token.casefold() not in {value.casefold() for value in compact}:
            compact.append(token)
    return " ".join(compact[:8])


def adaptive_search(engine: str, query: str, token: str) -> list[Mapping[str, Any]]:
    kind, raw = split_query(query)
    if engine == "github":
        params = runtime.urllib.parse.urlencode(
            {"q": github_query(kind, raw), "sort": "updated", "order": "desc", "per_page": 10}
        )
        data = runtime.request_json(
            "https://api.github.com/search/repositories?" + params,
            headers={"Authorization": f"Bearer {token}", "X-GitHub-Api-Version": "2022-11-28"},
        )
    elif engine == "tavily":
        data = runtime.request_json(
            "https://api.tavily.com/search",
            "POST",
            {
                "api_key": token,
                "query": raw,
                "search_depth": "advanced",
                "max_results": 8,
                "include_answer": False,
                "include_raw_content": False,
            },
        )
    else:
        data = runtime.request_json(
            "https://api.exa.ai/search",
            "POST",
            {"query": raw, "numResults": 8, "type": "auto", "contents": {"text": {"maxCharacters": 800}}},
            {"x-api-key": token},
        )
    return list(data.get("items") or data.get("results") or [])


runtime.query_set = query_set
runtime.search = adaptive_search


if __name__ == "__main__":
    raise SystemExit(runtime.main(sys.argv[1:]))
