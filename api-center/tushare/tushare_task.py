#!/usr/bin/env python3
"""Bounded read-only Tushare Pro execution control plane."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE / "ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"
ENDPOINT = "https://api.tushare.pro"
TOKEN_ENV = "TUSHARE_API_TOKEN"
OPERATION_API_NAMES = {
    "trade-calendar": "trade_cal",
    "stock-basic": "stock_basic",
    "daily-quotes": "daily",
    "weekly-quotes": "weekly",
    "monthly-quotes": "monthly",
    "adjust-factor": "adj_factor",
    "daily-basic": "daily_basic",
    "money-flow": "moneyflow",
    "margin-summary": "margin",
    "top-list": "top_list",
    "income-statement": "income",
    "balance-sheet": "balancesheet",
    "cash-flow-statement": "cashflow",
    "financial-indicator": "fina_indicator",
    "index-basic": "index_basic",
    "index-daily": "index_daily",
    "fund-basic": "fund_basic",
    "fund-nav": "fund_nav",
    "hk-hold": "hk_hold",
}


class TushareError(RuntimeError):
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


def provider_catalog() -> Mapping[str, Any]:
    catalog = load_json(CATALOG_PATH)
    return catalog["providers"][0]


def operation_catalog(operation: str) -> Mapping[str, Any]:
    for row in provider_catalog()["operations"]:
        if row["operation_id"] == operation:
            return row
    raise ValueError(f"unsupported Tushare operation: {operation}")


def validate_ticket(ticket: Mapping[str, Any]) -> None:
    errors = sorted(
        Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(ticket),
        key=lambda item: list(item.absolute_path),
    )
    if errors:
        raise ValueError("; ".join(
            f"{'.'.join(str(x) for x in item.absolute_path) or '$'}: {item.message}"
            for item in errors[:20]
        ))
    operation = str(ticket["operation"])
    schema = operation_catalog(operation)["parameter_schema"]
    parameter_errors = sorted(
        Draft202012Validator(schema).iter_errors(ticket.get("parameters") or {}),
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
        if not title.startswith("[api-tushare]"):
            raise ValueError("issue title must start with [api-tushare]")
        ticket = parsed
        accepted = True
        write_json(output_dir / "ticket.json", ticket)
    except (json.JSONDecodeError, ValueError) as exc:
        reason = str(exc)
    status = {
        "schema_version": "tushare-ticket-status-v1",
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


def token() -> str:
    value = str(os.getenv(TOKEN_ENV) or "").strip()
    if not value:
        raise TushareError("TUSHARE_TOKEN_MISSING", f"missing repository Secret {TOKEN_ENV}")
    return value


def scrub_text(value: str, secret: str) -> str:
    return value.replace(secret, "[REDACTED]") if secret else value


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
        raise TushareError("TUSHARE_RESPONSE_TOO_LARGE", "upstream response exceeded max_response_bytes")
    return status, raw, content_type


def query_tushare(
    operation: str,
    parameters: Mapping[str, Any],
    *,
    timeout: int,
    max_bytes: int,
    opener: Callable[..., Any] = urllib.request.urlopen,
    sleeper: Callable[[float], None] = time.sleep,
) -> tuple[dict[str, Any], dict[str, Any]]:
    api_name = OPERATION_API_NAMES[operation]
    secret = token()
    clean_parameters = dict(parameters)
    fields = str(clean_parameters.pop("fields", "") or "")
    body = json.dumps(
        {"api_name": api_name, "token": secret, "params": clean_parameters, "fields": fields},
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "gpts-evidence-data-center-tushare/1",
        },
        method="POST",
    )
    attempts = 0
    last_connection_error: Exception | None = None
    while attempts < 2:
        attempts += 1
        try:
            status, raw, content_type = _read_once(
                request, timeout=timeout, max_bytes=max_bytes, opener=opener
            )
        except urllib.error.URLError as exc:
            last_connection_error = exc
            if attempts < 2:
                sleeper(1.0)
                continue
            raise TushareError(
                "TUSHARE_CONNECTION_FAILED",
                f"upstream connection failed: {type(exc.reason).__name__}",
                retryable=True,
            ) from exc
        if status == 429 or 500 <= status <= 599:
            if attempts < 2:
                sleeper(1.0)
                continue
            raise TushareError(
                "TUSHARE_HTTP_TRANSIENT",
                f"upstream HTTP {status}",
                retryable=True,
            )
        if not 200 <= status < 300:
            detail = scrub_text(raw[:1000].decode("utf-8", errors="replace"), secret)
            raise TushareError("TUSHARE_HTTP_ERROR", f"upstream HTTP {status}: {detail}")
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TushareError("TUSHARE_INVALID_JSON", "upstream returned invalid JSON") from exc
        if not isinstance(payload, Mapping):
            raise TushareError("TUSHARE_INVALID_RESPONSE", "upstream JSON root must be an object")
        try:
            business_code = int(payload.get("code", -1))
        except (TypeError, ValueError):
            business_code = -1
        if business_code != 0:
            message = scrub_text(str(payload.get("msg") or "Tushare request failed"), secret)
            error_code = "TUSHARE_PERMISSION_DENIED" if business_code == 2002 else "TUSHARE_BUSINESS_ERROR"
            raise TushareError(error_code, f"Tushare code {business_code}: {message}")
        data = payload.get("data")
        if not isinstance(data, Mapping):
            raise TushareError("TUSHARE_INVALID_RESPONSE", "successful response has no data object")
        columns = data.get("fields")
        items = data.get("items")
        if not isinstance(columns, list) or not isinstance(items, list):
            raise TushareError("TUSHARE_INVALID_RESPONSE", "data.fields or data.items is invalid")
        normalized_rows: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, list):
                raise TushareError("TUSHARE_INVALID_RESPONSE", "data item must be an array")
            normalized_rows.append({str(name): value for name, value in zip(columns, item)})
        result = {
            "api_name": api_name,
            "fields": [str(item) for item in columns],
            "items": items,
            "rows": normalized_rows,
            "row_count": len(items),
        }
        parsed = urllib.parse.urlsplit(ENDPOINT)
        metadata = {
            "http_status": status,
            "business_code": business_code,
            "content_type": content_type,
            "request_origin": parsed.netloc,
            "request_path": parsed.path or "/",
            "http_method": "POST",
            "credential_mode": "json-token",
            "credential_environment_variable": TOKEN_ENV,
            "secret_value_exposed": False,
            "upstream_called": True,
            "transport_attempts": attempts,
            "api_name": api_name,
            "row_count": len(items),
        }
        return result, metadata
    raise TushareError(
        "TUSHARE_CONNECTION_FAILED",
        f"upstream connection failed: {type(last_connection_error).__name__}",
        retryable=True,
    )


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket)
    operation = str(ticket["operation"])
    started_at = utc_now()
    try:
        if operation == "catalog-capabilities":
            result = load_json(CATALOG_PATH)
            metadata = {
                "upstream_called": False,
                "credential_mode": "none",
                "secret_value_exposed": False,
                "operation_count": len(provider_catalog()["operations"]),
            }
        else:
            acceptance = ticket["acceptance"]
            result, metadata = query_tushare(
                operation,
                ticket.get("parameters") or {},
                timeout=int(acceptance["timeout_seconds"]),
                max_bytes=int(acceptance["max_response_bytes"]),
            )
        snapshot = {
            "schema_version": "tushare-api-snapshot-v1",
            "status": "API_TUSHARE_COMPLETED",
            "task_id": ticket["task_id"],
            "provider": "tushare",
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
        write_json(output_dir / "tushare-snapshot.json", snapshot)
        write_output("status", snapshot["status"])
        write_output("snapshot_sha256", snapshot["snapshot_sha256"])
        return 0
    except TushareError as exc:
        failure = {
            "schema_version": "tushare-diagnostics-v1",
            "status": "API_TUSHARE_FAILED",
            "task_id": ticket.get("task_id"),
            "provider": "tushare",
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
        write_json(output_dir / "tushare-diagnostics.json", failure)
        write_output("status", failure["status"])
        write_output("error_code", exc.code)
        return 1


def render(output_dir: Path, phase: str, artifact_url: str = "") -> int:
    if phase in {"accepted", "rejected"}:
        status = load_json(output_dir / "ticket-status.json")
        heading = "API_TUSHARE_ACCEPTED" if status["accepted"] else "API_TUSHARE_REJECTED"
        print(f"## {heading}\n")
        print(f"- Task ID: `{status.get('task_id') or 'unknown'}`")
        print(f"- Operation: `{status.get('operation') or 'unknown'}`")
        print(f"- Ticket SHA-256: `{status.get('ticket_sha256') or 'unavailable'}`")
        if not status["accepted"]:
            print(f"- Reason: `{status.get('reason') or 'invalid ticket'}`")
        print("- Secret values exposed: `false`")
        print("- Model calls: `0`")
        return 0
    snapshot_path = output_dir / "tushare-snapshot.json"
    if snapshot_path.exists():
        snapshot = load_json(snapshot_path)
        metadata = snapshot.get("metadata") or {}
        print("## API_TUSHARE_COMPLETED\n")
        print(f"- Task ID: `{snapshot['task_id']}`")
        print(f"- Operation: `{snapshot['operation']}`")
        print(f"- API name: `{metadata.get('api_name') or 'local-catalog'}`")
        print(f"- Upstream called: `{str(bool(metadata.get('upstream_called'))).lower()}`")
        print(f"- Rows: `{metadata.get('row_count', 0)}`")
        print(f"- Snapshot SHA-256: `{snapshot['snapshot_sha256']}`")
        print(f"- Artifact: {artifact_url or 'unavailable'}")
        print("- Secret values exposed: `false`")
        print("- Model calls: `0`")
        return 0
    failure = load_json(output_dir / "tushare-diagnostics.json")
    error = failure.get("error") or {}
    print("## API_TUSHARE_FAILED\n")
    print(f"- Task ID: `{failure.get('task_id') or 'unknown'}`")
    print(f"- Operation: `{failure.get('operation') or 'unknown'}`")
    print(f"- Error code: `{error.get('code') or 'TUSHARE_UNKNOWN_ERROR'}`")
    print(f"- Message: `{error.get('message') or 'unknown failure'}`")
    print(f"- Retryable: `{str(bool(error.get('retryable'))).lower()}`")
    print(f"- Artifact: {artifact_url or 'unavailable'}")
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
