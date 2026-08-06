#!/usr/bin/env python3
"""Download and fully extract one approved public-domain/open-license text.

This probe reuses the lawful-book reader's source and archive protections. It
writes the complete normalized text to a separate file, records hashes and
counts, and fails when the downloaded document was truncated during parsing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import lawful_book_reader as reader


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def probe_full_book(
    registry: Mapping[str, Any],
    *,
    url: str,
    rights_basis: str,
    rights_note: str,
    text_output: Path,
    timeout: int = 30,
    max_bytes: int = 50_000_000,
    max_chars: int = 5_000_000,
) -> dict[str, Any]:
    errors = reader.validate_source_registry(registry)
    if rights_basis not in reader.REMOTE_RIGHTS_BASES:
        errors.append("remote full-book probe requires public-domain or open-license basis")
    if len(rights_note.strip()) < 8:
        errors.append("rights note is required")
    if errors:
        return {
            "schema_version": "full-book-text-probe-v1",
            "generated_at": utc_now(),
            "status": "blocked",
            "policy_errors": errors,
        }

    payload, fmt, content_type, source_record = reader.download_book(
        registry,
        url,
        rights_basis,
        timeout,
        max_bytes,
    )
    parsed = reader.parse_book(payload, fmt, max_chars)
    full_text = str(parsed.get("content_text") or "")
    content_complete = parsed.get("content_truncated") is False
    text_output.parent.mkdir(parents=True, exist_ok=True)
    text_output.write_text(full_text, encoding="utf-8")
    text_bytes = full_text.encode("utf-8")

    status = "pass" if content_complete and bool(full_text) else "incomplete"
    return {
        "schema_version": "full-book-text-probe-v1",
        "generated_at": utc_now(),
        "status": status,
        "rights_basis": rights_basis,
        "rights_note": rights_note[:500],
        "source": url,
        "source_policy": dict(source_record),
        "format": fmt,
        "content_type": content_type,
        "downloaded_bytes": len(payload),
        "source_sha256": sha256_bytes(payload),
        "metadata": parsed.get("metadata", {}),
        "toc": parsed.get("toc", []),
        "toc_entries": len(parsed.get("toc") or []),
        "chapter_records": len(parsed.get("chapters") or []),
        "content_chars": len(full_text),
        "content_utf8_bytes": len(text_bytes),
        "content_sha256": sha256_bytes(text_bytes),
        "content_complete": content_complete,
        "content_truncated": parsed.get("content_truncated"),
        "full_text_file": str(text_output),
        "safety": {
            "approved_source_required": True,
            "rights_attestation_required": True,
            "cross_domain_redirects_followed": False,
            "anna_archive_used": False,
            "access_controls_bypassed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--rights-basis", required=True, choices=sorted(reader.REMOTE_RIGHTS_BASES))
    parser.add_argument("--rights-note", required=True)
    parser.add_argument("--text-output", type=Path, required=True)
    parser.add_argument("--report-output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--max-bytes", type=int, default=50_000_000)
    parser.add_argument("--max-chars", type=int, default=5_000_000)
    parser.add_argument("--enforce", action="store_true")
    args = parser.parse_args()
    try:
        report = probe_full_book(
            load_json(args.registry),
            url=args.url,
            rights_basis=args.rights_basis,
            rights_note=args.rights_note,
            text_output=args.text_output,
            timeout=min(max(args.timeout, 5), 60),
            max_bytes=min(max(args.max_bytes, 100_000), 50_000_000),
            max_chars=min(max(args.max_chars, 10_000), 10_000_000),
        )
    except Exception as exc:
        report = {
            "schema_version": "full-book-text-probe-v1",
            "generated_at": utc_now(),
            "status": "fail",
            "error": f"{type(exc).__name__}: {str(exc)[:500]}",
        }
    save_json(args.report_output, report)
    print(json.dumps({
        "status": report.get("status"),
        "format": report.get("format"),
        "downloaded_bytes": report.get("downloaded_bytes", 0),
        "toc_entries": report.get("toc_entries", 0),
        "content_chars": report.get("content_chars", 0),
        "content_complete": report.get("content_complete", False),
        "content_sha256": report.get("content_sha256"),
    }, ensure_ascii=False))
    if args.enforce and report.get("status") != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
