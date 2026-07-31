#!/usr/bin/env python3
"""Fixed, fully catalogued, read-only Wind AIFin Market adapter."""
from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
CATALOG_PATH = HERE / "provider-catalog.json"
SCHEMA_PATH = HERE / "ticket.schema.json"
MAX_UPSTREAM_BYTES = 1_000_000

SERVER_ENDPOINTS = {
    "stock_data": "https://mcp.wind.com.cn/vserver_stock_data/mcp/",
    "financial_docs": "https://mcp.wind.com.cn/vserver_financial_docs/mcp/",
    "economic_data": "https://mcp.wind.com.cn/vserver_economic_data/mcp/",
    "analytics_data": "https://mcp.wind.com.cn/vserver_analytics_data/mcp/",
}

OPERATION_MAP = {
    "stock-price-indicators": ("stock_data", "get_stock_price_indicators", ("windcode", "indexes")),
    "risk-metrics": ("stock_data", "get_risk_metrics", ("question",)),
    "stock-events": ("stock_data", "get_stock_events", ("question",)),
    "stock-kline": ("stock_data", "get_stock_kline", ("windcode", "begin_date", "end_date", "count", "period", "aftype", "issusp", "afdate")),
    "stock-basicinfo": ("stock_data", "get_stock_basicinfo", ("question",)),
    "stock-equity-holders": ("stock_data", "get_stock_equity_holders", ("question",)),
    "stock-fundamentals": ("stock_data", "get_stock_fundamentals", ("question",)),
    "stock-quote": ("stock_data", "get_stock_quote", ("windcode", "begin", "end")),
    "stock-technicals": ("stock_data", "get_stock_technicals", ("question",)),
    "stock-search": ("stock_data", "search_stocks", ("question",)),
    "company-announcements": ("financial_docs", "get_company_announcements", ("query", "top_k")),
    "financial-news": ("financial_docs", "get_financial_news", ("query", "top_k")),
    "economic-data": ("economic_data", "natural_language_get_edb_data", ("executionMode", "question", "observation", "beginDate", "endDate")),
    "economic-data-direct": ("economic_data", "get_economic_data", ("metricIdsStr", "beginDate", "endDate", "freq", "magnitude", "currency", "searchType", "ifUnion")),
    "analytics-query": ("analytics_data", "get_financial_data", ("question",)),
}

REQUIRED = {
    "stock-price-indicators": {"windcode"}, "risk-metrics": {"question"},
    "stock-events": {"question"}, "stock-kline": {"windcode", "begin_date", "end_date"},
    "stock-basicinfo": {"question"}, "stock-equity-holders": {"question"},
    "stock-fundamentals": {"question"}, "stock-quote": {"windcode"},
    "stock-technicals": {"question"}, "stock-search": {"question"},
    "company-announcements": {"query"}, "financial-news": {"query"},
    "economic-data": {"executionMode", "question"}, "economic-data-direct": {"metricIdsStr"},
    "analytics-query": {"question"},
}
DATE_DASH_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
DATE_COMPACT_RE = re.compile(r"^[0-9]{8}$")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def github_output(name: str, value: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(f"{name}={value.replace(chr(10), ' ')}\n")


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
    body = json.dumps({"jsonrpc": "2.0", "id": int(time.time() * 1000), "method": method, "params": dict(params)}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(endpoint, data=body, method="POST", headers={
        "Authorization": f"Bearer {api_key}", "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json", "User-Agent": "github-api-center-aifin/2.0",
    })
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read(MAX_UPSTREAM_BYTES + 1)
            if len(raw) > MAX_UPSTREAM_BYTES:
                raise RuntimeError(f"RESPONSE_TOO_LARGE: upstream response exceeded {MAX_UPSTREAM_BYTES} bytes")
            payload = parse_sse_or_json(raw.decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        body_text = exc.read(500).decode("utf-8", errors="replace")
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
    mcp_request(server_type, "initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "github-api-center-aifin", "version": "2.0"}}, api_key)


def _require_text(params: Mapping[str, Any], name: str, maximum: int = 20000) -> str:
    value = str(params.get(name) or "").strip()
    if not value or len(value) > maximum:
        raise ValueError(f"parameter {name} must contain 1 to {maximum} characters")
    return value


def _optional_date(params: Mapping[str, Any], name: str, compact: bool = False) -> None:
    value = str(params.get(name) or "")
    if value and not (DATE_COMPACT_RE if compact else DATE_DASH_RE).fullmatch(value):
        raise ValueError(f"parameter {name} must use {'YYYYMMDD' if compact else 'YYYY-MM-DD'}")


def _catalog_tool_parameters(parameters: Mapping[str, Any]) -> dict[str, Any]:
    server_type = str(parameters.get("server_type") or "")
    if server_type not in SERVER_ENDPOINTS:
        raise ValueError(f"unsupported server_type: {server_type}")
    if set(parameters) != {"server_type"}:
        raise ValueError("catalog-tools only accepts server_type")
    return {"server_type": server_type}


def _base_parameters(operation: str, parameters: Mapping[str, Any]) -> dict[str, Any]:
    _, _, allowed = OPERATION_MAP[operation]
    unknown = sorted(set(parameters) - set(allowed))
    if unknown:
        raise ValueError(f"unsupported parameters: {unknown}")
    cleaned = {name: parameters[name] for name in allowed if name in parameters}
    missing = sorted(REQUIRED[operation] - set(cleaned))
    if missing:
        raise ValueError(f"missing required parameters: {missing}")
    blank = sorted(key for key, value in cleaned.items() if isinstance(value, str) and not value.strip())
    if blank:
        raise ValueError(f"blank parameters are forbidden: {blank}")
    for name in REQUIRED[operation] & {"question", "query", "metricIdsStr", "windcode", "executionMode"}:
        _require_text(cleaned, name)
    return cleaned


def _document_parameters(cleaned: dict[str, Any]) -> None:
    top_k = int(cleaned.get("top_k", 5))
    if not 1 <= top_k <= 20:
        raise ValueError("top_k must be between 1 and 20")
    cleaned["top_k"] = top_k


def _kline_parameters(cleaned: dict[str, Any]) -> None:
    for name in ("begin_date", "end_date", "afdate"):
        _optional_date(cleaned, name)
    if "count" in cleaned:
        count = int(cleaned["count"])
        if count == 0 or not -5000 <= count <= 5000:
            raise ValueError("count must be between -5000 and 5000 and not zero")
        cleaned["count"] = count
    enums = {
        "period": {"1", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"},
        "aftype": {"0", "1"},
        "issusp": {"0", "1"},
    }
    _normalize_enums(cleaned, enums)


def _normalize_enums(cleaned: dict[str, Any], enums: Mapping[str, set[str]]) -> None:
    for name, values in enums.items():
        if name not in cleaned:
            continue
        normalized = str(cleaned[name])
        if normalized not in values:
            raise ValueError(f"unsupported {name}")
        cleaned[name] = normalized


def _economic_parameters(cleaned: dict[str, Any]) -> None:
    aliases = {"search": "仅搜索", "fetch": "仅提数", "searchFetch": "搜索并提数"}
    cleaned["executionMode"] = aliases.get(str(cleaned["executionMode"]), str(cleaned["executionMode"]))
    if cleaned["executionMode"] not in {"仅搜索", "仅提数", "搜索并提数"}:
        raise ValueError("executionMode must be 仅搜索, 仅提数, 搜索并提数 or a supported English alias")
    _optional_date(cleaned, "beginDate", compact=True)
    _optional_date(cleaned, "endDate", compact=True)
    has_range = bool(cleaned.get("beginDate") and cleaned.get("endDate"))
    has_observation = bool(cleaned.get("observation"))
    if cleaned["executionMode"] in {"仅提数", "搜索并提数"} and not (has_observation or has_range):
        raise ValueError("data-fetching modes require observation or both beginDate and endDate")
    if has_observation and (cleaned.get("beginDate") or cleaned.get("endDate")):
        raise ValueError("observation is mutually exclusive with beginDate/endDate")


def _economic_direct_parameters(cleaned: dict[str, Any]) -> None:
    _optional_date(cleaned, "beginDate", compact=True)
    _optional_date(cleaned, "endDate", compact=True)
    _normalize_enums(cleaned, {
        "freq": {"1", "2", "3", "4", "5", "6", "7", "8"},
        "magnitude": {"1", "1000", "10000", "1000000", "10000000", "100000000", "1000000000", "10000000000", "100000000000", "1000000000000"},
        "currency": {"USD", "CNY", "EUR", "JPY", "AUD", "GBP", "CHF", "CAD", "SGD", "BYR", "HKD", "MYR"},
        "searchType": {"0", "1"},
        "ifUnion": {"1", "2"},
    })


def sanitize_parameters(operation: str, parameters: Mapping[str, Any]) -> dict[str, Any]:
    if operation == "catalog-tools":
        return _catalog_tool_parameters(parameters)
    cleaned = _base_parameters(operation, parameters)
    if operation in {"company-announcements", "financial-news"}:
        _document_parameters(cleaned)
    elif operation == "stock-kline":
        _kline_parameters(cleaned)
    elif operation == "stock-quote":
        _optional_date(cleaned, "begin")
        _optional_date(cleaned, "end")
    elif operation == "economic-data":
        _economic_parameters(cleaned)
    elif operation == "economic-data-direct":
        _economic_direct_parameters(cleaned)
    return cleaned


def prepare(event_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    event = load_json(event_path); issue = event.get("issue") or {}; body = str(issue.get("body") or "")
    status: dict[str, Any] = {"accepted": False, "status": "API_AIFIN_REJECTED"}
    try:
        ticket = json.loads(body); validator = Draft202012Validator(load_json(SCHEMA_PATH))
        errors = sorted(validator.iter_errors(ticket), key=lambda item: list(item.absolute_path))
        if errors:
            raise ValueError("; ".join(f"{'.'.join(str(part) for part in err.absolute_path) or '$'}: {err.message}" for err in errors[:20]))
        operation = str(ticket["operation"]); params = dict(ticket.get("parameters") or {})
        if operation not in {"catalog-capabilities", "catalog-tools", *OPERATION_MAP.keys()}:
            raise ValueError(f"unsupported operation: {operation}")
        if operation == "catalog-capabilities" and params:
            raise ValueError("catalog-capabilities accepts no parameters")
        if operation != "catalog-capabilities": sanitize_parameters(operation, params)
        write_json(output_dir / "ticket.json", ticket)
        status = {"accepted": True, "status": "API_AIFIN_ACCEPTED", "task_id": ticket["task_id"], "operation": operation}
    except Exception as exc:
        status["error"] = {"code": "TICKET_INVALID", "message": str(exc)[:1000]}
    write_json(output_dir / "ticket-status.json", status); github_output("accepted", "true" if status["accepted"] else "false")
    return 0 if status["accepted"] else 1


def execute(ticket_path: Path, output_dir: Path) -> int:
    ticket = load_json(ticket_path); operation = str(ticket["operation"]); parameters = dict(ticket.get("parameters") or {})
    snapshot: dict[str, Any] = {"schema_version": "aifin-snapshot-v2", "task_id": ticket["task_id"], "objective": ticket["objective"], "operation": operation, "provider": "Wind AIFin Market", "secret_values_exposed": False, "model_calls": 0}
    try:
        if operation == "catalog-capabilities":
            snapshot.update({"status": "API_AIFIN_COMPLETED", "result": load_json(CATALOG_PATH), "upstream_called": False})
        else:
            api_key = os.environ.get("WIND_API_KEY", "").strip()
            if not api_key:
                raise RuntimeError("WIND_API_KEY_MISSING: configure dedicated Repository Secret WIND_API_KEY")
            cleaned = sanitize_parameters(operation, parameters)
            if operation == "catalog-tools":
                server_type = cleaned["server_type"]; initialize(server_type, api_key); result = mcp_request(server_type, "tools/list", {}, api_key); tool_name = "tools/list"
            else:
                server_type, tool_name, _ = OPERATION_MAP[operation]; initialize(server_type, api_key)
                result = mcp_request(server_type, "tools/call", {"name": tool_name, "arguments": cleaned, "_meta": {"clientVersion": "2.0"}}, api_key)
            serialized = json.dumps(result, ensure_ascii=False, allow_nan=False).encode("utf-8")
            if len(serialized) > MAX_UPSTREAM_BYTES:
                raise RuntimeError(f"RESPONSE_TOO_LARGE: response exceeded {MAX_UPSTREAM_BYTES} bytes")
            snapshot.update({"status": "API_AIFIN_COMPLETED", "server_type": server_type, "tool_name": tool_name, "result": result, "upstream_called": True})
    except Exception as exc:
        message = str(exc); status = "API_AIFIN_BLOCKED" if "WIND_API_KEY_MISSING" in message else "API_AIFIN_FAILED"
        snapshot.update({"status": status, "error": {"code": message.split(":", 1)[0][:100], "message": message[:1000]}, "upstream_called": False if status == "API_AIFIN_BLOCKED" else True})
    write_json(output_dir / "aifin-snapshot.json", snapshot)
    write_json(output_dir / "aifin-diagnostics.json", {"status": snapshot["status"], "operation": operation, "secret_values_exposed": False, "error": snapshot.get("error")})
    github_output("status", snapshot["status"])
    return 0 if snapshot["status"] == "API_AIFIN_COMPLETED" else 1


def render(output_dir: Path, phase: str, artifact_url: str = "") -> int:
    status_doc = load_json(output_dir / "ticket-status.json") if (output_dir / "ticket-status.json").exists() else {}
    if phase == "accepted":
        print("\n".join(["## API_AIFIN_ACCEPTED", "", f"- Task ID: `{status_doc.get('task_id', 'unknown')}`", f"- Operation: `{status_doc.get('operation', 'unknown')}`", "- Secret values exposed: `false`"])); return 0
    if phase == "rejected":
        error = status_doc.get("error") or {}; print("\n".join(["## API_AIFIN_REJECTED", "", f"- Error code: `{error.get('code', 'TICKET_INVALID')}`", f"- Message: {error.get('message', 'invalid ticket')}"])); return 0
    snapshot_path = output_dir / "aifin-snapshot.json"; snapshot = load_json(snapshot_path) if snapshot_path.exists() else {"status": "API_AIFIN_FAILED"}
    lines = [f"## {snapshot.get('status', 'API_AIFIN_FAILED')}", "", f"- Task ID: `{snapshot.get('task_id', 'unknown')}`", f"- Operation: `{snapshot.get('operation', 'unknown')}`", f"- Upstream called: `{str(bool(snapshot.get('upstream_called'))).lower()}`", "- Secret values exposed: `false`", f"- Artifact: {artifact_url or 'unavailable'}"]
    if snapshot.get("server_type"): lines.append(f"- Server type: `{snapshot['server_type']}`")
    if snapshot.get("tool_name"): lines.append(f"- Tool: `{snapshot['tool_name']}`")
    if snapshot.get("error"): lines.extend([f"- Error code: `{snapshot['error'].get('code', 'UNKNOWN')}`", f"- Error: {snapshot['error'].get('message', '')}"])
    print("\n".join(lines)); return 0


def main() -> int:
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare"); p.add_argument("--event-path", required=True); p.add_argument("--output-dir", required=True)
    p = sub.add_parser("execute"); p.add_argument("--ticket", required=True); p.add_argument("--output-dir", required=True)
    p = sub.add_parser("render"); p.add_argument("--output-dir", required=True); p.add_argument("--phase", required=True, choices=["accepted", "rejected", "completed"]); p.add_argument("--artifact-url", default="")
    args = parser.parse_args()
    if args.command == "prepare": return prepare(Path(args.event_path), Path(args.output_dir))
    if args.command == "execute": return execute(Path(args.ticket), Path(args.output_dir))
    return render(Path(args.output_dir), args.phase, args.artifact_url)


if __name__ == "__main__":
    raise SystemExit(main())
