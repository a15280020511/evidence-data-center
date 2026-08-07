#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import anna_lawful_source_resolver as resolver

ROOT = Path(__file__).resolve().parent
SEARCH_REGISTRY = json.loads(
    (ROOT / "public-book-search-sources.json").read_text(encoding="utf-8")
)
READER_REGISTRY = json.loads(
    (ROOT / "lawful-book-sources.json").read_text(encoding="utf-8")
)


def fake_search(
    registry: Mapping[str, Any],
    *,
    query: str,
    limit: int,
    timeout: int,
    max_bytes: int,
) -> Mapping[str, Any]:
    del registry, query, limit, timeout, max_bytes
    return {
        "status": "pass",
        "source_count": 4,
        "successful_source_count": 4,
        "failed_source_count": 0,
        "source_side_hard_stop_count": 0,
        "result_count": 4,
        "results": [
            {
                "title": "Alice's Adventures in Wonderland",
                "authors": ["Lewis Carroll"],
                "source_id": "project-gutenberg",
                "source_display_name": "Project Gutenberg",
                "provider_record_id": "11",
                "catalog_url": "https://www.gutenberg.org/ebooks/11",
                "rights_basis": "public-domain-us",
                "available_formats": ["txt", "epub"],
                "readable_locations": [
                    {
                        "format": "txt",
                        "url": "https://www.gutenberg.org/cache/epub/11/pg11.txt",
                        "declared_by": "official-opds",
                    },
                    {
                        "format": "epub",
                        "url": "https://www.gutenberg.org/ebooks/11.epub3.images",
                        "declared_by": "official-opds",
                    },
                ],
            },
            {
                "title": "Alice in Wonderland",
                "authors": [],
                "source_id": "wikisource-en",
                "source_display_name": "English Wikisource",
                "catalog_url": "https://en.wikisource.org/wiki/Alice_in_Wonderland",
                "rights_basis": "item-rights-and-cc-by-sa",
                "available_formats": ["html"],
                "readable_locations": [
                    {
                        "format": "html",
                        "url": "https://en.wikisource.org/wiki/Alice_in_Wonderland",
                        "declared_by": "mediawiki-page",
                    }
                ],
            },
            {
                "title": "Alice in Wonderland",
                "authors": ["Lewis Carroll"],
                "source_id": "unknown-source",
                "source_display_name": "Unknown",
                "catalog_url": "https://example.invalid/book",
                "rights_basis": "unknown",
                "available_formats": ["pdf"],
                "readable_locations": [
                    {
                        "format": "pdf",
                        "url": "https://example.invalid/book.pdf",
                        "declared_by": "untrusted",
                    }
                ],
            },
            {
                "title": "A Completely Different Book",
                "authors": ["Someone Else"],
                "source_id": "project-gutenberg",
                "source_display_name": "Project Gutenberg",
                "catalog_url": "https://www.gutenberg.org/ebooks/999",
                "rights_basis": "public-domain-us",
                "available_formats": ["txt"],
                "readable_locations": [
                    {
                        "format": "txt",
                        "url": "https://www.gutenberg.org/files/999/999-0.txt",
                        "declared_by": "official-opds",
                    }
                ],
            },
        ],
    }


def test_normalization_and_similarity() -> None:
    assert resolver.normalize_text("  Alice’s  Adventures! ") == "alice s adventures"
    close = resolver.text_similarity(
        "Alice in Wonderland", "Alice's Adventures in Wonderland"
    )
    far = resolver.text_similarity(
        "Alice in Wonderland", "A Completely Different Book"
    )
    assert close > far
    assert close > 0.55


def test_url_and_anna_references_blocked() -> None:
    report = resolver.resolve_metadata(
        SEARCH_REGISTRY,
        READER_REGISTRY,
        title="https://annas-archive.example/book/123",
        search_fn=fake_search,
    )
    assert report["status"] == "blocked", report
    assert report["resolution_state"] == "policy_blocked", report
    assert any("URLs are not accepted" in item for item in report["policy_errors"])
    assert report["safety"]["anna_download_urls_consumed"] is False


def test_reader_ready_matching_and_unknown_host_filter() -> None:
    report = resolver.resolve_metadata(
        SEARCH_REGISTRY,
        READER_REGISTRY,
        title="Alice in Wonderland",
        author="Lewis Carroll",
        match_threshold=0.50,
        search_fn=fake_search,
    )
    assert report["status"] == "pass", report
    assert report["resolution_state"] == "matched-reader-ready", report
    assert report["candidate_count"] >= 2, report
    assert report["reader_ready_count"] >= 2, report
    first = report["candidates"][0]
    assert first["match_score"] >= 0.50, first
    assert first["reader_ready"] is True, first
    assert first["reader_ready_locations"], first
    for candidate in report["candidates"]:
        if candidate["source_id"] == "unknown-source":
            assert candidate["reader_ready"] is False, candidate
            assert candidate["reader_ready_locations"] == [], candidate
    assert report["safety"]["anna_detail_pages_visited"] is False
    assert report["safety"]["anna_mirror_or_external_file_hosts_visited"] is False


def test_no_match_is_reported_without_unsafe_fallback() -> None:
    report = resolver.resolve_metadata(
        SEARCH_REGISTRY,
        READER_REGISTRY,
        title="Nonexistent Quantum Treatise 987654",
        author="No Such Author",
        match_threshold=0.95,
        search_fn=fake_search,
    )
    assert report["status"] == "pass", report
    assert report["resolution_state"] == "no-lawful-match", report
    assert report["candidate_count"] == 0, report
    assert report["reader_ready_count"] == 0, report
    assert report["safety"]["access_controls_bypassed"] is False


def main() -> int:
    tests = [
        test_normalization_and_similarity,
        test_url_and_anna_references_blocked,
        test_reader_ready_matching_and_unknown_host_filter,
        test_no_match_is_reported_without_unsafe_fallback,
    ]
    results: dict[str, str] = {}
    for test in tests:
        test()
        results[test.__name__] = "passed"
    print(json.dumps(results, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
