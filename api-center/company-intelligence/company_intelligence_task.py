#!/usr/bin/env python3
"""Read-only Qichacha and Tianyancha managed-provider execution."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
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
QICHACHA_CREDENTIALS_ENV = "QICHACHA_CREDENTIALS_JSON"
TIANYANCHA_TOKEN_ENV = "TIANYANCHA_API_TOKEN"

OPERATION_PROVIDER = {
    "catalog-capabilities": {"qichacha", "tianyancha"},
    "company-search": {"qichacha"},
    "company-investments": {"qichacha"},
    "company-basic": {"tianyancha"},
    "company-annual-reports": {"tianyancha"},
}

QCC_ENDPOINTS = {
    "company-search": "https://api.qichacha.com/FuzzySearch/GetList",
    "company-investments": "https://api.qichacha.com/InvestmentCheck/GetList",
}
TYC_ENDPOINTS = {
    "company-basic": "https://open.api.tianyancha.com/services/open/ic/baseinfoV2/2.0",
    "company-annual-reports": "https://open.api.tianyancha.com/services/open/ic/annualreport/2.0",
}

SENSITIVE_KEY_RE = re.compile(
    r"(?:phone|mobile|tel|email|mail|idcard|identity|passport|contact|opername|"
    r"legalperson|legal_person|personname|person_name|humanname|human_name)",
    re.IGNORECASE,
)


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


def _catalog_operations() -> dict[tuple[str, str], Mapping[str, Any]]:
    catalog = load_json(CATALOG_PATH)
    result: dict[tuple[str, str], Mapping[str, Any]] = {}
    for provider in catalog["providers"]:
        provider_id = str(provider["provider_id"])
        for operation in provider["operations"]:
            result[(provider_id, str(operation["operation_id"]))] = operation
    return result


def validate_ticket(ticket: Mapping[str, Any]) -> None:
    validator = Draft202012Validator(load_json(SCHEMA_PATH))
    errors = sorted(
        validator.iter_errors(ticket), key=lambda item: list(item.absolute_path)
    )
    if errors:
        rendered = "; ".join(
            f"{'.'.join(str(x) for x in item.absolute_path) or '$'}: {item.message}"
            for item in errors[:20]
        )
        raise ValueError(rendered)
    provider = str(ticket["provider"])
    operation = str(ticket["operation"])
    if provider not in OPERATION_PROVIDER.get(operation, set()):
        raise ValueError(f"operation {operation} is not available for provider {provider}")
    operation_contract = _catalog_operations().get((provider, operation))
    if operation_contract is None:
        raise ValueError(f"unsupported provider operation: {provider}/{operation}")
    schema = operation_contract.get("parameter_schema")
    if isinstance(schema, Mapping):
        parameter_errors = sorted(
            Draft202012Validator(dict(schema)).iter_errors(
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
        if not title.startswith("[api-company]"):
            raise ValueError("issue title must start with [api-company]")
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
        "schema_version": "company-intelligence-ticket-status-v1",
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


def _bounded_int(
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


def _require_text(value: Any, name: str, maximum: int = 200) -> str:
    text = str(value or "").strip()
    if not text or len(text) > maximum:
        raise ValueError(f"{name} must contain 1 to {maximum} characters")
    return text


def _qcc_credentials() -> tuple[str, str]:
    raw = str(os.getenv(QICHACHA_CREDENTIALS_ENV) or "").strip()
    if not raw:
        raise RuntimeError(f"missing repository Secret {QICHACHA_CREDENTIALS_ENV}")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{QICHACHA_CREDENTIALS_ENV} is not valid JSON") from exc
    if not isinstance(value, Mapping):
        raise RuntimeError(f"{QICHACHA_CREDENTIALS_ENV} must contain a JSON object")
    app_key = str(value.get("app_key") or value.get("key") or "").strip()
    secret_key = str(
        value.get("secret_key") or value.get("secretKey") or ""
    ).strip()
    if not app_key or not secret_key:
        raise RuntimeError(
            f"{QICHACHA_CREDENTIALS_ENV} must contain app_key and secret_key"
        )
    return app_key, secret_key


def _qcc_auth(
    app_key: str, secret_key: str, timestamp: int | None = None
) -> tuple[str, str]:
    timespan = str(int(time.time()) if timestamp is None else int(timestamp))
    token = hashlib.md5(
        f"{app_key}{timespan}{secret_key}".encode("utf-8")
    ).hexdigest().upper()
    return timespan, token


def _tyc_token() -> str:
    token = str(os.getenv(TIANYANCHA_TOKEN_ENV) or "").strip()
    if not token:
        raise RuntimeError(f"missing repository Secret {TIANYANCHA_TOKEN_ENV}")
    return token


def sanitize_payload(value: Any) -> Any:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for raw_key, item in value.items():
            key = str(raw_key)
            if SENSITIVE_KEY_RE.search(key):
                continue
            result[key] = sanitize_payload(item)
        return result
    if isinstance(value, list):
        return [sanitize_payload(item) for item in value]
    return value


def _http_json(
    url: str,
    *,
    headers: Mapping[str, str],
    params: Mapping[str, Any],
    timeout: int,
    max_bytes: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    query = urllib.parse.urlencode(
        {key: value for key, value in params.items() if value not in (None, "")}
    )
    request_url = f"{url}?{query}" if query else url
    request = urllib.request.Request(
        request_url,
        headers={
            "Accept": "application/json",
            "User-Agent": "gpts-company-intelligence-api-center/1",
            **dict(headers),
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = int(response.status)
            raw = response.read(max_bytes + 1)
            content_type = str(response.headers.get("Content-Type") or "")
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        raw = exc.read(max_bytes + 1)
        content_type = (
            str(exc.headers.get("Content-Type") or "") if exc.headers else ""
        )
    if len(raw) > max_bytes:
        raise RuntimeError(
            f"response exceeds acceptance.max_response_bytes={max_bytes}"
        )
    try:
        payload = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"upstream returned non-JSON HTTP {status}") from exc
    if not isinstance(payload, Mapping):
        raise RuntimeError("upstream JSON root must be an object")
    metadata = {
        "http_status": status,
        "content_type": content_type,
        "request_origin": urllib.parse.urlsplit(url).netloc,
        "request_path": urllib.parse.urlsplit(url).path,
    }
    if not 200 <= status < 300:
        raise RuntimeError(f"upstream HTTP {status}")
    return dict(payload), metadata


def _qichacha(
    operation: str,
    parameters: Mapping[str, Any],
    timeout: int,
    max_bytes: int,
) -> tuple[Any, dict[str, Any]]:
    app_key, secret_key = _qcc_credentials()
    timespan, token = _qcc_auth(app_key, secret_key)
    keyword = _require_text(parameters.get("keyword"), "keyword")
    query: dict[str, Any] = {"key": app_key, "searchKey": keyword}
    if operation == "company-search":
        query["pageIndex"] = _bounded_int(
            parameters.get("page_index"),
            default=1,
            minimum=1,
            maximum=100,
            name="page_index",
        )
    elif operation == "company-investments":
        query["pageIndex"] = _bounded_int(
            parameters.get("page_index"),
            default=1,
            minimum=1,
            maximum=100,
            name="page_index",
        )
        query["pageSize"] = _bounded_int(
            parameters.get("page_size"),
            default=10,
            minimum=1,
            maximum=20,
            name="page_size",
        )
    else:
        raise ValueError(f"unsupported Qichacha operation: {operation}")
    payload, metadata = _http_json(
        QCC_ENDPOINTS[operation],
        headers={"Token": token, "Timespan": timespan},
        params=query,
        timeout=timeout,
        max_bytes=max_bytes,
    )
    business_status = str(payload.get("Status") or "")
    metadata["business_status"] = business_status
    if business_status != "200":
        message = str(payload.get("Message") or "upstream business request failed")
        raise RuntimeError(
            f"Qichacha business status {business_status or 'unknown'}: {message}"
        )
    return sanitize_payload(payload), metadata


def _tianyancha(
    operation: str,
    parameters: Mapping[str, Any],
    timeout: int,
    max_bytes: int,
) -> tuple[Any, dict[str, Any]]:
    keyword = _require_text(parameters.get("keyword"), "keyword")
    query: dict[str, Any] = {"keyword": keyword}
    if operation == "company-annual-reports" and parameters.get("year") not in (
        None,
        "",
    ):
        query["year"] = _bounded_int(
            parameters.get("year"),
            default=2025,
            minimum=1980,
            maximum=2100,
            name="year",
        )
    if operation not in TYC_ENDPOINTS:
        raise ValueError(f"unsupported Tianyancha operation: {operation}")
    payload, metadata = _http_json(
        TYC_ENDPOINTS[operation],
        headers={"Authorization": _tyc_token()},
        params=query,
        timeout=timeout,
        max_bytes=max_bytes,
    )
    error_code = payload.get("error_code")
    metadata["business_status"] = error_code
    if error_code != 0:
        reason = str(payload.get("reason") or "upstream business request failed")
        raise RuntimeError(f"Tianyancha business status {error_code}: {reason}")
    return sanitize_payload(payload), metadata


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket)
    provider = str(ticket["provider"])
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket.get("acceptance") or {})
    timeout = _bounded_int(
        acceptance.get("timeout_seconds"),
        default=30,
        minimum=5,
        maximum=60,
        name="timeout_seconds",
    )
    max_bytes = _bounded_int(
        acceptance.get("max_response_bytes"),
        default=500_000,
        minimum=1024,
        maximum=2_000_000,
        name="max_response_bytes",
    )
    started = time.perf_counter()
    started_at = utc_now()
    status = "API_COMPANY_FAILED"
    data: Any = None
    metadata: dict[str, Any] = {}
    failure: dict[str, Any] | None = None
    credential_secret_name: str | None = None
    try:
        if operation == "catalog-capabilities":
            catalog = load_json(CATALOG_PATH)
            data = next(
                row for row in catalog["providers"] if row["provider_id"] == provider
            )
            metadata = {"source": "repository-catalog", "http_status": None}
        elif provider == "qichacha":
            credential_secret_name = QICHACHA_CREDENTIALS_ENV
            data, metadata = _qichacha(operation, parameters, timeout, max_bytes)
        elif provider == "tianyancha":
            credential_secret_name = TIANYANCHA_TOKEN_ENV
            data, metadata = _tianyancha(operation, parameters, timeout, max_bytes)
        else:
            raise ValueError(f"unsupported provider: {provider}")
        encoded = json.dumps(data, ensure_ascii=False, allow_nan=False).encode("utf-8")
        if len(encoded) > max_bytes:
            raise RuntimeError(
                f"sanitized result exceeds acceptance.max_response_bytes={max_bytes}"
            )
        status = "API_COMPANY_COMPLETED"
    except RuntimeError as exc:
        text = str(exc)
        blocked = text.startswith("missing repository Secret")
        status = "API_COMPANY_BLOCKED" if blocked else "API_COMPANY_FAILED"
        failure = {
            "code": (
                "COMPANY_CREDENTIALS_MISSING"
                if blocked
                else "COMPANY_UPSTREAM_ERROR"
            ),
            "message": text,
            "retryable": not blocked,
        }
    except (ValueError, json.JSONDecodeError, StopIteration) as exc:
        failure = {
            "code": "COMPANY_REQUEST_REJECTED",
            "message": str(exc),
            "retryable": False,
        }
    snapshot = {
        "schema_version": "company-intelligence-api-snapshot-v1",
        "status": status,
        "created_at": utc_now(),
        "started_at": started_at,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "task_id": str(ticket["task_id"]),
        "provider": provider,
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
            "authorization_headers_recorded": False,
            "credential_query_values_recorded": False,
            "arbitrary_url_allowed": False,
            "write_operations_allowed": False,
            "direct_contact_fields_removed": True,
            "public_non_personal_data_only": True,
        },
        "model_calls": 0,
    }
    snapshot["snapshot_sha256"] = canonical_sha(snapshot)
    write_json(output_dir / "company-snapshot.json", snapshot)
    write_json(
        output_dir / "company-diagnostics.json",
        {
            "schema_version": "company-intelligence-api-diagnostics-v1",
            "status": status,
            "provider": provider,
            "operation": operation,
            "failure": failure,
            "credential_secret_name": credential_secret_name,
            "credential_secret_value_exposed": False,
        },
    )
    summary = [
        f"# {status}",
        "",
        f"- Task ID: `{ticket['task_id']}`",
        f"- Provider: `{provider}`",
        f"- Operation: `{operation}`",
        f"- Snapshot SHA256: `{snapshot['snapshot_sha256']}`",
        "- Model calls: `0`",
    ]
    if failure:
        summary.extend(
            [
                f"- Error code: `{failure['code']}`",
                f"- Message: {failure['message']}",
            ]
        )
    (output_dir / "company-summary.md").write_text(
        "\n".join(summary) + "\n", encoding="utf-8"
    )
    write_json(
        output_dir / "artifact-manifest.json",
        {
            "schema_version": "company-intelligence-artifact-manifest-v1",
            "files": [
                "ticket.json",
                "ticket-status.json",
                "company-snapshot.json",
                "company-diagnostics.json",
                "company-summary.md",
            ],
            "snapshot_sha256": snapshot["snapshot_sha256"],
            "secret_values_included": False,
        },
    )
    write_output("status", status)
    write_output("snapshot_sha256", snapshot["snapshot_sha256"])
    return 0 if status == "API_COMPANY_COMPLETED" else 1


def render(output_dir: Path, phase: str, artifact_url: str) -> int:
    if phase == "accepted":
        status = load_json(output_dir / "ticket-status.json")
        print("## API_COMPANY_ACCEPTED")
        print()
        print(f"- Task ID: `{status.get('task_id') or ''}`")
        print(f"- Provider: `{status.get('provider') or ''}`")
        print(f"- Operation: `{status.get('operation') or ''}`")
        print(f"- Ticket SHA256: `{status.get('ticket_sha256') or ''}`")
        print("- Model calls: `0`")
        return 0
    if phase == "rejected":
        status = load_json(output_dir / "ticket-status.json")
        print("## API_COMPANY_REJECTED")
        print()
        print(f"- Reason: `{status.get('reason') or 'invalid ticket'}`")
        return 0
    snapshot = load_json(output_dir / "company-snapshot.json")
    print(f"## {snapshot['status']}")
    print()
    print(f"- Task ID: `{snapshot['task_id']}`")
    print(f"- Provider: `{snapshot['provider']}`")
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
    render_parser.add_argument(
        "--phase", choices=["accepted", "rejected", "completed"], required=True
    )
    render_parser.add_argument("--artifact-url", default="")
    args = parser.parse_args()
    if args.command == "prepare":
        return prepare(Path(args.event_path), Path(args.output_dir))
    if args.command == "execute":
        return execute(Path(args.ticket), Path(args.output_dir))
    return render(Path(args.output_dir), args.phase, args.artifact_url)


if __name__ == "__main__":
    raise SystemExit(main())
