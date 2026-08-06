#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import global_knowledge_registry as registry_mod

HERE = Path(__file__).resolve().parent
REGISTRY_PATH = HERE / "global-knowledge-sources.json"


def main() -> int:
    registry = registry_mod.load_registry(REGISTRY_PATH)
    errors = registry_mod.validate_registry(registry)
    assert errors == [], errors

    rows = registry_mod.plan_sources(registry, env={})
    report = registry_mod.summarize(registry, rows)
    assert report["source_count"] >= 50, report["source_count"]
    assert report["category_count"] >= 12, report["category_count"]
    assert report["shadow_metadata_source_count"] >= 7
    assert report["shadow_network_access_count"] == 0

    shadow = [row for row in rows if row["category"] == "shadow-library"]
    assert shadow
    assert all(row["mode"] == "metadata-only" for row in shadow)
    assert all(row["endpoint"] is None for row in shadow)
    assert all(row["network_access_allowed"] is False for row in shadow)

    openalex = next(row for row in rows if row["id"] == "openalex")
    assert openalex["runtime_available"] is False
    assert openalex["runtime_reason"] == "key-missing:OPENALEX_API_KEY"
    keyed = registry_mod.plan_sources(registry, env={"OPENALEX_API_KEY": "test"})
    openalex_keyed = next(row for row in keyed if row["id"] == "openalex")
    assert openalex_keyed["runtime_available"] is True

    malicious = json.loads(json.dumps(registry))
    bad = next(row for row in malicious["sources"] if row["id"] == "library-genesis")
    bad["endpoint"] = "https://example.invalid/download"
    bad["mode"] = "fulltext-when-rights-open"
    bad_errors = registry_mod.validate_registry(malicious)
    assert any("shadow source must be metadata-only" in item for item in bad_errors)
    assert any("shadow source endpoint must not be persisted" in item for item in bad_errors)

    without_shadow = registry_mod.plan_sources(registry, include_shadow=False, env={})
    assert all(row["category"] != "shadow-library" for row in without_shadow)

    print(json.dumps({
        "registry_validation": "passed",
        "source_count": report["source_count"],
        "category_count": report["category_count"],
        "shadow_metadata_source_count": report["shadow_metadata_source_count"],
        "shadow_network_access_count": report["shadow_network_access_count"],
        "key_gate": "passed",
        "shadow_isolation": "passed"
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
