#!/usr/bin/env python3
"""Download and extract text from lawfully accessible PDF books.

This module extends the existing lawful-book policy rather than creating a second
unrestricted downloader. Remote PDF retrieval is limited to hosts explicitly
approved in ``lawful-book-sources.json`` through ``pdf_formats`` and requires a
public-domain or open-license attestation. User-provided local PDFs require an
explicit lawful-possession attestation.

The reader never visits Anna's Archive detail pages, never resolves Anna download
links, never bypasses access controls, and never accepts an unknown remote host.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import mimetypes
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import lawful_book_reader as base

try:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError
except ImportError as exc:  # pragma: no cover - exercised by deployment validation
    raise RuntimeError(
        "pypdf is required; install api-center/information-tool-radar/"
        "book-reader-requirements.txt"
    ) from exc

PDF_FORMAT = "pdf"
PDF_MIME_TYPE = "application/pdf"
ACTIVE_ACTION_TYPES = {
    "/JavaScript",
    "/Launch",
    "/SubmitForm",
    "/ImportData",
    "/GoToR",
}
DEFAULT_MAX_PAGES = 2_000
DEFAULT_MAX_BYTES = 25_000_000
DEFAULT_MAX_CHARS = 500_000


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _deref(value: Any) -> Any:
    getter = getattr(value, "get_object", None)
    if callable(getter):
        try:
            return getter()
        except Exception:
            return value
    return value


def _mapping(value: Any) -> Mapping[str, Any]:
    candidate = _deref(value)
    return candidate if isinstance(candidate, Mapping) else {}


def _sequence(value: Any) -> Sequence[Any]:
    candidate = _deref(value)
    if isinstance(candidate, Sequence) and not isinstance(candidate, (str, bytes, bytearray)):
        return candidate
    return ()


def validate_pdf_source_registry(registry: Mapping[str, Any]) -> list[str]:
    """Validate the shared source registry plus PDF-specific declarations."""
    errors = list(base.validate_source_registry(registry))
    policy = registry.get("policy")
    if not isinstance(policy, Mapping):
        return errors

    max_pages = policy.get("maximum_pdf_pages", DEFAULT_MAX_PAGES)
    if not isinstance(max_pages, int) or not 1 <= max_pages <= 5_000:
        errors.append("policy maximum_pdf_pages must be an integer from 1 to 5000")

    pdf_source_count = 0
    for item in registry.get("sources") or []:
        if not isinstance(item, Mapping):
            continue
        pdf_formats = {
            str(value).casefold() for value in item.get("pdf_formats") or []
        }
        if not pdf_formats:
            continue
        pdf_source_count += 1
        if pdf_formats != {PDF_FORMAT}:
            errors.append(
                f"invalid pdf_formats for {item.get('host')}: {sorted(pdf_formats)}"
            )
        host = str(item.get("host") or "").casefold()
        if "anna" in host or "annas-archive" in host:
            errors.append("Anna's Archive may not be a PDF source")
    if pdf_source_count < 1:
        errors.append("at least one explicitly approved PDF source is required")
    return errors


def pdf_source_for_url(
    registry: Mapping[str, Any], url: str
) -> Mapping[str, Any]:
    source = base.source_for_url(registry, url)
    formats = {str(value).casefold() for value in source.get("pdf_formats") or []}
    if PDF_FORMAT not in formats:
        host = urllib.parse.urlparse(url).hostname or "unknown"
        raise ValueError(f"PDF retrieval is not approved for source domain: {host}")
    return source


def infer_pdf_format(name: str, content_type: str = "") -> str:
    path = urllib.parse.urlparse(name).path if "://" in name else name
    suffix = Path(path).suffix.casefold()
    lowered = content_type.casefold().split(";", 1)[0].strip()
    if suffix == ".pdf" or lowered == PDF_MIME_TYPE:
        return PDF_FORMAT
    return ""


def download_pdf(
    registry: Mapping[str, Any],
    url: str,
    rights_basis: str,
    timeout: int,
    max_bytes: int,
) -> tuple[bytes, str, Mapping[str, Any]]:
    source = pdf_source_for_url(registry, url)
    allowed_rights = {str(value) for value in source.get("rights_bases") or []}
    if rights_basis not in allowed_rights:
        raise ValueError(
            f"rights basis {rights_basis} is not approved for this PDF source"
        )

    request = urllib.request.Request(
        url,
        headers={
            "Accept": PDF_MIME_TYPE,
            "Accept-Encoding": "identity",
            "User-Agent": base.USER_AGENT,
        },
        method="GET",
    )
    try:
        with base.build_opener().open(request, timeout=timeout) as response:
            payload = response.read(max_bytes + 1)
            if len(payload) > max_bytes:
                raise RuntimeError(f"PDF exceeds {max_bytes} bytes")
            content_type = response.headers.get("Content-Type", "")
            final_url = response.geturl()
    except urllib.error.HTTPError as exc:
        if int(exc.code) in base.REDIRECT_CODES:
            location = exc.headers.get("Location") if exc.headers else None
            target = urllib.parse.urljoin(url, location or "")
            raise RuntimeError(
                f"redirect blocked; review final PDF URL separately: {target}"
            )
        raise

    if final_url != url:
        raise RuntimeError("unexpected redirect was followed")
    if infer_pdf_format(url, content_type) != PDF_FORMAT:
        raise ValueError(f"remote object is not an unambiguous PDF: {content_type}")
    if not payload.startswith(b"%PDF-"):
        raise ValueError("remote object does not contain a PDF header")
    return payload, content_type, source


def _outline_entries(items: Any, level: int = 1) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []

    def visit(value: Any, depth: int) -> None:
        if len(output) >= 500 or depth > 20:
            return
        if isinstance(value, list):
            for child in value:
                visit(child, min(depth + 1, 20))
            return
        title = getattr(value, "title", "")
        if title:
            normalized = " ".join(str(title).split()).strip()
            if normalized:
                output.append({"level": max(1, depth), "title": normalized[:300]})

    visit(items, level)
    return output[:500]


def inspect_pdf_safety(reader: PdfReader) -> dict[str, Any]:
    """Reject active content and embedded payloads before text extraction."""
    findings: list[str] = []
    root = _mapping(reader.trailer.get("/Root"))
    if "/OpenAction" in root:
        findings.append("document OpenAction is forbidden")
    if "/AA" in root:
        findings.append("document additional actions are forbidden")

    names = _mapping(root.get("/Names"))
    if "/JavaScript" in names:
        findings.append("document JavaScript name tree is forbidden")
    if "/EmbeddedFiles" in names:
        findings.append("embedded files are forbidden")

    acroform = _mapping(root.get("/AcroForm"))
    if "/XFA" in acroform:
        findings.append("XFA forms are forbidden")

    annotations_examined = 0
    for page_number, page in enumerate(reader.pages, start=1):
        page_map = _mapping(page)
        if "/AA" in page_map:
            findings.append(f"page {page_number} additional actions are forbidden")
        for annotation in _sequence(page_map.get("/Annots")):
            annotations_examined += 1
            if annotations_examined > 20_000:
                findings.append("annotation count exceeds safety limit")
                break
            annotation_map = _mapping(annotation)
            action = _mapping(annotation_map.get("/A"))
            action_type = str(action.get("/S") or "")
            if action_type in ACTIVE_ACTION_TYPES:
                findings.append(
                    f"page {page_number} contains forbidden action {action_type}"
                )
        if findings or annotations_examined > 20_000:
            break

    return {
        "active_content_rejected": True,
        "embedded_files_rejected": True,
        "encrypted_pdf_rejected": True,
        "annotations_examined": annotations_examined,
        "findings": findings,
        "passed": not findings,
    }


def _normalize_page_text(value: str) -> str:
    lines = [line.rstrip() for line in value.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return "\n".join(lines).strip()


def parse_pdf(
    payload: bytes,
    max_chars: int,
    max_pages: int = DEFAULT_MAX_PAGES,
) -> dict[str, Any]:
    if not payload.startswith(b"%PDF-"):
        raise ValueError("PDF header missing")
    try:
        reader = PdfReader(io.BytesIO(payload), strict=False)
    except PdfReadError as exc:
        raise ValueError(f"invalid PDF: {exc}") from exc

    if reader.is_encrypted:
        raise ValueError("encrypted PDFs are not supported")
    page_count = len(reader.pages)
    if page_count < 1:
        raise ValueError("PDF contains no pages")
    if page_count > max_pages:
        raise ValueError(f"PDF page count exceeds {max_pages}")

    safety = inspect_pdf_safety(reader)
    if not safety["passed"]:
        raise ValueError("; ".join(safety["findings"][:10]))

    metadata: dict[str, str] = {}
    raw_metadata = reader.metadata
    if raw_metadata:
        for key, value in raw_metadata.items():
            if value is None:
                continue
            normalized_key = str(key).lstrip("/").casefold()[:100]
            normalized_value = " ".join(str(value).split()).strip()
            if normalized_key and normalized_value:
                metadata[normalized_key] = normalized_value[:1_000]

    try:
        toc = _outline_entries(reader.outline)
    except Exception:
        toc = []

    full_parts: list[str] = []
    page_records: list[dict[str, Any]] = []
    total_text_observed = 0
    pages_with_text = 0
    remaining = max_chars
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            extracted = page.extract_text() or ""
        except Exception as exc:
            raise ValueError(f"PDF text extraction failed on page {page_number}: {exc}") from exc
        normalized = _normalize_page_text(extracted)
        if normalized:
            pages_with_text += 1
            total_text_observed += len(normalized)
            if len(page_records) < 200:
                page_records.append(
                    {
                        "page": page_number,
                        "text_excerpt": normalized[:1_000],
                        "characters": len(normalized),
                    }
                )
            if remaining > 0:
                selected = normalized[:remaining]
                full_parts.append(selected)
                remaining -= len(selected)

    content_text = "\n\n".join(full_parts)[:max_chars]
    content_truncated = total_text_observed > len(content_text)
    return {
        "metadata": metadata,
        "toc": toc,
        "chapters": page_records,
        "content_text": content_text,
        "content_chars_extracted": len(content_text),
        "content_chars_observed": total_text_observed,
        "content_truncated": content_truncated,
        "content_complete": not content_truncated,
        "page_count": page_count,
        "pages_with_text": pages_with_text,
        "text_layer_present": pages_with_text > 0,
        "pdf_safety": safety,
    }


def run_pdf_reader(
    registry: Mapping[str, Any],
    *,
    rights_basis: str,
    rights_note: str,
    url: str | None = None,
    file_path: Path | None = None,
    timeout: int = 25,
    max_bytes: int = DEFAULT_MAX_BYTES,
    max_chars: int = DEFAULT_MAX_CHARS,
    max_pages: int = DEFAULT_MAX_PAGES,
    retained_file: Path | None = None,
    require_text: bool = False,
) -> dict[str, Any]:
    policy_errors = validate_pdf_source_registry(registry)
    if rights_basis not in base.RIGHTS_BASES:
        policy_errors.append("invalid rights basis")
    if len(rights_note.strip()) < 8:
        policy_errors.append("rights attestation note is required")
    if bool(url) == bool(file_path):
        policy_errors.append("provide exactly one of URL or local PDF")
    if url and rights_basis not in base.REMOTE_RIGHTS_BASES:
        policy_errors.append("remote PDF retrieval requires public-domain or open-license basis")
    if file_path and rights_basis != "user-provided":
        policy_errors.append("local PDFs require user-provided rights basis")
    if url:
        try:
            pdf_source_for_url(registry, url)
        except ValueError as exc:
            policy_errors.append(str(exc))
    if file_path and infer_pdf_format(
        str(file_path), mimetypes.guess_type(str(file_path))[0] or ""
    ) != PDF_FORMAT:
        policy_errors.append("local file must be a PDF")

    if policy_errors:
        return {
            "schema_version": "lawful-book-reader-report-v1",
            "generated_at": utc_now(),
            "status": "blocked",
            "format": PDF_FORMAT,
            "policy_errors": policy_errors,
            "rights_basis": rights_basis,
            "rights_note": rights_note[:500],
        }

    source_record: Mapping[str, Any] | None = None
    content_type = PDF_MIME_TYPE
    if url:
        payload, content_type, source_record = download_pdf(
            registry, url, rights_basis, timeout, max_bytes
        )
        source = url
    else:
        assert file_path is not None
        payload = file_path.read_bytes()
        if len(payload) > max_bytes:
            raise ValueError(f"PDF exceeds {max_bytes} bytes")
        source = str(file_path)

    parsed = parse_pdf(payload, max_chars=max_chars, max_pages=max_pages)
    if require_text and not parsed["text_layer_present"]:
        raise ValueError("PDF contains no extractable text layer")

    retained = False
    retained_path: str | None = None
    if retained_file is not None:
        retained_file.parent.mkdir(parents=True, exist_ok=True)
        retained_file.write_bytes(payload)
        retained = True
        retained_path = str(retained_file)

    content_text = str(parsed["content_text"])
    return {
        "schema_version": "lawful-book-reader-report-v1",
        "generated_at": utc_now(),
        "status": "pass",
        "rights_basis": rights_basis,
        "rights_note": rights_note[:500],
        "source": source,
        "source_host": (
            urllib.parse.urlparse(url).hostname.casefold()
            if url and urllib.parse.urlparse(url).hostname
            else None
        ),
        "source_policy": dict(source_record) if source_record else {"type": "user-provided"},
        "format": PDF_FORMAT,
        "content_type": content_type,
        "downloaded_bytes": len(payload),
        "source_sha256": hashlib.sha256(payload).hexdigest(),
        "file_retained": retained,
        "retained_path": retained_path,
        "metadata": parsed["metadata"],
        "toc": parsed["toc"],
        "chapters": parsed["chapters"],
        "page_count": parsed["page_count"],
        "pages_with_text": parsed["pages_with_text"],
        "text_layer_present": parsed["text_layer_present"],
        "content_text": content_text,
        "content_chars_extracted": parsed["content_chars_extracted"],
        "content_chars_observed": parsed["content_chars_observed"],
        "content_truncated": parsed["content_truncated"],
        "content_complete": parsed["content_complete"],
        "content_sha256": hashlib.sha256(content_text.encode("utf-8")).hexdigest(),
        "pdf_safety": parsed["pdf_safety"],
        "safety": {
            "approved_source_required_for_remote": True,
            "rights_attestation_required": True,
            "cross_domain_redirects_followed": False,
            "anna_archive_downloads_allowed": False,
            "access_controls_bypassed": False,
            "active_pdf_content_executed": False,
            "supported_format": PDF_FORMAT,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url")
    source.add_argument("--file", type=Path)
    parser.add_argument("--rights-basis", required=True, choices=sorted(base.RIGHTS_BASES))
    parser.add_argument("--rights-note", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--text-output", type=Path)
    parser.add_argument("--retain-file", type=Path)
    parser.add_argument("--timeout", type=int, default=25)
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES)
    parser.add_argument("--require-text", action="store_true")
    parser.add_argument("--enforce", action="store_true")
    args = parser.parse_args()

    try:
        report = run_pdf_reader(
            base.load_json(args.registry),
            rights_basis=args.rights_basis,
            rights_note=args.rights_note,
            url=args.url,
            file_path=args.file,
            timeout=min(max(args.timeout, 5), 60),
            max_bytes=min(max(args.max_bytes, 100_000), 50_000_000),
            max_chars=min(max(args.max_chars, 1_000), 5_000_000),
            max_pages=min(max(args.max_pages, 1), 5_000),
            retained_file=args.retain_file,
            require_text=args.require_text,
        )
    except Exception as exc:
        report = {
            "schema_version": "lawful-book-reader-report-v1",
            "generated_at": utc_now(),
            "status": "fail",
            "format": PDF_FORMAT,
            "rights_basis": args.rights_basis,
            "rights_note": args.rights_note[:500],
            "error": f"{type(exc).__name__}: {str(exc)[:500]}",
        }

    if args.text_output and report.get("status") == "pass":
        args.text_output.parent.mkdir(parents=True, exist_ok=True)
        args.text_output.write_text(str(report.get("content_text") or ""), encoding="utf-8")
        report["text_output"] = str(args.text_output)

    base.save_json(args.output, report)
    print(
        json.dumps(
            {
                "status": report.get("status"),
                "format": report.get("format"),
                "downloaded_bytes": report.get("downloaded_bytes", 0),
                "pages": report.get("page_count", 0),
                "pages_with_text": report.get("pages_with_text", 0),
                "content_chars_extracted": report.get("content_chars_extracted", 0),
                "content_complete": report.get("content_complete", False),
                "file_retained": report.get("file_retained", False),
            },
            ensure_ascii=False,
        )
    )
    if args.enforce and report.get("status") != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
