#!/usr/bin/env python3
"""Bounded runtime for global institutional, university and Google public APIs."""
from __future__ import annotations

import json
import os
import re
import sys
import time
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
MATRIX_PATH = HERE / "source-access-matrix.json"
GOOGLE_KEY_ENV = "GOOGLE_PUBLIC_INTELLIGENCE_API_KEY"
USER_AGENT = "evidence-data-center-global-open-apis/1"
LANGUAGES_RE = re.compile(r"^[A-Za-z]{2,3}(?:-[A-Za-z]{2,4})?(?:,[A-Za-z]{2,3}(?:-[A-Za-z]{2,4})?)*$")
RESERVED_QUERY_RE = re.compile(r"[+\-!(){}\[\]^\"~*?:\\/]|\b(?:AND|OR|NOT)\b", re.IGNORECASE)


def safe_text(value: Any, name: str, maximum: int, minimum: int = 1) -> str:
    text = str(value or "").strip()
    if len(text) < minimum or len(text) > maximum or any(ord(ch) < 32 for ch in text):
        raise ValueError(f"{name} is invalid")
    return text


def safe_plain_query(value: Any, name: str = "query") -> str:
    text = safe_text(value, name, 200, 1)
    text = RESERVED_QUERY_RE.sub(" ", text)
    text = " ".join(text.split())
    if len(text) < 1:
        raise ValueError(f"{name} contains no searchable text")
    return text


def google_key() -> str:
    value = str(os.getenv(GOOGLE_KEY_ENV) or "").strip()
    if not value:
        raise RuntimeError(f"required backend credential is not configured: {GOOGLE_KEY_ENV}")
    if not 16 <= len(value) <= 2048 or any(ord(ch) < 33 or ord(ch) > 126 for ch in value):
        raise RuntimeError(f"invalid backend credential: {GOOGLE_KEY_ENV}")
    return value


def build_request(operation: str, parameters: Mapping[str, Any]) -> tuple[str | None, str, list[tuple[str, str]], Mapping[str, Any] | None, str, list[str]]:
    if operation == "catalog-capabilities":
        if parameters:
            raise ValueError("catalog-capabilities accepts no parameters")
        return None, "LOCAL", [], None, "catalog", []
    if operation == "source-access-matrix":
        if parameters:
            raise ValueError("source-access-matrix accepts no parameters")
        return None, "LOCAL", [], None, "matrix", []
    if operation == "google-knowledge-entities":
        query = safe_plain_query(parameters.get("query"))
        limit = bounded_int(parameters.get("limit"), default=5, minimum=1, maximum=10, name="limit")
        params = [("query", query), ("limit", str(limit)), ("indent", "false"), ("key", google_key())]
        languages = str(parameters.get("languages") or "").strip()
        if languages:
            if not LANGUAGES_RE.fullmatch(languages):
                raise ValueError("languages must be a comma-separated language-code list")
            for language in languages.split(","):
                params.append(("languages", language))
        entity_type = str(parameters.get("entity_type") or "").strip()
        if entity_type:
            allowed = {"Person", "Organization", "Corporation", "Place", "Event", "CreativeWork", "Product"}
            if entity_type not in allowed:
                raise ValueError("entity_type is not allowlisted")
            params.append(("types", entity_type))
        return "https://kgsearch.googleapis.com/v1/entities:search", "GET", params, None, "google-kg", [GOOGLE_KEY_ENV]
    if operation == "google-civic-elections":
        if parameters:
            raise ValueError("google-civic-elections accepts no parameters")
        return "https://www.googleapis.com/civicinfo/v2/elections", "GET", [("key", google_key())], None, "google-civic-elections", [GOOGLE_KEY_ENV]
    if operation == "google-civic-divisions":
        query = safe_plain_query(parameters.get("query"))
        return "https://www.googleapis.com/civicinfo/v2/divisions", "GET", [("query", query), ("key", google_key())], None, "google-civic-divisions", [GOOGLE_KEY_ENV]
    if operation == "open-book-search":
        source_id = safe_text(parameters.get("source_id"), "source_id", 10)
        origins = {
            "oapen": "https://library.oapen.org/rest/search",
            "doab": "https://directory.doabooks.org/rest/search",
        }
        if source_id not in origins:
            raise ValueError("source_id is not allowlisted")
        query = safe_plain_query(parameters.get("query"))
        return origins[source_id], "GET", [("query", query), ("expand", "metadata")], None, f"open-book-{source_id}", []
    if operation == "gbif-species-search":
        query = safe_plain_query(parameters.get("query"))
        limit = bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=50, name="limit")
        return "https://api.gbif.org/v1/species/search", "GET", [("q", query), ("limit", str(limit)), ("offset", "0")], None, "gbif-results", []
    if operation == "gbif-occurrence-search":
        taxon_key = bounded_int(parameters.get("taxon_key"), default=0, minimum=1, maximum=2147483647, name="taxon_key")
        limit = bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=50, name="limit")
        params = [("taxon_key", str(taxon_key)), ("limit", str(limit)), ("offset", "0")]
        country = str(parameters.get("country") or "").strip().upper()
        if country:
            if not re.fullmatch(r"[A-Z]{2}", country):
                raise ValueError("country must be an ISO two-letter code")
            params.append(("country", country))
        if parameters.get("year") is not None:
            year = bounded_int(parameters.get("year"), default=2000, minimum=1600, maximum=2100, name="year")
            params.append(("year", str(year)))
        return "https://api.gbif.org/v1/occurrence/search", "GET", params, None, "gbif-results", []
    if operation == "wellcome-works-search":
        query = safe_plain_query(parameters.get("query"))
        limit = bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=50, name="limit")
        params = [("query", query), ("pageSize", str(limit)), ("include", "identifiers,items,subjects,contributors,production,languages,images")]
        return "https://api.wellcomecollection.org/catalogue/v2/works", "GET", params, None, "wellcome-results", []
    if operation == "data-europa-dataset-search":
        query = safe_plain_query(parameters.get("query"))
        limit = bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=100, name="limit")
        body = {"q": query, "filters": ["dataset"], "page": 0, "limit": limit, "showScore": True}
        return "https://data.europa.eu/api/hub/search/search", "POST", [], body, "data-europa", []
    raise ValueError(f"unsupported operation: {operation}")


def validate_response(kind: str, data: Any) -> int | None:
    if kind.startswith("open-book-"):
        if isinstance(data, list):
            return len(data)
        if isinstance(data, Mapping):
            for key in ("items", "results", "searchResults"):
                if isinstance(data.get(key), list):
                    return len(data[key])
        raise RuntimeError("open-book REST response contract failed")
    if not isinstance(data, Mapping):
        raise RuntimeError("upstream response must be a JSON object")
    if kind == "google-kg":
        rows = data.get("itemListElement")
        if not isinstance(rows, list):
            raise RuntimeError("Google Knowledge Graph response contract failed")
        return len(rows)
    if kind == "google-civic-elections":
        rows = data.get("elections")
        if not isinstance(rows, list):
            raise RuntimeError("Google Civic elections response contract failed")
        return len(rows)
    if kind == "google-civic-divisions":
        rows = data.get("results")
        if not isinstance(rows, list):
            raise RuntimeError("Google Civic divisions response contract failed")
        return len(rows)
    if kind == "gbif-results":
        rows = data.get("results")
        if not isinstance(rows, list):
            raise RuntimeError("GBIF response contract failed")
        return len(rows)
    if kind == "wellcome-results":
        rows = data.get("results")
        if not isinstance(rows, list):
            raise RuntimeError("Wellcome Catalogue response contract failed")
        return len(rows)
    if kind == "data-europa":
        if not any(key in data for key in ("result", "results", "items", "total")):
            raise RuntimeError("data.europa.eu response contract failed")
        for key in ("results", "items"):
            if isinstance(data.get(key), list):
                return len(data[key])
        result = data.get("result")
        if isinstance(result, Mapping):
            for key in ("results", "items", "datasets"):
                if isinstance(result.get(key), list):
                    return len(result[key])
        return None
    raise RuntimeError("unknown response contract")


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket.get("acceptance") or {})
    timeout = bounded_int(acceptance.get("timeout_seconds"), default=45, minimum=5, maximum=90, name="timeout_seconds")
    max_bytes = bounded_int(acceptance.get("max_response_bytes"), default=5_000_000, minimum=1024, maximum=10_000_000, name="max_response_bytes")
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_GLOBAL_OPEN_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "request_count": 0,
        "automatic_pagination": False,
        "automatic_retry": False,
        "redirects_allowed": False,
        "write_operations_allowed": False,
        "secret_values_exposed": False,
        "model_calls": 0,
    }
    try:
        url, method, query, body, kind, credentials = build_request(operation, parameters)
        if kind == "catalog":
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        elif kind == "matrix":
            snapshot = {"source_access_matrix": load_json(MATRIX_PATH)}
        else:
            response = requests.request(
                method,
                str(url),
                params=query,
                json=dict(body) if body is not None else None,
                headers={"Accept": "application/json", "Content-Type": "application/json", "User-Agent": USER_AGENT},
                timeout=timeout,
                allow_redirects=False,
            )
            raw = response.content
            if len(raw) > max_bytes:
                raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
            if not 200 <= response.status_code < 300:
                text = raw[:1000].decode("utf-8", errors="replace")
                raise RuntimeError(f"upstream HTTP {response.status_code}: {text}")
            try:
                data = response.json()
            except ValueError as exc:
                raise RuntimeError("upstream returned invalid JSON") from exc
            row_count = validate_response(kind, data)
            (output_dir / "response.json").write_bytes(raw)
            snapshot = {"provider": kind, "operation": operation, "data": data}
            metadata.update({
                "upstream_called": True,
                "request_count": 1,
                "api_origin": urlparse(str(url)).hostname,
                "http_method": method,
                "http_status": response.status_code,
                "content_type": response.headers.get("Content-Type", ""),
                "response_bytes": len(raw),
                "response_sha256": bytes_sha(raw),
                "row_count": row_count,
                "credential_names": credentials,
                "credential_mode": "backend-only" if credentials else "none",
            })
        status = "INTEL_GLOBAL_OPEN_COMPLETED"
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
        schema_prefix="global-open-apis",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-global-open]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="global-open-apis-ticket-status-v1",
            display_name="全球开放机构与Google公共知识API",
        )
    )
