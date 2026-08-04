#!/usr/bin/env python3
"""Bounded, read-only TickFlow and SerpAPI execution control plane."""
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
TICKFLOW_API_KEY_ENV = "TICKFLOW_API_KEY"
SERPAPI_API_KEY_ENV = "SERPAPI_API_KEY"
PROVIDER_OPERATIONS = {
    "tickflow": {"catalog-capabilities", "quotes", "klines", "intraday-klines", "instruments"},
    "serpapi": {"catalog-capabilities", "google-search", "google-news", "google-scholar"},
}
SYMBOL_RE = re.compile(r"^[A-Za-z0-9._-]{3,32}$")
PERIODS = {"1m", "5m", "10m", "15m", "30m", "60m", "1d", "1w", "1M", "1Q", "1Y"}
INTRADAY_PERIODS = {"1m", "5m", "10m", "15m", "30m", "60m"}
ADJUSTMENTS = {"forward", "backward", "forward_additive", "backward_additive", "none"}
TIME_RANGES = {"day": "d", "week": "w", "month": "m", "year": "y"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def write_output(name: str, value: Any) -> None:
    target = os.getenv("GITHUB_OUTPUT")
    if not target:
        return
    text = str(value).replace("\n", " ").replace("\r", " ")
    with open(target, "a", encoding="utf-8") as handle:
        handle.write(f"{name}={text}\n")


def catalog_provider(provider: str) -> Mapping[str, Any]:
    for row in load_json(CATALOG_PATH)["providers"]:
        if row["provider_id"] == provider:
            return row
    raise ValueError(f"unsupported provider: {provider}")


def catalog_operation(provider: str, operation: str) -> Mapping[str, Any]:
    for row in catalog_provider(provider)["operations"]:
        if row["operation_id"] == operation:
            return row
    raise ValueError(f"unsupported provider operation: {provider}/{operation}")


def validate_ticket(ticket: Mapping[str, Any]) -> None:
    errors = sorted(Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(ticket), key=lambda item: list(item.absolute_path))
    if errors:
        rendered = "; ".join(
            f"{'.'.join(str(x) for x in item.absolute_path) or '$'}: {item.message}"
            for item in errors[:20]
        )
        raise ValueError(rendered)
    provider = str(ticket["provider"])
    operation = str(ticket["operation"])
    if operation not in PROVIDER_OPERATIONS.get(provider, set()):
        raise ValueError(f"operation {operation} is not available for provider {provider}")
    parameter_schema = catalog_operation(provider, operation).get("parameter_schema")
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


def expected_prefix(provider: str) -> str:
    return "[api-tickflow]" if provider == "tickflow" else "[api-serpapi]"


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
        if not title.startswith(expected_prefix(str(parsed["provider"]))):
            raise ValueError(f"issue title must start with {expected_prefix(str(parsed['provider']))}")
        ticket = parsed
        accepted = True
        write_json(output_dir / "ticket.json", ticket)
    except (json.JSONDecodeError, ValueError) as exc:
        reason = str(exc)
    status = {
        "schema_version": "market-search-ticket-status-v1",
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


def optional_country_code(value: Any, name: str) -> str:
    text = str(value or "").strip().lower()
    if text and (len(text) != 2 or not text.isalpha()):
        raise ValueError(f"{name} must be a two-letter country code")
    return text


def optional_language_code(value: Any, name: str) -> str:
    text = str(value or "").strip().lower()
    if text and not re.fullmatch(r"[a-z]{2}(?:-[a-z]{2})?", text):
        raise ValueError(f"{name} must be a supported language code")
    return text


def symbols(value: Any, *, maximum: int) -> list[str]:
    if not isinstance(value, list) or not 1 <= len(value) <= maximum:
        raise ValueError(f"symbols must contain 1 to {maximum} values")
    result: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if not SYMBOL_RE.fullmatch(text):
            raise ValueError(f"invalid symbol: {text}")
        if text not in result:
            result.append(text)
    return result


def provider_key(provider: str) -> tuple[str, str]:
    name = TICKFLOW_API_KEY_ENV if provider == "tickflow" else SERPAPI_API_KEY_ENV
    key = str(os.getenv(name) or "").strip()
    if not key:
        raise RuntimeError(f"missing repository Secret {name}")
    return name, key


def scrub(value: Any, secrets: list[str]) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): scrub(item, secrets)
            for key, item in value.items()
            if str(key).casefold() not in {"api_key", "x-api-key", "authorization"}
        }
    if isinstance(value, list):
        return [scrub(item, secrets) for item in value]
    if isinstance(value, str):
        text = value
        for secret in secrets:
            if secret:
                text = text.replace(secret, "[REDACTED]")
        return text
    return value


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
        raise RuntimeError(f"upstream connection failed: {type(exc.reason).__name__}") from exc
    if len(raw) > max_bytes:
        raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
    if not 200 <= status < 300:
        message = raw[:1000].decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"upstream HTTP {status}: {message}")
    return status, raw, content_type


def get_json(url: str, query: Mapping[str, Any], headers: Mapping[str, str], *, timeout: int, max_bytes: int) -> tuple[dict[str, Any], dict[str, Any]]:
    encoded = urllib.parse.urlencode(query, doseq=True)
    request_url = f"{url}?{encoded}" if encoded else url
    request = urllib.request.Request(
        request_url,
        headers={"Accept": "application/json", "User-Agent": "gpts-evidence-data-center-market-search/1", **dict(headers)},
        method="GET",
    )
    status, raw, content_type = read_response(request, timeout, max_bytes)
    try:
        payload = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("upstream returned invalid JSON") from exc
    if not isinstance(payload, Mapping):
        raise RuntimeError("upstream JSON root must be an object")
    parsed = urllib.parse.urlsplit(url)
    return dict(payload), {
        "http_status": status,
        "content_type": content_type,
        "request_origin": parsed.netloc,
        "request_path": parsed.path,
        "credential_mode": "api-key",
        "upstream_called": True,
    }


def tickflow_query(operation: str, parameters: Mapping[str, Any], timeout: int, max_bytes: int) -> tuple[Any, dict[str, Any], str]:
    _, key = provider_key("tickflow")
    headers = {"x-api-key": key}
    if operation == "quotes":
        query: dict[str, Any] = {}
        if parameters.get("symbols"):
            query["symbols"] = ",".join(symbols(parameters["symbols"], maximum=100))
        if parameters.get("universes"):
            query["universes"] = ",".join(str(item) for item in parameters["universes"])
        endpoint = "https://api.tickflow.org/v1/quotes"
    elif operation == "klines":
        period = str(parameters.get("period") or "1d")
        if period not in PERIODS:
            raise ValueError("period is not allowed")
        query = {
            "symbol": required_text(parameters.get("symbol"), "symbol", 32),
            "period": period,
            "count": bounded_int(parameters.get("count"), default=100, minimum=1, maximum=10000, name="count"),
        }
        for field in ("start_time", "end_time"):
            if parameters.get(field) is not None:
                query[field] = bounded_int(parameters[field], default=0, minimum=0, maximum=9999999999999, name=field)
        adjust = str(parameters.get("adjust") or "none")
        if adjust not in ADJUSTMENTS:
            raise ValueError("adjust is not allowed")
        query["adjust"] = adjust
        endpoint = "https://api.tickflow.org/v1/klines"
    elif operation == "intraday-klines":
        period = str(parameters.get("period") or "1m")
        if period not in INTRADAY_PERIODS:
            raise ValueError("period is not allowed")
        query = {
            "symbol": required_text(parameters.get("symbol"), "symbol", 32),
            "period": period,
            "count": bounded_int(parameters.get("count"), default=100, minimum=1, maximum=2000, name="count"),
        }
        endpoint = "https://api.tickflow.org/v1/klines/intraday"
    elif operation == "instruments":
        query = {"symbols": ",".join(symbols(parameters.get("symbols"), maximum=100))}
        endpoint = "https://api.tickflow.org/v1/instruments"
    else:
        raise ValueError(f"unsupported TickFlow operation: {operation}")
    payload, metadata = get_json(endpoint, query, headers, timeout=timeout, max_bytes=max_bytes)
    if "data" not in payload:
        raise RuntimeError("TickFlow response has no data field")
    return scrub(payload, [key]), metadata, TICKFLOW_API_KEY_ENV


def serpapi_query(operation: str, parameters: Mapping[str, Any], timeout: int, max_bytes: int) -> tuple[Any, dict[str, Any], str]:
    _, key = provider_key("serpapi")
    query_text = required_text(parameters.get("query"), "query", 1000)
    engines = {"google-search": "google", "google-news": "google_news", "google-scholar": "google_scholar"}
    query: dict[str, Any] = {
        "engine": engines[operation],
        "q": query_text,
        "api_key": key,
        "output": "json",
        "async": "false",
    }
    hl = optional_language_code(parameters.get("hl"), "hl")
    if hl:
        query["hl"] = hl
    if parameters.get("start") is not None:
        query["start"] = bounded_int(parameters["start"], default=0, minimum=0, maximum=90, name="start")
    if operation == "google-search":
        location = str(parameters.get("location") or "").strip()
        if location:
            if len(location) > 200:
                raise ValueError("location is too long")
            query["location"] = location
        gl = optional_country_code(parameters.get("gl"), "gl")
        if gl:
            query["gl"] = gl
        device = str(parameters.get("device") or "desktop")
        safe = str(parameters.get("safe") or "active")
        if device not in {"desktop", "tablet", "mobile"}:
            raise ValueError("device is not allowed")
        if safe not in {"active", "off"}:
            raise ValueError("safe is not allowed")
        query["device"] = device
        query["safe"] = safe
        time_range = str(parameters.get("time_range") or "")
        if time_range:
            query["tbs"] = f"qdr:{TIME_RANGES[time_range]}"
    elif operation == "google-news":
        gl = optional_country_code(parameters.get("gl"), "gl")
        if gl:
            query["gl"] = gl
        time_range = str(parameters.get("time_range") or "")
        if time_range:
            query["q"] = f"{query_text} when:1{TIME_RANGES[time_range]}"
    elif operation == "google-scholar":
        for source, target in (("year_low", "as_ylo"), ("year_high", "as_yhi")):
            if parameters.get(source) is not None:
                query[target] = bounded_int(parameters[source], default=1900, minimum=1900, maximum=2100, name=source)
        if "as_ylo" in query and "as_yhi" in query and query["as_ylo"] > query["as_yhi"]:
            raise ValueError("year_low must not exceed year_high")
        if bool(parameters.get("sort_by_date", False)):
            query["scisbd"] = "1"
    payload, metadata = get_json("https://serpapi.com/search", query, {}, timeout=timeout, max_bytes=max_bytes)
    if payload.get("error"):
        raise RuntimeError(f"SerpAPI business failure: {str(payload['error'])[:500]}")
    search_metadata = payload.get("search_metadata")
    if isinstance(search_metadata, Mapping) and str(search_metadata.get("status") or "").casefold() == "error":
        raise RuntimeError("SerpAPI search_metadata.status=Error")
    return scrub(payload, [key]), metadata, SERPAPI_API_KEY_ENV


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket)
    provider = str(ticket["provider"])
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket.get("acceptance") or {})
    timeout = bounded_int(acceptance.get("timeout_seconds"), default=45, minimum=5, maximum=60, name="timeout_seconds")
    max_bytes = bounded_int(acceptance.get("max_response_bytes"), default=1_000_000, minimum=1024, maximum=3_000_000, name="max_response_bytes")
    started_at = utc_now()
    started = time.perf_counter()
    status = "API_MARKET_SEARCH_FAILED"
    data: Any = None
    metadata: dict[str, Any] = {}
    failure: dict[str, Any] | None = None
    credential_secret_name: str | None = None
    try:
        if operation == "catalog-capabilities":
            data = dict(catalog_provider(provider))
            metadata = {"source": "repository-catalog", "http_status": None, "upstream_called": False, "credential_mode": "none"}
        elif provider == "tickflow":
            data, metadata, credential_secret_name = tickflow_query(operation, parameters, timeout, max_bytes)
        else:
            data, metadata, credential_secret_name = serpapi_query(operation, parameters, timeout, max_bytes)
        status = "API_MARKET_SEARCH_COMPLETED"
        write_json(output_dir / "result.json", data)
    except (ValueError, RuntimeError) as exc:
        failure = {"error_code": "MARKET_SEARCH_UPSTREAM_ERROR", "message": str(exc)[:2000], "exception_type": type(exc).__name__}
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    execution_status = {
        "schema_version": "market-search-execution-status-v1",
        "status": status,
        "task_id": str(ticket["task_id"]),
        "provider": provider,
        "operation": operation,
        "started_at": started_at,
        "completed_at": utc_now(),
        "elapsed_ms": elapsed_ms,
        "credential_secret_name": credential_secret_name,
        "secret_values_exposed": False,
        "model_calls": 0,
        "metadata": metadata,
        "failure": failure,
        "result_sha256": canonical_sha(data) if status == "API_MARKET_SEARCH_COMPLETED" else None,
    }
    write_json(output_dir / "execution-status.json", execution_status)
    write_output("status", status)
    return 0 if status == "API_MARKET_SEARCH_COMPLETED" else 1


def render(output_dir: Path, phase: str, artifact_url: str = "") -> int:
    ticket_status = load_json(output_dir / "ticket-status.json")
    if phase == "accepted":
        print("## API_MARKET_SEARCH_ACCEPTED\n")
        print(f"- Task ID: `{ticket_status.get('task_id', '')}`")
        print(f"- Provider: `{ticket_status.get('provider', '')}`")
        print(f"- Operation: `{ticket_status.get('operation', '')}`")
        print(f"- Ticket SHA256: `{ticket_status.get('ticket_sha256', '')}`")
        print("- Model calls: `0`")
        return 0
    if phase == "rejected":
        print("## API_MARKET_SEARCH_REJECTED\n")
        print(f"- Reason: {ticket_status.get('reason') or 'ticket rejected'}")
        print("- Secret values exposed: `false`")
        print("- Model calls: `0`")
        return 0
    execution = load_json(output_dir / "execution-status.json")
    print(f"## {execution['status']}\n")
    print(f"- Task ID: `{execution['task_id']}`")
    print(f"- Provider: `{execution['provider']}`")
    print(f"- Operation: `{execution['operation']}`")
    print(f"- Upstream called: `{str(bool(execution['metadata'].get('upstream_called'))).lower()}`")
    print(f"- Credential mode: `{execution['metadata'].get('credential_mode', 'none')}`")
    print(f"- Result SHA256: `{execution.get('result_sha256') or ''}`")
    if artifact_url:
        print(f"- Artifact: {artifact_url}")
    print("- Secret values exposed: `false`")
    print("- Model calls: `0`")
    if execution["status"] == "API_MARKET_SEARCH_COMPLETED" and (output_dir / "result.json").is_file():
        preview = (output_dir / "result.json").read_text(encoding="utf-8")
        if len(preview) > 12000:
            preview = preview[:12000] + "\n... [preview truncated; full result is in Artifact]"
        print("\n```json")
        print(preview.rstrip())
        print("```")
    elif execution.get("failure"):
        print(f"- Error code: `{execution['failure'].get('error_code', '')}`")
        print(f"- Message: {execution['failure'].get('message', '')}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--event-path", type=Path, required=True)
    prepare_parser.add_argument("--output-dir", type=Path, required=True)
    execute_parser = sub.add_parser("execute")
    execute_parser.add_argument("--ticket", type=Path, required=True)
    execute_parser.add_argument("--output-dir", type=Path, required=True)
    render_parser = sub.add_parser("render")
    render_parser.add_argument("--output-dir", type=Path, required=True)
    render_parser.add_argument("--phase", choices=["accepted", "rejected", "completed"], required=True)
    render_parser.add_argument("--artifact-url", default="")
    args = parser.parse_args()
    if args.command == "prepare":
        return prepare(args.event_path, args.output_dir)
    if args.command == "execute":
        return execute(args.ticket, args.output_dir)
    return render(args.output_dir, args.phase, args.artifact_url)


if __name__ == "__main__":
    raise SystemExit(main())
