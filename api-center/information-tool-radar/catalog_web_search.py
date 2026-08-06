#!/usr/bin/env python3
"""Controlled metadata-only web catalog search with fail-closed domain handling.

This adapter uses only Python's standard library. It reads visible search-result
titles from explicitly approved HTTPS domains. It never installs third-party
wrappers, follows result/detail/download links, or follows cross-domain redirects.
"""
from __future__ import annotations

import argparse
import html
import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Mapping

USER_AGENT = (
    "evidence-data-center-catalog-search/1.0 "
    "(+https://github.com/a15280020511/evidence-data-center)"
)
ALLOWED_REDIRECT_CODES = {301, 302, 303, 307, 308}


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


class SearchResultParser(HTMLParser):
    """Extract visible titles without retaining result URLs."""

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


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Block redirects so an approved domain cannot silently move to an unknown host."""

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


def normalize_domain(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"domain must use HTTPS: {url}")
    if not parsed.hostname:
        raise ValueError(f"domain hostname missing: {url}")
    if parsed.username or parsed.password or parsed.port:
        raise ValueError(f"domain credentials/port not allowed: {url}")
    if parsed.path not in ("", "/") or parsed.params or parsed.query or parsed.fragment:
        raise ValueError(f"domain URL must not contain path/query/fragment: {url}")
    return f"https://{parsed.hostname.casefold()}"


def validate_registry(registry: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if registry.get("schema_version") != "catalog-domain-registry-v1":
        errors.append("unsupported schema_version")
    if registry.get("mode") != "metadata-only":
        errors.append("mode must be metadata-only")

    policy = registry.get("policy")
    if not isinstance(policy, Mapping):
        errors.append("policy missing")
        policy = {}
    required_policy = {
        "https_required": True,
        "fail_closed": True,
        "automatic_domain_promotion": False,
        "follow_cross_domain_redirects": False,
        "unknown_domains_allowed": False,
    }
    for key, expected in required_policy.items():
        if policy.get(key) is not expected:
            errors.append(f"policy {key} must be {expected!r}")

    domains = registry.get("domains")
    if not isinstance(domains, list) or not domains:
        errors.append("approved domain list missing")
        return errors

    seen: set[str] = set()
    enabled = 0
    for item in domains:
        if not isinstance(item, Mapping):
            errors.append("invalid domain entry")
            continue
        try:
            normalized = normalize_domain(str(item.get("url") or ""))
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if normalized in seen:
            errors.append(f"duplicate domain: {normalized}")
        seen.add(normalized)
        if item.get("approval_status") != "approved":
            errors.append(f"domain not approved: {normalized}")
        if item.get("enabled") is True:
            enabled += 1
        priority = item.get("priority")
        if not isinstance(priority, int) or priority < 1:
            errors.append(f"invalid priority: {normalized}")

    if enabled < int(policy.get("minimum_healthy_domains") or 1):
        errors.append("not enough enabled approved domains")
    return errors


def approved_domains(registry: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in registry.get("domains") or []:
        if not isinstance(item, Mapping):
            continue
        if item.get("enabled") is not True or item.get("approval_status") != "approved":
            continue
        row = dict(item)
        row["url"] = normalize_domain(str(item.get("url") or ""))
        rows.append(row)
    return sorted(rows, key=lambda value: int(value.get("priority") or 999999))


def build_opener() -> urllib.request.OpenerDirector:
    context = ssl.create_default_context()
    return urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=context),
        NoRedirect(),
    )


def request_search(
    domain: str,
    query: str,
    timeout: int,
    max_bytes: int,
) -> tuple[int, str]:
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
    with build_opener().open(request, timeout=timeout) as response:
        payload = response.read(max_bytes + 1)
        if len(payload) > max_bytes:
            raise RuntimeError(f"response exceeded {max_bytes} bytes")
        charset = response.headers.get_content_charset() or "utf-8"
        return int(response.status), payload.decode(charset, errors="replace")


def redirect_candidate(source_domain: str, location: str | None) -> dict[str, Any] | None:
    if not location:
        return None
    target = urllib.parse.urljoin(source_domain.rstrip("/") + "/", location)
    parsed = urllib.parse.urlparse(target)
    if parsed.scheme != "https" or not parsed.hostname:
        return None
    target_domain = f"https://{parsed.hostname.casefold()}"
    if target_domain == source_domain:
        return None
    return {
        "source_domain": source_domain,
        "candidate_domain": target_domain,
        "status": "unapproved-not-followed",
    }


def probe_domain(
    domain: str,
    query: str,
    timeout: int,
    max_bytes: int,
    max_titles: int,
    retries: int,
) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    for attempt_number in range(1, retries + 1):
        try:
            status_code, page = request_search(domain, query, timeout, max_bytes)
            parser = SearchResultParser()
            parser.feed(page)
            titles = parser.titles
            if status_code == 200 and titles:
                return {
                    "domain": domain,
                    "status": "healthy",
                    "http_status": status_code,
                    "result_count_observed": len(titles),
                    "sample_titles": titles[:max_titles],
                    "attempts": attempts + [{
                        "attempt": attempt_number,
                        "http_status": status_code,
                        "visible_titles": len(titles),
                        "error": None,
                    }],
                    "redirect_candidate": None,
                }
            attempts.append({
                "attempt": attempt_number,
                "http_status": status_code,
                "visible_titles": len(titles),
                "error": "search-result contract mismatch",
            })
        except urllib.error.HTTPError as exc:
            location = exc.headers.get("Location") if exc.headers else None
            candidate = (
                redirect_candidate(domain, location)
                if int(exc.code) in ALLOWED_REDIRECT_CODES
                else None
            )
            attempts.append({
                "attempt": attempt_number,
                "http_status": int(exc.code),
                "visible_titles": 0,
                "error": f"HTTPError: {exc.code}",
                "redirect_candidate": candidate,
            })
            if candidate is not None:
                return {
                    "domain": domain,
                    "status": "redirect-blocked",
                    "http_status": int(exc.code),
                    "result_count_observed": 0,
                    "sample_titles": [],
                    "attempts": attempts,
                    "redirect_candidate": candidate,
                }
        except Exception as exc:
            attempts.append({
                "attempt": attempt_number,
                "http_status": None,
                "visible_titles": 0,
                "error": f"{type(exc).__name__}: {str(exc)[:180]}",
            })

    return {
        "domain": domain,
        "status": "unavailable",
        "http_status": None,
        "result_count_observed": 0,
        "sample_titles": [],
        "attempts": attempts,
        "redirect_candidate": None,
    }


def search_catalog(
    registry: Mapping[str, Any],
    query: str,
    timeout: int = 18,
    max_bytes: int = 2_000_000,
    max_titles: int = 10,
    retries: int = 2,
) -> dict[str, Any]:
    errors = validate_registry(registry)
    query = " ".join(query.split()).strip()
    if not query:
        errors.append("query is empty")
    if len(query) > 200:
        errors.append("query exceeds 200 characters")

    if errors:
        return {
            "schema_version": "catalog-web-search-report-v1",
            "generated_at": utc_now(),
            "status": "fail",
            "query": query,
            "policy_errors": errors,
            "selected_domain": None,
            "domains": [],
            "redirect_candidates": [],
            "manual_review_required": True,
        }

    rows = [
        probe_domain(
            item["url"],
            query,
            timeout=timeout,
            max_bytes=max_bytes,
            max_titles=max_titles,
            retries=retries,
        )
        for item in approved_domains(registry)
    ]
    healthy = [row for row in rows if row["status"] == "healthy"]
    selected = healthy[0] if healthy else None
    redirect_candidates = [
        row["redirect_candidate"]
        for row in rows
        if row.get("redirect_candidate") is not None
    ]

    if selected is None:
        status = "unavailable"
    elif rows and selected["domain"] == rows[0]["domain"] and not redirect_candidates:
        status = "pass"
    else:
        status = "degraded"

    return {
        "schema_version": "catalog-web-search-report-v1",
        "generated_at": utc_now(),
        "status": status,
        "scope": "public search-result metadata only",
        "query": query,
        "selected_domain": selected["domain"] if selected else None,
        "result_count_observed": selected["result_count_observed"] if selected else 0,
        "sample_titles": selected["sample_titles"] if selected else [],
        "domains": rows,
        "redirect_candidates": redirect_candidates,
        "manual_review_required": bool(redirect_candidates or selected is None),
        "domain_change_policy": {
            "approved_fallbacks_only": True,
            "cross_domain_redirects_followed": False,
            "new_domains_auto_approved": False,
            "unapproved_redirect_recorded_as_candidate": True,
            "all_domains_unavailable_action": "fail-closed",
        },
        "safety": {
            "third_party_packages_installed": False,
            "third_party_code_executed": False,
            "detail_pages_followed": False,
            "download_links_followed": False,
            "direct_links_recorded": False,
            "book_files_retrieved": False,
            "credentials_used": False,
            "access_controls_bypassed": False,
        },
        "interpretation": (
            "A visible catalog record proves only that the title is searchable. "
            "It does not establish a right to access or download a particular edition."
        ),
        "policy_errors": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=18)
    parser.add_argument("--max-bytes", type=int, default=2_000_000)
    parser.add_argument("--max-titles", type=int, default=10)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--enforce", action="store_true")
    args = parser.parse_args()

    report = search_catalog(
        load_json(args.registry),
        query=args.query,
        timeout=min(max(args.timeout, 5), 45),
        max_bytes=min(max(args.max_bytes, 100_000), 3_000_000),
        max_titles=min(max(args.max_titles, 1), 20),
        retries=min(max(args.retries, 1), 3),
    )
    save_json(args.output, report)
    print(json.dumps({
        "status": report["status"],
        "selected_domain": report.get("selected_domain"),
        "result_count_observed": report.get("result_count_observed", 0),
        "redirect_candidates": len(report.get("redirect_candidates") or []),
        "manual_review_required": report.get("manual_review_required"),
    }, ensure_ascii=False))
    if args.enforce and report["status"] not in {"pass", "degraded"}:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
