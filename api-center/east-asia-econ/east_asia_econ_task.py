#!/usr/bin/env python3
"""Managed read-only East Asia Econ Data API execution for API-center tickets."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
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
API_KEY_ENV = "EAST_ASIA_ECON_API_KEY"
BASE_URL = "https://data-api.eastasiaecon.com"
DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
PUBLIC_OPERATIONS = {"search-series", "series-info", "database-stats"}
AUTHENTICATED_OPERATIONS = {"series-data", "usage"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def bytes_sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def write_output(name: str, value: Any) -> None:
    target = os.getenv("GITHUB_OUTPUT")
    if not target:
        return
    text = str(value).replace("\n", " ").replace("\r", " ")
    with open(target, "a", encoding="utf-8") as handle:
        handle.write(f"{name}={text}\n")


def provider_catalog() -> dict[str, Any]:
    catalog = load_json(CATALOG_PATH)
    if not isinstance(catalog, Mapping):
        raise ValueError("provider catalog must be an object")
    return dict(catalog)


def operation_map() -> dict[str, Mapping[str, Any]]:
    providers = provider_catalog().get("providers")
    provider = providers[0] if isinstance(providers, list) and providers else {}
    operations = provider.get("operations", []) if isinstance(provider, Mapping) else []
    return {str(row["operation_id"]): row for row in operations if isinstance(row, Mapping)}


def validate_ticket(ticket: Mapping[str, Any]) -> None:
    validator = Draft202012Validator(load_json(SCHEMA_PATH))
    errors = sorted(validator.iter_errors(ticket), key=lambda item: list(item.absolute_path))
    if errors:
        rendered = "; ".join(
            f"{'.'.join(str(x) for x in item.absolute_path) or '$'}: {item.message}"
            for item in errors[:20]
        )
        raise ValueError(rendered)
    operation = str(ticket["operation"])
    row = operation_map().get(operation)
    if row is None:
        raise ValueError(f"unsupported East Asia Econ operation: {operation}")
    parameters = ticket.get("parameters")
    if not isinstance(parameters, Mapping):
        raise ValueError("parameters must be an object")
    allowed = {str(name) for name in row.get("parameters", [])}
    unexpected = sorted(set(parameters) - allowed)
    if unexpected:
        raise ValueError(f"non-allowlisted parameters: {unexpected}")
    operation_schema = row.get("parameter_schema")
    if isinstance(operation_schema, Mapping):
        operation_errors = sorted(
            Draft202012Validator(operation_schema).iter_errors(parameters),
            key=lambda item: list(item.absolute_path),
        )
        if operation_errors:
            rendered = "; ".join(
                f"parameters.{'.'.join(str(x) for x in item.absolute_path)}: {item.message}"
                for item in operation_errors[:20]
            )
            raise ValueError(rendered)
    start = str(parameters.get("start") or "")
    end = str(parameters.get("end") or "")
    if start and end and start > end:
        raise ValueError("parameters.start must not be after parameters.end")


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
        if not title.startswith("[api-east-asia-econ]"):
            raise ValueError("issue title must start with [api-east-asia-econ]")
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
        "schema_version": "east-asia-econ-ticket-status-v1",
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


def bounded_int(value: Any, *, default: int, minimum: int, maximum: int, name: str) -> int:
    if value in (None, ""):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if not minimum <= parsed <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return parsed


def clean_text(value: Any, *, name: str, maximum: int) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{name} is required")
    if len(text) > maximum or any(ord(char) < 0x20 for char in text):
        raise ValueError(f"{name} contains forbidden characters or is too long")
    if "http://" in text.casefold() or "https://" in text.casefold():
        raise ValueError(f"{name} must not contain a URL")
    return text


def api_key() -> str:
    value = str(os.getenv(API_KEY_ENV) or "").strip()
    if not value:
        raise RuntimeError(f"missing repository Secret {API_KEY_ENV}")
    if not value.startswith("eae_") or not 8 <= len(value) <= 512:
        raise RuntimeError(f"invalid repository Secret {API_KEY_ENV}")
    if any(ord(char) < 0x21 or ord(char) > 0x7E for char in value):
        raise RuntimeError(f"invalid repository Secret {API_KEY_ENV}: visible ASCII required")
    return value


def build_request(operation: str, parameters: Mapping[str, Any]) -> tuple[str | None, dict[str, Any], bool]:
    if operation == "catalog-capabilities":
        return None, {}, False
    if operation == "search-series":
        query: dict[str, Any] = {"q": clean_text(parameters.get("q"), name="q", maximum=200)}
        for name in ("country", "freq", "limit"):
            if parameters.get(name) not in (None, ""):
                query[name] = parameters[name]
        return "/v3/search", query, False
    if operation == "series-info":
        name = clean_text(parameters.get("series_name"), name="series_name", maximum=500)
        return f"/v3/info/{quote(name, safe='')}", {}, False
    if operation == "database-stats":
        return "/v3/stats", {}, False
    if operation == "series-data":
        name = clean_text(parameters.get("series_name"), name="series_name", maximum=500)
        query = {}
        for field in ("freq", "start", "end"):
            value = parameters.get(field)
            if value not in (None, ""):
                query[field] = value
        for field in ("start", "end"):
            if field in query and not DATE_RE.fullmatch(str(query[field])):
                raise ValueError(f"{field} must use YYYY-MM-DD")
        return f"/v3/series/{quote(name, safe='')}", query, True
    if operation == "usage":
        return "/usage", {}, True
    raise ValueError(f"unsupported East Asia Econ operation: {operation}")


def sanitize(value: Any, secret: str) -> Any:
    if isinstance(value, Mapping):
        return {str(key): sanitize(item, secret) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize(item, secret) for item in value]
    if isinstance(value, str) and secret:
        return value.replace(secret, "[REDACTED]")
    return value


def request_json(path: str, query: Mapping[str, Any], *, authenticated: bool, timeout: int, max_bytes: int) -> tuple[dict[str, Any], dict[str, Any]]:
    if not path.startswith(("/v3/search", "/v3/info/", "/v3/stats", "/v3/series/", "/usage")):
        raise ValueError("request path is not allowlisted")
    secret = api_key() if authenticated else ""
    headers = {"Accept": "application/json", "User-Agent": "gpts-east-asia-econ-api-center/1"}
    if secret:
        headers["X-API-Key"] = secret
    response = requests.get(
        BASE_URL + path,
        headers=headers,
        params=dict(query),
        timeout=timeout,
        allow_redirects=False,
    )
    raw = response.content
    if len(raw) > max_bytes:
        raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
    try:
        payload = response.json() if raw else {}
    except ValueError as exc:
        raise RuntimeError(f"East Asia Econ returned non-JSON HTTP {response.status_code}") from exc
    safe_payload = sanitize(payload, secret)
    if not response.ok:
        message = safe_payload.get("message") if isinstance(safe_payload, Mapping) else safe_payload
        if isinstance(safe_payload, Mapping) and safe_payload.get("error"):
            message = safe_payload.get("error")
        raise RuntimeError(f"East Asia Econ HTTP {response.status_code}: {message}")
    if not isinstance(safe_payload, Mapping):
        raise RuntimeError("East Asia Econ JSON root must be an object")
    metadata = {
        "http_status": response.status_code,
        "content_type": response.headers.get("Content-Type", ""),
        "request_path": path,
        "response_bytes": len(raw),
        "authentication": "X-API-Key header; value not recorded" if authenticated else "none",
        "response_sha256": bytes_sha(raw),
    }
    return dict(safe_payload), metadata


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(acceptance.get("timeout_seconds"), default=30, minimum=5, maximum=60, name="timeout_seconds")
    max_bytes = bounded_int(acceptance.get("max_response_bytes"), default=5000000, minimum=1024, maximum=20000000, name="max_response_bytes")
    started_at = utc_now()
    started = time.perf_counter()
    status = "API_EAST_ASIA_ECON_FAILED"
    failure: dict[str, Any] | None = None
    snapshot: dict[str, Any] = {}
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "api_origin": "data-api.eastasiaecon.com",
        "credential_mode": "none",
        "secret_values_exposed": False,
    }
    try:
        path, query, authenticated = build_request(operation, parameters)
        if path is None:
            snapshot = {"provider": provider_catalog()}
            status = "API_EAST_ASIA_ECON_COMPLETED"
        else:
            payload, request_metadata = request_json(path, query, authenticated=authenticated, timeout=timeout, max_bytes=max_bytes)
            metadata.update(request_metadata)
            metadata["upstream_called"] = True
            metadata["credential_mode"] = "x-api-key-header-backend-only" if authenticated else "none"
            snapshot = {"provider": "east-asia-econ", "operation": operation, "data": payload}
            status = "API_EAST_ASIA_ECON_COMPLETED"
    except Exception as exc:
        failure = {"type": type(exc).__name__, "message": str(exc)[:2000]}
    duration_ms = round((time.perf_counter() - started) * 1000)
    if snapshot:
        write_json(output_dir / "snapshot.json", snapshot)
    diagnostics = {
        "schema_version": "east-asia-econ-diagnostics-v1",
        "status": status,
        "task_id": ticket["task_id"],
        "operation": operation,
        "started_at": started_at,
        "completed_at": utc_now(),
        "duration_ms": duration_ms,
        "metadata": metadata,
        "failure": failure,
        "secret_values_exposed": False,
        "model_calls": 0,
    }
    write_json(output_dir / "diagnostics.json", diagnostics)
    files = []
    for path_item in sorted(output_dir.iterdir()):
        if path_item.is_file() and path_item.name != "manifest.json":
            raw = path_item.read_bytes()
            files.append({"name": path_item.name, "bytes": len(raw), "sha256": bytes_sha(raw)})
    manifest = {
        "schema_version": "east-asia-econ-manifest-v1",
        "status": status,
        "task_id": ticket["task_id"],
        "provider": "east-asia-econ",
        "operation": operation,
        "files": files,
        "secret_values_exposed": False,
        "model_calls": 0,
    }
    write_json(output_dir / "manifest.json", manifest)
    write_output("status", status)
    return 0 if status == "API_EAST_ASIA_ECON_COMPLETED" else 1


def render(output_dir: Path, phase: str, artifact_url: str) -> int:
    ticket_status = load_json(output_dir / "ticket-status.json") if (output_dir / "ticket-status.json").exists() else {}
    if phase == "accepted":
        print(f"East Asia Econ API ticket accepted: `{ticket_status.get('task_id', '')}` / `{ticket_status.get('operation', '')}`. Secret values remain backend-only.")
        return 0
    if phase == "rejected":
        print(f"East Asia Econ API ticket rejected: {ticket_status.get('reason') or 'invalid ticket'}")
        return 0
    diagnostics = load_json(output_dir / "diagnostics.json") if (output_dir / "diagnostics.json").exists() else {}
    manifest = load_json(output_dir / "manifest.json") if (output_dir / "manifest.json").exists() else {}
    print(f"East Asia Econ API result: `{diagnostics.get('status', 'UNKNOWN')}`")
    print(f"\n- Operation: `{diagnostics.get('operation', '')}`")
    print(f"- Duration: `{diagnostics.get('duration_ms', 0)} ms`")
    print(f"- Files: `{len(manifest.get('files') or [])}`")
    if artifact_url:
        print(f"- Artifact: {artifact_url}")
    failure = diagnostics.get("failure")
    if isinstance(failure, Mapping):
        print(f"- Failure: `{failure.get('type', '')}` — {failure.get('message', '')}")
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
