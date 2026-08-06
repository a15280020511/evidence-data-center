#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import catalog_lawful_resolver as resolver


BASE = Path(__file__).parent
CATALOG_REGISTRY = json.loads(
    (BASE / "catalog-domains.json").read_text(encoding="utf-8")
)
PUBLIC_REGISTRY = json.loads(
    (BASE / "public-book-search-sources.json").read_text(encoding="utf-8")
)
READER_REGISTRY = json.loads(
    (BASE / "lawful-book-sources.json").read_text(encoding="utf-8")
)


def fake_catalog(
    registry: Mapping[str, Any],
    query: str,
    **_: Any,
) -> Mapping[str, Any]:
    assert registry["mode"] == "metadata-only"
    return {
        "status": "pass",
        "resolution_source": "test Wikimedia metadata",
        "selected_domain": "https://annas-archive.example",
        "sample_titles": [
            "Alice's Adventures in Wonderland [EPUB]",
            "Alice's Adventures in Wonderland [EPUB]",
        ],
    }


def fake_catalog_unavailable(
    registry: Mapping[str, Any],
    query: str,
    **_: Any,
) -> Mapping[str, Any]:
    return {
        "status": "unavailable",
        "resolution_source": "test",
        "selected_domain": None,
        "sample_titles": [],
    }


def fake_public(
    registry: Mapping[str, Any],
    *,
    query: str,
    **_: Any,
) -> Mapping[str, Any]:
    assert registry["schema_version"] == "public-book-search-sources-v1"
    return {
        "status": "pass",
        "source_count": 4,
        "successful_source_count": 4,
        "source_side_hard_stop_count": 0,
        "result_count": 3,
        "results": [
            {
                "title": "Alice's Adventures in Wonderland",
                "authors": ["Lewis Carroll"],
                "source_id": "project-gutenberg",
                "source_display_name": "Project Gutenberg",
                "catalog_url": "https://www.gutenberg.org/ebooks/11",
                "available_formats": ["epub", "txt"],
                "readable_locations": [
                    {
                        "format": "epub",
                        "url": "https://www.gutenberg.org/cache/epub/11/pg11.epub",
                        "declared_by": "official-opds",
                    }
                ],
            },
            {
                "title": "Alice in Wonderland",
                "authors": [],
                "source_id": "wikisource-en",
                "source_display_name": "English Wikisource",
                "catalog_url": "https://en.wikisource.org/wiki/Alice_in_Wonderland",
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
                "title": "Unrelated Book",
                "authors": [],
                "source_id": "project-gutenberg",
                "source_display_name": "Project Gutenberg",
                "catalog_url": "https://www.gutenberg.org/ebooks/999",
                "available_formats": ["txt"],
                "readable_locations": [
                    {
                        "format": "txt",
                        "url": "https://annas-archive.example/file.txt",
                        "declared_by": "official-opds",
                    }
                ],
            },
        ],
    }


def fake_reader(
    registry: Mapping[str, Any],
    **kwargs: Any,
) -> Mapping[str, Any]:
    assert registry["schema_version"] == "lawful-book-source-registry-v1"
    assert kwargs["url"].startswith("https://www.gutenberg.org/")
    assert kwargs["rights_basis"] == "public-domain"
    return {
        "status": "pass",
        "source": kwargs["url"],
        "downloaded_bytes": 1234,
        "content_chars_extracted": 5000,
    }


def main() -> int:
    assert resolver.title_similarity(
        "Alice's Adventures in Wonderland [EPUB]",
        "Alice's Adventures in Wonderland",
    ) >= 0.95
    assert resolver.title_similarity("Alice", "Unrelated Book") < 0.62

    report = resolver.resolve_to_lawful_fulltext(
        CATALOG_REGISTRY,
        PUBLIC_REGISTRY,
        READER_REGISTRY,
        query="Alice in Wonderland",
        catalog_search_fn=fake_catalog,
        public_search_fn=fake_public,
        reader_fn=fake_reader,
        public_sleep_fn=lambda _: None,
    )
    assert report["status"] == "pass"
    assert report["catalog_query_fallback_used"] is False
    assert report["match_count"] == 2
    assert report["selected_match"]["source_id"] == "project-gutenberg"
    assert report["selected_match"]["rights_basis"] == "public-domain"
    serialized = json.dumps(report, ensure_ascii=False).casefold()
    assert "annas-archive.example/file" not in serialized
    assert report["safety"]["anna_download_links_followed"] is False

    fallback = resolver.resolve_to_lawful_fulltext(
        CATALOG_REGISTRY,
        PUBLIC_REGISTRY,
        READER_REGISTRY,
        query="Alice in Wonderland",
        catalog_search_fn=fake_catalog_unavailable,
        public_search_fn=fake_public,
        reader_fn=fake_reader,
        public_sleep_fn=lambda _: None,
    )
    assert fallback["status"] == "pass"
    assert fallback["catalog_query_fallback_used"] is True
    assert fallback["catalog_candidate_titles"] == ["alice in wonderland"]

    blocked = resolver.resolve_to_lawful_fulltext(
        CATALOG_REGISTRY,
        PUBLIC_REGISTRY,
        READER_REGISTRY,
        query="Alice in Wonderland",
        read_first=True,
        rights_note="",
        catalog_search_fn=fake_catalog,
        public_search_fn=fake_public,
        reader_fn=fake_reader,
        public_sleep_fn=lambda _: None,
    )
    assert blocked["status"] == "blocked"
    assert any("rights_note" in error for error in blocked["policy_errors"])

    read = resolver.resolve_to_lawful_fulltext(
        CATALOG_REGISTRY,
        PUBLIC_REGISTRY,
        READER_REGISTRY,
        query="Alice in Wonderland",
        read_first=True,
        rights_note="Project Gutenberg provider-declared public-domain edition.",
        catalog_search_fn=fake_catalog,
        public_search_fn=fake_public,
        reader_fn=fake_reader,
        public_sleep_fn=lambda _: None,
    )
    assert read["status"] == "pass"
    assert read["reader"]["status"] == "pass"
    assert read["reader"]["downloaded_bytes"] == 1234

    print(
        json.dumps(
            {
                "title_normalization": "passed",
                "catalog_metadata_bridge": "passed",
                "lawful_match_ranking": "passed",
                "anna_link_rejection": "passed",
                "query_fallback": "passed",
                "rights_attestation_gate": "passed",
                "approved_reader_handoff": "passed",
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
