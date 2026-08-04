#!/usr/bin/env python3
"""Cross-check Cloudflare AI routing and daily harvest quota controls."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

HERE = Path(__file__).resolve().parent
ROUTING_PATH = HERE / "cloudflare-ai-routing-policy.json"
DAILY_PATH = HERE / "cloudflare-daily-harvest-policy.json"


class QuotaConsistencyError(RuntimeError):
    pass


def _load(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise QuotaConsistencyError(f"{path.name} must contain an object")
    return value


def validate() -> dict[str, Any]:
    routing = _load(ROUTING_PATH)
    daily = _load(DAILY_PATH)
    if routing.get("schema_version") != "cloudflare-ai-numeric-routing-policy-v1":
        raise QuotaConsistencyError("unsupported Cloudflare AI routing policy")
    quota = routing.get("quota_policy")
    if not isinstance(quota, Mapping):
        raise QuotaConsistencyError("routing quota policy missing")
    expected = {
        "cloudflare_free_allocation_is_primary_semantic_budget": True,
        "reserve_fraction_for_high_value_pages": 0.02,
        "stop_new_ai_jobs_at_utilization": 0.98,
        "hard_stop_on_cloudflare_429": True,
        "same_day_retry_after_quota_error_allowed": False,
        "next_utc_day_resume_required": True,
        "overflow_action": "defer-until-next-utc-day-or-approved-external-tier",
        "standard_numeric_sources_must_not_consume_ai_quota": True,
    }
    if any(quota.get(key) != value for key, value in expected.items()):
        raise QuotaConsistencyError("routing quota policy mismatch")
    external = routing.get("external_model_policy")
    if not isinstance(external, Mapping):
        raise QuotaConsistencyError("external model policy missing")
    if external.get("enabled_by_default") is not False:
        raise QuotaConsistencyError("external model must remain disabled by default")
    if external.get("automatic_paid_fallback_allowed") is not False:
        raise QuotaConsistencyError("automatic paid fallback must remain forbidden")
    budget = daily.get("daily_budget")
    schedule = daily.get("schedule")
    limits = daily.get("cloudflare_free_limits")
    if not isinstance(budget, Mapping) or not isinstance(schedule, Mapping) or not isinstance(limits, Mapping):
        raise QuotaConsistencyError("daily harvest policy incomplete")
    if budget.get("maximum_estimated_workers_ai_neurons") != 9800:
        raise QuotaConsistencyError("daily neuron budget must match 98 percent utilization")
    if limits.get("workers_ai_neurons_per_utc_day") != 10000:
        raise QuotaConsistencyError("Workers AI free allocation mismatch")
    if budget.get("maximum_estimated_browser_run_seconds") != 570:
        raise QuotaConsistencyError("daily browser safety budget mismatch")
    if limits.get("browser_run_seconds_per_utc_day") != 600:
        raise QuotaConsistencyError("Browser Run free allocation mismatch")
    if schedule.get("resume_cron_utc") != "15 0 * * *":
        raise QuotaConsistencyError("next-day resume schedule mismatch")
    if schedule.get("same_day_automatic_retry_after_quota_error") is not False:
        raise QuotaConsistencyError("same-day automatic quota retry is forbidden")
    return {
        "status": "CLOUDFLARE_DAILY_QUOTA_POLICIES_CONSISTENT",
        "utilization_soft_stop": 0.98,
        "workers_ai_daily_budget": 9800,
        "browser_run_daily_budget_seconds": 570,
        "hard_stop_on_429": True,
        "next_day_resume": True,
        "external_model_enabled_by_default": False,
        "automatic_paid_fallback_allowed": False,
        "model_calls": 0,
        "paid_calls": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["validate"])
    parser.add_argument("--output-dir", type=Path, default=Path("china-intelligence-quota-validation"))
    args = parser.parse_args()
    receipt = validate()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "quota-consistency-receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
