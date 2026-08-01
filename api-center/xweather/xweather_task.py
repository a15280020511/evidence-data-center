#!/usr/bin/env python3
"""Bounded read-only Xweather Weather API execution."""
from __future__ import annotations

import json
import os
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
ORIGIN = "https://data.api.xweather.com"
CLIENT_ID_ENV = "XWEATHER_CLIENT_ID"
CLIENT_SECRET_ENV = "XWEATHER_CLIENT_SECRET"


class XweatherError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def credentials() -> tuple[str, str]:
    client_id = str(os.getenv(CLIENT_ID_ENV) or "").strip()
    client_secret = str(os.getenv(CLIENT_SECRET_ENV) or "").strip()
    if not client_id:
        raise XweatherError(
            "XWEATHER_CLIENT_ID_MISSING",
            f"missing repository Variable {CLIENT_ID_ENV}",
        )
    if not client_secret:
        raise XweatherError(
            "XWEATHER_CLIENT_SECRET_MISSING",
            f"missing repository Secret {CLIENT_SECRET_ENV}",
        )
    for name, value in ((CLIENT_ID_ENV, client_id), (CLIENT_SECRET_ENV, client_secret)):
        if not 8 <= len(value) <= 512:
            raise XweatherError("XWEATHER_CREDENTIAL_INVALID", f"invalid {name} length")
        if any(ord(char) < 0x21 or ord(char) > 0x7E for char in value):
            raise XweatherError("XWEATHER_CREDENTIAL_INVALID", f"invalid {name} characters")
    return client_id, client_secret


def operation_row(operation: str) -> Mapping[str, Any]:
    row = operation_map(CATALOG_PATH).get(operation)
    if row is None:
        raise ValueError(f"unsupported Xweather operation: {operation}")
    return row


def build_request(operation: str, parameters: Mapping[str, Any]) -> tuple[str | None, dict[str, str], dict[str, Any]]:
    row = operation_row(operation)
    execution = row["execution"]
    if execution.get("local") is True:
        return None, {}, {
            "request_origin": "local",
            "http_method": "LOCAL",
            "credential_mode": "none",
            "secret_value_exposed": False,
        }
    path = str(execution["path_template"])
    clean = dict(parameters)
    for name in execution.get("path_parameters") or []:
        value = clean.pop(name)
        path = path.replace("{" + name + "}", quote(str(value), safe=",._@+-"))
    query_map = dict(execution.get("query_parameter_map") or {})
    query: dict[str, str] = {}
    for name, value in clean.items():
        if value in (None, ""):
            continue
        query[str(query_map.get(name) or name)] = str(value)
    return ORIGIN + path, query, {
        "request_origin": "data.api.xweather.com",
        "request_path": path,
        "http_method": "GET",
        "credential_mode": "client-id-variable-plus-client-secret-backend-only",
        "credential_environment_variables": [CLIENT_ID_ENV, CLIENT_SECRET_ENV],
        "secret_value_exposed": False,
        "redirects_allowed": False,
        "query_parameter_names": sorted(query),
    }


def result_rows(payload: Any) -> int:
    if not isinstance(payload, Mapping):
        return len(payload) if isinstance(payload, list) else 1
    response = payload.get("response")
    if isinstance(response, list):
        total = len(response)
        for item in response:
            if isinstance(item, Mapping):
                periods = item.get("periods")
                if isinstance(periods, list):
                    total += len(periods)
        return total
    return 1


def query_xweather(
    operation: str,
    parameters: Mapping[str, Any],
    *,
    timeout: int,
    max_bytes: int,
    max_rows: int,
) -> tuple[Any, dict[str, Any]]:
    client_id, client_secret = credentials()
    url, query, metadata = build_request(operation, parameters)
    if url is None:
        raise ValueError("local operations must not call query_xweather")
    upstream_query = dict(query)
    upstream_query["client_id"] = client_id
    upstream_query["client_secret"] = client_secret
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "User-Agent": "gpts-evidence-data-center-xweather/1",
    }
    attempts = 0
    while attempts < 2:
        attempts += 1
        try:
            response = requests.get(
                url,
                params=upstream_query,
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
            raise XweatherError(
                "XWEATHER_CONNECTION_FAILED",
                f"upstream connection failed: {type(exc).__name__}",
                retryable=True,
            ) from exc
        if len(raw) > max_bytes:
            raise XweatherError(
                "XWEATHER_RESPONSE_TOO_LARGE",
                "upstream response exceeded max_response_bytes",
            )
        if response.is_redirect:
            raise XweatherError(
                "XWEATHER_REDIRECT_REJECTED",
                f"upstream attempted HTTP {response.status_code} redirect",
            )
        if response.status_code == 429 or 500 <= response.status_code <= 599:
            if attempts < 2:
                time.sleep(1.0)
                continue
            raise XweatherError(
                "XWEATHER_HTTP_TRANSIENT",
                f"upstream HTTP {response.status_code}",
                retryable=True,
            )
        if response.status_code in {401, 403}:
            raise XweatherError(
                "XWEATHER_CREDENTIAL_OR_PLAN_DENIED",
                f"upstream HTTP {response.status_code}",
            )
        if not 200 <= response.status_code < 300:
            raise XweatherError("XWEATHER_HTTP_ERROR", f"upstream HTTP {response.status_code}")
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else None
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise XweatherError("XWEATHER_INVALID_JSON", "upstream returned invalid JSON") from exc
        if isinstance(payload, Mapping) and payload.get("success") is False:
            error = payload.get("error") if isinstance(payload.get("error"), Mapping) else {}
            code = str(error.get("code") or "unknown")
            description = str(error.get("description") or error.get("message") or "request failed")
            raise XweatherError("XWEATHER_BUSINESS_ERROR", f"Xweather {code}: {description[:500]}")
        rows = result_rows(payload)
        if rows > max_rows:
            raise XweatherError(
                "XWEATHER_RESULT_TOO_MANY_ROWS",
                f"upstream result has {rows} rows; max_rows is {max_rows}",
            )
        metadata.update(
            {
                "http_status": response.status_code,
                "content_type": response.headers.get("Content-Type", ""),
                "response_bytes": len(raw),
                "result_rows": rows,
                "attempts": attempts,
            }
        )
        return payload, metadata
    raise AssertionError("unreachable")


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(
        acceptance.get("timeout_seconds"),
        default=45,
        minimum=5,
        maximum=120,
        name="timeout_seconds",
    )
    max_bytes = bounded_int(
        acceptance.get("max_response_bytes"),
        default=5_000_000,
        minimum=1024,
        maximum=20_000_000,
        name="max_response_bytes",
    )
    max_rows = bounded_int(
        acceptance.get("max_rows"),
        default=500,
        minimum=1,
        maximum=5000,
        name="max_rows",
    )
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "API_XWEATHER_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "api_origin": "data.api.xweather.com",
        "credential_mode": "client-id-variable-plus-client-secret-backend-only",
        "secret_values_exposed": False,
    }
    try:
        if operation == "catalog-capabilities":
            snapshot = {"provider": provider_row(CATALOG_PATH)}
            metadata["credential_mode"] = "none"
        else:
            payload, request_metadata = query_xweather(
                operation,
                parameters,
                timeout=timeout,
                max_bytes=max_bytes,
                max_rows=max_rows,
            )
            metadata.update(request_metadata)
            metadata["upstream_called"] = True
            snapshot = {
                "provider": "xweather",
                "operation": operation,
                "data": payload,
            }
        status = "API_XWEATHER_COMPLETED"
    except Exception as exc:
        message = str(exc)
        for env_name in (CLIENT_ID_ENV, CLIENT_SECRET_ENV):
            value = str(os.getenv(env_name) or "")
            if value:
                message = message.replace(value, "[REDACTED]")
        failure = {
            "type": type(exc).__name__,
            "code": getattr(exc, "code", "XWEATHER_EXECUTION_ERROR"),
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
        schema_prefix="xweather",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[api-xweather]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="xweather-ticket-status-v1",
            display_name="Xweather",
        )
    )
