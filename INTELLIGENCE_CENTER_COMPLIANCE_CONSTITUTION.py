#!/usr/bin/env python3
"""Machine-executable compliance constitution for the Intelligence Center."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ALLOW = "ALLOW"
REVIEW = "MANUAL_REVIEW"
BLOCK = "BLOCKED"
STOP = "STOPPED_BY_UPSTREAM"

REQUIRED = {
    "task_id", "source_type", "access_method", "authorization_basis",
    "purpose", "fields", "foreign_egress", "fixed_egress",
    "ip_rotation", "proxy_pool", "bypass_attempted",
    "contains_personal_data", "contains_sensitive_personal_data",
    "contains_identity_authentication_data", "contains_secret_or_important_data",
    "overseas_storage", "storage_location", "redistribution",
    "full_database_copy", "concurrency", "rate_limit_rps", "incremental_only",
}

STOP_SIGNALS = {
    401, 403, 429,
    "CAPTCHA", "WAF_CHALLENGE", "DEVICE_VERIFICATION",
    "ACCOUNT_FROZEN", "IP_BLOCKED", "GEO_BLOCKED", "CEASE_NOTICE",
}

COMMERCIAL_WEB = {"commercial_web"}
AUTHORIZED_COMMERCIAL = {"commercial_api", "commercial_sftp"}
GOV_OPEN = {"government_open_api", "government_download"}


def result(decision: str, *rules: str) -> dict[str, Any]:
    return {"decision": decision, "matched_rules": list(rules)}


def evaluate(t: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(k for k in REQUIRED if k not in t)
    if missing:
        return {"decision": BLOCK, "matched_rules": ["MISSING_REQUIRED_INPUT"], "missing": missing}

    signal = t.get("upstream_signal")
    if signal in STOP_SIGNALS:
        return result(STOP, "UPSTREAM_REJECTION")

    if t["bypass_attempted"] or t["ip_rotation"] or t["proxy_pool"]:
        return result(BLOCK, "BYPASS_OR_IP_EVASION")

    if not str(t["authorization_basis"]).strip() or t.get("access_exceeds_authorization"):
        return result(BLOCK, "NO_OR_EXCEEDED_AUTHORIZATION")

    if t.get("credential_source") in {"stolen", "shared", "purchased", "leaked", "expired", "unknown"}:
        return result(BLOCK, "INVALID_CREDENTIAL_SOURCE")

    if t["contains_secret_or_important_data"]:
        return result(BLOCK, "SECRET_OR_IMPORTANT_DATA")

    if t["contains_identity_authentication_data"]:
        return result(BLOCK, "IDENTITY_AUTHENTICATION_DATA")

    if t["source_type"] in COMMERCIAL_WEB:
        return result(BLOCK, "COMMERCIAL_WEB_SCRAPING")

    if (t["redistribution"] or t["full_database_copy"]) and not t.get("explicit_contract_permission", False):
        return result(BLOCK, "UNAUTHORIZED_COPY_OR_REDISTRIBUTION")

    if t["overseas_storage"]:
        restricted = t["contains_personal_data"] or t["contains_sensitive_personal_data"]
        if restricted or not t.get("contract_allows_overseas_storage", False):
            return result(BLOCK, "OVERSEAS_STORAGE_NOT_ALLOWED")

    if t["foreign_egress"]:
        foreign_ok = all([
            t["fixed_egress"],
            bool(t.get("egress_country")),
            bool(t.get("egress_provider")),
            t.get("source_allows_foreign_access", False),
        ])
        if not foreign_ok:
            return result(REVIEW, "FOREIGN_EGRESS_REVIEW")

    if t["contains_personal_data"] or t["contains_sensitive_personal_data"]:
        return result(REVIEW, "PERSONAL_DATA_REVIEW")

    if t["source_type"] == "public_html":
        html_ok = all([
            t.get("robots_and_terms_allow", False),
            t["concurrency"] <= 1,
            t["rate_limit_rps"] <= 1 / 3,
            t["incremental_only"],
        ])
        return result(ALLOW if html_ok else REVIEW, "PUBLIC_HTML_LIMITS")

    if t["source_type"] in GOV_OPEN:
        if t["access_method"] in {"official_api", "official_download"}:
            return result(ALLOW, "GOVERNMENT_OPEN_DATA")

    if t["source_type"] in AUTHORIZED_COMMERCIAL:
        commercial_ok = all([
            t.get("explicit_contract_permission", False),
            t.get("contract_allows_current_purpose", False),
            t.get("contract_allows_current_storage", False),
        ])
        return result(ALLOW if commercial_ok else REVIEW, "COMMERCIAL_AUTHORIZATION")

    return result(REVIEW, "DEFAULT_REVIEW")


def self_test() -> None:
    base = {
        "task_id": "test", "source_type": "government_open_api",
        "access_method": "official_api", "authorization_basis": "official open API",
        "purpose": "public statistics", "fields": ["value"],
        "foreign_egress": True, "fixed_egress": True,
        "egress_country": "US", "egress_provider": "Cloudflare",
        "source_allows_foreign_access": True,
        "ip_rotation": False, "proxy_pool": False, "bypass_attempted": False,
        "contains_personal_data": False, "contains_sensitive_personal_data": False,
        "contains_identity_authentication_data": False,
        "contains_secret_or_important_data": False,
        "overseas_storage": False, "storage_location": "controlled",
        "redistribution": False, "full_database_copy": False,
        "concurrency": 1, "rate_limit_rps": 0.2, "incremental_only": True,
    }
    assert evaluate(base)["decision"] == ALLOW
    assert evaluate({**base, "ip_rotation": True})["decision"] == BLOCK
    assert evaluate({**base, "upstream_signal": 403})["decision"] == STOP
    print("PASS")


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        self_test()
        return
    raw = Path(sys.argv[1]).read_text("utf-8") if len(sys.argv) == 2 else sys.stdin.read()
    ticket = json.loads(raw)
    print(json.dumps(evaluate(ticket), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
