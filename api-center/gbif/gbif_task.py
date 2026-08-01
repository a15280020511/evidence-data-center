#!/usr/bin/env python3
"""Bounded read-only GBIF execution for Intelligence Center tickets."""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import quote

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
ORIGIN = "https://api.gbif.org"
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")
TEXT_RE = re.compile(r"^[^\x00-\x1f\x7f]{1,500}$")
GEO_DISTANCE_RE = re.compile(r"^-?(?:90(?:\.0+)?|[0-8]?[0-9](?:\.\d+)?),-?(?:180(?:\.0+)?|1[0-7][0-9](?:\.\d+)?|[0-9]?[0-9](?:\.\d+)?),(?:[1-9]\d*(?:\.\d+)?)(?:m|km)$")
COUNTRY_RE = re.compile(r"^[A-Z]{2}$")
RANKS = {"KINGDOM", "PHYLUM", "CLASS", "ORDER", "FAMILY", "GENUS", "SPECIES", "SUBSPECIES", "VARIETY", "FORM", "UNRANKED"}
DATASET_TYPES = {"OCCURRENCE", "CHECKLIST", "SAMPLING_EVENT", "METADATA"}


class GbifError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def _text(parameters: Mapping[str, Any], name: str, *, required: bool = False, maximum: int = 500) -> str | None:
    value = parameters.get(name)
    if value in (None, ""):
        if required:
            raise ValueError(f"{name} is required")
        return None
    text = str(value)
    if len(text) > maximum or not TEXT_RE.fullmatch(text):
        raise ValueError(f"{name} is invalid")
    return text


def _uuid(parameters: Mapping[str, Any], name: str) -> str:
    value = str(parameters.get(name) or "")
    if not UUID_RE.fullmatch(value):
        raise ValueError(f"{name} must be a UUID")
    return value.lower()


def _paging(parameters: Mapping[str, Any], *, limit_max: int = 300) -> tuple[int, int]:
    limit = bounded_int(parameters.get("limit"), default=50, minimum=1, maximum=limit_max, name="limit")
    offset = bounded_int(parameters.get("offset"), default=0, minimum=0, maximum=99_999, name="offset")
    if offset + limit > 100_000:
        raise ValueError("offset + limit must not exceed 100000")
    return limit, offset


def _add_common_occurrence_filters(query: dict[str, str], parameters: Mapping[str, Any]) -> None:
    mappings = {"q": "q", "scientific_name": "scientificName", "event_date": "eventDate", "year": "year"}
    for source, target in mappings.items():
        value = _text(parameters, source)
        if value is not None:
            if source == "year" and not re.fullmatch(r"\d{4}(?:,\d{4})?", value):
                raise ValueError("year must be YYYY or YYYY,YYYY")
            query[target] = value
    if parameters.get("taxon_key") is not None:
        query["taxonKey"] = str(bounded_int(parameters.get("taxon_key"), default=1, minimum=1, maximum=2_147_483_647, name="taxon_key"))
    if parameters.get("country") not in (None, ""):
        country = str(parameters["country"]).upper()
        if not COUNTRY_RE.fullmatch(country):
            raise ValueError("country must be ISO alpha-2")
        query["country"] = country
    if parameters.get("geo_distance") not in (None, ""):
        value = str(parameters["geo_distance"])
        if not GEO_DISTANCE_RE.fullmatch(value):
            raise ValueError("geo_distance must be latitude,longitude,distance with m or km")
        query["geoDistance"] = value
    for source, target in (("has_coordinate", "hasCoordinate"), ("has_geospatial_issue", "hasGeospatialIssue")):
        if source in parameters:
            query[target] = "true" if bool(parameters[source]) else "false"


def build_request(operation: str, parameters: Mapping[str, Any]) -> tuple[str | None, dict[str, str]]:
    if operation == "catalog-capabilities":
        return None, {}
    if operation == "species-match":
        query: dict[str, str] = {"name": _text(parameters, "name", required=True, maximum=300) or ""}
        for name in ("kingdom", "phylum", "order", "family", "genus"):
            value = _text(parameters, name, maximum=200)
            if value is not None:
                query[name] = value
        class_name = _text(parameters, "class_name", maximum=200)
        if class_name is not None:
            query["class"] = class_name
        if parameters.get("rank") not in (None, ""):
            rank = str(parameters["rank"]).upper()
            if rank not in RANKS:
                raise ValueError("rank is not allowlisted")
            query["rank"] = rank
        for name in ("strict", "verbose"):
            if name in parameters:
                query[name] = "true" if bool(parameters[name]) else "false"
        return "/v1/species/match", query
    if operation in {"species-search", "species-suggest"}:
        q = _text(parameters, "q", required=True, maximum=300) or ""
        limit, offset = _paging(parameters, limit_max=100)
        path = "/v1/species/search" if operation == "species-search" else "/v1/species/suggest"
        query = {"q": q, "limit": str(limit)}
        if operation == "species-search":
            query["offset"] = str(offset)
        return path, query
    if operation == "species-get":
        usage_key = bounded_int(parameters.get("usage_key"), default=1, minimum=1, maximum=2_147_483_647, name="usage_key")
        return f"/v1/species/{usage_key}", {}
    if operation in {"occurrence-search", "occurrence-count"}:
        query: dict[str, str] = {}
        _add_common_occurrence_filters(query, parameters)
        if operation == "occurrence-search":
            limit, offset = _paging(parameters, limit_max=300)
            query.update({"limit": str(limit), "offset": str(offset)})
            return "/v1/occurrence/search", query
        return "/v1/occurrence/count", query
    if operation == "occurrence-get":
        gbif_id = bounded_int(parameters.get("gbif_id"), default=1, minimum=1, maximum=9_223_372_036_854_775_807, name="gbif_id")
        return f"/v1/occurrence/{gbif_id}", {}
    if operation == "dataset-search":
        q = _text(parameters, "q", required=True, maximum=300) or ""
        limit, offset = _paging(parameters, limit_max=100)
        query = {"q": q, "limit": str(limit), "offset": str(offset)}
        if parameters.get("type") not in (None, ""):
            dataset_type = str(parameters["type"]).upper()
            if dataset_type not in DATASET_TYPES:
                raise ValueError("type is not allowlisted")
            query["type"] = dataset_type
        if parameters.get("publishing_country") not in (None, ""):
            country = str(parameters["publishing_country"]).upper()
            if not COUNTRY_RE.fullmatch(country):
                raise ValueError("publishing_country must be ISO alpha-2")
            query["publishingCountry"] = country
        return "/v1/dataset/search", query
    if operation == "dataset-get":
        return f"/v1/dataset/{quote(_uuid(parameters, 'dataset_key'), safe='-')}", {}
    raise ValueError(f"unsupported operation: {operation}")


def _row_count(payload: Any) -> int:
    if isinstance(payload, Mapping):
        results = payload.get("results")
        if isinstance(results, list):
            return len(results)
        return 1
    if isinstance(payload, list):
        return len(payload)
    return 1


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(acceptance.get("timeout_seconds"), default=45, minimum=5, maximum=120, name="timeout_seconds")
    max_bytes = bounded_int(acceptance.get("max_response_bytes"), default=5_000_000, minimum=1024, maximum=20_000_000, name="max_response_bytes")
    max_rows = bounded_int(acceptance.get("max_rows"), default=300, minimum=1, maximum=5000, name="max_rows")
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_GBIF_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "api_origin": "api.gbif.org",
        "credential_mode": "none",
        "secret_values_exposed": False,
        "bulk_downloads_allowed": False,
        "write_operations_allowed": False,
        "automatic_pagination_allowed": False,
    }
    try:
        path, query = build_request(operation, parameters)
        if path is None:
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        else:
            response = requests.get(
                ORIGIN + path,
                params=query,
                headers={"Accept": "application/json", "User-Agent": "evidence-data-center-gbif/1.0"},
                timeout=timeout,
                allow_redirects=False,
            )
            raw = response.content
            if len(raw) > max_bytes:
                raise GbifError("GBIF_RESPONSE_TOO_LARGE", "response exceeded max_response_bytes")
            if response.is_redirect:
                raise GbifError("GBIF_REDIRECT_REJECTED", f"upstream attempted HTTP {response.status_code} redirect")
            if response.status_code == 429:
                raise GbifError("GBIF_RATE_LIMITED", "upstream HTTP 429", retryable=True)
            if not response.ok:
                raise GbifError("GBIF_HTTP_ERROR", f"upstream HTTP {response.status_code}")
            try:
                payload = json.loads(raw.decode("utf-8")) if raw else None
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise GbifError("GBIF_INVALID_JSON", "upstream returned invalid JSON") from exc
            rows = _row_count(payload)
            if rows > max_rows:
                raise GbifError("GBIF_RESULT_TOO_MANY_ROWS", f"upstream result has {rows} rows; max_rows is {max_rows}")
            snapshot = {"provider": "gbif", "operation": operation, "row_count": rows, "data": payload}
            (output_dir / "response.json").write_bytes(raw)
            metadata.update({
                "upstream_called": True,
                "request_origin": ORIGIN,
                "request_path": path,
                "query_parameter_names": sorted(query),
                "http_status": response.status_code,
                "content_type": response.headers.get("Content-Type", ""),
                "response_bytes": len(raw),
                "response_sha256": bytes_sha(raw),
                "result_rows": rows,
            })
        status = "INTEL_GBIF_COMPLETED"
    except Exception as exc:
        failure = {
            "type": type(exc).__name__,
            "code": getattr(exc, "code", "GBIF_EXECUTION_ERROR"),
            "retryable": bool(getattr(exc, "retryable", False)),
            "message": str(exc)[:2000],
        }
    return finish_execution(
        ticket=ticket,
        output_dir=output_dir,
        status=status,
        snapshot=snapshot,
        metadata=metadata,
        failure=failure,
        started_at=started_at,
        started_perf=started_perf,
        schema_prefix="gbif",
    )


if __name__ == "__main__":
    raise SystemExit(run_cli(
        execute=execute,
        ticket_prefix="[intel-gbif]",
        schema_path=SCHEMA_PATH,
        catalog_path=CATALOG_PATH,
        status_schema="gbif-ticket-status-v1",
        display_name="GBIF",
    ))
