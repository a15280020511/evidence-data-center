#!/usr/bin/env python3
"""Bounded, read-only Jina Reader and Exa managed-provider execution."""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import socket
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
JINA_API_KEY_ENV = "JINA_API_KEY"
EXA_API_KEY_ENV = "EXA_API_KEY"
BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "metadata.azure.internal",
    "kubernetes.default",
    "kubernetes.default.svc",
    "instance-data",
}
BLOCKED_SUFFIXES = (
    ".local",
    ".internal",
    ".localhost",
    ".svc",
    ".cluster.local",
)
OPERATION_PROVIDER = {
    "catalog-capabilities": {"jina-reader", "exa"},
    "read-url": {"jina-reader"},
    "search": {"exa"},
    "contents": {"exa"},
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
    parameter_schema = operation_contract.get("parameter_schema")
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
        if not title.startswith("[api-web]"):
            raise ValueError("issue title must start with [api-web]")
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
        "schema_version": "web-retrieval-ticket-status-v1",
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


def _required_text(value: Any, name: str, maximum: int) -> str:
    text = str(value or "").strip()
    if not text or len(text) > maximum:
        raise ValueError(f"{name} must contain 1 to {maximum} characters")
    return text


def _is_global_ip(address: str) -> bool:
    parsed = ipaddress.ip_address(address)
    return bool(parsed.is_global)


def validate_public_https_url(value: Any) -> str:
    url = _required_text(value, "url", 2048)
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme.lower() != "https":
        raise ValueError("url must use https")
    if not parsed.hostname:
        raise ValueError("url must include a hostname")
    if parsed.username or parsed.password:
        raise ValueError("url credentials are forbidden")
    if parsed.port not in (None, 443):
        raise ValueError("url may use only the default HTTPS port")
    hostname = parsed.hostname.casefold().rstrip(".")
    if hostname in BLOCKED_HOSTNAMES or hostname.endswith(BLOCKED_SUFFIXES):
        raise ValueError("url targets a blocked hostname")
    try:
        literal = ipaddress.ip_address(hostname)
    except ValueError:
        literal = None
    if literal is not None and not literal.is_global:
        raise ValueError("url targets a non-public IP address")
    try:
        records = socket.getaddrinfo(
            hostname,
            443,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
    except socket.gaierror as exc:
        raise ValueError("url hostname could not be resolved") from exc
    resolved = {
        str(record[4][0]).split("%", 1)[0]
        for record in records
        if record and len(record) >= 5 and record[4]
    }
    if not resolved:
        raise ValueError("url hostname did not resolve to an IP address")
    if any(not _is_global_ip(address) for address in resolved):
        raise ValueError("url hostname resolves to a non-public IP address")
    normalized = urllib.parse.urlunsplit(
        ("https", parsed.netloc, parsed.path or "/", parsed.query, "")
    )
    return normalized


def _read_response(
    request: urllib.request.Request, timeout: int, max_bytes: int
) -> tuple[int, bytes, str]:
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
    if not 200 <= status < 300:
        message = raw[:500].decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"upstream HTTP {status}: {message}")
    return status, raw, content_type


def _decode_payload(raw: bytes, content_type: str) -> Any:
    if not raw:
        return {}
    if "json" in content_type.casefold():
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("upstream declared JSON but returned invalid JSON") from exc
    text = raw.decode("utf-8", errors="replace")
    return {"content": text}


def _jina_read(
    parameters: Mapping[str, Any], timeout: int, max_bytes: int
) -> tuple[Any, dict[str, Any]]:
    target_url = validate_public_https_url(parameters.get("url"))
    max_tokens = _bounded_int(
        parameters.get("max_tokens"),
        default=8000,
        minimum=500,
        maximum=20000,
        name="max_tokens",
    )
    headers = {
        "Accept": "application/json",
        "X-Respond-With": "markdown",
        "X-Timeout": str(min(timeout, 120)),
        "X-Max-Tokens": str(max_tokens),
        "User-Agent": "gpts-evidence-data-center-jina-reader/1",
    }
    api_key = str(os.getenv(JINA_API_KEY_ENV) or "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if parameters.get("no_cache") is True:
        headers["X-No-Cache"] = "true"
    reader_url = "https://r.jina.ai/" + target_url
    request = urllib.request.Request(reader_url, headers=headers, method="GET")
    status, raw, content_type = _read_response(request, timeout, max_bytes)
    payload = _decode_payload(raw, content_type)
    metadata = {
        "http_status": status,
        "content_type": content_type,
        "request_origin": "r.jina.ai",
        "target_origin": urllib.parse.urlsplit(target_url).netloc,
        "credential_mode": "api-key" if api_key else "anonymous",
        "upstream_called": True,
    }
    return payload, metadata


def _exa_key() -> str:
    key = str(os.getenv(EXA_API_KEY_ENV) or "").strip()
    if not key:
        raise RuntimeError(f"missing repository Secret {EXA_API_KEY_ENV}")
    return key


def _post_json(
    url: str,
    body: Mapping[str, Any],
    *,
    headers: Mapping[str, str],
    timeout: int,
    max_bytes: int,
) -> tuple[Any, dict[str, Any]]:
    request = urllib.request.Request(
        url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "gpts-evidence-data-center-web-retrieval/1",
            **dict(headers),
        },
        method="POST",
    )
    status, raw, content_type = _read_response(request, timeout, max_bytes)
    payload = _decode_payload(raw, content_type)
    if not isinstance(payload, Mapping):
        raise RuntimeError("upstream JSON root must be an object")
    metadata = {
        "http_status": status,
        "content_type": content_type,
        "request_origin": urllib.parse.urlsplit(url).netloc,
        "request_path": urllib.parse.urlsplit(url).path,
        "credential_mode": "api-key",
        "upstream_called": True,
    }
    return dict(payload), metadata


def _exa_search(
    parameters: Mapping[str, Any], timeout: int, max_bytes: int
) -> tuple[Any, dict[str, Any]]:
    query = _required_text(parameters.get("query"), "query", 1000)
    num_results = _bounded_int(
        parameters.get("num_results"),
        default=5,
        minimum=1,
        maximum=10,
        name="num_results",
    )
    search_type = str(parameters.get("search_type") or "auto")
    if search_type not in {"auto", "fast", "instant"}:
        raise ValueError("search_type is not allowed")
    content_mode = str(parameters.get("content_mode") or "highlights")
    if content_mode not in {"none", "highlights", "text"}:
        raise ValueError("content_mode is not allowed")
    max_characters = _bounded_int(
        parameters.get("max_characters"),
        default=4000,
        minimum=500,
        maximum=20000,
        name="max_characters",
    )
    body: dict[str, Any] = {
        "query": query,
        "type": search_type,
        "numResults": num_results,
    }
    if content_mode == "highlights":
        body["contents"] = {
            "highlights": {"query": query, "maxCharacters": max_characters}
        }
    elif content_mode == "text":
        body["contents"] = {"text": {"maxCharacters": max_characters}}
    payload, metadata = _post_json(
        "https://api.exa.ai/search",
        body,
        headers={"x-api-key": _exa_key()},
        timeout=timeout,
        max_bytes=max_bytes,
    )
    if not isinstance(payload.get("results"), list):
        raise RuntimeError("Exa search response has no results array")
    metadata["result_count"] = len(payload["results"])
    return payload, metadata


def _exa_contents(
    parameters: Mapping[str, Any], timeout: int, max_bytes: int
) -> tuple[Any, dict[str, Any]]:
    raw_urls = parameters.get("urls")
    if not isinstance(raw_urls, list):
        raise ValueError("urls must be an array")
    urls = [validate_public_https_url(item) for item in raw_urls]
    if not 1 <= len(urls) <= 5:
        raise ValueError("urls must contain 1 to 5 values")
    content_mode = str(parameters.get("content_mode") or "text")
    if content_mode not in {"highlights", "text"}:
        raise ValueError("content_mode is not allowed")
    max_characters = _bounded_int(
        parameters.get("max_characters"),
        default=8000,
        minimum=500,
        maximum=20000,
        name="max_characters",
    )
    max_age_hours = _bounded_int(
        parameters.get("max_age_hours"),
        default=24,
        minimum=0,
        maximum=720,
        name="max_age_hours",
    )
    body: dict[str, Any] = {"urls": urls, "maxAgeHours": max_age_hours}
    if content_mode == "text":
        body["text"] = {"maxCharacters": max_characters}
    else:
        highlight_query = _required_text(
            parameters.get("highlight_query") or "main facts and evidence",
            "highlight_query",
            1000,
        )
        body["highlights"] = {
            "query": highlight_query,
            "maxCharacters": max_characters,
        }
    payload, metadata = _post_json(
        "https://api.exa.ai/contents",
        body,
        headers={"x-api-key": _exa_key()},
        timeout=timeout,
        max_bytes=max_bytes,
    )
    if not isinstance(payload.get("results"), list):
        raise RuntimeError("Exa contents response has no results array")
    metadata["result_count"] = len(payload["results"])
    metadata["requested_url_count"] = len(urls)
    return payload, metadata


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
        default=45,
        minimum=5,
        maximum=120,
        name="timeout_seconds",
    )
    max_bytes = _bounded_int(
        acceptance.get("max_response_bytes"),
        default=1_000_000,
        minimum=1024,
        maximum=5_000_000,
        name="max_response_bytes",
    )
    started = time.perf_counter()
    started_at = utc_now()
    status = "API_WEB_FAILED"
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
            metadata = {
                "source": "repository-catalog",
                "http_status": None,
                "upstream_called": False,
                "credential_mode": "none",
            }
        elif provider == "jina-reader":
            credential_secret_name = (
                JINA_API_KEY_ENV if str(os.getenv(JINA_API_KEY_ENV) or "").strip() else None
            )
            data, metadata = _jina_read(parameters, timeout, max_bytes)
        elif provider == "exa" and operation == "search":
            credential_secret_name = EXA_API_KEY_ENV
            data, metadata = _exa_search(parameters, timeout, max_bytes)
        elif provider == "exa" and operation == "contents":
            credential_secret_name = EXA_API_KEY_ENV
            data, metadata = _exa_contents(parameters, timeout, max_bytes)
        else:
            raise ValueError(f"unsupported provider operation: {provider}/{operation}")
        status = "API_WEB_COMPLETED"
    except RuntimeError as exc:
        message = str(exc)
        code = "API_WEB_BLOCKED" if message.startswith("missing repository Secret") else "API_WEB_UPSTREAM_FAILED"
        status = code
        failure = {
            "code": code,
            "stage": "execute",
            "message": message,
            "retryable": False,
        }
    except ValueError as exc:
        status = "API_WEB_REJECTED"
        failure = {
            "code": "API_WEB_REJECTED",
            "stage": "validate",
            "message": str(exc),
            "retryable": False,
        }
    completed_at = utc_now()
    result = {
        "schema_version": "web-retrieval-result-v1",
        "status": status,
        "task_id": str(ticket["task_id"]),
        "provider": provider,
        "operation": operation,
        "started_at": started_at,
        "completed_at": completed_at,
        "duration_ms": round((time.perf_counter() - started) * 1000, 3),
        "data": data,
        "metadata": metadata,
        "failure": failure,
        "credential_secret_name": credential_secret_name,
        "secret_values_exposed": False,
        "model_calls": 0,
        "ticket_sha256": canonical_sha(ticket),
    }
    result["snapshot_sha256"] = canonical_sha(
        {key: value for key, value in result.items() if key != "snapshot_sha256"}
    )
    write_json(output_dir / "result.json", result)
    write_json(
        output_dir / "api-diagnostics.json",
        {
            "status": status,
            "failure": failure,
            "provider": provider,
            "operation": operation,
            "upstream_called": bool(metadata.get("upstream_called")),
            "secret_values_exposed": False,
        },
    )
    write_output("status", status)
    return 0 if status == "API_WEB_COMPLETED" else 1


def _compact_json(value: Any, limit: int = 12000) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)
    if len(text) <= limit:
        return text
    return text[:limit] + "\n... [truncated; full result is in the Artifact]"


def render(output_dir: Path, phase: str, artifact_url: str = "") -> int:
    ticket_status = load_json(output_dir / "ticket-status.json")
    if phase == "accepted":
        print("## API_WEB_ACCEPTED")
        print()
        print(f"- Task ID: `{ticket_status.get('task_id', '')}`")
        print(f"- Provider: `{ticket_status.get('provider', '')}`")
        print(f"- Operation: `{ticket_status.get('operation', '')}`")
        print(f"- Ticket SHA256: `{ticket_status.get('ticket_sha256', '')}`")
        print("- Model calls: `0`")
        return 0
    if phase == "rejected":
        print("## API_WEB_REJECTED")
        print()
        print(f"- Reason: {ticket_status.get('reason', '')}")
        print("- Secret values exposed: `false`")
        print("- Model calls: `0`")
        return 0
    result = load_json(output_dir / "result.json")
    print(f"## {result['status']}")
    print()
    print(f"- Task ID: `{result['task_id']}`")
    print(f"- Provider: `{result['provider']}`")
    print(f"- Operation: `{result['operation']}`")
    print(f"- Upstream called: `{str(bool(result['metadata'].get('upstream_called'))).lower()}`")
    print(f"- Credential mode: `{result['metadata'].get('credential_mode', 'none')}`")
    print(f"- Snapshot SHA256: `{result['snapshot_sha256']}`")
    if artifact_url:
        print(f"- Artifact: {artifact_url}")
    print("- Secret values exposed: `false`")
    print("- Model calls: `0`")
    if result.get("failure"):
        print()
        print(f"- Failure: `{result['failure']['code']}` — {result['failure']['message']}")
    elif result.get("data") is not None:
        print()
        print("```json")
        print(_compact_json(result["data"]))
        print("```")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--event-path", type=Path, required=True)
    prepare_parser.add_argument("--output-dir", type=Path, required=True)

    execute_parser = subparsers.add_parser("execute")
    execute_parser.add_argument("--ticket", type=Path, required=True)
    execute_parser.add_argument("--output-dir", type=Path, required=True)

    render_parser = subparsers.add_parser("render")
    render_parser.add_argument("--output-dir", type=Path, required=True)
    render_parser.add_argument(
        "--phase", choices=("accepted", "rejected", "completed"), required=True
    )
    render_parser.add_argument("--artifact-url", default="")

    args = parser.parse_args()
    if args.command == "prepare":
        return prepare(args.event_path, args.output_dir)
    if args.command == "execute":
        return execute(args.ticket, args.output_dir)
    return render(args.output_dir, args.phase, args.artifact_url)


if __name__ == "__main__":
    raise SystemExit(main())
