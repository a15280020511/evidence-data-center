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

    assert scope.get("schema_version") == "intelligence-jurisdiction-scope-v3"
    assert scope.get("status") == "production-control"
    assert scope.get("default_legal_target") == "PRC_MAINLAND"
    assert scope.get("principle") == "prc_strict_controls_only_for_user_attributable_real_name_or_identity_linked_legal_risk"
    assert scope.get("prc_source_channel_policy") == "prc-source-channel-policy.json"

    classification = scope.get("classification", {})
    assert classification.get("source_country_metadata_required") is True
    assert len(classification.get("prc_nexus_applies_when_any", [])) >= 4
    assert len(classification.get("user_identity_attribution_signals", [])) >= 5
    assert len(classification.get("material_legal_or_account_risk_triggers", [])) >= 6
    assert set(classification.get("prc_strict_requires_all", [])) == {
        "prc_nexus_present",
        "at_least_one_user_identity_attribution_signal",
        "at_least_one_material_legal_or_account_risk_trigger",
    }
    assert len(classification.get("prc_public_baseline_when_all", [])) >= 4
    assert classification.get("ordinary_ip_tld_or_routine_anonymous_access_log_alone_is_not_sufficient") is True
    assert classification.get("unknown_source_country_action") == "REVIEW_BEFORE_PRODUCTION"
    assert classification.get("unknown_identity_attribution_action") == "REVIEW_BEFORE_PRODUCTION"
    assert classification.get("unknown_material_risk_action") == "REVIEW_BEFORE_PRODUCTION"

    profiles = scope.get("profiles", {})
    prc = profiles.get("PRC_STRICT", {})
    global_baseline = profiles.get("GLOBAL_OPERATIONAL_BASELINE", {})
    assert prc.get("legal_baseline") == "PRC_MAINLAND"
    assert "reasonably attributable" in prc.get("applies_to", "")
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

    assert "PRC public sources" in global_baseline.get("applies_to", "")
    assert global_baseline.get("prc_specific_legal_controls_enabled") is False
    assert global_baseline.get("prc_cross_border_data_gate") is False
    assert global_baseline.get("prc_fixed_runner_required") is False
    assert global_baseline.get("foreign_cloud_authenticated_backend_blocked_by_prc_policy") is False
    assert global_baseline.get("prc_public_web_default_rate_limits_enabled") is False
    assert global_baseline.get("prc_account_primary_origin_binding_required") is False
    assert global_baseline.get("prc_detailed_source_footprint_receipt_required") is False
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

    attributable_controls = set(scope.get("prc_attributable_risk_controls", []))
    required_attributable_controls = {
        "prc_channel_tier_assignment",
        "prc_attributable_source_server_visible_footprint_profile",
        "prc_attributable_account_primary_origin_binding",
        "prc_attributable_cross_tool_source_budget_and_circuit_breaker",
        "prc_attributable_foreign_cloud_authenticated_backend_gate",
        "prc_personal_important_and_restricted_geospatial_cross_border_gate",
        "prc_fixed_runner_fallback",
        "prc_no_cross_origin_denial_bypass",
    }
    assert not (required_attributable_controls - attributable_controls)

    assert channels.get("schema_version") == "prc-source-channel-tiering-v2"
    assert channels.get("status") == "production-control"
    assert channels.get("jurisdiction") == "PRC_MAINLAND"
    assert channels.get("principle") == "identity_attribution_gate_then_channel_tier_then_minimum_necessary_controls"
    assert channels.get("default_action") == "REVIEW_BEFORE_PRODUCTION"
    assert len(channels.get("classification_dimensions", [])) >= 10

    scope_gate = channels.get("scope_gate", {})
    assert set(scope_gate.get("strict_control_requires_all", [])) == {
        "prc_nexus_present",
        "user_real_name_or_identity_linked_activity_is_reasonably_attributable",
        "material_legal_or_account_risk_trigger_present",
    }
    assert len(scope_gate.get("identity_attribution_examples", [])) >= 4
    assert len(scope_gate.get("risk_trigger_examples", [])) >= 6
    assert scope_gate.get("outside_scope_action") == "USE_GLOBAL_OPERATIONAL_BASELINE_WITHOUT_PRC_SPECIFIC_RATE_OR_ORIGIN_CONTROLS"
    assert scope_gate.get("ordinary_ip_tld_or_routine_anonymous_server_log_alone_triggers_strict_control") is False

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

    assert green.get("applicability_condition") == "PRC_STRICT_SCOPE_GATE_PASSED"
    assert green.get("production_state") == "PRODUCTION_SAFE_READONLY"
    assert len(green.get("channels", [])) >= 6
    assert green.get("request_defaults", {}).get("official_api") == "FOLLOW_PROVIDER_DOCUMENTED_LIMITS"
    assert "blanket_ten_second_interval" in set(green.get("controls_not_required_by_default", []))
    assert "prc_fixed_runner" in set(green.get("controls_not_required_by_default", []))

    assert yellow.get("applicability_condition") == "PRC_STRICT_SCOPE_GATE_PASSED"
    assert yellow.get("production_state") == "PROVISIONAL_SAFE_READONLY_OR_PRODUCTION_SAFE_READONLY"
    yellow_defaults = yellow.get("request_defaults", {})
    assert yellow_defaults.get("max_concurrency") == 1
    assert yellow_defaults.get("minimum_interval_seconds") == 10
    assert yellow_defaults.get("max_pages_per_task") == 20
    assert yellow_defaults.get("max_requests_per_domain_per_hour") == 30
    assert "401_403_429_captcha_waf_hard_stop" in set(yellow.get("required_controls", []))

    assert orange.get("applicability_condition") == "PRC_STRICT_SCOPE_GATE_PASSED"
    assert orange.get("production_state") == "CONTROLLED_SPECIAL_USE"
    orange_controls = set(orange.get("required_controls", []))
    assert "dedicated_source_specific_connector" in orange_controls
    assert "official_api_or_export_first" in orange_controls
    assert "foreign_cloud_authenticated_access_requires_explicit_provider_permission" in orange_controls
    assert orange.get("request_defaults", {}).get("origin_switch") == "FORBIDDEN"

    assert red.get("applicability_condition") == "GLOBAL_SECURITY_DENY_INCLUDING_PRC_STRICT"
    assert red.get("production_state") == "REJECTED_OR_DISABLED"
    assert len(red.get("channels", [])) >= 9
    assert red.get("required_action") == "PERMANENTLY_DENY_AND_QUARANTINE_ANY_TOOL_REQUIRING_THESE_CAPABILITIES"

    escalation = channels.get("tier_escalation_rules", {})
    for key in (
        "personal_data_detected",
        "important_data_detected",
        "restricted_geospatial_data_detected",
        "commercial_secret_or_nonpublic_backend_data_detected",
        "identity_attribution_becomes_known",
        "material_legal_or_account_risk_becomes_known",
        "license_scope_unknown",
        "401_403_429_captcha_waf_or_account_alert",
    ):
        assert key in escalation
    assert len(channels.get("channel_selection_order", [])) >= 7

    assert footprint.get("schema_version") == "source-server-footprint-control-v2"
    assert footprint.get("status") == "production-control"
    assert footprint.get("jurisdiction") == "PRC_MAINLAND"
    assert footprint.get("principle") == "strict_footprint_control_only_for_user_attributable_prc_legal_or_account_risk"
    assert footprint.get("foreign_ip_itself_is_illegal") is False
    assert footprint.get("identity_concealment_goal") is False

    footprint_gate = footprint.get("scope_gate", {})
    assert footprint_gate.get("requires_profile") == "PRC_STRICT"
    assert footprint_gate.get("routine_anonymous_ip_or_access_log_alone_is_sufficient") is False
    assert footprint_gate.get("public_no_login_no_user_binding_action") == "GLOBAL_OPERATIONAL_BASELINE"

    source_profiles = footprint.get("prc_source_profiles", {})
    public_profile = source_profiles.get("public_web_no_login_no_user_binding", {})
    assert public_profile.get("strict_prc_footprint_controls_required") is False
    assert public_profile.get("profile") == "GLOBAL_OPERATIONAL_BASELINE"
    assert public_profile.get("prc_default_ten_second_interval_required") is False
    assert public_profile.get("prc_default_twenty_page_limit_required") is False
    assert public_profile.get("routine_anonymous_server_log_is_identity_attribution") is False

    identity_consistency = footprint.get("identity_and_origin_consistency", {})
    assert identity_consistency.get("applies_only_to_user_attributable_account_key_session_or_paid_identity") is True
    assert identity_consistency.get("one_primary_origin_class_per_account_or_key") is True
    assert identity_consistency.get("alternate_origin_after_denial_allowed") is False

    request_defaults = footprint.get("request_footprint_defaults", {})
    assert request_defaults.get("applies_only_to_prc_strict_profile") is True
    assert request_defaults.get("web_max_concurrency") == 1
    assert request_defaults.get("web_minimum_interval_seconds") == 10
    assert request_defaults.get("web_max_pages_per_task") == 20

    retry = footprint.get("retry_policy", {})
    assert retry.get("automatic_retry_for_401") is False
    assert retry.get("automatic_retry_for_403") is False
    assert retry.get("automatic_retry_for_429") is False
    assert retry.get("automatic_retry_for_captcha_waf_or_block") is False

    audit_receipt = footprint.get("source_side_audit_receipt", {})
    assert audit_receipt.get("detailed_receipt_required_only_for_prc_strict") is True
    assert audit_receipt.get("baseline_structured_receipt_required_for_other_profiles") is True
    assert audit_receipt.get("secret_cookie_or_real_name_value_recording_allowed") is False
    required_receipt_fields = {
        "jurisdiction_profile",
        "identity_attribution_state",
        "material_risk_state",
        "authenticated",
        "http_status_sequence",
        "cleanup_status",
    }
    assert not (required_receipt_fields - set(audit_receipt.get("required_fields", [])))

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
        "strict_prc_controls_scope": "USER_ATTRIBUTABLE_REAL_NAME_OR_IDENTITY_LINKED_PRC_LEGAL_OR_ACCOUNT_RISK_ONLY",
        "prc_strict_gate": ["PRC_NEXUS", "USER_ATTRIBUTION", "MATERIAL_RISK"],
        "anonymous_prc_public_source_profile": "GLOBAL_OPERATIONAL_BASELINE",
        "ordinary_anonymous_log_triggers_strict_control": False,
        "prc_channel_tiers": sorted(tiers),
        "green_official_channels_relaxed": True,
        "managed_providers_checked": len(managed_providers),
        "connectors_checked": manifest.get("connector_count"),
        "zero_risk_guarantee": False,
        "foreign_ip_itself_is_illegal": False,
        "automatic_429_retry": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
