#!/usr/bin/env python3
"""Bounded Wolfram|Alpha and LlamaParse managed-provider control plane."""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from jsonschema import Draft202012Validator, FormatChecker

HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE / "ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"
WOLFRAM_ENV = "WOLFRAMALPHA_APP_ID"
LLAMA_ENV = "LLAMA_CLOUD_API_KEY"
LLAMA_BASE = "https://api.cloud.llamaindex.ai/api/v2/parse"

WOLFRAM_ENDPOINTS = {
    "llm-query": "https://www.wolframalpha.com/api/v1/llm-api",
    "full-results-json": "https://api.wolframalpha.com/v2/query",
    "short-answer": "https://api.wolframalpha.com/v1/result",
    "query-recognizer": "https://www.wolframalpha.com/queryrecognizer/query.jsp",
}


class ProviderError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def canonical_sha(value: Any) -> str:
    raw = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def write_output(name: str, value: Any) -> None:
    target = os.getenv("GITHUB_OUTPUT")
    if not target:
        return
    text = str(value).replace("\n", " ").replace("\r", " ")
    with open(target, "a", encoding="utf-8") as handle:
        handle.write(f"{name}={text}\n")


def provider_catalog(provider: str) -> Mapping[str, Any]:
    for row in load_json(CATALOG_PATH)["providers"]:
        if row["provider_id"] == provider:
            return row
    raise ValueError(f"unsupported provider: {provider}")


def operation_catalog(provider: str, operation: str) -> Mapping[str, Any]:
    for row in provider_catalog(provider)["operations"]:
        if row["operation_id"] == operation:
            return row
    raise ValueError(f"unsupported operation: {provider}/{operation}")


def validate_ticket(ticket: Mapping[str, Any]) -> None:
    validator = Draft202012Validator(load_json(SCHEMA_PATH), format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(ticket), key=lambda item: list(item.absolute_path))
    if errors:
        raise ValueError("; ".join(
            f"{'.'.join(str(x) for x in item.absolute_path) or '$'}: {item.message}"
            for item in errors[:20]
        ))
    provider = str(ticket["provider"])
    operation = str(ticket["operation"])
    schema = operation_catalog(provider, operation)["parameter_schema"]
    parameter_errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(
            ticket.get("parameters") or {}
        ),
        key=lambda item: list(item.absolute_path),
    )
    if parameter_errors:
        raise ValueError("; ".join(
            f"parameters.{'.'.join(str(x) for x in item.absolute_path)}: {item.message}"
            for item in parameter_errors[:20]
        ))


def prepare(event_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    event = load_json(event_path)
    issue = event.get("issue") if isinstance(event.get("issue"), Mapping) else {}
    title = str(issue.get("title") or "")
    body = str(issue.get("body") or "")
    accepted = False
    reason = ""
    ticket: Mapping[str, Any] | None = None
    try:
        parsed = json.loads(body)
        if not isinstance(parsed, Mapping):
            raise ValueError("ticket body must be a JSON object")
        validate_ticket(parsed)
        provider = str(parsed["provider"])
        expected_prefix = str(provider_catalog(provider)["ticket_prefix"])
        if not title.startswith(expected_prefix):
            raise ValueError(f"issue title must start with {expected_prefix}")
        ticket = parsed
        accepted = True
        write_json(output_dir / "ticket.json", ticket)
    except (json.JSONDecodeError, ValueError) as exc:
        reason = str(exc)
    status = {
        "schema_version": "knowledge-document-ticket-status-v1",
        "accepted": accepted,
        "reason": reason,
        "task_id": str((ticket or {}).get("task_id") or ""),
        "provider": str((ticket or {}).get("provider") or ""),
        "operation": str((ticket or {}).get("operation") or ""),
        "ticket_sha256": canonical_sha(ticket) if ticket else None,
        "secret_values_exposed": False,
        "model_calls": 0,
    }
    write_json(output_dir / "ticket-status.json", status)
    write_output("accepted", "true" if accepted else "false")
    write_output("provider", status["provider"])
    write_output("reason", reason)
    return 0 if accepted else 1


def secret(name: str) -> str:
    value = str(os.getenv(name) or "").strip()
    if not value:
        raise ProviderError("PROVIDER_SECRET_MISSING", f"missing repository Secret {name}")
    return value


def scrub(value: str, secrets: list[str]) -> str:
    for item in secrets:
        if item:
            value = value.replace(item, "[REDACTED]")
    return value


def _read_once(
    request: urllib.request.Request,
    *,
    timeout: int,
    max_bytes: int,
    opener: Callable[..., Any],
) -> tuple[int, bytes, str]:
    try:
        with opener(request, timeout=timeout) as response:
            status = int(getattr(response, "status", 200))
            raw = response.read(max_bytes + 1)
            content_type = str(response.headers.get("Content-Type") or "")
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        raw = exc.read(max_bytes + 1)
        content_type = str(exc.headers.get("Content-Type") or "") if exc.headers else ""
    if len(raw) > max_bytes:
        raise ProviderError("PROVIDER_RESPONSE_TOO_LARGE", "upstream response exceeded max_response_bytes")
    return status, raw, content_type


def request_with_retry(
    request: urllib.request.Request,
    *,
    timeout: int,
    max_bytes: int,
    secrets: list[str],
    opener: Callable[..., Any] = urllib.request.urlopen,
    sleeper: Callable[[float], None] = time.sleep,
) -> tuple[int, bytes, str, int]:
    for attempt in (1, 2):
        try:
            status, raw, content_type = _read_once(
                request, timeout=timeout, max_bytes=max_bytes, opener=opener
            )
        except urllib.error.URLError as exc:
            if attempt == 1:
                sleeper(1.0)
                continue
            reason = type(getattr(exc, "reason", exc)).__name__
            raise ProviderError(
                "PROVIDER_CONNECTION_FAILED",
                f"upstream connection failed: {reason}",
                retryable=True,
            ) from exc
        if status == 429 or 500 <= status <= 599:
            if attempt == 1:
                sleeper(1.0)
                continue
            raise ProviderError(
                "PROVIDER_HTTP_TRANSIENT", f"upstream HTTP {status}", retryable=True
            )
        if not 200 <= status < 300:
            detail = scrub(raw[:1200].decode("utf-8", errors="replace"), secrets)
            code = "PROVIDER_AUTH_FAILED" if status in {401, 403} else "PROVIDER_HTTP_ERROR"
            raise ProviderError(code, f"upstream HTTP {status}: {detail}")
        return status, raw, content_type, attempt
    raise ProviderError("PROVIDER_CONNECTION_FAILED", "upstream request exhausted retries", retryable=True)


def validate_public_https_url(value: str) -> str:
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise ProviderError("LLAMAPARSE_SOURCE_URL_REJECTED", "source_url must be absolute HTTPS")
    if parsed.username or parsed.password:
        raise ProviderError("LLAMAPARSE_SOURCE_URL_REJECTED", "source_url userinfo is forbidden")
    if parsed.port not in {None, 443}:
        raise ProviderError("LLAMAPARSE_SOURCE_URL_REJECTED", "source_url must use port 443")
    host = parsed.hostname.rstrip(".").lower()
    if host in {"localhost"} or host.endswith(".localhost"):
        raise ProviderError("LLAMAPARSE_SOURCE_URL_REJECTED", "loopback source host is forbidden")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)}
    except socket.gaierror as exc:
        raise ProviderError("LLAMAPARSE_SOURCE_DNS_FAILED", "source_url hostname did not resolve") from exc
    if not addresses:
        raise ProviderError("LLAMAPARSE_SOURCE_DNS_FAILED", "source_url hostname has no addresses")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise ProviderError("LLAMAPARSE_SOURCE_URL_REJECTED", "source_url resolves to a non-public address")
    return urllib.parse.urlunsplit(parsed)


def query_wolfram(
    operation: str,
    parameters: Mapping[str, Any],
    *,
    timeout: int,
    max_bytes: int,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> tuple[Any, dict[str, Any]]:
    appid = secret(WOLFRAM_ENV)
    endpoint = WOLFRAM_ENDPOINTS[operation]
    params = dict(parameters)
    headers = {
        "Accept": "application/json, text/plain;q=0.9",
        "User-Agent": "gpts-evidence-data-center-wolframalpha/1",
    }
    if operation == "llm-query":
        params["input"] = params.pop("input")
        headers["Authorization"] = f"Bearer {appid}"
    elif operation == "full-results-json":
        params["output"] = "json"
        params["appid"] = appid
    elif operation == "short-answer":
        params["i"] = params.pop("input")
        params["appid"] = appid
    elif operation == "query-recognizer":
        params["i"] = params.pop("input")
        params["mode"] = params.get("mode") or "Default"
        params["output"] = "json"
        params["appid"] = appid
    query = urllib.parse.urlencode(params, doseq=isinstance(params.get("assumption"), list))
    request = urllib.request.Request(f"{endpoint}?{query}", headers=headers, method="GET")
    status, raw, content_type, attempts = request_with_retry(
        request, timeout=timeout, max_bytes=max_bytes, secrets=[appid], opener=opener
    )
    if operation in {"full-results-json", "query-recognizer"}:
        try:
            result: Any = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProviderError("WOLFRAM_INVALID_JSON", "WolframAlpha returned invalid JSON") from exc
    else:
        result = {"text": raw.decode("utf-8", errors="replace")}
    parsed = urllib.parse.urlsplit(endpoint)
    return result, {
        "http_status": status,
        "content_type": content_type,
        "request_origin": parsed.netloc,
        "request_path": parsed.path,
        "http_method": "GET",
        "credential_mode": "authorization-bearer" if operation == "llm-query" else "query-appid",
        "credential_environment_variable": WOLFRAM_ENV,
        "secret_value_exposed": False,
        "upstream_called": True,
        "transport_attempts": attempts,
    }


def query_llamaparse(
    operation: str,
    parameters: Mapping[str, Any],
    *,
    timeout: int,
    max_bytes: int,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> tuple[Any, dict[str, Any]]:
    api_key = secret(LLAMA_ENV)
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "gpts-evidence-data-center-llamaparse/1",
    }
    method = "GET"
    body: bytes | None = None
    endpoint = LLAMA_BASE
    if operation == "create-parse-job":
        payload = dict(parameters)
        if payload.get("source_url"):
            payload["source_url"] = validate_public_https_url(str(payload["source_url"]))
        payload.setdefault("tier", "agentic")
        payload.setdefault("version", "latest")
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
        method = "POST"
    elif operation == "list-parse-jobs":
        query = urllib.parse.urlencode(parameters)
        endpoint = f"{LLAMA_BASE}?{query}" if query else LLAMA_BASE
    elif operation == "get-parse-result":
        job_id = urllib.parse.quote(str(parameters["job_id"]), safe="")
        query_params: dict[str, str] = {}
        expand = parameters.get("expand") or []
        if expand:
            query_params["expand"] = ",".join(str(item) for item in expand)
        image_filenames = parameters.get("image_filenames") or []
        if image_filenames:
            query_params["image_filenames"] = ",".join(str(item) for item in image_filenames)
        query = urllib.parse.urlencode(query_params)
        endpoint = f"{LLAMA_BASE}/{job_id}" + (f"?{query}" if query else "")
    request = urllib.request.Request(endpoint, data=body, headers=headers, method=method)
    status, raw, content_type, attempts = request_with_retry(
        request, timeout=timeout, max_bytes=max_bytes, secrets=[api_key], opener=opener
    )
    try:
        result = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderError("LLAMAPARSE_INVALID_JSON", "LlamaParse returned invalid JSON") from exc
    if not isinstance(result, Mapping):
        raise ProviderError("LLAMAPARSE_INVALID_RESPONSE", "LlamaParse JSON root must be an object")
    parsed = urllib.parse.urlsplit(endpoint)
    return dict(result), {
        "http_status": status,
        "content_type": content_type,
        "request_origin": parsed.netloc,
        "request_path": parsed.path,
        "http_method": method,
        "credential_mode": "authorization-bearer",
        "credential_environment_variable": LLAMA_ENV,
        "secret_value_exposed": False,
        "upstream_called": True,
        "transport_attempts": attempts,
    }


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket)
    provider = str(ticket["provider"])
    operation = str(ticket["operation"])
    started_at = utc_now()
    try:
        if operation == "catalog-capabilities":
            result = {"provider": provider, "catalog": provider_catalog(provider)}
            metadata = {
                "upstream_called": False,
                "credential_mode": "none",
                "secret_value_exposed": False,
                "operation_count": len(provider_catalog(provider)["operations"]),
            }
        else:
            acceptance = ticket["acceptance"]
            kwargs = {
                "timeout": int(acceptance["timeout_seconds"]),
                "max_bytes": int(acceptance["max_response_bytes"]),
            }
            if provider == "wolframalpha":
                result, metadata = query_wolfram(operation, ticket.get("parameters") or {}, **kwargs)
            else:
                result, metadata = query_llamaparse(operation, ticket.get("parameters") or {}, **kwargs)
        snapshot = {
            "schema_version": "knowledge-document-api-snapshot-v1",
            "status": f"API_{provider.upper()}_COMPLETED",
            "task_id": ticket["task_id"],
            "provider": provider,
            "operation": operation,
            "started_at": started_at,
            "completed_at": utc_now(),
            "ticket_sha256": canonical_sha(ticket),
            "metadata": metadata,
            "result": result,
            "secret_values_exposed": False,
            "model_calls": 0,
        }
        snapshot["snapshot_sha256"] = canonical_sha(snapshot)
        write_json(output_dir / f"{provider}-snapshot.json", snapshot)
        write_output("status", snapshot["status"])
        write_output("snapshot_sha256", snapshot["snapshot_sha256"])
        return 0
    except ProviderError as exc:
        failure = {
            "schema_version": "knowledge-document-diagnostics-v1",
            "status": f"API_{provider.upper()}_FAILED",
            "task_id": ticket.get("task_id"),
            "provider": provider,
            "operation": operation,
            "started_at": started_at,
            "failed_at": utc_now(),
            "error": {
                "code": exc.code,
                "message": str(exc)[:4000],
                "retryable": exc.retryable,
            },
            "secret_values_exposed": False,
            "model_calls": 0,
        }
        failure["diagnostics_sha256"] = canonical_sha(failure)
        write_json(output_dir / f"{provider}-diagnostics.json", failure)
        write_output("status", failure["status"])
        write_output("error_code", exc.code)
        return 1


def render(output_dir: Path, phase: str, artifact_url: str = "") -> int:
    if phase in {"accepted", "rejected"}:
        status = load_json(output_dir / "ticket-status.json")
        provider = str(status.get("provider") or "provider").upper()
        heading = f"API_{provider}_ACCEPTED" if status["accepted"] else f"API_{provider}_REJECTED"
        print(f"## {heading}\n")
        print(f"- Task ID: `{status.get('task_id') or 'unknown'}`")
        print(f"- Operation: `{status.get('operation') or 'unknown'}`")
        print(f"- Ticket SHA-256: `{status.get('ticket_sha256') or 'unavailable'}`")
        if not status["accepted"]:
            print(f"- Reason: `{status.get('reason') or 'invalid ticket'}`")
        print("- Secret values exposed: `false`")
        print("- Model calls: `0`")
        return 0
    candidates = list(output_dir.glob("*-snapshot.json"))
    if candidates:
        snapshot = load_json(candidates[0])
        metadata = snapshot.get("metadata") or {}
        print(f"## {snapshot['status']}\n")
        print(f"- Task ID: `{snapshot['task_id']}`")
        print(f"- Provider: `{snapshot['provider']}`")
        print(f"- Operation: `{snapshot['operation']}`")
        print(f"- Upstream called: `{str(bool(metadata.get('upstream_called'))).lower()}`")
        print(f"- Transport attempts: `{metadata.get('transport_attempts', 0)}`")
        print(f"- Snapshot SHA-256: `{snapshot['snapshot_sha256']}`")
        print(f"- Artifact: {artifact_url or 'unavailable'}")
        print("- Secret values exposed: `false`")
        print("- Model calls: `0`")
        return 0
    failures = list(output_dir.glob("*-diagnostics.json"))
    failure = load_json(failures[0]) if failures else {
        "status": "API_PROVIDER_FAILED",
        "error": {},
    }
    print(f"## {failure['status']}\n")
    print(f"- Error code: `{failure.get('error', {}).get('code') or 'UNKNOWN'}`")
    print(f"- Message: `{failure.get('error', {}).get('message') or 'execution failed'}`")
    print(f"- Artifact: {artifact_url or 'unavailable'}")
    print("- Secret values exposed: `false`")
    print("- Model calls: `0`")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--event-path", required=True)
    prepare_parser.add_argument("--output-dir", required=True)
    execute_parser = sub.add_parser("execute")
    execute_parser.add_argument("--ticket", required=True)
    execute_parser.add_argument("--output-dir", required=True)
    render_parser = sub.add_parser("render")
    render_parser.add_argument("--output-dir", required=True)
    render_parser.add_argument("--phase", required=True, choices=["accepted", "rejected", "completed"])
    render_parser.add_argument("--artifact-url", default="")
    args = parser.parse_args()
    if args.command == "prepare":
        return prepare(Path(args.event_path), Path(args.output_dir))
    if args.command == "execute":
        return execute(Path(args.ticket), Path(args.output_dir))
    return render(Path(args.output_dir), args.phase, args.artifact_url)


if __name__ == "__main__":
    raise SystemExit(main())
