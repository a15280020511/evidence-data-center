#!/usr/bin/env python3
"""Validate the PRC free-intelligence lifecycle registry and provider contracts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

HERE = Path(__file__).resolve().parent
REGISTRY_PATH = HERE / "prc-tool-registry.json"
CATALOG_PATH = HERE / "provider-catalog.json"
ROOT = HERE.parent
ADMISSION_POLICY_PATH = ROOT / "tool-admission-policy.json"

PRODUCTION_STATES = {"PRODUCTION_SAFE_READONLY", "PROVISIONAL_SAFE_READONLY"}
FORBIDDEN_TEXT = (
    "captcha_solving_allowed\": true",
    "proxy_rotation_allowed\": true",
    "automatic_paid_overage\": true",
    "arbitrary_urls_allowed\": true",
)
EXPECTED_ACTIVE = {
    "china-check-mcp": "china-check",
    "sinofacts-dataset": "sinofacts",
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(message: str) -> None:
    raise SystemExit(message)


def main() -> int:
    registry = load(REGISTRY_PATH)
    catalog = load(CATALOG_PATH)
    policy = load(ADMISSION_POLICY_PATH)
    if not isinstance(registry, Mapping) or not isinstance(catalog, Mapping):
        fail("registry/catalog must be JSON objects")

    allowed_states = set(policy.get("allowed_states") or [])
    declared_states = set(registry.get("allowed_statuses") or [])
    if declared_states != allowed_states:
        fail(f"registry allowed_statuses drift: {sorted(declared_states ^ allowed_states)}")

    rows = registry.get("tools")
    providers = catalog.get("providers")
    if not isinstance(rows, list) or not isinstance(providers, list):
        fail("registry tools and catalog providers must be arrays")

    ids: set[str] = set()
    active_registry: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            fail("tool registry row must be an object")
        tool_id = str(row.get("id") or "")
        if not tool_id or tool_id in ids:
            fail(f"invalid or duplicate tool id: {tool_id}")
        ids.add(tool_id)
        status = str(row.get("status") or "")
        if status not in allowed_states:
            fail(f"{tool_id}: invalid lifecycle status {status}")
        production = bool(row.get("production_enabled"))
        if production:
            active_registry.add(tool_id)
            if status not in PRODUCTION_STATES:
                fail(f"{tool_id}: production tool must use a production state")
            if bool(row.get("key_required")):
                fail(f"{tool_id}: production tool must not require a key")
            if bool(row.get("automatic_paid_overage")):
                fail(f"{tool_id}: automatic paid overage is forbidden")
            license_name = str(row.get("license") or "").upper()
            if not license_name or "UNDECLARED" in license_name or "UNKNOWN" in license_name:
                fail(f"{tool_id}: production license scope is not explicit")
            free_mode = str(row.get("free_mode") or "").casefold()
            if "paid" in free_mode or "commercial_data_only" in free_mode:
                fail(f"{tool_id}: production free_mode is not free: {free_mode}")

    if active_registry != set(EXPECTED_ACTIVE):
        fail(f"unexpected production tool set: {sorted(active_registry)}")

    enabled_provider_ids = {
        str(row.get("provider_id"))
        for row in providers
        if isinstance(row, Mapping) and bool(row.get("enabled"))
    }
    expected_provider_ids = set(EXPECTED_ACTIVE.values())
    if enabled_provider_ids != expected_provider_ids:
        fail(
            "enabled provider set differs from approved production registry: "
            f"providers={sorted(enabled_provider_ids)} expected={sorted(expected_provider_ids)}"
        )

    serialized = json.dumps(catalog, ensure_ascii=False, sort_keys=True).casefold()
    for forbidden in FORBIDDEN_TEXT:
        if forbidden.casefold() in serialized:
            fail(f"provider catalog enables forbidden capability: {forbidden}")

    for provider in providers:
        if not isinstance(provider, Mapping):
            fail("provider row must be object")
        if provider.get("required_secret_environment_variable"):
            fail(f"{provider.get('provider_id')}: no-key suite must not require a Secret")
        limits = provider.get("limits") if isinstance(provider.get("limits"), Mapping) else {}
        if limits.get("automatic_paid_overage") is not False:
            fail(f"{provider.get('provider_id')}: automatic_paid_overage must be false")
        for key in (
            "arbitrary_urls_allowed",
            "proxy_rotation_allowed",
            "captcha_solving_allowed",
            "cross_provider_retry_after_denial",
        ):
            if limits.get(key) is True:
                fail(f"{provider.get('provider_id')}: forbidden {key}=true")

    rejected_must_stay_off = {
        "opensanctions",
        "mediacrawler",
        "drissionpage",
        "pywencai",
        "public-proxy-pools",
    }
    by_id = {str(row.get("id")): row for row in rows if isinstance(row, Mapping)}
    for tool_id in rejected_must_stay_off:
        row = by_id.get(tool_id)
        if not row or bool(row.get("production_enabled")) or row.get("status") != "REJECTED":
            fail(f"{tool_id}: rejected tool unexpectedly admitted")

    law = by_id.get("lawrefbook-laws")
    if not law or law.get("status") != "QUARANTINED" or bool(law.get("production_enabled")):
        fail("lawrefbook-laws must remain quarantined until license scope is explicit")

    print(
        json.dumps(
            {
                "status": "PASS",
                "production_tools": sorted(active_registry),
                "enabled_providers": sorted(enabled_provider_ids),
                "external_secrets_required": 0,
                "automatic_paid_overage": False,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
