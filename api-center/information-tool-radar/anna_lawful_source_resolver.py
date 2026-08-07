#!/usr/bin/env python3
"""Resolve Anna-visible bibliographic metadata to approved lawful book sources.

This module does not open Anna's Archive detail pages, download links, mirrors,
or external file hosts. It accepts bibliographic facts such as title and author,
searches the existing fixed public-book providers, ranks likely matching works,
and exposes only locations accepted by the existing lawful-book source registry.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import unicodedata
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import lawful_book_reader as lawful_reader
import public_book_search as search_engine
import public_book_search_cli as search_quality

SUPPORTED_READER_FORMATS = {"epub", "html", "xhtml", "txt", "pdf"}
URL_RE = re.compile(r"https?://", re.I)


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


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = re.sub(r"[^\w\s]", " ", normalized, flags=re.UNICODE)
    return " ".join(normalized.split())


def token_set(value: str) -> set[str]:
    return {token for token in normalize_text(value).split() if len(token) > 1}


def text_similarity(left: str, right: str) -> float:
    left_norm = normalize_text(left)
    right_norm = normalize_text(right)
    if not left_norm or not right_norm:
        return 0.0
    sequence = difflib.SequenceMatcher(None, left_norm, right_norm).ratio()
    left_tokens = token_set(left_norm)
    right_tokens = token_set(right_norm)
    union = left_tokens | right_tokens
    jaccard = len(left_tokens & right_tokens) / len(union) if union else 0.0
    containment = (
        len(left_tokens & right_tokens) / min(len(left_tokens), len(right_tokens))
        if left_tokens and right_tokens
        else 0.0
    )
    return max(0.0, min(1.0, sequence * 0.45 + jaccard * 0.35 + containment * 0.20))


def validate_metadata(title: str, author: str, isbn: str) -> list[str]:
    errors: list[str] = []
    normalized_title = " ".join(title.split()).strip()
    normalized_author = " ".join(author.split()).strip()
    normalized_isbn = re.sub(r"[^0-9Xx]", "", isbn)
    if not normalized_title:
        errors.append("title is required")
    if len(normalized_title) > 500:
        errors.append("title exceeds 500 characters")
    if len(normalized_author) > 300:
        errors.append("author exceeds 300 characters")
    if URL_RE.search(title) or URL_RE.search(author) or URL_RE.search(isbn):
        errors.append("URLs are not accepted; provide bibliographic metadata only")
    combined = f"{title} {author} {isbn}".casefold()
    if "annas-archive" in combined or "annasarchive" in combined:
        errors.append("Anna detail or download references are not accepted")
    if isbn and len(normalized_isbn) not in {10, 13}:
        errors.append("ISBN must contain 10 or 13 ISBN characters")
    return errors


def candidate_authors(item: Mapping[str, Any]) -> str:
    authors = item.get("authors") or []
    if isinstance(authors, Sequence) and not isinstance(authors, (str, bytes, bytearray)):
        return " ".join(str(value) for value in authors if value)
    return str(authors or "")


def candidate_score(
    *,
    requested_title: str,
    requested_author: str,
    item: Mapping[str, Any],
) -> tuple[float, dict[str, float]]:
    title_score = text_similarity(requested_title, str(item.get("title") or ""))
    author_score = (
        text_similarity(requested_author, candidate_authors(item))
        if requested_author
        else 0.0
    )
    if requested_author:
        score = title_score * 0.82 + author_score * 0.18
    else:
        score = title_score
    if title_score < 0.30:
        score *= 0.55
    return round(max(0.0, min(1.0, score)), 6), {
        "title": round(title_score, 6),
        "author": round(author_score, 6),
    }


def approved_reader_locations(
    item: Mapping[str, Any],
    reader_registry: Mapping[str, Any],
) -> list[dict[str, Any]]:
    approved: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for raw in item.get("readable_locations") or []:
        if not isinstance(raw, Mapping):
            continue
        fmt = str(raw.get("format") or "").casefold()
        url = str(raw.get("url") or "")
        if fmt not in SUPPORTED_READER_FORMATS or not url:
            continue
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname:
            continue
        try:
            source = lawful_reader.source_for_url(reader_registry, url)
        except ValueError:
            continue
        allowed_formats = {
            str(value).casefold() for value in source.get("formats") or []
        }
        allowed_formats.update(
            str(value).casefold() for value in source.get("pdf_formats") or []
        )
        if fmt not in allowed_formats:
            continue
        key = (fmt, url)
        if key in seen:
            continue
        seen.add(key)
        approved.append(
            {
                "format": fmt,
                "url": url,
                "declared_by": str(raw.get("declared_by") or ""),
                "approved_host": parsed.hostname.casefold(),
                "approval_basis": source.get("approval_basis"),
            }
        )
    return approved


def resolve_metadata(
    search_registry: Mapping[str, Any],
    reader_registry: Mapping[str, Any],
    *,
    title: str,
    author: str = "",
    isbn: str = "",
    limit_per_source: int = 10,
    match_threshold: float = 0.55,
    timeout: int = 25,
    max_bytes: int = 5_000_000,
    search_fn: Callable[..., Mapping[str, Any]] = search_engine.run_search,
) -> dict[str, Any]:
    errors = validate_metadata(title, author, isbn)
    errors.extend(search_engine.validate_registry(search_registry))
    errors.extend(lawful_reader.validate_source_registry(reader_registry))
    if not 1 <= limit_per_source <= 20:
        errors.append("limit_per_source must be 1..20")
    if not 0.0 <= match_threshold <= 1.0:
        errors.append("match_threshold must be between 0 and 1")
    normalized_title = " ".join(title.split()).strip()
    normalized_author = " ".join(author.split()).strip()
    normalized_isbn = re.sub(r"[^0-9Xx]", "", isbn).upper()
    if errors:
        return {
            "schema_version": "anna-lawful-source-resolution-v1",
            "generated_at": utc_now(),
            "status": "blocked",
            "resolution_state": "policy_blocked",
            "metadata": {
                "title": normalized_title,
                "author": normalized_author,
                "isbn": normalized_isbn,
            },
            "policy_errors": sorted(set(errors)),
            "candidates": [],
            "safety": safety_snapshot(),
        }

    search_quality.install_quality_filter()
    query = " ".join(value for value in [normalized_title, normalized_author] if value)
    search_report = dict(
        search_fn(
            search_registry,
            query=query,
            limit=limit_per_source,
            timeout=timeout,
            max_bytes=max_bytes,
        )
    )
    ranked: list[dict[str, Any]] = []
    for raw in search_report.get("results") or []:
        if not isinstance(raw, Mapping):
            continue
        score, components = candidate_score(
            requested_title=normalized_title,
            requested_author=normalized_author,
            item=raw,
        )
        if score < match_threshold:
            continue
        locations = approved_reader_locations(raw, reader_registry)
        ranked.append(
            {
                "match_score": score,
                "score_components": components,
                "title": raw.get("title"),
                "authors": raw.get("authors") or [],
                "source_id": raw.get("source_id"),
                "source_display_name": raw.get("source_display_name"),
                "provider_record_id": raw.get("provider_record_id"),
                "catalog_url": raw.get("catalog_url"),
                "rights_basis": raw.get("rights_basis") or raw.get("source_rights_basis"),
                "available_formats": raw.get("available_formats") or [],
                "reader_ready_locations": locations,
                "reader_ready": bool(locations),
            }
        )
    ranked.sort(
        key=lambda item: (
            -float(item["match_score"]),
            not bool(item["reader_ready"]),
            str(item.get("source_id") or ""),
            str(item.get("title") or ""),
        )
    )
    reader_ready_count = sum(bool(item["reader_ready"]) for item in ranked)
    state = "matched-reader-ready" if reader_ready_count else "matched-catalog-only"
    if not ranked:
        state = "no-lawful-match"
    return {
        "schema_version": "anna-lawful-source-resolution-v1",
        "generated_at": utc_now(),
        "status": "pass" if search_report.get("status") == "pass" else "degraded",
        "resolution_state": state,
        "metadata": {
            "title": normalized_title,
            "author": normalized_author,
            "isbn": normalized_isbn,
        },
        "query": query,
        "match_threshold": match_threshold,
        "candidate_count": len(ranked),
        "reader_ready_count": reader_ready_count,
        "candidates": ranked[:20],
        "search_summary": {
            "status": search_report.get("status"),
            "source_count": search_report.get("source_count", 0),
            "successful_source_count": search_report.get("successful_source_count", 0),
            "failed_source_count": search_report.get("failed_source_count", 0),
            "source_side_hard_stop_count": search_report.get(
                "source_side_hard_stop_count", 0
            ),
            "raw_result_count": search_report.get("result_count", 0),
        },
        "policy_errors": [],
        "safety": safety_snapshot(),
    }


def safety_snapshot() -> dict[str, Any]:
    return {
        "anna_catalog_metadata_may_be_used_as_query_input": True,
        "anna_detail_pages_visited": False,
        "anna_download_urls_consumed": False,
        "anna_mirror_or_external_file_hosts_visited": False,
        "access_controls_bypassed": False,
        "automatic_retries_after_401_403_429": False,
        "approved_reader_registry_required": True,
        "catalog_match_treated_as_download_authorization": False,
        "result_requires_public_domain_open_license_or_user_authorization": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--search-registry", type=Path, required=True)
    parser.add_argument("--reader-registry", type=Path, required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--author", default="")
    parser.add_argument("--isbn", default="")
    parser.add_argument("--limit-per-source", type=int, default=10)
    parser.add_argument("--match-threshold", type=float, default=0.55)
    parser.add_argument("--timeout", type=int, default=25)
    parser.add_argument("--max-bytes", type=int, default=5_000_000)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--enforce", action="store_true")
    args = parser.parse_args()
    report = resolve_metadata(
        load_json(args.search_registry),
        load_json(args.reader_registry),
        title=args.title,
        author=args.author,
        isbn=args.isbn,
        limit_per_source=args.limit_per_source,
        match_threshold=args.match_threshold,
        timeout=min(max(args.timeout, 5), 60),
        max_bytes=min(max(args.max_bytes, 100_000), 10_000_000),
    )
    save_json(args.output, report)
    print(
        json.dumps(
            {
                "status": report.get("status"),
                "resolution_state": report.get("resolution_state"),
                "candidate_count": report.get("candidate_count", 0),
                "reader_ready_count": report.get("reader_ready_count", 0),
                "anna_download_urls_consumed": report.get("safety", {}).get(
                    "anna_download_urls_consumed"
                ),
            },
            ensure_ascii=False,
        )
    )
    if args.enforce and report.get("status") not in {"pass", "degraded"}:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
