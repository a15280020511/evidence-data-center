#!/usr/bin/env python3
from __future__ import annotations

import json

import public_book_search as engine
import public_book_search_cli as cli


GUTENBERG_NAVIGATION_AND_BOOKS = b'''<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>https://www.gutenberg.org/ebooks/subjects</id>
    <title>Subjects</title>
    <link rel="subsection" type="application/atom+xml" href="https://www.gutenberg.org/ebooks/subjects.opds" />
  </entry>
  <entry>
    <id>https://www.gutenberg.org/ebooks/search-entry</id>
    <title>Alice's Adventures in Wonderland</title>
    <author><name>Lewis Carroll</name></author>
    <link rel="alternate" type="application/atom+xml" href="https://www.gutenberg.org/ebooks/11.opds" />
    <link rel="http://opds-spec.org/acquisition" type="application/epub+zip" href="https://www.gutenberg.org/cache/epub/11/pg11.epub" />
    <link rel="http://opds-spec.org/acquisition" type="text/plain" href="https://www.gutenberg.org/cache/epub/11/pg11.txt" />
    <link rel="http://opds-spec.org/acquisition" type="application/pdf" href="https://evil.example/book.pdf" />
  </entry>
  <entry>
    <id>ebook:11</id>
    <title>Duplicate Alice</title>
  </entry>
</feed>'''


def main() -> int:
    results = cli.parse_gutenberg_opds(GUTENBERG_NAVIGATION_AND_BOOKS, 10)
    assert len(results) == 1, results
    item = results[0]
    assert item["provider_record_id"] == "11", item
    assert item["title"] == "Alice's Adventures in Wonderland", item
    assert item["catalog_url"] == "https://www.gutenberg.org/ebooks/11", item
    assert item["available_formats"] == ["epub", "txt"], item
    assert all("evil.example" not in x["url"] for x in item["readable_locations"])
    assert all(x["title"] != "Subjects" for x in results)

    cli.install_quality_filter()
    assert engine.parse_gutenberg_opds is cli.parse_gutenberg_opds

    print(
        json.dumps(
            {
                "gutenberg_navigation_filtered": "passed",
                "numeric_ebook_id_required": "passed",
                "duplicate_ebook_id_removed": "passed",
                "canonical_catalog_url": "passed",
                "provider_declared_locations_only": "passed",
                "production_filter_installed": "passed",
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
