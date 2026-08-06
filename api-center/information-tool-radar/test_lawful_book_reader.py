#!/usr/bin/env python3
from __future__ import annotations

import io
import json
import tempfile
import zipfile
from pathlib import Path

import lawful_book_reader as reader


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
        "sources": [
            {
                "host": "www.gutenberg.org",
                "enabled": True,
                "allow_subdomains": False,
                "rights_bases": ["public-domain"],
                "formats": ["epub", "html", "xhtml", "txt"],
            }
        ],
    }


def sample_epub() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("mimetype", "application/epub+zip")
        archive.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>
            <container xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
              <rootfiles>
                <rootfile full-path="OEBPS/content.opf"
                  media-type="application/oebps-package+xml"/>
              </rootfiles>
            </container>""",
        )
        archive.writestr(
            "OEBPS/content.opf",
            """<?xml version="1.0"?>
            <package xmlns="http://www.idpf.org/2007/opf" version="3.0">
              <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
                <dc:title>Test Strategy Book</dc:title>
                <dc:creator>Example Author</dc:creator>
                <dc:language>en</dc:language>
              </metadata>
              <manifest>
                <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
                <item id="c1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
                <item id="c2" href="chapter2.xhtml" media-type="application/xhtml+xml"/>
              </manifest>
              <spine>
                <itemref idref="c1"/>
                <itemref idref="c2"/>
              </spine>
            </package>""",
        )
        archive.writestr(
            "OEBPS/nav.xhtml",
            """<html xmlns="http://www.w3.org/1999/xhtml">
            <body><nav><ol><li><a href="chapter1.xhtml">First Move</a></li>
            <li><a href="chapter2.xhtml">Second Move</a></li></ol></nav></body></html>""",
        )
        archive.writestr(
            "OEBPS/chapter1.xhtml",
            "<html><body><h1>First Move</h1><p>Know the terrain.</p></body></html>",
        )
        archive.writestr(
            "OEBPS/chapter2.xhtml",
            "<html><body><h1>Second Move</h1><p>Preserve optionality.</p></body></html>",
        )
    return buffer.getvalue()


def main() -> int:
    assert reader.validate_source_registry(registry()) == []
    approved = reader.source_for_url(
        registry(), "https://www.gutenberg.org/cache/epub/1/pg1.txt"
    )
    assert approved["host"] == "www.gutenberg.org"

    for blocked in (
        "https://annas-archive.gl/md5/example",
        "https://unknown.example/book.epub",
    ):
        try:
            reader.source_for_url(registry(), blocked)
        except ValueError:
            pass
        else:
            raise AssertionError(f"unapproved source should be rejected: {blocked}")

    html_result = reader.parse_book(
        b"<html><body><h1>Part One</h1><p>Visible body.</p><script>hidden</script></body></html>",
        "html",
        1000,
    )
    assert html_result["toc"][0]["title"] == "Part One"
    assert "Visible body." in html_result["content_text"]
    assert "hidden" not in html_result["content_text"]

    txt_result = reader.parse_book(
        "第一章 形势\n正文内容\n第二章 谋攻\n更多正文".encode("utf-8"),
        "txt",
        1000,
    )
    assert len(txt_result["toc"]) == 2

    epub_result = reader.parse_book(sample_epub(), "epub", 5000)
    assert epub_result["metadata"]["title"] == "Test Strategy Book"
    assert [item["title"] for item in epub_result["toc"]] == ["First Move", "Second Move"]
    assert "Know the terrain." in epub_result["content_text"]
    assert "Preserve optionality." in epub_result["content_text"]

    bad_buffer = io.BytesIO()
    with zipfile.ZipFile(bad_buffer, "w") as archive:
        archive.writestr("../escape.xhtml", "bad")
    try:
        reader.safe_zip_members(zipfile.ZipFile(io.BytesIO(bad_buffer.getvalue())))
    except ValueError:
        pass
    else:
        raise AssertionError("unsafe EPUB path must be rejected")

    with tempfile.TemporaryDirectory() as tmp:
        local = Path(tmp) / "book.txt"
        local.write_text("Chapter I\nBody text.", encoding="utf-8")
        report = reader.run_reader(
            registry(),
            rights_basis="user-provided",
            rights_note="User confirms lawful possession and processing rights.",
            file_path=local,
            max_chars=1000,
        )
        assert report["status"] == "pass"
        assert report["format"] == "txt"

    blocked_report = reader.run_reader(
        registry(),
        rights_basis="public-domain",
        rights_note="Public-domain source.",
        url="https://annas-archive.gl/book.epub",
    )
    assert blocked_report["status"] == "blocked"

    print(json.dumps({
        "approved_public_domain_source": "passed",
        "anna_archive_download_rejected": "passed",
        "unknown_domain_rejected": "passed",
        "html_toc_and_body": "passed",
        "text_toc_and_body": "passed",
        "epub_toc_and_body": "passed",
        "unsafe_epub_rejected": "passed",
        "user_provided_file": "passed",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
