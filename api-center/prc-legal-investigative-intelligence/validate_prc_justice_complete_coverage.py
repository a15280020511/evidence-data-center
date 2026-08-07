#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DAG_PATH = HERE / "prc-justice-complete-node-dag.json"
MONITOR_PATH = HERE / "prc-justice-monitoring-registry.json"


def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path.name} must be an object")
    return data


def main() -> int:
    dag = load(DAG_PATH)
    monitor = load(MONITOR_PATH)

    assert dag["schema_version"] == "prc-justice-complete-node-dag-v1"
    assert dag["jurisdiction"] == "PRC_MAINLAND"
    assert len(dag["normative_hierarchy"]) >= 12
    assert len(dag["legal_domain_nodes"]) >= 30
    assert len(dag["institutional_nodes"]) >= 10

    institutional_text = " ".join(
        node
        for group in dag["institutional_nodes"]
        for node in group.get("nodes", [])
    )
    required_institutions = [
        "中央政法委",
        "最高人民法院",
        "军事法院",
        "新疆生产建设兵团法院",
        "最高人民检察院",
        "军事检察",
        "公安部",
        "国家监察委员会",
        "司法部",
        "中国海警",
        "海关缉私",
        "移民管理",
        "人民陪审员",
        "人民监督员",
    ]
    for item in required_institutions:
        assert item in institutional_text, item

    required_dags = {
        "criminal_case_lifecycle",
        "civil_case_lifecycle",
        "administrative_case_lifecycle",
        "procuratorial_supervision_lifecycle",
        "discipline_supervision_lifecycle",
        "execution_bankruptcy_lifecycle",
        "public_legal_service_lifecycle",
        "education_research_to_practice_lifecycle",
        "lawmaking_to_case_feedback_lifecycle",
    }
    assert required_dags <= set(dag["process_dags"])
    assert len(dag["process_dags"]["criminal_case_lifecycle"]) >= 20
    assert "死刑复核（适用时）" in dag["process_dags"]["criminal_case_lifecycle"]
    assert "国家赔偿/司法救助（适用时）" in dag["process_dags"]["criminal_case_lifecycle"]

    safety = dag["safety_boundary"]
    for key in [
        "authenticated_party_auto_login",
        "captcha_or_waf_bypass",
        "hidden_api_reverse_engineering",
        "secret_internal_operational_material",
        "covert_surveillance_implementation_details",
        "target_selection_guidance",
        "investigation_evasion",
        "anti_forensics",
        "evidence_destruction",
    ]:
        assert safety[key] is False, key

    assert monitor["schema_version"] == "prc-justice-monitoring-registry-v1"
    assert len(monitor["source_groups"]) >= 8
    assert monitor["monitoring_policy"]["concurrency"] == 1
    assert monitor["monitoring_policy"]["automatic_retry"] is False
    assert monitor["monitoring_policy"]["automatic_login"] is False
    assert monitor["monitoring_policy"]["captcha_solving"] is False
    assert monitor["monitoring_policy"]["waf_bypass"] is False

    source_ids = {
        source.get("source_id")
        for group in monitor["source_groups"]
        for source in group.get("sources", [])
    }
    required_sources = {
        "npc-national-law-database",
        "spc-official",
        "spc-case-library",
        "spp-official",
        "12309-public",
        "mps-official",
        "mps-standards",
        "ccdi-nsc",
        "moj-official",
        "central-politico-legal",
        "coast-guard",
        "customs-anti-smuggling",
        "immigration-border",
        "academic-index-layer",
    }
    assert required_sources <= source_ids

    connectors = {row["id"]: row for row in monitor["discovery_and_retrieval_connectors"]}
    for connector in ["yuandian-law", "exa-api", "tavily-api", "jina-reader"]:
        assert connectors[connector]["status"] == "INTEGRATED"
    assert connectors["exa-mcp"]["status"] == "OPTIONAL_REDUNDANT"
    assert connectors["firecrawl-mcp"]["status"] == "RECOMMENDED_OPTIONAL"
    assert connectors["playwright-mcp"]["status"] == "RECOMMENDED_LOCAL_FALLBACK"
    assert connectors["browserless-mcp"]["status"] == "NOT_RECOMMENDED_AS_DEFAULT_FOR_PRC_JUSTICE"

    print(json.dumps({
        "status": "PASS",
        "normative_nodes": len(dag["normative_hierarchy"]),
        "institution_groups": len(dag["institutional_nodes"]),
        "legal_domains": len(dag["legal_domain_nodes"]),
        "process_dags": len(dag["process_dags"]),
        "monitoring_groups": len(monitor["source_groups"]),
        "connector_rows": len(monitor["discovery_and_retrieval_connectors"]),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
