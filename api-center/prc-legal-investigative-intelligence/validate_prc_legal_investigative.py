#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from prc_legal_investigative_task import CATALOG_PATH, execute

SAMPLES = {
    "catalog-capabilities": {},
    "source-catalog": {"topic": "electronic_evidence", "limit": 20},
    "source-route": {"source_id": "public-security-electronic-evidence-rules"},
    "legal-system-matrix": {"system_lane": "court_system", "limit": 100},
    "investigative-evidence-matrix": {"limit": 100},
    "public-security-practice-matrix": {"limit": 100},
    "joint-audit-plan": {"risk_topics": ["electronic_evidence", "personal_information", "geospatial"]},
}


def validate(operation: str) -> dict[str, object]:
    ticket = {
        "task_id": f"prc-legal-{operation}",
        "provider": "prc-legal-investigative-intelligence",
        "operation": operation,
        "objective": "zero-network catalog validation",
        "parameters": SAMPLES[operation],
        "data_policy": {"classification": "public", "contains_personal_data": False},
        "acceptance": {"timeout_seconds": 10, "max_response_bytes": 5000000},
    }
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        ticket_path = root / "ticket.json"
        output_dir = root / "output"
        ticket_path.write_text(json.dumps(ticket, ensure_ascii=False), encoding="utf-8")
        result = execute(ticket_path, output_dir)
        diagnostics = json.loads((output_dir / "diagnostics.json").read_text(encoding="utf-8"))
        if result != 0 or diagnostics["status"] != "INTEL_PRC_LEGAL_INVESTIGATIVE_COMPLETED":
            raise AssertionError(diagnostics)
        metadata = diagnostics["metadata"]
        assert metadata["network_used"] is False
        assert metadata["upstream_called"] is False
        assert metadata["request_count"] == 0
        assert metadata["automatic_login"] is False
        assert metadata["captcha_solving"] is False
        assert metadata["waf_bypass"] is False
        assert metadata["investigation_evasion"] is False
        assert metadata["technical_surveillance_details"] is False
        assert diagnostics["secret_values_exposed"] is False
        assert diagnostics["model_calls"] == 0
        snapshot = json.loads((output_dir / "snapshot.json").read_text(encoding="utf-8"))
        if operation == "legal-system-matrix":
            view = snapshot["legal_system_matrix"]
            assert view["schema_version"] == "prc-legal-system-matrix-v1"
            assert view["lane_count"] == 1
            assert view["source_count"] >= 8
            assert view["system_lanes"][0]["lane_id"] == "court_system"
        if operation == "public-security-practice-matrix":
            view = snapshot["public_security_practice_matrix"]
            assert view["schema_version"] == "prc-justice-knowledge-practice-matrix-v2"
            assert view["source_count"] >= 30
            assert view["capability_domain_count"] >= 20
            assert view["safety_boundary"]["operational_surveillance_details_allowed"] is False
            assert view["safety_boundary"]["private_training_platform_login_allowed"] is False
            source_ids = {row["source_id"] for row in view["source_families"]}
            required_sources = {
                "mps-public-rules-news",
                "national-criminal-technology-standardization",
                "ppsuc-public-education-research",
                "cipuc-public-education-research",
                "spc-national-judge-college",
                "spp-national-prosecutor-college",
                "spp-procuratorial-technology",
                "judicial-appraisal-science-institute",
                "central-judicial-police-officer-college",
                "ccdi-nsc-public-law-practice",
                "china-academy-discipline-inspection-supervision",
                "discipline-inspection-nine-textbooks",
                "yuandian-spc-spp-case-outcome-family",
            }
            assert required_sources <= source_ids
            assert "anti_forensics_or_evasion_method" in view["forbidden_extraction_fields"]
            assert "operational_tactical_playbook" in view["forbidden_extraction_fields"]
        if operation == "joint-audit-plan":
            plan = snapshot["joint_audit_plan"]
            assert plan["matched_legal_system_lane_ids"]
            assert plan["investigation_evasion_allowed"] is False
            assert "public_security_source_view" in {stage["stage"] for stage in plan["stages"]}
            assert "case_derived_outcome_view" in {stage["stage"] for stage in plan["stages"]}
        return {"status": "PASS", "operation": operation, "provider_catalog": CATALOG_PATH.name}


def main() -> int:
    receipts = [validate(operation) for operation in SAMPLES]
    print(json.dumps({"status": "PASS", "receipts": receipts}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
