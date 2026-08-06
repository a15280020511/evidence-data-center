#!/usr/bin/env python3
"""Resolve an Anna's Archive catalog domain live from Wikimedia and search metadata.

No Anna domain is persisted. Every run queries Wikidata/Wikipedia, ranks current
root-domain candidates, validates the public search-result contract, uses the
first healthy candidate only for that run, and discards it afterwards.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import catalog_domain_discovery as domain_discovery
import catalog_web_search as web_probe


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def validate_runtime_registry(registry: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if registry.get("schema_version") != "catalog-domain-registry-v1":
        errors.append("unsupported schema_version")
    if registry.get("mode") != "metadata-only":
        errors.append("mode must be metadata-only")
    policy = registry.get("policy")
    if not isinstance(policy, Mapping):
        return ["policy missing"]
    required = {
        "https_required": True,
        "fail_closed": True,
        "no_persisted_domains": True,
        "resolve_from_wikimedia_each_run": True,
        "automatic_domain_promotion": False,
        "follow_cross_domain_redirects": False,
        "unknown_domains_allowed": False,
    }
    for key, expected in required.items():
        if policy.get(key) is not expected:
            errors.append(f"policy {key} must be {expected!r}")
    domains = registry.get("domains")
    if domains not in ([], None):
        errors.append("Anna domains must not be persisted")
    minimum_score = policy.get("minimum_source_score")
    if not isinstance(minimum_score, int) or minimum_score < 1:
        errors.append("minimum_source_score must be a positive integer")
    maximum = policy.get("maximum_runtime_candidates")
    if not isinstance(maximum, int) or not 1 <= maximum <= 20:
        errors.append("maximum_runtime_candidates must be between 1 and 20")
    try:
        domain_discovery.discovery_config(registry)
    except Exception as exc:
        errors.append(f"invalid discovery configuration: {exc}")
    return errors


def has_wikimedia_source(row: Mapping[str, Any]) -> bool:
    for source in row.get("sources") or []:
        if not isinstance(source, Mapping):
            continue
        if source.get("type") in {"wikidata-P856", "wikipedia-external-link"}:
            return True
    return False


def runtime_candidates(
    discovery_report: Mapping[str, Any],
    *,
    minimum_score: int,
    maximum: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in discovery_report.get("candidates") or []:
        if not isinstance(raw, Mapping):
            continue
        if raw.get("candidate_kind") != "root-domain":
            continue
        score = int(raw.get("source_score") or 0)
        if score < minimum_score or not has_wikimedia_source(raw):
            continue
        domain = str(raw.get("candidate_domain") or "")
        try:
            normalized = web_probe.normalize_domain(domain)
        except ValueError:
            continue
        row = dict(raw)
        row["candidate_domain"] = normalized
        row["source_score"] = score
        rows.append(row)
    rows.sort(key=lambda item: (-int(item["source_score"]), item["candidate_domain"]))
    return rows[:maximum]


def search_catalog_runtime(
    registry: Mapping[str, Any],
    query: str,
    *,
    timeout: int = 18,
    max_bytes: int = 2_000_000,
    max_titles: int = 10,
    retries: int = 2,
) -> dict[str, Any]:
    errors = validate_runtime_registry(registry)
    normalized_query = " ".join(query.split()).strip()
    if not normalized_query:
        errors.append("query is empty")
    if len(normalized_query) > 200:
        errors.append("query exceeds 200 characters")
    if errors:
        return {
            "schema_version": "catalog-runtime-search-report-v1",
            "generated_at": utc_now(),
            "status": "fail",
            "query": normalized_query,
            "policy_errors": errors,
            "selected_domain": None,
            "domain_persisted": False,
        }

    try:
        discovery_report = domain_discovery.discover(
            registry,
            timeout=timeout,
            max_bytes=min(max_bytes, 2_000_000),
        )
    except Exception as exc:
        return {
            "schema_version": "catalog-runtime-search-report-v1",
            "generated_at": utc_now(),
            "status": "unavailable",
            "query": normalized_query,
            "policy_errors": [],
            "resolution_error": f"{type(exc).__name__}: {str(exc)[:300]}",
            "selected_domain": None,
            "domain_persisted": False,
            "manual_review_required": True,
        }

    policy = registry["policy"]
    candidates = runtime_candidates(
        discovery_report,
        minimum_score=int(policy["minimum_source_score"]),
        maximum=int(policy["maximum_runtime_candidates"]),
    )
    probes: list[dict[str, Any]] = []
    selected: dict[str, Any] | None = None
    selected_candidate: dict[str, Any] | None = None
    for candidate in candidates:
        result = web_probe.probe_domain(
            candidate["candidate_domain"],
            normalized_query,
            timeout=timeout,
            max_bytes=max_bytes,
            max_titles=max_titles,
            retries=retries,
        )
        probes.append(result)
        if result.get("status") == "healthy":
            selected = result
            selected_candidate = candidate
            break

    status = "pass" if selected is not None else "unavailable"
    return {
        "schema_version": "catalog-runtime-search-report-v1",
        "generated_at": utc_now(),
        "status": status,
        "scope": "public search-result metadata only",
        "query": normalized_query,
        "resolution_source": "live Wikidata/Wikipedia APIs",
        "domain_persisted": False,
        "stored_domain_count": 0,
        "selected_domain": selected.get("domain") if selected else None,
        "selected_candidate_sources": selected_candidate.get("sources", []) if selected_candidate else [],
        "selected_candidate_score": selected_candidate.get("source_score") if selected_candidate else None,
        "result_count_observed": selected.get("result_count_observed", 0) if selected else 0,
        "sample_titles": selected.get("sample_titles", []) if selected else [],
        "runtime_candidates": candidates,
        "runtime_probes": probes,
        "manual_review_required": selected is None,
        "discovery_status": discovery_report.get("status"),
        "discovery_source_errors": discovery_report.get("source_errors", []),
        "safety": {
            "domain_saved_after_run": False,
            "cross_domain_redirects_followed": False,
            "detail_pages_followed": False,
            "download_links_followed": False,
            "book_files_retrieved_from_anna": False,
            "access_controls_bypassed": False,
        },
        "policy_errors": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=18)
    parser.add_argument("--max-bytes", type=int, default=2_000_000)
    parser.add_argument("--max-titles", type=int, default=10)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--enforce", action="store_true")
    args = parser.parse_args()
    report = search_catalog_runtime(
        load_json(args.registry),
        args.query,
        timeout=min(max(args.timeout, 5), 30),
        max_bytes=min(max(args.max_bytes, 100_000), 3_000_000),
        max_titles=min(max(args.max_titles, 1), 20),
        retries=min(max(args.retries, 1), 3),
    )
    save_json(args.output, report)
    print(json.dumps({
        "status": report.get("status"),
        "resolution_source": report.get("resolution_source"),
        "stored_domain_count": report.get("stored_domain_count", 0),
        "selected_domain": report.get("selected_domain"),
        "result_count_observed": report.get("result_count_observed", 0),
        "runtime_candidates": len(report.get("runtime_candidates") or []),
    }, ensure_ascii=False))
    if args.enforce and report.get("status") != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
