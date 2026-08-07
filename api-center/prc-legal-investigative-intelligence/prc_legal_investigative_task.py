#!/usr/bin/env python3
"""Local source router for PRC legal, judicial and electronic-evidence intelligence."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Mapping

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from managed_provider_runtime import (  # noqa: E402
    bounded_int,
    finish_execution,
    load_json,
    provider_row,
    run_cli,
    utc_now,
    validate_ticket,
)

SCHEMA_PATH = HERE / "ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"
SOURCE_CATALOG_PATH = HERE / "source-catalog.json"
INVESTIGATIVE_MATRIX_PATH = HERE / "investigative-evidence-matrix.json"
LEGAL_SYSTEM_MATRIX_PATH = HERE / "legal-system-matrix.json"
PRACTICE_MATRIX_PATH = HERE / "public-security-knowledge-practice-matrix.json"


def normalized(value: Any) -> str:
    return str(value or "").strip().lower()


def filter_sources(catalog: Mapping[str, Any], parameters: Mapping[str, Any]) -> Mapping[str, Any]:
    topic = normalized(parameters.get("topic"))
    access_class = normalized(parameters.get("access_class"))
    evidence_weight = normalized(parameters.get("evidence_weight"))
    limit = bounded_int(parameters.get("limit"), default=50, minimum=1, maximum=100, name="limit")
    selected: list[dict[str, Any]] = []
    for source in catalog.get("sources") or []:
        if not isinstance(source, Mapping):
            continue
        if topic and topic not in {normalized(item) for item in source.get("topics") or []}:
            continue
        if access_class and access_class not in normalized(source.get("access_class")):
            continue
        if evidence_weight and evidence_weight != normalized(source.get("evidence_weight")):
            continue
        selected.append(dict(source))
        if len(selected) >= limit:
            break
    return {
        "schema_version": catalog.get("schema_version"),
        "reviewed_at": catalog.get("reviewed_at"),
        "jurisdiction": catalog.get("jurisdiction"),
        "count": len(selected),
        "sources": selected,
    }


def source_route(catalog: Mapping[str, Any], source_id: str) -> Mapping[str, Any]:
    for source in catalog.get("sources") or []:
        if isinstance(source, Mapping) and source.get("source_id") == source_id:
            return {
                "source_id": source_id,
                "name": source.get("name"),
                "evidence_weight": source.get("evidence_weight"),
                "access_class": source.get("access_class"),
                "authentication": source.get("authentication"),
                "role": source.get("role"),
                "retrieval_route": source.get("retrieval_route"),
                "official_confirmation_required": bool(source.get("official_confirmation_required", False)),
                "stop_on_login_or_captcha": bool(source.get("stop_on_login_or_captcha", False)),
            }
    raise ValueError(f"unknown source_id: {source_id}")


def stage_sources(catalog: Mapping[str, Any], topics: set[str]) -> list[Mapping[str, Any]]:
    rows = [row for row in catalog.get("sources") or [] if isinstance(row, Mapping)]
    if not topics:
        return rows
    selected = []
    for row in rows:
        source_topics = {normalized(item) for item in row.get("topics") or []}
        if source_topics & topics:
            selected.append(row)
    return selected


def filter_investigative_matrix(matrix: Mapping[str, Any], parameters: Mapping[str, Any]) -> Mapping[str, Any]:
    topic = normalized(parameters.get("topic"))
    limit = bounded_int(parameters.get("limit"), default=100, minimum=1, maximum=100, name="limit")
    authorities: list[dict[str, Any]] = []
    for row in matrix.get("authority_layers") or []:
        if not isinstance(row, Mapping):
            continue
        topics = {normalized(item) for item in row.get("topics") or []}
        if topic and topic not in topics:
            continue
        authorities.append(dict(row))
        if len(authorities) >= limit:
            break
    categories: list[dict[str, Any]] = []
    for row in matrix.get("evidence_and_investigative_categories") or []:
        if not isinstance(row, Mapping):
            continue
        searchable = {
            normalized(row.get("category_id")),
            normalized(row.get("name")),
            normalized(row.get("legal_view")),
            normalized(row.get("defensive_use")),
        }
        searchable.update(normalized(item) for item in row.get("evidence_examples") or [])
        if topic and not any(topic in value for value in searchable if value):
            continue
        categories.append(dict(row))
        if len(categories) >= limit:
            break
    return {
        "schema_version": matrix.get("schema_version"),
        "reviewed_at": matrix.get("reviewed_at"),
        "jurisdiction": matrix.get("jurisdiction"),
        "purpose": matrix.get("purpose"),
        "safety_boundary": matrix.get("safety_boundary"),
        "authority_count": len(authorities),
        "category_count": len(categories),
        "authority_layers": authorities,
        "evidence_and_investigative_categories": categories,
        "joint_review_logic": matrix.get("joint_review_logic"),
        "final_rule": matrix.get("final_rule"),
    }


def _legal_lane_text(row: Mapping[str, Any]) -> str:
    return " ".join([
        normalized(row.get("lane_id")),
        normalized(row.get("name")),
        normalized(row.get("role")),
        " ".join(normalized(item) for item in row.get("source_ids") or []),
        " ".join(normalized(item) for item in row.get("law_families") or []),
    ])


def filter_legal_system_matrix(matrix: Mapping[str, Any], parameters: Mapping[str, Any]) -> Mapping[str, Any]:
    topic = normalized(parameters.get("topic"))
    system_lane = normalized(parameters.get("system_lane"))
    limit = bounded_int(parameters.get("limit"), default=100, minimum=1, maximum=100, name="limit")
    lanes: list[dict[str, Any]] = []
    selected_source_ids: set[str] = set()
    for row in matrix.get("system_lanes") or []:
        if not isinstance(row, Mapping):
            continue
        if system_lane and normalized(row.get("lane_id")) != system_lane:
            continue
        if topic and topic not in _legal_lane_text(row):
            continue
        lanes.append(dict(row))
        selected_source_ids.update(str(item) for item in row.get("source_ids") or [])
        if len(lanes) >= limit:
            break
    if not system_lane and not topic:
        selected_source_ids = {
            str(row.get("source_id")) for row in matrix.get("sources") or []
            if isinstance(row, Mapping) and row.get("source_id")
        }
    sources: list[dict[str, Any]] = []
    for row in matrix.get("sources") or []:
        if not isinstance(row, Mapping):
            continue
        source_id = str(row.get("source_id") or "")
        if selected_source_ids and source_id not in selected_source_ids:
            continue
        searchable = " ".join([
            normalized(source_id), normalized(row.get("name")), normalized(row.get("role")),
            normalized(row.get("authority_type")), normalized(row.get("access_class")),
            " ".join(normalized(item) for item in row.get("hosts") or []),
        ])
        if topic and not lanes and topic not in searchable:
            continue
        sources.append(dict(row))
        if len(sources) >= limit:
            break
    return {
        "schema_version": matrix.get("schema_version"),
        "reviewed_at": matrix.get("reviewed_at"),
        "jurisdiction": matrix.get("jurisdiction"),
        "purpose": matrix.get("purpose"),
        "safety_boundary": matrix.get("safety_boundary"),
        "pairing_model": matrix.get("pairing_model"),
        "lane_count": len(lanes),
        "source_count": len(sources),
        "system_lanes": lanes,
        "sources": sources,
        "decision_pipeline": matrix.get("decision_pipeline"),
        "final_rule": matrix.get("final_rule"),
    }


def filter_practice_matrix(matrix: Mapping[str, Any], parameters: Mapping[str, Any]) -> Mapping[str, Any]:
    topic = normalized(parameters.get("topic"))
    view = normalized(parameters.get("view"))
    limit = bounded_int(parameters.get("limit"), default=100, minimum=1, maximum=100, name="limit")
    sources: list[dict[str, Any]] = []
    for row in matrix.get("source_families") or []:
        if not isinstance(row, Mapping):
            continue
        if view and view not in normalized(row.get("view")):
            continue
        text = " ".join([
            normalized(row.get("source_id")), normalized(row.get("name")), normalized(row.get("authority_type")),
            normalized(row.get("view")), " ".join(normalized(item) for item in row.get("use") or []),
        ])
        if topic and topic not in text:
            continue
        sources.append(dict(row))
        if len(sources) >= limit:
            break
    domains: list[dict[str, Any]] = []
    for row in matrix.get("capability_domains") or []:
        if not isinstance(row, Mapping):
            continue
        text = " ".join([normalized(row.get("domain_id")), normalized(row.get("name")), normalized(row.get("safe_scope"))])
        if topic and topic not in text:
            continue
        domains.append(dict(row))
        if len(domains) >= limit:
            break
    return {
        "schema_version": matrix.get("schema_version"),
        "reviewed_at": matrix.get("reviewed_at"),
        "jurisdiction": matrix.get("jurisdiction"),
        "purpose": matrix.get("purpose"),
        "safety_boundary": matrix.get("safety_boundary"),
        "two_view_model": matrix.get("two_view_model"),
        "source_count": len(sources),
        "capability_domain_count": len(domains),
        "source_families": sources,
        "capability_domains": domains,
        "case_derived_extraction_fields": matrix.get("case_derived_extraction_fields"),
        "forbidden_extraction_fields": matrix.get("forbidden_extraction_fields"),
        "decision_logic": matrix.get("decision_logic"),
    }


def joint_audit_plan(catalog: Mapping[str, Any], matrix: Mapping[str, Any], legal_matrix: Mapping[str, Any], practice_matrix: Mapping[str, Any], parameters: Mapping[str, Any]) -> Mapping[str, Any]:
    topics_raw = parameters.get("risk_topics") or []
    if not isinstance(topics_raw, list):
        raise ValueError("risk_topics must be an array")
    topics = {normalized(item) for item in topics_raw if normalized(item)}
    candidates = stage_sources(catalog, topics)
    candidate_ids = {str(row.get("source_id")) for row in candidates}
    stage_map = [
        ("yuandian_recall", ["yuandian-law"]),
        ("legal_system_lane_selection", ["npc-national-law-database", "spc-official", "spp-guiding-cases", "public-security-electronic-evidence-rules", "moj-national-regulations"]),
        ("public_security_source_view", ["mps-public-rules-news", "mps-public-security-standards", "ppsuc-public-education-research", "cipuc-public-education-research", "cppu-public-education-research"]),
        ("case_derived_outcome_view", ["yuandian-spc-spp-case-outcome-family", "spp-procuratorial-technology", "local-public-security-official-family"]),
        ("current_official_law_validation", ["npc-national-law-database", "moj-national-regulations"]),
        ("criminal_and_administrative_procedure", ["spc-official", "spp-guiding-cases", "public-security-electronic-evidence-rules"]),
        ("judicial_and_procuratorial_cases", ["spc-case-library", "spc-official", "spp-guiding-cases"]),
        ("public_security_electronic_evidence_rules", ["public-security-electronic-evidence-rules"]),
        ("sector_regulator_rules_and_enforcement", ["cac-data-governance", "samr-enforcement", "miit-data-security", "national-data-administration", "cnipa-copyright-data-rights"]),
        ("technical_standards", ["tc260", "cncert"]),
        ("special_redline_domains", ["state-secrets-bureau", "mnr-geospatial"]),
    ]
    stages = []
    always_include = {"yuandian-law", "npc-national-law-database", "public-security-electronic-evidence-rules"}
    practice_ids = {str(row.get("source_id")) for row in practice_matrix.get("source_families") or [] if isinstance(row, Mapping)}
    for stage_name, source_ids in stage_map:
        if topics and stage_name not in {"public_security_source_view", "case_derived_outcome_view"}:
            routed = [source_id for source_id in source_ids if source_id in candidate_ids or source_id in always_include]
        else:
            routed = [source_id for source_id in source_ids if source_id in practice_ids or source_id not in {"mps-public-rules-news", "mps-public-security-standards", "ppsuc-public-education-research", "cipuc-public-education-research", "cppu-public-education-research", "yuandian-spc-spp-case-outcome-family", "spp-procuratorial-technology", "local-public-security-official-family"}]
        stages.append({"stage": stage_name, "source_ids": routed})
    matrix_view = filter_investigative_matrix(matrix, {"limit": 100})
    matched_authorities = []
    for row in matrix_view["authority_layers"]:
        row_topics = {normalized(item) for item in row.get("topics") or []}
        if not topics or row_topics & topics:
            matched_authorities.append(row.get("authority_id"))
    matched_categories = []
    for row in matrix_view["evidence_and_investigative_categories"]:
        text = " ".join([
            normalized(row.get("category_id")), normalized(row.get("name")), normalized(row.get("legal_view")),
            normalized(row.get("defensive_use")), " ".join(normalized(item) for item in row.get("evidence_examples") or []),
        ])
        if not topics or any(topic in text for topic in topics):
            matched_categories.append(row.get("category_id"))
    matched_legal_lanes = []
    for row in legal_matrix.get("system_lanes") or []:
        if not isinstance(row, Mapping):
            continue
        text = _legal_lane_text(row)
        if not topics or any(topic in text for topic in topics):
            matched_legal_lanes.append(row.get("lane_id"))
    if topics and not matched_legal_lanes:
        matched_legal_lanes = ["national_legislation", "court_system", "procuratorate_system", "public_security_and_investigation"]
    matched_practice_domains = []
    for row in practice_matrix.get("capability_domains") or []:
        if not isinstance(row, Mapping):
            continue
        text = " ".join([normalized(row.get("domain_id")), normalized(row.get("name")), normalized(row.get("safe_scope"))])
        if not topics or any(topic in text for topic in topics):
            matched_practice_domains.append(row.get("domain_id"))
    return {
        "jurisdiction": "PRC_MAINLAND",
        "risk_topics": sorted(topics),
        "purpose": "defensive_compliance_and_evidence_review_only",
        "decision_rule": "YuanDian provides broad recall; public police education/standards/research describe declared capability domains; public cases provide demonstrated outcome evidence; current official law and primary judicial/procuratorial/public-security sources control final verification.",
        "investigation_evasion_allowed": False,
        "identity_concealment_allowed": False,
        "technical_surveillance_implementation_details_allowed": False,
        "stages": stages,
        "matched_legal_system_lane_ids": matched_legal_lanes,
        "matched_authority_ids": matched_authorities,
        "matched_investigative_category_ids": matched_categories,
        "matched_public_security_capability_domain_ids": matched_practice_domains,
        "final_output": ["GREEN", "YELLOW", "ORANGE", "RED", "REVIEW_BEFORE_PRODUCTION"],
    }


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_PRC_LEGAL_INVESTIGATIVE_FAILED"
    failure: Mapping[str, Any] | None = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False, "network_used": False, "request_count": 0, "automatic_retry": False,
        "automatic_pagination": False, "automatic_login": False, "captcha_solving": False, "waf_bypass": False,
        "investigation_evasion": False, "technical_surveillance_details": False, "secret_values_exposed": False,
        "model_calls": 0,
    }
    try:
        catalog = load_json(SOURCE_CATALOG_PATH)
        matrix = load_json(INVESTIGATIVE_MATRIX_PATH)
        legal_matrix = load_json(LEGAL_SYSTEM_MATRIX_PATH)
        practice_matrix = load_json(PRACTICE_MATRIX_PATH)
        if operation == "catalog-capabilities":
            if parameters:
                raise ValueError("catalog-capabilities accepts no parameters")
            snapshot = {
                "provider": provider_row(CATALOG_PATH),
                "source_catalog_summary": {"schema_version": catalog.get("schema_version"), "reviewed_at": catalog.get("reviewed_at"), "source_count": len(catalog.get("sources") or [])},
                "investigative_matrix_summary": {"schema_version": matrix.get("schema_version"), "reviewed_at": matrix.get("reviewed_at"), "authority_count": len(matrix.get("authority_layers") or []), "category_count": len(matrix.get("evidence_and_investigative_categories") or [])},
                "legal_system_matrix_summary": {"schema_version": legal_matrix.get("schema_version"), "reviewed_at": legal_matrix.get("reviewed_at"), "lane_count": len(legal_matrix.get("system_lanes") or []), "source_count": len(legal_matrix.get("sources") or [])},
                "public_security_practice_matrix_summary": {"schema_version": practice_matrix.get("schema_version"), "reviewed_at": practice_matrix.get("reviewed_at"), "source_count": len(practice_matrix.get("source_families") or []), "capability_domain_count": len(practice_matrix.get("capability_domains") or [])},
            }
        elif operation == "source-catalog":
            snapshot = {"source_catalog": filter_sources(catalog, parameters)}
        elif operation == "source-route":
            snapshot = {"source_route": source_route(catalog, str(parameters.get("source_id") or ""))}
        elif operation == "investigative-evidence-matrix":
            snapshot = {"investigative_evidence_matrix": filter_investigative_matrix(matrix, parameters)}
        elif operation == "legal-system-matrix":
            snapshot = {"legal_system_matrix": filter_legal_system_matrix(legal_matrix, parameters)}
        elif operation == "public-security-practice-matrix":
            snapshot = {"public_security_practice_matrix": filter_practice_matrix(practice_matrix, parameters)}
        elif operation == "joint-audit-plan":
            snapshot = {"joint_audit_plan": joint_audit_plan(catalog, matrix, legal_matrix, practice_matrix, parameters)}
        else:
            raise ValueError(f"unsupported operation: {operation}")
        status = "INTEL_PRC_LEGAL_INVESTIGATIVE_COMPLETED"
    except Exception as exc:
        failure = {"type": type(exc).__name__, "message": str(exc)[:2000]}
    return finish_execution(
        ticket=ticket, output_dir=output_dir, status=status, snapshot=snapshot, metadata=metadata, failure=failure,
        started_at=started_at, started_perf=started_perf, schema_prefix="prc-legal-investigative-intelligence",
    )


if __name__ == "__main__":
    raise SystemExit(run_cli(
        execute=execute,
        ticket_prefix="[intel-prc-legal]",
        schema_path=SCHEMA_PATH,
        catalog_path=CATALOG_PATH,
        status_schema="prc-legal-investigative-ticket-status-v1",
        display_name="PRC Legal Investigative Intelligence",
    ))
