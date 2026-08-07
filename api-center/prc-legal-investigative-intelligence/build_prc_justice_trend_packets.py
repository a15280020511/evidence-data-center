#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Mapping

HERE = Path(__file__).resolve().parent


def load(name: str) -> dict[str, Any]:
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def load_jsonl(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if isinstance(value, Mapping):
                rows.append(dict(value))
    return rows


def dump(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(value), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def safe_list(value: Any) -> list[str]:
    return [str(x) for x in (value or []) if str(x)]


def build_packets(
    output_dir: Path,
    as_of: str,
    discovered_events_path: Path | None = None,
    verified_events_path: Path | None = None,
) -> dict[str, Any]:
    system = load("prc-justice-capability-trend-system.json")
    contract = load("prc-justice-trend-analysis-contract.json")
    case_ledger = load("case-derived-investigative-capability-ledger.json")
    tech = load("investigative-technology-intelligence-matrix.json")
    discovered_events = load_jsonl(discovered_events_path)
    verified_events = load_jsonl(verified_events_path)

    observations = [dict(row) for row in case_ledger.get("observations") or [] if isinstance(row, Mapping)]
    capability_meta = {
        str(row.get("capability_id")): dict(row)
        for row in tech.get("technology_domains") or []
        if isinstance(row, Mapping) and row.get("capability_id")
    }

    case_evidence_cards = []
    cases_by_cap: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in observations:
        evidence_id = str(row.get("observation_id") or "")
        caps = safe_list(row.get("capability_ids"))
        case_evidence_cards.append({
            "evidence_id": evidence_id,
            "evidence_kind": "PRIMARY_CASE_OBSERVATION",
            "publication_date": row.get("publication_date"),
            "institution": row.get("jurisdiction_or_institution"),
            "case_type": row.get("case_type"),
            "procedural_stage": row.get("procedural_stage"),
            "capability_ids": caps,
            "public_evidence_categories": row.get("public_evidence_chain") or [],
            "verification_status": row.get("verification_status"),
            "primary_source_url": row.get("primary_source_url"),
            "source_fingerprint": row.get("source_fingerprint"),
        })
        for cap in caps:
            cases_by_cap[cap].append(row)

    verified_signal_cards = []
    signals_by_cap: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in verified_events:
        source = event.get("source") or {}
        if not source.get("primary") or event.get("review_status") not in {"PRIMARY_VERIFIED", "CONTESTED"}:
            continue
        caps = safe_list(event.get("capability_ids"))
        card = {
            "evidence_id": event.get("event_id"),
            "evidence_kind": "PRIMARY_VERIFIED_SIGNAL_EVENT",
            "publication_date": event.get("publication_date"),
            "institution_type": event.get("institution_type"),
            "institution": event.get("institution_name"),
            "region": event.get("region"),
            "signal_type": event.get("signal_type"),
            "subject_type": event.get("subject_type"),
            "capability_ids": caps,
            "lifecycle_stage": event.get("lifecycle_stage"),
            "support_or_conflict": event.get("support_or_conflict"),
            "verification_status": event.get("review_status"),
            "primary_source_url": source.get("url"),
            "source_fingerprint": source.get("content_fingerprint"),
        }
        verified_signal_cards.append(card)
        for cap in caps:
            if cap in capability_meta:
                signals_by_cap[cap].append(event)

    capability_rows = []
    for cap_id, meta in sorted(capability_meta.items()):
        case_rows = cases_by_cap.get(cap_id, [])
        signal_rows_for_cap = signals_by_cap.get(cap_id, [])
        dates = sorted(
            {str(r.get("publication_date")) for r in case_rows + signal_rows_for_cap if r.get("publication_date")}
        )
        institution_names = {
            str(r.get("jurisdiction_or_institution")) for r in case_rows if r.get("jurisdiction_or_institution")
        } | {
            str(r.get("institution_name")) for r in signal_rows_for_cap if r.get("institution_name")
        }
        institution_types = {
            str(r.get("institution_type")) for r in signal_rows_for_cap if r.get("institution_type")
        }
        regions = {str(r.get("region")) for r in signal_rows_for_cap if r.get("region")}
        type_counts: dict[str, int] = defaultdict(int)
        for event in signal_rows_for_cap:
            type_counts[str(event.get("signal_type") or "")] += 1
        capability_rows.append({
            "capability_id": cap_id,
            "capability_name": meta.get("name"),
            "first_seen": dates[0] if dates else None,
            "latest_seen": dates[-1] if dates else None,
            "primary_case_count": len(case_rows),
            "independent_institution_count": len(institution_names),
            "institution_type_count": len(institution_types),
            "region_count": len(regions),
            "standard_signal_count": type_counts.get("standard", 0),
            "training_signal_count": type_counts.get("education_and_training", 0),
            "research_signal_count": type_counts.get("research", 0),
            "procurement_signal_count": type_counts.get("procurement_and_budget", 0),
            "deployment_signal_count": type_counts.get("infrastructure_and_deployment", 0),
            "judicial_outcome_support_count": sum(
                1
                for event in signal_rows_for_cap
                if event.get("signal_type") == "judicial_outcome" and event.get("support_or_conflict") == "SUPPORTS"
            ),
            "conflict_count": sum(len(r.get("conflicts_with_observation_ids") or []) for r in case_rows)
            + sum(1 for event in signal_rows_for_cap if event.get("support_or_conflict") == "CONFLICTS"),
            "data_limitations": [
                "region_count_depends_on_machine_normalized_region_fields",
                "scores_must_not_treat_discovery_only_events_as_verified_signals",
            ],
        })

    discovery_summaries = []
    for event in discovered_events:
        source = event.get("source") or {}
        discovery_summaries.append({
            "event_id": event.get("event_id"),
            "event_date": event.get("event_date"),
            "publication_date": event.get("publication_date"),
            "signal_type": event.get("signal_type"),
            "subject_type": event.get("subject_type"),
            "source_url": source.get("url"),
            "source_host": source.get("host"),
            "source_title": source.get("title"),
            "review_status": event.get("review_status"),
            "fact_status": "DISCOVERY_ONLY_NOT_PRIMARY_VERIFIED",
        })

    numeric_signal_rows = []
    for event in verified_events:
        source = event.get("source") or {}
        if not source.get("primary") or event.get("review_status") not in {"PRIMARY_VERIFIED", "CONTESTED"}:
            continue
        caps = safe_list(event.get("capability_ids")) or [None]
        for cap in caps:
            numeric_signal_rows.append({
                "event_id": event.get("event_id"),
                "event_date": event.get("event_date"),
                "institution_type": event.get("institution_type"),
                "region": event.get("region"),
                "signal_type": event.get("signal_type"),
                "capability_id": cap,
                "lifecycle_stage": event.get("lifecycle_stage"),
                "source_primary": True,
                "support_or_conflict": event.get("support_or_conflict"),
                "freshness_weight": 1.0,
                "fact_status": "PRIMARY_VERIFIED_SIGNAL_EVENT",
            })

    all_verified_cards = case_evidence_cards + verified_signal_cards
    model_packet = {
        "schema_version": "prc-justice-model-analysis-packet-v1",
        "packet_id": f"prc-justice-model-{as_of}-{stable_hash({'verified': all_verified_cards, 'discovery': discovery_summaries})[:12]}",
        "as_of_date": as_of,
        "time_window": {"start": None, "end": as_of},
        "subject_scope": ["capability", "technology_trend", "practice_standard", "doctrine", "enforcement"],
        "signal_event_ids": [str(row.get("event_id")) for row in verified_events if row.get("event_id")],
        "evidence_cards": all_verified_cards,
        "verified_signal_evidence_cards": verified_signal_cards,
        "discovery_event_summaries": discovery_summaries,
        "existing_capability_ids": sorted(capability_meta),
        "allowed_tasks": contract["model_analysis_packet"]["allowed_tasks"],
        "forbidden_inferences": contract["model_analysis_packet"]["forbidden_inferences"],
        "response_contract": contract["model_analysis_packet"]["response_contract"],
        "discovery_events_must_not_be_treated_as_verified_facts": True,
        "raw_source_text_included": False,
        "personal_data_included": False,
    }

    numeric_pack = {
        "schema_version": "prc-justice-trend-numeric-pack-v1",
        "pack_id": f"prc-justice-numeric-{as_of}-{stable_hash({'capabilities': capability_rows, 'signals': numeric_signal_rows})[:12]}",
        "as_of_date": as_of,
        "time_windows_days": system.get("trend_windows_days") or [],
        "signal_rows": numeric_signal_rows,
        "capability_rows": capability_rows,
        "outcome_rows": [],
        "required_computations": contract["justice_trend_numeric_pack"]["required_computations"],
        "deterministic_constraints": contract["justice_trend_numeric_pack"]["deterministic_constraints"],
        "input_snapshot_hash": stable_hash({
            "case_ledger": case_ledger,
            "capabilities": sorted(capability_meta),
            "verified_signal_events": verified_events,
        }),
        "discovery_events_excluded_from_capability_scoring_until_primary_verified": True,
        "raw_source_text_included": False,
        "personal_data_included": False,
    }

    dump(output_dir / "model-analysis-packet.json", model_packet)
    dump(output_dir / "justice-trend-numeric-pack.json", numeric_pack)
    receipt = {
        "status": "PASS",
        "as_of_date": as_of,
        "model_packet_id": model_packet["packet_id"],
        "numeric_pack_id": numeric_pack["pack_id"],
        "verified_case_evidence_card_count": len(case_evidence_cards),
        "verified_signal_evidence_card_count": len(verified_signal_cards),
        "capability_row_count": len(capability_rows),
        "discovered_signal_event_count": len(discovered_events),
        "verified_signal_event_count": len(verified_events),
        "numeric_verified_signal_row_count": len(numeric_signal_rows),
        "discovered_signals_are_verified_facts": False,
        "raw_source_text_included": False,
        "personal_data_included": False,
        "network_used": False,
        "model_calls": 0,
        "compute_calls": 0,
        "governance_route_required_for_downstream_analysis": True,
    }
    dump(output_dir / "build-receipt.json", receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="prc-justice-trend-packets")
    parser.add_argument("--as-of", default=date.today().isoformat())
    parser.add_argument("--signal-events", "--discovered-events", dest="discovered_events", type=Path, default=None)
    parser.add_argument("--verified-events", type=Path, default=None)
    args = parser.parse_args()
    receipt = build_packets(
        Path(args.output_dir),
        str(args.as_of),
        args.discovered_events,
        args.verified_events,
    )
    print(json.dumps(receipt, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
