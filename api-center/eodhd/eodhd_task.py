#!/usr/bin/env python3
"""Bounded read-only EODHD REST API execution control plane."""
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
ORIGIN = "https://eodhd.com"
TOKEN_ENV = "EODHD_API_TOKEN"
ALLOWED_SCREENER_FIELDS = {
    "code", "name", "exchange", "sector", "industry", "market_capitalization",
    "earnings_share", "dividend_yield", "adjusted_close", "refund_1d_p", "refund_5d_p",
    "avgvol_1d", "avgvol_200d",
}
ALLOWED_SCREENER_OPERATORS = {"=", "!=", ">", "<", ">=", "<=", "match", "not_match"}


class EodhdError(RuntimeError):
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
    raise ValueError(f"unsupported EODHD operation: {operation}")


def validate_screener(parameters: Mapping[str, Any]) -> None:
    raw = parameters.get("filters_json")
    if raw in (None, ""):
        return
    try:
        value = json.loads(str(raw))
    except json.JSONDecodeError as exc:
        raise ValueError("parameters.filters_json must contain valid JSON") from exc
    if not isinstance(value, list) or len(value) > 20:
        raise ValueError("parameters.filters_json must be a list with at most 20 filters")
    for item in value:
        if not isinstance(item, list) or len(item) != 3:
            raise ValueError("each screener filter must be [field, operator, value]")
        field, operator, _ = item
        if str(field) not in ALLOWED_SCREENER_FIELDS:
            raise ValueError(f"unsupported screener field: {field}")
        if str(operator) not in ALLOWED_SCREENER_OPERATORS:
            raise ValueError(f"unsupported screener operator: {operator}")


def validate_ticket(ticket: Mapping[str, Any]) -> None:
    errors = sorted(Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(ticket), key=lambda item: list(item.absolute_path))
    if errors:
        raise ValueError("; ".join(
            f"{'.'.join(str(x) for x in item.absolute_path) or '$'}: {item.message}"
            for item in errors[:20]
        ))
    operation = str(ticket["operation"])
    schema = operation_catalog(operation)["parameter_schema"]
    parameter_errors = sorted(Draft202012Validator(schema).iter_errors(ticket.get("parameters") or {}), key=lambda item: list(item.absolute_path))
    if parameter_errors:
        raise ValueError("; ".join(
            f"parameters.{'.'.join(str(x) for x in item.absolute_path)}: {item.message}"
            for item in parameter_errors[:20]
        ))
    if operation == "screener":
        validate_screener(ticket.get("parameters") or {})


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
        if not title.startswith("[api-eodhd]"):
            raise ValueError("issue title must start with [api-eodhd]")
        ticket = parsed
        accepted = True
        write_json(output_dir / "ticket.json", ticket)
    except (json.JSONDecodeError, ValueError) as exc:
        reason = str(exc)
    status = {
        "schema_version": "eodhd-ticket-status-v1",
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
        raise EodhdError("EODHD_TOKEN_MISSING", f"missing repository Secret {TOKEN_ENV}")
    return value


def scrub(value: str, secret: str) -> str:
    return value.replace(secret, "[REDACTED]") if secret else value


def encode_query_value(value: Any) -> str:
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)


def build_request(operation: str, parameters: Mapping[str, Any], secret: str) -> tuple[urllib.request.Request, dict[str, Any]]:
    row = operation_catalog(operation)
    execution = row["execution"]
    path = str(execution["path_template"])
    clean = dict(parameters)
    for name in execution.get("path_parameters") or []:
        value = clean.pop(name)
        path = path.replace("{" + name + "}", urllib.parse.quote(str(value), safe="._-"))
    query_map = dict(execution.get("query_parameter_map") or {})
    query: dict[str, str] = {}
    for name, value in clean.items():
        if value in (None, ""):
            continue
        target = str(query_map.get(name) or name)
        if operation == "screener" and name == "filters_json":
            parsed = json.loads(str(value))
            value = json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
        query[target] = encode_query_value(value)
    for name, value in dict(execution.get("force_query") or {}).items():
        query[str(name)] = str(value)
    query["api_token"] = secret
    url = ORIGIN + path + "?" + urllib.parse.urlencode(query, doseq=False, safe="[],")
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "gpts-evidence-data-center-eodhd/1"}, method="GET")
    metadata = {
        "request_origin": "eodhd.com",
        "request_path": path,
        "http_method": "GET",
        "credential_mode": "api_token_query_backend_only",
        "credential_environment_variable": TOKEN_ENV,
        "secret_value_exposed": False,
    }
    return request, metadata


def _read_once(request: urllib.request.Request, *, timeout: int, max_bytes: int, opener: Callable[..., Any]) -> tuple[int, bytes, str]:
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
        raise EodhdError("EODHD_RESPONSE_TOO_LARGE", "upstream response exceeded max_response_bytes")
    return status, raw, content_type


def row_count(payload: Any) -> int:
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, Mapping):
        for key in ("data", "results", "items"):
            nested = payload.get(key)
            if isinstance(nested, list):
                return len(nested)
        return len(payload)
    return 1


def query_eodhd(
    operation: str,
    parameters: Mapping[str, Any],
    *,
    timeout: int,
    max_bytes: int,
    max_rows: int,
    opener: Callable[..., Any] = urllib.request.urlopen,
    sleeper: Callable[[float], None] = time.sleep,
) -> tuple[Any, dict[str, Any]]:
    secret = token()
    request, metadata = build_request(operation, parameters, secret)
    attempts = 0
    while attempts < 2:
        attempts += 1
        try:
            status, raw, content_type = _read_once(request, timeout=timeout, max_bytes=max_bytes, opener=opener)
        except urllib.error.URLError as exc:
            if attempts < 2:
                sleeper(1.0)
                continue
            raise EodhdError("EODHD_CONNECTION_FAILED", f"upstream connection failed: {type(exc.reason).__name__}", retryable=True) from exc
        if status == 429 or 500 <= status <= 599:
            if attempts < 2:
                sleeper(1.0)
                continue
            raise EodhdError("EODHD_HTTP_TRANSIENT", f"upstream HTTP {status}", retryable=True)
        if status in {401, 403}:
            raise EodhdError("EODHD_AUTH_FAILED", f"upstream HTTP {status}")
        if not 200 <= status < 300:
            detail = scrub(raw[:1000].decode("utf-8", errors="replace"), secret)
            raise EodhdError("EODHD_HTTP_ERROR", f"upstream HTTP {status}: {detail}")
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else None
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise EodhdError("EODHD_INVALID_JSON", "upstream returned invalid JSON") from exc
        if isinstance(payload, Mapping):
            error_message = payload.get("error") or payload.get("message")
            code = payload.get("code")
            if error_message and (code is not None or len(payload) <= 3):
                raise EodhdError("EODHD_BUSINESS_ERROR", scrub(str(error_message), secret))
        count = row_count(payload)
        if count > max_rows:
            raise EodhdError("EODHD_RESULT_TOO_MANY_ROWS", f"upstream result has {count} rows; max_rows is {max_rows}")
        metadata.update({
            "http_status": status,
            "content_type": content_type,
            "upstream_called": True,
            "transport_attempts": attempts,
            "row_count": count,
            "response_bytes": len(raw),
        })
        return payload, metadata
    raise EodhdError("EODHD_CONNECTION_FAILED", "upstream connection failed", retryable=True)


def write_manifest(output_dir: Path, snapshot_sha: str | None = None) -> None:
    files = sorted(path.name for path in output_dir.iterdir() if path.is_file() and path.name != "artifact-manifest.json")
    write_json(output_dir / "artifact-manifest.json", {
        "schema_version": "eodhd-artifact-manifest-v1",
        "files": files,
        "snapshot_sha256": snapshot_sha,
        "secret_values_included": False,
        "model_calls": 0,
    })


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket)
    operation = str(ticket["operation"])
    started_at = utc_now()
    try:
        if operation == "catalog-capabilities":
            result = load_json(CATALOG_PATH)
            metadata = {"upstream_called": False, "credential_mode": "none", "secret_value_exposed": False, "operation_count": len(provider_catalog()["operations"]), "row_count": len(provider_catalog()["operations"])}
        else:
            acceptance = ticket["acceptance"]
            result, metadata = query_eodhd(
                operation,
                ticket.get("parameters") or {},
                timeout=int(acceptance["timeout_seconds"]),
                max_bytes=int(acceptance["max_response_bytes"]),
                max_rows=int(acceptance["max_rows"]),
            )
        snapshot = {
            "schema_version": "eodhd-api-snapshot-v1",
            "status": "API_EODHD_COMPLETED",
            "task_id": ticket["task_id"],
            "provider": "eodhd",
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
        write_json(output_dir / "eodhd-snapshot.json", snapshot)
        write_json(output_dir / "eodhd-diagnostics.json", {"schema_version": "eodhd-diagnostics-v1", "status": snapshot["status"], "failure": None, "secret_values_exposed": False, "model_calls": 0})
        (output_dir / "eodhd-summary.md").write_text(
            "\n".join(["# API_EODHD_COMPLETED", "", f"- Task ID: `{snapshot['task_id']}`", f"- Operation: `{operation}`", f"- Rows: `{metadata.get('row_count', 0)}`", f"- Snapshot SHA-256: `{snapshot['snapshot_sha256']}`", "- Secret values exposed: `false`", "- Model calls: `0`", ""]),
            encoding="utf-8",
        )
        write_manifest(output_dir, snapshot["snapshot_sha256"])
        write_output("status", snapshot["status"])
        write_output("snapshot_sha256", snapshot["snapshot_sha256"])
        return 0
    except EodhdError as exc:
        failure = {
            "schema_version": "eodhd-diagnostics-v1",
            "status": "API_EODHD_FAILED",
            "task_id": ticket.get("task_id"),
            "provider": "eodhd",
            "operation": operation,
            "started_at": started_at,
            "failed_at": utc_now(),
            "error": {"code": exc.code, "message": str(exc)[:4000], "retryable": exc.retryable},
            "secret_values_exposed": False,
            "model_calls": 0,
        }
        failure["diagnostics_sha256"] = canonical_sha(failure)
        write_json(output_dir / "eodhd-diagnostics.json", failure)
        (output_dir / "eodhd-summary.md").write_text(
            "\n".join(["# API_EODHD_FAILED", "", f"- Task ID: `{failure['task_id']}`", f"- Operation: `{operation}`", f"- Error code: `{exc.code}`", f"- Message: {str(exc)[:1000]}", "- Secret values exposed: `false`", "- Model calls: `0`", ""]),
            encoding="utf-8",
        )
        write_manifest(output_dir)
        write_output("status", failure["status"])
        write_output("error_code", exc.code)
        return 1


def render(output_dir: Path, phase: str, artifact_url: str = "") -> int:
    if phase in {"accepted", "rejected"}:
        status = load_json(output_dir / "ticket-status.json")
        heading = "API_EODHD_ACCEPTED" if status["accepted"] else "API_EODHD_REJECTED"
        print(f"## {heading}\n")
        print(f"- Task ID: `{status.get('task_id') or 'unknown'}`")
        print(f"- Operation: `{status.get('operation') or 'unknown'}`")
        print(f"- Ticket SHA-256: `{status.get('ticket_sha256') or 'unavailable'}`")
        if not status["accepted"]:
            print(f"- Reason: `{status.get('reason') or 'invalid ticket'}`")
        print("- Secret values exposed: `false`")
        print("- Model calls: `0`")
        return 0
    snapshot_path = output_dir / "eodhd-snapshot.json"
    if snapshot_path.exists():
        snapshot = load_json(snapshot_path)
        metadata = snapshot.get("metadata") or {}
        print("## API_EODHD_COMPLETED\n")
        print(f"- Task ID: `{snapshot['task_id']}`")
        print(f"- Operation: `{snapshot['operation']}`")
        print(f"- Upstream called: `{str(bool(metadata.get('upstream_called'))).lower()}`")
        print(f"- Rows: `{metadata.get('row_count', 0)}`")
        print(f"- Snapshot SHA-256: `{snapshot['snapshot_sha256']}`")
        if artifact_url:
            print(f"- Artifact: {artifact_url}")
        print("- Secret values exposed: `false`")
        print("- Model calls: `0`")
        return 0
    failure = load_json(output_dir / "eodhd-diagnostics.json")
    error = failure.get("error") or {}
    print("## API_EODHD_FAILED\n")
    print(f"- Task ID: `{failure.get('task_id') or 'unknown'}`")
    print(f"- Operation: `{failure.get('operation') or 'unknown'}`")
    print(f"- Error code: `{error.get('code') or 'EODHD_UNKNOWN'}`")
    print(f"- Message: {error.get('message') or 'unknown failure'}")
    if artifact_url:
        print(f"- Artifact: {artifact_url}")
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
