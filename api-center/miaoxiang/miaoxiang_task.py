#!/usr/bin/env python3
"""Read-only Dongfang Caifu Miaoxiang financial API execution."""
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
from typing import Any, Mapping

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE / "ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"
API_KEY_ENV = "MX_APIKEY"
BASE_URL = "https://mkapi2.dfcfs.com/finskillshub"
ENDPOINTS = {
    "financial-search": "/api/claw/news-search",
    "financial-data": "/api/claw/query",
    "stock-screen": "/api/claw/stock-screen",
}


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


def operation_map() -> dict[str, Mapping[str, Any]]:
    catalog = load_json(CATALOG_PATH)
    provider = catalog["providers"][0]
    return {
        str(row["operation_id"]): row
        for row in provider["operations"]
        if isinstance(row, Mapping)
    }


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
    operation = str(ticket["operation"])
    contract = operation_map().get(operation)
    if contract is None:
        raise ValueError(f"unsupported Miaoxiang operation: {operation}")
    parameter_schema = contract.get("parameter_schema")
    if isinstance(parameter_schema, Mapping):
        parameter_errors = sorted(
            Draft202012Validator(dict(parameter_schema)).iter_errors(
                ticket.get("parameters") or {}
            ),
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
        if not title.startswith("[api-mx]"):
            raise ValueError("issue title must start with [api-mx]")
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
        "schema_version": "miaoxiang-ticket-status-v1",
        "accepted": accepted,
        "reason": reason,
        "task_id": str((ticket or {}).get("task_id") or ""),
        "provider": "miaoxiang",
        "operation": str((ticket or {}).get("operation") or ""),
        "ticket_sha256": canonical_sha(ticket) if ticket else None,
        "secret_values_exposed": False,
        "model_calls": 0,
    }
    write_json(output_dir / "ticket-status.json", status)
    write_output("accepted", "true" if accepted else "false")
    write_output("reason", reason)
    return 0 if accepted else 1


def bounded_int(
    value: Any, *, default: int, minimum: int, maximum: int, name: str
) -> int:
    if value in (None, ""):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if not minimum <= parsed <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return parsed


def require_text(value: Any, name: str, maximum: int = 500) -> str:
    text = str(value or "").strip()
    if not text or len(text) > maximum or "\x00" in text:
        raise ValueError(f"{name} must contain 1 to {maximum} valid characters")
    return text


def build_body(operation: str, parameters: Mapping[str, Any]) -> dict[str, Any]:
    if operation == "financial-search":
        return {"query": require_text(parameters.get("query"), "query")}
    if operation == "financial-data":
        return {"toolQuery": require_text(parameters.get("query"), "query")}
    if operation == "stock-screen":
        return {
            "keyword": require_text(parameters.get("keyword"), "keyword"),
            "pageNo": bounded_int(
                parameters.get("page_no"), default=1, minimum=1, maximum=100, name="page_no"
            ),
            "pageSize": bounded_int(
                parameters.get("page_size"), default=20, minimum=1, maximum=100, name="page_size"
            ),
        }
    raise ValueError(f"unsupported Miaoxiang operation: {operation}")


def request_json(
    operation: str,
    *,
    api_key: str,
    body: Mapping[str, Any],
    timeout: int,
    max_bytes: int,
) -> tuple[Any, dict[str, Any]]:
    path = ENDPOINTS.get(operation)
    if not path:
        raise ValueError(f"operation has no allowlisted endpoint: {operation}")
    url = BASE_URL + path
    raw_body = json.dumps(dict(body), ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=raw_body,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "gpts-miaoxiang-api-center/1",
            "apikey": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = int(response.status)
            raw = response.read(max_bytes + 1)
            content_type = str(response.headers.get("Content-Type") or "")
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        raw = exc.read(max_bytes + 1)
        content_type = str(exc.headers.get("Content-Type") or "") if exc.headers else ""
    if len(raw) > max_bytes:
        raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
    try:
        payload = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Miaoxiang returned non-JSON HTTP {status}") from exc
    if not 200 <= status < 300:
        message = payload.get("message") if isinstance(payload, Mapping) else payload
        raise RuntimeError(f"Miaoxiang HTTP {status}: {message}")
    if isinstance(payload, Mapping):
        business_code = payload.get("code", payload.get("status"))
        if business_code not in (None, 0, "0", 200, "200", "success", "SUCCESS"):
            message = payload.get("message", payload.get("msg", "business request failed"))
            raise RuntimeError(f"Miaoxiang business status {business_code}: {message}")
    return payload, {
        "http_status": status,
        "content_type": content_type,
        "request_origin": urllib.parse.urlsplit(url).netloc,
        "request_path": path,
        "authentication": "apikey header; value not recorded",
    }


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket.get("acceptance") or {})
    timeout = bounded_int(
        acceptance.get("timeout_seconds"), default=30, minimum=5, maximum=60, name="timeout_seconds"
    )
    max_bytes = bounded_int(
        acceptance.get("max_response_bytes"),
        default=500_000,
        minimum=1024,
        maximum=2_000_000,
        name="max_response_bytes",
    )
    started = time.perf_counter()
    started_at = utc_now()
    status = "API_MIAOXIANG_FAILED"
    data: Any = None
    metadata: dict[str, Any] = {}
    failure: dict[str, Any] | None = None
    try:
        if operation == "catalog-capabilities":
            data = load_json(CATALOG_PATH)["providers"][0]
            metadata = {"source": "repository-catalog", "http_status": None}
        else:
            api_key = str(os.getenv(API_KEY_ENV) or "").strip()
            if not api_key:
                raise RuntimeError(f"missing repository Secret {API_KEY_ENV}")
            body = build_body(operation, parameters)
            data, metadata = request_json(
                operation,
                api_key=api_key,
                body=body,
                timeout=timeout,
                max_bytes=max_bytes,
            )
        encoded = json.dumps(data, ensure_ascii=False, allow_nan=False).encode("utf-8")
        if len(encoded) > max_bytes:
            raise RuntimeError(f"result exceeds acceptance.max_response_bytes={max_bytes}")
        status = "API_MIAOXIANG_COMPLETED"
    except RuntimeError as exc:
        text = str(exc)
        blocked = text.startswith("missing repository Secret")
        status = "API_MIAOXIANG_BLOCKED" if blocked else "API_MIAOXIANG_FAILED"
        failure = {
            "code": "MIAOXIANG_API_KEY_MISSING" if blocked else "MIAOXIANG_UPSTREAM_ERROR",
            "message": text,
            "retryable": not blocked,
        }
    except (ValueError, json.JSONDecodeError) as exc:
        failure = {
            "code": "MIAOXIANG_REQUEST_REJECTED",
            "message": str(exc),
            "retryable": False,
        }
    snapshot = {
        "schema_version": "miaoxiang-api-snapshot-v1",
        "status": status,
        "created_at": utc_now(),
        "started_at": started_at,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "task_id": str(ticket["task_id"]),
        "provider": "miaoxiang",
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
            "api_key_recorded": False,
            "arbitrary_url_allowed": False,
            "write_operations_allowed": False,
            "watchlist_mutation_allowed": False,
            "simulated_trading_allowed": False,
            "public_non_personal_data_only": True,
        },
        "model_calls": 0,
    }
    snapshot["snapshot_sha256"] = canonical_sha(snapshot)
    write_json(output_dir / "miaoxiang-snapshot.json", snapshot)
    write_json(
        output_dir / "miaoxiang-diagnostics.json",
        {
            "schema_version": "miaoxiang-api-diagnostics-v1",
            "status": status,
            "provider": "miaoxiang",
            "operation": operation,
            "failure": failure,
            "credential_secret_name": API_KEY_ENV if operation != "catalog-capabilities" else None,
            "credential_secret_value_exposed": False,
        },
    )
    summary = [
        f"# {status}",
        "",
        f"- Task ID: `{ticket['task_id']}`",
        "- Provider: `miaoxiang`",
        f"- Operation: `{operation}`",
        f"- Snapshot SHA256: `{snapshot['snapshot_sha256']}`",
        "- Model calls: `0`",
    ]
    if failure:
        summary.extend([f"- Error code: `{failure['code']}`", f"- Message: {failure['message']}"])
    (output_dir / "miaoxiang-summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    write_json(
        output_dir / "artifact-manifest.json",
        {
            "schema_version": "miaoxiang-artifact-manifest-v1",
            "files": [
                "ticket.json",
                "ticket-status.json",
                "miaoxiang-snapshot.json",
                "miaoxiang-diagnostics.json",
                "miaoxiang-summary.md",
            ],
            "snapshot_sha256": snapshot["snapshot_sha256"],
            "secret_values_included": False,
        },
    )
    write_output("status", status)
    write_output("snapshot_sha256", snapshot["snapshot_sha256"])
    return 0 if status == "API_MIAOXIANG_COMPLETED" else 1


def render(output_dir: Path, phase: str, artifact_url: str) -> int:
    if phase == "accepted":
        status = load_json(output_dir / "ticket-status.json")
        print("## API_MIAOXIANG_ACCEPTED")
        print()
        print(f"- Task ID: `{status.get('task_id') or ''}`")
        print(f"- Operation: `{status.get('operation') or ''}`")
        print(f"- Ticket SHA256: `{status.get('ticket_sha256') or ''}`")
        print("- Model calls: `0`")
        return 0
    if phase == "rejected":
        status = load_json(output_dir / "ticket-status.json")
        print("## API_MIAOXIANG_REJECTED")
        print()
        print(f"- Reason: `{status.get('reason') or 'invalid ticket'}`")
        return 0
    snapshot = load_json(output_dir / "miaoxiang-snapshot.json")
    print(f"## {snapshot['status']}")
    print()
    print(f"- Task ID: `{snapshot['task_id']}`")
    print("- Provider: `miaoxiang`")
    print(f"- Operation: `{snapshot['operation']}`")
    print(f"- Snapshot SHA256: `{snapshot['snapshot_sha256']}`")
    print(f"- Artifact: {artifact_url or 'unavailable'}")
    print("- Model calls: `0`")
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
    args = parser.parse_args()
    if args.command == "prepare":
        return prepare(Path(args.event_path), Path(args.output_dir))
    if args.command == "execute":
        return execute(Path(args.ticket), Path(args.output_dir))
    return render(Path(args.output_dir), args.phase, args.artifact_url)


if __name__ == "__main__":
    raise SystemExit(main())
