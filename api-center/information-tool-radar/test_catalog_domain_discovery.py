#!/usr/bin/env python3
from __future__ import annotations

import json

import catalog_domain_discovery as discovery


def registry() -> dict[str, object]:
    return {
        "schema_version": "catalog-domain-registry-v1",
        "mode": "metadata-only",
        "policy": {
            "https_required": True,
            "fail_closed": True,
            "automatic_domain_promotion": False,
            "follow_cross_domain_redirects": False,
            "unknown_domains_allowed": False,
            "minimum_healthy_domains": 1,
        },
        "discovery": {
            "candidate_only": True,
            "automatic_promotion": False,
            "entity_queries": ["Anna's Archive", "安娜的档案"],
            "wikipedia_languages": ["en", "zh"],
            "domain_tokens": ["annas-archive"],
        },
        "domains": [
            {
                "url": "https://annas-archive.gl",
                "enabled": True,
                "approval_status": "approved",
                "priority": 10,
            }
        ],
    }


def main() -> int:
    cfg = discovery.discovery_config(registry())
    assert cfg["candidate_only"] is True
    assert cfg["automatic_promotion"] is False
    assert discovery.normalize_domain("https://Example.org/path") == "https://example.org"

    original_search = discovery.search_wikidata
    original_fetch = discovery.fetch_entities
    original_links = discovery.wikipedia_external_links

    def fake_search(query: str, language: str, timeout: int, max_bytes: int) -> list[str]:
        assert query
        assert language == "en"
        return ["Q123"]

    def fake_fetch(ids: list[str], timeout: int, max_bytes: int) -> dict[str, object]:
        assert ids == ["Q123"]
        return {
            "Q123": {
                "claims": {
                    "P856": [
                        {
                            "mainsnak": {
                                "datavalue": {"value": "https://annas-archive.new/path"}
                            }
                        }
                    ]
                },
                "sitelinks": {
                    "enwiki": {"title": "Anna's Archive"},
                    "zhwiki": {"title": "安娜的档案"},
                },
            }
        }

    def fake_links(language: str, title: str, timeout: int, max_bytes: int) -> list[str]:
        return [
            "https://annas-archive.gl/",
            "https://annas-archive.other/somewhere",
            "https://unrelated.example/",
        ]

    discovery.search_wikidata = fake_search
    discovery.fetch_entities = fake_fetch
    discovery.wikipedia_external_links = fake_links
    try:
        report = discovery.discover(registry())
    finally:
        discovery.search_wikidata = original_search
        discovery.fetch_entities = original_fetch
        discovery.wikipedia_external_links = original_links

    assert report["registry_mutated"] is False
    assert report["automatic_promotion"] is False
    assert report["manual_review_required"] is True
    domains = {row["candidate_domain"]: row for row in report["candidates"]}
    assert domains["https://annas-archive.gl"]["status"] == "already-approved"
    assert domains["https://annas-archive.new"]["status"] == "unapproved-candidate"
    assert domains["https://annas-archive.other"]["status"] == "unapproved-candidate"
    assert "https://unrelated.example" not in domains

    invalid = registry()
    invalid["discovery"] = dict(invalid["discovery"])
    invalid["discovery"]["automatic_promotion"] = True
    try:
        discovery.discovery_config(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("automatic promotion must be rejected")

    print(json.dumps({
        "candidate_only": "passed",
        "wikidata_official_website_candidate": "passed",
        "wikipedia_external_link_candidate": "passed",
        "approved_domain_recognition": "passed",
        "automatic_promotion_rejected": "passed",
        "unrelated_domains_filtered": "passed",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
