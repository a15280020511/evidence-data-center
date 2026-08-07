#!/usr/bin/env python3
"""Validate and plan the global open-library discovery backbone.

This layer does not claim to enumerate every library statically. It keeps a
small set of high-coverage parent directories/aggregators that can discover
national libraries, university repositories and open digital collections.
Discovered child endpoints require separate verification before production use.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

SCHEMA = "global-open-library-discovery-v1"


def load_registry(path: Path) -> Mapping[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise ValueError("registry must be an object")
    return data


def validate_registry(registry: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if registry.get("schema_version") != SCHEMA:
        errors.append(f"schema_version must be {SCHEMA}")
    policy = registry.get("policy")
    if not isinstance(policy, Mapping):
        return errors + ["policy missing"]
    for key in ("read_only", "https_required", "rights_check_required_before_fulltext", "provider_declared_fulltext_only", "credentials_must_not_be_submitted_during_discovery"):
        if policy.get(key) is not True:
            errors.append(f"policy.{key} must be true")
    for key in ("automatic_child_endpoint_promotion", "billing_activation_allowed"):
        if policy.get(key) is not False:
            errors.append(f"policy.{key} must be false")
    rows = registry.get("discovery_sources")
    if not isinstance(rows, list) or not rows:
        return errors + ["discovery_sources must be non-empty"]
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            errors.append(f"discovery_sources[{index}] invalid")
            continue
        source_id = str(row.get("id") or "")
        if not source_id:
            errors.append(f"discovery_sources[{index}].id missing")
            continue
        if source_id in seen:
            errors.append(f"duplicate id: {source_id}")
        seen.add(source_id)
        for key in ("name", "scope", "endpoint", "auth", "mode"):
            if not str(row.get(key) or "").strip():
                errors.append(f"{source_id}.{key} missing")
        if not str(row.get("endpoint") or "").startswith("https://"):
            errors.append(f"{source_id}.endpoint must be https")
    return errors


def summarize(registry: Mapping[str, Any]) -> dict[str, Any]:
    errors = validate_registry(registry)
    if errors:
        return {"schema_version": SCHEMA, "status": "fail", "errors": errors}
    rows = list(registry["discovery_sources"])
    modes = Counter(str(row.get("mode")) for row in rows)
    return {
        "schema_version": SCHEMA,
        "status": "pass",
        "discovery_source_count": len(rows),
        "mode_counts": dict(sorted(modes.items())),
        "global_scope_count": sum("global" in str(row.get("scope")) for row in rows),
        "sources": rows,
        "governance": {
            "automatic_child_endpoint_promotion": False,
            "child_verification_required": True,
            "rights_check_required_before_fulltext": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--enforce", action="store_true")
    args = parser.parse_args()
    report = summarize(load_registry(args.registry))
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(json.dumps({
        "status": report.get("status"),
        "discovery_source_count": report.get("discovery_source_count", 0),
        "global_scope_count": report.get("global_scope_count", 0),
    }, ensure_ascii=False))
    if args.enforce and report.get("status") != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
