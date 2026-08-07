#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from discover_prc_justice_trend_signals import select_query_rows

HERE = Path(__file__).resolve().parent
EXPECTED = {
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


def main() -> int:
    plan = json.loads((HERE / "prc-justice-trend-source-plan.json").read_text(encoding="utf-8"))
    rows = plan.get("signal_plans") or []
    types = {row.get("signal_type") for row in rows}
    assert types == EXPECTED, (types, EXPECTED)
    assert len(rows) == 12
    for row in rows:
        assert row.get("priority")
        assert row.get("source_families")
        assert row.get("query_templates")
        assert all(str(q).strip() for q in row["query_templates"])

    daily_types = set(plan["cadence"]["daily"])
    weekly_types = daily_types | set(plan["cadence"]["weekly"])
    daily_rows = select_query_rows(plan, daily_types, 6)
    weekly_rows = select_query_rows(plan, weekly_types, 12)
    assert {signal_type for signal_type, _ in daily_rows} == daily_types
    assert {signal_type for signal_type, _ in weekly_rows} == weekly_types
    assert len(daily_rows) <= 6
    assert len(weekly_rows) <= 12

    procurement = next(row for row in rows if row["signal_type"] == "procurement_and_budget")
    assert "ccgp.gov.cn" in procurement.get("allowed_hosts", [])
    rules = set(plan.get("cross_source_rules") or [])
    for required in [
        "training_signal_alone_never_equals_operational_capability",
        "procurement_intent_alone_never_equals_deployment",
        "case_practice_requires_primary_source_for_automatic_absorption",
        "judicial_outcome_can_confirm_or_downgrade_practice_inference",
        "standard_change_triggers_revalidation_of_related_capabilities",
        "doctrine_claim_must_distinguish_academic_discussion_from_formal_rule",
    ]:
        assert required in rules, required
    print(json.dumps({
        "status": "PASS",
        "signal_layers": len(types),
        "daily_signal_types": len(daily_types),
        "weekly_signal_types": len(weekly_types),
        "daily_query_coverage_complete": True,
        "weekly_query_coverage_complete": True,
        "procurement_monitoring": True,
        "training_monitoring": True,
        "research_monitoring": True,
        "standard_monitoring": True,
        "deployment_monitoring": True,
        "judicial_outcome_monitoring": True,
        "doctrine_monitoring": True,
        "cross_source_gates": len(rules),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
