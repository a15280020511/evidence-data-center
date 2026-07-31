#!/usr/bin/env python3
"""Bounded read-only BaoStock execution control plane."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE / "ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"

FUNCTIONS = {
    "trade-dates": "query_trade_dates",
    "all-stocks": "query_all_stock",
    "stock-basic": "query_stock_basic",
    "history-k": "query_history_k_data_plus",
    "adjust-factor": "query_adjust_factor",
    "stock-industry": "query_stock_industry",
    "sz50-constituents": "query_sz50_stocks",
    "hs300-constituents": "query_hs300_stocks",
    "zz500-constituents": "query_zz500_stocks",
    "profit-data": "query_profit_data",
    "operation-data": "query_operation_data",
    "growth-data": "query_growth_data",
    "balance-data": "query_balance_data",
    "cash-flow-data": "query_cash_flow_data",
    "dupont-data": "query_dupont_data",
    "performance-express": "query_performance_express_report",
    "forecast-report": "query_forecast_report",
    "deposit-rate": "query_deposit_rate_data",
    "shibor": "query_shibor_data",
}


class BaoStockError(RuntimeError):
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
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def write_output(name: str, value: Any) -> None:
    target = os.getenv("GITHUB_OUTPUT")
    if not target:
        return
    text = str(value).replace("\n", " ").replace("\r", " ")
    with open(target, "a", encoding="utf-8") as handle:
        handle.write(f"{name}={text}\n")


def provider_catalog() -> Mapping[str, Any]:
    return load_json(CATALOG_PATH)["providers"][0]


def operation_catalog(operation: str) -> Mapping[str, Any]:
    for row in provider_catalog()["operations"]:
        if row["operation_id"] == operation:
            return row
    raise ValueError(f"unsupported BaoStock operation: {operation}")


def validate_ticket(ticket: Mapping[str, Any]) -> None:
    errors = sorted(Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(ticket), key=lambda item: list(item.absolute_path))
    if errors:
        raise ValueError("; ".join(f"{'.'.join(str(x) for x in item.absolute_path) or '$'}: {item.message}" for item in errors[:20]))
    schema = operation_catalog(str(ticket["operation"]))["parameter_schema"]
    errors = sorted(Draft202012Validator(schema).iter_errors(ticket.get("parameters") or {}), key=lambda item: list(item.absolute_path))
    if errors:
        raise ValueError("; ".join(f"parameters.{'.'.join(str(x) for x in item.absolute_path)}: {item.message}" for item in errors[:20]))


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
        if not title.startswith("[api-baostock]"):
            raise ValueError("issue title must start with [api-baostock]")
        ticket = parsed
        accepted = True
        write_json(output_dir / "ticket.json", ticket)
    except (json.JSONDecodeError, ValueError) as exc:
        reason = str(exc)
    status = {
        "schema_version": "baostock-ticket-status-v1", "accepted": accepted, "reason": reason,
        "task_id": str((ticket or {}).get("task_id") or ""), "provider": str((ticket or {}).get("provider") or ""),
        "operation": str((ticket or {}).get("operation") or ""), "ticket_sha256": canonical_sha(ticket) if ticket else None,
        "credentials_required": False, "secret_values_exposed": False, "model_calls": 0,
    }
    write_json(output_dir / "ticket-status.json", status)
    write_output("accepted", "true" if accepted else "false")
    write_output("reason", reason)
    return 0 if accepted else 1


def _client() -> Any:
    try:
        return importlib.import_module("baostock")
    except ImportError as exc:
        raise BaoStockError("BAOSTOCK_CLIENT_MISSING", "baostock package is not installed") from exc


def _assert_success(result: Any, phase: str) -> None:
    code = str(getattr(result, "error_code", ""))
    if code != "0":
        message = str(getattr(result, "error_msg", "unknown upstream error"))[:2000]
        retryable = any(token in message.lower() for token in ("timeout", "connect", "network", "socket"))
        raise BaoStockError("BAOSTOCK_UPSTREAM_ERROR", f"{phase} failed ({code}): {message}", retryable=retryable)


def _invoke(client: Any, operation: str, parameters: Mapping[str, Any]) -> Any:
    fn = getattr(client, FUNCTIONS[operation], None)
    if not callable(fn):
        raise BaoStockError("BAOSTOCK_FUNCTION_UNAVAILABLE", f"installed client has no {FUNCTIONS[operation]}")
    p = dict(parameters)
    if operation == "history-k":
        return fn(p.pop("code"), p.pop("fields"), start_date=p.pop("start_date"), end_date=p.pop("end_date"), frequency=p.pop("frequency", "d"), adjustflag=p.pop("adjustflag", "3"))
    if operation in {"profit-data", "operation-data", "growth-data", "balance-data", "cash-flow-data", "dupont-data"}:
        return fn(code=p["code"], year=int(p["year"]), quarter=int(p["quarter"]))
    return fn(**p)


def _collect(result: Any, max_rows: int, max_bytes: int) -> dict[str, Any]:
    _assert_success(result, "query")
    fields = [str(item) for item in list(getattr(result, "fields", []) or [])]
    rows: list[dict[str, Any]] = []
    truncated = False
    while result.next():
        values = list(result.get_row_data())
        if len(rows) >= max_rows:
            truncated = True
            break
        rows.append({name: values[index] if index < len(values) else None for index, name in enumerate(fields)})
        if len(json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) > max_bytes:
            raise BaoStockError("BAOSTOCK_RESPONSE_TOO_LARGE", "normalized response exceeded max_response_bytes")
    return {"fields": fields, "rows": rows, "row_count": len(rows), "truncated": truncated}


def query_baostock(operation: str, parameters: Mapping[str, Any], *, timeout: int, max_rows: int, max_bytes: int) -> tuple[dict[str, Any], dict[str, Any]]:
    client = _client()
    previous_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(float(timeout))
    logged_in = False
    try:
        login = client.login()
        _assert_success(login, "login")
        logged_in = True
        result = _invoke(client, operation, parameters)
        data = _collect(result, max_rows=max_rows, max_bytes=max_bytes)
        metadata = {
            "upstream_called": True, "client_package": "baostock", "credential_mode": "none",
            "credentials_required": False, "secret_value_exposed": False, "query_function": FUNCTIONS[operation],
            "row_count": data["row_count"], "truncated": data["truncated"], "transport_timeout_seconds": timeout,
        }
        return data, metadata
    except (OSError, TimeoutError) as exc:
        raise BaoStockError("BAOSTOCK_CONNECTION_FAILED", f"upstream connection failed: {type(exc).__name__}", retryable=True) from exc
    finally:
        if logged_in:
            try:
                client.logout()
            except Exception:
                pass
        socket.setdefaulttimeout(previous_timeout)


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket)
    operation = str(ticket["operation"])
    started_at = utc_now()
    try:
        if operation == "catalog-capabilities":
            result = load_json(CATALOG_PATH)
            metadata = {"upstream_called": False, "credential_mode": "none", "credentials_required": False, "secret_value_exposed": False, "operation_count": len(provider_catalog()["operations"])}
        else:
            acceptance = ticket["acceptance"]
            result, metadata = query_baostock(operation, ticket.get("parameters") or {}, timeout=int(acceptance["timeout_seconds"]), max_rows=int(acceptance["max_rows"]), max_bytes=int(acceptance["max_response_bytes"]))
        snapshot = {
            "schema_version": "baostock-api-snapshot-v1", "status": "API_BAOSTOCK_COMPLETED",
            "task_id": ticket["task_id"], "provider": "baostock", "operation": operation,
            "started_at": started_at, "completed_at": utc_now(), "ticket_sha256": canonical_sha(ticket),
            "metadata": metadata, "result": result, "credentials_required": False,
            "secret_values_exposed": False, "model_calls": 0,
        }
        snapshot["snapshot_sha256"] = canonical_sha(snapshot)
        write_json(output_dir / "baostock-snapshot.json", snapshot)
        write_json(output_dir / "artifact-manifest.json", {"schema_version": "baostock-artifact-manifest-v1", "files": ["ticket.json", "ticket-status.json", "baostock-snapshot.json"], "snapshot_sha256": snapshot["snapshot_sha256"], "secret_values_included": False})
        write_output("status", snapshot["status"])
        write_output("snapshot_sha256", snapshot["snapshot_sha256"])
        return 0
    except BaoStockError as exc:
        failure = {
            "schema_version": "baostock-diagnostics-v1", "status": "API_BAOSTOCK_FAILED",
            "task_id": ticket.get("task_id"), "provider": "baostock", "operation": operation,
            "started_at": started_at, "failed_at": utc_now(),
            "error": {"code": exc.code, "message": str(exc)[:4000], "retryable": exc.retryable},
            "credentials_required": False, "secret_values_exposed": False, "model_calls": 0,
        }
        failure["diagnostics_sha256"] = canonical_sha(failure)
        write_json(output_dir / "baostock-diagnostics.json", failure)
        write_json(output_dir / "artifact-manifest.json", {"schema_version": "baostock-artifact-manifest-v1", "files": ["ticket.json", "ticket-status.json", "baostock-diagnostics.json"], "diagnostics_sha256": failure["diagnostics_sha256"], "secret_values_included": False})
        write_output("status", failure["status"])
        write_output("error_code", exc.code)
        return 1


def render(output_dir: Path, phase: str, artifact_url: str = "") -> int:
    if phase in {"accepted", "rejected"}:
        status = load_json(output_dir / "ticket-status.json")
        heading = "API_BAOSTOCK_ACCEPTED" if status["accepted"] else "API_BAOSTOCK_REJECTED"
        print(f"## {heading}\n")
        print(f"- Task ID: `{status.get('task_id') or 'unknown'}`")
        print(f"- Operation: `{status.get('operation') or 'unknown'}`")
        print(f"- Ticket SHA-256: `{status.get('ticket_sha256') or 'unavailable'}`")
        if not status["accepted"]:
            print(f"- Reason: `{status.get('reason') or 'invalid ticket'}`")
        print("- Credentials required: `false`")
        print("- Secret values exposed: `false`")
        print("- Model calls: `0`")
        return 0
    snapshot = output_dir / "baostock-snapshot.json"
    if snapshot.exists():
        data = load_json(snapshot)
        metadata = data.get("metadata") or {}
        print("## API_BAOSTOCK_COMPLETED\n")
        print(f"- Task ID: `{data['task_id']}`")
        print(f"- Operation: `{data['operation']}`")
        print(f"- Upstream called: `{str(bool(metadata.get('upstream_called'))).lower()}`")
        print(f"- Query function: `{metadata.get('query_function') or 'local-catalog'}`")
        print(f"- Rows: `{metadata.get('row_count', 0)}`")
        print(f"- Snapshot SHA-256: `{data['snapshot_sha256']}`")
    else:
        data = load_json(output_dir / "baostock-diagnostics.json")
        print("## API_BAOSTOCK_FAILED\n")
        print(f"- Task ID: `{data.get('task_id') or 'unknown'}`")
        print(f"- Operation: `{data.get('operation') or 'unknown'}`")
        print(f"- Error code: `{data['error']['code']}`")
        print(f"- Message: `{data['error']['message']}`")
        print(f"- Retryable: `{str(bool(data['error']['retryable'])).lower()}`")
        print(f"- Diagnostics SHA-256: `{data['diagnostics_sha256']}`")
    print(f"- Artifact: {artifact_url or 'unavailable'}")
    print("- Credentials required: `false`")
    print("- Secret values exposed: `false`")
    print("- Model calls: `0`")
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
    args = parser.parse_args()
    if args.command == "prepare":
        return prepare(Path(args.event_path), Path(args.output_dir))
    if args.command == "execute":
        return execute(Path(args.ticket), Path(args.output_dir))
    return render(Path(args.output_dir), args.phase, args.artifact_url)


if __name__ == "__main__":
    raise SystemExit(main())
