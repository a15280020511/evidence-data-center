#!/usr/bin/env python3
"""Bounded discovery runtime for country portals and industry source directories."""
from __future__ import annotations

import json
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
ATLAS_PATH = HERE / "source-atlas.json"
USER_AGENT = "evidence-data-center-country-industry-atlas/1"
REGISTRY_URL = "https://dataportals.org/api/data.json"
PLAIN_QUERY_RE = re.compile(r"[^0-9A-Za-z\u00C0-\u024F\u4E00-\u9FFF _.-]+")
COUNTRY_RE = re.compile(r"^[A-Za-z]{2,16}$")


def safe_text(value: Any, name: str, maximum: int, minimum: int = 1) -> str:
    text = str(value or "").strip()
    if len(text) < minimum or len(text) > maximum or any(ord(ch) < 32 for ch in text):
        raise ValueError(f"{name} is invalid")
    return text


def safe_query(value: Any, name: str = "query", maximum: int = 160, required: bool = False) -> str:
    text = str(value or "").strip()
    if not text and not required:
        return ""
    text = safe_text(text, name, maximum)
    text = PLAIN_QUERY_RE.sub(" ", text)
    text = " ".join(text.split())
    if required and not text:
        raise ValueError(f"{name} contains no searchable text")
    return text


def safe_country(value: Any) -> str:
    text = str(value or "").strip().upper()
    if text and not COUNTRY_RE.fullmatch(text):
        raise ValueError("country must be a short country or area code/name token")
    return text


def build_request(
    operation: str,
    parameters: Mapping[str, Any],
) -> tuple[str | None, str, list[tuple[str, str]], Mapping[str, Any] | None, str]:
    if operation == "catalog-capabilities":
        if parameters:
            raise ValueError("catalog-capabilities accepts no parameters")
        return None, "LOCAL", [], None, "catalog"
    if operation == "country-industry-atlas":
        if parameters:
            raise ValueError("country-industry-atlas accepts no parameters")
        return None, "LOCAL", [], None, "atlas"
    if operation == "atlas-search":
        allowed = {"query", "region", "country", "industry", "access_tier", "limit"}
        if set(parameters) - allowed:
            raise ValueError("atlas-search contains unsupported parameters")
        return None, "LOCAL", [], None, "atlas-search"
    if operation == "portal-registry-search":
        allowed = {"query", "country", "status", "api_only", "government_only", "limit"}
        if set(parameters) - allowed:
            raise ValueError("portal-registry-search contains unsupported parameters")
        return REGISTRY_URL, "GET", [], None, "portal-registry"
    raise ValueError(f"unsupported operation: {operation}")


def atlas_records(atlas: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for section in (
        "official_discovery_layers",
        "regional_country_gateways",
        "industry_discovery_directories",
        "direct_api_candidates",
        "registration_or_application_candidates",
        "catalog_only_sources",
    ):
        values = atlas.get(section)
        if not isinstance(values, list):
            raise RuntimeError(f"atlas section is invalid: {section}")
        for item in values:
            if isinstance(item, Mapping):
                row = dict(item)
                row["atlas_section"] = section
                rows.append(row)
    return rows


def filter_atlas(atlas: Mapping[str, Any], parameters: Mapping[str, Any]) -> Mapping[str, Any]:
    query = safe_query(parameters.get("query")).lower()
    region = safe_query(parameters.get("region"), "region", 40).lower()
    country = safe_country(parameters.get("country")).lower()
    industry = safe_query(parameters.get("industry"), "industry", 80).lower()
    access_tier = safe_query(parameters.get("access_tier"), "access_tier", 50).lower()
    limit = bounded_int(parameters.get("limit"), default=50, minimum=1, maximum=100, name="limit")
    selected: list[dict[str, Any]] = []
    for row in atlas_records(atlas):
        searchable = json.dumps(row, ensure_ascii=False).lower()
        if query and query not in searchable:
            continue
        if region and region not in str(row.get("region", "")).lower():
            continue
        country_values = row.get("country_codes") or row.get("country_code") or row.get("countries") or ""
        if country and country not in json.dumps(country_values, ensure_ascii=False).lower():
            continue
        industry_values = row.get("industries") or row.get("industry") or row.get("category") or ""
        if industry and industry not in json.dumps(industry_values, ensure_ascii=False).lower():
            continue
        if access_tier and access_tier != str(row.get("access_tier", "")).lower():
            continue
        selected.append(row)
        if len(selected) >= limit:
            break
    return {"count": len(selected), "results": selected}


def portal_is_government(row: Mapping[str, Any]) -> bool:
    classification = str(row.get("publisher_classification") or "").strip().lower()
    tags = {str(item).strip().lower() for item in (row.get("tags") or []) if isinstance(item, str)}
    return classification == "government" or bool(tags & {"government", "official", "national", "level.national"})


def filter_portal_registry(data: Any, parameters: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(data, Mapping):
        raise RuntimeError("DataPortals registry response must be an object")
    query = safe_query(parameters.get("query")).lower()
    country = safe_country(parameters.get("country")).lower()
    status = str(parameters.get("status") or "active").strip().lower()
    if status not in {"active", "inactive", "all"}:
        raise ValueError("status must be active, inactive or all")
    api_only = bool(parameters.get("api_only", False))
    government_only = bool(parameters.get("government_only", True))
    limit = bounded_int(parameters.get("limit"), default=25, minimum=1, maximum=100, name="limit")
    selected: list[dict[str, Any]] = []
    for portal_id, value in data.items():
        if not isinstance(value, Mapping):
            continue
        row_status = str(value.get("status") or "").strip().lower()
        if status != "all" and row_status != status:
            continue
        row_country = str(value.get("country") or "").strip().lower()
        if country and row_country != country:
            continue
        if api_only and not (value.get("api_endpoint") or value.get("api_type")):
            continue
        if government_only and not portal_is_government(value):
            continue
        searchable = " ".join(
            str(value.get(key) or "")
            for key in ("title", "description", "publisher", "place", "country", "api_type", "generator")
        ).lower()
        searchable += " " + " ".join(str(item) for item in (value.get("tags") or []))
        if query and query not in searchable:
            continue
        selected.append(
            {
                "portal_id": str(portal_id),
                "title": value.get("title"),
                "url": value.get("url"),
                "publisher": value.get("publisher"),
                "publisher_classification": value.get("publisher_classification"),
                "country": value.get("country"),
                "place": value.get("place"),
                "status": value.get("status"),
                "generator": value.get("generator"),
                "api_endpoint": value.get("api_endpoint"),
                "api_type": value.get("api_type"),
                "license_id": value.get("license_id"),
                "tags": value.get("tags") or [],
            }
        )
        if len(selected) >= limit:
            break
    return {
        "registry": "DataPortals.org / Open Knowledge Foundation",
        "registry_license": "Public Domain",
        "discovery_only": True,
        "verification_required_before_production": True,
        "count": len(selected),
        "results": selected,
    }


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
    status = "INTEL_COUNTRY_INDUSTRY_ATLAS_FAILED"
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
        url, method, query, body, kind = build_request(operation, parameters)
        if kind == "catalog":
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        elif kind == "atlas":
            snapshot = {"country_industry_atlas": load_json(ATLAS_PATH)}
        elif kind == "atlas-search":
            snapshot = {"country_industry_atlas_search": filter_atlas(load_json(ATLAS_PATH), parameters)}
        else:
            response = requests.request(
                method,
                str(url),
                params=query,
                json=dict(body) if body is not None else None,
                headers={"Accept": "application/json", "User-Agent": USER_AGENT},
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
            filtered = filter_portal_registry(data, parameters)
            (output_dir / "registry-response.json").write_bytes(raw)
            snapshot = {"provider": kind, "operation": operation, "data": filtered}
            metadata.update(
                {
                    "upstream_called": True,
                    "request_count": 1,
                    "api_origin": urlparse(str(url)).hostname,
                    "http_method": method,
                    "http_status": response.status_code,
                    "content_type": response.headers.get("Content-Type", ""),
                    "response_bytes": len(raw),
                    "response_sha256": bytes_sha(raw),
                    "row_count": filtered["count"],
                    "credential_mode": "none",
                    "discovery_only": True,
                }
            )
        status = "INTEL_COUNTRY_INDUSTRY_ATLAS_COMPLETED"
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
        schema_prefix="country-industry-atlas",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-country-atlas]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="country-industry-atlas-ticket-status-v1",
            display_name="全球国家与行业来源图谱",
        )
    )
