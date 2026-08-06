#!/usr/bin/env python3
"""Metadata-only live probe for strategy-related books in Anna's Archive.

The probe requests only public search-result pages, extracts visible result titles,
and never follows result/detail/download links. It is intended for bounded evidence
collection in GitHub Actions, not as a production connector.
"""
from __future__ import annotations

import argparse
import html
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

DOMAINS = [
    "https://annas-archive.gl",
    "https://annas-archive.pk",
    "https://annas-archive.gd",
]
QUERIES = ["谋略", "战略", "孙子兵法", "三十六计", "The Art of War"]
USER_AGENT = (
    "evidence-data-center-metadata-probe/1.0 "
    "(+https://github.com/a15280020511/evidence-data-center)"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class SearchResultParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._capture = False
        self._parts: list[str] = []
        self.titles: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() != "a":
            return
        values = {key.casefold(): value or "" for key, value in attrs}
        href = values.get("href", "")
        if href.startswith("/md5/"):
            self._capture = True
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() != "a" or not self._capture:
            return
        title = " ".join(" ".join(self._parts).split()).strip()
        title = html.unescape(title)[:240]
        if title and title not in self.titles:
            self.titles.append(title)
        self._capture = False
        self._parts = []


def request_search(domain: str, query: str, timeout: int, max_bytes: int) -> tuple[int, str]:
    url = domain.rstrip("/") + "/search?" + urllib.parse.urlencode({"q": query})
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Encoding": "identity",
            "User-Agent": USER_AGENT,
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read(max_bytes + 1)
        if len(payload) > max_bytes:
            raise RuntimeError(f"response exceeded {max_bytes} bytes")
        charset = response.headers.get_content_charset() or "utf-8"
        return int(response.status), payload.decode(charset, errors="replace")


def probe_query(query: str, timeout: int, max_bytes: int, max_titles: int) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    for domain in DOMAINS:
        try:
            status_code, page = request_search(domain, query, timeout, max_bytes)
            parser = SearchResultParser()
            parser.feed(page)
            titles = parser.titles[:max_titles]
            attempts.append(
                {
                    "domain": domain,
                    "http_status": status_code,
                    "visible_result_titles": len(parser.titles),
                    "error": None,
                }
            )
            if titles:
                return {
                    "query": query,
                    "status": "results_found",
                    "domain": domain,
                    "http_status": status_code,
                    "result_count_observed": len(parser.titles),
                    "sample_titles": titles,
                    "attempts": attempts,
                }
        except urllib.error.HTTPError as exc:
            attempts.append(
                {
                    "domain": domain,
                    "http_status": int(exc.code),
                    "visible_result_titles": 0,
                    "error": f"HTTPError: {exc.code}",
                }
            )
        except Exception as exc:  # bounded diagnostic evidence
            attempts.append(
                {
                    "domain": domain,
                    "http_status": None,
                    "visible_result_titles": 0,
                    "error": f"{type(exc).__name__}: {str(exc)[:180]}",
                }
            )
    return {
        "query": query,
        "status": "no_results_or_unavailable",
        "domain": None,
        "http_status": None,
        "result_count_observed": 0,
        "sample_titles": [],
        "attempts": attempts,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--max-bytes", type=int, default=2_000_000)
    parser.add_argument("--max-titles", type=int, default=8)
    args = parser.parse_args()

    timeout = min(max(args.timeout, 5), 45)
    max_bytes = min(max(args.max_bytes, 100_000), 3_000_000)
    max_titles = min(max(args.max_titles, 1), 12)
    rows = [probe_query(query, timeout, max_bytes, max_titles) for query in QUERIES]
    successful = [row for row in rows if row["status"] == "results_found"]
    total_observed = sum(int(row["result_count_observed"]) for row in rows)
    status = "pass" if len(successful) >= 3 else "partial" if successful else "unavailable"
    report = {
        "schema_version": "annas-strategy-catalog-probe-v1",
        "generated_at": utc_now(),
        "status": status,
        "scope": "public search-result metadata only",
        "queries_tested": len(rows),
        "queries_with_results": len(successful),
        "visible_results_observed": total_observed,
        "results": rows,
        "safety": {
            "metadata_only": True,
            "detail_pages_followed": False,
            "download_links_followed": False,
            "direct_links_recorded": False,
            "credentials_used": False,
            "access_controls_bypassed": False,
        },
        "interpretation": (
            "A visible catalog record only proves searchability. It does not establish "
            "that accessing or downloading a particular edition is lawful."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": status,
                "queries_tested": len(rows),
                "queries_with_results": len(successful),
                "visible_results_observed": total_observed,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
