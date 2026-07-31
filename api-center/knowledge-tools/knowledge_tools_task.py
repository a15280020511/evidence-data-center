#!/usr/bin/env python3
"""Bounded Wolfram|Alpha and LlamaParse execution control plane."""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
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
WOLFRAM_ALPHA_APP_ID_ENV = "WOLFRAM_ALPHA_APP_ID"
LLAMA_CLOUD_API_KEY_ENV = "LLAMA_CLOUD_API_KEY"
PROVIDER_OPERATIONS = {
    "wolfram-alpha": {"catalog-capabilities", "full-results", "short-answer", "llm-result"},
    "llamaparse": {"catalog-capabilities", "parse-public-document", "get-job"},
}
WOLFRAM_UNITS = {"default", "metric", "imperial"}
LLAMA_TIERS = {"fast", "cost_effective", "agentic", "agentic_plus"}
LLAMA_REGIONS = {
    "na": "https://api.cloud.llamaindex.ai",
    "eu": "https://api.cloud.eu.llamaindex.ai",
}
LLAMA_EXPANDS = {
    "text",
    "markdown",
    "items",
    "metadata",
    "job_metadata",
    "text_full",
    "markdown_full",
}
JOB_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")
DATE_VERSION_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DOCUMENT_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".csv",
    ".html", ".htm", ".txt", ".md", ".json", ".rtf", ".png", ".jpg", ".jpeg", ".tif", ".tiff",
}
TERMINAL_JOB_STATUSES = {"COMPLETED", "FAILED", "CANCELLED"}


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
    provider = str(ticket["provider"])
    operation = str(ticket["operation"])
    if operation not in PROVIDER_OPERATIONS.get(provider, set()):
        raise ValueError(f"operation {operation} is not available for provider {provider}")
    parameter_schema = catalog_operation(provider, operation)["parameter_schema"]
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
    prefixes = {
        "wolfram-alpha": "[api-wolfram]",
        "llamaparse": "[api-llamaparse]",
    }
    return prefixes.get(provider, "[api-unsupported]")


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
        prefix = expected_prefix(str(parsed["provider"]))
        if not title.startswith(prefix):
            raise ValueError(f"issue title must start with {prefix}")
        ticket = parsed
        accepted = True
        write_json(output_dir / "ticket.json", ticket)
    except (json.JSONDecodeError, ValueError) as exc:
        reason = str(exc)
    status = {
        "schema_version": "knowledge-tools-ticket-status-v1",
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


def bounded_int(
    value: Any,
    *,
    default: int,
    minimum: int,
    maximum: int,
    name: str,
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


def required_text(value: Any, name: str, maximum: int) -> str:
    text = str(value or "").strip()
    if not text or len(text) > maximum:
        raise ValueError(f"{name} must contain 1 to {maximum} characters")
    return text


def provider_key(provider: str) -> tuple[str, str]:
    names = {
        "wolfram-alpha": WOLFRAM_ALPHA_APP_ID_ENV,
        "llamaparse": LLAMA_CLOUD_API_KEY_ENV,
    }
    name = names[provider]
    key = str(os.getenv(name) or "").strip()
    if not key:
        raise RuntimeError(f"missing repository Secret {name}")
    return name, key


def scrub(value: Any, secrets: list[str]) -> Any:
    blocked_keys = {
        "api_key",
        "appid",
        "authorization",
        "presigned_url",
        "download_url",
        "signed_url",
    }
    if isinstance(value, Mapping):
        return {
            str(key): scrub(item, secrets)
            for key, item in value.items()
            if str(key).casefold() not in blocked_keys
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


def read_response(
    request: urllib.request.Request,
    timeout: int,
    max_bytes: int,
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
    except urllib.error.URLError as exc:
        raise RuntimeError(f"upstream connection failed: {type(exc.reason).__name__}") from exc
    if len(raw) > max_bytes:
        raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
    if not 200 <= status < 300:
        message = raw[:1000].decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"upstream HTTP {status}: {message}")
    return status, raw, content_type


def request_json(
    url: str,
    *,
    method: str,
    headers: Mapping[str, str],
    timeout: int,
    max_bytes: int,
    query: Mapping[str, Any] | None = None,
    body: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    encoded = urllib.parse.urlencode(query or {}, doseq=True)
    request_url = f"{url}?{encoded}" if encoded else url
    payload = None
    request_headers = {
        "Accept": "application/json",
        "User-Agent": "gpts-evidence-data-center-knowledge-tools/1",
        **dict(headers),
    }
    if body is not None:
        payload = json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        request_url,
        data=payload,
        headers=request_headers,
        method=method,
    )
    status, raw, content_type = read_response(request, timeout, max_bytes)
    try:
        parsed_payload = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("upstream returned invalid JSON") from exc
    if not isinstance(parsed_payload, Mapping):
        raise RuntimeError("upstream JSON root must be an object")
    parsed_url = urllib.parse.urlsplit(url)
    return dict(parsed_payload), {
        "http_status": status,
        "content_type": content_type,
        "request_origin": parsed_url.netloc,
        "request_path": parsed_url.path,
        "upstream_called": True,
    }


def request_text(
    url: str,
    query: Mapping[str, Any],
    *,
    timeout: int,
    max_bytes: int,
) -> tuple[str, dict[str, Any]]:
    encoded = urllib.parse.urlencode(query, doseq=True)
    request = urllib.request.Request(
        f"{url}?{encoded}",
        headers={
            "Accept": "text/plain",
            "User-Agent": "gpts-evidence-data-center-knowledge-tools/1",
        },
        method="GET",
    )
    status, raw, content_type = read_response(request, timeout, max_bytes)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError("upstream returned invalid UTF-8 text") from exc
    parsed_url = urllib.parse.urlsplit(url)
    return text.strip(), {
        "http_status": status,
        "content_type": content_type,
        "request_origin": parsed_url.netloc,
        "request_path": parsed_url.path,
        "upstream_called": True,
    }


def wolfram_query(
    operation: str,
    parameters: Mapping[str, Any],
    timeout: int,
    max_bytes: int,
) -> tuple[Any, dict[str, Any], str]:
    _, app_id = provider_key("wolfram-alpha")
    input_text = required_text(parameters.get("input"), "input", 2000)
    units = str(parameters.get("units") or "default")
    if units not in WOLFRAM_UNITS:
        raise ValueError("units is not allowed")
    location = str(parameters.get("location") or "").strip()
    if len(location) > 200:
        raise ValueError("location is too long")
    languagecode = str(parameters.get("languagecode") or "").strip().lower()
    if languagecode and not re.fullmatch(r"[a-z]{2}", languagecode):
        raise ValueError("languagecode must be a two-letter code")
    upstream_timeout = bounded_int(
        parameters.get("upstream_timeout_seconds"),
        default=min(timeout, 15),
        minimum=1,
        maximum=min(timeout, 30),
        name="upstream_timeout_seconds",
    )

    if operation == "full-results":
        query: dict[str, Any] = {
            "appid": app_id,
            "input": input_text,
            "output": "json",
            "format": "plaintext",
            "totaltimeout": upstream_timeout,
        }
        endpoint = "https://api.wolframalpha.com/v2/query"
        if units != "default":
            query["units"] = units
        if location:
            query["location"] = location
        if languagecode:
            query["languagecode"] = languagecode
        payload, metadata = request_json(
            endpoint,
            method="GET",
            headers={},
            timeout=timeout,
            max_bytes=max_bytes,
            query=query,
        )
        query_result = payload.get("queryresult")
        if not isinstance(query_result, Mapping):
            raise RuntimeError("Wolfram|Alpha response has no queryresult object")
        if bool(query_result.get("error")):
            raise RuntimeError("Wolfram|Alpha queryresult.error=true")
        result: Any = scrub(payload, [app_id])
    elif operation in {"short-answer", "llm-result"}:
        if operation == "short-answer":
            endpoint = "https://api.wolframalpha.com/v1/result"
            query = {"appid": app_id, "i": input_text, "timeout": upstream_timeout}
        else:
            endpoint = "https://www.wolframalpha.com/api/v1/llm-api"
            query = {"appid": app_id, "input": input_text, "totaltimeout": upstream_timeout}
        if units != "default":
            query["units"] = units
        if location:
            query["location"] = location
        if languagecode and operation == "llm-result":
            query["languagecode"] = languagecode
        text, metadata = request_text(
            endpoint,
            query,
            timeout=timeout,
            max_bytes=max_bytes,
        )
        if not text:
            raise RuntimeError("Wolfram|Alpha returned an empty result")
        result = {"text": scrub(text, [app_id])}
    else:
        raise ValueError(f"unsupported Wolfram|Alpha operation: {operation}")
    metadata["credential_mode"] = "app-id"
    return result, metadata, WOLFRAM_ALPHA_APP_ID_ENV


def validate_public_document_url(value: Any) -> str:
    text = required_text(value, "source_url", 2000)
    parsed = urllib.parse.urlsplit(text)
    if parsed.scheme.lower() != "https":
        raise ValueError("source_url must use https")
    if parsed.username or parsed.password:
        raise ValueError("source_url credentials are not allowed")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("source_url has an invalid port") from exc
    if port not in (None, 443):
        raise ValueError("source_url custom ports are not allowed")
    host = (parsed.hostname or "").lower().rstrip(".")
    if not host or host == "localhost" or host.endswith(".localhost"):
        raise ValueError("source_url host is not allowed")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ValueError("source_url IP literals are not allowed")
    path_lower = parsed.path.lower()
    suffix = Path(path_lower).suffix

    allowed = False
    if host == "raw.githubusercontent.com":
        allowed = suffix in DOCUMENT_EXTENSIONS
    elif host == "github.com":
        allowed = "/raw/" in path_lower and suffix in DOCUMENT_EXTENSIONS
    elif host in {"arxiv.org", "export.arxiv.org"}:
        allowed = path_lower.startswith("/pdf/")
    elif host in {
        "openaccess.thecvf.com",
        "aclanthology.org",
        "proceedings.neurips.cc",
        "papers.ssrn.com",
        "annualreports.com",
        "www.annualreports.com",
    }:
        allowed = suffix in DOCUMENT_EXTENSIONS or path_lower.endswith(".pdf")
    elif host == "openreview.net":
        allowed = path_lower == "/pdf" and bool(urllib.parse.parse_qs(parsed.query).get("id"))
    elif host in {"sec.gov", "www.sec.gov"}:
        allowed = path_lower.startswith("/archives/") and suffix in DOCUMENT_EXTENSIONS
    if not allowed:
        raise ValueError("source_url host or document path is not in the fixed public-document allowlist")
    normalized = urllib.parse.urlunsplit(
        ("https", parsed.netloc, parsed.path, parsed.query, "")
    )
    return normalized


def llama_base_url(parameters: Mapping[str, Any]) -> tuple[str, str]:
    region = str(parameters.get("region") or "na").lower()
    if region not in LLAMA_REGIONS:
        raise ValueError("region is not allowed")
    return LLAMA_REGIONS[region], region


def llama_headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"}


def llama_get_job(
    api_key: str,
    base_url: str,
    job_id: str,
    expands: list[str],
    timeout: int,
    max_bytes: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    query = {"expand": ",".join(expands)} if expands else {}
    return request_json(
        f"{base_url}/api/v2/parse/{urllib.parse.quote(job_id, safe='')}",
        method="GET",
        headers=llama_headers(api_key),
        timeout=timeout,
        max_bytes=max_bytes,
        query=query,
    )


def normalize_expands(value: Any, *, default: list[str]) -> list[str]:
    if value in (None, []):
        return list(default)
    if not isinstance(value, list) or not 1 <= len(value) <= 5:
        raise ValueError("expand must contain 1 to 5 values")
    result: list[str] = []
    for item in value:
        text = str(item)
        if text not in LLAMA_EXPANDS:
            raise ValueError(f"unsupported expand value: {text}")
        if text not in result:
            result.append(text)
    return result


def llamaparse_query(
    operation: str,
    parameters: Mapping[str, Any],
    timeout: int,
    max_bytes: int,
    poll_timeout: int,
) -> tuple[Any, dict[str, Any], str]:
    _, api_key = provider_key("llamaparse")
    base_url, region = llama_base_url(parameters)
    if operation == "get-job":
        job_id = required_text(parameters.get("job_id"), "job_id", 128)
        if not JOB_ID_RE.fullmatch(job_id):
            raise ValueError("job_id has an invalid format")
        expands = normalize_expands(
            parameters.get("expand"),
            default=["markdown_full", "metadata", "job_metadata"],
        )
        payload, metadata = llama_get_job(
            api_key,
            base_url,
            job_id,
            expands,
            timeout,
            max_bytes,
        )
        metadata.update({"credential_mode": "bearer", "region": region})
        return scrub(payload, [api_key]), metadata, LLAMA_CLOUD_API_KEY_ENV

    if operation != "parse-public-document":
        raise ValueError(f"unsupported LlamaParse operation: {operation}")

    source_url = validate_public_document_url(parameters.get("source_url"))
    tier = str(parameters.get("tier") or "cost_effective")
    if tier not in LLAMA_TIERS:
        raise ValueError("tier is not allowed")
    version = str(parameters.get("version") or "latest")
    if version != "latest" and not DATE_VERSION_RE.fullmatch(version):
        raise ValueError("version must be latest or YYYY-MM-DD")
    expands = normalize_expands(
        parameters.get("expand"),
        default=["markdown_full", "metadata", "job_metadata"],
    )
    body: dict[str, Any] = {
        "source_url": source_url,
        "tier": tier,
        "version": version,
        "disable_cache": bool(parameters.get("disable_cache", False)),
    }
    if parameters.get("max_pages") is not None:
        body["page_ranges"] = {
            "max_pages": bounded_int(
                parameters.get("max_pages"),
                default=50,
                minimum=1,
                maximum=200,
                name="max_pages",
            )
        }
    custom_prompt = str(parameters.get("custom_prompt") or "").strip()
    if custom_prompt:
        if len(custom_prompt) > 1000:
            raise ValueError("custom_prompt is too long")
        if tier == "fast":
            raise ValueError("custom_prompt is not available on fast tier")
        body["agentic_options"] = {"custom_prompt": custom_prompt}

    create_payload, create_metadata = request_json(
        f"{base_url}/api/v2/parse",
        method="POST",
        headers=llama_headers(api_key),
        timeout=timeout,
        max_bytes=max_bytes,
        body=body,
    )
    job_id = str(create_payload.get("id") or "")
    if not job_id:
        raise RuntimeError("LlamaParse create response has no id")
    status = str(create_payload.get("status") or "").upper()
    deadline = time.monotonic() + poll_timeout
    last_payload: dict[str, Any] = create_payload
    last_metadata = create_metadata
    while status not in TERMINAL_JOB_STATUSES:
        if time.monotonic() >= deadline:
            raise RuntimeError(f"LlamaParse job polling timed out; job_id={job_id}")
        time.sleep(2)
        last_payload, last_metadata = llama_get_job(
            api_key,
            base_url,
            job_id,
            expands,
            timeout,
            max_bytes,
        )
        job = last_payload.get("job")
        if not isinstance(job, Mapping):
            raise RuntimeError("LlamaParse retrieve response has no job object")
        status = str(job.get("status") or "").upper()
    if status != "COMPLETED":
        job = last_payload.get("job")
        message = str(job.get("error_message") or status) if isinstance(job, Mapping) else status
        raise RuntimeError(f"LlamaParse job ended with {status}: {message[:1000]}")
    last_metadata.update(
        {
            "credential_mode": "bearer",
            "region": region,
            "job_id": job_id,
            "polling_completed": True,
        }
    )
    return scrub(last_payload, [api_key]), last_metadata, LLAMA_CLOUD_API_KEY_ENV


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket)
    provider = str(ticket["provider"])
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket.get("acceptance") or {})
    timeout = bounded_int(
        acceptance.get("timeout_seconds"),
        default=60,
        minimum=5,
        maximum=120,
        name="timeout_seconds",
    )
    max_bytes = bounded_int(
        acceptance.get("max_response_bytes"),
        default=2_000_000,
        minimum=1024,
        maximum=5_000_000,
        name="max_response_bytes",
    )
    poll_timeout = bounded_int(
        acceptance.get("poll_timeout_seconds"),
        default=300,
        minimum=10,
        maximum=600,
        name="poll_timeout_seconds",
    )
    started_at = utc_now()
    started = time.perf_counter()
    status = "API_KNOWLEDGE_TOOLS_FAILED"
    data: Any = None
    metadata: dict[str, Any] = {}
    failure: dict[str, Any] | None = None
    credential_secret_name: str | None = None
    try:
        if operation == "catalog-capabilities":
            data = dict(catalog_provider(provider))
            metadata = {
                "source": "repository-catalog",
                "http_status": None,
                "upstream_called": False,
                "credential_mode": "none",
            }
        elif provider == "wolfram-alpha":
            data, metadata, credential_secret_name = wolfram_query(
                operation,
                parameters,
                timeout,
                max_bytes,
            )
        else:
            data, metadata, credential_secret_name = llamaparse_query(
                operation,
                parameters,
                timeout,
                max_bytes,
                poll_timeout,
            )
        status = "API_KNOWLEDGE_TOOLS_COMPLETED"
        write_json(output_dir / "result.json", data)
    except (ValueError, RuntimeError) as exc:
        failure = {
            "error_code": "KNOWLEDGE_TOOLS_UPSTREAM_ERROR",
            "message": str(exc)[:2000],
            "exception_type": type(exc).__name__,
        }
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    execution_status = {
        "schema_version": "knowledge-tools-execution-status-v1",
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
        "result_sha256": canonical_sha(data)
        if status == "API_KNOWLEDGE_TOOLS_COMPLETED"
        else None,
    }
    write_json(output_dir / "execution-status.json", execution_status)
    write_output("status", status)
    return 0 if status == "API_KNOWLEDGE_TOOLS_COMPLETED" else 1


def render(output_dir: Path, phase: str, artifact_url: str = "") -> int:
    ticket_status = load_json(output_dir / "ticket-status.json")
    if phase == "accepted":
        print("## API_KNOWLEDGE_TOOLS_ACCEPTED\n")
        print(f"- Task ID: `{ticket_status.get('task_id', '')}`")
        print(f"- Provider: `{ticket_status.get('provider', '')}`")
        print(f"- Operation: `{ticket_status.get('operation', '')}`")
        print(f"- Ticket SHA256: `{ticket_status.get('ticket_sha256', '')}`")
        print("- Model calls: `0`")
        return 0
    if phase == "rejected":
        print("## API_KNOWLEDGE_TOOLS_REJECTED\n")
        print(f"- Reason: {ticket_status.get('reason') or 'ticket rejected'}")
        print("- Secret values exposed: `false`")
        print("- Model calls: `0`")
        return 0
    execution = load_json(output_dir / "execution-status.json")
    print(f"## {execution['status']}\n")
    print(f"- Task ID: `{execution['task_id']}`")
    print(f"- Provider: `{execution['provider']}`")
    print(f"- Operation: `{execution['operation']}`")
    print(
        f"- Upstream called: "
        f"`{str(bool(execution['metadata'].get('upstream_called'))).lower()}`"
    )
    print(
        f"- Credential mode: "
        f"`{execution['metadata'].get('credential_mode', 'none')}`"
    )
    print(f"- Result SHA256: `{execution.get('result_sha256') or ''}`")
    if artifact_url:
        print(f"- Artifact: {artifact_url}")
    print("- Secret values exposed: `false`")
    print("- Model calls: `0`")
    if (
        execution["status"] == "API_KNOWLEDGE_TOOLS_COMPLETED"
        and (output_dir / "result.json").is_file()
    ):
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
    render_parser.add_argument(
        "--phase",
        choices=["accepted", "rejected", "completed"],
        required=True,
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
