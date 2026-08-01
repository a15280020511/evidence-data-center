#!/usr/bin/env python3
"""Bounded read-only U.S. EIA API v2 execution for Intelligence Center tickets."""
from __future__ import annotations

import json
import os
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
ORIGIN = "https://api.eia.gov"
SECRET_ENV = "EIA_API_KEY"
ROUTE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
SERIES_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,199}$")
PERIOD_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:+._-]{0,31}$")
RESERVED_ROUTE_SEGMENTS = {"data", "facet"}


def _route(parameters: Mapping[str, Any]) -> str:
    raw = str(parameters.get("route") or "").strip().strip("/")
    if not raw:
        raise ValueError("route is required")
    segments = raw.split("/")
    if len(segments) > 8:
        raise ValueError("route may contain at most 8 segments")
    for segment in segments:
        if not ROUTE_SEGMENT_RE.fullmatch(segment):
            raise ValueError("route contains an invalid segment")
        if segment.casefold() in RESERVED_ROUTE_SEGMENTS:
            raise ValueError("route must not include terminal data or facet segments")
    return "/".join(quote(segment, safe="._-") for segment in segments)


def _name(parameters: Mapping[str, Any], key: str) -> str:
    value = str(parameters.get(key) or "")
    if not NAME_RE.fullmatch(value):
        raise ValueError(f"{key} is invalid")
    return value


def _series_id(parameters: Mapping[str, Any]) -> str:
    value = str(parameters.get("series_id") or "")
    if not SERIES_ID_RE.fullmatch(value):
        raise ValueError("series_id is invalid")
    return value


def _bounded_page(parameters: Mapping[str, Any], *, default_length: int) -> tuple[int, int]:
    offset = bounded_int(parameters.get("offset"), default=0, minimum=0, maximum=10_000_000, name="offset")
    length = bounded_int(parameters.get("length"), default=default_length, minimum=1, maximum=5000, name="length")
    return offset, length


def _append_period(query: list[tuple[str, str]], parameters: Mapping[str, Any], name: str) -> None:
    raw = parameters.get(name)
    if raw in (None, ""):
        return
    value = str(raw)
    if not PERIOD_RE.fullmatch(value):
        raise ValueError(f"{name} is invalid")
    query.append((name, value))


def _data_query(parameters: Mapping[str, Any]) -> list[tuple[str, str]]:
    columns = parameters.get("data")
    if not isinstance(columns, list) or not columns or len(columns) > 20:
        raise ValueError("data must contain 1 to 20 column names")
    names = [str(item) for item in columns]
    if len(names) != len(set(names)) or any(not NAME_RE.fullmatch(item) for item in names):
        raise ValueError("data contains an invalid or duplicate column name")

    query: list[tuple[str, str]] = [("data[]", item) for item in names]
    frequency = parameters.get("frequency")
    if frequency not in (None, ""):
        value = str(frequency)
        if not NAME_RE.fullmatch(value):
            raise ValueError("frequency is invalid")
        query.append(("frequency", value))

    facets = parameters.get("facets")
    total_facet_values = 0
    if facets not in (None, {}):
        if not isinstance(facets, Mapping) or len(facets) > 12:
            raise ValueError("facets must be an object with at most 12 keys")
        for facet_name, raw_values in facets.items():
            name = str(facet_name)
            if not NAME_RE.fullmatch(name):
                raise ValueError("facets contains an invalid facet name")
            if not isinstance(raw_values, list) or not raw_values or len(raw_values) > 50:
                raise ValueError("each facet must contain 1 to 50 values")
            values = [str(item) for item in raw_values]
            if len(values) != len(set(values)):
                raise ValueError("facet values must be unique")
            for value in values:
                if not value or len(value) > 200 or any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
                    raise ValueError("facet contains an invalid value")
                query.append((f"facets[{name}][]", value))
            total_facet_values += len(values)
        if total_facet_values > 100:
            raise ValueError("facets may contain at most 100 values in total")

    _append_period(query, parameters, "start")
    _append_period(query, parameters, "end")

    sort = parameters.get("sort")
    if sort not in (None, []):
        if not isinstance(sort, list) or len(sort) > 4:
            raise ValueError("sort must contain at most 4 rules")
        for index, raw_rule in enumerate(sort):
            if not isinstance(raw_rule, Mapping):
                raise ValueError("each sort rule must be an object")
            if set(raw_rule) != {"column", "direction"}:
                raise ValueError("sort rules require only column and direction")
            column = str(raw_rule.get("column") or "")
            direction = str(raw_rule.get("direction") or "").lower()
            if not NAME_RE.fullmatch(column) or direction not in {"asc", "desc"}:
                raise ValueError("sort rule is invalid")
            query.extend(
                [
                    (f"sort[{index}][column]", column),
                    (f"sort[{index}][direction]", direction),
                ]
            )

    offset, length = _bounded_page(parameters, default_length=500)
    query.extend([("offset", str(offset)), ("length", str(length))])
    return query


def build_request(operation: str, parameters: Mapping[str, Any]) -> tuple[str | None, list[tuple[str, str]]]:
    if operation == "catalog-capabilities":
        return None, []
    if operation == "api-root":
        return "/v2/", []
    if operation == "route-metadata":
        return f"/v2/{_route(parameters)}/", []
    if operation == "facet-values":
        offset, length = _bounded_page(parameters, default_length=500)
        return (
            f"/v2/{_route(parameters)}/facet/{quote(_name(parameters, 'facet'), safe='._-')}/",
            [("offset", str(offset)), ("length", str(length))],
        )
    if operation == "route-data":
        return f"/v2/{_route(parameters)}/data/", _data_query(parameters)
    if operation == "series-by-id":
        return f"/v2/seriesid/{quote(_series_id(parameters), safe='._:-')}", []
    raise ValueError(f"unsupported operation: {operation}")


def _scrub(value: Any, secret: str) -> Any:
    if isinstance(value, str):
        return value.replace(secret, "[REDACTED]") if secret else value
    if isinstance(value, list):
        return [_scrub(item, secret) for item in value]
    if isinstance(value, Mapping):
        return {str(_scrub(key, secret)): _scrub(item, secret) for key, item in value.items()}
    return value


def _row_count(payload: Any) -> int:
    if not isinstance(payload, Mapping):
        return len(payload) if isinstance(payload, list) else 0
    response = payload.get("response")
    if isinstance(response, Mapping):
        for key in ("data", "facets", "routes"):
            value = response.get(key)
            if isinstance(value, list):
                return len(value)
        return 1
    return 1


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(acceptance.get("timeout_seconds"), default=30, minimum=5, maximum=60, name="timeout_seconds")
    max_bytes = bounded_int(
        acceptance.get("max_response_bytes"),
        default=10_000_000,
        minimum=1024,
        maximum=20_000_000,
        name="max_response_bytes",
    )
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_EIA_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "api_origin": "api.eia.gov",
        "api_version": "v2",
        "credential_mode": "api_key_query_backend_only",
        "secret_environment_variable": SECRET_ENV,
        "secret_values_exposed": False,
        "requests_per_ticket": 1,
        "automatic_retry": False,
        "automatic_pagination": False,
        "maximum_rows_per_response": 5000,
    }
    secret = str(os.environ.get(SECRET_ENV) or "").strip()
    try:
        path, query = build_request(operation, parameters)
        if path is None:
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        else:
            if not secret:
                raise RuntimeError(f"{SECRET_ENV} is not configured")
            safe_query_names = sorted({name for name, _ in query})
            upstream_query: list[tuple[str, str]] = list(query)
            upstream_query.append(("api_key", secret))
            response = requests.get(
                ORIGIN + path,
                params=upstream_query,
                headers={"Accept": "application/json", "User-Agent": "intelligence-center-eia/1"},
                timeout=timeout,
                allow_redirects=False,
            )
            raw = bytes(response.content or b"")
            if len(raw) > max_bytes:
                raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
            try:
                payload = response.json()
            except ValueError as exc:
                raise RuntimeError("EIA returned invalid JSON") from exc
            clean = _scrub(payload, secret)
            if not response.ok:
                raise RuntimeError(f"EIA HTTP {response.status_code}: {str(clean)[:1200]}")
            if isinstance(clean, Mapping) and clean.get("error"):
                raise RuntimeError(f"EIA business error: {str(clean.get('error'))[:1200]}")
            sanitized = (json.dumps(clean, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
            if len(sanitized) > max_bytes:
                raise RuntimeError("sanitized response exceeds max_response_bytes")
            (output_dir / "response.json").write_bytes(sanitized)
            snapshot = {
                "provider": "eia",
                "operation": operation,
                "row_count": _row_count(clean),
                "data": clean,
            }
            metadata.update(
                {
                    "upstream_called": True,
                    "http_status": response.status_code,
                    "content_type": response.headers.get("Content-Type", ""),
                    "request_path": path,
                    "query_parameter_names": safe_query_names,
                    "response_bytes": len(sanitized),
                    "response_sha256": bytes_sha(sanitized),
                    "row_count": _row_count(clean),
                }
            )
        status = "INTEL_EIA_COMPLETED"
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
        schema_prefix="eia",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-eia]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="eia-ticket-status-v1",
            display_name="U.S. EIA",
        )
    )
