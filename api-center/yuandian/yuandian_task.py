#!/usr/bin/env python3
"""Maximum-safe read-only adapter for the YuanDian legal open platform."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import traceback
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
SCHEMA = json.loads((HERE / "ticket.schema.json").read_text(encoding="utf-8"))
CATALOG = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
SNAPSHOT = json.loads((HERE / "readonly-apis.snapshot.json").read_text(encoding="utf-8"))
PROVIDER = CATALOG["providers"][0]
OPERATIONS = {str(row["operation_id"]): row for row in PROVIDER["operations"]}
FIXED_APIS = {str(row["operation_id"]): row for row in SNAPSHOT["apis"]}
ROUTE_SNAPSHOT = {str(row["route_key"]): row for row in SNAPSHOT["apis"]}
OFFICIAL_ORIGIN = "https://open.chineselaw.com"
CATALOG_URL = f"{OFFICIAL_ORIGIN}/api/apis?pageNum=1&pageSize=200&sortBy=latest"
ROUTE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{2,95}$")
ARGUMENT_RE = re.compile(r"^[A-Za-z_\u4e00-\u9fff][A-Za-z0-9_\-\u4e00-\u9fff]{0,95}$")
FORBIDDEN_ARGUMENT_NAMES = {
    "url", "uri", "endpoint", "host", "headers", "header", "authorization",
    "cookie", "api_key", "apikey", "token", "secret", "password", "method",
}
SECRET_KEY_RE = re.compile(r"(?:api.?key|authorization|cookie|token|secret|password)", re.I)
PERSONAL_KEY_RE = re.compile(
    r"(?:身份证|证件号|公民身份|手机号|手机号码|联系电话|联系手机|邮箱|电子邮箱|email|phone|mobile|id.?card)",
    re.I,
)
PHONE_RE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
ID_RE = re.compile(r"(?<!\d)\d{17}[0-9Xx](?!\d)")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def output(name: str, value: Any) -> None:
    target = os.getenv("GITHUB_OUTPUT")
    if target:
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(f"{name}={str(value).replace(chr(10), ' ')}\n")


def _bounded_int(value: Any, default: int, minimum: int, maximum: int, name: str) -> int:
    if value in (None, ""):
        return default
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an integer")
    parsed = int(value)
    if not minimum <= parsed <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return parsed


def _validate_json_value(value: Any, *, depth: int = 0) -> None:
    if depth > 6:
        raise ValueError("arguments exceed maximum nesting depth 6")
    if value is None or isinstance(value, (bool, int, float)):
        return
    if isinstance(value, str):
        if len(value) > 20000:
            raise ValueError("argument string exceeds 20000 characters")
        return
    if isinstance(value, Mapping):
        if len(value) > 60:
            raise ValueError("arguments object exceeds 60 properties")
        for raw_key, item in value.items():
            key = str(raw_key)
            if not ARGUMENT_RE.fullmatch(key):
                raise ValueError(f"unsafe argument name: {key}")
            if key.lower() in FORBIDDEN_ARGUMENT_NAMES or SECRET_KEY_RE.search(key):
                raise ValueError(f"forbidden request-control or secret argument: {key}")
            _validate_json_value(item, depth=depth + 1)
        return
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        if len(value) > 200:
            raise ValueError("argument array exceeds 200 items")
        for item in value:
            _validate_json_value(item, depth=depth + 1)
        return
    raise ValueError(f"unsupported argument value type: {type(value).__name__}")


def _validate_schema(ticket: Mapping[str, Any]) -> None:
    errors = sorted(Draft202012Validator(SCHEMA).iter_errors(ticket), key=lambda item: list(item.absolute_path))
    if errors:
        raise ValueError("; ".join(
            f"{'.'.join(str(x) for x in error.absolute_path) or '$'}: {error.message}"
            for error in errors[:20]
        ))


def validate_ticket(ticket: Mapping[str, Any]) -> None:
    _validate_schema(ticket)
    if str(ticket.get("provider")) != "yuandian-law":
        raise ValueError("provider must be yuandian-law")
    operation = str(ticket.get("operation") or "")
    row = OPERATIONS.get(operation)
    if row is None:
        raise ValueError(f"unsupported YuanDian operation: {operation}")
    parameters = ticket.get("parameters") or {}
    if not isinstance(parameters, Mapping):
        raise ValueError("parameters must be an object")
    allowlist = {str(name) for name in row.get("parameters") or []}
    unexpected = sorted(set(parameters) - allowlist)
    if unexpected:
        raise ValueError(f"non-allowlisted parameters: {unexpected}")
    if operation == "catalog-capabilities" and parameters:
        raise ValueError("catalog-capabilities accepts no parameters")
    if operation == "catalog-live":
        _bounded_int(parameters.get("page_size"), 200, 1, 200, "page_size")
        category = parameters.get("category_id")
        if category not in (None, "", 6, 7, 9, 10):
            raise ValueError("category_id must be one of 6, 7, 9, 10")
        return
    if operation == "invoke-readonly-api":
        route_key = str(parameters.get("route_key") or "")
        if not ROUTE_RE.fullmatch(route_key):
            raise ValueError("route_key has an unsafe format")
    arguments = parameters.get("arguments") or {}
    if not isinstance(arguments, Mapping):
        raise ValueError("arguments must be an object")
    _validate_json_value(arguments)
    _bounded_int(parameters.get("timeout_seconds"), 60, 5, 120, "timeout_seconds")
    _bounded_int(parameters.get("max_response_bytes"), 1_000_000, 1024, 5_000_000, "max_response_bytes")


def prepare(event_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    event = json.loads(event_path.read_text(encoding="utf-8"))
    issue = event.get("issue") if isinstance(event.get("issue"), Mapping) else {}
    accepted = False
    reason = ""
    ticket: Mapping[str, Any] | None = None
    try:
        parsed = json.loads(str(issue.get("body") or ""))
        if not isinstance(parsed, Mapping):
            raise ValueError("ticket body must be a JSON object")
        validate_ticket(parsed)
        if not str(issue.get("title") or "").startswith("[api-yuandian]"):
            raise ValueError("issue title must start with [api-yuandian]")
        ticket = dict(parsed)
        write_json(output_dir / "ticket.json", ticket)
        accepted = True
    except (json.JSONDecodeError, ValueError) as exc:
        reason = str(exc)
    status = {
        "schema_version": "yuandian-ticket-status-v1",
        "accepted": accepted,
        "reason": reason,
        "task_id": str((ticket or {}).get("task_id") or ""),
        "provider": str((ticket or {}).get("provider") or ""),
        "operation": str((ticket or {}).get("operation") or ""),
        "ticket_sha256": canonical_sha(ticket) if ticket else None,
        "model_calls": 0,
        "secret_values_exposed": False,
    }
    write_json(output_dir / "ticket-status.json", status)
    output("accepted", "true" if accepted else "false")
    output("reason", reason)
    return 0 if accepted else 1


def _resolve_api_key() -> str:
    return str(os.getenv("YUANDIAN_API_KEY") or "").strip()


def _fixed_url(route_key: str) -> str:
    if not ROUTE_RE.fullmatch(route_key):
        raise ValueError("route_key has an unsafe format")
    url = f"{OFFICIAL_ORIGIN}/open/{route_key}"
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "open.chineselaw.com":
        raise ValueError("only the fixed YuanDian HTTPS origin is allowed")
    return url


def _read_json_response(request: urllib.request.Request, timeout: int, max_bytes: int) -> Any:
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(max_bytes + 1)
        status = int(getattr(response, "status", 200))
    if len(raw) > max_bytes:
        raise ValueError(f"YuanDian response exceeds {max_bytes} bytes")
    if status < 200 or status >= 300:
        raise RuntimeError(f"YuanDian HTTP status {status}")
    return json.loads(raw.decode("utf-8-sig"))


def _request_json(method: str, url: str, *, api_key: str = "", arguments: Mapping[str, Any] | None = None,
                  timeout: int = 60, max_bytes: int = 1_000_000) -> Any:
    method = method.upper()
    if method not in {"GET", "POST"}:
        raise ValueError("only GET and POST YuanDian APIs are allowed")
    headers = {"Accept": "application/json", "User-Agent": "managed-yuandian-api-center/1"}
    if api_key:
        headers["X-API-Key"] = api_key
    body = None
    args = dict(arguments or {})
    if method == "GET":
        query = urllib.parse.urlencode(args, doseq=True)
        if query:
            url = f"{url}{'&' if '?' in url else '?'}{query}"
    else:
        headers["Content-Type"] = "application/json; charset=utf-8"
        body = json.dumps(args, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return _read_json_response(urllib.request.Request(url, data=body, headers=headers, method=method), timeout, max_bytes)


def _catalog_rows(payload: Any) -> list[Mapping[str, Any]]:
    queue = [payload]
    while queue:
        value = queue.pop(0)
        if isinstance(value, list) and all(isinstance(row, Mapping) for row in value):
            return list(value)
        if isinstance(value, Mapping):
            for key in ("records", "list", "rows", "content", "items", "data"):
                candidate = value.get(key)
                if isinstance(candidate, (list, Mapping)):
                    queue.append(candidate)
    raise ValueError("YuanDian catalog response did not contain an API list")


def _normalize_catalog_row(row: Mapping[str, Any]) -> dict[str, Any] | None:
    route_key = str(row.get("routeKey") or row.get("route_key") or "")
    method = str(row.get("httpMethod") or row.get("method") or "").upper()
    if not ROUTE_RE.fullmatch(route_key) or method not in {"GET", "POST"}:
        return None
    return {
        "id": row.get("id"),
        "name": str(row.get("name") or row.get("apiName") or route_key),
        "category": str(row.get("categoryName") or row.get("category") or ""),
        "category_id": row.get("categoryId"),
        "route_key": route_key,
        "http_method": method,
        "description": str(row.get("description") or row.get("summary") or ""),
        "price": row.get("price"),
        "charge_type": row.get("chargeType"),
        "request_params": row.get("requestParams") or row.get("request_params") or [],
        "response_params": row.get("responseParams") or row.get("response_params") or [],
        "full_document": row.get("fullDocument") or "",
        "read_only": True,
    }


def fetch_live_catalog(category_id: int | None = None, page_size: int = 200) -> list[dict[str, Any]]:
    query = {"pageNum": 1, "pageSize": page_size, "sortBy": "latest"}
    if category_id is not None:
        query["categoryId"] = category_id
    url = f"{OFFICIAL_ORIGIN}/api/apis?{urllib.parse.urlencode(query)}"
    payload = _request_json("GET", url, timeout=30, max_bytes=5_000_000)
    rows = [_normalize_catalog_row(row) for row in _catalog_rows(payload)]
    return [row for row in rows if row is not None]


def _business_success(payload: Any) -> None:
    if not isinstance(payload, Mapping):
        return
    code = payload.get("code")
    if code is not None and str(code) not in {"0", "200", "201"}:
        raise RuntimeError(f"YuanDian business code {code}: {payload.get('message') or payload.get('msg') or ''}")
    status = str(payload.get("status") or "").lower()
    if status in {"failed", "failure", "error", "unauthorized", "forbidden"}:
        raise RuntimeError(f"YuanDian business status {status}")


def _redact(value: Any, key: str = "") -> Any:
    if SECRET_KEY_RE.search(key) or PERSONAL_KEY_RE.search(key):
        return "[REDACTED]"
    if isinstance(value, Mapping):
        return {str(k): _redact(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, str):
        text = PHONE_RE.sub("[REDACTED_PHONE]", value)
        text = ID_RE.sub("[REDACTED_ID]", text)
        return EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    return value


def _execute_operation(operation: str, parameters: Mapping[str, Any]) -> dict[str, Any]:
    if operation == "catalog-capabilities":
        return {"provider": "yuandian-law", "catalog": CATALOG, "readonly_api_snapshot": SNAPSHOT}
    if operation == "catalog-live":
        category = parameters.get("category_id")
        rows = fetch_live_catalog(int(category) if category not in (None, "") else None,
                                  _bounded_int(parameters.get("page_size"), 200, 1, 200, "page_size"))
        return {
            "provider": "yuandian-law", "operation": operation, "api_count": len(rows),
            "snapshot_api_count": len(SNAPSHOT["apis"]), "rows": _redact(rows),
        }
    if operation == "invoke-readonly-api":
        route_key = str(parameters.get("route_key") or "")
        live = {row["route_key"]: row for row in fetch_live_catalog()}
        api = live.get(route_key)
        if api is None:
            raise ValueError("route_key is not present in the current official YuanDian catalog")
    else:
        api = FIXED_APIS[operation]
        route_key = str(api["route_key"])
    method = str(api["http_method"]).upper()
    api_key = _resolve_api_key()
    if not api_key:
        raise ValueError("YUANDIAN_API_KEY is required for YuanDian business API calls")
    arguments = dict(parameters.get("arguments") or {})
    timeout = _bounded_int(parameters.get("timeout_seconds"), 60, 5, 120, "timeout_seconds")
    max_bytes = _bounded_int(parameters.get("max_response_bytes"), 1_000_000, 1024, 5_000_000, "max_response_bytes")
    payload = _request_json(method, _fixed_url(route_key), api_key=api_key, arguments=arguments,
                            timeout=timeout, max_bytes=max_bytes)
    _business_success(payload)
    return {
        "provider": "yuandian-law", "operation": operation, "route_key": route_key,
        "http_method": method, "upstream_called": True,
        "response": _redact(payload), "direct_personal_identifiers_redacted": True,
    }


def _manifest(output_dir: Path) -> None:
    files = []
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name != "artifact-manifest.json":
            files.append({"path": str(path.relative_to(output_dir)), "size_bytes": path.stat().st_size,
                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    write_json(output_dir / "artifact-manifest.json", {"version": 1, "files": files})


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = json.loads(ticket_path.read_text(encoding="utf-8"))
    try:
        validate_ticket(ticket)
        data = _execute_operation(str(ticket["operation"]), dict(ticket.get("parameters") or {}))
        snapshot = {
            "schema_version": "yuandian-snapshot-v1", "status": "API_YUANDIAN_COMPLETED",
            "task_id": ticket["task_id"], "provider": ticket["provider"], "operation": ticket["operation"],
            "ticket_sha256": canonical_sha(ticket), "data": data,
            "security": {"model_calls": 0, "arbitrary_urls_allowed": False, "arbitrary_headers_allowed": False,
                         "write_operations_allowed": False, "secret_values_included": False,
                         "direct_personal_identifiers_redacted": True},
        }
        write_json(output_dir / "yuandian-snapshot.json", snapshot)
        write_json(output_dir / "yuandian-audit.json", {"status": "PASS", "snapshot_sha256": canonical_sha(snapshot),
                                                         "model_calls": 0, "fixed_origin": OFFICIAL_ORIGIN})
        (output_dir / "yuandian-summary.md").write_text(
            "# API_YUANDIAN_COMPLETED\n\n"
            f"- Task ID: `{ticket['task_id']}`\n- Operation: `{ticket['operation']}`\n"
            f"- Snapshot SHA256: `{canonical_sha(snapshot)}`\n", encoding="utf-8")
        output("status", "API_YUANDIAN_COMPLETED")
        _manifest(output_dir)
        return 0
    except Exception as exc:
        failure = {
            "schema_version": "yuandian-snapshot-v1", "status": "API_YUANDIAN_FAILED",
            "task_id": str(ticket.get("task_id") or ""), "provider": str(ticket.get("provider") or ""),
            "operation": str(ticket.get("operation") or ""),
            "failure": {"code": "YUANDIAN_UPSTREAM_OR_REQUEST_FAILED", "error_type": type(exc).__name__,
                        "message": str(exc), "retryable": isinstance(exc, (OSError, TimeoutError, urllib.error.URLError))},
            "security": {"model_calls": 0, "arbitrary_urls_allowed": False, "arbitrary_headers_allowed": False,
                         "write_operations_allowed": False, "secret_values_included": False,
                         "direct_personal_identifiers_redacted": True},
        }
        write_json(output_dir / "yuandian-snapshot.json", failure)
        write_json(output_dir / "yuandian-error.json", {"error_type": type(exc).__name__, "message": str(exc),
                                                         "traceback": "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))[-20000:]})
        output("status", "API_YUANDIAN_FAILED")
        _manifest(output_dir)
        return 1


def render(output_dir: Path, phase: str, artifact_url: str = "") -> int:
    status = json.loads((output_dir / "ticket-status.json").read_text(encoding="utf-8"))
    if phase == "accepted":
        print("## API_YUANDIAN_ACCEPTED")
        print(f"\n- Task ID: `{status.get('task_id')}`\n- Operation: `{status.get('operation')}`\n- Model calls: `0`")
        return 0
    if phase == "rejected":
        print("## API_YUANDIAN_REJECTED")
        print(f"\n- Reason: `{status.get('reason') or 'unknown'}`")
        return 0
    snapshot = json.loads((output_dir / "yuandian-snapshot.json").read_text(encoding="utf-8"))
    print(f"## {snapshot['status']}")
    print(f"\n- Task ID: `{snapshot.get('task_id')}`\n- Operation: `{snapshot.get('operation')}`")
    if snapshot["status"] == "API_YUANDIAN_COMPLETED":
        print(f"- Snapshot SHA256: `{canonical_sha(snapshot)}`\n- Artifact: {artifact_url or 'unavailable'}")
        print("\n```json")
        print(json.dumps(snapshot["data"], ensure_ascii=False, indent=2)[:45000])
        print("```")
    else:
        print(f"- Error: `{snapshot.get('failure', {}).get('message') or 'unknown'}`\n- Artifact: {artifact_url or 'unavailable'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare"); p.add_argument("--event-path", required=True); p.add_argument("--output-dir", required=True)
    p = sub.add_parser("execute"); p.add_argument("--ticket", required=True); p.add_argument("--output-dir", required=True)
    p = sub.add_parser("render"); p.add_argument("--output-dir", required=True); p.add_argument("--phase", choices=["accepted", "rejected", "completed"], required=True); p.add_argument("--artifact-url", default="")
    args = parser.parse_args()
    if args.command == "prepare": return prepare(Path(args.event_path), Path(args.output_dir))
    if args.command == "execute": return execute(Path(args.ticket), Path(args.output_dir))
    return render(Path(args.output_dir), args.phase, args.artifact_url)


if __name__ == "__main__":
    raise SystemExit(main())
