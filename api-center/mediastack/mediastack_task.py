#!/usr/bin/env python3
"""Bounded read-only Mediastack execution for Intelligence Center tickets."""
from __future__ import annotations

import json
import os
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
    finish_execution,
    load_json,
    operation_map,
    provider_row,
    run_cli,
    utc_now,
    validate_ticket,
)

SCHEMA_PATH = HERE / "ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"
ORIGIN = "https://api.mediastack.com"
API_HOST = "api.mediastack.com"
API_KEY_ENV = "MEDIASTACK_API_KEY"
MAX_REQUEST_ROWS = 100
MAX_OFFSET = 10_000
MAX_DATE_RANGE_DAYS = 366


class MediastackError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def api_key() -> str:
    value = str(os.getenv(API_KEY_ENV) or "").strip()
    if not value:
        raise MediastackError(
            "MEDIASTACK_API_KEY_MISSING",
            f"missing repository Secret {API_KEY_ENV}",
        )
    if not 8 <= len(value) <= 512:
        raise MediastackError(
            "MEDIASTACK_API_KEY_INVALID",
            f"invalid repository Secret {API_KEY_ENV} length",
        )
    if any(ord(char) < 0x21 or ord(char) > 0x7E for char in value):
        raise MediastackError(
            "MEDIASTACK_API_KEY_INVALID",
            f"invalid repository Secret {API_KEY_ENV} characters",
        )
    return value


def operation_row(operation: str) -> Mapping[str, Any]:
    row = operation_map(CATALOG_PATH).get(operation)
    if row is None:
        raise ValueError(f"unsupported Mediastack operation: {operation}")
    return row


def _comma_join(value: Any) -> str:
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    return str(value)


def _validate_date_filter(value: str) -> None:
    parts = value.split(",")
    if len(parts) not in {1, 2}:
        raise ValueError("date must be YYYY-MM-DD or YYYY-MM-DD,YYYY-MM-DD")
    parsed = [date.fromisoformat(part) for part in parts]
    if len(parsed) == 2:
        if parsed[1] < parsed[0]:
            raise ValueError("date range end must not precede start")
        if (parsed[1] - parsed[0]).days > MAX_DATE_RANGE_DAYS:
            raise ValueError(f"date range exceeds {MAX_DATE_RANGE_DAYS} days")


def build_request(
    operation: str,
    parameters: Mapping[str, Any],
) -> tuple[str | None, dict[str, str], dict[str, Any]]:
    row = operation_row(operation)
    execution = dict(row.get("execution") or {})
    if execution.get("local") is True:
        return None, {}, {
            "request_origin": "local",
            "http_method": "LOCAL",
            "credential_mode": "none",
            "secret_value_exposed": False,
        }
    path = str(execution.get("path_template") or "")
    expected_path = "/v1/sources" if operation == "list-sources" else "/v1/news"
    if path != expected_path:
        raise ValueError("provider catalog path does not match operation")
    clean = dict(parameters)
    if "date" in clean:
        _validate_date_filter(str(clean["date"]))
    limit = bounded_int(
        clean.get("limit"),
        default=25,
        minimum=1,
        maximum=MAX_REQUEST_ROWS,
        name="limit",
    )
    offset = bounded_int(
        clean.get("offset"),
        default=0,
        minimum=0,
        maximum=MAX_OFFSET,
        name="offset",
    )
    query: dict[str, str] = {"limit": str(limit), "offset": str(offset)}
    for name, value in clean.items():
        if name in {"limit", "offset"} or value in (None, "", []):
            continue
        query[name] = _comma_join(value)
    return ORIGIN + path, query, {
        "request_origin": API_HOST,
        "request_path": path,
        "http_method": "GET",
        "credential_mode": "access-key-query-backend-only",
        "credential_environment_variable": API_KEY_ENV,
        "secret_value_exposed": False,
        "redirects_allowed": False,
        "automatic_pagination_allowed": False,
        "article_body_fetching_allowed": False,
        "parameter_names": sorted(query),
        "billable_or_quota_counted": True,
    }


def _safe_error_detail(payload: Any) -> tuple[str, str]:
    if not isinstance(payload, Mapping):
        return "", ""
    error = payload.get("error")
    if not isinstance(error, Mapping):
        return "", ""
    return str(error.get("code") or ""), str(error.get("message") or "")


def query_mediastack(
    operation: str,
    parameters: Mapping[str, Any],
    *,
    timeout: int,
    max_bytes: int,
    max_rows: int,
) -> tuple[Any, dict[str, Any]]:
    url, query, metadata = build_request(operation, parameters)
    if url is None:
        raise ValueError("local operations must not call query_mediastack")
    secret = api_key()
    request_query = dict(query)
    request_query["access_key"] = secret
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "User-Agent": "evidence-intelligence-center-mediastack/1",
    }
    attempts = 0
    while attempts < 2:
        attempts += 1
        try:
            response = requests.get(
                url,
                params=request_query,
                headers=headers,
                timeout=timeout,
                allow_redirects=False,
                stream=True,
            )
            raw = response.raw.read(max_bytes + 1, decode_content=True)
        except requests.RequestException as exc:
            if attempts < 2:
                time.sleep(1.0)
                continue
            raise MediastackError(
                "MEDIASTACK_CONNECTION_FAILED",
                type(exc).__name__,
                retryable=True,
            ) from exc
        if len(raw) > max_bytes:
            raise MediastackError(
                "MEDIASTACK_RESPONSE_TOO_LARGE",
                "upstream response exceeded max_response_bytes",
            )
        if response.is_redirect:
            raise MediastackError(
                "MEDIASTACK_REDIRECT_REJECTED",
                f"upstream attempted HTTP {response.status_code} redirect",
            )
        if response.status_code == 429 or response.status_code >= 500:
            if attempts < 2:
                time.sleep(1.0)
                continue
            raise MediastackError(
                "MEDIASTACK_HTTP_TRANSIENT",
                f"upstream HTTP {response.status_code}",
                retryable=True,
            )
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else None
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MediastackError(
                "MEDIASTACK_INVALID_JSON",
                "upstream returned invalid JSON",
            ) from exc

        code, message = _safe_error_detail(payload)
        if response.status_code in {401, 403} or code in {
            "invalid_access_key",
            "missing_access_key",
        }:
            raise MediastackError(
                "MEDIASTACK_CREDENTIAL_DENIED",
                message or f"upstream HTTP {response.status_code}",
            )
        if code in {"usage_limit_reached", "rate_limit_reached"}:
            raise MediastackError(
                "MEDIASTACK_QUOTA_OR_RATE_LIMITED",
                message or code,
                retryable=code == "rate_limit_reached",
            )
        if code in {
            "function_access_restricted",
            "https_access_restricted",
        }:
            raise MediastackError(
                "MEDIASTACK_PLAN_REQUIRED",
                message or code,
            )
        if not 200 <= response.status_code < 300:
            raise MediastackError(
                "MEDIASTACK_HTTP_ERROR",
                message or f"upstream HTTP {response.status_code}",
            )
        if code:
            raise MediastackError(
                "MEDIASTACK_BUSINESS_ERROR",
                message or code,
            )
        if not isinstance(payload, Mapping):
            raise MediastackError(
                "MEDIASTACK_RESULT_INVALID",
                "upstream response must be a JSON object",
            )
        rows = payload.get("data")
        if not isinstance(rows, list):
            raise MediastackError(
                "MEDIASTACK_DATA_MISSING",
                "upstream response did not contain a data array",
            )
        if len(rows) > max_rows:
            raise MediastackError(
                "MEDIASTACK_RESULT_TOO_MANY_ROWS",
                f"upstream returned {len(rows)} rows; max_rows is {max_rows}",
            )
        metadata.update({
            "http_status": response.status_code,
            "content_type": response.headers.get("Content-Type", ""),
            "response_bytes": len(raw),
            "row_count": len(rows),
            "attempts": attempts,
            "upstream_called": True,
        })
        return payload, metadata
    raise AssertionError("unreachable")


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(
        ticket,
        schema_path=SCHEMA_PATH,
        catalog_path=CATALOG_PATH,
    )
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(
        acceptance.get("timeout_seconds"),
        default=45,
        minimum=5,
        maximum=90,
        name="timeout_seconds",
    )
    max_bytes = bounded_int(
        acceptance.get("max_response_bytes"),
        default=5_000_000,
        minimum=1024,
        maximum=10_000_000,
        name="max_response_bytes",
    )
    max_rows = bounded_int(
        acceptance.get("max_rows"),
        default=100,
        minimum=1,
        maximum=100,
        name="max_rows",
    )
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_MEDIASTACK_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "api_origin": API_HOST,
        "credential_mode": "access-key-query-backend-only",
        "secret_values_exposed": False,
        "one_request_per_ticket": True,
        "automatic_pagination_allowed": False,
        "article_body_fetching_allowed": False,
        "free_plan_requests_per_month": 100,
        "free_plan_delayed_news": True,
    }
    try:
        if operation == "catalog-capabilities":
            snapshot = {"provider": provider_row(CATALOG_PATH)}
            metadata["credential_mode"] = "none"
        else:
            payload, request_metadata = query_mediastack(
                operation,
                parameters,
                timeout=timeout,
                max_bytes=max_bytes,
                max_rows=max_rows,
            )
            metadata.update(request_metadata)
            snapshot = {
                "provider": "mediastack",
                "operation": operation,
                "data": payload,
            }
        status = "INTEL_MEDIASTACK_COMPLETED"
    except Exception as exc:
        message = str(exc)
        secret = str(os.getenv(API_KEY_ENV) or "")
        if secret:
            message = message.replace(secret, "[REDACTED]")
        failure = {
            "type": type(exc).__name__,
            "code": getattr(exc, "code", "MEDIASTACK_EXECUTION_ERROR"),
            "retryable": bool(getattr(exc, "retryable", False)),
            "message": message[:2000],
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
        schema_prefix="mediastack",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-mediastack]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="mediastack-ticket-status-v1",
            display_name="Mediastack 全球新闻情报",
        )
    )
