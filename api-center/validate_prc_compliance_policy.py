from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_json(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def main() -> None:
    policy = load_json("tool-admission-policy.json")
    catalog = load_json("api-catalog.json")
    manifest = load_json("connector-manifest.json")

    baseline = policy.get("legal_compliance_baseline", {})
    assert baseline.get("jurisdiction") == "PRC_MAINLAND"
    assert baseline.get("foreign_law_compliance_target") is False
    assert baseline.get("zero_risk_guarantee_prohibited") is True
    assert policy.get("continuity_principle") == "preserve_legal_capability_via_safe_fallbacks"

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
        "captcha_solving",
        "automatic_unblock",
        "hidden_endpoint_scanning",
        "vulnerability_scanning",
        "write_operations",
        "transaction",
        "trading",
        "unbounded_pagination",
        "full_database_mirroring",
        "raw_data_resale",
    }
    permanent_denies = set(policy.get("permanent_denies", []))
    missing_denies = sorted(required_denies - permanent_denies)
    assert not missing_denies, f"missing permanent denies: {missing_denies}"

    hard_stops = policy.get("hard_stop_rules", {})
    for key in ("401", "403", "429", "captcha", "waf", "block_page"):
        assert key in hard_stops, f"missing hard-stop rule: {key}"

    forbidden_recovery = set(policy.get("forbidden_recovery_actions", []))
    assert "rotate_ip_after_denial" in forbidden_recovery
    assert "rotate_key_after_denial" in forbidden_recovery
    assert "rotate_account_after_denial" in forbidden_recovery
    assert "proxy_fallback_after_denial" in forbidden_recovery

    managed_providers = catalog.get("managed_providers", [])
    assert managed_providers, "managed provider catalog is empty"
    dangerous_limit_keys = {
        "arbitrary_urls_allowed",
        "arbitrary_code_allowed",
        "arbitrary_headers_allowed",
        "captcha_bypass_allowed",
        "residential_proxy_allowed",
        "proxy_rotation_after_denial_allowed",
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

    result = {
        "status": "PASS",
        "legal_baseline": "PRC_MAINLAND",
        "managed_providers_checked": len(managed_providers),
        "connectors_checked": manifest.get("connector_count"),
        "zero_risk_guarantee": False,
        "continuity_fallbacks": len(policy.get("continuity_fallback_order", [])),
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
