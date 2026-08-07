#!/usr/bin/env python3
"""Truthful, resilient coverage gate for the Information & Tool Radar."""
from __future__ import annotations

import json
import sys
import urllib.parse
from typing import Any, Iterable, Mapping

import radar as base
import radar_v3  # installs prior resilience and latency bounds

_ORIGINAL_BUILD_REPORT = base.build_report


def parse_cdx_payload(payload: bytes) -> list[dict[str, Any]]:
    """Parse CDX JSON arrays, JSON objects, or newline-delimited JSON."""
    text = payload.decode("utf-8", errors="replace").strip()
    if not text:
        return []
    try:
        return base.parse_cdx(json.loads(text))
    except json.JSONDecodeError:
        pass

    objects: list[Any] = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            objects.append(json.loads(line))
    if not objects:
        return []
    if all(isinstance(item, Mapping) for item in objects):
        return [dict(item) for item in objects]
    if isinstance(objects[0], list) and all(isinstance(value, str) for value in objects[0]):
        header = objects[0]
        return [dict(zip(header, row)) for row in objects[1:] if isinstance(row, list)]
    rows: list[dict[str, Any]] = []
    for item in objects:
        if isinstance(item, Mapping):
            rows.append(dict(item))
    return rows


def wayback(config: Mapping[str, Any], runtime: Mapping[str, int]) -> base.AdapterResult:
    """Use fast Internet Archive probes and parse Arquivo.pt JSONL fallback."""
    result = base.AdapterResult("wayback", str(config["category"]))
    primary = str(config.get("endpoint") or "")
    fallback = str(config.get("fallback_endpoint") or "")
    result.details["backend_success"] = {primary: 0, fallback: 0}

    for domain in list(config.get("probe_domains") or []):
        result.probes += 1
        rows: list[dict[str, Any]] = []
        backend = ""
        if primary:
            try:
                data = base.request_json(
                    base.query_url(primary, {
                        "url": domain,
                        "output": "json",
                        "fl": "timestamp,original,statuscode,digest",
                        "filter": "statuscode:200",
                        "collapse": "digest",
                        "limit": runtime["max_records"],
                    }),
                    timeout=min(runtime["timeout"], 5),
                    max_bytes=runtime["max_bytes"],
                    attempts=1,
                )
                rows = base.parse_cdx(data)
                backend = "internet-archive"
                result.details["backend_success"][primary] += 1
            except Exception as exc:
                result.add_error(f"{domain} via {primary}: {type(exc).__name__}: {exc}")

        if not rows and fallback:
            try:
                payload = base.request_bytes(
                    base.query_url(fallback, {
                        "url": domain,
                        "output": "json",
                        "limit": runtime["max_records"],
                    }),
                    timeout=min(runtime["timeout"], 12),
                    max_bytes=runtime["max_bytes"],
                    attempts=2,
                )
                rows = parse_cdx_payload(payload)
                backend = "arquivo.pt"
                result.details["backend_success"][fallback] += 1
            except Exception as exc:
                result.add_error(f"{domain} via {fallback}: {type(exc).__name__}: {exc}")

        if rows:
            result.successful_probes += 1
        for item in rows[: runtime["max_records"]]:
            original = str(item.get("original") or item.get("url") or domain)
            timestamp = str(item.get("timestamp") or "")
            if backend == "arquivo.pt":
                locator = f"https://arquivo.pt/wayback/{timestamp}/{original}" if timestamp else original
            else:
                locator = f"https://web.archive.org/web/{timestamp}/{original}" if timestamp else original
            result.candidates.append(base.make_candidate(
                result.name,
                result.category,
                f"Archived snapshot: {domain}",
                locator,
                {**item, "archive_backend": backend},
                status="reference",
            ))
    result.success = result.successful_probes > 0 and bool(result.candidates)
    return result


def _append_reliefweb_candidates(
    result: base.AdapterResult,
    rows: list[Any],
    max_records: int,
) -> None:
    for item in rows[:max_records]:
        if not isinstance(item, Mapping):
            continue
        fields = item.get("fields") if isinstance(item.get("fields"), Mapping) else {}
        title = str(fields.get("name") or fields.get("title") or item.get("id") or "ReliefWeb disaster")
        locator = str(fields.get("url") or item.get("href") or "")
        if not locator:
            continue
        countries = fields.get("country") if isinstance(fields.get("country"), list) else []
        country = None
        if countries and isinstance(countries[0], Mapping):
            country = str(countries[0].get("name") or "") or None
        result.candidates.append(base.make_candidate(
            result.name,
            result.category,
            title,
            locator,
            {
                "id": item.get("id"),
                "status": fields.get("status"),
                "date": fields.get("date"),
                "glide": fields.get("glide"),
                "coverage_level": "curated-humanitarian-event-metadata",
                "event_backend": "reliefweb",
            },
            country=country,
            status="change_signal",
        ))


def _append_eonet_candidates(
    result: base.AdapterResult,
    rows: list[Any],
    max_records: int,
) -> None:
    for item in rows[:max_records]:
        if not isinstance(item, Mapping):
            continue
        title = str(item.get("title") or item.get("id") or "NASA EONET event")
        locator = str(item.get("link") or "")
        if not locator:
            sources = item.get("sources") if isinstance(item.get("sources"), list) else []
            if sources and isinstance(sources[0], Mapping):
                locator = str(sources[0].get("url") or "")
        if not locator:
            continue
        categories = item.get("categories") if isinstance(item.get("categories"), list) else []
        category_ids = [
            str(row.get("id") or row.get("title") or "")
            for row in categories
            if isinstance(row, Mapping)
        ]
        geometry = item.get("geometry") if isinstance(item.get("geometry"), list) else []
        latest_geometry = geometry[-1] if geometry and isinstance(geometry[-1], Mapping) else {}
        result.candidates.append(base.make_candidate(
            result.name,
            result.category,
            title,
            locator,
            {
                "id": item.get("id"),
                "closed": item.get("closed"),
                "categories": category_ids,
                "latest_date": latest_geometry.get("date"),
                "coverage_level": "public-natural-event-metadata",
                "event_backend": "nasa-eonet",
            },
            status="change_signal",
        ))


def reliefweb(config: Mapping[str, Any], runtime: Mapping[str, int]) -> base.AdapterResult:
    """Read ReliefWeb, falling back to NASA EONET without weakening the gate."""
    result = base.AdapterResult("reliefweb", str(config["category"]))
    primary = str(config.get("endpoint") or "")
    fallback = str(config.get("fallback_endpoint") or "")
    result.details["backend_success"] = {"reliefweb": 0, "nasa-eonet": 0}

    result.probes += 1
    try:
        data = base.request_json(
            base.query_url(primary, {
                "appname": str(config.get("appname") or "evidence-data-center"),
                "preset": "latest",
                "profile": "list",
                "slim": 1,
                "limit": runtime["max_records"],
            }),
            timeout=runtime["timeout"],
            max_bytes=runtime["max_bytes"],
            attempts=1,
        )
        rows = data.get("data") if isinstance(data, Mapping) else []
        if not isinstance(rows, list) or not rows:
            raise RuntimeError("ReliefWeb data missing")
        _append_reliefweb_candidates(result, rows, runtime["max_records"])
        if result.candidates:
            result.successful_probes += 1
            result.details["backend_success"]["reliefweb"] += 1
    except Exception as exc:
        result.add_error(f"ReliefWeb primary: {type(exc).__name__}: {exc}")

    if not result.candidates and fallback:
        result.probes += 1
        try:
            data = base.request_json(
                base.query_url(fallback, {
                    "status": "open",
                    "limit": runtime["max_records"],
                }),
                timeout=runtime["timeout"],
                max_bytes=runtime["max_bytes"],
                attempts=1,
            )
            rows = data.get("events") if isinstance(data, Mapping) else []
            if not isinstance(rows, list) or not rows:
                raise RuntimeError("NASA EONET events missing")
            _append_eonet_candidates(result, rows, runtime["max_records"])
            if result.candidates:
                result.successful_probes += 1
                result.details["backend_success"]["nasa-eonet"] += 1
        except Exception as exc:
            result.add_error(f"NASA EONET fallback: {type(exc).__name__}: {exc}")

    result.success = result.successful_probes > 0 and bool(result.candidates)
    return result


def build_report(config: Mapping[str, Any], results: list[base.AdapterResult]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Gate required providers while reporting every optional provider failure."""
    report, candidates = _ORIGINAL_BUILD_REPORT(config, results)
    adapters_config = config.get("adapters") if isinstance(config.get("adapters"), Mapping) else {}
    required_names = {
        str(name)
        for name, row in adapters_config.items()
        if isinstance(row, Mapping)
        and bool(row.get("enabled", False))
        and bool(row.get("required_for_gate", True))
    }
    result_map = {result.name: result for result in results}
    required_succeeded = sum(1 for name in required_names if name in result_map and result_map[name].success)
    required_rate = required_succeeded / len(required_names) if required_names else 0.0
    required_threshold = float(config.get("minimum_required_adapter_success_rate") or 0.0)
    category_threshold = float(config.get("minimum_category_coverage") or 0.0)
    category_rate = float(report.get("metrics", {}).get("category_coverage") or 0.0)
    optional_degraded = sorted(
        result.name for result in results if result.name not in required_names and not result.success
    )
    required_failed = sorted(
        name for name in required_names if name not in result_map or not result_map[name].success
    )

    metrics = report.setdefault("metrics", {})
    metrics["all_adapter_success_rate"] = metrics.get("adapter_success_rate", 0.0)
    metrics["required_adapters_enabled"] = len(required_names)
    metrics["required_adapters_succeeded"] = required_succeeded
    metrics["required_adapter_success_rate"] = round(required_rate, 4)
    metrics["optional_adapters_degraded"] = len(optional_degraded)
    report["required_adapter_failures"] = required_failed
    report["degraded_optional_adapters"] = optional_degraded
    report["thresholds"] = {
        "minimum_required_adapter_success_rate": required_threshold,
        "minimum_category_coverage": category_threshold,
    }
    report["status"] = (
        "pass" if required_rate >= required_threshold and category_rate >= category_threshold else "fail"
    )
    return report, candidates


base.ADAPTERS["wayback"] = wayback
base.ADAPTERS["reliefweb"] = reliefweb
base.build_report = build_report


if __name__ == "__main__":
    raise SystemExit(base.main(sys.argv[1:]))
