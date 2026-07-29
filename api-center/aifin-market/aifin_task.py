#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
CATALOG_PATH = HERE / "provider-catalog.json"
SCHEMA_PATH = HERE / "ticket.schema.json"

SERVER_ENDPOINTS = {
    "stock_data": "https://mcp.wind.com.cn/vserver_stock_data/mcp/",
    "financial_docs": "https://mcp.wind.com.cn/vserver_financial_docs/mcp/",
    "economic_data": "https://mcp.wind.com.cn/vserver_economic_data/mcp/",
    "analytics_data": "https://mcp.wind.com.cn/vserver_analytics_data/mcp/",
}

OPERATION_MAP = {
    "stock-quote": ("stock_data", "get_stock_quote", ("windcode",)),
    "stock-price-indicators": (
        "stock_data",
        "get_stock_price_indicators",
        ("windcode", "indexes"),
    ),
    "financial-news": ("financial_docs", "get_financial_news", ("query", "top_k")),
    "economic-data": (
        "economic_data",
        "natural_language_get_edb_data",
        ("executionMode", "question", "observation", "beginDate", "endDate"),
    ),
    "analytics-query": ("analytics_data", "get_financial_data", ("question",)),
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def github_output(name: str, value: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(f"{name}={value}\n")


def parse_sse_or_json(text: str) -> Any:
    stripped = text.strip()
    if not stripped:
        raise ValueError("empty MCP response")
    if stripped.startswith("{"):
        return json.loads(stripped)
    last_data = None
    for line in stripped.splitlines():
        if line.startswith("data: "):
            last_data = line[6:]
    if last_data is None:
        raise ValueError("MCP response is neither JSON nor SSE")
    return json.loads(last_data)


def mcp_request(server_type: str, method: str, params: Mapping[str, Any], api_key: str) -> Any:
    endpoint = SERVER_ENDPOINTS[server_type]
    body = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": method,
            "params": dict(params),
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "User-Agent": "github-api-center-aifin/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = parse_sse_or_json(response.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")[:500]
        code = "AUTH_ERROR" if exc.code == 401 else "QUOTA_ERROR" if exc.code == 429 else "NETWORK_ERROR"
        raise RuntimeError(f"{code}: HTTP {exc.code}; {body_text}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"NETWORK_ERROR: {exc}") from exc

    if isinstance(payload, Mapping) and payload.get("error"):
        raise RuntimeError(f"MCP_ERROR: {json.dumps(payload['error'], ensure_ascii=False)[:500]}")
    result = payload.get("result") if isinstance(payload, Mapping) else None
    if isinstance(result, Mapping) and result.get("isError"):
        raise RuntimeError(f"TOOL_ERROR: {json.dumps(result, ensure_ascii=False)[:500]}")
    return result


def initialize(server_type: str, api_key: str) -> None:
    mcp_request(
        server_type,
        "initialize",
        {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "github-api-center-aifin", "version": "1.0"},
        },
        api_key,
    )


def sanitize_parameters(operation: str, parameters: Mapping[str, Any]) -> dict[str, Any]:
    if operation == "catalog-tools":
        server_type = str(parameters.get("server_type") or "")
        if server_type not in SERVER_ENDPOINTS:
            raise ValueError(f"unsupported server_type: {server_type}")
        return {"server_type": server_type}
    server_type, tool_name, allowed = OPERATION_MAP[operation]
    _ = (server_type, tool_name)
    unknown = sorted(set(parameters) - set(allowed))
    if unknown:
        raise ValueError(f"unsupported parameters: {unknown}")
    cleaned = {name: parameters[name] for name in allowed if name in parameters}
    required_by_operation = {
        "stock-quote": {"windcode"},
        "stock-price-indicators": {"windcode", "indexes"},
        "financial-news": {"query"},
        "economic-data": {"executionMode", "question"},
        "analytics-query": {"question"},
    }
    missing = sorted(required_by_operation.get(operation, set()) - set(cleaned))
    if missing:
        raise ValueError(f"missing required parameters: {missing}")
    for key, value in cleaned.items():
        if isinstance(value, str) and not value.strip():
            raise ValueError(f"parameter {key} must not be blank")
    return cleaned


def prepare(event_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    event = load_json(event_path)
    issue = event.get("issue") or {}
    body = str(issue.get("body") or "")
    status: dict[str, Any] = {"accepted": False, "status": "API_AIFIN_REJECTED"}
    try:
        ticket = json.loads(body)
        schema = load_json(SCHEMA_PATH)
        validator = Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(ticket), key=lambda item: list(item.absolute_path))
        if errors:
            message = "; ".join(
                f"{'.'.join(str(part) for part in err.absolute_path) or '$'}: {err.message}"
                for err in errors[:20]
            )
            raise ValueError(message)
        operation = str(ticket["operation"])
        params = dict(ticket.get("parameters") or {})
        if operation not in {"catalog-capabilities", "catalog-tools", *OPERATION_MAP.keys()}:
            raise ValueError(f"unsupported operation: {operation}")
        if operation != "catalog-capabilities":
            sanitize_parameters(operation, params)
        write_json(output_dir / "ticket.json", ticket)
        status = {
            "accepted": True,
            "status": "API_AIFIN_ACCEPTED",
            "task_id": ticket["task_id"],
            "operation": operation,
        }
    except Exception as exc:
        status["error"] = {"code": "TICKET_INVALID", "message": str(exc)[:1000]}
    write_json(output_dir / "ticket-status.json", status)
    github_output("accepted", "true" if status["accepted"] else "false")
    return 0 if status["accepted"] else 1


def execute(ticket_path: Path, output_dir: Path) -> int:
    ticket = load_json(ticket_path)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    snapshot: dict[str, Any] = {
        "schema_version": "aifin-snapshot-v1",
        "task_id": ticket["task_id"],
        "objective": ticket["objective"],
        "operation": operation,
        "provider": "Wind AIFin Market",
        "secret_values_exposed": False,
        "model_calls": 0,
    }
    try:
        if operation == "catalog-capabilities":
            snapshot.update(
                {
                    "status": "API_AIFIN_COMPLETED",
                    "result": load_json(CATALOG_PATH),
                    "upstream_called": False,
                }
            )
        else:
            api_key = os.environ.get("WIND_API_KEY", "").strip()
            if not api_key:
                raise RuntimeError("WIND_API_KEY_MISSING: configure repository secret WIND_API_KEY or the same key in API_CENTER_SECRETS_JSON")
            cleaned = sanitize_parameters(operation, parameters)
            if operation == "catalog-tools":
                server_type = cleaned["server_type"]
                initialize(server_type, api_key)
                result = mcp_request(server_type, "tools/list", {}, api_key)
                tool_name = "tools/list"
            else:
                server_type, tool_name, _ = OPERATION_MAP[operation]
                initialize(server_type, api_key)
                result = mcp_request(
                    server_type,
                    "tools/call",
                    {
                        "name": tool_name,
                        "arguments": cleaned,
                        "_meta": {"clientVersion": "1.0"},
                    },
                    api_key,
                )
            serialized = json.dumps(result, ensure_ascii=False)
            if len(serialized.encode("utf-8")) > 200_000:
                raise RuntimeError("RESPONSE_TOO_LARGE: response exceeded 200000 bytes")
            snapshot.update(
                {
                    "status": "API_AIFIN_COMPLETED",
                    "server_type": server_type,
                    "tool_name": tool_name,
                    "result": result,
                    "upstream_called": True,
                }
            )
    except Exception as exc:
        message = str(exc)
        status = "API_AIFIN_BLOCKED" if "WIND_API_KEY_MISSING" in message else "API_AIFIN_FAILED"
        snapshot.update(
            {
                "status": status,
                "error": {
                    "code": message.split(":", 1)[0][:100],
                    "message": message[:1000],
                },
                "upstream_called": False if status == "API_AIFIN_BLOCKED" else True,
            }
        )
    write_json(output_dir / "aifin-snapshot.json", snapshot)
    write_json(
        output_dir / "aifin-diagnostics.json",
        {
            "status": snapshot["status"],
            "operation": operation,
            "secret_values_exposed": False,
            "error": snapshot.get("error"),
        },
    )
    github_output("status", snapshot["status"])
    return 0 if snapshot["status"] == "API_AIFIN_COMPLETED" else 1


def render(output_dir: Path, phase: str, artifact_url: str = "") -> int:
    status_doc = load_json(output_dir / "ticket-status.json") if (output_dir / "ticket-status.json").exists() else {}
    if phase == "accepted":
        print(
            "\n".join(
                [
                    "## API_AIFIN_ACCEPTED",
                    "",
                    f"- Task ID: `{status_doc.get('task_id', 'unknown')}`",
                    f"- Operation: `{status_doc.get('operation', 'unknown')}`",
                    "- Secret values exposed: `false`",
                ]
            )
        )
        return 0
    if phase == "rejected":
        error = status_doc.get("error") or {}
        print(
            "\n".join(
                [
                    "## API_AIFIN_REJECTED",
                    "",
                    f"- Error code: `{error.get('code', 'TICKET_INVALID')}`",
                    f"- Message: {error.get('message', 'invalid ticket')}",
                ]
            )
        )
        return 0

    snapshot_path = output_dir / "aifin-snapshot.json"
    snapshot = load_json(snapshot_path) if snapshot_path.exists() else {"status": "API_AIFIN_FAILED"}
    lines = [
        f"## {snapshot.get('status', 'API_AIFIN_FAILED')}",
        "",
        f"- Task ID: `{snapshot.get('task_id', 'unknown')}`",
        f"- Operation: `{snapshot.get('operation', 'unknown')}`",
        f"- Upstream called: `{str(bool(snapshot.get('upstream_called'))).lower()}`",
        "- Secret values exposed: `false`",
        f"- Artifact: {artifact_url or 'unavailable'}",
    ]
    if snapshot.get("server_type"):
        lines.append(f"- Server type: `{snapshot['server_type']}`")
    if snapshot.get("tool_name"):
        lines.append(f"- Tool: `{snapshot['tool_name']}`")
    if snapshot.get("error"):
        lines.extend(
            [
                f"- Error code: `{snapshot['error'].get('code', 'UNKNOWN')}`",
                f"- Error: {snapshot['error'].get('message', '')}",
            ]
        )
    print("\n".join(lines))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p_prepare = sub.add_parser("prepare")
    p_prepare.add_argument("--event-path", required=True)
    p_prepare.add_argument("--output-dir", required=True)
    p_execute = sub.add_parser("execute")
    p_execute.add_argument("--ticket", required=True)
    p_execute.add_argument("--output-dir", required=True)
    p_render = sub.add_parser("render")
    p_render.add_argument("--output-dir", required=True)
    p_render.add_argument("--phase", required=True, choices=["accepted", "rejected", "completed"])
    p_render.add_argument("--artifact-url", default="")
    args = parser.parse_args()
    if args.command == "prepare":
        return prepare(Path(args.event_path), Path(args.output_dir))
    if args.command == "execute":
        return execute(Path(args.ticket), Path(args.output_dir))
    return render(Path(args.output_dir), args.phase, args.artifact_url)


if __name__ == "__main__":
    raise SystemExit(main())
