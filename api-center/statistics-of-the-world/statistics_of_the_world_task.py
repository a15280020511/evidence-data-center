#!/usr/bin/env python3
"""Bounded read-only Statistics of the World execution."""
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
BASE_URL = "https://statisticsoftheworld.com"
API_HOST = "statisticsoftheworld.com"
API_KEY_ENV = "SOTW_API_KEY"
COUNTRY_RE = re.compile(r"^[A-Z]{3}$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{1,127}$")
SEARCH_RE = re.compile(r"^[A-Za-z0-9 ()%+.,/_-]{2,100}$")


class SOTWError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def optional_api_key() -> str:
    value = str(os.getenv(API_KEY_ENV) or "").strip()
    if not value:
        return ""
    if not 8 <= len(value) <= 512:
        raise SOTWError("SOTW_API_KEY_INVALID", "configured SOTW_API_KEY has invalid length")
    if any(ord(char) < 0x21 or ord(char) > 0x7E for char in value):
        raise SOTWError("SOTW_API_KEY_INVALID", "configured SOTW_API_KEY has invalid characters")
    return value


def _country(value: Any) -> str:
    text = str(value or "")
    if not COUNTRY_RE.fullmatch(text):
        raise ValueError("country must be an ISO alpha-3 code")
    return text


def _identifier(value: Any, name: str) -> str:
    text = str(value or "")
    if not IDENTIFIER_RE.fullmatch(text):
        raise ValueError(f"{name} is invalid")
    return text


def build_request(operation: str, parameters: Mapping[str, Any]) -> tuple[str | None, dict[str, str], dict[str, Any]]:
    if operation == "catalog-capabilities":
        return None, {}, {"http_method": "LOCAL", "request_origin": "local"}
    query: dict[str, str] = {}
    if operation == "list-countries":
        path = "/api/v1/countries"
    elif operation == "get-country":
        path = "/api/v1/countries/" + quote(_country(parameters.get("country")), safe="")
    elif operation == "list-indicators":
        path = "/api/v1/indicators"
    elif operation == "get-indicator":
        path = "/api/v1/indicators/" + quote(_identifier(parameters.get("indicator"), "indicator"), safe="._-")
    elif operation == "get-history":
        path = "/api/v2/history"
        query = {
            "indicator": _identifier(parameters.get("indicator"), "indicator"),
            "country": _country(parameters.get("country")),
        }
    elif operation == "get-rankings":
        indicator = _identifier(parameters.get("indicator"), "indicator")
        path = "/api/v1/rankings/" + quote(indicator, safe="._-")
        query["limit"] = str(bounded_int(parameters.get("limit"), default=100, minimum=1, maximum=500, name="limit"))
    elif operation == "search-indicators":
        text = str(parameters.get("query") or "")
        if not SEARCH_RE.fullmatch(text):
            raise ValueError("query contains unsupported characters")
        path = "/api/v1/search"
        query["q"] = text
    elif operation == "compare-countries":
        countries = parameters.get("countries")
        if not isinstance(countries, list) or not 2 <= len(countries) <= 10:
            raise ValueError("countries must contain 2 to 10 ISO alpha-3 codes")
        normalized = [_country(value) for value in countries]
        if len(set(normalized)) != len(normalized):
            raise ValueError("countries must be unique")
        path = "/api/v1/compare"
        query["countries"] = ",".join(normalized)
    elif operation == "list-series":
        path = "/api/v1/series"
    elif operation == "get-series":
        series = _identifier(parameters.get("series"), "series")
        path = "/api/v1/series/" + quote(series, safe="._-")
        if parameters.get("geo"):
            query["geo"] = _country(parameters.get("geo"))
        if parameters.get("from"):
            from_date = str(parameters["from"])
            try:
                time.strptime(from_date, "%Y-%m-%d")
            except ValueError as exc:
                raise ValueError("from must be YYYY-MM-DD") from exc
            query["from"] = from_date
        if parameters.get("latest") is not None:
            query["latest"] = "1" if bool(parameters["latest"]) else "0"
    else:
        raise ValueError(f"unsupported operation: {operation}")
    return BASE_URL + path, query, {
        "http_method": "GET",
        "request_origin": API_HOST,
        "request_path": path,
        "credential_mode": "optional-x-api-key-backend-only",
        "credential_environment_variable": API_KEY_ENV,
        "secret_value_exposed": False,
        "redirects_allowed": False,
        "automatic_pagination_allowed": False,
        "bulk_download_allowed": False,
        "parameter_names": sorted(query),
    }


def _row_count(payload: Any) -> int:
    if isinstance(payload, Mapping):
        data = payload.get("data")
        if isinstance(data, list):
            return len(data)
        indicators = payload.get("indicators")
        if isinstance(indicators, list):
            return len(indicators)
        count = payload.get("count")
        if isinstance(count, int) and count >= 0:
            return count
    if isinstance(payload, list):
        return len(payload)
    return 1


def query_sotw(operation: str, parameters: Mapping[str, Any], *, timeout: int, max_bytes: int, max_rows: int) -> tuple[Any, dict[str, Any]]:
    url, query, metadata = build_request(operation, parameters)
    if url is None:
        raise ValueError("local operation must not call query_sotw")
    key = optional_api_key()
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "User-Agent": "evidence-intelligence-center-sotw/1",
    }
    if key:
        headers["X-API-Key"] = key
    try:
        response = requests.get(url, params=query, headers=headers, timeout=timeout, allow_redirects=False, stream=True)
        raw = response.raw.read(max_bytes + 1, decode_content=True)
    except requests.RequestException as exc:
        raise SOTWError("SOTW_CONNECTION_FAILED", type(exc).__name__, retryable=True) from exc
    if len(raw) > max_bytes:
        raise SOTWError("SOTW_RESPONSE_TOO_LARGE", "response exceeded max_response_bytes")
    if response.is_redirect:
        raise SOTWError("SOTW_REDIRECT_REJECTED", f"upstream attempted HTTP {response.status_code} redirect")
    try:
        payload = json.loads(raw.decode("utf-8")) if raw else None
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SOTWError("SOTW_INVALID_JSON", "upstream returned invalid JSON") from exc
    message = ""
    if isinstance(payload, Mapping):
        message = str(payload.get("message") or payload.get("error") or "")[:1000]
    if response.status_code == 401:
        raise SOTWError("SOTW_CREDENTIAL_DENIED", message or "upstream HTTP 401")
    if response.status_code == 403:
        raise SOTWError("SOTW_PLAN_OR_LICENSE_RESTRICTED", message or "upstream HTTP 403")
    if response.status_code == 429:
        raise SOTWError("SOTW_RATE_LIMITED", message or "upstream HTTP 429", retryable=True)
    if response.status_code >= 500:
        raise SOTWError("SOTW_HTTP_TRANSIENT", f"upstream HTTP {response.status_code}", retryable=True)
    if not 200 <= response.status_code < 300:
        raise SOTWError("SOTW_HTTP_ERROR", message or f"upstream HTTP {response.status_code}")
    rows = _row_count(payload)
    if rows > max_rows and operation not in {"list-countries", "list-indicators", "list-series"}:
        raise SOTWError("SOTW_RESULT_TOO_LARGE", f"row count {rows} exceeds max_rows={max_rows}")
    metadata.update({
        "http_status": response.status_code,
        "content_type": response.headers.get("Content-Type", ""),
        "response_bytes": len(raw),
        "response_sha256": bytes_sha(raw),
        "row_count": rows,
        "api_key_configured": bool(key),
        "rate_limit_limit": response.headers.get("X-RateLimit-Limit", ""),
        "rate_limit_remaining": response.headers.get("X-RateLimit-Remaining", ""),
        "rate_limit_reset": response.headers.get("X-RateLimit-Reset", ""),
        "rate_limit_tier": response.headers.get("X-RateLimit-Tier", ""),
    })
    return payload, metadata


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(acceptance.get("timeout_seconds"), default=30, minimum=5, maximum=60, name="timeout_seconds")
    max_bytes = bounded_int(acceptance.get("max_response_bytes"), default=5_000_000, minimum=1024, maximum=10_000_000, name="max_response_bytes")
    max_rows = bounded_int(acceptance.get("max_rows"), default=500, minimum=1, maximum=500, name="max_rows")
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_SOTW_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "api_origin": API_HOST,
        "secret_values_exposed": False,
        "authoritative_single_source": False,
        "source_attribution_required": True,
    }
    try:
        if operation == "catalog-capabilities":
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        else:
            payload, request_metadata = query_sotw(operation, parameters, timeout=timeout, max_bytes=max_bytes, max_rows=max_rows)
            raw = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
            (output_dir / "response.json").write_bytes(raw)
            metadata.update(request_metadata)
            metadata["upstream_called"] = True
            snapshot = {"provider": "statistics-of-the-world", "operation": operation, "row_count": request_metadata["row_count"], "data": payload}
        status = "INTEL_SOTW_COMPLETED"
    except Exception as exc:
        failure = {
            "type": type(exc).__name__,
            "code": getattr(exc, "code", type(exc).__name__),
            "message": str(exc)[:2000],
            "retryable": bool(getattr(exc, "retryable", False)),
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
        schema_prefix="statistics-of-the-world",
    )


if __name__ == "__main__":
    raise SystemExit(run_cli(
        execute=execute,
        ticket_prefix="[intel-sotw]",
        schema_path=SCHEMA_PATH,
        catalog_path=CATALOG_PATH,
        status_schema="statistics-of-the-world-ticket-status-v1",
        display_name="Statistics of the World",
    ))
