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
            "no_persisted_domains": True,
            "resolve_from_wikimedia_each_run": True,
            "automatic_domain_promotion": False,
            "follow_cross_domain_redirects": False,
            "unknown_domains_allowed": False,
            "minimum_source_score": 3,
            "maximum_runtime_candidates": 8,
        },
        "discovery": {
            "candidate_only": True,
            "automatic_promotion": False,
            "entity_queries": ["Anna's Archive", "安娜的档案"],
            "wikipedia_languages": ["en", "zh"],
            "domain_tokens": ["annas-archive"],
        },
        "domains": [],
    }


def main() -> int:
    cfg = discovery.discovery_config(registry())
    assert cfg["candidate_only"] is True
    assert cfg["automatic_promotion"] is False
    assert discovery.approved_domain_set(registry()) == set()

    original_search = discovery.search_wikidata
    original_fetch = discovery.fetch_entities
    original_links = discovery.wikipedia_external_links

    discovery.search_wikidata = lambda *args, **kwargs: ["Q123"]
    discovery.fetch_entities = lambda *args, **kwargs: {
        "Q123": {
            "claims": {"P856": [{"mainsnak": {"datavalue": {"value": "https://annas-archive.new/"}}}]},
            "sitelinks": {
                "enwiki": {"title": "Anna's Archive"},
                "zhwiki": {"title": "安娜的档案"},
            },
        }
    }
    discovery.wikipedia_external_links = lambda *args, **kwargs: [
        "https://annas-archive.other/",
        "https://software.annas-archive.new/project",
        "https://unrelated.example/",
    ]
    try:
        report = discovery.discover(registry())
    finally:
        discovery.search_wikidata = original_search
        discovery.fetch_entities = original_fetch
        discovery.wikipedia_external_links = original_links

    assert report["registry_mutated"] is False
    assert report["approved_domains"] == []
    domains = {row["candidate_domain"]: row for row in report["candidates"]}
    assert domains["https://annas-archive.new"]["status"] == "unapproved-candidate"
    assert domains["https://annas-archive.other"]["candidate_kind"] == "root-domain"
    assert domains["https://software.annas-archive.new"]["candidate_kind"] == "related-subdomain"
    assert "https://unrelated.example" not in domains

    print(json.dumps({
        "wikimedia_candidate_discovery": "passed",
        "zero_approved_domains": "passed",
        "no_registry_mutation": "passed",
        "root_domain_filter": "passed",
        "unrelated_domain_filter": "passed",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
