#!/usr/bin/env python3
"""Bounded read-only GNews execution for Intelligence Center tickets."""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
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
ORIGIN = "https://gnews.io"
API_HOST = "gnews.io"
API_KEY_ENV = "GNEWS_API_KEY"
MAX_ARTICLES = 10
MAX_PAGE = 100
MAX_DATE_RANGE_DAYS = 30


class GNewsError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def api_key() -> str:
    value = str(os.getenv(API_KEY_ENV) or "").strip()
    if not value:
        raise GNewsError("GNEWS_API_KEY_MISSING", f"missing repository Secret {API_KEY_ENV}")
    if not 8 <= len(value) <= 512:
        raise GNewsError("GNEWS_API_KEY_INVALID", f"invalid repository Secret {API_KEY_ENV} length")
    if any(ord(char) < 0x21 or ord(char) > 0x7E for char in value):
        raise GNewsError("GNEWS_API_KEY_INVALID", f"invalid repository Secret {API_KEY_ENV} characters")
    return value


def operation_row(operation: str) -> Mapping[str, Any]:
    row = operation_map(CATALOG_PATH).get(operation)
    if row is None:
        raise ValueError(f"unsupported GNews operation: {operation}")
    return row


def _iso8601(value: Any, *, name: str) -> datetime:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{name} must not be empty")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{name} must be ISO 8601 date-time") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _validate_dates(parameters: Mapping[str, Any]) -> None:
    start = _iso8601(parameters["from"], name="from") if "from" in parameters else None
    end = _iso8601(parameters["to"], name="to") if "to" in parameters else None
    if start and end:
        if end < start:
            raise ValueError("to must not precede from")
        if (end - start).days > MAX_DATE_RANGE_DAYS:
            raise ValueError(f"date range exceeds {MAX_DATE_RANGE_DAYS} days")


def _join_list(value: Any) -> str:
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    return str(value)


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

    expected_path = {
        "search-news": "/api/v4/search",
        "top-headlines": "/api/v4/top-headlines",
    }.get(operation)
    path = str(execution.get("path_template") or "")
    if path != expected_path:
        raise ValueError("provider catalog path does not match operation")

    clean = dict(parameters)
    if operation == "search-news":
        q = str(clean.get("q") or "").strip()
        if not q or len(q) > 200:
            raise ValueError("q must contain 1 to 200 characters")
    _validate_dates(clean)

    maximum = bounded_int(
        clean.get("max"), default=10, minimum=1, maximum=MAX_ARTICLES, name="max"
    )
    page = bounded_int(
        clean.get("page"), default=1, minimum=1, maximum=MAX_PAGE, name="page"
    )
    query: dict[str, str] = {"max": str(maximum), "page": str(page)}
    for name, value in clean.items():
        if name in {"max", "page"} or value in (None, "", []):
            continue
        query[name] = _join_list(value)

    return ORIGIN + path, query, {
        "request_origin": API_HOST,
        "request_path": path,
        "http_method": "GET",
        "credential_mode": "x-api-key-header-backend-only",
        "credential_environment_variable": API_KEY_ENV,
        "secret_value_exposed": False,
        "redirects_allowed": False,
        "automatic_pagination_allowed": False,
        "article_body_fetching_allowed": False,
        "parameter_names": sorted(query),
        "billable_or_quota_counted": True,
    }


def _safe_error_message(payload: Any) -> str:
    if not isinstance(payload, Mapping):
        return ""
    errors = payload.get("errors")
    if isinstance(errors, list):
        return "; ".join(str(item) for item in errors[:5])
    if isinstance(errors, Mapping):
        return "; ".join(f"{key}: {value}" for key, value in list(errors.items())[:5])
    return str(payload.get("message") or payload.get("error") or "")


def query_gnews(
    operation: str,
    parameters: Mapping[str, Any],
    *,
    timeout: int,
    max_bytes: int,
    max_rows: int,
) -> tuple[Mapping[str, Any], dict[str, Any]]:
    url, query, metadata = build_request(operation, parameters)
    if url is None:
        raise ValueError("local operations must not call query_gnews")
    secret = api_key()
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "User-Agent": "evidence-intelligence-center-gnews/1",
        "X-Api-Key": secret,
    }
    try:
        response = requests.get(
            url,
            params=query,
            headers=headers,
            timeout=timeout,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        raise GNewsError("GNEWS_CONNECTION_FAILED", type(exc).__name__, retryable=True) from exc

    raw = response.content
    if len(raw) > max_bytes:
        raise GNewsError("GNEWS_RESPONSE_TOO_LARGE", "upstream response exceeded max_response_bytes")
    if response.is_redirect:
        raise GNewsError("GNEWS_REDIRECT_REJECTED", f"upstream attempted HTTP {response.status_code} redirect")
    try:
        payload = json.loads(raw.decode("utf-8")) if raw else None
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GNewsError("GNEWS_INVALID_JSON", "upstream returned invalid JSON") from exc

    message = _safe_error_message(payload)
    if response.status_code == 401:
        raise GNewsError("GNEWS_CREDENTIAL_DENIED", message or "upstream HTTP 401")
    if response.status_code == 403:
        raise GNewsError("GNEWS_QUOTA_OR_PLAN_DENIED", message or "upstream HTTP 403")
    if response.status_code == 429:
        raise GNewsError("GNEWS_RATE_LIMITED", message or "upstream HTTP 429", retryable=True)
    if response.status_code >= 500:
        raise GNewsError("GNEWS_HTTP_TRANSIENT", f"upstream HTTP {response.status_code}", retryable=True)
    if not 200 <= response.status_code < 300:
        raise GNewsError("GNEWS_HTTP_ERROR", message or f"upstream HTTP {response.status_code}")
    if not isinstance(payload, Mapping):
        raise GNewsError("GNEWS_RESULT_INVALID", "upstream response must be a JSON object")
    articles = payload.get("articles")
    if not isinstance(articles, list):
        raise GNewsError("GNEWS_ARTICLES_MISSING", "upstream response did not contain an articles array")
    if len(articles) > max_rows:
        raise GNewsError(
            "GNEWS_RESULT_TOO_MANY_ROWS",
            f"upstream returned {len(articles)} articles; max_rows is {max_rows}",
        )

    metadata.update({
        "http_status": response.status_code,
        "content_type": response.headers.get("Content-Type", ""),
        "response_bytes": len(raw),
        "row_count": len(articles),
        "total_articles": payload.get("totalArticles"),
        "upstream_called": True,
        "requests_per_ticket": 1,
    })
    return payload, metadata


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(
        acceptance.get("timeout_seconds"), default=45, minimum=5, maximum=90, name="timeout_seconds"
    )
    max_bytes = bounded_int(
        acceptance.get("max_response_bytes"),
        default=5_000_000,
        minimum=1024,
        maximum=10_000_000,
        name="max_response_bytes",
    )
    max_rows = bounded_int(
        acceptance.get("max_rows"), default=10, minimum=1, maximum=10, name="max_rows"
    )
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_GNEWS_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "api_origin": API_HOST,
        "credential_mode": "x-api-key-header-backend-only",
        "secret_values_exposed": False,
        "one_request_per_ticket": True,
        "automatic_pagination_allowed": False,
        "article_body_fetching_allowed": False,
        "free_plan_requests_per_day": 100,
        "free_plan_delay_hours": 12,
        "free_plan_historical_days": 30,
        "free_plan_noncommercial_development_testing_only": True,
    }
    try:
        if operation == "catalog-capabilities":
            snapshot = {"provider": provider_row(CATALOG_PATH)}
            metadata["credential_mode"] = "none"
        else:
            payload, request_metadata = query_gnews(
                operation,
                parameters,
                timeout=timeout,
                max_bytes=max_bytes,
                max_rows=max_rows,
            )
            metadata.update(request_metadata)
            snapshot = {"provider": "gnews", "operation": operation, "data": payload}
        status = "INTEL_GNEWS_COMPLETED"
    except Exception as exc:
        message = str(exc)
        secret = str(os.getenv(API_KEY_ENV) or "")
        if secret:
            message = message.replace(secret, "[REDACTED]")
        failure = {
            "type": type(exc).__name__,
            "code": getattr(exc, "code", "GNEWS_EXECUTION_ERROR"),
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
        schema_prefix="gnews",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-gnews]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="gnews-ticket-status-v1",
            display_name="GNews 全球新闻情报",
        )
    )
