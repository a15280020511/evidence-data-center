#!/usr/bin/env python3
"""Validate China enterprise, social-platform and daily-harvest controls."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

HERE = Path(__file__).resolve().parent
HF_CONTROL = HERE.parents[1] / "huggingface" / "numeric-baseline-library"
ENTERPRISE_PATH = HF_CONTROL / "china-enterprise-soe-operational-domain-requirements.json"
SOCIAL_CODEBOOK_PATH = HF_CONTROL / "china-social-intelligence-codebook.json"
SOCIAL_ACCESS_PATH = HERE / "china-social-platform-access-policy.json"
DAILY_POLICY_PATH = HERE / "cloudflare-daily-harvest-policy.json"


class ChinaIntelligenceControlError(RuntimeError):
    pass


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _sha(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ChinaIntelligenceControlError(f"{name} must be an object")
    return value


def _unique_ids(rows: Any, expected: int, name: str, prefix: str | None = None) -> list[str]:
    if not isinstance(rows, list) or len(rows) != expected:
        raise ChinaIntelligenceControlError(f"{name} must contain exactly {expected} rows")
    ids: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise ChinaIntelligenceControlError(f"{name} row must be an object")
        value = str(row.get("id") or "")
        if not value or (prefix and not value.startswith(prefix)):
            raise ChinaIntelligenceControlError(f"invalid {name} id: {value!r}")
        ids.append(value)
    if len(ids) != len(set(ids)):
        raise ChinaIntelligenceControlError(f"duplicate {name} ids")
    return ids


def validate_enterprise(payload: Mapping[str, Any]) -> dict[str, Any]:
    if payload.get("schema_version") != "china-enterprise-soe-operational-domain-requirements-v1":
        raise ChinaIntelligenceControlError("unsupported enterprise/SOE control schema")
    if payload.get("status") != "production-control" or payload.get("domain_count") != 20:
        raise ChinaIntelligenceControlError("enterprise/SOE domains are incomplete")
    policy = _mapping(payload.get("storage_policy"), "enterprise storage policy")
    required_policy = {
        "huggingface_payload_numeric_only": True,
        "natural_language_payload_allowed": False,
        "control_metadata_location": "github",
        "selection_and_relay_owner": "gpts-usage-center",
        "compute_runtime_network_allowed": False,
        "direct_center_connection_allowed": False,
        "public_sources_only": True,
        "personal_data_allowed": False,
        "restricted_nonpublic_data_allowed": False,
        "individual_employee_tracking_allowed": False,
        "automatic_investment_recommendation_allowed": False,
    }
    if any(policy.get(key) != value for key, value in required_policy.items()):
        raise ChinaIntelligenceControlError("enterprise/SOE storage policy mismatch")
    scope = _mapping(payload.get("entity_scope"), "enterprise entity scope")
    if len(scope) < 10 or not all(value is True for value in scope.values()):
        raise ChinaIntelligenceControlError("enterprise entity scope is incomplete")
    domains = payload.get("domains")
    ids = _unique_ids(domains, 20, "enterprise domains", "cn-")
    for row in domains:
        if len(row.get("variable_groups") or []) < 10:
            raise ChinaIntelligenceControlError(f"enterprise domain lacks variable groups: {row.get('id')}")
        if not row.get("default_tables"):
            raise ChinaIntelligenceControlError(f"enterprise domain lacks table mappings: {row.get('id')}")
    return {"enterprise_domain_count": len(ids), "enterprise_domain_ids": ids}


def validate_social_access(payload: Mapping[str, Any]) -> dict[str, Any]:
    if payload.get("schema_version") != "china-social-platform-access-policy-v1":
        raise ChinaIntelligenceControlError("unsupported social access policy")
    if payload.get("status") != "production-control" or payload.get("platform_count") != 5:
        raise ChinaIntelligenceControlError("social platform policy is incomplete")
    global_policy = _mapping(payload.get("global_policy"), "social global policy")
    required_true = {
        "official_api_first",
        "browser_public_page_fallback_allowed",
        "numeric_aggregate_only",
        "enterprise_policy_topic_focus",
    }
    required_false = {
        "login_bypass_allowed",
        "captcha_bypass_allowed",
        "anti_bot_evasion_allowed",
        "mobile_private_api_reverse_engineering_allowed",
        "user_cookie_pool_allowed",
        "private_message_collection_allowed",
        "personal_profile_building_allowed",
        "raw_content_persistence_allowed",
        "raw_comment_persistence_allowed",
        "copyrighted_video_download_allowed",
        "deleted_or_restricted_content_recovery_allowed",
    }
    if any(global_policy.get(key) is not True for key in required_true):
        raise ChinaIntelligenceControlError("required safe social capability is disabled")
    if any(global_policy.get(key) is not False for key in required_false):
        raise ChinaIntelligenceControlError("forbidden social collection capability is enabled")
    platforms = payload.get("platforms")
    ids = _unique_ids(platforms, 5, "social platforms")
    expected = {"weibo", "douyin", "bilibili", "zhihu", "wechat-channels"}
    if set(ids) != expected:
        raise ChinaIntelligenceControlError("social platform coverage mismatch")
    numeric_outputs = payload.get("allowed_numeric_outputs")
    forbidden_outputs = payload.get("forbidden_outputs")
    if not isinstance(numeric_outputs, list) or len(numeric_outputs) < 10:
        raise ChinaIntelligenceControlError("social numeric output contract is incomplete")
    if not isinstance(forbidden_outputs, list) or len(forbidden_outputs) < 7:
        raise ChinaIntelligenceControlError("social forbidden output contract is incomplete")
    return {"social_platform_count": len(ids), "social_platform_ids": ids}


def validate_social_codebook(payload: Mapping[str, Any], social_access: Mapping[str, Any]) -> dict[str, Any]:
    if payload.get("schema_version") != "china-social-intelligence-codebook-v1":
        raise ChinaIntelligenceControlError("unsupported social intelligence codebook")
    if payload.get("status") != "production-control":
        raise ChinaIntelligenceControlError("social intelligence codebook is not production-control")
    if payload.get("storage_location") != "github-only" or payload.get("huggingface_upload_allowed") is not False:
        raise ChinaIntelligenceControlError("social codebook must remain GitHub-only")
    platforms = _mapping(payload.get("platforms"), "social platform codes")
    policy_platforms = {
        str(row["id"]): int(row["platform_id"])
        for row in social_access.get("platforms") or []
    }
    code_platforms = {
        "weibo": platforms.get("WEIBO"),
        "douyin": platforms.get("DOUYIN"),
        "bilibili": platforms.get("BILIBILI"),
        "zhihu": platforms.get("ZHIHU"),
        "wechat-channels": platforms.get("WECHAT_CHANNELS"),
    }
    if code_platforms != policy_platforms:
        raise ChinaIntelligenceControlError("social platform numeric codes mismatch")
    metrics = _mapping(payload.get("metrics"), "social metric codes")
    events = _mapping(payload.get("events"), "social event codes")
    relations = _mapping(payload.get("relations"), "social relation codes")
    quality = _mapping(payload.get("quality_flags"), "social quality flags")
    if len(metrics) != 70 or len(set(metrics.values())) != 70:
        raise ChinaIntelligenceControlError("social codebook must contain exactly 70 unique metrics")
    if len(events) < 12 or len(relations) < 10 or len(quality) < 12:
        raise ChinaIntelligenceControlError("social event/relation/quality codes are incomplete")
    rules = _mapping(payload.get("rules"), "social codebook rules")
    if rules.get("raw_content_to_huggingface") is not False:
        raise ChinaIntelligenceControlError("raw social content must not enter Hugging Face")
    if rules.get("individual_account_profile_to_huggingface") is not False:
        raise ChinaIntelligenceControlError("individual account profiles must not enter Hugging Face")
    if int(rules.get("minimum_aggregation_group_size") or 0) < 20:
        raise ChinaIntelligenceControlError("social aggregation group is too small")
    return {
        "social_metric_count": len(metrics),
        "social_event_count": len(events),
        "social_relation_count": len(relations),
    }


def validate_daily_policy(payload: Mapping[str, Any]) -> dict[str, Any]:
    if payload.get("schema_version") != "cloudflare-daily-harvest-policy-v1":
        raise ChinaIntelligenceControlError("unsupported daily harvest policy")
    if payload.get("status") != "production-control":
        raise ChinaIntelligenceControlError("daily harvest policy is not production-control")
    limits = _mapping(payload.get("cloudflare_free_limits"), "Cloudflare free limits")
    expected_limits = {
        "workers_ai_neurons_per_utc_day": 10000,
        "browser_run_seconds_per_utc_day": 600,
        "quick_action_minimum_interval_seconds": 10,
        "browser_timeout_seconds": 60,
        "crawl_jobs_per_utc_day": 5,
        "crawl_max_pages_per_job": 100,
        "reset_time_utc": "00:00",
    }
    if any(limits.get(key) != value for key, value in expected_limits.items()):
        raise ChinaIntelligenceControlError("Cloudflare free limits snapshot mismatch")
    budget = _mapping(payload.get("daily_budget"), "daily budget")
    if int(budget.get("maximum_estimated_workers_ai_neurons") or 0) > 10000:
        raise ChinaIntelligenceControlError("daily neuron budget exceeds free allocation")
    if int(budget.get("maximum_estimated_browser_run_seconds") or 0) > 600:
        raise ChinaIntelligenceControlError("daily browser budget exceeds free allocation")
    if int(budget.get("maximum_concurrent_collection_tasks") or 0) != 1:
        raise ChinaIntelligenceControlError("daily harvest must remain serial")
    if budget.get("paid_usage_allowed") is not False or budget.get("automatic_paid_upgrade_allowed") is not False:
        raise ChinaIntelligenceControlError("paid Cloudflare usage must remain disabled")
    schedule = _mapping(payload.get("schedule"), "daily schedule")
    if schedule.get("resume_cron_utc") != "15 0 * * *":
        raise ChinaIntelligenceControlError("daily resume schedule mismatch")
    if schedule.get("same_day_automatic_retry_after_quota_error") is not False:
        raise ChinaIntelligenceControlError("same-day retry after quota exhaustion is forbidden")
    queue = _mapping(payload.get("queue"), "daily queue")
    if queue.get("storage") != "github-issues-and-comments" or queue.get("raw_content_in_queue_allowed") is not False:
        raise ChinaIntelligenceControlError("daily queue storage policy mismatch")
    if queue.get("one_active_task_global") is not True or queue.get("duplicate_task_id_allowed") is not False:
        raise ChinaIntelligenceControlError("daily queue concurrency or duplicate policy mismatch")
    stop_conditions = set(payload.get("stop_conditions") or [])
    required_stops = {
        "cloudflare_http_429",
        "browser_time_limit_exceeded",
        "workers_ai_neuron_limit_exceeded",
        "captcha_or_login_required",
        "platform_access_policy_violation",
    }
    if not required_stops.issubset(stop_conditions):
        raise ChinaIntelligenceControlError("daily quota stop conditions are incomplete")
    data_rules = _mapping(payload.get("data_rules"), "daily data rules")
    if data_rules.get("numeric_parquet_only_to_huggingface") is not True:
        raise ChinaIntelligenceControlError("daily harvest must write numeric Parquet only")
    if data_rules.get("raw_text_to_huggingface") is not False or data_rules.get("personal_data_allowed") is not False:
        raise ChinaIntelligenceControlError("daily harvest raw text or personal data policy mismatch")
    return {
        "daily_neuron_budget": int(budget["maximum_estimated_workers_ai_neurons"]),
        "daily_browser_second_budget": int(budget["maximum_estimated_browser_run_seconds"]),
        "daily_request_cap": int(budget["maximum_quick_action_requests"]),
        "daily_resume_cron_utc": schedule["resume_cron_utc"],
    }


def validate_all() -> dict[str, Any]:
    enterprise = _mapping(_load(ENTERPRISE_PATH), "enterprise controls")
    social_access = _mapping(_load(SOCIAL_ACCESS_PATH), "social access controls")
    social_codebook = _mapping(_load(SOCIAL_CODEBOOK_PATH), "social codebook")
    daily_policy = _mapping(_load(DAILY_POLICY_PATH), "daily policy")
    receipt: dict[str, Any] = {
        "status": "CHINA_ENTERPRISE_SOCIAL_DAILY_CONTROLS_VALIDATED",
        "model_calls": 0,
        "paid_calls": 0,
        "raw_text_persisted": False,
        "numeric_huggingface_payload_only": True,
        "direct_center_connection_allowed": False,
    }
    receipt.update(validate_enterprise(enterprise))
    receipt.update(validate_social_access(social_access))
    receipt.update(validate_social_codebook(social_codebook, social_access))
    receipt.update(validate_daily_policy(daily_policy))
    receipt["control_sha256"] = _sha(
        {
            "enterprise": enterprise,
            "social_access": social_access,
            "social_codebook": social_codebook,
            "daily_policy": daily_policy,
        }
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["validate"])
    parser.add_argument("--output-dir", type=Path, default=Path("china-intelligence-control-validation"))
    args = parser.parse_args()
    receipt = validate_all()
    _write(args.output_dir / "validation-receipt.json", receipt)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
