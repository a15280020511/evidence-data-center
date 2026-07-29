#!/usr/bin/env python3
"""Managed read-only Google Data Commons REST V2 execution for API-center tickets."""
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

import requests
from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE / "ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"
CHINA_PACK_PATH = HERE / "china-starter-pack.json"
API_KEY_ENV = "GOOGLE_DATA_COMMONS_API_KEY"
BASE_URL = "https://api.datacommons.org/v2"
ALLOWED_ENDPOINTS = {"/resolve", "/node", "/observation"}
DCID_RE = re.compile(r"^[A-Za-z0-9_./:-]{1,256}$")
DATE_RE = re.compile(r"^(?:LATEST|all|\d{4}(?:-\d{2}(?:-\d{2}(?:T[0-9:.+-]+Z?)?)?)?)$")
RELATION_RE = re.compile(r"^[A-Za-z0-9_./:<>{}\[\],+* -]{1,300}$")
SELECT_FIELDS = {"date", "entity", "variable", "value", "facet"}


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


def _operation_map() -> dict[str, Mapping[str, Any]]:
    catalog = load_json(CATALOG_PATH)
    return {
        str(row["operation_id"]): row
        for row in catalog.get("operations", [])
        if isinstance(row, Mapping)
    }


def validate_ticket(ticket: Mapping[str, Any]) -> None:
    schema = load_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(ticket), key=lambda item: list(item.absolute_path))
    if errors:
        rendered = "; ".join(
            f"{'.'.join(str(x) for x in item.absolute_path) or '$'}: {item.message}"
            for item in errors[:20]
        )
        raise ValueError(rendered)
    operation = str(ticket["operation"])
    operation_row = _operation_map().get(operation)
    if operation_row is None:
        raise ValueError(f"unsupported Data Commons operation: {operation}")
    allowed = {str(name) for name in operation_row.get("parameters", [])}
    unexpected = sorted(set(ticket.get("parameters", {})) - allowed)
    if unexpected:
        raise ValueError(f"non-allowlisted parameters: {unexpected}")


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
        if not title.startswith("[api-dc]"):
            raise ValueError("issue title must start with [api-dc]")
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
        "schema_version": "data-commons-ticket-status-v1",
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


def _bounded_int(value: Any, *, default: int, minimum: int, maximum: int, name: str) -> int:
    if value in (None, ""):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if not minimum <= parsed <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return parsed


def _parse_string_list(
    value: Any,
    *,
    name: str,
    maximum: int,
    required: bool = True,
    pattern: re.Pattern[str] | None = None,
) -> list[str]:
    raw = str(value or "").strip()
    if not raw:
        if required:
            raise ValueError(f"{name} is required")
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} must be a JSON array of strings") from exc
    if not isinstance(parsed, list) or (required and not parsed) or len(parsed) > maximum:
        raise ValueError(f"{name} must contain between {1 if required else 0} and {maximum} items")
    result: list[str] = []
    for item in parsed:
        text = str(item) if isinstance(item, str) else ""
        if not text or len(text) > 300 or "\n" in text or "\r" in text:
            raise ValueError(f"{name} contains an invalid string")
        if "http://" in text.casefold() or "https://" in text.casefold():
            raise ValueError(f"{name} must not contain URLs")
        if pattern and not pattern.fullmatch(text):
            raise ValueError(f"{name} contains an invalid identifier: {text}")
        result.append(text)
    return result


def _relation_expression(value: Any, *, required: bool) -> str:
    text = str(value or "").strip()
    if not text:
        if required:
            raise ValueError("property relation expression is required")
        return ""
    if not RELATION_RE.fullmatch(text):
        raise ValueError("property relation expression contains forbidden characters or is too long")
    if "http://" in text.casefold() or "https://" in text.casefold():
        raise ValueError("property relation expression must not contain URLs")
    return text


def _request_json(endpoint: str, *, api_key: str, body: Mapping[str, Any], timeout: int, max_bytes: int) -> tuple[dict[str, Any], dict[str, Any]]:
    if endpoint not in ALLOWED_ENDPOINTS:
        raise ValueError(f"endpoint is not allowlisted: {endpoint}")
    response = requests.post(
        BASE_URL + endpoint,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-API-Key": api_key,
            "User-Agent": "gpts-data-commons-api-center/1",
        },
        json=dict(body),
        timeout=timeout,
    )
    raw = response.content
    if len(raw) > max_bytes:
        raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
    try:
        payload = response.json() if raw else {}
    except ValueError as exc:
        raise RuntimeError(f"Data Commons returned non-JSON HTTP {response.status_code}") from exc
    if not response.ok:
        message = payload.get("message") if isinstance(payload, Mapping) else payload
        if isinstance(payload, Mapping) and payload.get("error"):
            message = payload.get("error")
        raise RuntimeError(f"Data Commons HTTP {response.status_code}: {message}")
    return dict(payload), {
        "http_status": response.status_code,
        "content_type": response.headers.get("Content-Type", ""),
        "request_url": BASE_URL + endpoint,
        "authentication": "X-API-Key header; value not recorded",
    }


def _build_operation(operation: str, parameters: Mapping[str, Any]) -> tuple[str | None, dict[str, Any], dict[str, Any]]:
    if operation == "catalog-capabilities":
        return None, {}, {
            "provider_catalog": load_json(CATALOG_PATH),
            "china_starter_pack": load_json(CHINA_PACK_PATH),
        }
    if operation == "resolve-place":
        nodes = _parse_string_list(parameters.get("nodes_json"), name="nodes_json", maximum=20)
        property_expression = _relation_expression(parameters.get("property"), required=False)
        body: dict[str, Any] = {"nodes": nodes, "resolver": "place"}
        if property_expression:
            body["property"] = property_expression
        return "/resolve", body, {}
    if operation == "resolve-indicator":
        nodes = _parse_string_list(parameters.get("nodes_json"), name="nodes_json", maximum=20)
        return "/resolve", {"nodes": nodes, "resolver": "indicator"}, {}
    if operation == "node-properties":
        nodes = _parse_string_list(
            parameters.get("nodes_json"),
            name="nodes_json",
            maximum=20,
            pattern=DCID_RE,
        )
        property_expression = _relation_expression(parameters.get("property"), required=True)
        return "/node", {"nodes": nodes, "property": property_expression}, {}
    if operation == "observations":
        entities = _parse_string_list(
            parameters.get("entity_dcids_json"),
            name="entity_dcids_json",
            maximum=20,
            pattern=DCID_RE,
        )
        variables = _parse_string_list(
            parameters.get("variable_dcids_json"),
            name="variable_dcids_json",
            maximum=20,
            pattern=DCID_RE,
        )
        date = str(parameters.get("date") or "LATEST")
        if not DATE_RE.fullmatch(date):
            raise ValueError("date must be LATEST, all, YYYY, YYYY-MM, YYYY-MM-DD, or an ISO date-time")
        select = _parse_string_list(
            parameters.get("select_json") or '["date","entity","variable","value","facet"]',
            name="select_json",
            maximum=5,
        )
        if len(set(select)) != len(select) or not set(select) <= SELECT_FIELDS:
            raise ValueError(f"select_json may contain only {sorted(SELECT_FIELDS)} without duplicates")
        facet_ids = _parse_string_list(
            parameters.get("facet_ids_json"),
            name="facet_ids_json",
            maximum=20,
            required=False,
            pattern=DCID_RE,
        )
        domains = _parse_string_list(
            parameters.get("domains_json"),
            name="domains_json",
            maximum=20,
            required=False,
        )
        body = {
            "date": date,
            "variable": {"dcids": variables},
            "entity": {"dcids": entities},
            "select": select,
        }
        if facet_ids or domains:
            body["filter"] = {}
            if facet_ids:
                body["filter"]["facet_ids"] = facet_ids
            if domains:
                body["filter"]["domains"] = domains
        return "/observation", body, {}
    raise ValueError(f"unsupported Data Commons operation: {operation}")


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket.get("acceptance") or {})
    timeout = _bounded_int(acceptance.get("timeout_seconds"), default=30, minimum=1, maximum=60, name="timeout_seconds")
    max_response_bytes = _bounded_int(acceptance.get("max_response_bytes"), default=500_000, minimum=1024, maximum=1_000_000, name="max_response_bytes")
    started = time.perf_counter()
    started_at = utc_now()
    status = "API_DATA_COMMONS_FAILED"
    data: Any = None
    metadata: dict[str, Any] = {}
    failure: dict[str, Any] | None = None
    try:
        endpoint, body, local_data = _build_operation(operation, parameters)
        if endpoint is None:
            data = local_data
            metadata = {"http_status": 200, "catalog_source": "repository-policy"}
        else:
            api_key = str(os.getenv(API_KEY_ENV) or "").strip()
            if not api_key:
                raise RuntimeError(f"missing repository Secret {API_KEY_ENV}")
            data, metadata = _request_json(
                endpoint,
                api_key=api_key,
                body=body,
                timeout=timeout,
                max_bytes=max_response_bytes,
            )
        encoded = json.dumps(data, ensure_ascii=False, allow_nan=False).encode("utf-8")
        if len(encoded) > max_response_bytes:
            raise RuntimeError(f"result exceeds acceptance.max_response_bytes={max_response_bytes}")
        status = "API_DATA_COMMONS_COMPLETED"
    except RuntimeError as exc:
        text = str(exc)
        blocked = text.startswith("missing repository Secret")
        status = "API_DATA_COMMONS_BLOCKED" if blocked else "API_DATA_COMMONS_FAILED"
        failure = {
            "code": "DATA_COMMONS_API_KEY_MISSING" if blocked else "DATA_COMMONS_UPSTREAM_ERROR",
            "message": text,
            "retryable": not blocked,
        }
    except (ValueError, json.JSONDecodeError) as exc:
        failure = {"code": "DATA_COMMONS_REQUEST_REJECTED", "message": str(exc), "retryable": False}
    snapshot = {
        "schema_version": "data-commons-api-snapshot-v1",
        "status": status,
        "created_at": utc_now(),
        "started_at": started_at,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "task_id": str(ticket["task_id"]),
        "provider": "data-commons",
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
            "authorization_header_recorded": False,
            "public_non_personal_data_only": True,
            "arbitrary_url_allowed": False,
            "sparql_allowed": False,
            "write_operations_allowed": False,
        },
        "model_calls": 0,
    }
    snapshot["snapshot_sha256"] = canonical_sha(snapshot)
    write_json(output_dir / "data-commons-snapshot.json", snapshot)
    diagnostics = {
        "schema_version": "data-commons-api-diagnostics-v1",
        "status": status,
        "provider": "data-commons",
        "operation": operation,
        "failure": failure,
        "credential_secret_name": API_KEY_ENV if operation != "catalog-capabilities" else None,
        "credential_secret_value_exposed": False,
    }
    write_json(output_dir / "data-commons-diagnostics.json", diagnostics)
    summary = [
        f"# {status}",
        "",
        f"- Task ID: `{ticket['task_id']}`",
        "- Provider: `data-commons`",
        f"- Operation: `{operation}`",
        f"- Snapshot SHA256: `{snapshot['snapshot_sha256']}`",
        "- Model calls: `0`",
    ]
    if failure:
        summary.extend([f"- Error code: `{failure['code']}`", f"- Message: {failure['message']}"])
    (output_dir / "data-commons-summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": "data-commons-artifact-manifest-v1",
        "files": [
            "ticket.json",
            "ticket-status.json",
            "data-commons-snapshot.json",
            "data-commons-diagnostics.json",
            "data-commons-summary.md",
        ],
        "snapshot_sha256": snapshot["snapshot_sha256"],
        "secret_values_included": False,
    }
    write_json(output_dir / "artifact-manifest.json", manifest)
    write_output("status", status)
    write_output("snapshot_sha256", snapshot["snapshot_sha256"])
    return 0 if status == "API_DATA_COMMONS_COMPLETED" else 1


def render(output_dir: Path, phase: str, artifact_url: str) -> int:
    if phase == "accepted":
        status = load_json(output_dir / "ticket-status.json")
        print("## API_DATA_COMMONS_ACCEPTED")
        print()
        print(f"- Task ID: `{status.get('task_id') or ''}`")
        print(f"- Operation: `{status.get('operation') or ''}`")
        print(f"- Ticket SHA256: `{status.get('ticket_sha256') or ''}`")
        print("- Model calls: `0`")
        return 0
    if phase == "rejected":
        status = load_json(output_dir / "ticket-status.json")
        print("## API_DATA_COMMONS_REJECTED")
        print()
        print(f"- Reason: `{status.get('reason') or 'invalid ticket'}`")
        return 0
    snapshot = load_json(output_dir / "data-commons-snapshot.json")
    print(f"## {snapshot['status']}")
    print()
    print(f"- Task ID: `{snapshot['task_id']}`")
    print("- Provider: `data-commons`")
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
