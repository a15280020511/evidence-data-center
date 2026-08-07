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


def dump(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(value), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_packets(output_dir: Path, as_of: str) -> dict[str, Any]:
    system = load("prc-justice-capability-trend-system.json")
    contract = load("prc-justice-trend-analysis-contract.json")
    ledger = load("case-derived-investigative-capability-ledger.json")
    tech = load("investigative-technology-intelligence-matrix.json")

    observations = [dict(row) for row in ledger.get("observations") or [] if isinstance(row, Mapping)]
    capability_meta = {
        str(row.get("capability_id")): dict(row)
        for row in tech.get("technology_domains") or []
        if isinstance(row, Mapping) and row.get("capability_id")
    }

    evidence_cards = []
    by_cap: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in observations:
        evidence_id = str(row.get("observation_id") or "")
        caps = [str(x) for x in row.get("capability_ids") or []]
        evidence_cards.append({
            "evidence_id": evidence_id,
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
            by_cap[cap].append(row)

    capability_rows = []
    for cap_id, meta in sorted(capability_meta.items()):
        rows = by_cap.get(cap_id, [])
        dates = sorted(str(r.get("publication_date")) for r in rows if r.get("publication_date"))
        institutions = {str(r.get("jurisdiction_or_institution")) for r in rows if r.get("jurisdiction_or_institution")}
        capability_rows.append({
            "capability_id": cap_id,
            "capability_name": meta.get("name"),
            "first_seen": dates[0] if dates else None,
            "latest_seen": dates[-1] if dates else None,
            "primary_case_count": len(rows),
            "independent_institution_count": len(institutions),
            "institution_type_count": 0,
            "region_count": 0,
            "standard_signal_count": 0,
            "training_signal_count": 0,
            "research_signal_count": 0,
            "procurement_signal_count": 0,
            "deployment_signal_count": 0,
            "judicial_outcome_support_count": 0,
            "conflict_count": sum(len(r.get("conflicts_with_observation_ids") or []) for r in rows),
            "data_limitations": [
                "current_seed_ledger_does_not_yet_machine_normalize_region_or_institution_type",
                "non_case_signal_counts_require_signal_event_store_population"
            ] if rows or True else []
        })

    model_packet = {
        "schema_version": "prc-justice-model-analysis-packet-v1",
        "packet_id": f"prc-justice-model-{as_of}-{stable_hash(evidence_cards)[:12]}",
        "as_of_date": as_of,
        "time_window": {"start": None, "end": as_of},
        "subject_scope": ["capability","technology_trend","practice_standard","doctrine","enforcement"],
        "signal_event_ids": [],
        "evidence_cards": evidence_cards,
        "existing_capability_ids": sorted(capability_meta),
        "allowed_tasks": contract["model_analysis_packet"]["allowed_tasks"],
        "forbidden_inferences": contract["model_analysis_packet"]["forbidden_inferences"],
        "response_contract": contract["model_analysis_packet"]["response_contract"],
        "raw_source_text_included": False,
        "personal_data_included": False
    }

    numeric_pack = {
        "schema_version": "prc-justice-trend-numeric-pack-v1",
        "pack_id": f"prc-justice-numeric-{as_of}-{stable_hash(capability_rows)[:12]}",
        "as_of_date": as_of,
        "time_windows_days": system.get("trend_windows_days") or [],
        "signal_rows": [],
        "capability_rows": capability_rows,
        "outcome_rows": [],
        "required_computations": contract["justice_trend_numeric_pack"]["required_computations"],
        "deterministic_constraints": contract["justice_trend_numeric_pack"]["deterministic_constraints"],
        "input_snapshot_hash": stable_hash({"ledger": ledger, "capabilities": sorted(capability_meta)}),
        "raw_source_text_included": False,
        "personal_data_included": False
    }

    dump(output_dir / "model-analysis-packet.json", model_packet)
    dump(output_dir / "justice-trend-numeric-pack.json", numeric_pack)
    receipt = {
        "status": "PASS",
        "as_of_date": as_of,
        "model_packet_id": model_packet["packet_id"],
        "numeric_pack_id": numeric_pack["pack_id"],
        "evidence_card_count": len(evidence_cards),
        "capability_row_count": len(capability_rows),
        "signal_event_count": 0,
        "raw_source_text_included": False,
        "personal_data_included": False,
        "network_used": False,
        "model_calls": 0,
        "compute_calls": 0,
        "governance_route_required_for_downstream_analysis": True
    }
    dump(output_dir / "build-receipt.json", receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="prc-justice-trend-packets")
    parser.add_argument("--as-of", default=date.today().isoformat())
    args = parser.parse_args()
    receipt = build_packets(Path(args.output_dir), str(args.as_of))
    print(json.dumps(receipt, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
