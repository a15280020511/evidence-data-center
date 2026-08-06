from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_json(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def main() -> None:
    policy = load_json("tool-admission-policy.json")
    footprint = load_json("source-server-footprint-policy.json")
    scope = load_json("jurisdiction-scope-policy.json")
    channels = load_json("prc-source-channel-policy.json")
    catalog = load_json("api-catalog.json")
    manifest = load_json("connector-manifest.json")

    baseline = policy.get("legal_compliance_baseline", {})
    assert baseline.get("jurisdiction") == "PRC_MAINLAND"
    assert baseline.get("foreign_law_compliance_target") is False
    assert baseline.get("zero_risk_guarantee_prohibited") is True
    assert policy.get("continuity_principle") == "preserve_legal_capability_via_safe_fallbacks"
    assert policy.get("source_server_footprint_policy") == "source-server-footprint-policy.json"

    assert scope.get("schema_version") == "intelligence-jurisdiction-scope-v2"
    assert scope.get("status") == "production-control"
    assert scope.get("default_legal_target") == "PRC_MAINLAND"
    assert scope.get("principle") == "prc_strict_controls_only_for_prc_sources_and_prc_data_flows"
    assert scope.get("prc_source_channel_policy") == "prc-source-channel-policy.json"

    classification = scope.get("classification", {})
    assert classification.get("source_country_metadata_required") is True
    assert classification.get("ip_address_or_tld_alone_is_not_sufficient") is True
    assert classification.get("unknown_source_country_action") == "REVIEW_BEFORE_PRODUCTION"
    assert len(classification.get("prc_scope_applies_when_any", [])) >= 4

    profiles = scope.get("profiles", {})
    prc = profiles.get("PRC_STRICT", {})
    global_baseline = profiles.get("GLOBAL_OPERATIONAL_BASELINE", {})
    assert prc.get("legal_baseline") == "PRC_MAINLAND"
    assert prc.get("source_channel_policy") == "prc-source-channel-policy.json"
    assert prc.get("channel_tiering_enabled") is True
    assert set(prc.get("required_channel_tiers", [])) == {
        "GREEN_DIRECT",
        "YELLOW_CONTROLLED",
        "ORANGE_DEDICATED",
        "RED_PROHIBITED",
    }
    assert prc.get("green_official_channels_may_use_channel_specific_relaxed_defaults") is True
    assert prc.get("prc_cross_border_data_gate") is True
    assert prc.get("foreign_cloud_authenticated_backend_gate") is True
    assert prc.get("account_primary_origin_binding") is True
    assert prc.get("cross_tool_source_circuit_breaker") is True
    assert prc.get("public_web_default_max_concurrency") == 1
    assert prc.get("denial_behavior") == "shared_hard_stop_across_tools_and_origins"

    assert global_baseline.get("prc_specific_legal_controls_enabled") is False
    assert global_baseline.get("prc_cross_border_data_gate") is False
    assert global_baseline.get("prc_fixed_runner_required") is False
    assert global_baseline.get("foreign_cloud_authenticated_backend_blocked_by_prc_policy") is False
    assert global_baseline.get("prc_public_web_default_rate_limits_enabled") is False
    assert global_baseline.get("provider_documented_limits_take_precedence") is True
    assert global_baseline.get("secret_isolation_required") is True
    assert global_baseline.get("provider_terms_and_account_scope_required") is True
    assert global_baseline.get("arbitrary_code_secret_exposure_vulnerability_exploitation_and_unapproved_write_operations_forbidden") is True

    global_controls = set(scope.get("global_security_controls", []))
    required_global_controls = {
        "secret_isolation",
        "account_and_api_scope_enforcement",
        "provider_terms_quota_and_block_signal_enforcement",
        "bounded_runtime_requests_pagination_response_bytes_and_cost",
        "no_stolen_credentials_or_secret_exposure",
        "no_vulnerability_exploitation_or_malicious_code",
        "no_unapproved_write_transaction_trading_or_account_control",
    }
    assert not (required_global_controls - global_controls)

    prc_only = set(scope.get("prc_only_controls", []))
    required_prc_only = {
        "prc_channel_tier_assignment",
        "prc_source_server_visible_footprint_profile",
        "prc_account_primary_origin_binding",
        "prc_cross_tool_source_budget_and_circuit_breaker",
        "prc_foreign_cloud_authenticated_backend_gate",
        "prc_public_web_low_frequency_defaults",
        "prc_green_official_channel_relaxed_defaults",
        "prc_personal_important_and_restricted_geospatial_cross_border_gate",
        "prc_fixed_runner_fallback",
        "prc_no_cross_origin_denial_bypass",
    }
    assert not (required_prc_only - prc_only)

    assert channels.get("schema_version") == "prc-source-channel-tiering-v1"
    assert channels.get("status") == "production-control"
    assert channels.get("jurisdiction") == "PRC_MAINLAND"
    assert channels.get("principle") == "classify_channel_then_apply_minimum_necessary_controls"
    assert channels.get("default_action") == "REVIEW_BEFORE_PRODUCTION"
    assert len(channels.get("classification_dimensions", [])) >= 8

    tiers = channels.get("tiers", {})
    assert set(tiers) == {
        "GREEN_DIRECT",
        "YELLOW_CONTROLLED",
        "ORANGE_DEDICATED",
        "RED_PROHIBITED",
    }
    green = tiers["GREEN_DIRECT"]
    yellow = tiers["YELLOW_CONTROLLED"]
    orange = tiers["ORANGE_DEDICATED"]
    red = tiers["RED_PROHIBITED"]

    assert green.get("production_state") == "PRODUCTION_SAFE_READONLY"
    assert len(green.get("channels", [])) >= 6
    assert green.get("request_defaults", {}).get("official_api") == "FOLLOW_PROVIDER_DOCUMENTED_LIMITS"
    assert green.get("request_defaults", {}).get("public_static_web_max_concurrency") == 2
    assert "blanket_ten_second_interval" in set(green.get("controls_not_required_by_default", []))
    assert "prc_fixed_runner" in set(green.get("controls_not_required_by_default", []))

    assert yellow.get("production_state") == "PROVISIONAL_SAFE_READONLY_OR_PRODUCTION_SAFE_READONLY"
    yellow_defaults = yellow.get("request_defaults", {})
    assert yellow_defaults.get("max_concurrency") == 1
    assert yellow_defaults.get("minimum_interval_seconds") == 10
    assert yellow_defaults.get("max_pages_per_task") == 20
    assert yellow_defaults.get("max_requests_per_domain_per_hour") == 30
    assert "401_403_429_captcha_waf_hard_stop" in set(yellow.get("required_controls", []))

    assert orange.get("production_state") == "CONTROLLED_SPECIAL_USE"
    orange_controls = set(orange.get("required_controls", []))
    assert "dedicated_source_specific_connector" in orange_controls
    assert "official_api_or_export_first" in orange_controls
    assert "foreign_cloud_authenticated_access_requires_explicit_provider_permission" in orange_controls
    assert orange.get("request_defaults", {}).get("origin_switch") == "FORBIDDEN"

    assert red.get("production_state") == "REJECTED_OR_DISABLED"
    assert len(red.get("channels", [])) >= 9
    assert red.get("required_action") == "PERMANENTLY_DENY_AND_QUARANTINE_ANY_TOOL_REQUIRING_THESE_CAPABILITIES"

    escalation = channels.get("tier_escalation_rules", {})
    for key in (
        "personal_data_detected",
        "important_data_detected",
        "restricted_geospatial_data_detected",
        "commercial_secret_or_nonpublic_backend_data_detected",
        "license_scope_unknown",
        "401_403_429_captcha_waf_or_account_alert",
    ):
        assert key in escalation
    assert len(channels.get("channel_selection_order", [])) >= 6

    assert footprint.get("status") == "production-control"
    assert footprint.get("jurisdiction") == "PRC_MAINLAND"
    assert footprint.get("foreign_ip_itself_is_illegal") is False
    assert footprint.get("identity_concealment_goal") is False

    retry = footprint.get("retry_policy", {})
    assert retry.get("automatic_retry_for_401") is False
    assert retry.get("automatic_retry_for_403") is False
    assert retry.get("automatic_retry_for_429") is False
    assert retry.get("automatic_retry_for_captcha_waf_or_block") is False

    api_task_text = (ROOT / "api_task.py").read_text(encoding="utf-8")
    retry_set_match = re.search(r"TRANSIENT_HTTP\s*=\s*\{([^}]*)\}", api_task_text)
    assert retry_set_match, "api_task.py retry set not found"
    retry_codes = {int(item) for item in re.findall(r"\b\d{3}\b", retry_set_match.group(1))}
    assert 401 not in retry_codes
    assert 403 not in retry_codes
    assert 429 not in retry_codes

    managed_providers = catalog.get("managed_providers", [])
    assert managed_providers, "managed provider catalog is empty"
    globally_dangerous_limit_keys = {
        "arbitrary_urls_allowed",
        "arbitrary_code_allowed",
        "arbitrary_headers_allowed",
        "write_operations_allowed",
        "trading_allowed",
        "account_control_allowed",
        "unbounded_pagination_allowed",
    }
    violations: list[str] = []
    for provider in managed_providers:
        limits = provider.get("limits", {})
        for key in globally_dangerous_limit_keys:
            if limits.get(key) is True:
                violations.append(f"{provider.get('provider_id')}:{key}")
    assert not violations, f"globally dangerous provider capabilities enabled: {sorted(violations)}"

    assert manifest.get("enabled_connector_count") == manifest.get("connector_count")
    for name in (
        "CHINA_MAINLAND_COMPLIANCE_BASELINE.md",
        "TOOL_ADMISSION_AND_CONTAINMENT_STANDARD.md",
        "SOURCE_SERVER_FOOTPRINT_CONTROL.md",
        "JURISDICTION_SCOPE_POLICY.md",
        "jurisdiction-scope-policy.json",
        "PRC_SOURCE_CHANNEL_TIERING.md",
        "prc-source-channel-policy.json",
    ):
        assert (ROOT / name).is_file(), f"missing policy file: {name}"

    result = {
        "status": "PASS",
        "legal_baseline": "PRC_MAINLAND",
        "strict_prc_controls_scope": "PRC_SOURCES_AND_PRC_DATA_FLOWS_ONLY",
        "prc_channel_tiers": sorted(tiers),
        "green_official_channels_relaxed": True,
        "non_prc_profile": "GLOBAL_OPERATIONAL_BASELINE",
        "source_server_footprint_control": "PRC_ONLY",
        "managed_providers_checked": len(managed_providers),
        "connectors_checked": manifest.get("connector_count"),
        "zero_risk_guarantee": False,
        "foreign_ip_itself_is_illegal": False,
        "automatic_429_retry": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
