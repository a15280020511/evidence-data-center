#!/usr/bin/env python3
"""Bounded read-only Tianditu place-search execution."""
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
SECRET_ENV = "TIANDITU_API_KEY"
ENDPOINT = "https://api.tianditu.gov.cn/v2/search"
PHONE_KEYS = {"phone", "telephone", "tel", "mobile", "mobilephone"}
QUERY_TYPES = {
    "viewport-search": 2,
    "nearby-search": 3,
    "polygon-search": 10,
    "administrative-search": 12,
    "category-search": 13,
    "statistics-search": 14,
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


def catalog_provider() -> Mapping[str, Any]:
    catalog = load_json(CATALOG_PATH)
    return next(row for row in catalog["providers"] if row["provider_id"] == "tianditu")


def operation_contract(operation: str) -> Mapping[str, Any]:
    provider = catalog_provider()
    return next(row for row in provider["operations"] if row["operation_id"] == operation)


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
    contract = operation_contract(operation)
    parameter_schema = contract.get("parameter_schema")
    parameter_errors = sorted(
        Draft202012Validator(parameter_schema).iter_errors(ticket.get("parameters") or {}),
        key=lambda item: list(item.absolute_path),
    )
    if parameter_errors:
        rendered = "; ".join(
            f"parameters.{'.'.join(str(x) for x in item.absolute_path)}: {item.message}"
            for item in parameter_errors[:20]
        )
        raise ValueError(rendered)
    if operation != "catalog-capabilities":
        build_post_str(operation, dict(ticket.get("parameters") or {}))


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
        if not title.startswith("[api-tianditu]"):
            raise ValueError("issue title must start with [api-tianditu]")
        parsed = json.loads(body)
        if not isinstance(parsed, Mapping):
            raise ValueError("ticket body must be a JSON object")
        validate_ticket(parsed)
        ticket = parsed
        accepted = True
        write_json(output_dir / "ticket.json", ticket)
    except (json.JSONDecodeError, ValueError, StopIteration) as exc:
        reason = str(exc)
    status = {
        "schema_version": "tianditu-ticket-status-v1",
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


def required_text(value: Any, name: str, maximum: int) -> str:
    text = str(value or "").strip()
    if not text or len(text) > maximum:
        raise ValueError(f"{name} must contain 1 to {maximum} characters")
    return text


def optional_text(value: Any, name: str, maximum: int) -> str:
    text = str(value or "").strip()
    if len(text) > maximum:
        raise ValueError(f"{name} must contain at most {maximum} characters")
    return text


def format_number(value: float) -> str:
    return format(float(value), ".12g")


def lonlat(value: Any, name: str) -> tuple[float, float]:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"{name} must contain longitude and latitude")
    try:
        longitude, latitude = float(value[0]), float(value[1])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} coordinates must be numeric") from exc
    if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
        raise ValueError(f"{name} coordinates are outside valid longitude/latitude ranges")
    return longitude, latitude


def map_bound(value: Any) -> str:
    if not isinstance(value, list) or len(value) != 4:
        raise ValueError("map_bound must contain min_lon, min_lat, max_lon, max_lat")
    min_lon, min_lat = lonlat(value[:2], "map_bound minimum")
    max_lon, max_lat = lonlat(value[2:], "map_bound maximum")
    if min_lon >= max_lon or min_lat >= max_lat:
        raise ValueError("map_bound minimums must be lower than maximums")
    return ",".join(format_number(item) for item in (min_lon, min_lat, max_lon, max_lat))


def data_types(value: Any) -> str:
    if value in (None, ""):
        return ""
    if not isinstance(value, list) or len(value) > 10:
        raise ValueError("data_types must be an array with at most 10 values")
    result: list[str] = []
    for item in value:
        text = required_text(item, "data_types item", 64)
        if "," in text:
            raise ValueError("data_types items may not contain commas")
        if text not in result:
            result.append(text)
    return ",".join(result)


def paging(parameters: Mapping[str, Any]) -> tuple[int, int]:
    start = bounded_int(parameters.get("start"), default=0, minimum=0, maximum=300, name="start")
    count = bounded_int(parameters.get("count"), default=10, minimum=1, maximum=300, name="count")
    if start + count > 500:
        raise ValueError("start + count may not exceed 500")
    return start, count


def common_optional(post: dict[str, Any], parameters: Mapping[str, Any], *, include_paging: bool = True) -> None:
    if include_paging:
        start, count = paging(parameters)
        post["start"] = start
        post["count"] = count
    types = data_types(parameters.get("data_types"))
    if types:
        post["dataTypes"] = types
    post["show"] = bounded_int(parameters.get("show"), default=1, minimum=1, maximum=2, name="show")


def build_post_str(operation: str, parameters: Mapping[str, Any]) -> dict[str, Any]:
    if operation == "normal-search":
        post: dict[str, Any] = {
            "keyWord": required_text(parameters.get("keyword"), "keyword", 200),
            "mapBound": map_bound(parameters.get("map_bound")),
            "level": bounded_int(parameters.get("level"), default=12, minimum=1, maximum=18, name="level"),
            "queryType": 7 if bool(parameters.get("place_only", False)) else 1,
        }
        specify = optional_text(parameters.get("specify"), "specify", 64)
        if specify:
            post["specify"] = specify
        common_optional(post, parameters)
        return post
    if operation == "viewport-search":
        post = {
            "keyWord": required_text(parameters.get("keyword"), "keyword", 200),
            "mapBound": map_bound(parameters.get("map_bound")),
            "level": bounded_int(parameters.get("level"), default=12, minimum=1, maximum=18, name="level"),
            "queryType": QUERY_TYPES[operation],
        }
        common_optional(post, parameters)
        return post
    if operation == "nearby-search":
        longitude, latitude = lonlat(parameters.get("center"), "center")
        post = {
            "keyWord": required_text(parameters.get("keyword"), "keyword", 200),
            "pointLonlat": f"{format_number(longitude)},{format_number(latitude)}",
            "queryRadius": bounded_int(parameters.get("radius"), default=1000, minimum=1, maximum=10000, name="radius"),
            "level": bounded_int(parameters.get("level"), default=12, minimum=1, maximum=18, name="level"),
            "queryType": QUERY_TYPES[operation],
        }
        common_optional(post, parameters)
        return post
    if operation == "polygon-search":
        raw_polygon = parameters.get("polygon")
        if not isinstance(raw_polygon, list) or not 4 <= len(raw_polygon) <= 20:
            raise ValueError("polygon must contain 4 to 20 coordinate pairs")
        points = [lonlat(item, f"polygon[{index}]") for index, item in enumerate(raw_polygon)]
        if points[0] != points[-1]:
            raise ValueError("polygon must be closed: first and last coordinates must match")
        if len(set(points[:-1])) < 3:
            raise ValueError("polygon must contain at least three distinct vertices")
        flattened = [format_number(number) for point in points for number in point]
        post = {
            "keyWord": required_text(parameters.get("keyword"), "keyword", 200),
            "polygon": ",".join(flattened),
            "queryType": QUERY_TYPES[operation],
        }
        common_optional(post, parameters)
        return post
    if operation == "administrative-search":
        post = {
            "keyWord": required_text(parameters.get("keyword"), "keyword", 200),
            "specify": required_text(parameters.get("specify"), "specify", 64),
            "queryType": QUERY_TYPES[operation],
        }
        common_optional(post, parameters)
        return post
    if operation == "category-search":
        types = data_types(parameters.get("data_types"))
        if not types:
            raise ValueError("category-search requires at least one data_types value")
        post = {
            "specify": required_text(parameters.get("specify"), "specify", 64),
            "mapBound": map_bound(parameters.get("map_bound")),
            "queryType": QUERY_TYPES[operation],
            "dataTypes": types,
        }
        common_optional(post, {key: value for key, value in parameters.items() if key != "data_types"})
        return post
    if operation == "statistics-search":
        post = {
            "keyWord": required_text(parameters.get("keyword"), "keyword", 200),
            "specify": required_text(parameters.get("specify"), "specify", 64),
            "queryType": QUERY_TYPES[operation],
        }
        common_optional(post, parameters, include_paging=False)
        return post
    raise ValueError(f"unsupported operation: {operation}")


def provider_key() -> str:
    key = str(os.getenv(SECRET_ENV) or "").strip()
    if not key:
        raise RuntimeError(f"missing repository Secret {SECRET_ENV}")
    return key


def read_response(request: urllib.request.Request, timeout: int, max_bytes: int) -> tuple[int, bytes, str]:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = int(response.status)
            raw = response.read(max_bytes + 1)
            content_type = str(response.headers.get("Content-Type") or "")
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        raw = exc.read(max_bytes + 1)
        content_type = str(exc.headers.get("Content-Type") or "") if exc.headers else ""
    except urllib.error.URLError as exc:
        raise RuntimeError("Tianditu upstream connection failed") from exc
    if len(raw) > max_bytes:
        raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
    if not 200 <= status < 300:
        message = raw[:1000].decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Tianditu upstream HTTP {status}: {message}")
    return status, raw, content_type


def business_status(payload: Mapping[str, Any]) -> tuple[str | None, str]:
    status = payload.get("status")
    row: Mapping[str, Any] | None = None
    if isinstance(status, Mapping):
        row = status
    elif isinstance(status, list) and status and isinstance(status[0], Mapping):
        row = status[0]
    if row is None:
        return None, ""
    code = row.get("infocode") if "infocode" in row else row.get("infoCode")
    description = str(row.get("cndesc") or row.get("message") or "")
    return str(code) if code is not None else None, description


def redact_direct_phones(value: Any) -> Any:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if str(key).casefold() in PHONE_KEYS and item not in (None, "", []):
                result[str(key)] = "[REDACTED_PUBLIC_PHONE]"
            else:
                result[str(key)] = redact_direct_phones(item)
        return result
    if isinstance(value, list):
        return [redact_direct_phones(item) for item in value]
    return value


def call_tianditu(operation: str, parameters: Mapping[str, Any], timeout: int, max_bytes: int) -> tuple[Any, dict[str, Any]]:
    post = build_post_str(operation, parameters)
    query = urllib.parse.urlencode(
        {
            "postStr": json.dumps(post, ensure_ascii=False, separators=(",", ":")),
            "type": "query",
            "tk": provider_key(),
        }
    )
    request = urllib.request.Request(
        f"{ENDPOINT}?{query}",
        headers={"Accept": "application/json", "User-Agent": "gpts-evidence-data-center-tianditu/1"},
        method="GET",
    )
    http_status, raw, content_type = read_response(request, timeout, max_bytes)
    try:
        payload = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Tianditu upstream returned invalid JSON") from exc
    if not isinstance(payload, Mapping):
        raise RuntimeError("Tianditu upstream JSON root must be an object")
    code, description = business_status(payload)
    if code is not None and code != "1000":
        raise RuntimeError(f"Tianditu business status {code}: {description or 'request failed'}")
    redacted = redact_direct_phones(dict(payload))
    result_count: int | None = None
    try:
        result_count = int(payload.get("count")) if payload.get("count") is not None else None
    except (TypeError, ValueError):
        result_count = None
    return redacted, {
        "http_status": http_status,
        "business_status": code,
        "content_type": content_type,
        "request_origin": "api.tianditu.gov.cn",
        "request_path": "/v2/search",
        "query_type": post["queryType"],
        "credential_mode": "query-token",
        "credential_secret_name": SECRET_ENV,
        "upstream_called": True,
        "result_count": result_count,
        "direct_phone_fields_redacted": True,
    }


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket.get("acceptance") or {})
    timeout = bounded_int(acceptance.get("timeout_seconds"), default=45, minimum=5, maximum=60, name="timeout_seconds")
    max_bytes = bounded_int(acceptance.get("max_response_bytes"), default=1_000_000, minimum=1024, maximum=3_000_000, name="max_response_bytes")
    started = time.perf_counter()
    started_at = utc_now()
    status = "API_TIANDITU_FAILED"
    data: Any = None
    metadata: dict[str, Any] = {}
    failure: dict[str, Any] | None = None
    try:
        if operation == "catalog-capabilities":
            data = catalog_provider()
            metadata = {
                "source": "repository-catalog",
                "http_status": None,
                "upstream_called": False,
                "credential_mode": "none",
                "direct_phone_fields_redacted": True,
            }
        else:
            data, metadata = call_tianditu(operation, parameters, timeout, max_bytes)
        status = "API_TIANDITU_COMPLETED"
    except (RuntimeError, ValueError, urllib.error.URLError) as exc:
        failure = {"code": "TIANDITU_UPSTREAM_ERROR", "message": str(exc)}
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    snapshot = {
        "schema_version": "tianditu-result-v1",
        "status": status,
        "task_id": str(ticket["task_id"]),
        "provider": "tianditu",
        "operation": operation,
        "started_at": started_at,
        "completed_at": utc_now(),
        "elapsed_ms": elapsed_ms,
        "data": data,
        "metadata": metadata,
        "failure": failure,
        "ticket_sha256": canonical_sha(ticket),
        "secret_values_exposed": False,
        "model_calls": 0,
    }
    snapshot["snapshot_sha256"] = canonical_sha(snapshot)
    write_json(output_dir / "result.json", snapshot)
    write_output("status", status)
    write_output("snapshot_sha256", snapshot["snapshot_sha256"])
    return 0 if status == "API_TIANDITU_COMPLETED" else 1


def render(output_dir: Path, phase: str, artifact_url: str = "") -> int:
    if phase in {"accepted", "rejected"}:
        status = load_json(output_dir / "ticket-status.json")
        if phase == "accepted":
            print("## API_TIANDITU_ACCEPTED\n")
            print(f"- Task ID: `{status['task_id']}`")
            print(f"- Operation: `{status['operation']}`")
            print(f"- Ticket SHA256: `{status['ticket_sha256']}`")
            print("- Model calls: `0`")
        else:
            print("## API_TIANDITU_REJECTED\n")
            print(f"- Reason: {status['reason'] or 'invalid ticket'}")
            print("- Model calls: `0`")
        return 0
    result = load_json(output_dir / "result.json")
    print(f"## {result['status']}\n")
    print(f"- Task ID: `{result['task_id']}`")
    print("- Provider: `tianditu`")
    print(f"- Operation: `{result['operation']}`")
    print(f"- Upstream called: `{str(bool(result['metadata'].get('upstream_called'))).lower()}`")
    print(f"- Snapshot SHA256: `{result['snapshot_sha256']}`")
    if artifact_url:
        print(f"- Artifact: {artifact_url}")
    print("- Secret values exposed: `false`")
    print("- Model calls: `0`")
    if result.get("failure"):
        print(f"- Error code: `{result['failure']['code']}`")
        print(f"- Message: {result['failure']['message']}")
    elif result.get("data") is not None:
        preview = json.dumps(result["data"], ensure_ascii=False, indent=2)
        if len(preview) > 6000:
            preview = preview[:6000] + "\n... [truncated; see Artifact]"
        print("\n```json")
        print(preview)
        print("```")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--event-path", required=True)
    prepare_parser.add_argument("--output-dir", required=True)
    execute_parser = subparsers.add_parser("execute")
    execute_parser.add_argument("--ticket", required=True)
    execute_parser.add_argument("--output-dir", required=True)
    render_parser = subparsers.add_parser("render")
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
