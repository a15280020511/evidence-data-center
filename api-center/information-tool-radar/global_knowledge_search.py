#!/usr/bin/env python3
"""Bounded live search across approved global knowledge sources.

Only explicitly implemented official/public endpoints are callable. Shadow-library
entries are never callable from this module. Results are metadata records; any
open-access/full-view location is returned only as provider-declared metadata and
is not fetched by this search layer.
"""
from __future__ import annotations

import argparse
import html
import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Callable, Mapping

import global_knowledge_registry as registry_mod

USER_AGENT = "evidence-data-center-global-knowledge-search/1.0"
HARD_STOP_HTTP = {401, 403, 429}
LIVE_SOURCE_IDS = {
    "open-library",
    "google-books",
    "crossref",
    "datacite",
    "europe-pmc",
    "semantic-scholar",
    "zenodo",
    "arxiv",
    "dblp",
    "library-of-congress",
}


def _clean(value: Any, limit: int = 500) -> str:
    return " ".join(html.unescape(str(value or "")).split()).strip()[:limit]


def _authors(values: Any) -> list[str]:
    output: list[str] = []
    if isinstance(values, list):
        for value in values:
            if isinstance(value, Mapping):
                text = _clean(value.get("name") or " ".join(filter(None, [value.get("given"), value.get("family")])))
            else:
                text = _clean(value)
            if text and text not in output:
                output.append(text)
    return output[:20]


def _year(value: Any) -> int | None:
    text = _clean(value, 32)
    for token in text.replace("/", "-").split("-"):
        if len(token) == 4 and token.isdigit():
            number = int(token)
            if 1000 <= number <= 3000:
                return number
    return None


class SameHostRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        old = urllib.parse.urlparse(req.full_url)
        new = urllib.parse.urlparse(urllib.parse.urljoin(req.full_url, newurl))
        if old.scheme != "https" or new.scheme != "https" or old.hostname != new.hostname:
            raise urllib.error.HTTPError(req.full_url, code, "cross-host redirect blocked", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        SameHostRedirect(),
    )


def request_bytes(url: str, *, timeout: int, max_bytes: int) -> bytes:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("only HTTPS endpoints are allowed")
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json, application/atom+xml, application/xml, text/xml;q=0.9",
            "Accept-Encoding": "identity",
            "User-Agent": USER_AGENT,
        },
        method="GET",
    )
    try:
        with _opener().open(request, timeout=timeout) as response:
            payload = response.read(max_bytes + 1)
            if len(payload) > max_bytes:
                raise RuntimeError(f"response exceeded {max_bytes} bytes")
            return payload
    except urllib.error.HTTPError as exc:
        if exc.code in HARD_STOP_HTTP:
            raise RuntimeError(f"source-side hard stop HTTP {exc.code}") from exc
        raise


def _json(url: str, *, timeout: int, max_bytes: int) -> Any:
    return json.loads(request_bytes(url, timeout=timeout, max_bytes=max_bytes).decode("utf-8", errors="replace"))


def _record(source_id: str, *, title: Any, authors: Any = None, year: Any = None, identifiers: Mapping[str, Any] | None = None, catalog_url: Any = None, provider_access: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
    clean_title = _clean(title, 400)
    if not clean_title:
        return None
    clean_ids = {str(k): _clean(v, 300) for k, v in (identifiers or {}).items() if _clean(v, 300)}
    row = {
        "source_id": source_id,
        "title": clean_title,
        "authors": _authors(authors),
        "year": _year(year),
        "identifiers": clean_ids,
        "catalog_url": _clean(catalog_url, 1000) or None,
        "provider_access": dict(provider_access or {}),
    }
    return row


def search_open_library(endpoint: str, query: str, limit: int, timeout: int, max_bytes: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"q": query, "limit": limit, "fields": "key,title,author_name,first_publish_year,isbn,public_scan_b,ia"})
    data = _json(f"{endpoint}?{params}", timeout=timeout, max_bytes=max_bytes)
    rows = []
    for item in (data.get("docs") if isinstance(data, Mapping) else []) or []:
        if not isinstance(item, Mapping):
            continue
        key = _clean(item.get("key"), 200)
        row = _record(
            "open-library",
            title=item.get("title"),
            authors=item.get("author_name"),
            year=item.get("first_publish_year"),
            identifiers={"openlibrary": key, "isbn": (item.get("isbn") or [None])[0]},
            catalog_url=f"https://openlibrary.org{key}" if key.startswith("/") else None,
            provider_access={"public_scan": bool(item.get("public_scan_b")), "internet_archive_ids": list(item.get("ia") or [])[:5]},
        )
        if row:
            rows.append(row)
    return rows[:limit]


def search_google_books(endpoint: str, query: str, limit: int, timeout: int, max_bytes: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"q": query, "maxResults": min(limit, 40), "printType": "books", "projection": "lite"})
    data = _json(f"{endpoint}?{params}", timeout=timeout, max_bytes=max_bytes)
    rows = []
    for item in (data.get("items") if isinstance(data, Mapping) else []) or []:
        if not isinstance(item, Mapping):
            continue
        info = item.get("volumeInfo") if isinstance(item.get("volumeInfo"), Mapping) else {}
        access = item.get("accessInfo") if isinstance(item.get("accessInfo"), Mapping) else {}
        identifiers = {}
        for ident in info.get("industryIdentifiers") or []:
            if isinstance(ident, Mapping) and ident.get("type") and ident.get("identifier"):
                identifiers[str(ident["type"]).casefold()] = ident["identifier"]
        row = _record(
            "google-books",
            title=info.get("title"),
            authors=info.get("authors"),
            year=info.get("publishedDate"),
            identifiers={"google_books": item.get("id"), **identifiers},
            catalog_url=info.get("infoLink") or item.get("selfLink"),
            provider_access={"viewability": access.get("viewability"), "public_domain": access.get("publicDomain"), "web_reader_link": access.get("webReaderLink")},
        )
        if row:
            rows.append(row)
    return rows[:limit]


def search_crossref(endpoint: str, query: str, limit: int, timeout: int, max_bytes: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"query.bibliographic": query, "rows": limit})
    data = _json(f"{endpoint}?{params}", timeout=timeout, max_bytes=max_bytes)
    message = data.get("message") if isinstance(data, Mapping) else {}
    rows = []
    for item in (message.get("items") if isinstance(message, Mapping) else []) or []:
        if not isinstance(item, Mapping):
            continue
        title = (item.get("title") or [None])[0]
        authors = [" ".join(filter(None, [a.get("given"), a.get("family")])) for a in item.get("author") or [] if isinstance(a, Mapping)]
        issued = item.get("issued") if isinstance(item.get("issued"), Mapping) else {}
        parts = issued.get("date-parts") or []
        year = parts[0][0] if parts and parts[0] else None
        row = _record("crossref", title=title, authors=authors, year=year, identifiers={"doi": item.get("DOI")}, catalog_url=item.get("URL"), provider_access={"type": item.get("type"), "license": [x.get("URL") for x in item.get("license") or [] if isinstance(x, Mapping) and x.get("URL")]})
        if row:
            rows.append(row)
    return rows[:limit]


def search_datacite(endpoint: str, query: str, limit: int, timeout: int, max_bytes: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"query": query, "page[size]": limit})
    data = _json(f"{endpoint}?{params}", timeout=timeout, max_bytes=max_bytes)
    rows = []
    for item in (data.get("data") if isinstance(data, Mapping) else []) or []:
        if not isinstance(item, Mapping):
            continue
        attrs = item.get("attributes") if isinstance(item.get("attributes"), Mapping) else {}
        titles = attrs.get("titles") or []
        title = titles[0].get("title") if titles and isinstance(titles[0], Mapping) else None
        creators = [c.get("name") for c in attrs.get("creators") or [] if isinstance(c, Mapping)]
        row = _record("datacite", title=title, authors=creators, year=attrs.get("publicationYear"), identifiers={"doi": attrs.get("doi") or item.get("id")}, catalog_url=attrs.get("url"), provider_access={"rights": attrs.get("rightsList") or [], "types": attrs.get("types") or {}})
        if row:
            rows.append(row)
    return rows[:limit]


def search_europe_pmc(endpoint: str, query: str, limit: int, timeout: int, max_bytes: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"query": query, "format": "json", "pageSize": limit, "resultType": "core"})
    data = _json(f"{endpoint}?{params}", timeout=timeout, max_bytes=max_bytes)
    result_list = data.get("resultList") if isinstance(data, Mapping) else {}
    rows = []
    for item in (result_list.get("result") if isinstance(result_list, Mapping) else []) or []:
        if not isinstance(item, Mapping):
            continue
        authors = [a.get("fullName") for a in ((item.get("authorList") or {}).get("author") if isinstance(item.get("authorList"), Mapping) else []) or [] if isinstance(a, Mapping)]
        pmcid = item.get("pmcid")
        row = _record("europe-pmc", title=item.get("title"), authors=authors, year=item.get("pubYear"), identifiers={"doi": item.get("doi"), "pmid": item.get("pmid"), "pmcid": pmcid}, catalog_url=f"https://europepmc.org/article/{item.get('source')}/{item.get('id')}" if item.get("source") and item.get("id") else None, provider_access={"is_open_access": item.get("isOpenAccess") == "Y", "in_pmc": bool(pmcid)})
        if row:
            rows.append(row)
    return rows[:limit]


def search_semantic_scholar(endpoint: str, query: str, limit: int, timeout: int, max_bytes: int) -> list[dict[str, Any]]:
    base = endpoint.rstrip("/") + "/paper/search"
    params = urllib.parse.urlencode({"query": query, "limit": min(limit, 100), "fields": "paperId,title,year,authors,url,externalIds,openAccessPdf"})
    data = _json(f"{base}?{params}", timeout=timeout, max_bytes=max_bytes)
    rows = []
    for item in (data.get("data") if isinstance(data, Mapping) else []) or []:
        if not isinstance(item, Mapping):
            continue
        ext = item.get("externalIds") if isinstance(item.get("externalIds"), Mapping) else {}
        oa = item.get("openAccessPdf") if isinstance(item.get("openAccessPdf"), Mapping) else {}
        row = _record("semantic-scholar", title=item.get("title"), authors=item.get("authors"), year=item.get("year"), identifiers={"semantic_scholar": item.get("paperId"), "doi": ext.get("DOI"), "arxiv": ext.get("ArXiv")}, catalog_url=item.get("url"), provider_access={"declared_open_access_pdf": oa.get("url"), "pdf_status": oa.get("status")})
        if row:
            rows.append(row)
    return rows[:limit]


def search_zenodo(endpoint: str, query: str, limit: int, timeout: int, max_bytes: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"q": query, "size": min(limit, 25)})
    data = _json(f"{endpoint}?{params}", timeout=timeout, max_bytes=max_bytes)
    hits = data.get("hits") if isinstance(data, Mapping) else {}
    items = hits.get("hits") if isinstance(hits, Mapping) else []
    rows = []
    for item in items or []:
        if not isinstance(item, Mapping):
            continue
        md = item.get("metadata") if isinstance(item.get("metadata"), Mapping) else {}
        creators = [c.get("name") for c in md.get("creators") or [] if isinstance(c, Mapping)]
        links = item.get("links") if isinstance(item.get("links"), Mapping) else {}
        row = _record("zenodo", title=md.get("title"), authors=creators, year=md.get("publication_date") or item.get("created"), identifiers={"zenodo": item.get("id"), "doi": item.get("doi") or md.get("doi")}, catalog_url=links.get("html") or links.get("self"), provider_access={"access_right": md.get("access_right"), "license": md.get("license")})
        if row:
            rows.append(row)
    return rows[:limit]


def _xml_local_text(element: ET.Element, local_name: str) -> str | None:
    for child in element.iter():
        if child.tag.rsplit("}", 1)[-1] == local_name and child.text:
            return _clean(child.text)
    return None


def search_arxiv(endpoint: str, query: str, limit: int, timeout: int, max_bytes: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"search_query": f"all:{query}", "start": 0, "max_results": limit})
    root = ET.fromstring(request_bytes(f"{endpoint}?{params}", timeout=timeout, max_bytes=max_bytes))
    ns = {"a": "http://www.w3.org/2005/Atom"}
    rows = []
    for entry in root.findall("a:entry", ns):
        authors = [_clean(x.findtext("a:name", default="", namespaces=ns)) for x in entry.findall("a:author", ns)]
        entry_id = _clean(entry.findtext("a:id", default="", namespaces=ns), 1000)
        arxiv_id = entry_id.rstrip("/").rsplit("/", 1)[-1] if entry_id else None
        row = _record("arxiv", title=entry.findtext("a:title", default="", namespaces=ns), authors=authors, year=entry.findtext("a:published", default="", namespaces=ns), identifiers={"arxiv": arxiv_id}, catalog_url=entry_id, provider_access={"published": entry.findtext("a:published", default="", namespaces=ns), "updated": entry.findtext("a:updated", default="", namespaces=ns)})
        if row:
            rows.append(row)
    return rows[:limit]


def search_dblp(endpoint: str, query: str, limit: int, timeout: int, max_bytes: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"q": query, "h": min(limit, 100), "format": "json"})
    data = _json(f"{endpoint}?{params}", timeout=timeout, max_bytes=max_bytes)
    hits = (((data.get("result") or {}).get("hits") or {}).get("hit") if isinstance(data, Mapping) else []) or []
    rows = []
    for hit in hits:
        info = hit.get("info") if isinstance(hit, Mapping) and isinstance(hit.get("info"), Mapping) else {}
        raw_authors = (info.get("authors") or {}).get("author") if isinstance(info.get("authors"), Mapping) else []
        if isinstance(raw_authors, Mapping):
            raw_authors = [raw_authors]
        authors = [a.get("text") if isinstance(a, Mapping) else a for a in raw_authors or []]
        row = _record("dblp", title=info.get("title"), authors=authors, year=info.get("year"), identifiers={"dblp": info.get("key"), "doi": info.get("doi")}, catalog_url=info.get("url"), provider_access={"type": info.get("type"), "venue": info.get("venue")})
        if row:
            rows.append(row)
    return rows[:limit]


def search_loc(endpoint: str, query: str, limit: int, timeout: int, max_bytes: int) -> list[dict[str, Any]]:
    base = endpoint.rstrip("/") + "/search/"
    params = urllib.parse.urlencode({"q": query, "fo": "json", "c": limit})
    data = _json(f"{base}?{params}", timeout=timeout, max_bytes=max_bytes)
    rows = []
    for item in (data.get("results") if isinstance(data, Mapping) else []) or []:
        if not isinstance(item, Mapping):
            continue
        contributors = item.get("contributor") or item.get("creator") or []
        if isinstance(contributors, str):
            contributors = [contributors]
        row = _record("library-of-congress", title=item.get("title"), authors=contributors, year=item.get("date"), identifiers={"loc": item.get("id"), "lccn": (item.get("number_lccn") or [None])[0] if isinstance(item.get("number_lccn"), list) else item.get("number_lccn")}, catalog_url=item.get("id"), provider_access={"online_format": item.get("online_format") or [], "rights": item.get("rights")})
        if row:
            rows.append(row)
    return rows[:limit]


SEARCHERS: dict[str, Callable[[str, str, int, int, int], list[dict[str, Any]]]] = {
    "open-library": search_open_library,
    "google-books": search_google_books,
    "crossref": search_crossref,
    "datacite": search_datacite,
    "europe-pmc": search_europe_pmc,
    "semantic-scholar": search_semantic_scholar,
    "zenodo": search_zenodo,
    "arxiv": search_arxiv,
    "dblp": search_dblp,
    "library-of-congress": search_loc,
}


def run_search(registry: Mapping[str, Any], *, query: str, source_ids: list[str] | None = None, limit: int = 5, timeout: int = 20, max_bytes: int = 2_000_000) -> dict[str, Any]:
    errors = registry_mod.validate_registry(registry)
    normalized_query = " ".join(query.split()).strip()
    if not normalized_query:
        errors.append("query is required")
    if len(normalized_query) > 300:
        errors.append("query exceeds 300 characters")
    if not 1 <= limit <= 20:
        errors.append("limit must be 1..20")
    selected = source_ids or sorted(LIVE_SOURCE_IDS)
    unknown = [source_id for source_id in selected if source_id not in LIVE_SOURCE_IDS]
    if unknown:
        errors.append("unsupported live source ids: " + ", ".join(unknown))
    by_id = {str(row.get("id")): row for row in registry.get("sources") or [] if isinstance(row, Mapping)}
    for source_id in selected:
        row = by_id.get(source_id)
        if not row:
            errors.append(f"source not registered: {source_id}")
        elif row.get("category") == registry_mod.SHADOW_CATEGORY:
            errors.append(f"shadow source cannot be live searched: {source_id}")
    if errors:
        return {"schema_version": "global-knowledge-search-report-v1", "status": "blocked", "query": normalized_query, "errors": errors, "results": [], "sources": []}

    source_reports = []
    results = []
    for source_id in selected:
        row = by_id[source_id]
        endpoint = str(row.get("endpoint") or "")
        try:
            found = SEARCHERS[source_id](endpoint, normalized_query, limit, timeout, max_bytes)
            results.extend(found)
            source_reports.append({"source_id": source_id, "status": "pass", "result_count": len(found), "error": None})
        except Exception as exc:
            source_reports.append({"source_id": source_id, "status": "fail", "result_count": 0, "error": f"{type(exc).__name__}: {str(exc)[:300]}"})

    success_count = sum(row["status"] == "pass" for row in source_reports)
    return {
        "schema_version": "global-knowledge-search-report-v1",
        "status": "pass" if success_count else "fail",
        "query": normalized_query,
        "source_count": len(source_reports),
        "successful_source_count": success_count,
        "failed_source_count": len(source_reports) - success_count,
        "result_count": len(results),
        "sources": source_reports,
        "results": results,
        "safety": {
            "metadata_search_only": True,
            "provider_declared_access_metadata_only": True,
            "result_files_fetched": False,
            "shadow_sources_live_searched": False,
            "access_controls_bypassed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--max-bytes", type=int, default=2_000_000)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--enforce", action="store_true")
    args = parser.parse_args()

    report = run_search(
        registry_mod.load_registry(args.registry),
        query=args.query,
        source_ids=args.source or None,
        limit=args.limit,
        timeout=min(max(args.timeout, 5), 30),
        max_bytes=min(max(args.max_bytes, 100_000), 5_000_000),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: report.get(k) for k in ("status", "source_count", "successful_source_count", "failed_source_count", "result_count")}, ensure_ascii=False))
    if args.enforce and report.get("status") != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
