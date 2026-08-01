#!/usr/bin/env python3
"""Bounded read-only WHO GHO OData execution for Intelligence Center tickets."""
from __future__ import annotations

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
BASE_URL = "https://ghoapi.azureedge.net/api"
INDICATOR_RE = re.compile(r"^[A-Z0-9][A-Z0-9_]{1,127}$")
SEARCH_RE = re.compile(r"^[A-Za-z0-9 .,/()%-]{2,120}$")
DIMENSIONS = {
    "COUNTRY", "REGION", "SEX", "AGEGROUP", "GHO", "PUBLISHSTATE",
    "WORLDBANKINCOMEGROUP",
}
REGIONS = {"AFR", "AMR", "SEAR", "EUR", "EMR", "WPR", "GLOBAL"}
SEXES = {"BTSX", "MLE", "FMLE"}


def page(parameters: Mapping[str, Any], *, default_top: int = 100, max_top: int = 1000) -> dict[str, str]:
    top = bounded_int(parameters.get("top"), default=default_top, minimum=1, maximum=max_top, name="top")
    skip = bounded_int(parameters.get("skip"), default=0, minimum=0, maximum=100000, name="skip")
    return {"$top": str(top), "$skip": str(skip), "$format": "json"}


def build_request(operation: str, parameters: Mapping[str, Any]) -> tuple[str | None, dict[str, str]]:
    if operation == "catalog-capabilities":
        return None, {}
    if operation == "list-dimensions":
        return "/Dimension", page(parameters)
    if operation == "list-dimension-values":
        dimension = str(parameters.get("dimension") or "")
        if dimension not in DIMENSIONS:
            raise ValueError("dimension is not allowlisted")
        return f"/DIMENSION/{dimension}/DimensionValues", page(parameters)
    if operation == "list-indicators":
        return "/Indicator", page(parameters)
    if operation == "search-indicators":
        query_text = str(parameters.get("query") or "")
        if not SEARCH_RE.fullmatch(query_text):
            raise ValueError("query contains unsupported characters")
        match = str(parameters.get("match") or "contains")
        if match not in {"contains", "exact"}:
            raise ValueError("match is invalid")
        escaped = query_text.replace("'", "''")
        query = page(parameters, default_top=50, max_top=200)
        query["$filter"] = (
            f"contains(IndicatorName,'{escaped}')"
            if match == "contains"
            else f"IndicatorName eq '{escaped}'"
        )
        return "/Indicator", query
    if operation == "get-countries":
        return "/DIMENSION/COUNTRY/DimensionValues", page(parameters)
    if operation == "get-regions":
        return "/DIMENSION/REGION/DimensionValues", page(parameters)
    if operation == "get-indicator-data":
        code = str(parameters.get("indicator_code") or "")
        if not INDICATOR_RE.fullmatch(code):
            raise ValueError("indicator_code is invalid")
        country = parameters.get("country")
        region = parameters.get("region")
        if country and region:
            raise ValueError("country and region are mutually exclusive")
        terms: list[str] = []
        if country:
            country_text = str(country)
            if not re.fullmatch(r"[A-Z]{3}", country_text):
                raise ValueError("country must be an ISO alpha-3 code")
            terms.extend(["SpatialDimType eq 'COUNTRY'", f"SpatialDim eq '{country_text}'"])
        if region:
            region_text = str(region)
            if region_text not in REGIONS:
                raise ValueError("region is invalid")
            terms.append(f"SpatialDim eq '{region_text}'")
        year_from = parameters.get("year_from")
        year_to = parameters.get("year_to")
        if year_from is not None:
            year_from = bounded_int(year_from, default=1900, minimum=1900, maximum=2100, name="year_from")
            terms.append(f"TimeDim ge {year_from}")
        if year_to is not None:
            year_to = bounded_int(year_to, default=2100, minimum=1900, maximum=2100, name="year_to")
            terms.append(f"TimeDim le {year_to}")
        if year_from is not None and year_to is not None and year_from > year_to:
            raise ValueError("year_from must not exceed year_to")
        sex = parameters.get("sex")
        if sex:
            sex_text = str(sex)
            if sex_text not in SEXES:
                raise ValueError("sex is invalid")
            terms.extend(["Dim1Type eq 'SEX'", f"Dim1 eq '{sex_text}'"])
        query = page(parameters)
        if terms:
            query["$filter"] = " and ".join(terms)
        query["$orderby"] = "TimeDim desc"
        return "/" + quote(code, safe="_"), query
    raise ValueError(f"unsupported operation: {operation}")


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(acceptance.get("timeout_seconds"), default=45, minimum=5, maximum=120, name="timeout_seconds")
    max_bytes = bounded_int(acceptance.get("max_response_bytes"), default=5_000_000, minimum=1024, maximum=20_000_000, name="max_response_bytes")
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_WHO_GHO_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "api_origin": "ghoapi.azureedge.net",
        "credential_mode": "none",
        "secret_values_exposed": False,
        "automatic_pagination": False,
        "legacy_endpoint_migration_watch_required": True,
    }
    try:
        path, query = build_request(operation, parameters)
        if path is None:
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        else:
            response = requests.get(
                BASE_URL + path,
                params=query,
                headers={"Accept": "application/json", "User-Agent": "intelligence-center-who-gho/1"},
                timeout=timeout,
                allow_redirects=False,
            )
            raw = response.content
            if len(raw) > max_bytes:
                raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
            if not response.ok:
                text = raw[:1000].decode("utf-8", errors="replace")
                raise RuntimeError(f"WHO GHO HTTP {response.status_code}: {text}")
            try:
                data = response.json()
            except ValueError as exc:
                raise RuntimeError("WHO GHO returned invalid JSON") from exc
            if not isinstance(data, Mapping) or not isinstance(data.get("value"), list):
                raise RuntimeError("WHO GHO response does not match OData value contract")
            (output_dir / "response.json").write_bytes(raw)
            snapshot = {
                "provider": "who-gho-odata",
                "operation": operation,
                "request_path": path,
                "row_count": len(data["value"]),
                "has_next_link": bool(data.get("@odata.nextLink")),
                "data": data,
            }
            metadata.update({
                "upstream_called": True,
                "http_status": response.status_code,
                "content_type": response.headers.get("Content-Type", ""),
                "request_path": path,
                "response_bytes": len(raw),
                "response_sha256": bytes_sha(raw),
                "row_count": len(data["value"]),
                "has_next_link": bool(data.get("@odata.nextLink")),
            })
        status = "INTEL_WHO_GHO_COMPLETED"
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
        schema_prefix="who-gho",
    )


if __name__ == "__main__":
    raise SystemExit(run_cli(
        execute=execute,
        ticket_prefix="[intel-who-gho]",
        schema_path=SCHEMA_PATH,
        catalog_path=CATALOG_PATH,
        status_schema="who-gho-ticket-status-v1",
        display_name="WHO GHO OData",
    ))
