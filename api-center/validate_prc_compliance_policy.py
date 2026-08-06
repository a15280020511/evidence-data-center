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
    catalog = load_json("api-catalog.json")
    manifest = load_json("connector-manifest.json")

    baseline = policy.get("legal_compliance_baseline", {})
    assert baseline.get("jurisdiction") == "PRC_MAINLAND"
    assert baseline.get("foreign_law_compliance_target") is False
    assert baseline.get("zero_risk_guarantee_prohibited") is True
    assert policy.get("continuity_principle") == "preserve_legal_capability_via_safe_fallbacks"
    assert policy.get("source_server_footprint_policy") == "source-server-footprint-policy.json"

    required_denies = {
        "arbitrary_url",
        "arbitrary_python",
        "arbitrary_shell",
        "arbitrary_javascript",
        "ticket_supplied_cookie",
        "ticket_supplied_authorization",
        "community_actor_with_credentials",
        "full_account_permissions",
        "residential_proxy",
        "proxy_pool",
        "random_egress_ip",
        "captcha_solving",
        "automatic_unblock",
        "user_agent_rotation",
        "tls_fingerprint_evasion",
        "hidden_endpoint_scanning",
        "vulnerability_scanning",
        "write_operations",
        "transaction",
        "trading",
        "unbounded_pagination",
        "full_database_mirroring",
        "raw_data_resale",
        "authenticated_prc_backend_via_foreign_cloud_without_explicit_permission",
        "cross_tool_denial_bypass",
        "cross_origin_retry_after_denial",
    }
    permanent_denies = set(policy.get("permanent_denies", []))
    missing_denies = sorted(required_denies - permanent_denies)
    assert not missing_denies, f"missing permanent denies: {missing_denies}"

    hard_stops = policy.get("hard_stop_rules", {})
    for key in (
        "401",
        "403",
        "429",
        "captcha",
        "waf",
        "block_page",
        "account_security_alert",
        "provider_complaint_or_notice",
    ):
        assert key in hard_stops, f"missing hard-stop rule: {key}"

    forbidden_recovery = set(policy.get("forbidden_recovery_actions", []))
    for action in (
        "rotate_ip_after_denial",
        "rotate_key_after_denial",
        "rotate_account_after_denial",
        "rotate_user_agent_after_denial",
        "switch_execution_provider_after_denial",
        "proxy_fallback_after_denial",
    ):
        assert action in forbidden_recovery, f"missing forbidden recovery action: {action}"

    assert footprint.get("status") == "production-control"
    assert footprint.get("jurisdiction") == "PRC_MAINLAND"
    assert footprint.get("foreign_ip_itself_is_illegal") is False
    assert footprint.get("identity_concealment_goal") is False

    origin = footprint.get("identity_and_origin_consistency", {})
    assert origin.get("one_primary_origin_class_per_account_or_key") is True
    assert origin.get("same_task_origin_switch_allowed") is False
    assert origin.get("denial_shared_across_all_tools") is True
    assert origin.get("cross_tool_quota_aggregation_required") is True
    assert origin.get("cross_tool_source_circuit_breaker_required") is True
    assert origin.get("alternate_origin_after_denial_allowed") is False

    retry = footprint.get("retry_policy", {})
    assert retry.get("automatic_retry_for_401") is False
    assert retry.get("automatic_retry_for_403") is False
    assert retry.get("automatic_retry_for_429") is False
    assert retry.get("automatic_retry_for_captcha_waf_or_block") is False
    assert retry.get("alternate_tool_or_origin_fallback_after_denial") is False

    authenticated = footprint.get("prc_source_profiles", {}).get(
        "authenticated_web_or_member_backend", {}
    )
    assert authenticated.get("foreign_cloud_allowed_by_default") is False
    assert authenticated.get("explicit_provider_permission_required_for_foreign_cloud") is True
    assert authenticated.get("account_origin_binding_required") is True

    client = footprint.get("client_identity", {})
    assert client.get("stable_user_agent_required") is True
    assert client.get("random_user_agent_rotation_allowed") is False
    assert client.get("tls_fingerprint_evasion_allowed") is False
    assert client.get("false_x_forwarded_for_allowed") is False

    api_task_text = (ROOT / "api_task.py").read_text(encoding="utf-8")
    retry_set_match = re.search(r"TRANSIENT_HTTP\s*=\s*\{([^}]*)\}", api_task_text)
    assert retry_set_match, "api_task.py retry set not found"
    retry_codes = {
        int(item)
        for item in re.findall(r"\b\d{3}\b", retry_set_match.group(1))
    }
    assert 401 not in retry_codes
    assert 403 not in retry_codes
    assert 429 not in retry_codes, "429 must be a hard stop, not an automatic retry"

    managed_providers = catalog.get("managed_providers", [])
    assert managed_providers, "managed provider catalog is empty"
    dangerous_limit_keys = {
        "arbitrary_urls_allowed",
        "arbitrary_code_allowed",
        "arbitrary_headers_allowed",
        "captcha_bypass_allowed",
        "residential_proxy_allowed",
        "proxy_rotation_after_denial_allowed",
        "user_agent_rotation_allowed",
        "fingerprint_evasion_allowed",
        "cross_origin_retry_after_denial_allowed",
        "write_operations_allowed",
        "trading_allowed",
        "account_control_allowed",
        "unbounded_pagination_allowed",
    }
    violations: list[str] = []
    for provider in managed_providers:
        limits = provider.get("limits", {})
        for key in dangerous_limit_keys:
            if limits.get(key) is True:
                violations.append(f"{provider.get('provider_id')}:{key}")
    assert not violations, f"dangerous provider capabilities enabled: {sorted(violations)}"

    assert manifest.get("enabled_connector_count") == manifest.get("connector_count")
    assert policy.get("catalog_admission_rule")
    assert (ROOT / "CHINA_MAINLAND_COMPLIANCE_BASELINE.md").is_file()
    assert (ROOT / "TOOL_ADMISSION_AND_CONTAINMENT_STANDARD.md").is_file()
    assert (ROOT / "SOURCE_SERVER_FOOTPRINT_CONTROL.md").is_file()

    result = {
        "status": "PASS",
        "legal_baseline": "PRC_MAINLAND",
        "source_server_footprint_control": "PASS",
        "managed_providers_checked": len(managed_providers),
        "connectors_checked": manifest.get("connector_count"),
        "zero_risk_guarantee": False,
        "continuity_fallbacks": len(policy.get("continuity_fallback_order", [])),
        "foreign_ip_itself_is_illegal": False,
        "automatic_429_retry": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
