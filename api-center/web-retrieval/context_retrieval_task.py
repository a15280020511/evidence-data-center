#!/usr/bin/env python3
"""Bounded, read-only Tavily and Firecrawl execution for public web context."""
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
SCHEMA_PATH = HERE / "context-ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"
TAVILY_API_KEY_ENV = "TAVILY_API_KEY"
FIRECRAWL_API_KEY_ENV = "FIRECRAWL_API_KEY"
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
    "catalog-capabilities": {"tavily", "firecrawl"},
    "search": {"tavily", "firecrawl"},
    "extract": {"tavily"},
    "map": {"tavily", "firecrawl"},
    "crawl": {"tavily"},
    "scrape": {"firecrawl"},
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
    result: dict[tuple[str, str], Mapping[str, Any]] = {}
    for provider in load_json(CATALOG_PATH)["providers"]:
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
    contract = _catalog_operations().get((provider, operation))
    if contract is None:
        raise ValueError(f"unsupported provider operation: {provider}/{operation}")
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
        if not title.startswith("[api-context]"):
            raise ValueError("issue title must start with [api-context]")
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
        "schema_version": "context-retrieval-ticket-status-v1",
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


def _optional_text(value: Any, name: str, maximum: int) -> str:
    text = str(value or "").strip()
    if len(text) > maximum:
        raise ValueError(f"{name} must contain at most {maximum} characters")
    return text


def _bounded_strings(
    value: Any,
    *,
    name: str,
    maximum_items: int,
    maximum_length: int,
) -> list[str]:
    if value in (None, ""):
        return []
    if not isinstance(value, list):
        raise ValueError(f"{name} must be an array")
    if len(value) > maximum_items:
        raise ValueError(f"{name} may contain at most {maximum_items} values")
    result: list[str] = []
    for item in value:
        text = _required_text(item, name, maximum_length)
        if text not in result:
            result.append(text)
    return result


def _is_global_ip(address: str) -> bool:
    return bool(ipaddress.ip_address(address).is_global)


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
    if not resolved or any(not _is_global_ip(address) for address in resolved):
        raise ValueError("url hostname does not resolve exclusively to public IPs")
    return urllib.parse.urlunsplit(
        ("https", parsed.netloc, parsed.path or "/", parsed.query, "")
    )


def _provider_key(provider: str) -> tuple[str, str]:
    if provider == "tavily":
        name = TAVILY_API_KEY_ENV
    elif provider == "firecrawl":
        name = FIRECRAWL_API_KEY_ENV
    else:
        raise ValueError(f"unsupported provider: {provider}")
    key = str(os.getenv(name) or "").strip()
    if not key:
        raise RuntimeError(f"missing repository Secret {name}")
    return name, key


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
        content_type = str(exc.headers.get("Content-Type") or "") if exc.headers else ""
    if len(raw) > max_bytes:
        raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
    if not 200 <= status < 300:
        message = raw[:1000].decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"upstream HTTP {status}: {message}")
    return status, raw, content_type


def _post_json(
    url: str,
    body: Mapping[str, Any],
    *,
    key: str,
    timeout: int,
    max_bytes: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    request = urllib.request.Request(
        url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "gpts-evidence-data-center-context-retrieval/1",
        },
        method="POST",
    )
    status, raw, content_type = _read_response(request, timeout, max_bytes)
    try:
        payload = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("upstream returned invalid JSON") from exc
    if not isinstance(payload, Mapping):
        raise RuntimeError("upstream JSON root must be an object")
    return dict(payload), {
        "http_status": status,
        "content_type": content_type,
        "request_origin": urllib.parse.urlsplit(url).netloc,
        "request_path": urllib.parse.urlsplit(url).path,
        "credential_mode": "api-key",
        "upstream_called": True,
    }


def _tavily_search(parameters: Mapping[str, Any], timeout: int, max_bytes: int) -> tuple[Any, dict[str, Any]]:
    query = _required_text(parameters.get("query"), "query", 1000)
    depth = str(parameters.get("search_depth") or "basic")
    if depth not in {"basic", "fast", "ultra-fast", "advanced"}:
        raise ValueError("search_depth is not allowed")
    topic = str(parameters.get("topic") or "general")
    if topic not in {"general", "news", "finance"}:
        raise ValueError("topic is not allowed")
    body: dict[str, Any] = {
        "query": query,
        "search_depth": depth,
        "topic": topic,
        "max_results": _bounded_int(parameters.get("max_results"), default=5, minimum=1, maximum=10, name="max_results"),
        "include_answer": False,
        "include_raw_content": bool(parameters.get("include_raw_content", False)),
        "include_images": False,
        "auto_parameters": False,
    }
    time_range = str(parameters.get("time_range") or "")
    if time_range:
        if time_range not in {"day", "week", "month", "year"}:
            raise ValueError("time_range is not allowed")
        body["time_range"] = time_range
    include_domains = _bounded_strings(parameters.get("include_domains"), name="include_domains", maximum_items=20, maximum_length=253)
    exclude_domains = _bounded_strings(parameters.get("exclude_domains"), name="exclude_domains", maximum_items=20, maximum_length=253)
    if include_domains:
        body["include_domains"] = include_domains
    if exclude_domains:
        body["exclude_domains"] = exclude_domains
    country = _optional_text(parameters.get("country"), "country", 64)
    if country:
        body["country"] = country.casefold()
    _, key = _provider_key("tavily")
    payload, metadata = _post_json("https://api.tavily.com/search", body, key=key, timeout=timeout, max_bytes=max_bytes)
    if not isinstance(payload.get("results"), list):
        raise RuntimeError("Tavily search response has no results array")
    metadata["result_count"] = len(payload["results"])
    metadata["usage"] = payload.get("usage")
    return payload, metadata


def _tavily_extract(parameters: Mapping[str, Any], timeout: int, max_bytes: int) -> tuple[Any, dict[str, Any]]:
    raw_urls = parameters.get("urls")
    if not isinstance(raw_urls, list) or not 1 <= len(raw_urls) <= 5:
        raise ValueError("urls must contain 1 to 5 values")
    urls = [validate_public_https_url(item) for item in raw_urls]
    depth = str(parameters.get("extract_depth") or "basic")
    if depth not in {"basic", "advanced"}:
        raise ValueError("extract_depth is not allowed")
    output_format = str(parameters.get("format") or "markdown")
    if output_format not in {"markdown", "text"}:
        raise ValueError("format is not allowed")
    body: dict[str, Any] = {
        "urls": urls,
        "extract_depth": depth,
        "format": output_format,
        "include_images": bool(parameters.get("include_images", False)),
        "include_favicon": False,
        "include_usage": True,
        "timeout": min(timeout, 60),
    }
    query = _optional_text(parameters.get("query"), "query", 1000)
    if query:
        body["query"] = query
        body["chunks_per_source"] = 3
    _, key = _provider_key("tavily")
    payload, metadata = _post_json("https://api.tavily.com/extract", body, key=key, timeout=timeout, max_bytes=max_bytes)
    if not isinstance(payload.get("results"), list):
        raise RuntimeError("Tavily extract response has no results array")
    metadata["result_count"] = len(payload["results"])
    metadata["requested_url_count"] = len(urls)
    metadata["usage"] = payload.get("usage")
    return payload, metadata


def _tavily_site(operation: str, parameters: Mapping[str, Any], timeout: int, max_bytes: int) -> tuple[Any, dict[str, Any]]:
    url = validate_public_https_url(parameters.get("url"))
    body: dict[str, Any] = {
        "url": url,
        "max_depth": _bounded_int(parameters.get("max_depth"), default=1, minimum=1, maximum=2 if operation == "crawl" else 3, name="max_depth"),
        "max_breadth": _bounded_int(parameters.get("max_breadth"), default=10, minimum=1, maximum=20, name="max_breadth"),
        "limit": _bounded_int(parameters.get("limit"), default=10, minimum=1, maximum=20 if operation == "crawl" else 50, name="limit"),
        "allow_external": False,
        "include_images": False,
        "timeout": min(max(timeout, 10), 150),
    }
    instructions = _optional_text(parameters.get("instructions"), "instructions", 500)
    if instructions:
        body["instructions"] = instructions
        body["chunks_per_source"] = 3
    for field in ("select_paths", "exclude_paths"):
        values = _bounded_strings(parameters.get(field), name=field, maximum_items=10, maximum_length=200)
        if values:
            body[field] = values
    if operation == "crawl":
        depth = str(parameters.get("extract_depth") or "basic")
        output_format = str(parameters.get("format") or "markdown")
        if depth not in {"basic", "advanced"}:
            raise ValueError("extract_depth is not allowed")
        if output_format not in {"markdown", "text"}:
            raise ValueError("format is not allowed")
        body["extract_depth"] = depth
        body["format"] = output_format
    _, key = _provider_key("tavily")
    payload, metadata = _post_json(f"https://api.tavily.com/{operation}", body, key=key, timeout=timeout, max_bytes=max_bytes)
    if not isinstance(payload.get("results"), list):
        raise RuntimeError(f"Tavily {operation} response has no results array")
    metadata["result_count"] = len(payload["results"])
    metadata["usage"] = payload.get("usage")
    return payload, metadata


def _firecrawl_search(parameters: Mapping[str, Any], timeout: int, max_bytes: int) -> tuple[Any, dict[str, Any]]:
    query = _required_text(parameters.get("query"), "query", 1000)
    limit = _bounded_int(parameters.get("limit"), default=5, minimum=1, maximum=10, name="limit")
    body: dict[str, Any] = {
        "query": query,
        "limit": limit,
        "sources": ["web"],
        "timeout": min(timeout * 1000, 60000),
        "ignoreInvalidURLs": True,
    }
    country = _optional_text(parameters.get("country"), "country", 2).upper()
    if country:
        if len(country) != 2 or not country.isalpha():
            raise ValueError("country must be a two-letter code")
        body["country"] = country
    time_range = str(parameters.get("time_range") or "")
    if time_range:
        mapping = {"day": "qdr:d", "week": "qdr:w", "month": "qdr:m", "year": "qdr:y"}
        if time_range not in mapping:
            raise ValueError("time_range is not allowed")
        body["tbs"] = mapping[time_range]
    if bool(parameters.get("include_markdown", False)):
        body["scrapeOptions"] = {
            "formats": ["markdown"],
            "onlyMainContent": True,
            "removeBase64Images": True,
            "blockAds": True,
            "timeout": min(timeout * 1000, 60000),
            "zeroDataRetention": True,
        }
    _, key = _provider_key("firecrawl")
    payload, metadata = _post_json("https://api.firecrawl.dev/v2/search", body, key=key, timeout=timeout, max_bytes=max_bytes)
    if payload.get("success") is not True:
        raise RuntimeError(f"Firecrawl search business failure: {payload.get('error') or 'success=false'}")
    data = payload.get("data")
    if not isinstance(data, Mapping) or not isinstance(data.get("web"), list):
        raise RuntimeError("Firecrawl search response has no data.web array")
    metadata["result_count"] = len(data["web"])
    return payload, metadata


def _firecrawl_scrape(parameters: Mapping[str, Any], timeout: int, max_bytes: int) -> tuple[Any, dict[str, Any]]:
    url = validate_public_https_url(parameters.get("url"))
    formats = _bounded_strings(parameters.get("formats") or ["markdown"], name="formats", maximum_items=2, maximum_length=20)
    if not formats or any(item not in {"markdown", "links"} for item in formats):
        raise ValueError("formats may contain only markdown and links")
    timeout_ms = _bounded_int(parameters.get("timeout_ms"), default=min(timeout * 1000, 60000), minimum=1000, maximum=60000, name="timeout_ms")
    body = {
        "url": url,
        "formats": formats,
        "onlyMainContent": bool(parameters.get("only_main_content", True)),
        "maxAge": _bounded_int(parameters.get("max_age_ms"), default=172800000, minimum=0, maximum=604800000, name="max_age_ms"),
        "timeout": timeout_ms,
        "removeBase64Images": True,
        "blockAds": True,
        "skipTlsVerification": False,
        "proxy": "auto",
        "zeroDataRetention": True,
    }
    _, key = _provider_key("firecrawl")
    payload, metadata = _post_json("https://api.firecrawl.dev/v2/scrape", body, key=key, timeout=timeout, max_bytes=max_bytes)
    if payload.get("success") is not True or not isinstance(payload.get("data"), Mapping):
        raise RuntimeError(f"Firecrawl scrape business failure: {payload.get('error') or 'invalid data'}")
    metadata["target_origin"] = urllib.parse.urlsplit(url).netloc
    return payload, metadata


def _firecrawl_map(parameters: Mapping[str, Any], timeout: int, max_bytes: int) -> tuple[Any, dict[str, Any]]:
    url = validate_public_https_url(parameters.get("url"))
    sitemap = str(parameters.get("sitemap") or "include")
    if sitemap not in {"skip", "include", "only"}:
        raise ValueError("sitemap is not allowed")
    body: dict[str, Any] = {
        "url": url,
        "sitemap": sitemap,
        "includeSubdomains": bool(parameters.get("include_subdomains", False)),
        "ignoreQueryParameters": bool(parameters.get("ignore_query_parameters", True)),
        "ignoreCache": False,
        "limit": _bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=100, name="limit"),
        "timeout": min(timeout * 1000, 60000),
    }
    search = _optional_text(parameters.get("search"), "search", 500)
    if search:
        body["search"] = search
    _, key = _provider_key("firecrawl")
    payload, metadata = _post_json("https://api.firecrawl.dev/v2/map", body, key=key, timeout=timeout, max_bytes=max_bytes)
    if payload.get("success") is not True or not isinstance(payload.get("links"), list):
        raise RuntimeError(f"Firecrawl map business failure: {payload.get('error') or 'invalid links'}")
    metadata["result_count"] = len(payload["links"])
    metadata["target_origin"] = urllib.parse.urlsplit(url).netloc
    return payload, metadata


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket)
    provider = str(ticket["provider"])
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket.get("acceptance") or {})
    timeout = _bounded_int(acceptance.get("timeout_seconds"), default=45, minimum=5, maximum=150, name="timeout_seconds")
    max_bytes = _bounded_int(acceptance.get("max_response_bytes"), default=1_000_000, minimum=1024, maximum=5_000_000, name="max_response_bytes")
    started = time.perf_counter()
    started_at = utc_now()
    status = "API_CONTEXT_FAILED"
    data: Any = None
    metadata: dict[str, Any] = {}
    failure: dict[str, Any] | None = None
    credential_secret_name: str | None = None
    try:
        if operation == "catalog-capabilities":
            data = next(row for row in load_json(CATALOG_PATH)["providers"] if row["provider_id"] == provider)
            metadata = {"source": "repository-catalog", "http_status": None, "upstream_called": False, "credential_mode": "none"}
        else:
            credential_secret_name = TAVILY_API_KEY_ENV if provider == "tavily" else FIRECRAWL_API_KEY_ENV
            if provider == "tavily" and operation == "search":
                data, metadata = _tavily_search(parameters, timeout, max_bytes)
            elif provider == "tavily" and operation == "extract":
                data, metadata = _tavily_extract(parameters, timeout, max_bytes)
            elif provider == "tavily" and operation in {"map", "crawl"}:
                data, metadata = _tavily_site(operation, parameters, timeout, max_bytes)
            elif provider == "firecrawl" and operation == "search":
                data, metadata = _firecrawl_search(parameters, timeout, max_bytes)
            elif provider == "firecrawl" and operation == "scrape":
                data, metadata = _firecrawl_scrape(parameters, timeout, max_bytes)
            elif provider == "firecrawl" and operation == "map":
                data, metadata = _firecrawl_map(parameters, timeout, max_bytes)
            else:
                raise ValueError(f"unsupported provider operation: {provider}/{operation}")
        status = "API_CONTEXT_COMPLETED"
    except RuntimeError as exc:
        message = str(exc)
        status = "API_CONTEXT_BLOCKED" if message.startswith("missing repository Secret") else "API_CONTEXT_UPSTREAM_FAILED"
        failure = {"code": status, "stage": "execute", "message": message, "retryable": False}
    except ValueError as exc:
        status = "API_CONTEXT_REJECTED"
        failure = {"code": status, "stage": "validate", "message": str(exc), "retryable": False}
    result = {
        "schema_version": "context-retrieval-result-v1",
        "status": status,
        "task_id": str(ticket["task_id"]),
        "provider": provider,
        "operation": operation,
        "started_at": started_at,
        "completed_at": utc_now(),
        "duration_ms": round((time.perf_counter() - started) * 1000, 3),
        "data": data,
        "metadata": metadata,
        "failure": failure,
        "credential_secret_name": credential_secret_name,
        "secret_values_exposed": False,
        "model_calls": 0,
        "ticket_sha256": canonical_sha(ticket),
    }
    result["snapshot_sha256"] = canonical_sha({key: value for key, value in result.items() if key != "snapshot_sha256"})
    write_json(output_dir / "result.json", result)
    write_json(output_dir / "api-diagnostics.json", {
        "status": status,
        "failure": failure,
        "provider": provider,
        "operation": operation,
        "upstream_called": bool(metadata.get("upstream_called")),
        "secret_values_exposed": False,
    })
    write_output("status", status)
    return 0 if status == "API_CONTEXT_COMPLETED" else 1


def _compact_json(value: Any, limit: int = 12000) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)
    return text if len(text) <= limit else text[:limit] + "\n... [truncated; full result is in the Artifact]"


def render(output_dir: Path, phase: str, artifact_url: str = "") -> int:
    ticket_status = load_json(output_dir / "ticket-status.json")
    if phase == "accepted":
        print("## API_CONTEXT_ACCEPTED")
        print()
        print(f"- Task ID: `{ticket_status.get('task_id', '')}`")
        print(f"- Provider: `{ticket_status.get('provider', '')}`")
        print(f"- Operation: `{ticket_status.get('operation', '')}`")
        print(f"- Ticket SHA256: `{ticket_status.get('ticket_sha256', '')}`")
        print("- Model calls: `0`")
        return 0
    if phase == "rejected":
        print("## API_CONTEXT_REJECTED")
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
    render_parser.add_argument("--phase", choices=("accepted", "rejected", "completed"), required=True)
    render_parser.add_argument("--artifact-url", default="")
    args = parser.parse_args()
    if args.command == "prepare":
        return prepare(args.event_path, args.output_dir)
    if args.command == "execute":
        return execute(args.ticket, args.output_dir)
    return render(args.output_dir, args.phase, args.artifact_url)


if __name__ == "__main__":
    raise SystemExit(main())
