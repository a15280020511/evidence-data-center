#!/usr/bin/env python3
"""Resolve Anna's Archive metadata into lawful, provider-declared full-text locations.

Anna's Archive is used only as a volatile catalog clue source. This module never
opens Anna detail pages, follows Anna download links, or retrieves book files
from Anna. Candidate titles are searched against the existing approved public-
book providers. An optional reader step may retrieve only an approved public-
domain/open-license location through ``lawful_book_reader``.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import catalog_runtime_search
import lawful_book_reader
import public_book_search


CatalogSearchFn = Callable[..., Mapping[str, Any]]
PublicSearchFn = Callable[..., Mapping[str, Any]]
ReaderFn = Callable[..., Mapping[str, Any]]

ANNA_MARKERS = ("anna", "annas-archive")
SUPPORTED_READ_FORMATS = {"epub", "html", "xhtml", "txt"}
RIGHTS_BY_SOURCE = {
    "project-gutenberg": "public-domain",
    "standard-ebooks": "open-license",
    "wikisource-en": "open-license",
    "wikisource-zh": "open-license",
}


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


def normalized_text(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"\b(?:pdf|epub|mobi|azw3?|djvu|fb2|txt|html?)\b", " ", text)
    text = re.sub(r"\[[^\]]{0,120}\]", " ", text)
    text = re.sub(r"\([^)]{0,120}\)$", " ", text)
    text = re.sub(r"[_/|·•—–:;,+]+", " ", text)
    text = re.sub(r"[^\w\u3400-\u9fff]+", " ", text, flags=re.UNICODE)
    return " ".join(text.split()).strip()


def title_similarity(left: str, right: str) -> float:
    a = normalized_text(left)
    b = normalized_text(right)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    ratio = SequenceMatcher(None, a, b).ratio()
    tokens_a = set(a.split())
    tokens_b = set(b.split())
    token_score = (
        len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
        if tokens_a and tokens_b
        else 0.0
    )
    containment = 1.0 if a in b or b in a else 0.0
    return round(max(ratio, token_score, containment * 0.95), 6)


def clean_catalog_title(value: str) -> str:
    text = " ".join(value.split()).strip()
    cleaned = normalized_text(text)
    return cleaned[:300] if cleaned else text[:300]


def unique_titles(values: Sequence[str], maximum: int) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = clean_catalog_title(str(value))
        key = normalized_text(cleaned)
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(cleaned)
        if len(output) >= maximum:
            break
    return output


def safe_readable_locations(item: Mapping[str, Any]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for raw in item.get("readable_locations") or []:
        if not isinstance(raw, Mapping):
            continue
        url = str(raw.get("url") or "")
        fmt = str(raw.get("format") or "").casefold()
        declared_by = str(raw.get("declared_by") or "")
        if not url.startswith("https://") or fmt not in SUPPORTED_READ_FORMATS:
            continue
        lowered = url.casefold()
        if any(marker in lowered for marker in ANNA_MARKERS):
            continue
        if declared_by not in {"official-opds", "mediawiki-page"}:
            continue
        output.append({"format": fmt, "url": url, "declared_by": declared_by})
    return output


def rank_matches(
    catalog_title: str,
    public_report: Mapping[str, Any],
    *,
    minimum_similarity: float,
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for raw in public_report.get("results") or []:
        if not isinstance(raw, Mapping):
            continue
        title = str(raw.get("title") or "")
        score = title_similarity(catalog_title, title)
        locations = safe_readable_locations(raw)
        if score < minimum_similarity or not locations:
            continue
        source_id = str(raw.get("source_id") or "")
        rights_basis = RIGHTS_BY_SOURCE.get(source_id)
        if not rights_basis:
            continue
        matches.append(
            {
                "catalog_title": catalog_title,
                "matched_title": title,
                "authors": list(raw.get("authors") or []),
                "source_id": source_id,
                "source_display_name": raw.get("source_display_name"),
                "similarity": score,
                "rights_basis": rights_basis,
                "catalog_url": raw.get("catalog_url"),
                "readable_locations": locations,
                "available_formats": list(raw.get("available_formats") or []),
            }
        )
    matches.sort(
        key=lambda item: (
            -float(item["similarity"]),
            item["source_id"],
            item["matched_title"],
        )
    )
    return matches


def _blocked_report(query: str, errors: Sequence[str]) -> dict[str, Any]:
    return {
        "schema_version": "catalog-lawful-resolver-report-v1",
        "generated_at": utc_now(),
        "status": "blocked",
        "query": query,
        "policy_errors": list(errors),
        "matches": [],
        "selected_match": None,
        "reader": None,
        "safety": {
            "anna_metadata_only": True,
            "anna_detail_pages_followed": False,
            "anna_download_links_followed": False,
            "book_files_retrieved_from_anna": False,
            "lawful_provider_locations_only": True,
            "access_controls_bypassed": False,
        },
    }


def resolve_to_lawful_fulltext(
    catalog_registry: Mapping[str, Any],
    public_registry: Mapping[str, Any],
    reader_registry: Mapping[str, Any],
    *,
    query: str,
    maximum_catalog_titles: int = 3,
    results_per_source: int = 5,
    minimum_similarity: float = 0.62,
    timeout: int = 25,
    max_bytes: int = 5_000_000,
    read_first: bool = False,
    rights_note: str = "",
    reader_max_bytes: int = 25_000_000,
    reader_max_chars: int = 150_000,
    catalog_search_fn: CatalogSearchFn = catalog_runtime_search.search_catalog_runtime,
    public_search_fn: PublicSearchFn = public_book_search.run_search,
    reader_fn: ReaderFn = lawful_book_reader.run_reader,
    public_sleep_fn: Callable[[float], None] | None = None,
) -> dict[str, Any]:
    normalized_query = " ".join(query.split()).strip()
    errors: list[str] = []
    if not normalized_query:
        errors.append("query is required")
    if len(normalized_query) > 300:
        errors.append("query exceeds 300 characters")
    if not 1 <= maximum_catalog_titles <= 10:
        errors.append("maximum_catalog_titles must be 1..10")
    if not 1 <= results_per_source <= 20:
        errors.append("results_per_source must be 1..20")
    if not 0.0 <= minimum_similarity <= 1.0:
        errors.append("minimum_similarity must be 0..1")
    if read_first and len(rights_note.strip()) < 8:
        errors.append("read_first requires an explicit rights_note")
    if catalog_runtime_search.validate_runtime_registry(catalog_registry):
        errors.append("catalog registry failed validation")
    if public_book_search.validate_registry(public_registry):
        errors.append("public-book registry failed validation")
    if lawful_book_reader.validate_source_registry(reader_registry):
        errors.append("lawful-reader registry failed validation")
    if errors:
        return _blocked_report(normalized_query, errors)

    catalog_report = dict(
        catalog_search_fn(
            catalog_registry,
            normalized_query,
            timeout=min(max(timeout, 5), 30),
            max_bytes=min(max(max_bytes, 100_000), 3_000_000),
            max_titles=maximum_catalog_titles,
            retries=1,
        )
    )
    raw_titles = [
        str(value)
        for value in (catalog_report.get("sample_titles") or [])
        if str(value).strip()
    ]
    catalog_titles = unique_titles(raw_titles, maximum_catalog_titles)
    fallback_used = False
    if not catalog_titles:
        catalog_titles = [clean_catalog_title(normalized_query)]
        fallback_used = True

    lawful_searches: list[dict[str, Any]] = []
    matches: list[dict[str, Any]] = []
    for title in catalog_titles:
        kwargs: dict[str, Any] = {
            "query": title,
            "limit": results_per_source,
            "timeout": min(max(timeout, 5), 60),
            "max_bytes": min(max(max_bytes, 100_000), 10_000_000),
        }
        if public_sleep_fn is not None:
            kwargs["sleep_fn"] = public_sleep_fn
        public_report = dict(public_search_fn(public_registry, **kwargs))
        ranked = rank_matches(
            title,
            public_report,
            minimum_similarity=minimum_similarity,
        )
        lawful_searches.append(
            {
                "catalog_title": title,
                "status": public_report.get("status"),
                "source_count": public_report.get("source_count", 0),
                "successful_source_count": public_report.get(
                    "successful_source_count", 0
                ),
                "result_count": public_report.get("result_count", 0),
                "match_count": len(ranked),
                "source_side_hard_stop_count": public_report.get(
                    "source_side_hard_stop_count", 0
                ),
            }
        )
        matches.extend(ranked)

    deduplicated: list[dict[str, Any]] = []
    seen_locations: set[str] = set()
    for match in sorted(
        matches,
        key=lambda item: (
            -float(item["similarity"]),
            item["source_id"],
            item["matched_title"],
        ),
    ):
        fresh_locations = [
            location
            for location in match["readable_locations"]
            if location["url"] not in seen_locations
        ]
        if not fresh_locations:
            continue
        for location in fresh_locations:
            seen_locations.add(location["url"])
        row = dict(match)
        row["readable_locations"] = fresh_locations
        deduplicated.append(row)

    selected_match = deduplicated[0] if deduplicated else None
    reader_report: Mapping[str, Any] | None = None
    if read_first and selected_match:
        location = selected_match["readable_locations"][0]
        reader_report = reader_fn(
            reader_registry,
            rights_basis=str(selected_match["rights_basis"]),
            rights_note=rights_note,
            url=str(location["url"]),
            timeout=min(max(timeout, 5), 60),
            max_bytes=min(max(reader_max_bytes, 100_000), 50_000_000),
            max_chars=min(max(reader_max_chars, 1_000), 500_000),
        )

    if deduplicated:
        status = "pass"
    elif catalog_report.get("status") == "pass":
        status = "no-lawful-match"
    else:
        status = "catalog-unavailable-no-lawful-match"

    return {
        "schema_version": "catalog-lawful-resolver-report-v1",
        "generated_at": utc_now(),
        "status": status,
        "query": normalized_query,
        "catalog_status": catalog_report.get("status"),
        "catalog_resolution_source": catalog_report.get("resolution_source"),
        "catalog_selected_domain_discarded_after_run": bool(
            catalog_report.get("selected_domain")
        ),
        "catalog_candidate_titles": catalog_titles,
        "catalog_query_fallback_used": fallback_used,
        "lawful_searches": lawful_searches,
        "match_count": len(deduplicated),
        "matches": deduplicated,
        "selected_match": selected_match,
        "reader": dict(reader_report) if reader_report is not None else None,
        "safety": {
            "anna_metadata_only": True,
            "anna_detail_pages_followed": False,
            "anna_download_links_followed": False,
            "book_files_retrieved_from_anna": False,
            "lawful_provider_locations_only": True,
            "provider_declared_locations_required": True,
            "rights_attestation_required_for_reader": True,
            "access_controls_bypassed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog-registry", type=Path, required=True)
    parser.add_argument("--public-registry", type=Path, required=True)
    parser.add_argument("--reader-registry", type=Path, required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--maximum-catalog-titles", type=int, default=3)
    parser.add_argument("--results-per-source", type=int, default=5)
    parser.add_argument("--minimum-similarity", type=float, default=0.62)
    parser.add_argument("--timeout", type=int, default=25)
    parser.add_argument("--max-bytes", type=int, default=5_000_000)
    parser.add_argument("--read-first", action="store_true")
    parser.add_argument("--rights-note", default="")
    parser.add_argument("--reader-max-bytes", type=int, default=25_000_000)
    parser.add_argument("--reader-max-chars", type=int, default=150_000)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--enforce", action="store_true")
    args = parser.parse_args()

    try:
        report = resolve_to_lawful_fulltext(
            load_json(args.catalog_registry),
            load_json(args.public_registry),
            load_json(args.reader_registry),
            query=args.query,
            maximum_catalog_titles=args.maximum_catalog_titles,
            results_per_source=args.results_per_source,
            minimum_similarity=args.minimum_similarity,
            timeout=args.timeout,
            max_bytes=args.max_bytes,
            read_first=args.read_first,
            rights_note=args.rights_note,
            reader_max_bytes=args.reader_max_bytes,
            reader_max_chars=args.reader_max_chars,
        )
    except Exception as exc:
        report = {
            "schema_version": "catalog-lawful-resolver-report-v1",
            "generated_at": utc_now(),
            "status": "fail",
            "query": args.query,
            "error": f"{type(exc).__name__}: {str(exc)[:500]}",
        }

    save_json(args.output, report)
    print(
        json.dumps(
            {
                "status": report.get("status"),
                "catalog_status": report.get("catalog_status"),
                "catalog_candidate_titles": len(
                    report.get("catalog_candidate_titles") or []
                ),
                "match_count": report.get("match_count", 0),
                "reader_status": (report.get("reader") or {}).get("status"),
            },
            ensure_ascii=False,
        )
    )
    if args.enforce and report.get("status") not in {"pass", "no-lawful-match"}:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
