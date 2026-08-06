#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import public_book_search as search


REGISTRY = json.loads(
    (Path(__file__).with_name("public-book-search-sources.json")).read_text(encoding="utf-8")
)

GUTENBERG = b'''<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>https://www.gutenberg.org/ebooks/11</id>
    <title>Alice's Adventures in Wonderland</title>
    <author><name>Lewis Carroll</name></author>
    <summary>&lt;p&gt;A classic fantasy.&lt;/p&gt;</summary>
    <link rel="alternate" type="text/html" href="http://www.gutenberg.org/ebooks/11" />
    <link rel="http://opds-spec.org/acquisition" type="application/epub+zip" href="https://www.gutenberg.org/cache/epub/11/pg11.epub" />
    <link rel="http://opds-spec.org/acquisition" type="text/plain" href="https://www.gutenberg.org/cache/epub/11/pg11.txt" />
    <link rel="http://opds-spec.org/acquisition" type="application/pdf" href="https://evil.example/book.pdf" />
  </entry>
</feed>'''

STANDARD = b'''<!doctype html><html><body>
<a href="/ebooks/lewis-carroll/alices-adventures-in-wonderland">Alice's Adventures in Wonderland</a>
<a href="/ebooks/lewis-carroll/alices-adventures-in-wonderland">Alice's Adventures in Wonderland</a>
<a href="/ebooks/lewis-carroll/downloads">Download</a>
</body></html>'''

WIKISOURCE = json.dumps(
    {
        "query": {
            "search": [
                {
                    "pageid": 123,
                    "title": "Alice's Adventures in Wonderland",
                    "wordcount": 27000,
                    "timestamp": "2026-01-01T00:00:00Z",
                    "snippet": "<span class=\"searchmatch\">Alice</span> text",
                }
            ]
        }
    }
).encode("utf-8")


def fake_fetcher(
    source: Mapping[str, Any], query: str, limit: int, timeout: int, max_bytes: int
) -> Mapping[str, Any]:
    payload = {
        "project-gutenberg": GUTENBERG,
        "standard-ebooks": STANDARD,
        "wikisource-en": WIKISOURCE,
        "wikisource-zh": WIKISOURCE,
    }[str(source["source_id"])]
    return {
        "success": True,
        "state": "success",
        "http_status": 200,
        "retry_after": None,
        "attempt_count": 1,
        "source_side_hard_stop": False,
        "duration_ms": 1.0,
        "request_url": search.build_request_url(source, query, limit),
        "content_type": "application/octet-stream",
        "payload": payload,
    }


def main() -> int:
    assert search.validate_registry(REGISTRY) == []

    gutenberg = search.parse_gutenberg_opds(GUTENBERG, 10)
    assert len(gutenberg) == 1
    assert gutenberg[0]["catalog_url"] == "https://www.gutenberg.org/ebooks/11"
    assert gutenberg[0]["available_formats"] == ["epub", "txt"]
    assert all("evil.example" not in item["url"] for item in gutenberg[0]["readable_locations"])

    standard = search.parse_standard_ebooks_html(STANDARD, 10)
    assert len(standard) == 1
    assert standard[0]["authors"] == ["Lewis Carroll"]
    assert standard[0]["catalog_url"].startswith("https://standardebooks.org/ebooks/")

    wiki_source = next(item for item in REGISTRY["sources"] if item["source_id"] == "wikisource-en")
    wiki = search.parse_mediawiki_search(WIKISOURCE, wiki_source, 10)
    assert len(wiki) == 1
    assert wiki[0]["readable_locations"][0]["format"] == "html"
    assert "searchmatch" not in wiki[0]["summary"]

    sleeps: list[float] = []
    report = search.run_search(
        REGISTRY,
        query="Alice in Wonderland",
        limit=5,
        fetcher=fake_fetcher,
        sleep_fn=sleeps.append,
    )
    assert report["status"] == "pass"
    assert report["source_count"] == 4
    assert report["successful_source_count"] == 4
    assert report["result_count"] == 4
    assert sleeps == [10.0, 10.0, 10.0]
    assert all(item["request_count"] == 1 for item in report["sources"])
    assert report["safety"]["automatic_retries_allowed"] is False
    assert report["safety"]["anna_archive_downloads_allowed"] is False

    call_count = 0

    def hard_stop(
        source: Mapping[str, Any], query: str, limit: int, timeout: int, max_bytes: int
    ) -> Mapping[str, Any]:
        nonlocal call_count
        call_count += 1
        return {
            "success": False,
            "state": "source_side_hard_stop",
            "http_status": 429,
            "retry_after": "120",
            "attempt_count": 1,
            "source_side_hard_stop": True,
            "duration_ms": 1.0,
            "request_url": search.build_request_url(source, query, limit),
            "content_type": "",
            "payload": b"",
        }

    stopped = search.run_search(
        REGISTRY,
        query="test",
        selected_sources=["project-gutenberg"],
        fetcher=hard_stop,
        sleep_fn=lambda _: None,
    )
    assert stopped["status"] == "fail"
    assert stopped["source_side_hard_stop_count"] == 1
    assert call_count == 1
    assert stopped["sources"][0]["automatic_retry_count"] == 0

    blocked = search.run_search(
        REGISTRY,
        query="test",
        selected_sources=["annas-archive"],
        fetcher=fake_fetcher,
        sleep_fn=lambda _: None,
    )
    assert blocked["status"] == "blocked"
    assert any("Anna" in error or "unknown" in error for error in blocked["policy_errors"])

    bad = json.loads(json.dumps(REGISTRY))
    bad["sources"].append(
        {
            "source_id": "annas-archive",
            "display_name": "Anna",
            "enabled": True,
            "host": "annas-archive.example",
            "endpoint": "https://annas-archive.example/search",
            "parser": "standard-ebooks-html",
        }
    )
    assert any("Anna" in error for error in search.validate_registry(bad))

    print(
        json.dumps(
            {
                "registry_validation": "passed",
                "gutenberg_opds_parse": "passed",
                "provider_declared_links_only": "passed",
                "standard_ebooks_parse": "passed",
                "wikisource_api_parse": "passed",
                "unified_serial_search": "passed",
                "hard_stop_no_retry": "passed",
                "anna_download_search_rejected": "passed",
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
