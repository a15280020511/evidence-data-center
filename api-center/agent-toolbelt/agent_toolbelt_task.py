#!/usr/bin/env python3
"""Bounded read-only Agent Toolbelt execution for API-center tickets."""
from __future__ import annotations

import ipaddress
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit

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
ORIGIN = "https://www.agenttoolbelt.live"
API_KEY_ENV = "AGENT_TOOLBELT_KEY"
MAX_REQUEST_BYTES = 15_000_000
URL_OPERATIONS = {"url-metadata", "web-summarizer"}


class AgentToolbeltError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def api_key() -> str:
    value = str(os.getenv(API_KEY_ENV) or "").strip()
    if not value:
        raise AgentToolbeltError(
            "AGENT_TOOLBELT_KEY_MISSING",
            f"missing repository Secret {API_KEY_ENV}",
        )
    if not 8 <= len(value) <= 512:
        raise AgentToolbeltError(
            "AGENT_TOOLBELT_KEY_INVALID",
            f"invalid repository Secret {API_KEY_ENV} length",
        )
    if not value.startswith("atb_"):
        raise AgentToolbeltError(
            "AGENT_TOOLBELT_KEY_INVALID",
            f"invalid repository Secret {API_KEY_ENV} prefix",
        )
    if any(ord(char) < 0x21 or ord(char) > 0x7E for char in value):
        raise AgentToolbeltError(
            "AGENT_TOOLBELT_KEY_INVALID",
            f"invalid repository Secret {API_KEY_ENV} characters",
        )
    return value


def operation_row(operation: str) -> Mapping[str, Any]:
    row = operation_map(CATALOG_PATH).get(operation)
    if row is None:
        raise ValueError(f"unsupported Agent Toolbelt operation: {operation}")
    return row


def validate_public_https_url(value: str) -> None:
    parsed = urlsplit(value)
    if parsed.scheme.lower() != "https":
        raise ValueError("URL inputs must use https")
    if not parsed.hostname:
        raise ValueError("URL input requires a hostname")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URL input must not contain credentials")
    host = parsed.hostname.rstrip(".").lower()
    if host in {"localhost", "localhost.localdomain"}:
        raise ValueError("localhost URL inputs are prohibited")
    if host.endswith((".localhost", ".local", ".internal", ".home", ".lan")):
        raise ValueError("private or local URL hostnames are prohibited")
    if len(host) > 253:
        raise ValueError("URL hostname is too long")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    ):
        raise ValueError(
            "private, loopback, link-local, reserved, or multicast IP URLs are prohibited"
        )


def validate_payload_shape(value: Any, *, depth: int = 0) -> None:
    if depth > 20:
        raise ValueError("request body nesting exceeds 20 levels")
    if value is None or isinstance(value, (bool, int, float, str)):
        return
    if isinstance(value, Mapping):
        if len(value) > 1000:
            raise ValueError("request object has too many keys")
        for key, item in value.items():
            if not isinstance(key, str) or len(key) > 256:
                raise ValueError("request object keys must be short strings")
            validate_payload_shape(item, depth=depth + 1)
        return
    if isinstance(value, list):
        if len(value) > 1000:
            raise ValueError("request array has too many items")
        for item in value:
            validate_payload_shape(item, depth=depth + 1)
        return
    raise ValueError(f"unsupported request value type: {type(value).__name__}")


def build_request(
    operation: str,
    parameters: Mapping[str, Any],
) -> tuple[str | None, bytes, dict[str, Any]]:
    row = operation_row(operation)
    execution = row["execution"]
    if execution.get("local") is True:
        return None, b"", {
            "request_origin": "local",
            "http_method": "LOCAL",
            "credential_mode": "none",
            "secret_value_exposed": False,
        }
    if operation in URL_OPERATIONS:
        validate_public_https_url(str(parameters["url"]))
    validate_payload_shape(parameters)
    encoded = json.dumps(
        parameters,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
    if len(encoded) > MAX_REQUEST_BYTES:
        raise ValueError(f"request body exceeds {MAX_REQUEST_BYTES} bytes")
    path = str(execution["path_template"])
    expected = f"/api/tools/{operation}"
    if path != expected:
        raise ValueError("provider catalog path does not match operation")
    return ORIGIN + path, encoded, {
        "request_origin": "www.agenttoolbelt.live",
        "request_path": path,
        "http_method": "POST",
        "credential_mode": "bearer-api-key-backend-only",
        "credential_environment_variable": API_KEY_ENV,
        "secret_value_exposed": False,
        "redirects_allowed": False,
        "request_bytes": len(encoded),
        "parameter_names": sorted(parameters),
        "billable_or_quota_counted": True,
        "upstream_llm_may_be_used": bool(
            row.get("result_contract", {}).get("upstream_llm_may_be_used")
        ),
    }


def query_agent_toolbelt(
    operation: str,
    parameters: Mapping[str, Any],
    *,
    timeout: int,
    max_bytes: int,
) -> tuple[Any, dict[str, Any]]:
    url, encoded, metadata = build_request(operation, parameters)
    if url is None:
        raise ValueError("local operations must not call query_agent_toolbelt")
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "Authorization": f"Bearer {api_key()}",
        "Content-Type": "application/json",
        "User-Agent": "gpts-evidence-data-center-agent-toolbelt/1",
    }
    attempts = 0
    while attempts < 2:
        attempts += 1
        try:
            response = requests.post(
                url,
                data=encoded,
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
            raise AgentToolbeltError(
                "AGENT_TOOLBELT_CONNECTION_FAILED",
                f"upstream connection failed: {type(exc).__name__}",
                retryable=True,
            ) from exc
        if len(raw) > max_bytes:
            raise AgentToolbeltError(
                "AGENT_TOOLBELT_RESPONSE_TOO_LARGE",
                "upstream response exceeded max_response_bytes",
            )
        if response.is_redirect:
            raise AgentToolbeltError(
                "AGENT_TOOLBELT_REDIRECT_REJECTED",
                f"upstream attempted HTTP {response.status_code} redirect",
            )
        if response.status_code == 429 or 500 <= response.status_code <= 599:
            if attempts < 2:
                time.sleep(1.0)
                continue
            raise AgentToolbeltError(
                "AGENT_TOOLBELT_HTTP_TRANSIENT",
                f"upstream HTTP {response.status_code}",
                retryable=True,
            )
        if response.status_code in {401, 403}:
            raise AgentToolbeltError(
                "AGENT_TOOLBELT_CREDENTIAL_OR_PLAN_DENIED",
                f"upstream HTTP {response.status_code}",
            )
        if response.status_code == 402:
            raise AgentToolbeltError(
                "AGENT_TOOLBELT_CREDIT_EXHAUSTED",
                "upstream HTTP 402: quota or prepaid credit exhausted",
            )
        if not 200 <= response.status_code < 300:
            message = f"upstream HTTP {response.status_code}"
            try:
                error_payload = json.loads(raw.decode("utf-8")) if raw else {}
                if isinstance(error_payload, Mapping):
                    detail = str(
                        error_payload.get("message")
                        or error_payload.get("error")
                        or ""
                    ).strip()
                    if detail:
                        message += f": {detail[:500]}"
            except (UnicodeDecodeError, json.JSONDecodeError):
                pass
            raise AgentToolbeltError("AGENT_TOOLBELT_HTTP_ERROR", message)
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else None
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AgentToolbeltError(
                "AGENT_TOOLBELT_INVALID_JSON",
                "upstream returned invalid JSON",
            ) from exc
        if isinstance(payload, Mapping) and payload.get("success") is False:
            detail = str(
                payload.get("message")
                or payload.get("error")
                or "request failed"
            )
            raise AgentToolbeltError(
                "AGENT_TOOLBELT_BUSINESS_ERROR",
                detail[:500],
            )
        metadata.update(
            {
                "http_status": response.status_code,
                "content_type": response.headers.get("Content-Type", ""),
                "response_bytes": len(raw),
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
        default=10_000_000,
        minimum=1024,
        maximum=20_000_000,
        name="max_response_bytes",
    )
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "API_AGENT_TOOLBELT_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "api_origin": "www.agenttoolbelt.live",
        "credential_mode": "bearer-api-key-backend-only",
        "secret_values_exposed": False,
        "one_request_per_ticket": True,
    }
    try:
        if operation == "catalog-capabilities":
            snapshot = {"provider": provider_row(CATALOG_PATH)}
            metadata["credential_mode"] = "none"
        else:
            payload, request_metadata = query_agent_toolbelt(
                operation,
                parameters,
                timeout=timeout,
                max_bytes=max_bytes,
            )
            metadata.update(request_metadata)
            metadata["upstream_called"] = True
            snapshot = {
                "provider": "agent-toolbelt",
                "operation": operation,
                "data": payload,
            }
        status = "API_AGENT_TOOLBELT_COMPLETED"
    except Exception as exc:
        message = str(exc)
        secret = str(os.getenv(API_KEY_ENV) or "")
        if secret:
            message = message.replace(secret, "[REDACTED]")
        failure = {
            "type": type(exc).__name__,
            "code": getattr(exc, "code", "AGENT_TOOLBELT_EXECUTION_ERROR"),
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
        schema_prefix="agent-toolbelt",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[api-agent-toolbelt]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="agent-toolbelt-ticket-status-v1",
            display_name="Agent Toolbelt",
        )
    )
