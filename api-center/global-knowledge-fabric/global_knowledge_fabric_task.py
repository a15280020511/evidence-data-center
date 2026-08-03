#!/usr/bin/env python3
"""Bounded runtime for third-wave global knowledge fabric sources."""
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
USER_AGENT = "evidence-data-center-global-knowledge-fabric/1.0"


def safe_text(value: Any, name: str, maximum: int) -> str:
    rendered = str(value or "").strip()
    if not rendered or len(rendered) > maximum or any(ord(ch) < 32 for ch in rendered):
        raise ValueError(f"{name} is invalid")
    return rendered


def safe_sparql_literal(value: Any) -> str:
    text = safe_text(value, "query", 200)
    return text.replace("\\", "\\\\").replace('"', '\\"')


def backend_credential(name: str, *, required: bool) -> str:
    value = str(os.getenv(name) or "").strip()
    if required and not value:
        raise RuntimeError(f"required backend credential is not configured: {name}")
    if len(value) > 4096 or any(ord(ch) < 32 for ch in value):
        raise RuntimeError(f"invalid backend credential: {name}")
    return value


def source_map() -> dict[str, Mapping[str, Any]]:
    rows = load_json(MATRIX_PATH).get("sources")
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
    if source_id == "ror":
        headers["Client-Id"] = value
    elif source_id == "orcid":
        headers["Authorization"] = f"Bearer {value}"
    elif source_id in {"regulations-gov", "data-gov"}:
        headers["X-Api-Key"] = value
    else:
        raise RuntimeError(f"credential injection is not configured for {source_id}")
    return headers, query, used


def common_headers(accept: str = "application/json") -> dict[str, str]:
    return {"Accept": accept, "User-Agent": USER_AGENT}


def query_and_limit(parameters: Mapping[str, Any]) -> tuple[str, int]:
    return (
        safe_text(parameters.get("query"), "query", 500),
        bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=50, name="limit"),
    )


def build_entity_search(row: Mapping[str, Any], parameters: Mapping[str, Any]):
    source_id = str(row["source_id"])
    term, limit = query_and_limit(parameters)
    headers, query, credentials = credentials_for(row)
    headers.update(common_headers())
    if source_id == "ror":
        url = "https://api.ror.org/v2/organizations"
        query += [("query", term), ("page", "1")]
    elif source_id == "orcid":
        url = "https://pub.orcid.org/v3.0/search/"
        headers["Accept"] = "application/vnd.orcid+json"
        query += [("q", term), ("start", "0"), ("rows", str(limit))]
    elif source_id == "dblp-author":
        url = "https://dblp.org/search/author/api"
        query += [("q", term), ("format", "json"), ("h", str(limit)), ("f", "0")]
    else:
        raise ValueError("unsupported entity source")
    return "GET", url, headers, query, None, credentials


def build_scholarly_search(row: Mapping[str, Any], parameters: Mapping[str, Any]):
    source_id = str(row["source_id"])
    term, limit = query_and_limit(parameters)
    headers = common_headers()
    query: list[tuple[str, str]] = []
    if source_id == "dblp-publication":
        url = "https://dblp.org/search/publ/api"
        query += [("q", term), ("format", "json"), ("h", str(limit)), ("f", "0")]
    elif source_id == "dblp-venue":
        url = "https://dblp.org/search/venue/api"
        query += [("q", term), ("format", "json"), ("h", str(limit)), ("f", "0")]
    else:
        raise ValueError("unsupported scholarly source")
    return "GET", url, headers, query, None, []


def build_dataset_search(row: Mapping[str, Any], parameters: Mapping[str, Any]):
    source_id = str(row["source_id"])
    term, limit = query_and_limit(parameters)
    headers = common_headers()
    if source_id == "harvard-dataverse":
        return "GET", "https://dataverse.harvard.edu/api/search", headers, [
            ("q", term), ("type", "dataset"), ("per_page", str(limit)), ("start", "0"),
        ], None, []
    if source_id == "openml":
        safe_name = quote(term, safe="")
        return "GET", f"https://www.openml.org/api/v1/json/data/list/data_name/{safe_name}/limit/{limit}", headers, [], None, []
    raise ValueError("unsupported dataset source")


def build_government_search(row: Mapping[str, Any], parameters: Mapping[str, Any]):
    source_id = str(row["source_id"])
    term, limit = query_and_limit(parameters)
    headers, query, credentials = credentials_for(row)
    headers.update(common_headers())
    if source_id == "grants-gov":
        return "POST", "https://api.grants.gov/v1/api/search2", headers, [], {"keyword": term, "rows": limit}, []
    if source_id == "regulations-gov":
        return "GET", "https://api.regulations.gov/v4/documents", headers, [
            ("filter[searchTerm]", term), ("page[size]", str(min(limit, 250))), ("sort", "-postedDate"),
        ], None, credentials
    if source_id == "data-gov":
        return "GET", "https://api.gsa.gov/technology/datagov/v4/search", headers, [
            ("q", term), ("per_page", str(limit)), ("sort", "relevance"),
        ], None, credentials
    if source_id == "eu-cellar":
        literal = safe_sparql_literal(term)
        sparql = (
            "PREFIX cdm: <http://publications.europa.eu/ontology/cdm#> "
            "PREFIX dc: <http://purl.org/dc/elements/1.1/> "
            "SELECT DISTINCT ?work ?title ?date WHERE { "
            "?work a cdm:work . OPTIONAL { ?work dc:title ?title . } "
            "OPTIONAL { ?work cdm:work_date_document ?date . } "
            f'FILTER(BOUND(?title) && CONTAINS(LCASE(STR(?title)), LCASE("{literal}"))) '
            f"}} LIMIT {limit}"
        )
        headers["Accept"] = "application/sparql-results+json"
        return "GET", "https://publications.europa.eu/webapi/rdf/sparql", headers, [
            ("query", sparql), ("format", "application/sparql-results+json"),
        ], None, []
    raise ValueError("unsupported government source")


def build_science_search(row: Mapping[str, Any], parameters: Mapping[str, Any]):
    source_id = str(row["source_id"])
    term, limit = query_and_limit(parameters)
    headers = common_headers()
    if source_id == "rcsb-pdb":
        body = {
            "query": {"type": "terminal", "service": "full_text", "parameters": {"value": term}},
            "return_type": "entry",
            "request_options": {"paginate": {"start": 0, "rows": limit}},
        }
        return "POST", "https://search.rcsb.org/rcsbsearch/v2/query", headers, [], body, []
    if source_id == "uniprot":
        return "GET", "https://rest.uniprot.org/uniprotkb/search", headers, [
            ("query", term), ("format", "json"), ("size", str(limit)),
        ], None, []
    if source_id == "chembl":
        return "GET", "https://www.ebi.ac.uk/chembl/api/data/molecule.json", headers, [
            ("pref_name__icontains", term), ("limit", str(limit)), ("offset", "0"),
        ], None, []
    raise ValueError("unsupported science source")


def build_standards_search(row: Mapping[str, Any], parameters: Mapping[str, Any]):
    term, limit = query_and_limit(parameters)
    return "GET", "https://datatracker.ietf.org/api/v1/doc/document/", common_headers(), [
        ("name__contains", term), ("limit", str(limit)), ("offset", "0"), ("format", "json"),
    ], None, []


def record_identifier(source_id: str, raw: Any) -> str:
    value = safe_text(raw, "record_id", 240)
    patterns = {
        "ror": r"^[0-9a-z]{9}$",
        "orcid": r"^[0-9X]{4}-[0-9X]{4}-[0-9X]{4}-[0-9X]{4}$",
        "harvard-dataverse": r"^[0-9]{1,12}$",
        "openml": r"^[0-9]{1,12}$",
        "grants-gov": r"^[0-9]{1,12}$",
        "regulations-gov": r"^[A-Za-z0-9._-]{3,200}$",
        "data-gov": r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
        "rcsb-pdb": r"^[A-Za-z0-9]{4}$",
        "uniprot": r"^[A-Za-z0-9]{6,20}$",
        "chembl": r"^CHEMBL[0-9]{1,12}$",
    }
    if not re.fullmatch(patterns[source_id], value):
        raise ValueError(f"record_id is invalid for {source_id}")
    return value


def build_record(row: Mapping[str, Any], parameters: Mapping[str, Any]):
    source_id = str(row["source_id"])
    record_id = record_identifier(source_id, parameters.get("record_id"))
    headers, query, credentials = credentials_for(row)
    headers.update(common_headers())
    method = "GET"
    body = None
    if source_id == "ror":
        url = f"https://api.ror.org/v2/organizations/{record_id}"
    elif source_id == "orcid":
        url = f"https://pub.orcid.org/v3.0/{record_id}/record"
        headers["Accept"] = "application/vnd.orcid+json"
    elif source_id == "harvard-dataverse":
        url = f"https://dataverse.harvard.edu/api/datasets/{record_id}"
    elif source_id == "openml":
        url = f"https://www.openml.org/api/v1/json/data/{record_id}"
    elif source_id == "grants-gov":
        method = "POST"
        url = "https://api.grants.gov/v1/api/fetchOpportunity"
        body = {"opportunityId": int(record_id)}
    elif source_id == "regulations-gov":
        url = f"https://api.regulations.gov/v4/documents/{quote(record_id, safe='._-')}"
    elif source_id == "data-gov":
        url = f"https://api.gsa.gov/technology/datagov/v4/harvest_record/{record_id}"
    elif source_id == "rcsb-pdb":
        url = f"https://data.rcsb.org/rest/v1/core/entry/{record_id.upper()}"
    elif source_id == "uniprot":
        url = f"https://rest.uniprot.org/uniprotkb/{record_id}.json"
    elif source_id == "chembl":
        url = f"https://www.ebi.ac.uk/chembl/api/data/molecule/{record_id}.json"
    else:
        raise ValueError("unsupported record source")
    return method, url, headers, query, body, credentials


def build(operation: str, parameters: Mapping[str, Any]):
    if operation == "entity-search":
        row = source_for(parameters.get("source_id"), operation)
        return row, build_entity_search(row, parameters)
    if operation == "scholarly-search":
        row = source_for(parameters.get("source_id"), operation)
        return row, build_scholarly_search(row, parameters)
    if operation == "dataset-search":
        row = source_for(parameters.get("source_id"), operation)
        return row, build_dataset_search(row, parameters)
    if operation == "government-search":
        row = source_for(parameters.get("source_id"), operation)
        return row, build_government_search(row, parameters)
    if operation == "science-search":
        row = source_for(parameters.get("source_id"), operation)
        return row, build_science_search(row, parameters)
    if operation == "record-get":
        row = source_for(parameters.get("source_id"), operation)
        return row, build_record(row, parameters)
    if operation == "standards-search":
        row = source_for(parameters.get("source_id"), operation)
        return row, build_standards_search(row, parameters)
    raise ValueError(f"unsupported operation: {operation}")


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    started_at = utc_now()
    started_perf = time.perf_counter()
    fixture = os.getenv("GLOBAL_KNOWLEDGE_FABRIC_FIXTURE_MODE") == "1"
    snapshot = None
    failure = None
    status = "INTEL_KNOWLEDGE_FABRIC_FAILED"
    metadata: dict[str, Any] = {
        "fixture_mode": fixture, "network_used": False, "upstream_called": False,
        "request_count": 0, "credential_names": [], "automatic_pagination_used": False,
        "automatic_retry_used": False, "redirects_followed": False,
        "secret_values_exposed": False, "model_calls": 0,
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
                "fixture": True, "operation": operation, "source_id": row["source_id"],
                "method": method, "origin": f"{parsed.scheme}://{parsed.netloc}",
                "path_template_verified": True, "query_names": [name for name, _ in query],
                "body_present": body is not None, "credential_names": credentials,
                "authorization_header_present": "Authorization" in headers,
            }
        else:
            row, request = build(operation, ticket.get("parameters") or {})
            method, url, headers, query, body, credentials = request
            acceptance = ticket.get("acceptance") or {}
            timeout = bounded_int(acceptance.get("timeout_seconds"), default=45, minimum=5, maximum=75, name="timeout_seconds")
            max_bytes = bounded_int(acceptance.get("max_response_bytes"), default=5000000, minimum=1024, maximum=5000000, name="max_response_bytes")
            response = requests.request(method, url, headers=headers, params=query, json=body, timeout=timeout, allow_redirects=False)
            raw = response.content
            metadata.update({
                "network_used": True, "upstream_called": True, "request_count": 1,
                "source_id": row["source_id"], "source_name": row["name"], "source_category": row["category"],
                "credential_names": credentials, "http_status": response.status_code,
                "response_bytes": len(raw), "response_sha256": bytes_sha(raw),
                "request_origin": f"{urlsplit(url).scheme}://{urlsplit(url).netloc}",
                "license_policy": row["license_policy"], "cost": row["cost"],
            })
            if 300 <= response.status_code < 400:
                raise RuntimeError("redirects are forbidden")
            response.raise_for_status()
            if len(raw) > max_bytes:
                raise RuntimeError("response exceeds max_response_bytes")
            content_type = response.headers.get("content-type", "").lower()
            if "json" in content_type:
                data: Any = response.json()
            else:
                data = {"content_type": content_type, "text": response.text}
            snapshot = {
                "provider": "global-knowledge-fabric", "operation": operation,
                "source_id": row["source_id"], "source_name": row["name"],
                "license_policy": row["license_policy"], "data": data,
            }
        status = "INTEL_KNOWLEDGE_FABRIC_COMPLETED"
    except Exception as exc:
        failure = {"type": type(exc).__name__, "message": str(exc)[:1500]}
    return finish_execution(
        ticket=ticket, output_dir=output_dir, status=status, snapshot=snapshot,
        metadata=metadata, failure=failure, started_at=started_at,
        started_perf=started_perf, schema_prefix="intel-knowledge-fabric",
    )


def main() -> int:
    return run_cli(
        execute=execute, ticket_prefix="[intel-knowledge-fabric]",
        schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH,
        status_schema="intel-knowledge-fabric-ticket-status-v1",
        display_name="全球知识织网第三波",
    )


if __name__ == "__main__":
    raise SystemExit(main())
