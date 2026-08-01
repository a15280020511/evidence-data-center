#!/usr/bin/env python3
"""Bounded read-only QWeather execution control plane."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import quote

import requests
from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE / "ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"
API_HOST = "ka6r72kcc3.re.qweatherapi.com"
ORIGIN = f"https://{API_HOST}"
KEY_ENV = "QWEATHER_API_KEY"


class QWeatherError(RuntimeError):
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


def provider_catalog() -> Mapping[str, Any]:
    return load_json(CATALOG_PATH)["providers"][0]


def operation_catalog(operation: str) -> Mapping[str, Any]:
    for row in provider_catalog()["operations"]:
        if row["operation_id"] == operation:
            return row
    raise ValueError(f"unsupported QWeather operation: {operation}")


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
    if operation == "solar-radiation-forecast":
        params = ticket.get("parameters") or {}
        extras = {part for part in str(params.get("extra") or "").split(",") if part}
        if "poa" in extras and ("tilt" not in params or "azimuth" not in params):
            raise ValueError("parameters.tilt and parameters.azimuth are required when extra includes poa")


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
        if not title.startswith("[api-qweather]"):
            raise ValueError("issue title must start with [api-qweather]")
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
        "schema_version": "qweather-ticket-status-v1",
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


def api_key() -> str:
    value = str(os.getenv(KEY_ENV) or "").strip()
    if not value:
        raise QWeatherError("QWEATHER_API_KEY_MISSING", f"missing repository Secret {KEY_ENV}")
    return value


def encode_query_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def path_value(name: str, value: Any) -> str:
    if name in {"latitude", "longitude"}:
        return f"{float(value):.2f}"
    return quote(str(value), safe="._-")


def build_request(operation: str, parameters: Mapping[str, Any]) -> tuple[str, dict[str, str], dict[str, Any]]:
    row = operation_catalog(operation)
    execution = row["execution"]
    path = str(execution["path_template"])
    clean = dict(parameters)
    for name in execution.get("path_parameters") or []:
        value = clean.pop(name)
        path = path.replace("{" + name + "}", path_value(name, value))
    query_map = dict(execution.get("query_parameter_map") or {})
    query: dict[str, str] = {}
    for name, value in clean.items():
        if value in (None, ""):
            continue
        query[str(query_map.get(name) or name)] = encode_query_value(value)
    url = ORIGIN + path
    metadata = {
        "request_origin": API_HOST,
        "request_path": path,
        "http_method": "GET",
        "credential_mode": "x_qw_api_key_backend_only",
        "credential_environment_variable": KEY_ENV,
        "secret_value_exposed": False,
        "redirects_allowed": False,
    }
    return url, query, metadata


def row_count(payload: Any) -> int:
    if isinstance(payload, list):
        return len(payload)
    if not isinstance(payload, Mapping):
        return 1
    for key in (
        "location", "topCityList", "poi", "daily", "hourly", "minutely",
        "indexes", "days", "stations", "pollutants", "forecast",
        "weatherHourly", "radiation",
    ):
        value = payload.get(key)
        if isinstance(value, list):
            return len(value)
    return len(payload)


def query_qweather(
    operation: str,
    parameters: Mapping[str, Any],
    *,
    timeout: int,
    max_bytes: int,
    max_rows: int,
) -> tuple[Any, dict[str, Any]]:
    key = api_key()
    url, params, metadata = build_request(operation, parameters)
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "User-Agent": "gpts-evidence-data-center-qweather/1",
        "X-QW-Api-Key": key,
    }
    attempts = 0
    while attempts < 2:
        attempts += 1
        try:
            response = requests.get(
                url,
                params=params,
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
            raise QWeatherError(
                "QWEATHER_CONNECTION_FAILED",
                f"upstream connection failed: {type(exc).__name__}",
                retryable=True,
            ) from exc
        if len(raw) > max_bytes:
            raise QWeatherError("QWEATHER_RESPONSE_TOO_LARGE", "upstream response exceeded max_response_bytes")
        if response.is_redirect:
            raise QWeatherError("QWEATHER_REDIRECT_REJECTED", f"upstream attempted HTTP {response.status_code} redirect")
        if response.status_code == 429 or 500 <= response.status_code <= 599:
            if attempts < 2:
                time.sleep(1.0)
                continue
            raise QWeatherError("QWEATHER_HTTP_TRANSIENT", f"upstream HTTP {response.status_code}", retryable=True)
        if response.status_code == 401:
            raise QWeatherError("QWEATHER_API_KEY_INVALID", "upstream HTTP 401")
        if response.status_code == 403:
            raise QWeatherError("QWEATHER_PERMISSION_OR_PLAN_REQUIRED", "upstream HTTP 403")
        if not 200 <= response.status_code < 300:
            raise QWeatherError("QWEATHER_HTTP_ERROR", f"upstream HTTP {response.status_code}")
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else None
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise QWeatherError("QWEATHER_INVALID_JSON", "upstream returned invalid JSON") from exc
        if isinstance(payload, Mapping) and "code" in payload and str(payload.get("code")) != "200":
            code = str(payload.get("code") or "unknown")
            error_code = {
                "401": "QWEATHER_API_KEY_INVALID",
                "402": "QWEATHER_QUOTA_OR_BALANCE_REQUIRED",
                "403": "QWEATHER_PERMISSION_OR_PLAN_REQUIRED",
                "404": "QWEATHER_LOCATION_NOT_FOUND",
                "429": "QWEATHER_RATE_LIMITED",
            }.get(code, "QWEATHER_BUSINESS_ERROR")
            raise QWeatherError(error_code, f"QWeather response code {code}", retryable=code in {"429", "500"})
        count = row_count(payload)
        if count > max_rows:
            raise QWeatherError("QWEATHER_RESULT_TOO_MANY_ROWS", f"upstream result has {count} rows; max_rows is {max_rows}")
        metadata.update({
            "http_status": response.status_code,
            "content_type": response.headers.get("Content-Type", ""),
            "content_encoding": response.headers.get("Content-Encoding", ""),
            "upstream_called": True,
            "transport_attempts": attempts,
            "row_count": count,
            "response_bytes": len(raw),
        })
        return payload, metadata
    raise QWeatherError("QWEATHER_CONNECTION_FAILED", "upstream connection failed", retryable=True)


def write_manifest(output_dir: Path, snapshot_sha: str | None = None) -> None:
    files = sorted(
        path.name for path in output_dir.iterdir()
        if path.is_file() and path.name != "artifact-manifest.json"
    )
    write_json(output_dir / "artifact-manifest.json", {
        "schema_version": "qweather-artifact-manifest-v1",
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
            metadata = {
                "upstream_called": False,
                "credential_mode": "none",
                "secret_value_exposed": False,
                "operation_count": len(provider_catalog()["operations"]),
                "row_count": len(provider_catalog()["operations"]),
            }
        else:
            acceptance = ticket["acceptance"]
            result, metadata = query_qweather(
                operation,
                ticket.get("parameters") or {},
                timeout=int(acceptance["timeout_seconds"]),
                max_bytes=int(acceptance["max_response_bytes"]),
                max_rows=int(acceptance["max_rows"]),
            )
        snapshot = {
            "schema_version": "qweather-api-snapshot-v1",
            "status": "API_QWEATHER_COMPLETED",
            "task_id": ticket["task_id"],
            "provider": "qweather",
            "operation": operation,
            "started_at": started_at,
            "completed_at": utc_now(),
            "ticket_sha256": canonical_sha(ticket),
            "metadata": metadata,
            "result": result,
            "security": {
                "fixed_api_host": API_HOST,
                "secret_values_exposed": False,
                "api_key_header_recorded": False,
                "redirects_allowed": False,
                "write_operations_allowed": False,
            },
            "model_calls": 0,
        }
        snapshot["snapshot_sha256"] = canonical_sha(snapshot)
        write_json(output_dir / "qweather-snapshot.json", snapshot)
        write_json(output_dir / "qweather-diagnostics.json", {
            "schema_version": "qweather-diagnostics-v1",
            "status": snapshot["status"],
            "failure": None,
            "secret_values_exposed": False,
            "model_calls": 0,
        })
        (output_dir / "qweather-summary.md").write_text(
            "\n".join([
                "# API_QWEATHER_COMPLETED", "",
                f"- Task ID: `{snapshot['task_id']}`",
                f"- Operation: `{operation}`",
                f"- Upstream called: `{str(metadata.get('upstream_called', False)).lower()}`",
                f"- Rows: `{metadata.get('row_count', 0)}`",
                f"- Snapshot SHA-256: `{snapshot['snapshot_sha256']}`",
                "- Secret values exposed: `false`",
                "- Model calls: `0`", "",
            ]),
            encoding="utf-8",
        )
        write_manifest(output_dir, snapshot["snapshot_sha256"])
        write_output("status", snapshot["status"])
        write_output("snapshot_sha256", snapshot["snapshot_sha256"])
        return 0
    except QWeatherError as exc:
        failure = {
            "schema_version": "qweather-diagnostics-v1",
            "status": "API_QWEATHER_BLOCKED" if exc.code == "QWEATHER_API_KEY_MISSING" else "API_QWEATHER_FAILED",
            "task_id": ticket.get("task_id"),
            "provider": "qweather",
            "operation": operation,
            "started_at": started_at,
            "failed_at": utc_now(),
            "error": {"code": exc.code, "message": str(exc)[:4000], "retryable": exc.retryable},
            "security": {
                "fixed_api_host": API_HOST,
                "secret_values_exposed": False,
                "api_key_header_recorded": False,
            },
            "model_calls": 0,
        }
        write_json(output_dir / "qweather-diagnostics.json", failure)
        (output_dir / "qweather-summary.md").write_text(
            "\n".join([
                f"# {failure['status']}", "",
                f"- Task ID: `{ticket.get('task_id') or ''}`",
                f"- Operation: `{operation}`",
                f"- Error code: `{exc.code}`",
                f"- Message: {str(exc)[:4000]}",
                "- Secret values exposed: `false`",
                "- Model calls: `0`", "",
            ]),
            encoding="utf-8",
        )
        write_manifest(output_dir)
        write_output("status", failure["status"])
        return 1


def render(output_dir: Path, phase: str, artifact_url: str = "") -> int:
    if phase == "accepted":
        status = load_json(output_dir / "ticket-status.json")
        print("## API_QWEATHER_ACCEPTED")
        print()
        print(f"- Task ID: `{status.get('task_id') or ''}`")
        print(f"- Operation: `{status.get('operation') or ''}`")
        print(f"- Ticket SHA-256: `{status.get('ticket_sha256') or ''}`")
        print("- Secret values exposed: `false`")
        print("- Model calls: `0`")
        return 0
    if phase == "rejected":
        status = load_json(output_dir / "ticket-status.json")
        print("## API_QWEATHER_REJECTED")
        print()
        print(f"- Reason: `{status.get('reason') or 'invalid ticket'}`")
        return 0
    snapshot_path = output_dir / "qweather-snapshot.json"
    if snapshot_path.is_file():
        snapshot = load_json(snapshot_path)
        print("## API_QWEATHER_COMPLETED")
        print()
        print(f"- Task ID: `{snapshot['task_id']}`")
        print(f"- Operation: `{snapshot['operation']}`")
        print(f"- Upstream called: `{str(snapshot['metadata'].get('upstream_called', False)).lower()}`")
        print(f"- Rows: `{snapshot['metadata'].get('row_count', 0)}`")
        print(f"- Snapshot SHA-256: `{snapshot['snapshot_sha256']}`")
        print(f"- Artifact: {artifact_url or 'unavailable'}")
        print("- Secret values exposed: `false`")
        print("- Model calls: `0`")
        return 0
    failure = load_json(output_dir / "qweather-diagnostics.json")
    print(f"## {failure['status']}")
    print()
    print(f"- Task ID: `{failure.get('task_id') or ''}`")
    print(f"- Operation: `{failure.get('operation') or ''}`")
    print(f"- Error code: `{failure['error']['code']}`")
    print(f"- Message: {failure['error']['message']}")
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
