#!/usr/bin/env python3
"""Bounded synchronous client for Gapup MCP public intelligence tools."""
from __future__ import annotations

import ipaddress
import json
import os
import re
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
MCP_URL = "https://mcp.gapup.io/mcp"
MCP_HOST = "mcp.gapup.io"
API_KEY_ENV = "GAPUP_API_KEY"
MAX_REQUEST_BYTES = 1_000_000
EMAIL_RE = re.compile(r"(?i)(?<![A-Z0-9._%+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![A-Z0-9._%+-])")
SECRET_RE = re.compile(r"(?i)(?:bearer\s+[A-Za-z0-9._~+/=-]{8,}|\b(?:gpk|sk|api)[_-][A-Za-z0-9_-]{8,})")
FORBIDDEN_KEYS = {
    "async", "webhook", "webhook_url", "callback", "callback_url", "job_id",
    "payment", "x_payment", "x-payment", "wallet", "api_key", "apikey",
    "token", "secret", "authorization", "cookie", "headers", "proxy",
}


class GapupMcpError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def api_key() -> str:
    value = str(os.getenv(API_KEY_ENV) or "").strip()
    if not value:
        raise GapupMcpError("GAPUP_API_KEY_MISSING", f"missing repository Secret {API_KEY_ENV}")
    if not value.startswith("gpk_"):
        raise GapupMcpError("GAPUP_API_KEY_INVALID", f"invalid repository Secret {API_KEY_ENV} prefix")
    if not 8 <= len(value) <= 512:
        raise GapupMcpError("GAPUP_API_KEY_INVALID", f"invalid repository Secret {API_KEY_ENV} length")
    if any(ord(char) < 0x21 or ord(char) > 0x7E for char in value):
        raise GapupMcpError("GAPUP_API_KEY_INVALID", f"invalid repository Secret {API_KEY_ENV} characters")
    return value


def operation_row(operation: str) -> Mapping[str, Any]:
    row = operation_map(CATALOG_PATH).get(operation)
    if row is None:
        raise ValueError(f"unsupported Gapup MCP operation: {operation}")
    return row


def validate_public_https_url(value: str) -> None:
    parsed = urlsplit(value)
    if parsed.scheme.lower() != "https":
        raise ValueError("URL inputs must use https")
    if not parsed.hostname:
        raise ValueError("URL input requires a hostname")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URL input must not contain credentials")
    if parsed.port not in (None, 443):
        raise ValueError("URL input must use the default HTTPS port")
    host = parsed.hostname.rstrip(".").lower()
    if host in {"localhost", "localhost.localdomain"}:
        raise ValueError("localhost URL inputs are prohibited")
    if host.endswith((".localhost", ".local", ".internal", ".home", ".lan")):
        raise ValueError("private or local URL hostnames are prohibited")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and (
        address.is_private or address.is_loopback or address.is_link_local
        or address.is_multicast or address.is_reserved or address.is_unspecified
    ):
        raise ValueError("private, loopback, link-local, reserved, or multicast IP URLs are prohibited")


def validate_public_parameters(value: Any, *, depth: int = 0, key_name: str = "") -> None:
    if depth > 20:
        raise ValueError("request body nesting exceeds 20 levels")
    normalized = key_name.lower().replace("-", "_")
    if normalized in {item.replace("-", "_") for item in FORBIDDEN_KEYS}:
        raise ValueError(f"parameter {key_name!r} is prohibited")
    if value is None or isinstance(value, (bool, int, float)):
        return
    if isinstance(value, str):
        if EMAIL_RE.search(value):
            raise ValueError("email addresses and personal identifiers are prohibited")
        if SECRET_RE.search(value):
            raise ValueError("credential-like values are prohibited")
        if value.lower().startswith(("http://", "https://")):
            validate_public_https_url(value)
        return
    if isinstance(value, Mapping):
        if len(value) > 100:
            raise ValueError("request object has too many keys")
        for key, item in value.items():
            if not isinstance(key, str) or len(key) > 128:
                raise ValueError("request object keys must be short strings")
            validate_public_parameters(item, depth=depth + 1, key_name=key)
        return
    if isinstance(value, list):
        if len(value) > 100:
            raise ValueError("request array has too many items")
        for item in value:
            validate_public_parameters(item, depth=depth + 1, key_name=key_name)
        return
    raise ValueError(f"unsupported request value type: {type(value).__name__}")


def parse_mcp_payload(raw: bytes, content_type: str) -> Any:
    if not raw:
        raise GapupMcpError("GAPUP_MCP_EMPTY_RESPONSE", "upstream returned an empty response")
    try:
        text = raw.decode("utf-8")
        if "text/event-stream" not in content_type.lower() and not text.lstrip().startswith(("event:", "data:")):
            return json.loads(text)
        events, data_lines = [], []
        for line in text.splitlines() + [""]:
            if line.startswith("data:"):
                data_lines.append(line[5:].lstrip())
            elif not line.strip() and data_lines:
                data = "\n".join(data_lines)
                data_lines = []
                if data and data != "[DONE]":
                    events.append(json.loads(data))
        if not events:
            raise ValueError("empty SSE response")
        return events[-1]
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise GapupMcpError("GAPUP_MCP_INVALID_RESPONSE", "upstream returned invalid MCP content") from exc


def scrub_secret(value: Any, secret: str) -> Any:
    if isinstance(value, str):
        return value.replace(secret, "[REDACTED]") if secret else value
    if isinstance(value, list):
        return [scrub_secret(item, secret) for item in value]
    if isinstance(value, Mapping):
        return {str(key): scrub_secret(item, secret) for key, item in value.items()}
    return value


def query_gapup(operation: str, parameters: Mapping[str, Any], *, timeout: int, max_bytes: int) -> tuple[Any, dict[str, Any]]:
    row = operation_row(operation)
    execution = dict(row.get("execution") or {})
    if execution.get("local") is True:
        raise ValueError("local operations must not call query_gapup")
    if execution.get("mcp_method") != "tools/call" or execution.get("mcp_tool_name") != operation:
        raise ValueError("provider catalog MCP route does not match operation")
    validate_public_parameters(parameters)
    arguments = dict(parameters)
    if execution.get("force_async_false") is True:
        arguments["async"] = False
    request_payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": 1,
        "params": {"name": operation, "arguments": arguments},
    }
    encoded = json.dumps(request_payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_REQUEST_BYTES:
        raise ValueError(f"request body exceeds {MAX_REQUEST_BYTES} bytes")
    secret = api_key()
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "x-api-key": secret,
        "User-Agent": "evidence-intelligence-center-gapup-mcp/1",
    }
    attempts = 0
    while attempts < 2:
        attempts += 1
        try:
            response = requests.post(
                MCP_URL,
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
            raise GapupMcpError("GAPUP_MCP_CONNECTION_FAILED", type(exc).__name__, retryable=True) from exc
        if len(raw) > max_bytes:
            raise GapupMcpError("GAPUP_MCP_RESPONSE_TOO_LARGE", "upstream response exceeded max_response_bytes")
        if response.is_redirect:
            raise GapupMcpError("GAPUP_MCP_REDIRECT_REJECTED", f"upstream attempted HTTP {response.status_code} redirect")
        if response.status_code in {401, 403}:
            raise GapupMcpError("GAPUP_MCP_CREDENTIAL_DENIED", f"upstream HTTP {response.status_code}")
        if response.status_code == 402:
            raise GapupMcpError(
                "GAPUP_MCP_PAYMENT_REQUIRED",
                "upstream requested x402 payment; automatic payment is prohibited",
            )
        if response.status_code == 429:
            raise GapupMcpError("GAPUP_MCP_RATE_LIMITED", "upstream HTTP 429", retryable=True)
        if response.status_code >= 500:
            if attempts < 2:
                time.sleep(1.0)
                continue
            raise GapupMcpError("GAPUP_MCP_HTTP_TRANSIENT", f"upstream HTTP {response.status_code}", retryable=True)
        if not 200 <= response.status_code < 300:
            raise GapupMcpError("GAPUP_MCP_HTTP_ERROR", f"upstream HTTP {response.status_code}")
        content_type = str(response.headers.get("Content-Type") or "")
        parsed = parse_mcp_payload(raw, content_type)
        if isinstance(parsed, Mapping) and parsed.get("error"):
            detail = json.dumps(parsed["error"], ensure_ascii=False)[:2000]
            raise GapupMcpError("GAPUP_MCP_JSONRPC_ERROR", f"upstream JSON-RPC error: {detail}")
        result = parsed.get("result") if isinstance(parsed, Mapping) else None
        if not isinstance(result, Mapping):
            raise GapupMcpError("GAPUP_MCP_RESULT_INVALID", "upstream response did not contain result")
        if result.get("isError") is True:
            raise GapupMcpError("GAPUP_MCP_TOOL_ERROR", "upstream tool returned isError=true")
        content = result.get("content")
        if not isinstance(content, list) or not content:
            raise GapupMcpError("GAPUP_MCP_CONTENT_MISSING", "upstream result did not contain content")
        deliverables = []
        for item in content:
            if not isinstance(item, Mapping):
                continue
            if item.get("type") == "text" and isinstance(item.get("text"), str):
                text = item["text"]
                try:
                    deliverables.append(json.loads(text))
                except json.JSONDecodeError:
                    deliverables.append(text)
            else:
                deliverables.append(dict(item))
        if not deliverables:
            raise GapupMcpError("GAPUP_MCP_CONTENT_INVALID", "upstream content was not usable")
        return scrub_secret(deliverables[0] if len(deliverables) == 1 else deliverables, secret), {
            "request_origin": MCP_HOST,
            "request_path": "/mcp",
            "http_method": "POST",
            "mcp_method": "tools/call",
            "mcp_tool_name": operation,
            "credential_mode": "x-api-key-backend-only",
            "credential_environment_variable": API_KEY_ENV,
            "secret_value_exposed": False,
            "redirects_allowed": False,
            "automatic_x402_payment_allowed": False,
            "async_forced_false": bool(execution.get("force_async_false")),
            "request_bytes": len(encoded),
            "response_bytes": len(raw),
            "http_status": response.status_code,
            "content_type": content_type,
            "attempts": attempts,
            "billable_or_quota_counted": True,
        }
    raise AssertionError("unreachable")


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(acceptance.get("timeout_seconds"), default=60, minimum=5, maximum=120, name="timeout_seconds")
    max_bytes = bounded_int(acceptance.get("max_response_bytes"), default=10_000_000, minimum=1024, maximum=20_000_000, name="max_response_bytes")
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_GAPUP_MCP_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "api_origin": MCP_HOST,
        "credential_mode": "x-api-key-backend-only",
        "secret_values_exposed": False,
        "one_request_per_ticket": True,
        "automatic_x402_payment_allowed": False,
        "async_jobs_allowed": False,
    }
    try:
        if operation == "catalog-capabilities":
            snapshot = {"provider": provider_row(CATALOG_PATH)}
            metadata["credential_mode"] = "none"
        else:
            payload, request_metadata = query_gapup(operation, parameters, timeout=timeout, max_bytes=max_bytes)
            metadata.update(request_metadata)
            metadata["upstream_called"] = True
            snapshot = {"provider": "gapup-mcp", "operation": operation, "data": payload}
        status = "INTEL_GAPUP_MCP_COMPLETED"
    except Exception as exc:
        message = str(exc)
        secret = str(os.getenv(API_KEY_ENV) or "")
        if secret:
            message = message.replace(secret, "[REDACTED]")
        failure = {
            "type": type(exc).__name__,
            "code": getattr(exc, "code", "GAPUP_MCP_EXECUTION_ERROR"),
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
        schema_prefix="gapup-mcp",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-gapup]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="gapup-mcp-ticket-status-v1",
            display_name="Gapup MCP 情报",
        )
    )
