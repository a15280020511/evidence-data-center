#!/usr/bin/env python3
"""Bounded official FRED/ALFRED read-only provider for the Intelligence Center."""
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
ORIGIN = "https://api.stlouisfed.org"
SECRET_ENV = "FRED_API_KEY"
API_KEY_RE = re.compile(r"^[a-z0-9]{32}$")
DATE_KEYS = {"realtime_start", "realtime_end", "observation_start", "observation_end"}
ARRAY_SEPARATORS = {"tag_names": ";", "exclude_tag_names": ";", "vintage_dates": ","}
PATHS = {
    "category": "/fred/category",
    "category-children": "/fred/category/children",
    "category-related": "/fred/category/related",
    "category-series": "/fred/category/series",
    "releases": "/fred/releases",
    "releases-dates": "/fred/releases/dates",
    "release": "/fred/release",
    "release-dates": "/fred/release/dates",
    "release-series": "/fred/release/series",
    "release-sources": "/fred/release/sources",
    "series": "/fred/series",
    "series-categories": "/fred/series/categories",
    "series-observations": "/fred/series/observations",
    "series-release": "/fred/series/release",
    "series-search": "/fred/series/search",
    "series-updates": "/fred/series/updates",
    "series-vintagedates": "/fred/series/vintagedates",
    "sources": "/fred/sources",
    "source": "/fred/source",
    "source-releases": "/fred/source/releases",
    "tags": "/fred/tags",
    "related-tags": "/fred/related_tags",
    "tags-series": "/fred/tags/series",
    "series-tags": "/fred/series/tags",
}
PAGINATED = {
    "category-series",
    "releases",
    "releases-dates",
    "release-dates",
    "release-series",
    "series-observations",
    "series-search",
    "series-updates",
    "series-vintagedates",
    "sources",
    "source-releases",
    "tags",
    "related-tags",
    "tags-series",
}


def _date_value(value: Any, name: str) -> str:
    text = str(value)
    try:
        date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{name} must be YYYY-MM-DD") from exc
    return text


def _validate_ranges(parameters: Mapping[str, Any]) -> None:
    for start_name, end_name in (
        ("realtime_start", "realtime_end"),
        ("observation_start", "observation_end"),
    ):
        start = parameters.get(start_name)
        end = parameters.get(end_name)
        if start not in (None, "") and end not in (None, ""):
            if date.fromisoformat(str(start)) > date.fromisoformat(str(end)):
                raise ValueError(f"{start_name} must not be after {end_name}")


def build_request(operation: str, parameters: Mapping[str, Any]) -> tuple[str | None, dict[str, str]]:
    if operation == "catalog-capabilities":
        if parameters:
            raise ValueError("catalog-capabilities accepts no parameters")
        return None, {}
    path = PATHS.get(operation)
    if path is None:
        raise ValueError(f"unsupported operation: {operation}")
    _validate_ranges(parameters)
    query: dict[str, str] = {"file_type": "json"}
    for name, raw in parameters.items():
        if raw in (None, ""):
            continue
        if name in DATE_KEYS:
            query[name] = _date_value(raw, name)
        elif name in ARRAY_SEPARATORS:
            if not isinstance(raw, list) or not raw:
                raise ValueError(f"{name} must be a non-empty list")
            query[name] = ARRAY_SEPARATORS[name].join(str(item) for item in raw)
        elif isinstance(raw, bool):
            query[name] = "true" if raw else "false"
        else:
            query[name] = str(raw)
    if operation in PAGINATED:
        query["limit"] = str(
            bounded_int(parameters.get("limit"), default=1000, minimum=1, maximum=1000, name="limit")
        )
        query["offset"] = str(
            bounded_int(parameters.get("offset"), default=0, minimum=0, maximum=100000, name="offset")
        )
    return path, query


def _row_count(payload: Any) -> int:
    if not isinstance(payload, Mapping):
        return len(payload) if isinstance(payload, list) else 0
    for name in (
        "observations",
        "seriess",
        "categories",
        "releases",
        "release_dates",
        "sources",
        "tags",
        "vintage_dates",
    ):
        value = payload.get(name)
        if isinstance(value, list):
            return len(value)
    return 1 if payload else 0


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
    status = "INTEL_FRED_FAILED"
    failure: Mapping[str, Any] | None = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "api_host": "api.stlouisfed.org",
        "api_version": "v1",
        "credential_mode": "api_key_query_backend_only",
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
            if not API_KEY_RE.fullmatch(secret):
                raise RuntimeError(f"{SECRET_ENV} must be a 32-character lowercase alphanumeric FRED API key")
            safe_query_names = sorted(query)
            upstream_query = dict(query)
            upstream_query["api_key"] = secret
            response = requests.get(
                ORIGIN + path,
                params=upstream_query,
                headers={"Accept": "application/json", "User-Agent": "gpts-intelligence-center-fred/1"},
                timeout=timeout,
                allow_redirects=False,
            )
            raw = bytes(response.content or b"")
            metadata.update(
                {
                    "upstream_called": True,
                    "request_path": path,
                    "query_parameter_names": safe_query_names,
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
                raise RuntimeError("FRED returned invalid JSON") from exc
            if not response.ok or (isinstance(payload, Mapping) and payload.get("error_code")):
                detail = str(payload)[:1500].replace(secret, "[REDACTED]")
                raise RuntimeError(f"FRED HTTP {response.status_code}: {detail}")
            (output_dir / "response.json").write_bytes(raw)
            snapshot = {
                "provider": "fred",
                "operation": operation,
                "row_count": _row_count(payload),
                "data": payload,
            }
            metadata.update(
                {
                    "response_sha256": bytes_sha(raw),
                    "row_count": _row_count(payload),
                }
            )
        status = "INTEL_FRED_COMPLETED"
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
        schema_prefix="fred",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-fred]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="fred-ticket-status-v1",
            display_name="FRED",
        )
    )
