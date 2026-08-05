#!/usr/bin/env python3
"""Resilient entry point for the isolated Information & Tool Radar.

This module extends ``radar.py`` without adding dependencies. Independent
fallbacks preserve category coverage while each failing provider remains
visible in the report.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
from typing import Any, Mapping

import radar as base

URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)


def common_crawl(config: Mapping[str, Any], runtime: Mapping[str, int]) -> base.AdapterResult:
    """Run capture probes and always retain the official index catalog signal."""
    try:
        result = base.common_crawl(config, runtime)
    except Exception as exc:
        result = base.AdapterResult("common_crawl", str(config["category"]))
        result.add_error(exc)

    index_id = str(result.details.get("index_id") or "")
    if not index_id:
        result.probes += 1
        try:
            catalog = base.request_json(
                str(config["index_catalog"]),
                timeout=runtime["timeout"],
                max_bytes=runtime["max_bytes"],
            )
            if not isinstance(catalog, list) or not catalog:
                raise RuntimeError("Common Crawl index catalog was empty")
            latest = catalog[0]
            index_id = str(latest.get("id") or "")
            result.details["index_id"] = index_id
            result.successful_probes += 1
        except Exception as exc:
            result.add_error(f"catalog fallback: {type(exc).__name__}: {exc}")

    if index_id:
        locator = f"https://index.commoncrawl.org/{urllib.parse.quote(index_id)}-index"
        result.candidates.append(
            base.make_candidate(
                result.name,
                result.category,
                f"Common Crawl index {index_id}",
                locator,
                {
                    "index_id": index_id,
                    "coverage_level": "official-index-catalog",
                    "capture_queries_degraded": not any(
                        item.get("evidence", {}).get("timestamp") for item in result.candidates
                    ),
                },
                status="reference",
            )
        )
        result.success = True
    return result


def _manifest_candidates(
    result: base.AdapterResult,
    payload: str,
    source_url: str,
    maximum: int,
) -> int:
    added = 0
    seen: set[str] = set()
    for raw_line in payload.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        matches = URL_RE.findall(line)
        if matches:
            locators = matches
        else:
            token = line.split()[-1]
            if not token or token.startswith("#"):
                continue
            locators = [urllib.parse.urljoin(source_url, token)]
        for locator in locators:
            locator = locator.rstrip(".,;)")
            if locator in seen:
                continue
            seen.add(locator)
            result.candidates.append(
                base.make_candidate(
                    result.name,
                    result.category,
                    "GDELT Web NGrams update manifest",
                    locator,
                    {
                        "manifest": source_url,
                        "coverage_level": "official-static-update-feed",
                    },
                    status="change_signal",
                )
            )
            added += 1
            if added >= maximum:
                return added
    return added


def gdelt(config: Mapping[str, Any], runtime: Mapping[str, int]) -> base.AdapterResult:
    """Use DOC API first and the official Web NGrams update feed on throttling."""
    try:
        result = base.gdelt(config, runtime)
    except Exception as exc:
        result = base.AdapterResult("gdelt", str(config["category"]))
        result.add_error(exc)

    if result.candidates:
        return result

    fallback = str(config.get("fallback_feed") or "")
    if not fallback:
        return result
    result.probes += 1
    try:
        payload = base.request_bytes(
            fallback,
            timeout=runtime["timeout"],
            max_bytes=runtime["max_bytes"],
            attempts=3,
        ).decode("utf-8", errors="replace")
        added = _manifest_candidates(result, payload, fallback, runtime["max_records"])
        if not added:
            raise RuntimeError("GDELT update manifest contained no usable entries")
        result.successful_probes += 1
        result.details["fallback_used"] = "web-ngrams-lastupdate"
        result.success = True
    except Exception as exc:
        result.add_error(f"static fallback: {type(exc).__name__}: {exc}")
    return result


def crossref(config: Mapping[str, Any], runtime: Mapping[str, int]) -> base.AdapterResult:
    """Independent public research-metadata source for the research-data class."""
    result = base.AdapterResult("crossref", str(config["category"]))
    endpoint = str(config["endpoint"])
    for query in list(config.get("queries") or []):
        result.probes += 1
        try:
            url = base.query_url(
                endpoint,
                {
                    "query.bibliographic": query,
                    "rows": runtime["max_records"],
                    "select": "DOI,title,URL,type,publisher,created,resource",
                    "mailto": "a15280020511@users.noreply.github.com",
                },
            )
            data = base.request_json(
                url,
                timeout=runtime["timeout"],
                max_bytes=runtime["max_bytes"],
                attempts=3,
            )
            message = data.get("message") if isinstance(data, Mapping) else {}
            rows = message.get("items") if isinstance(message, Mapping) else []
            if not isinstance(rows, list):
                raise RuntimeError("Crossref items missing")
            result.successful_probes += 1
            for item in rows[: runtime["max_records"]]:
                if not isinstance(item, Mapping):
                    continue
                titles = item.get("title") if isinstance(item.get("title"), list) else []
                doi = str(item.get("DOI") or "")
                locator = str(item.get("URL") or (f"https://doi.org/{doi}" if doi else ""))
                if not locator:
                    continue
                title = str(titles[0]) if titles else (doi or str(query))
                result.candidates.append(
                    base.make_candidate(
                        result.name,
                        result.category,
                        title,
                        locator,
                        {
                            "query": query,
                            "doi": doi,
                            "type": item.get("type"),
                            "publisher": item.get("publisher"),
                            "created": item.get("created"),
                            "coverage_level": "independent-research-metadata",
                        },
                        status="reference",
                    )
                )
        except Exception as exc:
            result.add_error(f"{query}: {type(exc).__name__}: {exc}")
    result.success = result.successful_probes > 0 and bool(result.candidates)
    return result


base.ADAPTERS["common_crawl"] = common_crawl
base.ADAPTERS["gdelt"] = gdelt
base.ADAPTERS["crossref"] = crossref


if __name__ == "__main__":
    raise SystemExit(base.main(sys.argv[1:]))
