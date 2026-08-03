#!/usr/bin/env python3
"""Bounded read-only runtime for global research and policy intelligence sources."""
from __future__ import annotations

import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

import requests

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from managed_provider_runtime import (  # noqa: E402
    bounded_int,
    bytes_sha,
    finish_execution,
    load_json,
    provider_row,
    run_cli,
    utc_now,
    validate_ticket,
)

SCHEMA_PATH = HERE / "ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"
SOURCE_INVENTORY_PATH = HERE / "source-inventory.json"
THINK_TANK_SOURCES_PATH = HERE / "think-tank-sources.json"

TOKEN_RE = re.compile(r"^[A-Za-z0-9._:/-]{1,300}$")
DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
ARXIV_ID_RE = re.compile(r"^[A-Za-z0-9./-]{1,40}$")
CIK_RE = re.compile(r"^[0-9]{1,10}$")


def clean_text(value: Any, name: str, maximum: int) -> str:
    text = str(value or "").strip()
    if not text or len(text) > maximum or any(ord(ch) < 32 for ch in text):
        raise ValueError(f"{name} is invalid")
    return text


def optional_text(value: Any, name: str, maximum: int) -> str | None:
    if value in (None, ""):
        return None
    return clean_text(value, name, maximum)


def require_env(name: str, *, email_like: bool = False) -> str:
    value = str(os.getenv(name) or "").strip()
    if not value:
        raise RuntimeError(f"required backend credential is not configured: {name}")
    if len(value) > 4096 or any(ord(ch) < 32 for ch in value):
        raise RuntimeError(f"backend credential is invalid: {name}")
    if email_like and "@" not in value:
        raise RuntimeError(f"{name} must identify the caller and include a contact email")
    return value


def safe_date(value: Any, name: str) -> str | None:
    if value in (None, ""):
        return None
    text = str(value)
    if not DATE_RE.fullmatch(text):
        raise ValueError(f"{name} must be YYYY-MM-DD")
    return text


def strip_tag(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def xml_to_obj(element: ET.Element) -> Any:
    children = list(element)
    attrs = {strip_tag(k): v for k, v in element.attrib.items()}
    text = (element.text or "").strip()
    if not children:
        if attrs:
            result: dict[str, Any] = {"@attributes": attrs}
            if text:
                result["#text"] = text
            return result
        return text
    grouped: dict[str, list[Any]] = {}
    for child in children:
        grouped.setdefault(strip_tag(child.tag), []).append(xml_to_obj(child))
    result = {
        key: values[0] if len(values) == 1 else values
        for key, values in grouped.items()
    }
    if attrs:
        result["@attributes"] = attrs
    if text:
        result["#text"] = text
    return result


def parse_arxiv(raw: bytes) -> dict[str, Any]:
    root = ET.fromstring(raw)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries: list[dict[str, Any]] = []
    for entry in root.findall("atom:entry", ns):
        authors = [
            (node.findtext("atom:name", default="", namespaces=ns) or "").strip()
            for node in entry.findall("atom:author", ns)
        ]
        links = []
        for link in entry.findall("atom:link", ns):
            links.append(
                {
                    "href": link.attrib.get("href", ""),
                    "rel": link.attrib.get("rel", ""),
                    "type": link.attrib.get("type", ""),
                    "title": link.attrib.get("title", ""),
                }
            )
        categories = [
            node.attrib.get("term", "")
            for node in entry.findall("atom:category", ns)
            if node.attrib.get("term")
        ]
        entries.append(
            {
                "id": (entry.findtext("atom:id", default="", namespaces=ns) or "").strip(),
                "title": " ".join(
                    (entry.findtext("atom:title", default="", namespaces=ns) or "").split()
                ),
                "summary": " ".join(
                    (entry.findtext("atom:summary", default="", namespaces=ns) or "").split()
                ),
                "published": (
                    entry.findtext("atom:published", default="", namespaces=ns) or ""
                ).strip(),
                "updated": (
                    entry.findtext("atom:updated", default="", namespaces=ns) or ""
                ).strip(),
                "authors": [author for author in authors if author],
                "categories": categories,
                "links": links,
            }
        )
    return {
        "feed_id": (root.findtext("atom:id", default="", namespaces=ns) or "").strip(),
        "title": " ".join(
            (root.findtext("atom:title", default="", namespaces=ns) or "").split()
        ),
        "updated": (root.findtext("atom:updated", default="", namespaces=ns) or "").strip(),
        "entry_count": len(entries),
        "entries": entries,
    }


def fixture_bytes(kind: str) -> bytes:
    if kind == "arxiv":
        return b"""<?xml version='1.0' encoding='UTF-8'?>
<feed xmlns='http://www.w3.org/2005/Atom'>
  <id>https://arxiv.org/api/test</id><title>Fixture</title><updated>2026-08-03T00:00:00Z</updated>
  <entry><id>https://arxiv.org/abs/2608.00001</id><title>China fixture report</title>
  <summary>Fixture abstract.</summary><published>2026-08-03T00:00:00Z</published>
  <updated>2026-08-03T00:00:00Z</updated><author><name>Test Author</name></author>
  <category term='econ.GN'/><link href='https://arxiv.org/pdf/2608.00001' rel='related' type='application/pdf'/></entry>
</feed>"""
    if kind == "oai":
        return b"""<?xml version='1.0' encoding='UTF-8'?>
<OAI-PMH xmlns='http://www.openarchives.org/OAI/2.0/'>
  <responseDate>2026-08-03T00:00:00Z</responseDate>
  <request verb='Identify'>https://digitallibrary.un.org/oai2d</request>
  <Identify><repositoryName>United Nations Digital Library</repositoryName><baseURL>https://digitallibrary.un.org/oai2d</baseURL></Identify>
</OAI-PMH>"""
    return json.dumps(
        {"status": "fixture", "results": [{"id": "fixture-1", "title": "Fixture record"}]},
        ensure_ascii=False,
    ).encode("utf-8")


def think_tank_catalog(parameters: Mapping[str, Any]) -> dict[str, Any]:
    catalog = load_json(THINK_TANK_SOURCES_PATH)
    region = str(parameters.get("region") or "all")
    topic = str(parameters.get("topic") or "all")
    sources = []
    for row in catalog["sources"]:
        if region != "all" and row["region"] != region:
            continue
        if topic != "all" and topic not in row["topics"]:
            continue
        sources.append(row)
    return {
        "schema_version": catalog["schema_version"],
        "updated_at": catalog["updated_at"],
        "policy": catalog["policy"],
        "region": region,
        "topic": topic,
        "source_count": len(sources),
        "sources": sources,
    }


def build_remote_request(
    operation: str, parameters: Mapping[str, Any]
) -> tuple[str, list[tuple[str, str]], dict[str, str], str, list[str]]:
    headers = {
        "Accept": "application/json, application/atom+xml, application/xml;q=0.9, text/xml;q=0.8",
        "User-Agent": "evidence-data-center-global-research/1.0",
    }
    query: list[tuple[str, str]] = []
    kind = "json"
    credentials: list[str] = []

    if operation == "search-arxiv":
        query_text = clean_text(parameters.get("query"), "query", 500)
        query = [
            ("search_query", query_text),
            (
                "start",
                str(
                    bounded_int(
                        parameters.get("start"), default=0, minimum=0, maximum=10000, name="start"
                    )
                ),
            ),
            (
                "max_results",
                str(
                    bounded_int(
                        parameters.get("max_results"),
                        default=20,
                        minimum=1,
                        maximum=100,
                        name="max_results",
                    )
                ),
            ),
            ("sortBy", str(parameters.get("sort_by") or "relevance")),
            ("sortOrder", str(parameters.get("sort_order") or "descending")),
        ]
        return "https://export.arxiv.org/api/query", query, headers, "arxiv", credentials

    if operation == "get-arxiv-entry":
        ids = parameters.get("ids")
        if not isinstance(ids, list) or not 1 <= len(ids) <= 20:
            raise ValueError("ids must contain 1 to 20 arXiv identifiers")
        normalized = [str(item) for item in ids]
        if len(normalized) != len(set(normalized)) or any(
            not ARXIV_ID_RE.fullmatch(item) for item in normalized
        ):
            raise ValueError("ids contains an invalid or duplicate arXiv identifier")
        return (
            "https://export.arxiv.org/api/query",
            [("id_list", ",".join(normalized)), ("max_results", str(len(normalized)))],
            headers,
            "arxiv",
            credentials,
        )

    if operation == "identify-un-digital-library":
        return (
            "https://digitallibrary.un.org/oai2d",
            [("verb", "Identify")],
            headers,
            "oai",
            credentials,
        )

    if operation == "list-un-digital-library-records":
        token = optional_text(parameters.get("resumption_token"), "resumption_token", 500)
        query = [("verb", "ListRecords")]
        if token:
            query.append(("resumptionToken", token))
        else:
            query.append(("metadataPrefix", str(parameters.get("metadata_prefix") or "oai_dc")))
            for source, target in (("set", "set"), ("from", "from"), ("until", "until")):
                value = parameters.get(source)
                if value not in (None, ""):
                    if source in {"from", "until"}:
                        query.append((target, safe_date(value, source) or ""))
                    else:
                        query.append((target, clean_text(value, source, 200)))
        return "https://digitallibrary.un.org/oai2d", query, headers, "oai", credentials

    if operation == "get-un-digital-library-record":
        identifier = clean_text(parameters.get("identifier"), "identifier", 300)
        return (
            "https://digitallibrary.un.org/oai2d",
            [
                ("verb", "GetRecord"),
                ("identifier", identifier),
                ("metadataPrefix", str(parameters.get("metadata_prefix") or "oai_dc")),
            ],
            headers,
            "oai",
            credentials,
        )

    if operation in {"get-sec-submissions", "get-sec-company-facts"}:
        cik = str(parameters.get("cik") or "")
        if not CIK_RE.fullmatch(cik):
            raise ValueError("cik must contain 1 to 10 digits")
        cik = cik.zfill(10)
        user_agent = require_env("SEC_USER_AGENT", email_like=True)
        headers["User-Agent"] = user_agent
        credentials.append("SEC_USER_AGENT")
        path = (
            f"/submissions/CIK{cik}.json"
            if operation == "get-sec-submissions"
            else f"/api/xbrl/companyfacts/CIK{cik}.json"
        )
        return f"https://data.sec.gov{path}", [], headers, kind, credentials

    if operation == "get-sec-xbrl-frame":
        taxonomy = str(parameters.get("taxonomy") or "")
        if taxonomy not in {"us-gaap", "dei", "ifrs-full"}:
            raise ValueError("taxonomy is invalid")
        tag = clean_text(parameters.get("tag"), "tag", 100)
        unit = clean_text(parameters.get("unit"), "unit", 40)
        period = clean_text(parameters.get("period"), "period", 20)
        if not re.fullmatch(r"^[A-Za-z][A-Za-z0-9]{1,99}$", tag):
            raise ValueError("tag is invalid")
        if not re.fullmatch(r"^[A-Za-z0-9-]{1,40}$", unit):
            raise ValueError("unit is invalid")
        if not re.fullmatch(r"^CY[0-9]{4}(Q[1-4])?I?$", period):
            raise ValueError("period is invalid")
        user_agent = require_env("SEC_USER_AGENT", email_like=True)
        headers["User-Agent"] = user_agent
        credentials.append("SEC_USER_AGENT")
        return (
            f"https://data.sec.gov/api/xbrl/frames/{taxonomy}/{tag}/{unit}/{period}.json",
            [],
            headers,
            kind,
            credentials,
        )

    if operation in {"list-congress-bills", "list-congress-hearings", "get-congress-crs-report"}:
        api_key = require_env("CONGRESS_API_KEY")
        credentials.append("CONGRESS_API_KEY")
        query = [("api_key", api_key), ("format", "json")]
        if operation == "list-congress-bills":
            path = "/v3/bill"
            for source, target in (
                ("congress", "congress"),
                ("bill_type", "billType"),
                ("from_datetime", "fromDateTime"),
                ("to_datetime", "toDateTime"),
            ):
                if parameters.get(source) not in (None, ""):
                    query.append((target, str(parameters[source])))
            query.extend(
                [
                    (
                        "limit",
                        str(
                            bounded_int(
                                parameters.get("limit"), default=20, minimum=1, maximum=100, name="limit"
                            )
                        ),
                    ),
                    (
                        "offset",
                        str(
                            bounded_int(
                                parameters.get("offset"), default=0, minimum=0, maximum=10000, name="offset"
                            )
                        ),
                    ),
                ]
            )
        elif operation == "list-congress-hearings":
            path = "/v3/hearing"
            if parameters.get("congress") not in (None, ""):
                query.append(("congress", str(parameters["congress"])))
            if parameters.get("chamber") not in (None, ""):
                query.append(("chamber", str(parameters["chamber"])))
            query.extend(
                [
                    (
                        "limit",
                        str(
                            bounded_int(
                                parameters.get("limit"), default=20, minimum=1, maximum=100, name="limit"
                            )
                        ),
                    ),
                    (
                        "offset",
                        str(
                            bounded_int(
                                parameters.get("offset"), default=0, minimum=0, maximum=10000, name="offset"
                            )
                        ),
                    ),
                ]
            )
        else:
            report_number = clean_text(parameters.get("report_number"), "report_number", 24)
            if not re.fullmatch(r"^[A-Za-z]{1,4}[0-9-]{1,20}$", report_number):
                raise ValueError("report_number is invalid")
            path = f"/v3/crsreport/{report_number}"
        return f"https://api.congress.gov{path}", query, headers, kind, credentials

    if operation in {"search-courtlistener", "get-courtlistener-opinion"}:
        token = require_env("COURTLISTENER_API_TOKEN")
        headers["Authorization"] = f"Token {token}"
        credentials.append("COURTLISTENER_API_TOKEN")
        if operation == "search-courtlistener":
            query = [("q", clean_text(parameters.get("query"), "query", 500))]
            if parameters.get("type") not in (None, ""):
                query.append(("type", str(parameters["type"])))
            if parameters.get("order_by") not in (None, ""):
                query.append(("order_by", str(parameters["order_by"])))
            query.append(
                (
                    "page",
                    str(
                        bounded_int(
                            parameters.get("page"), default=1, minimum=1, maximum=100, name="page"
                        )
                    ),
                )
            )
            path = "/api/rest/v4/search/"
        else:
            opinion_id = bounded_int(
                parameters.get("opinion_id"),
                default=0,
                minimum=1,
                maximum=999999999,
                name="opinion_id",
            )
            path = f"/api/rest/v4/opinions/{opinion_id}/"
        return f"https://www.courtlistener.com{path}", query, headers, kind, credentials

    if operation in {"search-nasdaq-data-link", "get-nasdaq-dataset"}:
        api_key = require_env("NASDAQ_DATA_LINK_API_KEY")
        credentials.append("NASDAQ_DATA_LINK_API_KEY")
        query = [("api_key", api_key)]
        if operation == "search-nasdaq-data-link":
            query.extend(
                [
                    ("query", clean_text(parameters.get("query"), "query", 300)),
                    (
                        "page",
                        str(
                            bounded_int(
                                parameters.get("page"), default=1, minimum=1, maximum=100, name="page"
                            )
                        ),
                    ),
                    (
                        "per_page",
                        str(
                            bounded_int(
                                parameters.get("per_page"), default=20, minimum=1, maximum=100, name="per_page"
                            )
                        ),
                    ),
                ]
            )
            path = "/api/v3/datasets.json"
        else:
            database_code = clean_text(parameters.get("database_code"), "database_code", 30)
            dataset_code = clean_text(parameters.get("dataset_code"), "dataset_code", 80)
            if not re.fullmatch(r"^[A-Za-z0-9_-]{1,30}$", database_code):
                raise ValueError("database_code is invalid")
            if not re.fullmatch(r"^[A-Za-z0-9_.-]{1,80}$", dataset_code):
                raise ValueError("dataset_code is invalid")
            path = f"/api/v3/datasets/{database_code}/{dataset_code}.json"
            for source in ("start_date", "end_date"):
                value = safe_date(parameters.get(source), source)
                if value:
                    query.append((source, value))
            for source in ("rows", "order", "collapse", "transform"):
                if parameters.get(source) not in (None, ""):
                    query.append((source, str(parameters[source])))
        return f"https://data.nasdaq.com{path}", query, headers, kind, credentials

    if operation in {"finnhub-company-news", "finnhub-transcripts-list", "finnhub-transcript"}:
        api_key = require_env("FINNHUB_API_KEY")
        headers["X-Finnhub-Token"] = api_key
        credentials.append("FINNHUB_API_KEY")
        if operation == "finnhub-company-news":
            symbol = clean_text(parameters.get("symbol"), "symbol", 30)
            start = safe_date(parameters.get("from"), "from")
            end = safe_date(parameters.get("to"), "to")
            if not start or not end or start > end:
                raise ValueError("from and to must be a valid ascending date range")
            path = "/api/v1/company-news"
            query = [("symbol", symbol), ("from", start), ("to", end)]
        elif operation == "finnhub-transcripts-list":
            path = "/api/v1/stock/transcripts/list"
            query = [("symbol", clean_text(parameters.get("symbol"), "symbol", 30))]
        else:
            path = "/api/v1/stock/transcripts"
            query = [
                (
                    "id",
                    clean_text(parameters.get("transcript_id"), "transcript_id", 120),
                )
            ]
        return f"https://finnhub.io{path}", query, headers, kind, credentials

    if operation in {"scopus-search", "scopus-abstract"}:
        api_key = require_env("SCOPUS_API_KEY")
        headers["X-ELS-APIKey"] = api_key
        inst_token = str(os.getenv("SCOPUS_INST_TOKEN") or "").strip()
        if inst_token:
            headers["X-ELS-Insttoken"] = inst_token
        credentials.append("SCOPUS_API_KEY")
        if inst_token:
            credentials.append("SCOPUS_INST_TOKEN")
        if operation == "scopus-search":
            path = "/content/search/scopus"
            query = [
                ("query", clean_text(parameters.get("query"), "query", 1000)),
                (
                    "start",
                    str(
                        bounded_int(
                            parameters.get("start"), default=0, minimum=0, maximum=5000, name="start"
                        )
                    ),
                ),
                (
                    "count",
                    str(
                        bounded_int(
                            parameters.get("count"), default=25, minimum=1, maximum=100, name="count"
                        )
                    ),
                ),
            ]
            for source in ("sort", "view"):
                if parameters.get(source) not in (None, ""):
                    query.append((source, str(parameters[source])))
        else:
            eid = clean_text(parameters.get("eid"), "eid", 80)
            if not TOKEN_RE.fullmatch(eid):
                raise ValueError("eid is invalid")
            path = f"/content/abstract/eid/{eid}"
            query = [("view", str(parameters.get("view") or "META_ABS"))]
        return f"https://api.elsevier.com{path}", query, headers, kind, credentials

    raise ValueError(f"unsupported operation: {operation}")


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(
        acceptance.get("timeout_seconds"), default=30, minimum=5, maximum=120, name="timeout_seconds"
    )
    max_bytes = bounded_int(
        acceptance.get("max_response_bytes"),
        default=10000000,
        minimum=1024,
        maximum=20000000,
        name="max_response_bytes",
    )
    started_at, started_perf = utc_now(), time.perf_counter()
    status = "INTEL_GLOBAL_RESEARCH_FAILED"
    failure: Mapping[str, Any] | None = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "network_used": False,
        "fixture_mode": os.getenv("GLOBAL_RESEARCH_FIXTURE_MODE") == "1",
        "requests_per_ticket_max": 1,
        "automatic_retry": False,
        "automatic_pagination": False,
        "secret_used": False,
        "secret_values_exposed": False,
        "model_calls": 0,
    }
    try:
        if operation == "catalog-capabilities":
            if parameters:
                raise ValueError("catalog-capabilities accepts no parameters")
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        elif operation == "source-inventory":
            if parameters:
                raise ValueError("source-inventory accepts no parameters")
            snapshot = load_json(SOURCE_INVENTORY_PATH)
        elif operation == "think-tank-source-catalog":
            snapshot = think_tank_catalog(parameters)
        else:
            url, query, headers, kind, credentials = build_remote_request(operation, parameters)
            parsed_url = urlparse(url)
            fixture_mode = metadata["fixture_mode"]
            if fixture_mode:
                raw = fixture_bytes(kind)
                http_status = 200
                content_type = (
                    "application/atom+xml"
                    if kind == "arxiv"
                    else "application/xml"
                    if kind == "oai"
                    else "application/json"
                )
            else:
                response = requests.get(
                    url,
                    params=query,
                    headers=headers,
                    timeout=timeout,
                    allow_redirects=False,
                )
                raw = bytes(response.content or b"")
                http_status = response.status_code
                content_type = response.headers.get("Content-Type", "")
                metadata["upstream_called"] = True
                metadata["network_used"] = True
                if not response.ok:
                    raise RuntimeError(f"upstream HTTP {response.status_code}")
            if len(raw) > max_bytes:
                raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
            if kind == "arxiv":
                payload: Any = parse_arxiv(raw)
            elif kind == "oai":
                payload = {strip_tag(ET.fromstring(raw).tag): xml_to_obj(ET.fromstring(raw))}
            else:
                try:
                    payload = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise RuntimeError("upstream returned invalid JSON") from exc
            stored = (
                json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
            ).encode("utf-8")
            if len(stored) > max_bytes:
                raise RuntimeError("normalized response exceeds max_response_bytes")
            (output_dir / "response.json").write_bytes(stored)
            row_count = (
                len(payload.get("entries") or [])
                if isinstance(payload, Mapping) and isinstance(payload.get("entries"), list)
                else len(payload)
                if isinstance(payload, list)
                else 1
            )
            snapshot = {
                "provider": "global-research-intelligence",
                "operation": operation,
                "row_count": row_count,
                "data": payload,
            }
            metadata.update(
                {
                    "api_host": parsed_url.hostname,
                    "request_path": parsed_url.path,
                    "query_parameter_names": sorted(
                        {key for key, _ in query if key not in {"api_key", "token"}}
                    ),
                    "credential_environment_variable_names": credentials,
                    "secret_used": bool(credentials),
                    "http_status": http_status,
                    "content_type": content_type,
                    "response_bytes_raw": len(raw),
                    "response_bytes": len(stored),
                    "response_sha256": bytes_sha(stored),
                    "row_count": row_count,
                }
            )
        status = "INTEL_GLOBAL_RESEARCH_COMPLETED"
    except Exception as exc:
        failure = {"type": type(exc).__name__, "message": str(exc)[:2000]}
    return finish_execution(
        ticket=ticket,
        output_dir=output_dir,
        status=status,
        snapshot=snapshot,
        metadata=metadata,
        failure=failure,
        started_at=started_at,
        started_perf=started_perf,
        schema_prefix="global-research-intelligence",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-global-research]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="global-research-intelligence-ticket-status-v1",
            display_name="Global Research Intelligence",
        )
    )
