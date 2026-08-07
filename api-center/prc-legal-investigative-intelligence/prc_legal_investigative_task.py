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


def joint_audit_plan(catalog: Mapping[str, Any], parameters: Mapping[str, Any]) -> Mapping[str, Any]:
    topics_raw = parameters.get("risk_topics") or []
    if not isinstance(topics_raw, list):
        raise ValueError("risk_topics must be an array")
    topics = {normalized(item) for item in topics_raw if normalized(item)}
    candidates = stage_sources(catalog, topics)
    candidate_ids = {str(row.get("source_id")) for row in candidates}

    stage_map = [
        ("yuandian_recall", ["yuandian-law"]),
        ("official_law_validation", ["npc-national-law-database", "spc-official", "moj-national-regulations"]),
        ("judicial_and_procuratorial_cases", ["spc-case-library", "spc-official", "spp-guiding-cases"]),
        ("public_security_electronic_evidence_rules", ["public-security-electronic-evidence-rules"]),
        ("sector_regulator_rules_and_enforcement", ["cac-data-governance", "samr-enforcement", "miit-data-security", "national-data-administration", "cnipa-copyright-data-rights"]),
        ("technical_standards", ["tc260", "cncert"]),
        ("special_redline_domains", ["state-secrets-bureau", "mnr-geospatial"]),
    ]
    stages = []
    for stage_name, source_ids in stage_map:
        if topics:
            routed = [source_id for source_id in source_ids if source_id in candidate_ids or source_id in {"yuandian-law", "npc-national-law-database", "public-security-electronic-evidence-rules"}]
        else:
            routed = list(source_ids)
        stages.append({"stage": stage_name, "source_ids": routed})

    return {
        "jurisdiction": "PRC_MAINLAND",
        "risk_topics": sorted(topics),
        "purpose": "defensive_compliance_and_evidence_review_only",
        "decision_rule": "YuanDian is a recall layer; current official law/regulator/judicial sources control final verification.",
        "investigation_evasion_allowed": False,
        "identity_concealment_allowed": False,
        "stages": stages,
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
        "upstream_called": False,
        "network_used": False,
        "request_count": 0,
        "automatic_retry": False,
        "automatic_pagination": False,
        "automatic_login": False,
        "captcha_solving": False,
        "waf_bypass": False,
        "investigation_evasion": False,
        "secret_values_exposed": False,
        "model_calls": 0,
    }
    try:
        catalog = load_json(SOURCE_CATALOG_PATH)
        if operation == "catalog-capabilities":
            if parameters:
                raise ValueError("catalog-capabilities accepts no parameters")
            snapshot = {"provider": provider_row(CATALOG_PATH), "source_catalog_summary": {"schema_version": catalog.get("schema_version"), "reviewed_at": catalog.get("reviewed_at"), "source_count": len(catalog.get("sources") or [])}}
        elif operation == "source-catalog":
            snapshot = {"source_catalog": filter_sources(catalog, parameters)}
        elif operation == "source-route":
            snapshot = {"source_route": source_route(catalog, str(parameters.get("source_id") or ""))}
        elif operation == "joint-audit-plan":
            snapshot = {"joint_audit_plan": joint_audit_plan(catalog, parameters)}
        else:
            raise ValueError(f"unsupported operation: {operation}")
        status = "INTEL_PRC_LEGAL_INVESTIGATIVE_COMPLETED"
    except Exception as exc:
        failure = {"type": type(exc).__name__, "message": str(exc)[:2000]}
    return finish_execution(
        ticket=ticket,
        output_dir=output_dir,
        status=status,
        snapshot=snapshot,
        metadata=metadata,
        failure=failure,
        started_at=started_at,
        started_perf=started_perf,
        schema_prefix="prc-legal-investigative-intelligence",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-prc-legal]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="prc-legal-investigative-ticket-status-v1",
            display_name="PRC Legal Investigative Intelligence",
        )
    )
