#!/usr/bin/env python3
"""Bounded runtime for second-wave global literature, archive and library sources."""
from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import quote, urlsplit

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
MATRIX_PATH = HERE / "source-access-matrix.json"
USER_AGENT = "evidence-data-center-global-knowledge/1.0"


def safe_text(value: Any, name: str, maximum: int) -> str:
    rendered = str(value or "").strip()
    if not rendered or len(rendered) > maximum or any(ord(ch) < 32 for ch in rendered):
        raise ValueError(f"{name} is invalid")
    return rendered


def backend_credential(name: str, *, required: bool) -> str:
    value = str(os.getenv(name) or "").strip()
    if required and not value:
        raise RuntimeError(f"required backend credential is not configured: {name}")
    if len(value) > 4096 or any(ord(ch) < 32 for ch in value):
        raise RuntimeError(f"invalid backend credential: {name}")
    return value


def source_map() -> dict[str, Mapping[str, Any]]:
    matrix = load_json(MATRIX_PATH)
    rows = matrix.get("sources")
    if not isinstance(rows, list):
        raise RuntimeError("source matrix is invalid")
    return {str(row["source_id"]): row for row in rows if isinstance(row, Mapping)}


def source_for(source_id: Any, operation: str) -> Mapping[str, Any]:
    source_id = safe_text(source_id, "source_id", 80)
    row = source_map().get(source_id)
    if row is None:
        raise ValueError("source_id is not enabled")
    if operation not in (row.get("operations") or []):
        raise ValueError(f"{source_id} does not support {operation}")
    parsed = urlsplit(str(row.get("base_url") or ""))
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError("source registry contains a non-HTTPS endpoint")
    return row


def credentials_for(row: Mapping[str, Any]) -> tuple[dict[str, str], list[tuple[str, str]], list[str]]:
    mode = str(row.get("credential_mode") or "none")
    name = str(row.get("credential_env") or "")
    headers: dict[str, str] = {}
    query: list[tuple[str, str]] = []
    used: list[str] = []
    if mode in {"none", ""}:
        return headers, query, used
    required = mode.startswith("required_")
    value = backend_credential(name, required=required)
    if not value:
        return headers, query, used
    used.append(name)
    source_id = str(row["source_id"])
    if source_id == "google-books":
        query.append(("key", value))
    elif source_id == "bhl":
        query.append(("apikey", value))
    elif source_id == "nara":
        headers["x-api-key"] = value
    elif source_id == "smithsonian":
        query.append(("api_key", value))
    elif source_id == "govinfo":
        query.append(("api_key", value))
    elif source_id == "trove":
        headers["X-API-KEY"] = value
    else:
        raise RuntimeError(f"credential injection is not configured for {source_id}")
    return headers, query, used


def record_identifier(source_id: str, raw: Any) -> str:
    value = safe_text(raw, "record_id", 200)
    patterns = {
        "ukri-gtr": r"^[A-Fa-f0-9-]{36}$",
        "clinicaltrials-gov": r"^NCT[0-9]{8}$",
        "federal-register": r"^[0-9]{2,4}-[0-9]{4,6}$",
        "met-museum": r"^[0-9]{1,12}$",
        "art-institute-chicago": r"^[0-9]{1,12}$",
        "digitalnz": r"^[0-9]{1,20}$",
        "google-books": r"^[A-Za-z0-9_-]{1,80}$",
        "bhl": r"^[0-9]{1,20}$",
        "govinfo": r"^[A-Za-z0-9._-]{1,160}$",
    }
    pattern = patterns.get(source_id)
    if pattern is None or not re.fullmatch(pattern, value):
        raise ValueError(f"record_id is invalid for {source_id}")
    return value


def common_headers(accept: str = "application/json, application/xml;q=0.8, text/xml;q=0.8") -> dict[str, str]:
    return {"Accept": accept, "User-Agent": USER_AGENT}


def build_search(row: Mapping[str, Any], parameters: Mapping[str, Any]):
    source_id = str(row["source_id"])
    query_text = safe_text(parameters.get("query"), "query", 500)
    limit = bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=50, name="limit")
    headers, credential_query, credentials = credentials_for(row)
    headers.update(common_headers())
    method = "GET"
    body = None
    query: list[tuple[str, str]] = list(credential_query)

    if source_id == "theses-fr":
        url = "https://theses.fr/api/v1/recherche/"
        query += [("q", query_text), ("debut", "0"), ("nombre", str(limit))]
    elif source_id == "eric":
        url = "https://api.ies.ed.gov/eric/"
        query += [("search", query_text), ("format", "json"), ("start", "0"), ("rows", str(max(20, limit)))]
    elif source_id == "ukri-gtr":
        url = "https://gtr.ukri.org/api/search/project"
        headers["Accept"] = "application/json"
        query += [("term", query_text), ("page", "1"), ("fetchSize", str(max(25, limit)))]
    elif source_id == "nih-reporter":
        method = "POST"
        url = "https://api.reporter.nih.gov/v2/projects/search"
        body = {
            "criteria": {
                "advanced_text_search": {
                    "operator": "and",
                    "search_field": "all",
                    "search_text": query_text,
                }
            },
            "offset": 0,
            "limit": limit,
            "sort_field": "project_start_date",
            "sort_order": "desc",
        }
    elif source_id == "clinicaltrials-gov":
        url = "https://clinicaltrials.gov/api/v2/studies"
        query += [("query.term", query_text), ("pageSize", str(limit)), ("format", "json"), ("countTotal", "true")]
    elif source_id == "usgs-publications":
        url = "https://pubs.usgs.gov/pubs-services/publication/"
        query += [("q", query_text), ("page_size", str(limit)), ("page_number", "1")]
    elif source_id == "federal-register":
        url = "https://www.federalregister.gov/api/v1/documents.json"
        query += [("conditions[term]", query_text), ("per_page", str(limit)), ("page", "1"), ("order", "newest")]
    elif source_id == "met-museum":
        url = "https://collectionapi.metmuseum.org/public/collection/v1/search"
        query += [("q", query_text), ("hasImages", "true")]
    elif source_id == "art-institute-chicago":
        url = "https://api.artic.edu/api/v1/artworks/search"
        fields = "id,title,date_display,artist_display,place_of_origin,short_description,image_id,is_public_domain,api_link,thumbnail"
        query += [("q", query_text), ("limit", str(limit)), ("page", "1"), ("fields", fields)]
    elif source_id == "digitalnz":
        url = "https://api.digitalnz.org/v3/records.json"
        fields = "id,title,description,creator,date,content_partner,display_collection,category,source_url,rights_url,copyright,is_commercial_use"
        query += [("text", query_text), ("per_page", str(limit)), ("page", "1"), ("fields", fields)]
    elif source_id == "trove":
        url = "https://api.trove.nla.gov.au/v3/result"
        query += [("category", "all"), ("q", query_text), ("n", str(limit)), ("s", "*"), ("encoding", "json"), ("reclevel", "brief")]
    elif source_id == "google-books":
        url = "https://www.googleapis.com/books/v1/volumes"
        query += [("q", query_text), ("maxResults", str(min(limit, 40))), ("startIndex", "0"), ("printType", "all"), ("projection", "lite")]
    elif source_id == "bhl":
        url = "https://www.biodiversitylibrary.org/api3"
        query += [("op", "PublicationSearch"), ("searchterm", query_text), ("searchtype", "F"), ("page", "1"), ("format", "json")]
    elif source_id == "nara":
        url = "https://catalog.archives.gov/api/v2/records/search"
        query += [("q", query_text), ("limit", str(limit)), ("page", "1")]
    elif source_id == "smithsonian":
        url = "https://api.si.edu/openaccess/api/v1.0/search"
        query += [("q", query_text), ("rows", str(limit)), ("start", "0")]
    else:
        raise ValueError(f"unsupported search source: {source_id}")
    return method, url, headers, query, body, credentials


def build_record(row: Mapping[str, Any], parameters: Mapping[str, Any]):
    source_id = str(row["source_id"])
    record_id = record_identifier(source_id, parameters.get("record_id"))
    headers, query, credentials = credentials_for(row)
    headers.update(common_headers())
    method = "GET"
    body = None

    if source_id == "ukri-gtr":
        url = f"https://gtr.ukri.org/gtr/api/projects/{record_id}"
        headers["Accept"] = "application/vnd.rcuk.gtr.json-v7"
    elif source_id == "clinicaltrials-gov":
        url = f"https://clinicaltrials.gov/api/v2/studies/{record_id}"
        query += [("format", "json")]
    elif source_id == "federal-register":
        url = f"https://www.federalregister.gov/api/v1/documents/{record_id}.json"
    elif source_id == "met-museum":
        url = f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{record_id}"
    elif source_id == "art-institute-chicago":
        url = f"https://api.artic.edu/api/v1/artworks/{record_id}"
        query += [("fields", "id,title,date_display,artist_display,place_of_origin,description,short_description,image_id,is_public_domain,api_link")]
    elif source_id == "digitalnz":
        url = f"https://api.digitalnz.org/v3/records/{record_id}.json"
    elif source_id == "google-books":
        url = f"https://www.googleapis.com/books/v1/volumes/{quote(record_id, safe='_-')}"
        query += [("projection", "full")]
    elif source_id == "bhl":
        url = "https://www.biodiversitylibrary.org/api3"
        query += [("op", "GetItemMetadata"), ("id", record_id), ("idtype", "bhl"), ("pages", "f"), ("ocr", "f"), ("parts", "t"), ("format", "json")]
    elif source_id == "govinfo":
        url = f"https://api.govinfo.gov/packages/{record_id}/summary"
    else:
        raise ValueError(f"unsupported record source: {source_id}")
    return method, url, headers, query, body, credentials


NBER_FILES = {
    "reference": "ref.tsv",
    "titles": "title.tsv",
    "abstracts": "abs.tsv",
    "authors": "auths.tsv",
    "dates": "date.tsv",
    "jel": "jel.tsv",
    "programs": "prog.tsv",
    "projects": "proj.tsv",
    "published": "published.tsv",
}


def build(operation: str, parameters: Mapping[str, Any]):
    if operation == "knowledge-search":
        row = source_for(parameters.get("source_id"), operation)
        return row, build_search(row, parameters)
    if operation == "knowledge-record":
        row = source_for(parameters.get("source_id"), operation)
        return row, build_record(row, parameters)
    if operation in {"oai-identify", "oai-list-records", "oai-get-record"}:
        row = source_for(parameters.get("source_id"), operation)
        headers = common_headers("application/xml, text/xml;q=0.9")
        query: list[tuple[str, str]] = []
        if operation == "oai-identify":
            query.append(("verb", "Identify"))
        elif operation == "oai-list-records":
            prefix = safe_text(parameters.get("metadata_prefix"), "metadata_prefix", 64)
            query += [("verb", "ListRecords"), ("metadataPrefix", prefix)]
            if parameters.get("from_date"):
                query.append(("from", safe_text(parameters["from_date"], "from_date", 10)))
            if parameters.get("until_date"):
                query.append(("until", safe_text(parameters["until_date"], "until_date", 10)))
            if parameters.get("set"):
                query.append(("set", safe_text(parameters["set"], "set", 200)))
        else:
            query += [
                ("verb", "GetRecord"),
                ("identifier", safe_text(parameters.get("identifier"), "identifier", 300)),
                ("metadataPrefix", safe_text(parameters.get("metadata_prefix"), "metadata_prefix", 64)),
            ]
        return row, ("GET", str(row["base_url"]), headers, query, None, [])
    if operation == "sru-search":
        row = source_for(parameters.get("source_id"), operation)
        query_text = safe_text(parameters.get("query"), "query", 500)
        limit = bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=50, name="limit")
        schema = str(parameters.get("record_schema") or "MARC21-xml")
        if schema not in {"MARC21-xml", "RDFxml", "oai_dc"}:
            raise ValueError("record_schema is not allowlisted")
        query = [
            ("version", "1.1"),
            ("operation", "searchRetrieve"),
            ("query", query_text),
            ("maximumRecords", str(limit)),
            ("startRecord", "1"),
            ("recordSchema", schema),
        ]
        return row, ("GET", str(row["base_url"]), common_headers("application/xml, text/xml;q=0.9"), query, None, [])
    if operation == "metadata-file-get":
        row = source_for(parameters.get("source_id"), operation)
        dataset = str(parameters.get("dataset") or "")
        filename = NBER_FILES.get(dataset)
        if filename is None:
            raise ValueError("dataset is not allowlisted")
        url = f"https://data.nber.org/nber_paper_chapter_metadata/tsv/{filename}"
        return row, ("GET", url, common_headers("text/tab-separated-values, text/plain;q=0.9"), [], None, [])
    raise ValueError(f"unsupported operation: {operation}")


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    started_at = utc_now()
    started_perf = time.perf_counter()
    fixture = os.getenv("GLOBAL_KNOWLEDGE_FIXTURE_MODE") == "1"
    snapshot = None
    failure = None
    status = "INTEL_KNOWLEDGE_FAILED"
    metadata: dict[str, Any] = {
        "fixture_mode": fixture,
        "network_used": False,
        "upstream_called": False,
        "request_count": 0,
        "credential_names": [],
        "automatic_pagination_used": False,
        "automatic_retry_used": False,
        "redirects_followed": False,
        "secret_values_exposed": False,
        "model_calls": 0,
    }
    try:
        if operation == "catalog-capabilities":
            snapshot = provider_row(CATALOG_PATH)
        elif operation == "source-access-matrix":
            snapshot = load_json(MATRIX_PATH)
        elif fixture:
            row, request = build(operation, ticket.get("parameters") or {})
            method, url, headers, query, body, credentials = request
            parsed = urlsplit(url)
            snapshot = {
                "fixture": True,
                "operation": operation,
                "source_id": row["source_id"],
                "method": method,
                "origin": f"{parsed.scheme}://{parsed.netloc}",
                "path_template_verified": True,
                "query_names": [name for name, _ in query],
                "body_present": body is not None,
                "credential_names": credentials,
                "authorization_header_present": "Authorization" in headers,
            }
        else:
            row, request = build(operation, ticket.get("parameters") or {})
            method, url, headers, query, body, credentials = request
            acceptance = ticket.get("acceptance") or {}
            timeout = bounded_int(acceptance.get("timeout_seconds"), default=60, minimum=5, maximum=90, name="timeout_seconds")
            max_bytes = bounded_int(acceptance.get("max_response_bytes"), default=5000000, minimum=1024, maximum=15000000, name="max_response_bytes")
            response = requests.request(method, url, headers=headers, params=query, json=body, timeout=timeout, allow_redirects=False)
            raw = response.content
            metadata.update({
                "network_used": True,
                "upstream_called": True,
                "request_count": 1,
                "source_id": row["source_id"],
                "source_name": row["name"],
                "source_category": row["category"],
                "credential_names": credentials,
                "http_status": response.status_code,
                "response_bytes": len(raw),
                "response_sha256": bytes_sha(raw),
                "request_origin": f"{urlsplit(url).scheme}://{urlsplit(url).netloc}",
                "license_policy": row["license_policy"],
                "cost": row["cost"],
            })
            if 300 <= response.status_code < 400:
                raise RuntimeError("redirects are forbidden")
            response.raise_for_status()
            if len(raw) > max_bytes:
                raise RuntimeError("response exceeds max_response_bytes")
            content_type = response.headers.get("content-type", "").lower()
            if "json" in content_type:
                data: Any = response.json()
            elif "pdf" in content_type:
                target = output_dir / "source-document.pdf"
                target.write_bytes(raw)
                data = {"content_type": content_type, "artifact_file": target.name}
            else:
                data = {"content_type": content_type, "text": response.text}
            snapshot = {
                "provider": "global-knowledge-archives",
                "operation": operation,
                "source_id": row["source_id"],
                "source_name": row["name"],
                "license_policy": row["license_policy"],
                "data": data,
            }
        status = "INTEL_KNOWLEDGE_COMPLETED"
    except Exception as exc:
        failure = {"type": type(exc).__name__, "message": str(exc)[:1500]}
    return finish_execution(
        ticket=ticket,
        output_dir=output_dir,
        status=status,
        snapshot=snapshot,
        metadata=metadata,
        failure=failure,
        started_at=started_at,
        started_perf=started_perf,
        schema_prefix="intel-knowledge",
    )


def main() -> int:
    return run_cli(
        execute=execute,
        ticket_prefix="[intel-knowledge]",
        schema_path=SCHEMA_PATH,
        catalog_path=CATALOG_PATH,
        status_schema="intel-knowledge-ticket-status-v1",
        display_name="全球文献档案资料库第二波",
    )


if __name__ == "__main__":
    raise SystemExit(main())
