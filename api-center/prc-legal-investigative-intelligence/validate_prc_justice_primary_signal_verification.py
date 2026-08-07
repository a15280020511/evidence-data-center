#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Mapping

import verify_prc_justice_trend_signals as verifier

HERE = Path(__file__).resolve().parent


def load(name: str) -> dict[str, Any]:
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    policy = load("prc-justice-primary-verification-policy.json")
    self_iteration = load("prc-justice-self-iteration-policy.json")
    ledger = load("prc-justice-verified-signal-ledger.json")
    storage = load("prc-justice-trend-storage-contract.json")
    tech = load("investigative-technology-intelligence-matrix.json")
    plan = load("prc-justice-trend-source-plan.json")

    gate = policy["verification_gate"]
    controls = policy["network_controls"]
    base_limits = self_iteration["limits"]
    base_cadence = self_iteration["cadence"]
    require(gate["maximum_age_days"] == base_cadence["maximum_age_days_for_search"], "freshness window drift")
    require(controls["maximum_primary_pages_per_run"] == base_limits["max_primary_pages_fetched"], "primary page limit drift")
    require(controls["minimum_seconds_between_primary_fetches"] == base_limits["minimum_seconds_between_prc_primary_fetches"], "request interval drift")
    require(controls["request_timeout_seconds"] == base_limits["request_timeout_seconds"], "timeout drift")
    require(controls["maximum_page_bytes"] == base_limits["max_page_bytes"], "page-byte limit drift")
    for key in [
        "automatic_retry",
        "follow_redirects",
        "automatic_login",
        "captcha_solving",
        "waf_bypass",
        "proxy_rotation",
        "identity_rotation",
        "hidden_api_reverse_engineering",
        "pdf_auto_ingestion",
    ]:
        require(controls[key] is False, f"unsafe network control enabled: {key}")

    safety = policy["safety_boundary"]
    require(safety["public_or_authorized_sources_only"] is True, "public/authorized source gate required")
    for key, value in safety.items():
        if key != "public_or_authorized_sources_only":
            require(value is False, f"unsafe safety capability enabled: {key}")

    write = policy["automatic_ledger_write"]
    require(write["enabled"] is True and write["append_only"] is True, "append-only ledger write required")
    require(write["only_paths_allowed"] == ["api-center/prc-legal-investigative-intelligence/prc-justice-verified-signal-ledger.json"], "automatic write scope widened")
    require(write["existing_events_must_not_be_mutated_or_deleted"] is True, "existing events must be immutable")
    require(write["branch_protection_bypass"] is False, "branch protection bypass forbidden")

    registry = verifier.build_source_registry(plan)
    allowed = verifier.allowed_hosts(plan, registry)
    for required_host in ["ccgp.gov.cn", "spp.gov.cn", "court.gov.cn", "mps.gov.cn"]:
        require(required_host in allowed, f"required verified-source host missing: {required_host}")
    require("edu.cn" not in allowed, "generic edu.cn must not be auto-ingestion allowlist")

    ledger_safety = ledger["safety_boundary"]
    require(ledger_safety["public_or_authorized_sources_only"] is True, "ledger source gate missing")
    require(ledger_safety["full_page_text_stored"] is False, "ledger must not store full page text")
    for key in ["personal_targeting", "secret_operational_details", "targeting_or_evasion_details", "anti_forensics"]:
        require(ledger_safety[key] is False, f"unsafe ledger field enabled: {key}")

    capability_ids = {str(row["capability_id"]) for row in tech.get("technology_domains") or [] if isinstance(row, Mapping) and row.get("capability_id")}
    event_ids: set[str] = set()
    fingerprints: set[str] = set()
    for event in ledger.get("events") or []:
        require(isinstance(event, Mapping), "ledger event must be object")
        event_id = str(event.get("event_id") or "")
        require(event_id and event_id not in event_ids, "duplicate or empty event_id")
        event_ids.add(event_id)
        require(event.get("review_status") in {"PRIMARY_VERIFIED", "CONTESTED"}, "ledger event not primary verified/contested")
        source = event.get("source") or {}
        require(source.get("primary") is True, "ledger event source must be primary")
        require(source.get("source_class") in {"official_primary", "academic_primary", "authorized_database"}, "invalid primary source class")
        fingerprint = str(source.get("content_fingerprint") or "")
        require(len(fingerprint) == 64 and fingerprint not in fingerprints, "invalid or duplicate source fingerprint")
        fingerprints.add(fingerprint)
        safety_event = event.get("safety") or {}
        require(safety_event.get("public_or_authorized") is True, "event public/authorized flag required")
        require(safety_event.get("contains_secret_operational_detail") is False, "secret detail in event")
        require(safety_event.get("contains_targeting_or_evasion_detail") is False, "targeting/evasion detail in event")
        require(safety_event.get("contains_personal_targeting") is False, "personal targeting in event")
        for capability_id in event.get("capability_ids") or []:
            require(str(capability_id) in capability_ids, f"unknown capability id in verified ledger: {capability_id}")

    fixture = {
        "event_id": "verified-test-20260807-abcdef",
        "review_status": "PRIMARY_VERIFIED",
        "source": {"content_fingerprint": "a" * 64},
    }
    original = copy.deepcopy(ledger)
    once, added_once = verifier.append_new_events(copy.deepcopy(ledger), [fixture])
    twice, added_twice = verifier.append_new_events(copy.deepcopy(once), [fixture])
    require(ledger == original, "append helper mutated source ledger")
    require(added_once == [fixture["event_id"]], "first append must add fixture")
    require(added_twice == [], "second append must deduplicate fixture")
    require(len(twice.get("events") or []) == len(once.get("events") or []), "dedup changed event count")

    storage_tiers = {row.get("tier_id"): row for row in storage.get("tiers") or [] if isinstance(row, Mapping)}
    require("signal_event_store" in storage_tiers, "signal event storage tier missing")
    require(storage_tiers["signal_event_store"].get("append_only") is True, "signal event store must be append-only")
    boundary = storage["data_boundary"]
    require(boundary["raw_source_text_in_compute_pack"] is False, "raw source text cannot enter compute pack")
    require(boundary["raw_source_text_in_model_packet"] is False, "raw source text cannot enter model packet")

    output = {
        "status": "PASS",
        "verified_ledger_event_count": len(event_ids),
        "resolved_source_family_count": len(registry),
        "automatic_primary_host_count": len(allowed),
        "freshness_window_days": gate["maximum_age_days"],
        "max_primary_pages_per_run": controls["maximum_primary_pages_per_run"],
        "minimum_seconds_between_fetches": controls["minimum_seconds_between_primary_fetches"],
        "append_only_ledger": True,
        "dedup_regression": True,
        "single_automatic_write_path": True,
        "full_page_text_stored": False,
        "redirect_following": False,
        "automatic_retry": False,
        "captcha_or_waf_bypass": False,
        "secret_operational_details": False,
        "investigation_evasion": False,
    }
    print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
