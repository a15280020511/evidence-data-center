#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import time
import urllib.parse
from datetime import timedelta
from pathlib import Path
from typing import Any, Iterable, Mapping

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import prc_justice_self_iteration as base  # noqa: E402

PLAN_PATH = HERE / "prc-justice-trend-source-plan.json"
POLICY_PATH = HERE / "prc-justice-self-iteration-policy.json"
LEDGER_PATH = HERE / "prc-justice-verified-signal-ledger.json"

ACCESS_CONTROL_MARKERS = (
    "captcha",
    "验证码",
    "访问验证",
    "安全验证",
    "access denied",
    "forbidden",
    "waf",
    "请求过于频繁",
    "访问受限",
)

SIGNAL_LIFECYCLE = {
    "education_and_training": "TRAINING_SIGNAL",
    "research": "RESEARCH_SIGNAL",
    "standard": "STANDARDIZED",
    "procurement_and_budget": "INVESTING",
    "infrastructure_and_deployment": "DEPLOYING",
    "case_practice": "FIRST_PRACTICE",
    "judicial_outcome": "FIRST_PRACTICE",
    "doctrine_and_commentary": "CONCEPT",
}

# These terms mean an evidentiary/procedural contradiction only in concrete
# case/outcome materials. The same words in a statute, interpretation, policy,
# training text, or standard do not by themselves make that source contested.
CONFLICT_APPLICABLE_SIGNAL_TYPES = {"case_practice", "judicial_outcome"}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if isinstance(value, Mapping):
            rows.append(dict(value))
    return rows


def source_rows(doc: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    for key in ("sources", "source_families"):
        for row in doc.get(key) or []:
            if isinstance(row, Mapping) and row.get("source_id"):
                yield row


def build_source_registry(plan: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for name in (
        "source-catalog.json",
        "legal-system-matrix.json",
        "public-security-knowledge-practice-matrix.json",
        "prc-politico-legal-full-spectrum-matrix.json",
    ):
        doc = base.load_json(HERE / name)
        for row in source_rows(doc):
            registry[str(row["source_id"])] = dict(row)
    for row in plan.get("local_source_families") or []:
        if isinstance(row, Mapping) and row.get("source_id"):
            registry[str(row["source_id"])] = dict(row)
    return registry


def allowed_hosts(plan: Mapping[str, Any], registry: Mapping[str, Mapping[str, Any]]) -> set[str]:
    referenced = {
        str(source_id)
        for signal in plan.get("signal_plans") or []
        if isinstance(signal, Mapping)
        for source_id in signal.get("source_families") or []
    }
    hosts: set[str] = set()
    for source_id in referenced:
        row = registry.get(source_id) or {}
        for host in row.get("hosts") or []:
            text = str(host).casefold().strip().rstrip(".")
            if text and text not in {"edu.cn"}:
                hosts.add(text)
    # Generic edu.cn is useful for discovery but is intentionally too broad for
    # automatic primary ingestion. Explicitly registered academy hosts remain allowed.
    for signal in plan.get("signal_plans") or []:
        if isinstance(signal, Mapping):
            for host in signal.get("allowed_hosts") or []:
                text = str(host).casefold().strip().rstrip(".")
                if text:
                    hosts.add(text)
    return hosts


def classify_institution(host: str) -> str:
    host = host.casefold().strip().rstrip(".")

    # Specific judicial/procuratorial host patterns must precede generic gov.cn.
    if host == "spp.gov.cn" or host.endswith(".spp.gov.cn") or host.endswith("jcy.gov.cn"):
        return "procuratorate"
    if host == "court.gov.cn" or host.endswith(".court.gov.cn") or host.endswith("fy.gov.cn"):
        return "court"
    if host == "mps.gov.cn" or host.endswith(".mps.gov.cn"):
        return "public_security"
    if host.endswith(("cipuc.edu.cn", "ppsuc.edu.cn", "cppu.edu.cn", "njpu.edu.cn")):
        return "public_security"
    if host == "moj.gov.cn" or host.endswith(".moj.gov.cn") or host.endswith(("ssfjd.com", "ssfjd.cn")):
        return "justice_administration_and_forensics"
    if host == "ccdi.gov.cn" or host.endswith(".ccdi.gov.cn"):
        return "discipline_supervision"
    if host.endswith("chinalaw.org.cn"):
        return "judicial_education_or_research"
    if host == "npc.gov.cn" or host.endswith(".npc.gov.cn") or host == "gov.cn" or host.endswith(".gov.cn") or host.endswith("12371.cn"):
        return "legislature_or_rulemaker"
    return "cross_institution"


def institution_name_for_host(host: str, institution_type: str) -> str:
    host = host.casefold()
    if institution_type == "procuratorate" and host != "spp.gov.cn" and not host.endswith(".spp.gov.cn"):
        return "地方检察机关公开来源"
    if institution_type == "court" and host != "court.gov.cn" and not host.endswith(".court.gov.cn"):
        return "地方法院公开来源"
    if institution_type == "judicial_education_or_research":
        return "公开司法教育/研究来源"
    return base.institution_for_host(host)


def source_class(host: str) -> str:
    host = host.casefold()
    if host.endswith(".edu.cn") or host.endswith("chinalaw.org.cn"):
        return "academic_primary"
    return "official_primary"


def safe_title(event: Mapping[str, Any], page_text: str) -> str | None:
    source = event.get("source") or {}
    title = base.normalized_text(source.get("title"))
    if title:
        return title[:500]
    return base.normalized_text(page_text[:180])[:500] or None


def stable_event_id(signal_type: str, url: str, publication_date: str, page_fingerprint: str) -> str:
    digest = hashlib.sha256(f"{signal_type}|{url}|{publication_date}|{page_fingerprint}".encode("utf-8")).hexdigest()
    return f"verified-{signal_type}-{publication_date.replace('-', '')}-{digest[:14]}"


def verify_event(
    event: Mapping[str, Any],
    *,
    allowed: set[str],
    policy: Mapping[str, Any],
    cutoff_date: str,
    now_date: str,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    source = event.get("source") or {}
    url = str(source.get("url") or "")
    signal_type = str(event.get("signal_type") or "")
    record: dict[str, Any] = {
        "discovery_event_id": event.get("event_id"),
        "url": url,
        "signal_type": signal_type,
        "status": "REVIEW_ONLY",
        "reason": None,
    }
    safe = base.safe_https_url(url, allowed, resolve=True)
    if not safe:
        record["reason"] = "unsafe_unresolved_or_unapproved_primary_url"
        return None, record

    fetch_policy = copy.deepcopy(dict(policy))
    fetch_policy["primary_outcome_hosts"] = sorted(allowed)
    try:
        page_text, fetch_meta = base.fetch_primary_page(safe, fetch_policy)
    except Exception as exc:
        record["reason"] = f"primary_fetch_failed:{type(exc).__name__}:{str(exc)[:180]}"
        return None, record

    if len(page_text) < 160:
        record["reason"] = "primary_page_too_little_text"
        return None, record
    folded = page_text.casefold()
    if any(marker in folded for marker in ACCESS_CONTROL_MARKERS):
        record["reason"] = "access_control_page_detected"
        return None, record
    if base.any_signal(page_text, policy.get("sensitive_operational_signals") or []):
        record["reason"] = "sensitive_operational_signal"
        return None, record

    pub_date = base.parse_date(str(event.get("publication_date") or ""), page_text)
    if not pub_date:
        record["reason"] = "publication_date_unverified"
        return None, record
    if pub_date < cutoff_date:
        record["reason"] = "historical_reference_outside_freshness_window"
        record["publication_date"] = pub_date
        return None, record
    if pub_date > now_date:
        record["reason"] = "future_publication_date_requires_review"
        record["publication_date"] = pub_date
        return None, record

    capabilities = base.matching_ids(page_text, policy.get("capability_patterns") or {})
    max_caps = int(policy["limits"]["max_capability_ids_per_observation"])
    if len(capabilities) > max_caps:
        capabilities = []
        record["capability_attribution_suppressed"] = "too_many_page_level_matches"

    conflict = (
        signal_type in CONFLICT_APPLICABLE_SIGNAL_TYPES
        and base.any_signal(page_text, policy.get("conflict_or_review_signals") or [])
    )
    host = str(urllib.parse.urlsplit(safe).hostname or "").casefold()
    institution_type = classify_institution(host)
    page_fingerprint = hashlib.sha256(base.normalized_text(page_text).encode("utf-8")).hexdigest()
    lifecycle = SIGNAL_LIFECYCLE.get(signal_type)
    if lifecycle == "FIRST_PRACTICE" and not capabilities:
        lifecycle = None

    verified = {
        "event_id": stable_event_id(signal_type, safe, pub_date, page_fingerprint),
        "event_date": pub_date,
        "publication_date": pub_date,
        "institution_type": institution_type,
        "institution_name": institution_name_for_host(host, institution_type),
        "region": None,
        "signal_type": signal_type,
        "subject_type": event.get("subject_type") or "institutional_capacity",
        "capability_ids": capabilities,
        "technology_terms": [],
        "legal_domains": [],
        "procedural_stage": None,
        "case_type": None,
        "metrics": {},
        "lifecycle_stage": lifecycle,
        "support_or_conflict": "CONFLICTS" if conflict else "SUPPORTS",
        "source": {
            "url": safe,
            "host": host,
            "source_class": source_class(host),
            "primary": True,
            "title": safe_title(event, page_text),
            "content_fingerprint": page_fingerprint,
            "retrieved_at": base.utc_now().replace(microsecond=0).isoformat(),
        },
        "evidence_ids": [str(event.get("event_id"))] if event.get("event_id") else [],
        "model_analysis": None,
        "review_status": "CONTESTED" if conflict else "PRIMARY_VERIFIED",
        "safety": {
            "public_or_authorized": True,
            "contains_secret_operational_detail": False,
            "contains_targeting_or_evasion_detail": False,
            "contains_personal_targeting": False,
        },
    }
    record.update({
        "status": verified["review_status"],
        "reason": None,
        "publication_date": pub_date,
        "host": host,
        "institution_type": institution_type,
        "matched_capability_ids": capabilities,
        "bytes_sampled": fetch_meta.get("bytes_sampled"),
        "content_type": fetch_meta.get("content_type"),
    })
    return verified, record


def append_new_events(ledger: dict[str, Any], events: list[dict[str, Any]]) -> tuple[dict[str, Any], list[str]]:
    """Append only non-contested PRIMARY_VERIFIED events.

    CONTESTED observations remain in run artifacts/review queues and are never
    silently promoted into the automatic long-term fact ledger.
    """
    existing_events = [dict(row) for row in ledger.get("events") or [] if isinstance(row, Mapping)]
    existing_ids = {str(row.get("event_id")) for row in existing_events if row.get("event_id")}
    existing_fingerprints = {
        str((row.get("source") or {}).get("content_fingerprint"))
        for row in existing_events
        if isinstance(row.get("source"), Mapping) and (row.get("source") or {}).get("content_fingerprint")
    }
    added: list[str] = []
    for event in events:
        if event.get("review_status") != "PRIMARY_VERIFIED" or event.get("support_or_conflict") != "SUPPORTS":
            continue
        event_id = str(event.get("event_id") or "")
        fingerprint = str((event.get("source") or {}).get("content_fingerprint") or "")
        if not event_id or event_id in existing_ids or (fingerprint and fingerprint in existing_fingerprints):
            continue
        existing_events.append(event)
        existing_ids.add(event_id)
        if fingerprint:
            existing_fingerprints.add(fingerprint)
        added.append(event_id)
    updated = dict(ledger)
    updated["events"] = existing_events
    updated["reviewed_at"] = base.iso_date()
    return updated, added


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--discovered-events", type=Path, required=True)
    parser.add_argument("--output-dir", default="prc-justice-primary-verification")
    parser.add_argument("--write-ledger", action="store_true")
    args = parser.parse_args()

    plan = base.load_json(PLAN_PATH)
    policy = base.load_json(POLICY_PATH)
    ledger = base.load_json(LEDGER_PATH)
    registry = build_source_registry(plan)
    allowed = allowed_hosts(plan, registry)
    discovered = load_jsonl(args.discovered_events)
    max_pages = int(policy["limits"]["max_primary_pages_fetched"])
    minimum_gap = int(policy["limits"]["minimum_seconds_between_prc_primary_fetches"])
    now = base.utc_now()
    cutoff = (now - timedelta(days=int(policy["cadence"]["maximum_age_days_for_search"]))).date().isoformat()
    today = now.date().isoformat()

    verified: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    last_attempt_at: float | None = None
    for event in discovered[:max_pages]:
        if last_attempt_at is not None:
            elapsed = time.monotonic() - last_attempt_at
            if elapsed < minimum_gap:
                time.sleep(minimum_gap - elapsed)
        last_attempt_at = time.monotonic()
        item, receipt = verify_event(event, allowed=allowed, policy=policy, cutoff_date=cutoff, now_date=today)
        receipts.append(receipt)
        if item is not None:
            verified.append(item)

    safe_verified = [row for row in verified if row.get("review_status") == "PRIMARY_VERIFIED"]
    contested = [row for row in verified if row.get("review_status") == "CONTESTED"]
    updated_ledger, added_ids = append_new_events(ledger, safe_verified)
    if args.write_ledger and added_ids:
        base.save_json(LEDGER_PATH, updated_ledger)

    output_dir = Path(args.output_dir)
    base.save_jsonl(output_dir / "verified-signal-events.jsonl", verified)
    base.save_jsonl(output_dir / "primary-verified-signal-events.jsonl", safe_verified)
    base.save_jsonl(output_dir / "contested-signal-events.jsonl", contested)
    base.save_jsonl(output_dir / "verification-receipts.jsonl", receipts)
    report = {
        "status": "PASS",
        "run_at": now.replace(microsecond=0).isoformat(),
        "freshness_cutoff_date": cutoff,
        "discovered_input_count": len(discovered),
        "primary_pages_attempted": len(receipts),
        "primary_verified_or_contested_count": len(verified),
        "primary_verified_count": len(safe_verified),
        "contested_count": len(contested),
        "new_ledger_event_count": len(added_ids),
        "new_ledger_event_ids": added_ids,
        "review_only_count": sum(1 for row in receipts if row.get("status") == "REVIEW_ONLY"),
        "contested_written_to_automatic_ledger": False,
        "ledger_changed": bool(added_ids),
        "allowed_host_count": len(allowed),
        "full_page_text_stored": False,
        "automatic_login": False,
        "redirect_following": False,
        "automatic_retry": False,
        "captcha_or_waf_bypass": False,
        "secret_operational_details": False,
        "personal_targeting": False,
        "model_calls": 0,
        "compute_calls": 0,
    }
    base.save_json(output_dir / "verification-report.json", report)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
