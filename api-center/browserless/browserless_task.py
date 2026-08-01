#!/usr/bin/env python3
"""Bounded, read-only Browserless REST execution for public HTTPS pages."""
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
CATALOG_PATH = HERE.parent / "web-retrieval" / "provider-catalog.json"
TOKEN_ENV = "BROWSERLESS_TOKEN"
API_ORIGIN = "https://production-sfo.browserless.io"
BLOCKED_HOSTNAMES = {"localhost", "metadata.google.internal", "metadata.azure.internal", "kubernetes.default", "kubernetes.default.svc", "instance-data"}
BLOCKED_SUFFIXES = (".local", ".internal", ".localhost", ".svc", ".cluster.local")
BINARY_TYPES = {"screenshot": {"png": "image/png", "jpeg": "image/jpeg", "webp": "image/webp"}, "pdf": {"pdf": "application/pdf"}}


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


def provider_catalog() -> Mapping[str, Any]:
    for row in load_json(CATALOG_PATH)["providers"]:
        if row.get("provider_id") == "browserless":
            return row
    raise RuntimeError("browserless provider catalog is missing")


def operation_contract(operation: str) -> Mapping[str, Any]:
    for row in provider_catalog()["operations"]:
        if row.get("operation_id") == operation:
            return row
    raise ValueError(f"unsupported browserless operation: {operation}")


def validate_ticket(ticket: Mapping[str, Any]) -> None:
    errors = sorted(Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(ticket), key=lambda item: list(item.absolute_path))
    if errors:
        raise ValueError("; ".join(f"{'.'.join(str(x) for x in item.absolute_path) or '$'}: {item.message}" for item in errors[:20]))
    contract = operation_contract(str(ticket["operation"]))
    parameter_schema = contract.get("parameter_schema")
    if isinstance(parameter_schema, Mapping):
        parameter_errors = sorted(Draft202012Validator(dict(parameter_schema)).iter_errors(ticket.get("parameters") or {}), key=lambda item: list(item.absolute_path))
        if parameter_errors:
            raise ValueError("; ".join(f"parameters.{'.'.join(str(x) for x in item.absolute_path)}: {item.message}" for item in parameter_errors[:20]))


def _required_text(value: Any, name: str, maximum: int) -> str:
    text = str(value or "").strip()
    if not text or len(text) > maximum:
        raise ValueError(f"{name} must contain 1 to {maximum} characters")
    return text


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


def validate_public_https_url(value: Any) -> str:
    url = _required_text(value, "url", 2048)
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise ValueError("url must be an absolute HTTPS URL")
    if parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError("url credentials and custom ports are forbidden")
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
        records = socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise ValueError("url hostname could not be resolved") from exc
    addresses = {str(row[4][0]).split("%", 1)[0] for row in records if row and len(row) >= 5 and row[4]}
    if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
        raise ValueError("url hostname does not resolve exclusively to public IPs")
    return urllib.parse.urlunsplit(("https", parsed.netloc, parsed.path or "/", parsed.query, ""))


def token() -> str:
    value = str(os.getenv(TOKEN_ENV) or "").strip()
    if not value:
        raise RuntimeError(f"missing repository Secret {TOKEN_ENV}")
    return value


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None


def sanitize(value: Any) -> Any:
    forbidden = ("authorization", "cookie", "token", "secret", "api_key", "apikey", "profile", "browserwsendpoint", "websocket")
    if isinstance(value, Mapping):
        return {str(key): sanitize(item) for key, item in value.items() if not any(part in str(key).casefold() for part in forbidden)}
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    return value


def request_body(operation: str, parameters: Mapping[str, Any]) -> tuple[dict[str, Any], str | None]:
    if operation == "search":
        return {"query": _required_text(parameters.get("query"), "query", 1000), "limit": _bounded_int(parameters.get("limit"), default=3, minimum=1, maximum=3, name="limit"), "sources": ["web"]}, None
    url = validate_public_https_url(parameters.get("url"))
    if operation == "content":
        return {"url": url}, None
    if operation == "scrape":
        selectors = parameters.get("selectors")
        if not isinstance(selectors, list) or not 1 <= len(selectors) <= 20:
            raise ValueError("selectors must contain 1 to 20 values")
        elements = [{"selector": _required_text(item, "selector", 500)} for item in selectors]
        return {"url": url, "elements": elements}, None
    if operation == "screenshot":
        image_type = str(parameters.get("image_type") or "png")
        if image_type not in {"png", "jpeg", "webp"}:
            raise ValueError("image_type is not allowed")
        options: dict[str, Any] = {"type": image_type, "fullPage": bool(parameters.get("full_page", True))}
        if image_type != "png" and parameters.get("quality") not in (None, ""):
            options["quality"] = _bounded_int(parameters.get("quality"), default=80, minimum=1, maximum=100, name="quality")
        return {"url": url, "options": options}, image_type
    if operation == "pdf":
        page_format = str(parameters.get("format") or "A4")
        if page_format not in {"A4", "Letter", "Legal", "A3", "A5"}:
            raise ValueError("format is not allowed")
        return {"url": url, "options": {"format": page_format, "landscape": bool(parameters.get("landscape", False)), "printBackground": bool(parameters.get("print_background", True))}}, "pdf"
    if operation == "performance":
        body: dict[str, Any] = {"url": url}
        categories = parameters.get("categories")
        if categories:
            allowed = {"accessibility", "best-practices", "performance", "pwa", "seo"}
            if not isinstance(categories, list) or not 1 <= len(categories) <= 5 or any(item not in allowed for item in categories):
                raise ValueError("categories contains unsupported values")
            body["config"] = {"extends": "lighthouse:default", "settings": {"onlyCategories": categories}}
        return body, None
    if operation == "map":
        body = {
            "url": url,
            "limit": _bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=100, name="limit"),
            "sitemap": str(parameters.get("sitemap") or "include"),
            "includeSubdomains": bool(parameters.get("include_subdomains", False)),
            "ignoreQueryParameters": bool(parameters.get("ignore_query_parameters", True)),
        }
        if body["sitemap"] not in {"include", "skip", "only"}:
            raise ValueError("sitemap is not allowed")
        search = str(parameters.get("search") or "").strip()
        if search:
            body["search"] = _required_text(search, "search", 500)
        return body, None
    raise ValueError(f"unsupported operation: {operation}")


def call_upstream(operation: str, body: Mapping[str, Any], timeout: int, max_bytes: int) -> tuple[int, bytes, str]:
    query = urllib.parse.urlencode({"token": token(), "timeout": timeout * 1000})
    endpoint = f"{API_ORIGIN}/{operation}?{query}"
    request = urllib.request.Request(endpoint, data=json.dumps(body, ensure_ascii=False).encode("utf-8"), headers={"Accept": "*/*", "Content-Type": "application/json", "User-Agent": "gpts-evidence-data-center-browserless/1"}, method="POST")
    opener = urllib.request.build_opener(NoRedirect())
    try:
        with opener.open(request, timeout=timeout + 10) as response:
            status = int(response.status)
            raw = response.read(max_bytes + 1)
            content_type = str(response.headers.get("Content-Type") or "")
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        raw = exc.read(max_bytes + 1)
        content_type = str(exc.headers.get("Content-Type") or "") if exc.headers else ""
    if len(raw) > max_bytes:
        raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
    if not 200 <= status < 300:
        message = raw[:1000].decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"upstream HTTP {status}: {message}")
    return status, raw, content_type


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
        if not title.startswith("[api-browserless]"):
            raise ValueError("issue title must start with [api-browserless]")
        parsed = json.loads(body)
        if not isinstance(parsed, Mapping):
            raise ValueError("ticket body must be a JSON object")
        validate_ticket(parsed)
        ticket = parsed
        accepted = True
        write_json(output_dir / "ticket.json", ticket)
    except (json.JSONDecodeError, ValueError) as exc:
        reason = str(exc)
    status = {"schema_version": "browserless-ticket-status-v1", "accepted": accepted, "reason": reason, "task_id": str((ticket or {}).get("task_id") or ""), "provider": "browserless", "operation": str((ticket or {}).get("operation") or ""), "ticket_sha256": canonical_sha(ticket) if ticket else None, "secret_values_exposed": False, "model_calls": 0}
    write_json(output_dir / "ticket-status.json", status)
    write_output("accepted", "true" if accepted else "false")
    write_output("reason", reason)
    return 0 if accepted else 1


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket)
    operation = str(ticket["operation"])
    acceptance = dict(ticket["acceptance"])
    timeout = _bounded_int(acceptance.get("timeout_seconds"), default=45, minimum=5, maximum=120, name="timeout_seconds")
    max_bytes = _bounded_int(acceptance.get("max_response_bytes"), default=1000000, minimum=1024, maximum=10000000, name="max_response_bytes")
    started_at = utc_now()
    started = time.perf_counter()
    status = "API_BROWSERLESS_FAILED"
    failure: dict[str, Any] | None = None
    snapshot: dict[str, Any] = {}
    metadata: dict[str, Any] = {"upstream_called": False, "api_origin": "production-sfo.browserless.io", "credential_mode": "query-token", "secret_values_exposed": False}
    try:
        if operation == "catalog-capabilities":
            snapshot = {"provider": provider_catalog()}
            metadata["credential_mode"] = "none"
        else:
            body, binary_extension = request_body(operation, dict(ticket.get("parameters") or {}))
            http_status, raw, content_type = call_upstream(operation, body, timeout, max_bytes)
            metadata.update({"upstream_called": True, "http_status": http_status, "content_type": content_type, "request_path": f"/{operation}", "response_bytes": len(raw)})
            if binary_extension:
                expected = BINARY_TYPES[operation][binary_extension]
                if expected not in content_type.casefold():
                    raise RuntimeError(f"unexpected binary content type: {content_type}")
                filename = f"result.{binary_extension}"
                (output_dir / filename).write_bytes(raw)
                snapshot = {"provider": "browserless", "operation": operation, "artifact_file": filename, "content_type": content_type, "bytes": len(raw), "sha256": bytes_sha(raw)}
            elif operation == "content":
                text = raw.decode("utf-8", errors="replace")
                snapshot = {"provider": "browserless", "operation": operation, "content_type": content_type, "content": text, "content_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}
            else:
                try:
                    payload = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise RuntimeError("upstream returned invalid JSON") from exc
                if not isinstance(payload, Mapping):
                    raise RuntimeError("upstream JSON root must be an object")
                if operation == "map" and payload.get("success") is not True:
                    raise RuntimeError(f"Browserless map business failure: {payload.get('message') or payload.get('error') or 'success=false'}")
                snapshot = {"provider": "browserless", "operation": operation, "data": sanitize(payload)}
            status = "API_BROWSERLESS_COMPLETED"
    except Exception as exc:
        failure = {"type": type(exc).__name__, "message": str(exc)[:2000]}
    duration_ms = round((time.perf_counter() - started) * 1000)
    if snapshot:
        write_json(output_dir / "snapshot.json", snapshot)
    diagnostics = {"schema_version": "browserless-diagnostics-v1", "status": status, "task_id": ticket["task_id"], "operation": operation, "started_at": started_at, "completed_at": utc_now(), "duration_ms": duration_ms, "metadata": metadata, "failure": failure, "secret_values_exposed": False, "model_calls": 0}
    write_json(output_dir / "diagnostics.json", diagnostics)
    files = []
    for path in sorted(output_dir.iterdir()):
        if path.is_file() and path.name != "manifest.json":
            raw = path.read_bytes()
            files.append({"name": path.name, "bytes": len(raw), "sha256": bytes_sha(raw)})
    manifest = {"schema_version": "browserless-manifest-v1", "status": status, "task_id": ticket["task_id"], "provider": "browserless", "operation": operation, "files": files, "secret_values_exposed": False, "model_calls": 0}
    write_json(output_dir / "manifest.json", manifest)
    write_output("status", status)
    return 0 if status == "API_BROWSERLESS_COMPLETED" else 1


def render(output_dir: Path, phase: str, artifact_url: str) -> int:
    ticket_status = load_json(output_dir / "ticket-status.json") if (output_dir / "ticket-status.json").exists() else {}
    if phase == "accepted":
        print(f"Browserless API ticket accepted: `{ticket_status.get('task_id', '')}` / `{ticket_status.get('operation', '')}`. Secret values remain backend-only.")
        return 0
    if phase == "rejected":
        print(f"Browserless API ticket rejected: {ticket_status.get('reason') or 'invalid ticket'}")
        return 0
    diagnostics = load_json(output_dir / "diagnostics.json") if (output_dir / "diagnostics.json").exists() else {}
    manifest = load_json(output_dir / "manifest.json") if (output_dir / "manifest.json").exists() else {}
    print(f"Browserless API result: `{diagnostics.get('status', 'UNKNOWN')}`")
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
