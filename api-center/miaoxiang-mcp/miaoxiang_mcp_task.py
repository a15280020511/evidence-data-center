#!/usr/bin/env python3
"""Bounded read-only client for the official Eastmoney Miaoxiang MCP server."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import requests
from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE / "ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"
MCP_URL = "https://mxapi.eastmoney.com/mxds/mcp"
MCP_HOST = "mxapi.eastmoney.com"
PROTOCOL_VERSION = "2025-11-25"
API_KEY_ENV = "EM_API_KEY"


class MiaoxiangMcpError(RuntimeError):
    def __init__(self, code: str, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_output(name: str, value: Any) -> None:
    target = os.getenv("GITHUB_OUTPUT")
    if target:
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(f"{name}={str(value).replace(chr(10), ' ')}\n")


def provider_catalog() -> Mapping[str, Any]:
    return load_json(CATALOG_PATH)["providers"][0]


def operation_catalog(operation: str) -> Mapping[str, Any]:
    for row in provider_catalog()["operations"]:
        if row["operation_id"] == operation:
            return row
    raise ValueError(f"unsupported Miaoxiang MCP operation: {operation}")


def validate_ticket(ticket: Mapping[str, Any]) -> None:
    errors = sorted(
        Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(ticket),
        key=lambda x: list(x.absolute_path),
    )
    if errors:
        raise ValueError(
            "; ".join(
                f"{'.'.join(map(str, error.absolute_path)) or '$'}: {error.message}"
                for error in errors[:20]
            )
        )
    schema = operation_catalog(str(ticket["operation"]))["parameter_schema"]
    errors = sorted(
        Draft202012Validator(schema).iter_errors(ticket.get("parameters") or {}),
        key=lambda x: list(x.absolute_path),
    )
    if errors:
        raise ValueError(
            "; ".join(
                f"parameters.{'.'.join(map(str, error.absolute_path))}: {error.message}"
                for error in errors[:20]
            )
        )


def prepare(event_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    event = load_json(event_path)
    issue = event.get("issue") if isinstance(event.get("issue"), Mapping) else {}
    accepted, reason, ticket = False, "", None
    try:
        if not str(issue.get("title") or "").startswith("[api-mx-mcp]"):
            raise ValueError("issue title must start with [api-mx-mcp]")
        parsed = json.loads(str(issue.get("body") or ""))
        if not isinstance(parsed, Mapping):
            raise ValueError("ticket body must be a JSON object")
        validate_ticket(parsed)
        ticket, accepted = parsed, True
        write_json(output_dir / "ticket.json", ticket)
    except (json.JSONDecodeError, ValueError) as exc:
        reason = str(exc)
    status = {
        "schema_version": "miaoxiang-mcp-ticket-status-v1",
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
    write_output("accepted", str(accepted).lower())
    return 0 if accepted else 1


def api_key() -> str:
    key = str(os.getenv(API_KEY_ENV) or "").strip()
    if not key:
        raise MiaoxiangMcpError(
            "MIAOXIANG_MCP_API_KEY_MISSING",
            f"missing repository Secret {API_KEY_ENV}",
        )
    if not key.startswith("em_"):
        raise MiaoxiangMcpError(
            "MIAOXIANG_MCP_API_KEY_FORMAT_INVALID",
            f"repository Secret {API_KEY_ENV} is not an em_ Miaoxiang MCP key",
        )
    return key


def scrub_secret(value: Any, secret: str) -> Any:
    if isinstance(value, str):
        return value.replace(secret, "[REDACTED]") if secret else value
    if isinstance(value, list):
        return [scrub_secret(item, secret) for item in value]
    if isinstance(value, Mapping):
        return {str(key): scrub_secret(item, secret) for key, item in value.items()}
    return value


def parse_mcp_payload(raw: bytes, content_type: str) -> Any:
    if not raw:
        return {}
    try:
        text = raw.decode("utf-8")
        if (
            "text/event-stream" not in content_type.lower()
            and not text.lstrip().startswith(("event:", "data:"))
        ):
            return json.loads(text)
        events, lines = [], []
        for line in text.splitlines() + [""]:
            if line.startswith("data:"):
                lines.append(line[5:].lstrip())
            elif not line.strip() and lines:
                data, lines = "\n".join(lines), []
                if data and data != "[DONE]":
                    events.append(json.loads(data))
        if not events:
            raise ValueError("empty SSE response")
        return events[-1]
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise MiaoxiangMcpError(
            "MIAOXIANG_MCP_INVALID_RESPONSE",
            "upstream returned invalid MCP content",
        ) from exc


def mcp_post(
    payload: Mapping[str, Any],
    *,
    key: str,
    timeout: int,
    max_bytes: int,
    session_id: str | None = None,
    expect_body: bool = True,
) -> tuple[Any, dict[str, Any], str | None]:
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "User-Agent": "evidence-data-center-miaoxiang-mcp/1",
        "em_api_key": key,
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    for attempt in (1, 2):
        try:
            response = requests.post(
                MCP_URL,
                headers=headers,
                json=dict(payload),
                timeout=timeout,
                allow_redirects=False,
                stream=True,
            )
            raw = response.raw.read(max_bytes + 1, decode_content=True)
        except requests.RequestException as exc:
            if attempt == 1:
                time.sleep(1)
                continue
            raise MiaoxiangMcpError(
                "MIAOXIANG_MCP_CONNECTION_FAILED",
                type(exc).__name__,
                True,
            ) from exc
        if len(raw) > max_bytes:
            raise MiaoxiangMcpError(
                "MIAOXIANG_MCP_RESPONSE_TOO_LARGE",
                "upstream response exceeded max_response_bytes",
            )
        if response.is_redirect:
            raise MiaoxiangMcpError(
                "MIAOXIANG_MCP_REDIRECT_REJECTED",
                f"upstream attempted HTTP {response.status_code} redirect",
            )
        if response.status_code in {401, 403}:
            raise MiaoxiangMcpError(
                "MIAOXIANG_MCP_API_KEY_INVALID",
                f"upstream HTTP {response.status_code}",
            )
        if response.status_code == 429 or response.status_code >= 500:
            if attempt == 1:
                time.sleep(1)
                continue
            raise MiaoxiangMcpError(
                "MIAOXIANG_MCP_HTTP_TRANSIENT",
                f"upstream HTTP {response.status_code}",
                True,
            )
        if not 200 <= response.status_code < 300:
            raise MiaoxiangMcpError(
                "MIAOXIANG_MCP_HTTP_ERROR",
                f"upstream HTTP {response.status_code}",
            )
        content_type = str(response.headers.get("Content-Type") or "")
        parsed = parse_mcp_payload(raw, content_type) if raw else {}
        if expect_body and not parsed:
            raise MiaoxiangMcpError(
                "MIAOXIANG_MCP_EMPTY_RESPONSE",
                "upstream returned an empty response",
            )
        if isinstance(parsed, Mapping) and parsed.get("error"):
            message = json.dumps(parsed["error"], ensure_ascii=False)[:3000]
            code = (
                "MIAOXIANG_MCP_API_KEY_INVALID"
                if any(
                    token in message.lower()
                    for token in ("api key", "apikey", "密钥", "unauthor")
                )
                else "MIAOXIANG_MCP_JSONRPC_ERROR"
            )
            raise MiaoxiangMcpError(code, f"upstream JSON-RPC error: {message}")
        returned_session = (
            str(response.headers.get("Mcp-Session-Id") or "").strip()
            or session_id
        )
        return (
            parsed,
            {
                "http_status": response.status_code,
                "content_type": content_type,
                "response_bytes": len(raw),
                "transport_attempts": attempt,
                "session_id_present": bool(returned_session),
            },
            returned_session,
        )
    raise MiaoxiangMcpError(
        "MIAOXIANG_MCP_CONNECTION_FAILED",
        "upstream connection failed",
        True,
    )


def initialize_mcp(
    *, key: str, timeout: int, max_bytes: int
) -> tuple[dict[str, Any], str | None, list[dict[str, Any]]]:
    response, meta1, session = mcp_post(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {
                    "name": "evidence-data-center",
                    "version": "1.0.0",
                },
            },
        },
        key=key,
        timeout=timeout,
        max_bytes=max_bytes,
    )
    result = response.get("result") if isinstance(response, Mapping) else None
    if not isinstance(result, Mapping):
        raise MiaoxiangMcpError(
            "MIAOXIANG_MCP_INITIALIZE_INVALID",
            "initialize response did not contain result",
        )
    protocol = str(result.get("protocolVersion") or "")
    if protocol != PROTOCOL_VERSION:
        raise MiaoxiangMcpError(
            "MIAOXIANG_MCP_PROTOCOL_MISMATCH",
            f"expected {PROTOCOL_VERSION}, received {protocol or 'missing'}",
        )
    _, meta2, session = mcp_post(
        {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        },
        key=key,
        timeout=timeout,
        max_bytes=max_bytes,
        session_id=session,
        expect_body=False,
    )
    return (
        {
            "protocol_version": protocol,
            "server_info": dict(result.get("serverInfo") or {}),
            "server_capabilities": result.get("capabilities") or {},
        },
        session,
        [meta1, meta2],
    )


def remote_tools_list(
    *, key: str, timeout: int, max_bytes: int
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    init, session, metas = initialize_mcp(
        key=key,
        timeout=timeout,
        max_bytes=max_bytes,
    )
    response, meta, _ = mcp_post(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        },
        key=key,
        timeout=timeout,
        max_bytes=max_bytes,
        session_id=session,
    )
    tools = (
        (response.get("result") or {}).get("tools")
        if isinstance(response, Mapping)
        else None
    )
    if not isinstance(tools, list):
        raise MiaoxiangMcpError(
            "MIAOXIANG_MCP_TOOLS_LIST_INVALID",
            "tools/list response missing result.tools",
        )
    tools = [dict(tool) for tool in tools if isinstance(tool, Mapping)]
    return tools, {
        **init,
        "request_count": 3,
        "request_metadata": [*metas, meta],
        "tool_count": len(tools),
        "upstream_called": True,
    }


def remote_tool_call(
    tool_name: str,
    arguments: Mapping[str, Any],
    *,
    key: str,
    timeout: int,
    max_bytes: int,
) -> tuple[Any, dict[str, Any]]:
    init, session, metas = initialize_mcp(
        key=key,
        timeout=timeout,
        max_bytes=max_bytes,
    )
    response, meta, _ = mcp_post(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": dict(arguments),
            },
        },
        key=key,
        timeout=timeout,
        max_bytes=max_bytes,
        session_id=session,
    )
    result = response.get("result") if isinstance(response, Mapping) else None
    if not isinstance(result, Mapping):
        raise MiaoxiangMcpError(
            "MIAOXIANG_MCP_TOOL_RESULT_INVALID",
            "tools/call response missing result",
        )
    if result.get("isError") is True:
        raise MiaoxiangMcpError(
            "MIAOXIANG_MCP_TOOL_ERROR",
            "MCP tool returned isError=true",
        )
    return dict(result), {
        **init,
        "request_count": 3,
        "request_metadata": [*metas, meta],
        "mcp_tool_name": tool_name,
        "upstream_called": True,
    }


def row_count(value: Any) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, Mapping):
        for key in ("tools", "content", "data", "items", "rows", "results"):
            if isinstance(value.get(key), list):
                return len(value[key])
        return len(value)
    return 1


def write_manifest(output_dir: Path, snapshot_sha: str | None = None) -> None:
    files = sorted(
        path.name
        for path in output_dir.iterdir()
        if path.is_file() and path.name != "artifact-manifest.json"
    )
    write_json(
        output_dir / "artifact-manifest.json",
        {
            "schema_version": "miaoxiang-mcp-artifact-manifest-v1",
            "files": files,
            "snapshot_sha256": snapshot_sha,
            "secret_values_included": False,
            "model_calls": 0,
        },
    )


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket)
    operation, started, key = str(ticket["operation"]), utc_now(), ""
    try:
        if operation == "catalog-capabilities":
            result = load_json(CATALOG_PATH)
            metadata = {
                "upstream_called": False,
                "credential_mode": "none",
                "operation_count": len(provider_catalog()["operations"]),
                "mcp_tool_count": provider_catalog()["limits"][
                    "fixed_mcp_tool_count"
                ],
                "row_count": len(provider_catalog()["operations"]),
            }
        else:
            key = api_key()
            acceptance = ticket["acceptance"]
            if operation == "mcp-tools-list":
                result, metadata = remote_tools_list(
                    key=key,
                    timeout=int(acceptance["timeout_seconds"]),
                    max_bytes=int(acceptance["max_response_bytes"]),
                )
            else:
                tool = str(operation_catalog(operation).get("mcp_tool_name") or "")
                if not tool:
                    raise MiaoxiangMcpError(
                        "MIAOXIANG_MCP_OPERATION_MAPPING_MISSING",
                        operation,
                    )
                result, metadata = remote_tool_call(
                    tool,
                    ticket.get("parameters") or {},
                    key=key,
                    timeout=int(acceptance["timeout_seconds"]),
                    max_bytes=int(acceptance["max_response_bytes"]),
                )
            result, metadata = scrub_secret(result, key), scrub_secret(metadata, key)
            metadata["row_count"] = row_count(result)
            metadata["credential_mode"] = "em_api_key_backend_only"
            if metadata["row_count"] > int(acceptance["max_rows"]):
                raise MiaoxiangMcpError(
                    "MIAOXIANG_MCP_RESULT_TOO_MANY_ROWS",
                    f"result rows {metadata['row_count']} exceed max_rows",
                )
        snapshot = {
            "schema_version": "miaoxiang-mcp-api-snapshot-v1",
            "status": "API_MIAOXIANG_MCP_COMPLETED",
            "task_id": ticket["task_id"],
            "provider": "miaoxiang-mcp",
            "operation": operation,
            "started_at": started,
            "completed_at": utc_now(),
            "ticket_sha256": canonical_sha(ticket),
            "metadata": metadata,
            "result": result,
            "security": {
                "fixed_mcp_url": MCP_URL,
                "fixed_mcp_host": MCP_HOST,
                "secret_values_exposed": False,
                "api_key_header_recorded": False,
                "arbitrary_jsonrpc_methods_allowed": False,
                "arbitrary_mcp_tool_names_allowed": False,
                "write_operations_allowed": False,
                "trading_or_order_execution_allowed": False,
            },
            "model_calls": 0,
        }
        snapshot = scrub_secret(snapshot, key)
        snapshot["snapshot_sha256"] = canonical_sha(snapshot)
        write_json(output_dir / "miaoxiang-mcp-snapshot.json", snapshot)
        write_json(
            output_dir / "miaoxiang-mcp-diagnostics.json",
            {
                "schema_version": "miaoxiang-mcp-diagnostics-v1",
                "status": snapshot["status"],
                "failure": None,
                "secret_values_exposed": False,
                "model_calls": 0,
            },
        )
        write_manifest(output_dir, snapshot["snapshot_sha256"])
        write_output("status", snapshot["status"])
        return 0
    except MiaoxiangMcpError as exc:
        message = str(exc).replace(key, "[REDACTED]") if key else str(exc)
        blocked = exc.code in {
            "MIAOXIANG_MCP_API_KEY_MISSING",
            "MIAOXIANG_MCP_API_KEY_FORMAT_INVALID",
            "MIAOXIANG_MCP_API_KEY_INVALID",
        }
        status = (
            "API_MIAOXIANG_MCP_BLOCKED"
            if blocked
            else "API_MIAOXIANG_MCP_FAILED"
        )
        failure = {
            "schema_version": "miaoxiang-mcp-diagnostics-v1",
            "status": status,
            "task_id": ticket.get("task_id"),
            "provider": "miaoxiang-mcp",
            "operation": operation,
            "started_at": started,
            "failed_at": utc_now(),
            "error": {
                "code": exc.code,
                "message": message[:4000],
                "retryable": exc.retryable,
            },
            "security": {
                "fixed_mcp_url": MCP_URL,
                "secret_values_exposed": False,
                "api_key_header_recorded": False,
            },
            "model_calls": 0,
        }
        write_json(output_dir / "miaoxiang-mcp-diagnostics.json", failure)
        write_manifest(output_dir)
        write_output("status", status)
        write_output("error_code", exc.code)
        return 1


def render(output_dir: Path, phase: str, artifact_url: str = "") -> int:
    if phase in {"accepted", "rejected"}:
        status = load_json(output_dir / "ticket-status.json")
        suffix = "ACCEPTED" if phase == "accepted" else "REJECTED"
        print(f"## API_MIAOXIANG_MCP_{suffix}")
        print()
        if phase == "accepted":
            print(f"- Task ID: `{status.get('task_id') or ''}`")
            print(f"- Operation: `{status.get('operation') or ''}`")
            print(f"- Ticket SHA-256: `{status.get('ticket_sha256') or ''}`")
        else:
            print(f"- Reason: `{status.get('reason') or 'invalid ticket'}`")
        print("- Secret values exposed: `false`")
        print("- Model calls: `0`")
        return 0
    diagnostics = load_json(output_dir / "miaoxiang-mcp-diagnostics.json")
    snapshot_path = output_dir / "miaoxiang-mcp-snapshot.json"
    snapshot = load_json(snapshot_path) if snapshot_path.exists() else {}
    print(f"## {diagnostics['status']}")
    print()
    print(
        f"- Task ID: `{diagnostics.get('task_id') or snapshot.get('task_id') or ''}`"
    )
    print(
        f"- Operation: `{diagnostics.get('operation') or snapshot.get('operation') or ''}`"
    )
    if snapshot:
        metadata = snapshot.get("metadata") or {}
        print(f"- MCP protocol: `{metadata.get('protocol_version') or 'local'}`")
        print(f"- MCP tool: `{metadata.get('mcp_tool_name') or 'none'}`")
        print(
            f"- Upstream called: `{str(metadata.get('upstream_called', False)).lower()}`"
        )
        print(f"- Rows: `{metadata.get('row_count', 0)}`")
        print(f"- Snapshot SHA-256: `{snapshot.get('snapshot_sha256') or ''}`")
    if diagnostics.get("error"):
        print(f"- Error code: `{diagnostics['error']['code']}`")
        print(f"- Message: {diagnostics['error']['message']}")
    print(f"- Artifact: {artifact_url or 'unavailable'}")
    print("- Secret values exposed: `false`")
    print("- Model calls: `0`")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--event-path", required=True)
    prepare_parser.add_argument("--output-dir", required=True)
    execute_parser = subparsers.add_parser("execute")
    execute_parser.add_argument("--ticket", required=True)
    execute_parser.add_argument("--output-dir", required=True)
    render_parser = subparsers.add_parser("render")
    render_parser.add_argument("--output-dir", required=True)
    render_parser.add_argument(
        "--phase",
        choices=["accepted", "rejected", "completed"],
        required=True,
    )
    render_parser.add_argument("--artifact-url", default="")
    args = parser.parse_args()
    if args.command == "prepare":
        return prepare(Path(args.event_path), Path(args.output_dir))
    if args.command == "execute":
        return execute(Path(args.ticket), Path(args.output_dir))
    return render(Path(args.output_dir), args.phase, args.artifact_url)


if __name__ == "__main__":
    raise SystemExit(main())
