#!/usr/bin/env python3
"""Latency-bounded production candidate for the Information & Tool Radar."""
from __future__ import annotations

import sys
from typing import Any, Mapping

import radar as base
import radar_v2  # installs Common Crawl, GDELT and Crossref resilience


def wayback(config: Mapping[str, Any], runtime: Mapping[str, int]) -> base.AdapterResult:
    """Fail fast on the unstable primary archive and preserve a bounded fallback."""
    result = base.AdapterResult("wayback", str(config["category"]))
    primary = str(config.get("endpoint") or "")
    fallback = str(config.get("fallback_endpoint") or "")
    backends = [(primary, min(runtime["timeout"], 6), 1), (fallback, min(runtime["timeout"], 12), 2)]
    result.details["backend_success"] = {url: 0 for url, _, _ in backends if url}

    for domain in list(config.get("probe_domains") or []):
        result.probes += 1
        for endpoint, timeout, attempts in backends:
            if not endpoint:
                continue
            try:
                params: dict[str, Any] = {
                    "url": domain,
                    "output": "json",
                    "limit": runtime["max_records"],
                }
                if "web.archive.org" in endpoint:
                    params.update({
                        "fl": "timestamp,original,statuscode,digest",
                        "filter": "statuscode:200",
                        "collapse": "digest",
                    })
                rows = base.parse_cdx(base.request_json(
                    base.query_url(endpoint, params),
                    timeout=timeout,
                    max_bytes=runtime["max_bytes"],
                    attempts=attempts,
                ))
                result.successful_probes += 1
                result.details["backend_success"][endpoint] += 1
                for item in rows[: runtime["max_records"]]:
                    original = str(item.get("original") or item.get("url") or domain)
                    timestamp = str(item.get("timestamp") or "")
                    is_arquivo = "arquivo.pt" in endpoint
                    replay = (
                        f"https://arquivo.pt/wayback/{timestamp}/{original}"
                        if is_arquivo and timestamp
                        else f"https://web.archive.org/web/{timestamp}/{original}"
                        if timestamp
                        else original
                    )
                    result.candidates.append(base.make_candidate(
                        result.name,
                        result.category,
                        f"Archived snapshot: {domain}",
                        replay,
                        {**item, "archive_backend": "arquivo.pt" if is_arquivo else "internet-archive"},
                        status="reference",
                    ))
                break
            except Exception as exc:
                result.add_error(f"{domain} via {endpoint}: {type(exc).__name__}: {exc}")
    result.success = result.successful_probes > 0 and bool(result.candidates)
    return result


def datacite(config: Mapping[str, Any], runtime: Mapping[str, int]) -> base.AdapterResult:
    """Keep DataCite visible as an independent health probe without blocking the radar."""
    result = base.AdapterResult("datacite", str(config["category"]))
    endpoint = str(config["endpoint"])
    queries = list(config.get("queries") or [])[:2]
    for query in queries:
        result.probes += 1
        try:
            rows = base.datacite_rows(base.request_json(
                base.query_url(endpoint, {"query": query, "page[size]": runtime["max_records"]}),
                timeout=min(runtime["timeout"], 8),
                max_bytes=runtime["max_bytes"],
                attempts=1,
            ))
            result.successful_probes += 1
            base.add_datacite_candidates(result, rows, str(query), runtime["max_records"])
        except Exception as exc:
            result.add_error(f"{query}: {type(exc).__name__}: {exc}")

    if not result.candidates:
        result.probes += 1
        params = dict(config.get("fallback_parameters") or {})
        params["page[size]"] = runtime["max_records"]
        try:
            rows = base.datacite_rows(base.request_json(
                base.query_url(endpoint, params),
                timeout=min(runtime["timeout"], 8),
                max_bytes=runtime["max_bytes"],
                attempts=1,
            ))
            result.successful_probes += 1
            result.details["fallback_used"] = True
            base.add_datacite_candidates(result, rows, "recent datasets fallback", runtime["max_records"])
        except Exception as exc:
            result.add_error(f"fallback: {type(exc).__name__}: {exc}")
    result.success = result.successful_probes > 0 and bool(result.candidates)
    return result


base.ADAPTERS["wayback"] = wayback
base.ADAPTERS["datacite"] = datacite


if __name__ == "__main__":
    raise SystemExit(base.main(sys.argv[1:]))
