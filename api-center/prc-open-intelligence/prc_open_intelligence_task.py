#!/usr/bin/env python3
"""Bounded, no-key PRC open-intelligence providers.

Production operations are deliberately limited to:
- China-Check's published no-auth MCP company lookup tools.
- SinoFacts' CC BY 4.0 GitHub snapshot.

No provider may rotate IPs/headers/accounts after denial. Paid upgrades are stripped.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE / "ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"
CHINA_CHECK_ENDPOINT = "https://www.china-check.com/api/mcp/mcp"
SINOFacts_INDEX_URL = "https://raw.githubusercontent.com/SinoFacts/dataset/main/index.json"
SINOFacts_RECORDS_URL = "https://raw.githubusercontent.com/SinoFacts/dataset/main/companies.jsonl"
SINOFacts_UPSTREAM_MAX_BYTES = 5_000_000
MCP_PROTOCOL_VERSION = "2025-06-18"

HARD_STOP_HTTP = {
    401: "AUTHORIZATION_DENIED",
    403: "AUTHORIZATION_DENIED",
    429: "RATE_LIMITED",
}
BLOCK_MARKERS = (
    "captcha",
    "验证码",
    "access denied",
    "request blocked",
    "访问被阻断",
    "当前所在地区暂不支持访问",
    "environment checking",
)
PERSONAL_OR_CONTACT_KEY_RE = re.compile(
    r"(?:phone|mobile|tel|email|mail|contact|idcard|identity|passport|"
    r"legalperson|legal_person|legalrepresentative|legal_representative|"
    r"personname|person_name|founders?_public|staffsize|staff_size)",
    re.IGNORECASE,
)
PAID_FIELD_RE = re.compile(
    r"(?:purchase|checkout|price|payment|paid|report_options?|order_url|upgrade)",
    re.IGNORECASE,
)


class ProviderStop(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def canonical_sha(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def write_output(name: str, value: Any) -> None:
    target = os.getenv("GITHUB_OUTPUT")
    if not target:
        return
    text = str(value).replace("\n", " ").replace("\r", " ")
    with open(target, "a", encoding="utf-8") as handle:
        handle.write(f"{name}={text}\n")


def _provider_rows() -> dict[str, Mapping[str, Any]]:
    catalog = load_json(CATALOG_PATH)
    return {str(row["provider_id"]): row for row in catalog["providers"]}


def _operation_rows() -> dict[tuple[str, str], Mapping[str, Any]]:
    result: dict[tuple[str, str], Mapping[str, Any]] = {}
    for provider_id, provider in _provider_rows().items():
        for operation in provider["operations"]:
            result[(provider_id, str(operation["operation_id"]))] = operation
    return result


def validate_ticket(ticket: Mapping[str, Any]) -> None:
    errors = sorted(
        Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(ticket),
        key=lambda item: list(item.absolute_path),
    )
    if errors:
        rendered = "; ".join(
            f"{'.'.join(str(x) for x in item.absolute_path) or '$'}: {item.message}"
            for item in errors[:20]
        )
        raise ValueError(rendered)
    provider = str(ticket["provider"])
    operation = str(ticket["operation"])
    contract = _operation_rows().get((provider, operation))
    if contract is None:
        raise ValueError(f"unsupported provider operation: {provider}/{operation}")
    schema = contract.get("parameter_schema")
    if isinstance(schema, Mapping):
        parameter_errors = sorted(
            Draft202012Validator(dict(schema)).iter_errors(ticket.get("parameters") or {}),
            key=lambda item: list(item.absolute_path),
        )
        if parameter_errors:
            rendered = "; ".join(
                f"parameters.{'.'.join(str(x) for x in item.absolute_path)}: {item.message}"
                for item in parameter_errors[:20]
            )
            raise ValueError(rendered)


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
        if not title.startswith("[api-prc-open]"):
            raise ValueError("issue title must start with [api-prc-open]")
        parsed = json.loads(body)
        if not isinstance(parsed, Mapping):
            raise ValueError("ticket body must be a JSON object")
        validate_ticket(parsed)
        ticket = parsed
        accepted = True
        write_json(output_dir / "ticket.json", ticket)
    except (json.JSONDecodeError, ValueError) as exc:
        reason = str(exc)
    status = {
        "schema_version": "prc-open-intelligence-ticket-status-v1",
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
    write_output("reason", reason)
    return 0 if accepted else 1


def _bounded_int(value: Any, *, default: int, minimum: int, maximum: int, name: str) -> int:
    if value in (None, ""):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if not minimum <= parsed <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return parsed


def _require_text(value: Any, name: str, maximum: int = 100) -> str:
    text = str(value or "").strip()
    if not text or len(text) > maximum:
        raise ValueError(f"{name} must contain 1 to {maximum} characters")
    return text


def _detect_block_page(raw: bytes) -> None:
    sample = raw[:100_000].decode("utf-8", errors="ignore").casefold()
    for marker in BLOCK_MARKERS:
        if marker.casefold() in sample:
            raise ProviderStop(
                "TECHNICAL_MEASURE_ENCOUNTERED",
                f"upstream returned access-control marker: {marker}",
            )


def _http_bytes(
    url: str,
    *,
    method: str = "GET",
    headers: Mapping[str, str] | None = None,
    body: bytes | None = None,
    timeout: int,
    max_bytes: int,
) -> tuple[bytes, dict[str, Any]]:
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Accept": "application/json, text/event-stream, text/plain;q=0.9, */*;q=0.1",
            "User-Agent": "evidence-data-center-prc-open-intelligence/1",
            **dict(headers or {}),
        },
        method=method,
    )
    response_headers: Mapping[str, str] | None = None
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = int(response.status)
            raw = response.read(max_bytes + 1)
            response_headers = response.headers
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        raw = exc.read(max_bytes + 1)
        response_headers = exc.headers
    except urllib.error.URLError as exc:
        raise ProviderStop("UPSTREAM_NETWORK_ERROR", str(exc.reason), retryable=True) from exc
    if len(raw) > max_bytes:
        raise ProviderStop("BOUNDED_LIMIT_EXCEEDED", f"response exceeds {max_bytes} bytes")
    if status in HARD_STOP_HTTP:
        raise ProviderStop(HARD_STOP_HTTP[status], f"upstream HTTP {status}")
    if not 200 <= status < 300:
        raise ProviderStop("UPSTREAM_HTTP_ERROR", f"upstream HTTP {status}", retryable=False)
    _detect_block_page(raw)
    metadata = {
        "http_status": status,
        "content_type": str(response_headers.get("Content-Type") or "") if response_headers else "",
        "request_origin": urllib.parse.urlsplit(url).netloc,
        "request_path": urllib.parse.urlsplit(url).path,
        "mcp_session_id": str(response_headers.get("Mcp-Session-Id") or "") if response_headers else "",
    }
    return raw, metadata


def _parse_json_or_sse(raw: bytes) -> Mapping[str, Any]:
    text = raw.decode("utf-8", errors="strict").strip()
    candidates: list[str] = []
    if text.startswith("{"):
        candidates.append(text)
    for line in text.splitlines():
        if line.startswith("data:"):
            payload = line[5:].strip()
            if payload and payload != "[DONE]":
                candidates.append(payload)
    for candidate in reversed(candidates):
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, Mapping):
            return parsed
    raise ProviderStop("UPSTREAM_PROTOCOL_ERROR", "upstream returned neither JSON nor MCP SSE JSON")


def _mcp_post(payload: Mapping[str, Any], *, session_id: str, timeout: int, max_bytes: int) -> tuple[Mapping[str, Any] | None, dict[str, Any]]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
        headers["MCP-Protocol-Version"] = MCP_PROTOCOL_VERSION
    raw, metadata = _http_bytes(
        CHINA_CHECK_ENDPOINT,
        method="POST",
        headers=headers,
        body=json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
        timeout=timeout,
        max_bytes=max_bytes,
    )
    if "id" not in payload:
        return None, metadata
    return _parse_json_or_sse(raw), metadata


def _mcp_initialize(*, timeout: int, max_bytes: int) -> tuple[str, set[str], list[dict[str, Any]]]:
    request_log: list[dict[str, Any]] = []
    init, meta = _mcp_post(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "evidence-data-center", "version": "1.0.0"},
            },
        },
        session_id="",
        timeout=timeout,
        max_bytes=max_bytes,
    )
    request_log.append(meta)
    if not isinstance(init, Mapping) or init.get("error"):
        raise ProviderStop("UPSTREAM_PROTOCOL_ERROR", "China-Check MCP initialize failed")
    session_id = str(meta.get("mcp_session_id") or "")
    _, notify_meta = _mcp_post(
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        session_id=session_id,
        timeout=timeout,
        max_bytes=max_bytes,
    )
    request_log.append(notify_meta)
    listing, list_meta = _mcp_post(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        session_id=session_id,
        timeout=timeout,
        max_bytes=max_bytes,
    )
    request_log.append(list_meta)
    tools = ((listing or {}).get("result") or {}).get("tools") if isinstance(listing, Mapping) else None
    names = {
        str(item.get("name"))
        for item in tools or []
        if isinstance(item, Mapping) and item.get("name")
    }
    required = {"search_chinese_company", "get_company_snapshot"}
    if not required.issubset(names):
        raise ProviderStop(
            "UPSTREAM_CONTRACT_DRIFT",
            f"China-Check expected MCP tools missing: {sorted(required - names)}",
        )
    return session_id, names, request_log


def sanitize_company_payload(value: Any) -> Any:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for raw_key, item in value.items():
            key = str(raw_key)
            if PERSONAL_OR_CONTACT_KEY_RE.search(key) or PAID_FIELD_RE.search(key):
                continue
            result[key] = sanitize_company_payload(item)
        return result
    if isinstance(value, list):
        return [sanitize_company_payload(item) for item in value]
    return value


def _extract_mcp_tool_result(message: Mapping[str, Any]) -> Any:
    if message.get("error"):
        raise ProviderStop("UPSTREAM_TOOL_ERROR", json.dumps(message["error"], ensure_ascii=False))
    result = message.get("result")
    if not isinstance(result, Mapping):
        raise ProviderStop("UPSTREAM_PROTOCOL_ERROR", "MCP result object missing")
    content = result.get("content")
    if not isinstance(content, list) or not content:
        raise ProviderStop("UPSTREAM_PROTOCOL_ERROR", "MCP result content missing")
    first = content[0]
    if not isinstance(first, Mapping):
        raise ProviderStop("UPSTREAM_PROTOCOL_ERROR", "MCP content item invalid")
    text = first.get("text")
    if isinstance(text, str):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"text": text}
    return first


def _china_check(operation: str, parameters: Mapping[str, Any], timeout: int, max_bytes: int) -> tuple[Any, dict[str, Any]]:
    session_id, tools, request_log = _mcp_initialize(timeout=timeout, max_bytes=max_bytes)
    language = str(parameters.get("language") or "zh").strip()
    if operation == "company-search":
        tool_name = "search_chinese_company"
        arguments: dict[str, Any] = {
            "query": _require_text(parameters.get("query"), "query"),
            "language": language,
        }
    elif operation == "company-snapshot":
        tool_name = "get_company_snapshot"
        arguments = {"language": language}
        if parameters.get("company_id") not in (None, ""):
            arguments["companyId"] = _require_text(parameters.get("company_id"), "company_id", 128)
        else:
            arguments["query"] = _require_text(parameters.get("query"), "query")
    else:
        raise ValueError(f"unsupported China-Check operation: {operation}")
    if tool_name not in tools:
        raise ProviderStop("UPSTREAM_CONTRACT_DRIFT", f"MCP tool disappeared: {tool_name}")
    message, meta = _mcp_post(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        },
        session_id=session_id,
        timeout=timeout,
        max_bytes=max_bytes,
    )
    request_log.append(meta)
    if not isinstance(message, Mapping):
        raise ProviderStop("UPSTREAM_PROTOCOL_ERROR", "MCP tools/call returned no response")
    data = sanitize_company_payload(_extract_mcp_tool_result(message))
    return data, {
        "source": "China-Check no-auth MCP",
        "endpoint": CHINA_CHECK_ENDPOINT,
        "mcp_tool": tool_name,
        "request_count": len(request_log),
        "requests": [
            {key: row.get(key) for key in ("http_status", "request_origin", "request_path")}
            for row in request_log
        ],
        "auth": "none",
        "paid_upgrade_used": False,
    }


def _fetch_json(url: str, *, timeout: int, max_bytes: int) -> tuple[Any, dict[str, Any]]:
    raw, metadata = _http_bytes(url, timeout=timeout, max_bytes=max_bytes)
    try:
        return json.loads(raw.decode("utf-8")), metadata
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderStop("UPSTREAM_PROTOCOL_ERROR", "upstream JSON decode failed") from exc


def _sinofacts_search(parameters: Mapping[str, Any], timeout: int, max_bytes: int) -> tuple[Any, dict[str, Any]]:
    query = _require_text(parameters.get("query"), "query").casefold()
    max_results = _bounded_int(
        parameters.get("max_results"), default=10, minimum=1, maximum=20, name="max_results"
    )
    payload, metadata = _fetch_json(SINOFacts_INDEX_URL, timeout=timeout, max_bytes=max_bytes)
    if not isinstance(payload, Mapping) or not isinstance(payload.get("companies"), list):
        raise ProviderStop("UPSTREAM_CONTRACT_DRIFT", "SinoFacts index schema changed")
    results = []
    for item in payload["companies"]:
        if not isinstance(item, Mapping):
            continue
        searchable = " ".join(
            str(item.get(key) or "") for key in ("slug", "domain", "name_en", "name_zh", "category")
        ).casefold()
        if query in searchable:
            results.append(dict(item))
        if len(results) >= max_results:
            break
    data = {
        "source": str(payload.get("source") or "SinoFacts"),
        "license": str(payload.get("license") or "CC BY 4.0"),
        "generated_at": payload.get("generated_at"),
        "dataset_count": payload.get("count"),
        "query": parameters.get("query"),
        "matches": results,
    }
    return data, {**metadata, "license": "CC BY 4.0", "full_database_mirrored": False}


def _sinofacts_profile(parameters: Mapping[str, Any], timeout: int, max_bytes: int) -> tuple[Any, dict[str, Any]]:
    query = _require_text(parameters.get("query"), "query").casefold()
    raw, metadata = _http_bytes(
        SINOFacts_RECORDS_URL,
        timeout=timeout,
        max_bytes=max(max_bytes, SINOFacts_UPSTREAM_MAX_BYTES),
    )
    selected: Mapping[str, Any] | None = None
    for raw_line in raw.decode("utf-8").splitlines():
        if not raw_line.strip():
            continue
        try:
            row = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, Mapping):
            continue
        profile = row.get("profile") if isinstance(row.get("profile"), Mapping) else {}
        searchable = " ".join(
            str(value or "")
            for value in (
                row.get("slug"),
                row.get("domain"),
                profile.get("name_en"),
                profile.get("name_zh"),
            )
        ).casefold()
        if query == str(row.get("slug") or "").casefold() or query in searchable:
            selected = row
            break
    if selected is None:
        data = {"source": "SinoFacts", "query": parameters.get("query"), "match": None}
    else:
        data = sanitize_company_payload(dict(selected))
        data["license_attribution"] = "Data: SinoFacts (https://sinofacts.com), CC BY 4.0"
    return data, {**metadata, "license": "CC BY 4.0", "records_returned": 0 if selected is None else 1}


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket)
    provider = str(ticket["provider"])
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket.get("acceptance") or {})
    timeout = _bounded_int(
        acceptance.get("timeout_seconds"), default=20, minimum=5, maximum=45, name="timeout_seconds"
    )
    max_bytes = _bounded_int(
        acceptance.get("max_response_bytes"),
        default=1_000_000,
        minimum=1024,
        maximum=1_500_000,
        name="max_response_bytes",
    )
    started = time.perf_counter()
    started_at = utc_now()
    status = "API_PRC_OPEN_FAILED"
    data: Any = None
    metadata: dict[str, Any] = {}
    failure: dict[str, Any] | None = None
    try:
        if operation == "catalog-capabilities":
            data = _provider_rows()[provider]
            metadata = {"source": "repository-catalog", "http_status": None}
        elif provider == "china-check":
            data, metadata = _china_check(operation, parameters, timeout, max_bytes)
        elif provider == "sinofacts" and operation == "company-search":
            data, metadata = _sinofacts_search(parameters, timeout, max_bytes)
        elif provider == "sinofacts" and operation == "company-profile":
            data, metadata = _sinofacts_profile(parameters, timeout, max_bytes)
        else:
            raise ValueError(f"unsupported provider operation: {provider}/{operation}")
        encoded = json.dumps(data, ensure_ascii=False, allow_nan=False).encode("utf-8")
        if len(encoded) > max_bytes:
            raise ProviderStop("BOUNDED_LIMIT_EXCEEDED", f"sanitized result exceeds {max_bytes} bytes")
        status = "API_PRC_OPEN_COMPLETED"
    except ProviderStop as exc:
        status = "API_PRC_OPEN_STOPPED" if exc.code in {
            "AUTHORIZATION_DENIED", "RATE_LIMITED", "TECHNICAL_MEASURE_ENCOUNTERED"
        } else "API_PRC_OPEN_FAILED"
        failure = {"code": exc.code, "message": str(exc), "retryable": exc.retryable}
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        failure = {"code": "PRC_OPEN_REQUEST_REJECTED", "message": str(exc), "retryable": False}
    snapshot = {
        "schema_version": "prc-open-intelligence-snapshot-v1",
        "status": status,
        "created_at": utc_now(),
        "started_at": started_at,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "task_id": str(ticket["task_id"]),
        "provider": provider,
        "operation": operation,
        "objective": str(ticket.get("objective") or ""),
        "ticket_sha256": canonical_sha(ticket),
        "parameters": parameters,
        "data_policy": dict(ticket["data_policy"]),
        "data": data,
        "upstream_metadata": metadata,
        "failure": failure,
        "security": {
            "secret_values_included": False,
            "credentials_required": False,
            "arbitrary_url_allowed": False,
            "write_operations_allowed": False,
            "proxy_rotation_allowed": False,
            "captcha_solving_allowed": False,
            "cross_provider_retry_after_denial": False,
            "personal_contact_fields_removed": True,
            "paid_upgrade_fields_removed": True,
            "public_non_personal_data_only": True
        },
        "model_calls": 0,
    }
    snapshot["snapshot_sha256"] = canonical_sha(snapshot)
    write_json(output_dir / "prc-open-snapshot.json", snapshot)
    write_json(
        output_dir / "prc-open-diagnostics.json",
        {
            "schema_version": "prc-open-intelligence-diagnostics-v1",
            "status": status,
            "provider": provider,
            "operation": operation,
            "failure": failure,
            "credential_secret_name": None,
            "credential_secret_value_exposed": False,
        },
    )
    summary = [
        f"# {status}",
        "",
        f"- Task ID: `{ticket['task_id']}`",
        f"- Provider: `{provider}`",
        f"- Operation: `{operation}`",
        f"- Snapshot SHA256: `{snapshot['snapshot_sha256']}`",
        "- External API key/Secret: `none`",
        "- Model calls: `0`",
    ]
    if failure:
        summary.extend([f"- Error code: `{failure['code']}`", f"- Message: {failure['message']}"])
    (output_dir / "prc-open-summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    write_json(
        output_dir / "artifact-manifest.json",
        {
            "schema_version": "prc-open-intelligence-artifact-manifest-v1",
            "files": [
                "ticket.json",
                "ticket-status.json",
                "prc-open-snapshot.json",
                "prc-open-diagnostics.json",
                "prc-open-summary.md"
            ],
            "snapshot_sha256": snapshot["snapshot_sha256"],
            "secret_values_included": False,
        },
    )
    write_output("status", status)
    write_output("snapshot_sha256", snapshot["snapshot_sha256"])
    return 0 if status == "API_PRC_OPEN_COMPLETED" else 1


def health(output_dir: Path, *, live: bool) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    checks: list[dict[str, Any]] = []
    overall = True
    for provider in ("china-check", "sinofacts"):
        started = time.perf_counter()
        status = "PASS"
        detail: dict[str, Any] = {}
        try:
            if provider == "china-check":
                if live:
                    _, tools, request_log = _mcp_initialize(timeout=20, max_bytes=500_000)
                    detail = {"tools": sorted(tools), "request_count": len(request_log)}
                else:
                    detail = {"mode": "static-only"}
            else:
                if live:
                    payload, _ = _fetch_json(SINOFacts_INDEX_URL, timeout=20, max_bytes=500_000)
                    if not isinstance(payload, Mapping) or int(payload.get("count") or 0) < 1:
                        raise ProviderStop("UPSTREAM_CONTRACT_DRIFT", "SinoFacts index is empty or invalid")
                    license_text = str(payload.get("license") or "")
                    if "CC BY 4.0" not in license_text:
                        raise ProviderStop("LICENSE_SCOPE_BLOCKED", f"unexpected SinoFacts license: {license_text}")
                    detail = {"count": payload.get("count"), "generated_at": payload.get("generated_at"), "license": license_text}
                else:
                    detail = {"mode": "static-only"}
        except Exception as exc:  # health must preserve diagnostics
            status = "FAIL"
            overall = False
            detail = {"error": str(exc), "type": type(exc).__name__}
        checks.append(
            {
                "provider": provider,
                "status": status,
                "elapsed_seconds": round(time.perf_counter() - started, 6),
                "detail": detail,
            }
        )
    report = {
        "schema_version": "prc-open-intelligence-health-v1",
        "created_at": utc_now(),
        "live": live,
        "overall": "PASS" if overall else "FAIL",
        "checks": checks,
        "external_api_keys_required": 0,
        "automatic_paid_overage": False,
    }
    write_json(output_dir / "health.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if overall else 1


def render(output_dir: Path, phase: str, artifact_url: str) -> int:
    if phase == "accepted":
        status = load_json(output_dir / "ticket-status.json")
        print("## API_PRC_OPEN_ACCEPTED")
        print()
        print(f"- Task ID: `{status.get('task_id') or ''}`")
        print(f"- Provider: `{status.get('provider') or ''}`")
        print(f"- Operation: `{status.get('operation') or ''}`")
        print(f"- Ticket SHA256: `{status.get('ticket_sha256') or ''}`")
        print("- External API key/Secret: `none`")
        return 0
    if phase == "rejected":
        status = load_json(output_dir / "ticket-status.json")
        print("## API_PRC_OPEN_REJECTED")
        print()
        print(f"- Reason: `{status.get('reason') or 'invalid ticket'}`")
        return 0
    snapshot = load_json(output_dir / "prc-open-snapshot.json")
    print(f"## {snapshot['status']}")
    print()
    print(f"- Task ID: `{snapshot['task_id']}`")
    print(f"- Provider: `{snapshot['provider']}`")
    print(f"- Operation: `{snapshot['operation']}`")
    print(f"- Snapshot SHA256: `{snapshot['snapshot_sha256']}`")
    print(f"- Artifact: {artifact_url or 'unavailable'}")
    print("- External API key/Secret: `none`")
    if snapshot.get("failure"):
        print(f"- Error code: `{snapshot['failure']['code']}`")
        print(f"- Message: {snapshot['failure']['message']}")
    else:
        excerpt = json.dumps(snapshot.get("data"), ensure_ascii=False, indent=2)
        if len(excerpt) > 30_000:
            excerpt = excerpt[:30_000] + "\n... [truncated; full result in Artifact]"
        print()
        print("```json")
        print(excerpt)
        print("```")
    return 0


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
    render_parser.add_argument("--phase", choices=["accepted", "rejected", "completed"], required=True)
    render_parser.add_argument("--artifact-url", default="")
    health_parser = sub.add_parser("health")
    health_parser.add_argument("--output-dir", required=True)
    health_parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.command == "prepare":
        return prepare(Path(args.event_path), Path(args.output_dir))
    if args.command == "execute":
        return execute(Path(args.ticket), Path(args.output_dir))
    if args.command == "health":
        return health(Path(args.output_dir), live=bool(args.live))
    return render(Path(args.output_dir), args.phase, args.artifact_url)


if __name__ == "__main__":
    raise SystemExit(main())
