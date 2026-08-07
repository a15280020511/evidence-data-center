#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import shadow_library_wikimedia_discovery as mod

HERE = Path(__file__).resolve().parent


def fake_getter(url: str, params: dict[str, str], timeout: int):
    del timeout
    if "wikipedia.org" in url:
        title = params.get("titles", "")
        if title == "Missing":
            return {"query": {"pages": [{"pageprops": {}}]}}
        return {"query": {"pages": [{"pageprops": {"wikibase_item": "Q123"}}]}}
    if "wikidata.org" in url:
        return {
            "entities": {
                "Q123": {
                    "claims": {
                        "P856": [
                            {"mainsnak": {"datavalue": {"value": "https://example.invalid/path"}}},
                            {"mainsnak": {"datavalue": {"value": "http://not-accepted.invalid"}}},
                        ]
                    }
                }
            }
        }
    raise AssertionError(url)


def main() -> int:
    registry = mod.load_registry(HERE / "shadow-library-wikimedia-sources.json")
    assert mod.validate_registry(registry) == []
    assert len(registry["reviewed_seeds"]) >= 15

    synthetic = dict(registry)
    synthetic["reviewed_seeds"] = [
        {
            "id": "fixture",
            "name": "Fixture Shadow Library",
            "wikipedia_titles": ["Fixture"],
            "lifecycle": "fixture",
            "metadata_adapter": "discovery-only",
        }
    ]
    domains = mod.resolve_seed_runtime_domains(
        synthetic,
        synthetic["reviewed_seeds"][0],
        getter=fake_getter,
    )
    assert domains == ["https://example.invalid"]

    report = mod.redacted_report(synthetic, getter=fake_getter)
    rendered = json.dumps(report, ensure_ascii=False)
    assert report["status"] == "pass"
    assert report["resolved_source_count"] == 1
    assert report["sources"][0]["runtime_domain_candidate_count"] == 1
    assert report["sources"][0]["runtime_domains_persisted"] is False
    assert report["safety"]["shadow_domains_exposed_in_report"] is False
    assert "example.invalid" not in rendered
    assert report["safety"]["shadow_download_links_followed"] is False
    assert report["safety"]["shadow_files_retrieved"] is False

    broken = json.loads(json.dumps(registry))
    broken["reviewed_seeds"][0]["homepage"] = "https://fixed-shadow.example"
    errors = mod.validate_registry(broken)
    assert any("persisted locator forbidden" in value for value in errors), errors

    print(json.dumps({
        "wikimedia_only_registry": "passed",
        "reviewed_seed_count": len(registry["reviewed_seeds"]),
        "runtime_domain_redaction": "passed",
        "fixed_domain_rejection": "passed",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
