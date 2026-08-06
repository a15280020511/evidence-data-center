#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import catalog_web_search as target

HERE = Path(__file__).resolve().parent


def base_registry() -> dict[str, object]:
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
        "domains": [
            {
                "url": "https://primary.example",
                "priority": 10,
                "enabled": True,
                "approval_status": "approved",
            },
            {
                "url": "https://fallback.example",
                "priority": 20,
                "enabled": True,
                "approval_status": "approved",
            },
        ],
    }


def main() -> int:
    production_registry = json.loads(
        (HERE / "catalog-domains.json").read_text(encoding="utf-8")
    )
    assert target.validate_registry(production_registry) == []
    forbidden_text = "\n".join(
        str(value) for value in production_registry["forbidden_operations"]
    ).casefold()
    for phrase in (
        "install or execute third-party wrapper packages",
        "follow detail or download links",
        "follow redirects to unapproved domains",
        "automatically approve a newly discovered domain",
    ):
        assert phrase in forbidden_text

    parser = target.SearchResultParser()
    parser.feed(
        '<a href="/md5/abc"><span>孙子兵法</span></a>'
        '<a href="/download/secret">must not capture</a>'
    )
    assert parser.titles == ["孙子兵法"]

    invalid = base_registry()
    invalid["policy"]["automatic_domain_promotion"] = True
    assert target.validate_registry(invalid)

    invalid_http = base_registry()
    invalid_http["domains"][0]["url"] = "http://primary.example"
    assert target.validate_registry(invalid_http)

    original_probe = target.probe_domain

    def fake_probe(
        domain: str,
        query: str,
        timeout: int,
        max_bytes: int,
        max_titles: int,
        retries: int,
    ) -> dict[str, object]:
        if domain == "https://primary.example":
            return {
                "domain": domain,
                "status": "unavailable",
                "http_status": None,
                "result_count_observed": 0,
                "sample_titles": [],
                "attempts": [],
                "redirect_candidate": None,
            }
        return {
            "domain": domain,
            "status": "healthy",
            "http_status": 200,
            "result_count_observed": 3,
            "sample_titles": ["孙子兵法", "三十六计"],
            "attempts": [],
            "redirect_candidate": None,
        }

    target.probe_domain = fake_probe
    try:
        report = target.search_catalog(base_registry(), "谋略")
    finally:
        target.probe_domain = original_probe
    assert report["status"] == "degraded"
    assert report["selected_domain"] == "https://fallback.example"
    assert report["safety"]["third_party_packages_installed"] is False
    assert report["safety"]["detail_pages_followed"] is False
    assert report["safety"]["book_files_retrieved"] is False

    def all_failed(
        domain: str,
        query: str,
        timeout: int,
        max_bytes: int,
        max_titles: int,
        retries: int,
    ) -> dict[str, object]:
        return {
            "domain": domain,
            "status": "unavailable",
            "http_status": None,
            "result_count_observed": 0,
            "sample_titles": [],
            "attempts": [],
            "redirect_candidate": None,
        }

    target.probe_domain = all_failed
    try:
        report = target.search_catalog(base_registry(), "战略")
    finally:
        target.probe_domain = original_probe
    assert report["status"] == "unavailable"
    assert report["selected_domain"] is None
    assert report["manual_review_required"] is True

    candidate = target.redirect_candidate(
        "https://primary.example",
        "https://new-domain.example/search?q=x",
    )
    assert candidate == {
        "source_domain": "https://primary.example",
        "candidate_domain": "https://new-domain.example",
        "status": "unapproved-not-followed",
    }

    print(json.dumps({
        "registry_policy": "passed",
        "metadata_only_parser": "passed",
        "approved_domain_failover": "passed",
        "all_domains_fail_closed": "passed",
        "redirect_candidate_not_followed": "passed",
        "third_party_package_absence": "passed",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
