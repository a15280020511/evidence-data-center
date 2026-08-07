#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import global_open_library_discovery as mod

HERE = Path(__file__).resolve().parent


def main() -> int:
    registry = mod.load_registry(HERE / "global-open-library-discovery-sources.json")
    errors = mod.validate_registry(registry)
    assert errors == [], errors
    report = mod.summarize(registry)
    assert report["status"] == "pass"
    assert report["discovery_source_count"] >= 15
    ids = {row["id"] for row in report["sources"]}
    assert {"ifla-library-map", "ifla-national-libraries", "openalex-institutions", "opendoar", "openaire", "wikidata-libraries"}.issubset(ids)
    assert report["governance"]["automatic_child_endpoint_promotion"] is False
    assert report["governance"]["child_verification_required"] is True
    assert report["governance"]["rights_check_required_before_fulltext"] is True

    malicious = json.loads(json.dumps(registry))
    malicious["policy"]["automatic_child_endpoint_promotion"] = True
    assert any("automatic_child_endpoint_promotion" in value for value in mod.validate_registry(malicious))

    print(json.dumps({
        "open_library_discovery_registry": "passed",
        "discovery_source_count": report["discovery_source_count"],
        "global_scope_count": report["global_scope_count"],
        "child_promotion_gate": "passed",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
