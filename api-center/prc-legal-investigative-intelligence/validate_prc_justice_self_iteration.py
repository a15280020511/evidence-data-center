#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
from pathlib import Path

from prc_justice_self_iteration import (
    build_observation,
    load_json,
    recompute_rollup,
    validate_contract,
)

HERE = Path(__file__).resolve().parent
POLICY = HERE / "prc-justice-self-iteration-policy.json"
MATRIX = HERE / "investigative-technology-intelligence-matrix.json"
LEDGER = HERE / "case-derived-investigative-capability-ledger.json"


def main() -> int:
    policy = load_json(POLICY)
    matrix = load_json(MATRIX)
    ledger = load_json(LEDGER)

    receipt = validate_contract(policy, matrix, ledger)
    assert receipt["status"] == "PASS"
    assert receipt["reviewable"] is True
    assert receipt["verifiable"] is True
    assert receipt["absorbable"] is True
    assert receipt["iterable"] is True
    assert receipt["secret_operational_details"] is False

    existing = [dict(row) for row in ledger["observations"]]
    candidate = {
        "url": "https://www.spp.gov.cn/example/202608/t20260807_000001.shtml",
        "title": "公开典型案例测试",
        "published_date": "2026-08-07",
        "engine": "fixture",
        "query": "fixture",
    }
    safe_text = (
        "2026年8月7日，最高人民检察院发布典型案例。"
        "案件在审查起诉阶段开展技术性证据审查，复核原始电子数据、应用日志、"
        "网络连接记录、平台数据和交易记录，并通过检警协作补强证据。"
    )
    observation, record = build_observation(candidate, safe_text, policy, existing)
    assert observation is not None
    assert record["status"] == "AUTO_ABSORB_ELIGIBLE"
    assert observation["verification_status"] == "PRIMARY_OBSERVED"
    caps = set(observation["capability_ids"])
    assert "electronic-data-forensics" in caps
    assert "network-log-and-connection-evidence" in caps
    assert "technical-evidence-specialist-review" in caps
    assert "interagency-evidence-cooperation" in caps
    assert observation["conflicts_with_observation_ids"] == []

    sensitive_text = safe_text + " 文中包含规避侦查的具体操作。"
    blocked, blocked_record = build_observation(candidate, sensitive_text, policy, existing)
    assert blocked is None
    assert blocked_record["reason"] == "sensitive_operational_signal"

    conflict_text = safe_text + " 法院最终认定证据不足并不予采信。"
    contested, contested_record = build_observation(candidate, conflict_text, policy, existing)
    assert contested is None
    assert contested_record["reason"] == "conflict_or_admissibility_review_signal"

    ledger_copy = copy.deepcopy(ledger)
    before = copy.deepcopy(ledger_copy["observations"])
    ledger_copy["observations"].append(observation)
    recompute_rollup(ledger_copy, policy)
    assert ledger_copy["observations"][: len(before)] == before
    rollups = {row["capability_id"]: row for row in ledger_copy["capability_rollup"]}
    assert set(observation["capability_ids"]).issubset(rollups)
    assert all(row["verification_level"] in {
        "PRIMARY_OBSERVED",
        "CORROBORATED_PRACTICE",
        "STRONGLY_CORROBORATED",
        "CONTESTED",
        "STALE_REVIEW_REQUIRED",
    } for row in rollups.values())

    safety = policy["safety_boundary"]
    assert safety["automatic_login"] is False
    assert safety["captcha_solving"] is False
    assert safety["waf_bypass"] is False
    assert safety["hidden_api_reverse_engineering"] is False
    assert safety["proxy_or_identity_rotation"] is False
    assert safety["investigation_evasion"] is False
    assert safety["anti_forensics"] is False
    assert policy["automation_gate"]["never_admin_bypass_branch_protection"] is True
    assert policy["verification_and_iteration"]["automatic_promotion_maximum"] == "CORROBORATED_PRACTICE"
    assert policy["verification_and_iteration"]["unmapped_new_technology_never_auto_adds_a_capability_id"] is True

    print(json.dumps({
        "status": "PASS",
        "schedule": policy["cadence"]["workflow_cron_utc"],
        "primary_hosts": len(policy["primary_outcome_hosts"]),
        "daily_queries": len(policy["daily_queries"]),
        "weekly_extra_queries": len(policy["weekly_extra_queries"]),
        "existing_observations": len(ledger["observations"]),
        "case_absorption": True,
        "network_investigation_learning": True,
        "reviewable": True,
        "verifiable": True,
        "absorbable": True,
        "iterable": True,
        "auto_merge_guarded": True,
        "secret_operational_details": False,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
