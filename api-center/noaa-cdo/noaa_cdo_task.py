#!/usr/bin/env python3
"""Bounded NOAA Climate Data Online v2 provider for the Intelligence Center."""
from __future__ import annotations

import os
import re
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any, Mapping

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
ORIGIN = "https://www.ncei.noaa.gov"
PREFIX = "/cdo-web/api/v2"
SECRET_ENV = "NOAA_CDO_TOKEN"
TOKEN_RE = re.compile(r"^[A-Za-z0-9._~-]{16,256}$")
PATHS = {
    "datasets": "/datasets",
    "datatypes": "/datatypes",
    "stations": "/stations",
    "data": "/data",
}
ARRAY_PARAMS = {"datatypeid"}
DATE_PARAMS = {"startdate", "enddate"}
CHINA_SOUTH = 18.0
CHINA_NORTH = 54.0
CHINA_WEST = 73.0
CHINA_EAST = 135.0


def _date_value(value: Any, name: str) -> str:
    text = str(value)
    try:
        date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{name} must be YYYY-MM-DD") from exc
    return text


def _validate_date_range(operation: str, parameters: Mapping[str, Any]) -> None:
    start_raw = parameters.get("startdate")
    end_raw = parameters.get("enddate")
    if start_raw in (None, "") or end_raw in (None, ""):
        return
    start = date.fromisoformat(str(start_raw))
    end = date.fromisoformat(str(end_raw))
    if start > end:
        raise ValueError("startdate must not be after enddate")
    if operation == "data":
        dataset = str(parameters.get("datasetid") or "")
        max_days = 3660 if dataset in {"GSOM", "GSOY"} else 366
        if (end - start).days > max_days:
            raise ValueError(
                "NOAA CDO data range exceeds provider limit: monthly/annual max 10 years; other datasets max 1 year"
            )


def _validate_china_extent(value: Any) -> str:
    text = str(value)
    parts = text.split(",")
    if len(parts) != 4:
        raise ValueError("extent must be south,west,north,east")
    try:
        south, west, north, east = (float(part) for part in parts)
    except ValueError as exc:
        raise ValueError("extent values must be numeric") from exc
    if south >= north or west >= east:
        raise ValueError("extent must have south<north and west<east")
    if not (
        CHINA_SOUTH <= south <= CHINA_NORTH
        and CHINA_SOUTH <= north <= CHINA_NORTH
        and CHINA_WEST <= west <= CHINA_EAST
        and CHINA_WEST <= east <= CHINA_EAST
    ):
        raise ValueError("extent must remain inside the configured China geographic envelope")
    return text


def build_request(operation: str, parameters: Mapping[str, Any]) -> tuple[str | None, list[tuple[str, str]]]:
    if operation == "catalog-capabilities":
        if parameters:
            raise ValueError("catalog-capabilities accepts no parameters")
        return None, []
    path = PATHS.get(operation)
    if path is None:
        raise ValueError(f"unsupported operation: {operation}")
    _validate_date_range(operation, parameters)
    query: list[tuple[str, str]] = []
    for name, raw in parameters.items():
        if raw in (None, ""):
            continue
        if name in DATE_PARAMS:
            query.append((name, _date_value(raw, name)))
        elif name == "extent":
            query.append((name, _validate_china_extent(raw)))
        elif name in ARRAY_PARAMS:
            if isinstance(raw, list):
                if not raw:
                    raise ValueError(f"{name} must not be empty")
                query.extend((name, str(item)) for item in raw)
            else:
                query.append((name, str(raw)))
        elif isinstance(raw, bool):
            query.append((name, "true" if raw else "false"))
        else:
            query.append((name, str(raw)))
    if operation in PATHS:
        names = {name for name, _ in query}
        if "limit" not in names:
            query.append(("limit", "1000"))
        if "offset" not in names:
            query.append(("offset", "1"))
    if operation == "data":
        dataset = str(parameters.get("datasetid") or "")
        station = str(parameters.get("stationid") or "")
        if not station.startswith(dataset + ":"):
            raise ValueError("stationid prefix must match datasetid")
        if parameters.get("units") not in (None, "metric"):
            raise ValueError("units must be metric")
    return PREFIX + path, query


def _row_count(payload: Any) -> int:
    if isinstance(payload, Mapping):
        rows = payload.get("results")
        if isinstance(rows, list):
            return len(rows)
        return 1 if payload else 0
    return len(payload) if isinstance(payload, list) else 0


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(
        acceptance.get("timeout_seconds"), default=30, minimum=5, maximum=60, name="timeout_seconds"
    )
    max_bytes = bounded_int(
        acceptance.get("max_response_bytes"),
        default=5_000_000,
        minimum=1024,
        maximum=10_000_000,
        name="max_response_bytes",
    )
    started_at, started_perf = utc_now(), time.perf_counter()
    status = "INTEL_NOAA_CDO_FAILED"
    failure: Mapping[str, Any] | None = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "api_host": "www.ncei.noaa.gov",
        "api_version": "CDO v2",
        "credential_mode": "token_header_backend_only",
        "secret_environment_variable": SECRET_ENV,
        "requests_per_ticket_max": 1,
        "automatic_retry": False,
        "automatic_pagination": False,
        "redirects_allowed": False,
        "secret_values_exposed": False,
        "operation": operation,
    }
    secret = str(os.environ.get(SECRET_ENV) or "").strip()
    try:
        path, query = build_request(operation, parameters)
        if path is None:
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        else:
            if not secret:
                raise RuntimeError(f"{SECRET_ENV} is not configured")
            if not TOKEN_RE.fullmatch(secret):
                raise RuntimeError(f"{SECRET_ENV} has an invalid format")
            response = requests.get(
                ORIGIN + path,
                params=query,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "gpts-intelligence-center-noaa-cdo/1",
                    "token": secret,
                },
                timeout=timeout,
                allow_redirects=False,
            )
            raw = bytes(response.content or b"")
            metadata.update(
                {
                    "upstream_called": True,
                    "request_path": path,
                    "query_parameter_names": sorted({name for name, _ in query}),
                    "http_status": int(response.status_code),
                    "content_type": str(response.headers.get("Content-Type") or ""),
                    "response_bytes": len(raw),
                }
            )
            if len(raw) > max_bytes:
                raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
            try:
                payload = response.json()
            except ValueError as exc:
                raise RuntimeError("NOAA CDO returned invalid JSON") from exc
            if not response.ok:
                detail = str(payload)[:1500].replace(secret, "[REDACTED]")
                raise RuntimeError(f"NOAA CDO HTTP {response.status_code}: {detail}")
            (output_dir / "response.json").write_bytes(raw)
            snapshot = {
                "provider": "noaa-cdo",
                "operation": operation,
                "row_count": _row_count(payload),
                "data": payload,
            }
            metadata.update(
                {"response_sha256": bytes_sha(raw), "row_count": _row_count(payload)}
            )
        status = "INTEL_NOAA_CDO_COMPLETED"
    except Exception as exc:
        message = str(exc)
        if secret:
            message = message.replace(secret, "[REDACTED]")
        failure = {"type": type(exc).__name__, "message": message[:2000]}
    return finish_execution(
        ticket=ticket,
        output_dir=output_dir,
        status=status,
        snapshot=snapshot,
        metadata=metadata,
        failure=failure,
        started_at=started_at,
        started_perf=started_perf,
        schema_prefix="noaa-cdo",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-noaa-cdo]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="noaa-cdo-ticket-status-v1",
            display_name="NOAA CDO",
        )
    )
