#!/usr/bin/env python3
"""Bounded free-plan Marketstack execution for Intelligence Center tickets."""
from __future__ import annotations

import os
import re
import sys
import time
from datetime import date
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
ORIGIN = "https://api.marketstack.com"
API_PREFIX = "/v2"
SECRET_ENV = "MARKETSTACK_ACCESS_KEY"
SYMBOL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,31}$")
MIC_RE = re.compile(r"^[A-Z0-9]{2,12}$")
SEARCH_RE = re.compile(r"^[^\x00-\x1f\x7f/?#\\]{1,100}$")


def _symbols(parameters: Mapping[str, Any]) -> str:
    raw = parameters.get("symbols")
    if not isinstance(raw, list) or not raw or len(raw) > 5:
        raise ValueError("symbols must contain 1 to 5 ticker symbols")
    values = [str(item).upper() for item in raw]
    if len(values) != len(set(values)):
        raise ValueError("symbols must be unique")
    if any(not SYMBOL_RE.fullmatch(value) for value in values):
        raise ValueError("symbols contains an invalid ticker")
    return ",".join(values)


def _symbol(parameters: Mapping[str, Any]) -> str:
    value = str(parameters.get("symbol") or "").upper()
    if not SYMBOL_RE.fullmatch(value):
        raise ValueError("symbol is invalid")
    return value


def _date_value(parameters: Mapping[str, Any], name: str, *, required: bool = False) -> str | None:
    raw = parameters.get(name)
    if raw in (None, ""):
        if required:
            raise ValueError(f"{name} is required")
        return None
    value = str(raw)
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be YYYY-MM-DD") from exc
    return value


def _bounded_history(parameters: Mapping[str, Any]) -> tuple[str | None, str | None]:
    start = _date_value(parameters, "date_from")
    end = _date_value(parameters, "date_to")
    if start and end:
        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end)
        if start_date > end_date:
            raise ValueError("date_from must not be after date_to")
        if (end_date - start_date).days > 366:
            raise ValueError("free-plan history span must not exceed 366 days")
    return start, end


def _page_query(parameters: Mapping[str, Any]) -> dict[str, str]:
    limit = bounded_int(parameters.get("limit"), default=100, minimum=1, maximum=100, name="limit")
    offset = bounded_int(parameters.get("offset"), default=0, minimum=0, maximum=10000, name="offset")
    return {"limit": str(limit), "offset": str(offset)}


def build_request(operation: str, parameters: Mapping[str, Any]) -> tuple[str | None, dict[str, str]]:
    if operation == "catalog-capabilities":
        return None, {}

    query = _page_query(parameters)
    if operation in {"eod-latest", "eod-history", "eod-by-date", "dividends", "splits"}:
        query["symbols"] = _symbols(parameters)

    if operation == "eod-latest":
        return API_PREFIX + "/eod/latest", query
    if operation == "eod-history":
        start, end = _bounded_history(parameters)
        if start:
            query["date_from"] = start
        if end:
            query["date_to"] = end
        sort = str(parameters.get("sort") or "DESC").upper()
        if sort not in {"ASC", "DESC"}:
            raise ValueError("sort must be ASC or DESC")
        query["sort"] = sort
        return API_PREFIX + "/eod", query
    if operation == "eod-by-date":
        value = _date_value(parameters, "date", required=True)
        return API_PREFIX + "/eod/" + quote(str(value), safe="-"), query
    if operation in {"dividends", "splits"}:
        start, end = _bounded_history(parameters)
        if start:
            query["date_from"] = start
        if end:
            query["date_to"] = end
        return API_PREFIX + "/" + operation, query
    if operation == "tickers-list":
        search = parameters.get("search")
        if search not in (None, ""):
            value = str(search)
            if not SEARCH_RE.fullmatch(value):
                raise ValueError("search is invalid")
            query["search"] = value
        exchange = parameters.get("exchange")
        if exchange not in (None, ""):
            value = str(exchange).upper()
            if not MIC_RE.fullmatch(value):
                raise ValueError("exchange must be a valid MIC-style code")
            query["exchange"] = value
        return API_PREFIX + "/tickerslist", query
    if operation == "ticker-info":
        return API_PREFIX + "/tickers/" + quote(_symbol(parameters), safe="._:-"), {}
    if operation == "exchanges-list":
        return API_PREFIX + "/exchanges", query
    if operation == "currencies-list":
        return API_PREFIX + "/currencies", query
    if operation == "timezones-list":
        return API_PREFIX + "/timezones", query
    raise ValueError(f"unsupported operation: {operation}")


def _row_count(value: Any) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, Mapping):
        data = value.get("data")
        if isinstance(data, list):
            return len(data)
        if isinstance(data, Mapping):
            for key in ("eod", "intraday", "splits", "dividends"):
                nested = data.get(key)
                if isinstance(nested, list):
                    return len(nested)
            return 1
        return 1
    return 0


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
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_MARKETSTACK_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "api_origin": "api.marketstack.com",
        "api_version": "v2",
        "credential_mode": "access_key_query_backend_only",
        "secret_environment_variable": SECRET_ENV,
        "secret_values_exposed": False,
        "requests_per_ticket": 1,
        "automatic_retry": False,
        "automatic_pagination": False,
        "free_plan_contract": True,
    }
    secret = str(os.environ.get(SECRET_ENV) or "").strip()
    try:
        path, query = build_request(operation, parameters)
        if path is None:
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        else:
            if not secret:
                raise RuntimeError(f"{SECRET_ENV} is not configured")
            safe_query_names = sorted(query)
            upstream_query = dict(query)
            upstream_query["access_key"] = secret
            response = requests.get(
                ORIGIN + path,
                params=upstream_query,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "intelligence-center-marketstack/1",
                },
                timeout=timeout,
                allow_redirects=False,
            )
            raw = response.content
            if len(raw) > max_bytes:
                raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
            try:
                data = response.json()
            except ValueError as exc:
                raise RuntimeError("Marketstack returned invalid JSON") from exc
            if not response.ok:
                detail = str(data)[:1000].replace(secret, "[REDACTED]")
                raise RuntimeError(f"Marketstack HTTP {response.status_code}: {detail}")
            if isinstance(data, Mapping) and data.get("error"):
                detail = str(data.get("error"))[:1000].replace(secret, "[REDACTED]")
                raise RuntimeError(f"Marketstack business error: {detail}")
            snapshot = {
                "provider": "marketstack",
                "operation": operation,
                "row_count": _row_count(data),
                "data": data,
            }
            (output_dir / "response.json").write_bytes(raw)
            metadata.update(
                {
                    "upstream_called": True,
                    "http_status": response.status_code,
                    "content_type": response.headers.get("Content-Type", ""),
                    "request_path": path,
                    "query_parameter_names": safe_query_names,
                    "response_bytes": len(raw),
                    "response_sha256": bytes_sha(raw),
                    "row_count": _row_count(data),
                    "symbol_count": len(parameters.get("symbols") or [])
                    if isinstance(parameters.get("symbols"), list)
                    else (1 if parameters.get("symbol") else 0),
                }
            )
        status = "INTEL_MARKETSTACK_COMPLETED"
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
        schema_prefix="marketstack",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-marketstack]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="marketstack-ticket-status-v1",
            display_name="Marketstack",
        )
    )
