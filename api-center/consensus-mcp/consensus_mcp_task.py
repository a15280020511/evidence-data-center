#!/usr/bin/env python3
"""Bounded read-only client for the official Consensus MCP server."""
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
MCP_URL = "https://mcp.consensus.app/mcp"
CLIENT_PROTOCOL_VERSION = "2025-03-26"
TOKEN_ENV = "CONSENSUS_MCP_BEARER_TOKEN"


class ConsensusMcpError(RuntimeError):
    def __init__(self, code: str, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


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
    raise ValueError(f"unsupported Consensus MCP operation: {operation}")


def validate_ticket(ticket: Mapping[str, Any]) -> None:
    errors = sorted(
        Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(ticket),
        key=lambda x: list(x.absolute_path),
    )
    if errors:
        raise ValueError("; ".join(
            f"{'.'.join(map(str, error.absolute_path)) or '$'}: {error.message}"
            for error in errors[:20]
        ))
    operation = operation_catalog(str(ticket["operation"]))
    parameter_schema = operation["parameter_schema"]
    errors = sorted(
        Draft202012Validator(parameter_schema).iter_errors(ticket.get("parameters") or {}),
        key=lambda x: list(x.absolute_path),
    )
    if errors:
        raise ValueError("; ".join(
            f"parameters.{'.'.join(map(str, error.absolute_path))}: {error.message}"
            for error in errors[:20]
        ))
    params = ticket.get("parameters") or {}
    if "year_min" in params and "year_max" in params and params["year_min"] > params["year_max"]:
        raise ValueError("parameters.year_min must be <= parameters.year_max")
    if "duration_min" in params and "duration_max" in params and params["duration_min"] > params["duration_max"]:
        raise ValueError("parameters.duration_min must be <= parameters.duration_max")


def bearer_token() -> str | None:
    token = str(os.getenv(TOKEN_ENV) or "").strip()
    return token or None


def parse_mcp_payload(raw: bytes, content_type: str) -> Any:
    if not raw:
        return {}
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ConsensusMcpError("CONSENSUS_MCP_INVALID_RESPONSE", "response was not UTF-8") from exc
    if "text/event-stream" not in content_type.lower() and not text.lstrip().startswith(("event:", "data:")):
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ConsensusMcpError("CONSENSUS_MCP_INVALID_RESPONSE", "response was not valid JSON") from exc
    events: list[Any] = []
    data_lines: list[str] = []
    for line in text.splitlines() + [""]:
        if line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
        elif not line.strip() and data_lines:
            data = "\n".join(data_lines)
            data_lines = []
            if data and data != "[DONE]":
                try:
                    events.append(json.loads(data))
                except json.JSONDecodeError as exc:
                    raise ConsensusMcpError("CONSENSUS_MCP_INVALID_RESPONSE", "SSE data was not JSON") from exc
    if not events:
        raise ConsensusMcpError("CONSENSUS_MCP_EMPTY_RESPONSE", "empty SSE response")
    return events[-1]


def mcp_post(
    payload: Mapping[str, Any],
    *,
    timeout: int,
    max_bytes: int,
    token: str | None = None,
    session_id: str | None = None,
    protocol_version: str | None = None,
    expect_body: bool = True,
) -> tuple[Any, dict[str, Any], str | None]:
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "User-Agent": "evidence-data-center-consensus-mcp/1",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    if protocol_version:
        headers["MCP-Protocol-Version"] = protocol_version
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
            raise ConsensusMcpError("CONSENSUS_MCP_CONNECTION_FAILED", type(exc).__name__, True) from exc
        if len(raw) > max_bytes:
            raise ConsensusMcpError("CONSENSUS_MCP_RESPONSE_TOO_LARGE", "response exceeded max_response_bytes")
        if response.is_redirect:
            raise ConsensusMcpError("CONSENSUS_MCP_REDIRECT_REJECTED", f"HTTP {response.status_code} redirect")
        if response.status_code in {401, 403}:
            raise ConsensusMcpError("CONSENSUS_MCP_AUTH_REQUIRED_OR_INVALID", f"upstream HTTP {response.status_code}")
        if response.status_code == 429 or response.status_code >= 500:
            if attempt == 1:
                time.sleep(1)
                continue
            raise ConsensusMcpError("CONSENSUS_MCP_HTTP_TRANSIENT", f"upstream HTTP {response.status_code}", True)
        if not 200 <= response.status_code < 300:
            raise ConsensusMcpError("CONSENSUS_MCP_HTTP_ERROR", f"upstream HTTP {response.status_code}")
        content_type = str(response.headers.get("Content-Type") or "")
        parsed = parse_mcp_payload(raw, content_type) if raw else {}
        if expect_body and not parsed:
            raise ConsensusMcpError("CONSENSUS_MCP_EMPTY_RESPONSE", "upstream returned empty response")
        if isinstance(parsed, Mapping) and parsed.get("error"):
            message = json.dumps(parsed["error"], ensure_ascii=False)[:2000]
            raise ConsensusMcpError("CONSENSUS_MCP_JSONRPC_ERROR", message)
        returned_session = str(response.headers.get("Mcp-Session-Id") or "").strip() or session_id
        return parsed, {
            "http_status": response.status_code,
            "content_type": content_type,
            "response_bytes": len(raw),
            "transport_attempts": attempt,
            "session_id_present": bool(returned_session),
            "authenticated": bool(token),
        }, returned_session
    raise ConsensusMcpError("CONSENSUS_MCP_CONNECTION_FAILED", "connection failed", True)


def initialize_mcp(*, timeout: int, max_bytes: int, token: str | None) -> tuple[dict[str, Any], str | None, list[dict[str, Any]]]:
    response, meta1, session = mcp_post(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": CLIENT_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "evidence-data-center", "version": "1.0.0"},
            },
        },
        timeout=timeout,
        max_bytes=max_bytes,
        token=token,
    )
    result = response.get("result") if isinstance(response, Mapping) else None
    if not isinstance(result, Mapping):
        raise ConsensusMcpError("CONSENSUS_MCP_INITIALIZE_INVALID", "initialize result missing")
    protocol = str(result.get("protocolVersion") or CLIENT_PROTOCOL_VERSION)
    _, meta2, session = mcp_post(
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        timeout=timeout,
        max_bytes=max_bytes,
        token=token,
        session_id=session,
        protocol_version=protocol,
        expect_body=False,
    )
    return {
        "protocol_version": protocol,
        "server_info": dict(result.get("serverInfo") or {}),
        "server_capabilities": result.get("capabilities") or {},
    }, session, [meta1, meta2]


def tools_list(*, timeout: int, max_bytes: int, token: str | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    init, session, metas = initialize_mcp(timeout=timeout, max_bytes=max_bytes, token=token)
    response, meta, _ = mcp_post(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        timeout=timeout,
        max_bytes=max_bytes,
        token=token,
        session_id=session,
        protocol_version=init["protocol_version"],
    )
    tools = (response.get("result") or {}).get("tools") if isinstance(response, Mapping) else None
    if not isinstance(tools, list):
        raise ConsensusMcpError("CONSENSUS_MCP_TOOLS_LIST_INVALID", "result.tools missing")
    rows = [dict(tool) for tool in tools if isinstance(tool, Mapping)]
    return rows, {**init, "request_count": 3, "request_metadata": [*metas, meta], "tool_count": len(rows)}


def extract_structured_result(result: Mapping[str, Any]) -> Any:
    structured = result.get("structuredContent")
    if isinstance(structured, (Mapping, list)):
        return structured
    content = result.get("content")
    if isinstance(content, list):
        for item in content:
            if not isinstance(item, Mapping) or item.get("type") != "text":
                continue
            text = str(item.get("text") or "").strip()
            if not text:
                continue
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, (Mapping, list)):
                return parsed
    return dict(result)


def truncate_papers(value: Any, maximum: int) -> Any:
    if isinstance(value, Mapping) and isinstance(value.get("papers"), list):
        output = dict(value)
        output["papers"] = list(value["papers"])[:maximum]
        output["returned_papers_after_local_cap"] = len(output["papers"])
        return output
    if isinstance(value, list):
        return value[:maximum]
    return value


def search(arguments: Mapping[str, Any], *, timeout: int, max_bytes: int, max_rows: int, token: str | None) -> tuple[Any, dict[str, Any]]:
    init, session, metas = initialize_mcp(timeout=timeout, max_bytes=max_bytes, token=token)
    response, meta, _ = mcp_post(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "search", "arguments": dict(arguments)},
        },
        timeout=timeout,
        max_bytes=max_bytes,
        token=token,
        session_id=session,
        protocol_version=init["protocol_version"],
    )
    result = response.get("result") if isinstance(response, Mapping) else None
    if not isinstance(result, Mapping):
        raise ConsensusMcpError("CONSENSUS_MCP_TOOL_RESULT_INVALID", "tools/call result missing")
    if result.get("isError") is True:
        raise ConsensusMcpError("CONSENSUS_MCP_TOOL_ERROR", "search returned isError=true")
    normalized = truncate_papers(extract_structured_result(result), max_rows)
    return normalized, {
        **init,
        "request_count": 3,
        "request_metadata": [*metas, meta],
        "mcp_tool_name": "search",
        "auth_mode": "bearer" if token else "anonymous-free",
    }


def prepare(event_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    event = load_json(event_path)
    issue = event.get("issue") if isinstance(event.get("issue"), Mapping) else {}
    accepted, reason, ticket = False, "", None
    try:
        if not str(issue.get("title") or "").startswith("[api-consensus-mcp]"):
            raise ValueError("issue title must start with [api-consensus-mcp]")
        parsed = json.loads(str(issue.get("body") or ""))
        if not isinstance(parsed, Mapping):
            raise ValueError("ticket body must be a JSON object")
        validate_ticket(parsed)
        ticket, accepted = dict(parsed), True
        write_json(output_dir / "ticket.json", ticket)
    except (json.JSONDecodeError, ValueError) as exc:
        reason = str(exc)
    status = {
        "schema_version": "consensus-mcp-ticket-status-v1",
        "accepted": accepted,
        "reason": reason,
        "task_id": str((ticket or {}).get("task_id") or ""),
        "operation": str((ticket or {}).get("operation") or ""),
        "ticket_sha256": canonical_sha(ticket) if ticket else None,
        "model_calls": 0,
        "secret_values_exposed": False,
    }
    write_json(output_dir / "ticket-status.json", status)
    write_output("accepted", str(accepted).lower())
    return 0 if accepted else 1


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket)
    operation = str(ticket["operation"])
    acceptance = ticket["acceptance"]
    timeout = int(acceptance["timeout_seconds"])
    max_bytes = int(acceptance["max_response_bytes"])
    max_rows = int(acceptance["max_rows"])
    token = bearer_token()
    started = utc_now()
    snapshot: dict[str, Any] = {
        "schema_version": "consensus-mcp-snapshot-v1",
        "status": "API_CONSENSUS_MCP_FAILED",
        "task_id": ticket["task_id"],
        "operation": operation,
        "objective": ticket["objective"],
        "started_at": started,
        "completed_at": None,
        "official_endpoint": MCP_URL,
        "auth_mode": "bearer" if token else "anonymous-free",
        "model_calls": 0,
        "write_operations": 0,
        "web_scraping": false,
    }
    try:
        if operation == "catalog-capabilities":
            result, meta = provider_catalog(), {"upstream_called": False, "request_count": 0}
        elif operation == "mcp-tools-list":
            result, meta = tools_list(timeout=timeout, max_bytes=max_bytes, token=token)
            allowed = {"search"}
            remote_names = {str(row.get("name") or "") for row in result}
            if "search" not in remote_names:
                raise ConsensusMcpError("CONSENSUS_MCP_SEARCH_TOOL_MISSING", "remote tools/list did not expose search")
            meta["allowed_tools_present"] = sorted(remote_names & allowed)
        else:
            result, meta = search(ticket.get("parameters") or {}, timeout=timeout, max_bytes=max_bytes, max_rows=max_rows, token=token)
        snapshot.update({"status": "API_CONSENSUS_MCP_COMPLETED", "result": result, "transport": meta})
    except ConsensusMcpError as exc:
        snapshot["error"] = {"code": exc.code, "message": str(exc), "retryable": exc.retryable}
    snapshot["completed_at"] = utc_now()
    snapshot["snapshot_sha256"] = canonical_sha({k: v for k, v in snapshot.items() if k != "snapshot_sha256"})
    write_json(output_dir / "snapshot.json", snapshot)
    write_json(output_dir / "artifact-manifest.json", {
        "schema_version": "consensus-mcp-artifact-manifest-v1",
        "files": ["snapshot.json", "ticket-status.json", "ticket.json"],
        "secret_values_exposed": False,
        "model_calls": 0,
    })
    write_output("status", snapshot["status"])
    return 0 if snapshot["status"] == "API_CONSENSUS_MCP_COMPLETED" else 1


def render(output_dir: Path, phase: str, artifact_url: str = "") -> int:
    status = load_json(output_dir / "ticket-status.json") if (output_dir / "ticket-status.json").exists() else {}
    if phase == "accepted":
        print("## CONSENSUS_MCP_ACCEPTED\n")
        print(f"- Task ID: `{status.get('task_id', '')}`")
        print(f"- Operation: `{status.get('operation', '')}`")
        print("- Default auth: `anonymous-free`")
        print("- Model calls: `0`")
        return 0
    if phase == "rejected":
        print("## CONSENSUS_MCP_REJECTED\n")
        print(f"- Reason: `{status.get('reason', 'invalid ticket')}`")
        return 0
    snapshot = load_json(output_dir / "snapshot.json") if (output_dir / "snapshot.json").exists() else {}
    print(f"## {snapshot.get('status', 'API_CONSENSUS_MCP_FAILED')}\n")
    print(f"- Task ID: `{snapshot.get('task_id', '')}`")
    print(f"- Operation: `{snapshot.get('operation', '')}`")
    print(f"- Auth mode: `{snapshot.get('auth_mode', '')}`")
    print("- Model calls: `0`")
    if artifact_url:
        print(f"- Artifact: {artifact_url}")
    if snapshot.get("error"):
        print(f"- Error: `{snapshot['error'].get('code')}` — {snapshot['error'].get('message')}")
    return 0


def canary(output: Path) -> int:
    token = bearer_token()
    report: dict[str, Any] = {"status": "fail", "endpoint": MCP_URL, "auth_mode": "bearer" if token else "anonymous-free"}
    try:
        tools, tools_meta = tools_list(timeout=30, max_bytes=1_000_000, token=token)
        names = sorted(str(row.get("name") or "") for row in tools)
        if "search" not in names:
            raise ConsensusMcpError("CONSENSUS_MCP_SEARCH_TOOL_MISSING", "search tool missing")
        result, search_meta = search({"query": "causal inference", "exclude_preprints": True}, timeout=30, max_bytes=1_500_000, max_rows=3, token=token)
        papers = result.get("papers") if isinstance(result, Mapping) and isinstance(result.get("papers"), list) else []
        report.update({
            "status": "pass",
            "tools": names,
            "search_tool_present": True,
            "paper_count": len(papers) if papers else None,
            "tools_transport": tools_meta,
            "search_transport": search_meta,
        })
    except ConsensusMcpError as exc:
        report["error"] = {"code": exc.code, "message": str(exc), "retryable": exc.retryable}
    write_json(output, report)
    print(json.dumps({"status": report["status"], "auth_mode": report["auth_mode"], "search_tool_present": report.get("search_tool_present", False), "paper_count": report.get("paper_count")}, ensure_ascii=False))
    return 0 if report["status"] == "pass" else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p_prepare = sub.add_parser("prepare")
    p_prepare.add_argument("--event-path", type=Path, required=True)
    p_prepare.add_argument("--output-dir", type=Path, required=True)

    p_execute = sub.add_parser("execute")
    p_execute.add_argument("--ticket", type=Path, required=True)
    p_execute.add_argument("--output-dir", type=Path, required=True)

    p_render = sub.add_parser("render")
    p_render.add_argument("--output-dir", type=Path, required=True)
    p_render.add_argument("--phase", choices=["accepted", "rejected", "completed"], required=True)
    p_render.add_argument("--artifact-url", default="")

    p_canary = sub.add_parser("canary")
    p_canary.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "prepare":
        return prepare(args.event_path, args.output_dir)
    if args.command == "execute":
        return execute(args.ticket, args.output_dir)
    if args.command == "render":
        return render(args.output_dir, args.phase, args.artifact_url)
    return canary(args.output)


if __name__ == "__main__":
    raise SystemExit(main())
