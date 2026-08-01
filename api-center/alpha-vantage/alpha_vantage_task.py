#!/usr/bin/env python3
"""Bounded read-only Alpha Vantage execution control plane."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import requests
from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE / "ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"
ENDPOINT = "https://www.alphavantage.co/query"
API_KEY_ENV = "ALPHA_VANTAGE_API_KEY"


class AlphaVantageError(RuntimeError):
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
    raise ValueError(f"unsupported Alpha Vantage operation: {operation}")


def validate_ticket(ticket: Mapping[str, Any]) -> None:
    errors = sorted(
        Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(ticket),
        key=lambda item: list(item.absolute_path),
    )
    if errors:
        raise ValueError(
            "; ".join(
                f"{'.'.join(str(x) for x in item.absolute_path) or '$'}: {item.message}"
                for item in errors[:20]
            )
        )
    operation = str(ticket["operation"])
    schema = operation_catalog(operation)["parameter_schema"]
    parameter_errors = sorted(
        Draft202012Validator(schema).iter_errors(ticket.get("parameters") or {}),
        key=lambda item: list(item.absolute_path),
    )
    if parameter_errors:
        raise ValueError(
            "; ".join(
                f"parameters.{'.'.join(str(x) for x in item.absolute_path)}: {item.message}"
                for item in parameter_errors[:20]
            )
        )


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
        if not title.startswith("[api-alpha-vantage]"):
            raise ValueError("issue title must start with [api-alpha-vantage]")
        ticket = parsed
        accepted = True
        write_json(output_dir / "ticket.json", ticket)
    except (json.JSONDecodeError, ValueError) as exc:
        reason = str(exc)
    status = {
        "schema_version": "alpha-vantage-ticket-status-v1",
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
    value = str(os.getenv(API_KEY_ENV) or "").strip()
    if not value:
        raise AlphaVantageError(
            "ALPHA_VANTAGE_KEY_MISSING",
            f"missing repository Secret {API_KEY_ENV}",
        )
    return value


def scrub_value(value: Any, secret: str) -> Any:
    if isinstance(value, str):
        return value.replace(secret, "[REDACTED]") if secret else value
    if isinstance(value, list):
        return [scrub_value(item, secret) for item in value]
    if isinstance(value, Mapping):
        return {
            str(scrub_value(key, secret)): scrub_value(item, secret)
            for key, item in value.items()
        }
    return value


def _classify_information(message: str) -> tuple[str, bool]:
    lowered = message.lower()
    if any(word in lowered for word in ("rate limit", "call frequency", "requests per day", "premium")):
        return "ALPHA_VANTAGE_RATE_OR_ENTITLEMENT", False
    return "ALPHA_VANTAGE_INFORMATION", False


def query_alpha_vantage(
    operation: str,
    parameters: Mapping[str, Any],
    *,
    timeout: int,
    max_bytes: int,
    requester: Any = requests.get,
) -> tuple[Any, dict[str, Any]]:
    operation_row = operation_catalog(operation)
    execution = operation_row["execution"]
    function = str(execution["function"])
    secret = api_key()
    query: dict[str, Any] = {"function": function}
    query.update(dict(execution.get("force_query") or {}))
    query.update(dict(parameters))
    query["apikey"] = secret

    try:
        response = requester(
            ENDPOINT,
            params=query,
            headers={
                "Accept": "application/json",
                "User-Agent": "gpts-evidence-data-center-alpha-vantage/1",
            },
            timeout=timeout,
            allow_redirects=False,
        )
    except requests.Timeout as exc:
        raise AlphaVantageError(
            "ALPHA_VANTAGE_TIMEOUT",
            "upstream request timed out",
            retryable=True,
        ) from exc
    except requests.RequestException as exc:
        raise AlphaVantageError(
            "ALPHA_VANTAGE_CONNECTION_FAILED",
            f"upstream connection failed: {type(exc).__name__}",
            retryable=True,
        ) from exc

    status = int(response.status_code)
    if 300 <= status <= 399:
        raise AlphaVantageError(
            "ALPHA_VANTAGE_REDIRECT_BLOCKED",
            f"upstream redirect blocked: HTTP {status}",
        )
    raw = bytes(response.content or b"")
    if len(raw) > max_bytes:
        raise AlphaVantageError(
            "ALPHA_VANTAGE_RESPONSE_TOO_LARGE",
            "upstream response exceeded max_response_bytes",
        )
    if not 200 <= status < 300:
        detail = raw[:1000].decode("utf-8", errors="replace")
        detail = detail.replace(secret, "[REDACTED]")
        retryable = status == 429 or 500 <= status <= 599
        raise AlphaVantageError(
            "ALPHA_VANTAGE_HTTP_ERROR",
            f"upstream HTTP {status}: {detail}",
            retryable=retryable,
        )

    try:
        payload = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AlphaVantageError(
            "ALPHA_VANTAGE_INVALID_JSON",
            "upstream returned invalid JSON",
        ) from exc
    if not isinstance(payload, (Mapping, list)):
        raise AlphaVantageError(
            "ALPHA_VANTAGE_INVALID_RESPONSE",
            "upstream JSON root must be an object or array",
        )
    if isinstance(payload, Mapping):
        if payload.get("Error Message"):
            raise AlphaVantageError(
                "ALPHA_VANTAGE_BAD_REQUEST",
                str(payload.get("Error Message"))[:2000].replace(secret, "[REDACTED]"),
            )
        information = payload.get("Information") or payload.get("Note")
        if information:
            code, retryable = _classify_information(str(information))
            raise AlphaVantageError(
                code,
                str(information)[:2000].replace(secret, "[REDACTED]"),
                retryable=retryable,
            )

    clean_payload = scrub_value(payload, secret)
    content_type = str(response.headers.get("Content-Type") or "")
    metadata = {
        "http_status": status,
        "content_type": content_type,
        "request_origin": "www.alphavantage.co",
        "request_path": "/query",
        "http_method": "GET",
        "credential_mode": "apikey-query-backend-only",
        "credential_environment_variable": API_KEY_ENV,
        "secret_value_exposed": False,
        "upstream_called": True,
        "transport_attempts": 1,
        "function": function,
        "response_bytes": len(raw),
        "premium_entitlement_may_be_required": bool(
            operation_row.get("result_contract", {}).get(
                "premium_entitlement_may_be_required"
            )
        ),
    }
    return clean_payload, metadata


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
            result, metadata = query_alpha_vantage(
                operation,
                ticket.get("parameters") or {},
                timeout=int(acceptance["timeout_seconds"]),
                max_bytes=int(acceptance["max_response_bytes"]),
            )
        snapshot = {
            "schema_version": "alpha-vantage-api-snapshot-v1",
            "status": "API_ALPHA_VANTAGE_COMPLETED",
            "task_id": ticket["task_id"],
            "provider": "alpha-vantage",
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
        write_json(output_dir / "alpha-vantage-snapshot.json", snapshot)
        write_output("status", snapshot["status"])
        write_output("snapshot_sha256", snapshot["snapshot_sha256"])
        return 0
    except AlphaVantageError as exc:
        failure = {
            "schema_version": "alpha-vantage-diagnostics-v1",
            "status": "API_ALPHA_VANTAGE_FAILED",
            "task_id": ticket.get("task_id"),
            "provider": "alpha-vantage",
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
        write_json(output_dir / "alpha-vantage-diagnostics.json", failure)
        write_output("status", failure["status"])
        write_output("error_code", exc.code)
        return 1


def render(output_dir: Path, phase: str, artifact_url: str = "") -> int:
    if phase in {"accepted", "rejected"}:
        status = load_json(output_dir / "ticket-status.json")
        heading = (
            "API_ALPHA_VANTAGE_ACCEPTED"
            if status["accepted"]
            else "API_ALPHA_VANTAGE_REJECTED"
        )
        print(f"## {heading}\n")
        print(f"- Task ID: `{status.get('task_id') or 'unknown'}`")
        print(f"- Operation: `{status.get('operation') or 'unknown'}`")
        print(f"- Ticket SHA-256: `{status.get('ticket_sha256') or 'unavailable'}`")
        if not status["accepted"]:
            print(f"- Reason: `{status.get('reason') or 'invalid ticket'}`")
        print("- Secret values exposed: `false`")
        print("- Model calls: `0`")
        return 0

    snapshot_path = output_dir / "alpha-vantage-snapshot.json"
    if snapshot_path.exists():
        snapshot = load_json(snapshot_path)
        metadata = snapshot.get("metadata") or {}
        print("## API_ALPHA_VANTAGE_COMPLETED\n")
        print(f"- Task ID: `{snapshot['task_id']}`")
        print(f"- Operation: `{snapshot['operation']}`")
        print(f"- Function: `{metadata.get('function') or 'local-catalog'}`")
        print(
            f"- Upstream called: `{str(bool(metadata.get('upstream_called'))).lower()}`"
        )
        print(f"- Response bytes: `{metadata.get('response_bytes', 0)}`")
        print(f"- Snapshot SHA-256: `{snapshot['snapshot_sha256']}`")
        if artifact_url:
            print(f"- Artifact: {artifact_url}")
        print("- Secret values exposed: `false`")
        print("- Model calls: `0`")
        return 0

    failure = load_json(output_dir / "alpha-vantage-diagnostics.json")
    print("## API_ALPHA_VANTAGE_FAILED\n")
    print(f"- Task ID: `{failure.get('task_id') or 'unknown'}`")
    print(f"- Operation: `{failure.get('operation') or 'unknown'}`")
    print(f"- Error code: `{failure['error']['code']}`")
    print(f"- Retryable: `{str(bool(failure['error']['retryable'])).lower()}`")
    print(f"- Message: `{failure['error']['message']}`")
    print(f"- Diagnostics SHA-256: `{failure['diagnostics_sha256']}`")
    if artifact_url:
        print(f"- Artifact: {artifact_url}")
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
    render_parser.add_argument("--phase", required=True)
    render_parser.add_argument("--artifact-url", default="")

    args = parser.parse_args()
    if args.command == "prepare":
        return prepare(Path(args.event_path), Path(args.output_dir))
    if args.command == "execute":
        return execute(Path(args.ticket), Path(args.output_dir))
    return render(Path(args.output_dir), args.phase, args.artifact_url)


if __name__ == "__main__":
    raise SystemExit(main())
