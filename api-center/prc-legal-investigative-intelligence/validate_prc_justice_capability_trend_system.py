#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name: str):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    system = load("prc-justice-capability-trend-system.json")
    event_schema = load("prc-justice-signal-event.schema.json")
    contract = load("prc-justice-trend-analysis-contract.json")
    tech = load("investigative-technology-intelligence-matrix.json")
    ledger = load("case-derived-investigative-capability-ledger.json")
    self_iteration = load("prc-justice-self-iteration-policy.json")

    require(system.get("jurisdiction") == "PRC_MAINLAND", "jurisdiction must be PRC_MAINLAND")
    safety = system.get("safety_boundary") or {}
    require(safety.get("public_or_authorized_sources_only") is True, "public/authorized source gate required")
    for key in [
        "secret_internal_systems",
        "covert_surveillance_implementation_details",
        "target_selection_or_tracking_playbook",
        "investigation_evasion",
        "anti_forensics",
        "evidence_destruction",
        "credential_or_hidden_endpoint_collection",
        "operational_tactical_playbook",
        "personal_targeting",
    ]:
        require(safety.get(key) is False, f"unsafe system capability enabled: {key}")

    axes = {row.get("axis_id") for row in system.get("four_axes") or []}
    require(axes == {"capability", "practice", "technology_trend", "doctrine_and_enforcement"}, "four-axis contract incomplete")

    expected_signals = {
        "law_and_norm",
        "policy_and_strategy",
        "education_and_training",
        "research",
        "standard",
        "procurement_and_budget",
        "talent_and_recruitment",
        "infrastructure_and_deployment",
        "case_practice",
        "judicial_outcome",
        "statistics_and_report",
        "doctrine_and_commentary",
    }
    signal_types = {row.get("signal_type") for row in system.get("signal_layers") or []}
    require(signal_types == expected_signals, "12 signal layers incomplete")

    lifecycle = system.get("capability_lifecycle") or []
    for stage in [
        "RESEARCH_SIGNAL",
        "TRAINING_SIGNAL",
        "STANDARDIZED",
        "INVESTING",
        "DEPLOYING",
        "FIRST_PRACTICE",
        "REPEATED_PRACTICE",
        "CROSS_REGION_OBSERVED",
        "CROSS_INSTITUTION_OBSERVED",
        "MATURE_PUBLIC_PRACTICE",
        "CONTESTED",
        "STALE_REVIEW_REQUIRED",
    ]:
        require(stage in lifecycle, f"missing lifecycle stage: {stage}")

    indices = {row.get("index_id") for row in system.get("indices") or []}
    require(indices == {"CES", "PSS", "TMS", "DI", "DSI", "ESI"}, "six-index contract incomplete")
    graphs = {row.get("graph_id") for row in system.get("graphs") or []}
    require(graphs == {"capability_map", "practice_standard_graph", "technology_lifecycle_graph", "doctrine_graph", "enforcement_graph"}, "five graph contract incomplete")

    analysis_layers = system.get("analysis_layers") or {}
    require(set(analysis_layers) == {"deterministic_layer", "model_layer", "compute_layer", "governance_layer"}, "analysis layers incomplete")
    model_layer = analysis_layers["model_layer"]
    require(model_layer.get("may_assert_unverified_fact") is False, "model must not assert unverified facts")
    require(model_layer.get("must_reference_evidence_ids") is True, "model findings require evidence ids")
    require(model_layer.get("must_not_infer_secret_capability_from_absence") is True, "secret capability inference gate required")
    compute_layer = analysis_layers["compute_layer"]
    require(compute_layer.get("network_required") is False, "compute layer must remain offline")

    handoff = system.get("handoff_contract") or {}
    require("governance_to_expert" in handoff and "governance_to_compute" in handoff, "governance routing missing")
    require("intelligence_to_expert" not in handoff and "intelligence_to_compute" not in handoff, "direct center-to-center handoff forbidden")

    required_card = set(system.get("mandatory_trend_evidence_card") or [])
    for field in ["primary_source_count", "independent_institution_count", "region_count", "CES", "PSS", "TMS", "DI", "supporting_evidence_ids", "conflicting_evidence_ids", "limitations"]:
        require(field in required_card, f"trend evidence card missing: {field}")

    props = event_schema.get("properties") or {}
    require(set(props["signal_type"]["enum"]) == expected_signals, "signal event enum drift")
    safety_props = props["safety"]["properties"]
    require(safety_props["public_or_authorized"].get("const") is True, "event source must be public/authorized")
    require(safety_props["contains_secret_operational_detail"].get("const") is False, "secret operational detail must be false")
    require(safety_props["contains_targeting_or_evasion_detail"].get("const") is False, "targeting/evasion detail must be false")
    require(safety_props["contains_personal_targeting"].get("const") is False, "personal targeting must be false")

    architecture = contract.get("architecture") or {}
    require("唯一跨中心路由" in architecture.get("governance_center", ""), "governance must remain sole router")
    forbidden = set(contract.get("model_analysis_packet", {}).get("forbidden_inferences") or [])
    for value in [
        "secret_internal_capability_inference",
        "covert_surveillance_implementation_inference",
        "target_selection_or_tracking_inference",
        "surveillance_blind_spot_inference",
        "investigation_evasion_advice",
        "anti_forensics_advice",
        "claiming_nationwide_deployment_from_single_case",
        "claiming_fact_without_evidence_id",
    ]:
        require(value in forbidden, f"missing model inference guard: {value}")

    never_allowed = set(contract.get("trend_claim_gate", {}).get("never_allowed") or [])
    for value in [
        "single_news_item_equals_capability",
        "course_title_equals_operational_deployment",
        "procurement_intent_equals_deployed_capability",
        "absence_of_case_equals_absence_of_capability",
        "secret_capability_extrapolation",
    ]:
        require(value in never_allowed, f"missing trend claim guard: {value}")

    numeric = contract.get("justice_trend_numeric_pack") or {}
    require((numeric.get("deterministic_constraints") or {}).get("no_network") is True, "numeric pack compute must be offline")
    require((numeric.get("deterministic_constraints") or {}).get("no_personal_data") is True, "numeric pack must exclude personal data")
    required_computations = set(numeric.get("required_computations") or [])
    for index_id in indices:
        require(index_id in required_computations, f"numeric pack missing computation: {index_id}")

    capability_ids = {row.get("capability_id") for row in tech.get("technology_domains") or []}
    require(len(capability_ids) >= 19, "expected at least 19 investigative technology capability domains")
    require(None not in capability_ids, "capability_id cannot be null")
    for observation in ledger.get("observations") or []:
        for capability_id in observation.get("capability_ids") or []:
            require(capability_id in capability_ids, f"ledger references unknown capability: {capability_id}")

    cadence = self_iteration.get("cadence") or {}
    require(bool(cadence.get("workflow_cron_utc")), "scheduled self-iteration cadence required")
    require(int(cadence.get("maximum_age_days_for_search") or 0) > 0, "freshness window required")

    output = {
        "status": "PASS",
        "system": system.get("system_name"),
        "axes": len(axes),
        "signal_layers": len(signal_types),
        "capability_domains": len(capability_ids),
        "graphs": len(graphs),
        "indices": sorted(indices),
        "scheduled_self_iteration": True,
        "model_evidence_citation_required": True,
        "compute_offline": True,
        "governance_only_cross_center_routing": True,
        "secret_operational_details": False,
        "investigation_evasion": False,
    }
    print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
