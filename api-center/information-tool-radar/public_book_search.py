#!/usr/bin/env python3
"""Unified, policy-bound search for lawful public-book sources.

The adapter searches Project Gutenberg, Standard Ebooks, and English/Chinese
Wikisource through fixed official/public endpoints. It returns catalog metadata
and provider-declared readable locations. It does not search Anna's Archive
book-detail/download pages and never resolves Anna download links.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from xml.etree import ElementTree as ET

USER_AGENT = (
    "evidence-data-center-public-book-search/1.0 "
    "(+https://github.com/a15280020511/evidence-data-center)"
)
HARD_STOP_HTTP = {401, 403, 429}
REDIRECT_HTTP = {301, 302, 303, 307, 308}
ALLOWED_PARSERS = {
    "opds-atom",
    "standard-ebooks-html",
    "mediawiki-search-json",
}
BOOK_FILE_MIME_TO_FORMAT = {
    "application/epub+zip": "epub",
    "text/html": "html",
    "application/xhtml+xml": "xhtml",
    "text/plain": "txt",
    "application/pdf": "pdf",
}
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


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


def normalize_host(value: str) -> str:
    host = value.strip().casefold().rstrip(".")
    if not host or "/" in host or ":" in host or "@" in host:
        raise ValueError(f"invalid host: {value}")
    return host


def validate_registry(registry: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if registry.get("schema_version") != "public-book-search-sources-v1":
        errors.append("unsupported schema_version")
    policy = registry.get("policy")
    if not isinstance(policy, Mapping):
        errors.append("policy missing")
        policy = {}
    expected = {
        "https_required": True,
        "unknown_sources_allowed": False,
        "redirects_allowed": False,
        "automatic_retries_allowed": False,
        "requests_per_source_max": 1,
        "source_concurrency_max": 1,
        "direct_file_links_must_be_provider_declared": True,
        "anna_archive_downloads_allowed": False,
        "access_control_bypass_allowed": False,
    }
    for key, value in expected.items():
        if policy.get(key) != value:
            errors.append(f"policy {key} must be {value!r}")
    if set(policy.get("source_side_hard_stop_http") or []) != HARD_STOP_HTTP:
        errors.append("source_side_hard_stop_http must be [401, 403, 429]")
    query_max = policy.get("query_length_max")
    if not isinstance(query_max, int) or not 1 <= query_max <= 500:
        errors.append("query_length_max must be 1..500")
    result_max = policy.get("results_per_source_max")
    if not isinstance(result_max, int) or not 1 <= result_max <= 50:
        errors.append("results_per_source_max must be 1..50")
    interval = policy.get("minimum_interval_seconds")
    if not isinstance(interval, int) or not 0 <= interval <= 60:
        errors.append("minimum_interval_seconds must be 0..60")

    sources = registry.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("sources missing")
        return errors
    seen_ids: set[str] = set()
    seen_endpoints: set[str] = set()
    for source in sources:
        if not isinstance(source, Mapping):
            errors.append("invalid source entry")
            continue
        source_id = str(source.get("source_id") or "")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", source_id):
            errors.append(f"invalid source_id: {source_id}")
        if source_id in seen_ids:
            errors.append(f"duplicate source_id: {source_id}")
        seen_ids.add(source_id)
        if "anna" in source_id:
            errors.append("Anna's Archive may not be a public-book download search source")
        if source.get("enabled") is not True:
            errors.append(f"source must be enabled: {source_id}")
        parser = str(source.get("parser") or "")
        if parser not in ALLOWED_PARSERS:
            errors.append(f"unsupported parser for {source_id}: {parser}")
        endpoint = str(source.get("endpoint") or "")
        parsed = urllib.parse.urlparse(endpoint)
        try:
            configured_host = normalize_host(str(source.get("host") or ""))
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if parsed.scheme != "https" or parsed.hostname != configured_host:
            errors.append(f"endpoint/host mismatch for {source_id}")
        if parsed.username or parsed.password or parsed.port:
            errors.append(f"credentials or explicit port forbidden for {source_id}")
        if endpoint in seen_endpoints:
            errors.append(f"duplicate endpoint: {endpoint}")
        seen_endpoints.add(endpoint)
    return errors


def source_map(registry: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {
        str(source["source_id"]): source
        for source in registry.get("sources") or []
        if isinstance(source, Mapping) and source.get("enabled") is True
    }


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Mapping[str, str],
        newurl: str,
    ) -> None:
        return None


def build_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        NoRedirect(),
    )


def build_request_url(source: Mapping[str, Any], query: str, limit: int) -> str:
    endpoint = str(source["endpoint"])
    parser = str(source["parser"])
    if parser in {"opds-atom", "standard-ebooks-html"}:
        params = {str(source.get("query_parameter") or "query"): query}
    elif parser == "mediawiki-search-json":
        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "list": "search",
            "srsearch": query,
            "srnamespace": "0",
            "srlimit": str(limit),
            "srprop": "size|wordcount|timestamp|snippet",
            "utf8": "1",
        }
    else:
        raise ValueError(f"unsupported parser: {parser}")
    return endpoint + ("&" if "?" in endpoint else "?") + urllib.parse.urlencode(params)


def _request_once(
    source: Mapping[str, Any],
    query: str,
    limit: int,
    timeout: int,
    max_bytes: int,
) -> dict[str, Any]:
    url = build_request_url(source, query, limit)
    accept = {
        "opds-atom": "application/atom+xml,application/xml;q=0.9,text/xml;q=0.8",
        "standard-ebooks-html": "text/html,application/xhtml+xml;q=0.9",
        "mediawiki-search-json": "application/json",
    }[str(source["parser"])]
    request = urllib.request.Request(
        url,
        headers={
            "Accept": accept,
            "Accept-Encoding": "identity",
            "User-Agent": USER_AGENT,
        },
        method="GET",
    )
    started = time.monotonic()
    try:
        with build_opener().open(request, timeout=timeout) as response:
            payload = response.read(max_bytes + 1)
            if len(payload) > max_bytes:
                raise RuntimeError(f"response exceeds {max_bytes} bytes")
            status = int(getattr(response, "status", 200))
            final_url = response.geturl()
            content_type = response.headers.get("Content-Type", "")
            retry_after = response.headers.get("Retry-After")
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        retry_after = exc.headers.get("Retry-After") if exc.headers else None
        location = exc.headers.get("Location") if exc.headers else None
        state = "source_side_hard_stop" if status in HARD_STOP_HTTP else "http_error"
        if status in REDIRECT_HTTP:
            state = "redirect_blocked"
        return {
            "success": False,
            "state": state,
            "http_status": status,
            "retry_after": retry_after,
            "redirect_location": location,
            "attempt_count": 1,
            "source_side_hard_stop": status in HARD_STOP_HTTP,
            "duration_ms": round((time.monotonic() - started) * 1000, 3),
            "request_url": url,
            "payload": b"",
            "content_type": "",
        }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {
            "success": False,
            "state": "network_error",
            "http_status": None,
            "retry_after": None,
            "attempt_count": 1,
            "source_side_hard_stop": False,
            "duration_ms": round((time.monotonic() - started) * 1000, 3),
            "request_url": url,
            "payload": b"",
            "content_type": "",
            "error": f"{type(exc).__name__}: {str(exc)[:300]}",
        }
    if final_url != url:
        return {
            "success": False,
            "state": "unexpected_redirect",
            "http_status": status,
            "retry_after": retry_after,
            "attempt_count": 1,
            "source_side_hard_stop": False,
            "duration_ms": round((time.monotonic() - started) * 1000, 3),
            "request_url": url,
            "payload": b"",
            "content_type": content_type,
        }
    return {
        "success": 200 <= status < 300,
        "state": "success" if 200 <= status < 300 else "http_error",
        "http_status": status,
        "retry_after": retry_after,
        "attempt_count": 1,
        "source_side_hard_stop": status in HARD_STOP_HTTP,
        "duration_ms": round((time.monotonic() - started) * 1000, 3),
        "request_url": url,
        "payload": payload,
        "content_type": content_type,
    }


def _clean_text(value: str) -> str:
    no_tags = re.sub(r"<[^>]+>", " ", value)
    return " ".join(html.unescape(no_tags).split()).strip()


def _safe_https_url(url: str, allowed_host: str) -> str | None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    host = parsed.hostname.casefold().rstrip(".")
    if host != allowed_host and not host.endswith("." + allowed_host):
        return None
    return parsed._replace(scheme="https", fragment="").geturl()


def parse_gutenberg_opds(payload: bytes, limit: int) -> list[dict[str, Any]]:
    root = ET.fromstring(payload)
    output: list[dict[str, Any]] = []
    for entry in root.findall("atom:entry", ATOM_NS):
        title = " ".join((entry.findtext("atom:title", default="", namespaces=ATOM_NS)).split())
        if not title:
            continue
        authors = [
            " ".join((node.findtext("atom:name", default="", namespaces=ATOM_NS)).split())
            for node in entry.findall("atom:author", ATOM_NS)
        ]
        authors = [value for value in authors if value]
        entry_id = entry.findtext("atom:id", default="", namespaces=ATOM_NS).strip()
        catalog_url: str | None = None
        readable_locations: list[dict[str, str]] = []
        available_formats: list[str] = []
        for link in entry.findall("atom:link", ATOM_NS):
            href = str(link.attrib.get("href") or "")
            rel = str(link.attrib.get("rel") or "")
            mime = str(link.attrib.get("type") or "").split(";", 1)[0].casefold()
            safe = _safe_https_url(href, "gutenberg.org")
            if not safe:
                continue
            if rel == "alternate" and "/ebooks/" in urllib.parse.urlparse(safe).path:
                catalog_url = safe
            fmt = BOOK_FILE_MIME_TO_FORMAT.get(mime)
            if fmt and "acquisition" in rel:
                available_formats.append(fmt)
                readable_locations.append(
                    {"format": fmt, "url": safe, "declared_by": "official-opds"}
                )
        if not catalog_url:
            safe_id = _safe_https_url(entry_id, "gutenberg.org")
            if safe_id and re.fullmatch(r"/ebooks/\d+/?", urllib.parse.urlparse(safe_id).path):
                catalog_url = safe_id
        if not catalog_url:
            match = re.search(r"(\d+)$", entry_id)
            if match:
                catalog_url = f"https://www.gutenberg.org/ebooks/{match.group(1)}"
        summary = _clean_text(entry.findtext("atom:summary", default="", namespaces=ATOM_NS))
        output.append(
            {
                "title": title[:500],
                "authors": authors[:20],
                "catalog_url": catalog_url,
                "readable_locations": readable_locations[:10],
                "available_formats": sorted(set(available_formats)),
                "summary": summary[:1000],
                "rights_basis": "public-domain-us",
            }
        )
        if len(output) >= limit:
            break
    return output


class StandardEbooksParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._href: str | None = None
        self._parts: list[str] = []
        self.records: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() != "a":
            return
        href = dict(attrs).get("href") or ""
        parsed = urllib.parse.urlparse(href)
        path = parsed.path
        segments = [segment for segment in path.split("/") if segment]
        if len(segments) >= 3 and segments[0] == "ebooks" and "downloads" not in segments:
            self._href = path
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() != "a" or self._href is None:
            return
        text = " ".join(" ".join(self._parts).split()).strip()
        if text and text.casefold() not in {"download", "read online", "details"}:
            self.records.append((self._href, text))
        self._href = None
        self._parts = []


def parse_standard_ebooks_html(payload: bytes, limit: int) -> list[dict[str, Any]]:
    text = payload.decode("utf-8", errors="replace")
    parser = StandardEbooksParser()
    parser.feed(text)
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path, title in parser.records:
        url = urllib.parse.urljoin("https://standardebooks.org", path)
        if url in seen:
            continue
        seen.add(url)
        segments = [urllib.parse.unquote(segment) for segment in path.split("/") if segment]
        author_hint = ""
        if len(segments) >= 2:
            author_hint = " ".join(part.capitalize() for part in segments[1].split("-"))
        output.append(
            {
                "title": title[:500],
                "authors": [author_hint] if author_hint else [],
                "catalog_url": url,
                "readable_locations": [],
                "available_formats": ["epub", "xhtml"],
                "summary": "",
                "rights_basis": "public-domain-us-and-cc0-project-work",
            }
        )
        if len(output) >= limit:
            break
    return output


def parse_mediawiki_search(
    payload: bytes, source: Mapping[str, Any], limit: int
) -> list[dict[str, Any]]:
    value = json.loads(payload.decode("utf-8"))
    records = ((value.get("query") or {}).get("search") or []) if isinstance(value, Mapping) else []
    host = str(source["host"])
    output: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, Mapping):
            continue
        title = " ".join(str(record.get("title") or "").split()).strip()
        if not title:
            continue
        url = f"https://{host}/wiki/{urllib.parse.quote(title.replace(' ', '_'), safe=':/')}"
        output.append(
            {
                "title": title[:500],
                "authors": [],
                "catalog_url": url,
                "readable_locations": [
                    {"format": "html", "url": url, "declared_by": "mediawiki-page"}
                ],
                "available_formats": ["html"],
                "summary": _clean_text(str(record.get("snippet") or ""))[:1000],
                "page_id": record.get("pageid"),
                "word_count": record.get("wordcount"),
                "last_modified": record.get("timestamp"),
                "rights_basis": "item-rights-and-cc-by-sa",
            }
        )
        if len(output) >= limit:
            break
    return output


def parse_response(
    source: Mapping[str, Any], payload: bytes, limit: int
) -> list[dict[str, Any]]:
    parser = str(source["parser"])
    if parser == "opds-atom":
        return parse_gutenberg_opds(payload, limit)
    if parser == "standard-ebooks-html":
        return parse_standard_ebooks_html(payload, limit)
    if parser == "mediawiki-search-json":
        return parse_mediawiki_search(payload, source, limit)
    raise ValueError(f"unsupported parser: {parser}")


def _host_hash(host: str) -> str:
    return hashlib.sha256(host.encode("utf-8")).hexdigest()


def run_search(
    registry: Mapping[str, Any],
    *,
    query: str,
    selected_sources: Sequence[str] | None = None,
    limit: int = 10,
    timeout: int = 25,
    max_bytes: int = 5_000_000,
    fetcher: Callable[[Mapping[str, Any], str, int, int, int], Mapping[str, Any]] = _request_once,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    errors = validate_registry(registry)
    policy = registry.get("policy") if isinstance(registry.get("policy"), Mapping) else {}
    normalized_query = " ".join(query.split()).strip()
    if not normalized_query:
        errors.append("query is required")
    query_max = int(policy.get("query_length_max") or 200)
    if len(normalized_query) > query_max:
        errors.append(f"query exceeds {query_max} characters")
    result_max = int(policy.get("results_per_source_max") or 20)
    if not 1 <= limit <= result_max:
        errors.append(f"limit must be 1..{result_max}")

    available = source_map(registry)
    source_ids = list(selected_sources or available.keys())
    if len(source_ids) != len(set(source_ids)):
        errors.append("duplicate selected source")
    for source_id in source_ids:
        if source_id not in available:
            errors.append(f"unknown or disabled source: {source_id}")
        if "anna" in source_id.casefold():
            errors.append("Anna's Archive download search is forbidden")
    if errors:
        return {
            "schema_version": "public-book-search-report-v1",
            "generated_at": utc_now(),
            "status": "blocked",
            "query": normalized_query,
            "policy_errors": errors,
            "safety": {
                "anna_archive_downloads_allowed": False,
                "automatic_retries_allowed": False,
                "redirects_allowed": False,
            },
        }

    results: list[dict[str, Any]] = []
    source_reports: list[dict[str, Any]] = []
    interval = float(policy.get("minimum_interval_seconds") or 0)
    for index, source_id in enumerate(source_ids):
        source = available[source_id]
        if index and interval:
            sleep_fn(interval)
        response = dict(fetcher(source, normalized_query, limit, timeout, max_bytes))
        payload = response.pop("payload", b"")
        report = {
            "source_id": source_id,
            "display_name": source.get("display_name"),
            "host_sha256": _host_hash(str(source["host"])),
            "access_class": source.get("access_class"),
            "request_count": int(response.get("attempt_count") or 0),
            "automatic_retry_count": 0,
            "source_switched": False,
            **response,
        }
        if response.get("success"):
            try:
                parsed = parse_response(source, bytes(payload), limit)
                for rank, item in enumerate(parsed, start=1):
                    item.update(
                        {
                            "source_id": source_id,
                            "source_display_name": source.get("display_name"),
                            "rank_within_source": rank,
                            "source_rights_basis": source.get("rights_basis"),
                        }
                    )
                results.extend(parsed)
                report["result_count"] = len(parsed)
                report["parse_state"] = "success"
            except (ET.ParseError, json.JSONDecodeError, UnicodeError, ValueError) as exc:
                report["success"] = False
                report["state"] = "parse_error"
                report["parse_state"] = "failure"
                report["error"] = f"{type(exc).__name__}: {str(exc)[:300]}"
                report["result_count"] = 0
        else:
            report["result_count"] = 0
            report["parse_state"] = "not_attempted"
        source_reports.append(report)

    successful = sum(bool(item.get("success")) for item in source_reports)
    hard_stops = sum(bool(item.get("source_side_hard_stop")) for item in source_reports)
    status = "pass" if successful else "fail"
    return {
        "schema_version": "public-book-search-report-v1",
        "generated_at": utc_now(),
        "status": status,
        "query": normalized_query,
        "selected_sources": source_ids,
        "source_count": len(source_ids),
        "successful_source_count": successful,
        "failed_source_count": len(source_ids) - successful,
        "source_side_hard_stop_count": hard_stops,
        "result_count": len(results),
        "results": results,
        "sources": source_reports,
        "safety": {
            "fixed_sources_only": True,
            "requests_per_source_max": 1,
            "source_concurrency_max": 1,
            "automatic_retries_allowed": False,
            "redirects_allowed": False,
            "source_side_hard_stop_http": sorted(HARD_STOP_HTTP),
            "same_source_endpoint_or_identity_switch_after_rejection_allowed": False,
            "minimum_interval_seconds": interval,
            "anna_archive_downloads_allowed": False,
            "access_control_bypass_allowed": False,
            "direct_file_links_must_be_provider_declared": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--source", action="append", dest="sources")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=25)
    parser.add_argument("--max-bytes", type=int, default=5_000_000)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--enforce", action="store_true")
    args = parser.parse_args()

    report = run_search(
        load_json(args.registry),
        query=args.query,
        selected_sources=args.sources,
        limit=args.limit,
        timeout=min(max(args.timeout, 5), 60),
        max_bytes=min(max(args.max_bytes, 100_000), 10_000_000),
    )
    save_json(args.output, report)
    print(
        json.dumps(
            {
                "status": report.get("status"),
                "query": report.get("query"),
                "source_count": report.get("source_count", 0),
                "successful_source_count": report.get("successful_source_count", 0),
                "result_count": report.get("result_count", 0),
                "source_side_hard_stop_count": report.get("source_side_hard_stop_count", 0),
            },
            ensure_ascii=False,
        )
    )
    if args.enforce and report.get("status") != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
