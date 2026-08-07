#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any, Mapping

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import prc_justice_self_iteration as base  # noqa: E402

PLAN_PATH = HERE / "prc-justice-trend-source-plan.json"
POLICY_PATH = HERE / "prc-justice-self-iteration-policy.json"


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def save_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(value), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def save_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n")


def parse_result_date(value: str) -> str | None:
    text = str(value or "").strip()
    if len(text) >= 10:
        candidate = text[:10]
        try:
            return base.datetime.fromisoformat(candidate).date().isoformat()
        except ValueError:
            pass
    return None


def select_query_rows(plan: Mapping[str, Any], selected_types: set[str], query_limit: int) -> list[tuple[str, str]]:
    by_type: dict[str, list[str]] = {}
    ordered_types: list[str] = []
    for row in plan.get("signal_plans") or []:
        signal_type = str(row.get("signal_type") or "")
        if signal_type not in selected_types:
            continue
        queries = [str(q).strip() for q in row.get("query_templates") or [] if str(q).strip()]
        if not queries:
            continue
        ordered_types.append(signal_type)
        by_type[signal_type] = queries

    limit = max(1, int(query_limit))
    rows: list[tuple[str, str]] = []
    index = 0
    while len(rows) < limit:
        progressed = False
        for signal_type in ordered_types:
            queries = by_type[signal_type]
            if index < len(queries):
                rows.append((signal_type, queries[index]))
                progressed = True
                if len(rows) >= limit:
                    break
        if not progressed:
            break
        index += 1
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=("auto", "daily", "weekly"), default="auto")
    parser.add_argument("--output-dir", default="prc-justice-trend-discovery")
    parser.add_argument("--max-queries-daily", type=int, default=6)
    parser.add_argument("--max-queries-weekly", type=int, default=12)
    parser.add_argument("--results-per-query", type=int, default=5)
    args = parser.parse_args()

    plan = base.load_json(PLAN_PATH)
    policy = base.load_json(POLICY_PATH)
    now = base.utc_now()
    profile = args.profile
    if profile == "auto":
        profile = "weekly" if now.weekday() == 6 else "daily"

    selected_types = set(plan["cadence"]["daily"])
    if profile == "weekly":
        selected_types |= set(plan["cadence"]["weekly"])

    query_limit = args.max_queries_weekly if profile == "weekly" else args.max_queries_daily
    query_rows = select_query_rows(plan, selected_types, query_limit)
    queried_types = {signal_type for signal_type, _ in query_rows}
    if query_limit >= len(selected_types) and queried_types != selected_types:
        missing = sorted(selected_types - queried_types)
        raise RuntimeError(f"query_planner_failed_to_cover_selected_signal_types:{missing}")

    result_limit = max(1, min(args.results_per_query, 8))
    timeout = int(policy["limits"]["request_timeout_seconds"])
    start_date = (now - timedelta(days=int(policy["cadence"]["maximum_age_days_for_search"]))).isoformat()

    tokens = {
        "tavily": str(os.getenv("TAVILY_API_KEY") or "").strip(),
        "exa": str(os.getenv("EXA_API_KEY") or "").strip(),
    }
    active = [name for name, token in tokens.items() if token]
    allowed_hosts = {
        str(x).casefold()
        for x in list(policy["primary_outcome_hosts"]) + list(policy["source_view_hosts"])
    }
    allowed_hosts |= {"ccgp.gov.cn", "gov.cn", "npc.gov.cn"}

    found: list[dict[str, Any]] = []
    errors: list[str] = []
    for signal_type, query in query_rows:
        if tokens["tavily"]:
            try:
                for row in base.search_tavily(query, tokens["tavily"], result_limit, timeout):
                    found.append({**row, "signal_type": signal_type})
            except Exception as exc:
                errors.append(f"tavily:{signal_type}:{type(exc).__name__}:{str(exc)[:160]}")
        if tokens["exa"]:
            try:
                for row in base.search_exa(query, tokens["exa"], result_limit, timeout, start_date):
                    found.append({**row, "signal_type": signal_type})
            except Exception as exc:
                errors.append(f"exa:{signal_type}:{type(exc).__name__}:{str(exc)[:160]}")

    dedup: dict[tuple[str, str], dict[str, Any]] = {}
    for row in found:
        url = base.safe_https_url(str(row.get("url") or ""), allowed_hosts, resolve=False)
        if not url:
            continue
        key = (str(row.get("signal_type") or ""), url)
        if key not in dedup:
            row = dict(row)
            row["url"] = url
            dedup[key] = row

    run_date = now.date().isoformat()
    events: list[dict[str, Any]] = []
    for (signal_type, url), row in list(dedup.items())[:80]:
        published = parse_result_date(str(row.get("published_date") or ""))
        fingerprint = stable_hash("|".join([
            url,
            str(row.get("title") or ""),
            str(row.get("snippet") or ""),
            signal_type,
        ]))
        events.append({
            "event_id": f"discover-{signal_type}-{fingerprint[:16]}",
            "event_date": published or run_date,
            "publication_date": published,
            "institution_type": "cross_institution",
            "institution_name": None,
            "region": None,
            "signal_type": signal_type,
            "subject_type": "capability" if signal_type in {"education_and_training","research","standard","procurement_and_budget","talent_and_recruitment","infrastructure_and_deployment","case_practice"} else ("doctrine" if signal_type == "doctrine_and_commentary" else ("enforcement" if signal_type in {"judicial_outcome","statistics_and_report"} else "institutional_capacity")),
            "capability_ids": [],
            "technology_terms": [],
            "legal_domains": [],
            "procedural_stage": None,
            "case_type": None,
            "metrics": {},
            "lifecycle_stage": None,
            "support_or_conflict": "NEUTRAL",
            "source": {
                "url": url,
                "host": str(base.urllib.parse.urlsplit(url).hostname or ""),
                "source_class": "secondary_discovery",
                "primary": False,
                "title": str(row.get("title") or "")[:500] or None,
                "content_fingerprint": fingerprint,
                "retrieved_at": now.replace(microsecond=0).isoformat()
            },
            "evidence_ids": [],
            "model_analysis": None,
            "review_status": "DISCOVERED",
            "safety": {
                "public_or_authorized": True,
                "contains_secret_operational_detail": False,
                "contains_targeting_or_evasion_detail": False,
                "contains_personal_targeting": False
            }
        })

    output_dir = Path(args.output_dir)
    save_jsonl(output_dir / "discovered-signal-events.jsonl", events)
    report = {
        "status": "PASS" if active else "FAIL_NO_DISCOVERY_KEY",
        "profile": profile,
        "run_at": now.replace(microsecond=0).isoformat(),
        "active_search_engines": active,
        "query_count": len(query_rows),
        "selected_signal_types": sorted(selected_types),
        "queried_signal_types": sorted(queried_types),
        "signal_type_coverage_complete": queried_types == selected_types if query_limit >= len(selected_types) else None,
        "raw_result_count": len(found),
        "official_or_approved_url_count": len(dedup),
        "discovered_event_count": len(events),
        "search_errors": errors,
        "primary_fact_claims_created": 0,
        "network_used": bool(active),
        "model_calls": 0,
        "compute_calls": 0,
        "discovery_only": True
    }
    save_json(output_dir / "discovery-report.json", report)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if active else 3


if __name__ == "__main__":
    raise SystemExit(main())
