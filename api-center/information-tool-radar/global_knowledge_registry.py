#!/usr/bin/env python3
"""Validate and route the global library/literature source registry.

This module is intentionally read-only. It produces a source plan for the
controller; network adapters remain bounded by each source's declared access
mode. Shadow-library entries are discovery/risk metadata only. Their site
domains must never be persisted: every shadow source is resolved transiently
through Wikipedia/Wikidata and discarded after the run.
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

SCHEMA = "global-knowledge-source-registry-v1"
SHADOW_DISCOVERY_PROFILE = "shadow-library-wikimedia-registry-v1"
ALLOWED_MODES = {
    "metadata",
    "metadata-only",
    "metadata-and-open-items",
    "metadata-and-full-view-only",
    "metadata-and-public-domain-items",
    "metadata-and-open-digital-items",
    "metadata-and-rights-labelled-media",
    "metadata-and-oa-location-discovery",
    "metadata-and-provider-declared-pdf-locations",
    "metadata-and-oa-links",
    "metadata-and-oa-fulltext",
    "metadata-and-oa-fulltext-where-declared",
    "metadata-and-preprint-fulltext",
    "metadata-and-open-files",
    "metadata-and-public-files",
    "metadata-and-oa-discovery",
    "metadata-and-fulltext-where-available",
    "metadata-and-authorized-content",
    "fulltext-when-rights-open",
    "fulltext-when-oa",
    "oa-location-discovery",
    "catalog",
    "directory",
}
SHADOW_CATEGORY = "shadow-library"
SHADOW_ALLOWED_ACCESS = {"wikimedia-dynamic-discovery"}
KEY_HINTS = {
    "openalex": "OPENALEX_API_KEY",
    "europeana": "EUROPEANA_API_KEY",
    "dpla": "DPLA_API_KEY",
    "trove": "TROVE_API_KEY",
    "core": "CORE_API_KEY",
    "nasa-ads": "NASA_ADS_API_TOKEN",
}


def load_registry(path: Path) -> Mapping[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise ValueError("registry must be a JSON object")
    return data


def validate_registry(registry: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if registry.get("schema_version") != SCHEMA:
        errors.append(f"schema_version must be {SCHEMA}")
    policy = registry.get("policy")
    if not isinstance(policy, Mapping):
        errors.append("policy missing")
        policy = {}
    required_true = (
        "https_required",
        "read_only",
        "rights_check_required_before_fulltext",
        "provider_declared_fulltext_only",
        "shadow_library_discovery_via_wikimedia_only",
        "shadow_library_runtime_domain_discard_after_run",
    )
    for key in required_true:
        if policy.get(key) is not True:
            errors.append(f"policy.{key} must be true")
    if policy.get("shadow_library_mode") != "metadata-only":
        errors.append("policy.shadow_library_mode must be metadata-only")
    for key in (
        "shadow_library_domains_persisted",
        "shadow_library_detail_pages_allowed",
        "shadow_library_download_links_allowed",
        "shadow_library_file_retrieval_allowed",
        "access_control_bypass_allowed",
        "captcha_bypass_allowed",
        "paywall_bypass_allowed",
    ):
        if policy.get(key) is not False:
            errors.append(f"policy.{key} must be false")

    rows = registry.get("sources")
    if not isinstance(rows, list) or not rows:
        return errors + ["sources must be a non-empty list"]
    seen: set[str] = set()
    for index, raw in enumerate(rows):
        if not isinstance(raw, Mapping):
            errors.append(f"sources[{index}] must be an object")
            continue
        source_id = str(raw.get("id") or "").strip()
        if not source_id:
            errors.append(f"sources[{index}].id missing")
            continue
        if source_id in seen:
            errors.append(f"duplicate source id: {source_id}")
        seen.add(source_id)
        for key in ("name", "category", "region", "access", "mode", "auth", "status", "rights"):
            if not str(raw.get(key) or "").strip():
                errors.append(f"{source_id}.{key} missing")
        if raw.get("mode") not in ALLOWED_MODES:
            errors.append(f"{source_id}.mode unsupported: {raw.get('mode')}")
        endpoint = raw.get("endpoint")
        if endpoint is not None and not str(endpoint).startswith("https://"):
            errors.append(f"{source_id}.endpoint must use https")
        if raw.get("category") == SHADOW_CATEGORY:
            if raw.get("mode") != "metadata-only":
                errors.append(f"{source_id}: shadow source must be metadata-only")
            if raw.get("access") not in SHADOW_ALLOWED_ACCESS:
                errors.append(f"{source_id}: shadow source must use Wikimedia dynamic discovery")
            if raw.get("discovery_profile") != SHADOW_DISCOVERY_PROFILE:
                errors.append(f"{source_id}: shadow discovery_profile must be {SHADOW_DISCOVERY_PROFILE}")
            if endpoint is not None:
                errors.append(f"{source_id}: shadow source endpoint must not be persisted")
            lowered = json.dumps(raw, ensure_ascii=False).casefold()
            for forbidden in ("direct-download", "ipfs://", "magnet:", "/md5/", ".onion"):
                if forbidden in lowered:
                    errors.append(f"{source_id}: forbidden shadow locator material: {forbidden}")
    return errors


def source_available(row: Mapping[str, Any], env: Mapping[str, str]) -> tuple[bool, str]:
    status = str(row.get("status") or "")
    source_id = str(row.get("id") or "")
    if row.get("category") == SHADOW_CATEGORY:
        return True, "wikimedia-metadata-only"
    if "key-required" in status:
        env_name = KEY_HINTS.get(source_id)
        if env_name and env.get(env_name):
            return True, f"key-present:{env_name}"
        return False, f"key-missing:{env_name or 'source-specific-key'}"
    if status == "catalog-only":
        return True, "catalog-only"
    return True, "available"


def plan_sources(
    registry: Mapping[str, Any],
    *,
    categories: set[str] | None = None,
    include_shadow: bool = True,
    available_only: bool = False,
    env: Mapping[str, str] = os.environ,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in registry.get("sources") or []:
        row = dict(raw)
        if categories and row.get("category") not in categories:
            continue
        if not include_shadow and row.get("category") == SHADOW_CATEGORY:
            continue
        available, reason = source_available(row, env)
        is_shadow = row.get("category") == SHADOW_CATEGORY
        row["runtime_available"] = available
        row["runtime_reason"] = reason
        row["network_access_allowed"] = not is_shadow
        row["shadow_site_network_access_allowed"] = False if is_shadow else None
        row["wikimedia_discovery_network_access_allowed"] = True if is_shadow else None
        row["runtime_domain_persisted"] = False if is_shadow else None
        row["fulltext_requires_rights_check"] = row.get("mode") != "metadata-only"
        if available_only and not available:
            continue
        rows.append(row)
    rows.sort(key=lambda x: (str(x.get("category")), str(x.get("name"))))
    return rows


def summarize(registry: Mapping[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    category_counts = Counter(str(row.get("category")) for row in rows)
    return {
        "schema_version": SCHEMA,
        "status": "pass",
        "source_count": len(rows),
        "category_count": len(category_counts),
        "category_counts": dict(sorted(category_counts.items())),
        "runtime_available_count": sum(bool(row.get("runtime_available")) for row in rows),
        "shadow_metadata_source_count": sum(row.get("category") == SHADOW_CATEGORY for row in rows),
        "shadow_network_access_count": sum(
            row.get("category") == SHADOW_CATEGORY and row.get("network_access_allowed") for row in rows
        ),
        "shadow_persisted_domain_count": sum(
            row.get("category") == SHADOW_CATEGORY and bool(row.get("endpoint")) for row in rows
        ),
        "sources": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--category", action="append", default=[])
    parser.add_argument("--exclude-shadow", action="store_true")
    parser.add_argument("--available-only", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--enforce", action="store_true")
    args = parser.parse_args()

    registry = load_registry(args.registry)
    errors = validate_registry(registry)
    if errors:
        report = {"schema_version": SCHEMA, "status": "fail", "errors": errors}
        code = 1
    else:
        rows = plan_sources(
            registry,
            categories=set(args.category) or None,
            include_shadow=not args.exclude_shadow,
            available_only=args.available_only,
        )
        report = summarize(registry, rows)
        code = 0
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(json.dumps({k: report.get(k) for k in (
        "status",
        "source_count",
        "category_count",
        "runtime_available_count",
        "shadow_metadata_source_count",
        "shadow_network_access_count",
        "shadow_persisted_domain_count",
    )}, ensure_ascii=False))
    return code if args.enforce else 0


if __name__ == "__main__":
    raise SystemExit(main())
