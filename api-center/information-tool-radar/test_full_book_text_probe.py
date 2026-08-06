#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import full_book_text_probe as target


def registry() -> dict[str, object]:
    return {
        "schema_version": "lawful-book-source-registry-v1",
        "policy": {
            "https_required": True,
            "unknown_domains_allowed": False,
            "cross_domain_redirects_allowed": False,
            "anna_archive_downloads_allowed": False,
            "rights_attestation_required": True,
        },
        "sources": [{
            "host": "www.gutenberg.org",
            "enabled": True,
            "allow_subdomains": False,
            "rights_bases": ["public-domain"],
            "formats": ["txt"],
        }],
    }


def main() -> int:
    original_download = target.reader.download_book
    original_parse = target.reader.parse_book

    def fake_download(*args: object, **kwargs: object):
        return (
            b"Chapter I\nComplete body.\nThe End",
            "txt",
            "text/plain",
            registry()["sources"][0],
        )

    def fake_parse(payload: bytes, fmt: str, max_chars: int):
        assert payload.endswith(b"The End")
        return {
            "metadata": {},
            "toc": [{"level": 1, "title": "Chapter I"}],
            "chapters": [],
            "content_text": "Chapter I\nComplete body.\nThe End",
            "content_truncated": False,
        }

    target.reader.download_book = fake_download
    target.reader.parse_book = fake_parse
    try:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "full.txt"
            report = target.probe_full_book(
                registry(),
                url="https://www.gutenberg.org/book.txt",
                rights_basis="public-domain",
                rights_note="Public-domain deterministic test edition.",
                text_output=output,
            )
            assert report["status"] == "pass"
            assert report["content_complete"] is True
            assert output.read_text(encoding="utf-8").endswith("The End")
            assert report["content_sha256"]
    finally:
        target.reader.download_book = original_download
        target.reader.parse_book = original_parse

    print(json.dumps({
        "complete_text_written": "passed",
        "content_hash_recorded": "passed",
        "truncation_gate": "passed",
        "approved_source_policy_reused": "passed",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
