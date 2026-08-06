#!/usr/bin/env python3
from __future__ import annotations

import io
import json
import tempfile
from pathlib import Path

from pypdf import PdfWriter

import lawful_pdf_reader as reader


def registry() -> dict[str, object]:
    return {
        "schema_version": "lawful-book-source-registry-v1",
        "policy": {
            "https_required": True,
            "unknown_domains_allowed": False,
            "cross_domain_redirects_allowed": False,
            "anna_archive_downloads_allowed": False,
            "rights_attestation_required": True,
            "maximum_pdf_pages": 2000,
        },
        "sources": [
            {
                "host": "www.gutenberg.org",
                "enabled": True,
                "allow_subdomains": False,
                "rights_bases": ["public-domain"],
                "formats": ["epub", "html", "xhtml", "txt"],
            },
            {
                "host": "upload.wikimedia.org",
                "enabled": True,
                "allow_subdomains": False,
                "rights_bases": ["public-domain", "open-license"],
                "formats": ["epub", "html", "xhtml", "txt"],
                "pdf_formats": ["pdf"],
            },
        ],
    }


def _pdf_object(number: int, body: bytes) -> bytes:
    return f"{number} 0 obj\n".encode("ascii") + body + b"\nendobj\n"


def sample_pdf(*, active_content: bool = False) -> bytes:
    stream = b"BT /F1 12 Tf 72 720 Td (Public domain PDF body text.) Tj ET"
    catalog = b"<< /Type /Catalog /Pages 2 0 R"
    if active_content:
        catalog += b" /OpenAction 7 0 R"
    catalog += b" >>"
    objects = [
        _pdf_object(1, catalog),
        _pdf_object(2, b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>"),
        _pdf_object(
            3,
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        ),
        _pdf_object(
            4,
            f"<< /Length {len(stream)} >>\nstream\n".encode("ascii")
            + stream
            + b"\nendstream",
        ),
        _pdf_object(5, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"),
        _pdf_object(6, b"<< /Title (Unit Test Public Domain Book) /Author (Test Author) >>"),
    ]
    if active_content:
        objects.append(
            _pdf_object(7, b"<< /S /JavaScript /JS (app.alert\\(1\\)) >>")
        )

    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for item in objects:
        offsets.append(len(output))
        output.extend(item)
    xref_offset = len(output)
    size = len(objects) + 1
    output.extend(f"xref\n0 {size}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        (
            f"trailer\n<< /Size {size} /Root 1 0 R /Info 6 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(output)


def encrypted_pdf() -> bytes:
    output = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.encrypt("secret")
    writer.write(output)
    return output.getvalue()


def main() -> int:
    assert reader.validate_pdf_source_registry(registry()) == []
    approved = reader.pdf_source_for_url(
        registry(),
        "https://upload.wikimedia.org/wikipedia/commons/1/12/example.pdf",
    )
    assert approved["host"] == "upload.wikimedia.org"

    for blocked in (
        "https://annas-archive.gl/md5/example.pdf",
        "https://www.gutenberg.org/files/example.pdf",
        "https://unknown.example/book.pdf",
    ):
        try:
            reader.pdf_source_for_url(registry(), blocked)
        except ValueError:
            pass
        else:
            raise AssertionError(f"unapproved PDF source should be rejected: {blocked}")

    assert reader.infer_pdf_format("book.pdf", "") == "pdf"
    assert reader.infer_pdf_format("download", "application/pdf") == "pdf"
    assert reader.infer_pdf_format("book.epub", "application/epub+zip") == ""

    parsed = reader.parse_pdf(sample_pdf(), max_chars=10_000)
    assert parsed["page_count"] == 1
    assert parsed["pages_with_text"] == 1
    assert parsed["text_layer_present"] is True
    assert parsed["content_complete"] is True
    assert parsed["content_truncated"] is False
    assert "Public domain PDF body text." in parsed["content_text"]
    assert parsed["metadata"]["title"] == "Unit Test Public Domain Book"

    truncated = reader.parse_pdf(sample_pdf(), max_chars=10)
    assert truncated["content_truncated"] is True
    assert truncated["content_complete"] is False

    for unsafe_payload in (sample_pdf(active_content=True), encrypted_pdf()):
        try:
            reader.parse_pdf(unsafe_payload, max_chars=10_000)
        except ValueError:
            pass
        else:
            raise AssertionError("unsafe PDF must be rejected")

    with tempfile.TemporaryDirectory() as tmp:
        local = Path(tmp) / "book.pdf"
        local.write_bytes(sample_pdf())
        report = reader.run_pdf_reader(
            registry(),
            rights_basis="user-provided",
            rights_note="User confirms lawful possession and PDF processing rights.",
            file_path=local,
            max_chars=10_000,
            require_text=True,
        )
        assert report["status"] == "pass"
        assert report["format"] == "pdf"
        assert report["content_complete"] is True
        assert report["source_sha256"]
        assert report["content_sha256"]
        assert report["safety"]["anna_archive_downloads_allowed"] is False

    blocked_report = reader.run_pdf_reader(
        registry(),
        rights_basis="public-domain",
        rights_note="Public-domain PDF source.",
        url="https://annas-archive.gl/book.pdf",
    )
    assert blocked_report["status"] == "blocked"

    print(
        json.dumps(
            {
                "approved_public_domain_pdf_source": "passed",
                "anna_pdf_download_rejected": "passed",
                "unknown_pdf_domain_rejected": "passed",
                "pdf_text_extraction": "passed",
                "pdf_metadata_extraction": "passed",
                "pdf_truncation_gate": "passed",
                "active_content_rejected": "passed",
                "encrypted_pdf_rejected": "passed",
                "user_provided_pdf": "passed",
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
