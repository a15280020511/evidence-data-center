#!/usr/bin/env python3
from __future__ import annotations

import json

import catalog_runtime_search as target


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
            "entity_queries": ["Anna's Archive"],
            "wikipedia_languages": ["en"],
            "domain_tokens": ["annas-archive"],
        },
        "domains": [],
    }


def discovery_report() -> dict[str, object]:
    return {
        "status": "pass",
        "source_errors": [],
        "candidates": [
            {
                "candidate_domain": "https://annas-archive.first",
                "candidate_kind": "root-domain",
                "source_score": 8,
                "sources": [{"type": "wikidata-P856"}],
            },
            {
                "candidate_domain": "https://annas-archive.second",
                "candidate_kind": "root-domain",
                "source_score": 5,
                "sources": [{"type": "wikipedia-external-link"}],
            },
            {
                "candidate_domain": "https://software.annas-archive.first",
                "candidate_kind": "related-subdomain",
                "source_score": 99,
                "sources": [{"type": "wikipedia-external-link"}],
            },
        ],
    }


def main() -> int:
    assert target.validate_runtime_registry(registry()) == []
    invalid = registry()
    invalid["domains"] = [{"url": "https://annas-archive.saved"}]
    assert "Anna domains must not be persisted" in target.validate_runtime_registry(invalid)

    original_discover = target.domain_discovery.discover
    original_probe = target.web_probe.probe_domain
    calls: list[str] = []

    def fake_discover(*args: object, **kwargs: object) -> dict[str, object]:
        return discovery_report()

    def fake_probe(domain: str, *args: object, **kwargs: object) -> dict[str, object]:
        calls.append(domain)
        if domain.endswith(".first"):
            return {
                "domain": domain,
                "status": "unavailable",
                "result_count_observed": 0,
                "sample_titles": [],
            }
        return {
            "domain": domain,
            "status": "healthy",
            "result_count_observed": 2,
            "sample_titles": ["孙子兵法", "三十六计"],
        }

    target.domain_discovery.discover = fake_discover
    target.web_probe.probe_domain = fake_probe
    try:
        report = target.search_catalog_runtime(registry(), "谋略")
    finally:
        target.domain_discovery.discover = original_discover
        target.web_probe.probe_domain = original_probe

    assert report["status"] == "pass"
    assert report["selected_domain"] == "https://annas-archive.second"
    assert report["stored_domain_count"] == 0
    assert report["domain_persisted"] is False
    assert calls == ["https://annas-archive.first", "https://annas-archive.second"]
    assert report["safety"]["book_files_retrieved_from_anna"] is False

    target.domain_discovery.discover = fake_discover
    target.web_probe.probe_domain = lambda domain, *a, **k: {
        "domain": domain,
        "status": "unavailable",
        "result_count_observed": 0,
        "sample_titles": [],
    }
    try:
        failed = target.search_catalog_runtime(registry(), "战略")
    finally:
        target.domain_discovery.discover = original_discover
        target.web_probe.probe_domain = original_probe
    assert failed["status"] == "unavailable"
    assert failed["selected_domain"] is None

    print(json.dumps({
        "no_persisted_domains": "passed",
        "live_wikimedia_resolution": "passed",
        "transient_candidate_contract_probe": "passed",
        "runtime_candidate_discard": "passed",
        "fail_closed": "passed",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
