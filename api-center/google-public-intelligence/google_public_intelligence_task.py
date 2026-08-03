#!/usr/bin/env python3
"""Bounded read-only execution for Google public intelligence APIs."""
from __future__ import annotations

import ipaddress
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit

import requests

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from managed_provider_runtime import (  # noqa: E402
    bounded_int,
    finish_execution,
    load_json,
    operation_map,
    provider_row,
    run_cli,
    utc_now,
    validate_ticket,
)

SCHEMA_PATH = HERE / "ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"
QUOTA_POLICY_PATH = HERE / "quota-policy.json"
API_KEY_ENV = "GOOGLE_PUBLIC_INTELLIGENCE_API_KEY"

ORIGINS = {
    "google": "https://www.googleapis.com",
    "factcheck": "https://factchecktools.googleapis.com",
    "pagespeed": "https://pagespeedonline.googleapis.com",
    "crux": "https://chromeuxreport.googleapis.com",
}
PATHS = {
    "youtube-search-videos": "/youtube/v3/search",
    "youtube-video": "/youtube/v3/videos",
    "youtube-channel": "/youtube/v3/channels",
    "factcheck-search": "/v1alpha1/claims:search",
    "pagespeed-analyze": "/pagespeedonline/v5/runPagespeed",
    "crux-query": "/v1/records:queryRecord",
    "crux-history-query": "/v1/records:queryHistoryRecord",
}

PHONE_RE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
ID_RE = re.compile(r"(?<!\d)\d{17}[0-9Xx](?!\d)")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SECRET_KEY_RE = re.compile(
    r"(?:api.?key|secret|access.?token|authorization|cookie|password)", re.I
)
PERSONAL_KEY_RE = re.compile(
    r"(?:身份证|证件号|手机号|手机号码|联系电话|联系手机|邮箱|电子邮箱|"
    r"email|phone|mobile|id.?card|bank.?card|passport)",
    re.I,
)


class GooglePublicIntelligenceError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def _secret() -> str:
    value = str(os.getenv(API_KEY_ENV) or "").strip()
    if not value:
        raise GooglePublicIntelligenceError(
            "GOOGLE_PUBLIC_CREDENTIAL_MISSING",
            f"missing repository Secret {API_KEY_ENV}",
        )
    if not 16 <= len(value) <= 2048:
        raise GooglePublicIntelligenceError(
            "GOOGLE_PUBLIC_CREDENTIAL_INVALID",
            f"invalid repository Secret {API_KEY_ENV} length",
        )
    if any(ord(char) < 0x21 or ord(char) > 0x7E for char in value):
        raise GooglePublicIntelligenceError(
            "GOOGLE_PUBLIC_CREDENTIAL_INVALID",
            f"invalid repository Secret {API_KEY_ENV} characters",
        )
    return value


def _redact(value: Any, key: str = "") -> Any:
    if SECRET_KEY_RE.search(key):
        return "[REDACTED_SECRET]"
    if PERSONAL_KEY_RE.search(key):
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


def _safe_google_error(payload: Any) -> tuple[str, str]:
    if not isinstance(payload, Mapping):
        return "", ""
    error = payload.get("error")
    if isinstance(error, Mapping):
        message = str(error.get("message") or "")[:1000]
        status = str(error.get("status") or "")[:100]
        details = error.get("errors")
        if isinstance(details, list) and details and isinstance(details[0], Mapping):
            reason = str(details[0].get("reason") or "")[:100]
            return reason or status, message
        return status, message
    return str(payload.get("code") or "")[:100], str(payload.get("message") or "")[:1000]


def _decode_json(response: requests.Response, *, max_bytes: int) -> Any:
    raw = response.content
    if len(raw) > max_bytes:
        raise GooglePublicIntelligenceError(
            "GOOGLE_PUBLIC_RESPONSE_TOO_LARGE",
            "upstream response exceeded max_response_bytes",
        )
    if response.is_redirect:
        raise GooglePublicIntelligenceError(
            "GOOGLE_PUBLIC_REDIRECT_REJECTED",
            f"upstream attempted HTTP {response.status_code} redirect",
        )
    try:
        return json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GooglePublicIntelligenceError(
            "GOOGLE_PUBLIC_INVALID_JSON",
            "upstream returned invalid JSON",
        ) from exc


def _check_http(response: requests.Response, payload: Any) -> None:
    reason, message = _safe_google_error(payload)
    combined = f"{reason}: {message}".strip(": ")
    lowered = combined.lower()
    if response.status_code in {401, 403}:
        if "quota" in lowered or "rate" in lowered or "limit" in lowered:
            raise GooglePublicIntelligenceError(
                "GOOGLE_PUBLIC_FREE_QUOTA_OR_RATE_LIMIT_REACHED",
                combined or f"upstream HTTP {response.status_code}",
            )
        raise GooglePublicIntelligenceError(
            "GOOGLE_PUBLIC_CREDENTIAL_OR_PERMISSION_DENIED",
            combined or f"upstream HTTP {response.status_code}",
        )
    if response.status_code == 429:
        raise GooglePublicIntelligenceError(
            "GOOGLE_PUBLIC_FREE_QUOTA_OR_RATE_LIMIT_REACHED",
            combined or "upstream HTTP 429",
        )
    if response.status_code == 404:
        raise GooglePublicIntelligenceError(
            "GOOGLE_PUBLIC_RECORD_NOT_FOUND",
            combined or "no eligible public record found",
        )
    if response.status_code >= 500:
        raise GooglePublicIntelligenceError(
            "GOOGLE_PUBLIC_HTTP_TRANSIENT",
            combined or f"upstream HTTP {response.status_code}",
            retryable=True,
        )
    if not 200 <= response.status_code < 300:
        raise GooglePublicIntelligenceError(
            "GOOGLE_PUBLIC_HTTP_ERROR",
            combined or f"upstream HTTP {response.status_code}",
        )


def _operation_row(operation: str) -> Mapping[str, Any]:
    row = operation_map(CATALOG_PATH).get(operation)
    if row is None:
        raise ValueError(f"unsupported Google public intelligence operation: {operation}")
    return row


def _validate_public_https(value: Any, *, origin_only: bool = False) -> str:
    text = str(value or "").strip()
    if not text or len(text) > 2048:
        raise ValueError("public HTTPS URL must be between 1 and 2048 characters")
    parsed = urlsplit(text)
    if parsed.scheme.lower() != "https":
        raise ValueError("only https URLs are allowed")
    if parsed.username or parsed.password:
        raise ValueError("URL credentials are not allowed")
    host = (parsed.hostname or "").rstrip(".").lower()
    if not host or "." not in host:
        raise ValueError("a public DNS hostname is required")
    try:
        host_ascii = host.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise ValueError("invalid hostname") from exc
    if host_ascii in {"localhost", "localhost.localdomain"}:
        raise ValueError("local hosts are not allowed")
    if host_ascii.endswith((".local", ".internal", ".localhost")):
        raise ValueError("private host suffixes are not allowed")
    try:
        ipaddress.ip_address(host_ascii)
    except ValueError:
        pass
    else:
        raise ValueError("IP literal targets are not allowed")
    if parsed.port not in (None, 443):
        raise ValueError("only the default HTTPS port is allowed")
    if origin_only and (parsed.path not in ("", "/") or parsed.query or parsed.fragment):
        raise ValueError("origin must not contain a path, query, or fragment")
    return text


def _bounded_request(
    *,
    operation: str,
    origin_key: str,
    method: str,
    params: Mapping[str, Any] | None,
    body: Mapping[str, Any] | None,
    timeout: int,
    max_bytes: int,
) -> tuple[Any, dict[str, Any]]:
    row = _operation_row(operation)
    execution = row.get("execution") or {}
    origin = ORIGINS[origin_key]
    path = PATHS[operation]
    if execution.get("official_origin") != origin:
        raise ValueError("provider catalog origin is not approved")
    if execution.get("path_template") != path:
        raise ValueError("provider catalog path is not approved")
    request_params: dict[str, Any] = dict(params or {})
    request_params["key"] = _secret()
    try:
        response = requests.request(
            method,
            origin + path,
            params=request_params,
            json=dict(body) if body is not None else None,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "evidence-intelligence-center-google-public/1",
            },
            timeout=timeout,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        raise GooglePublicIntelligenceError(
            "GOOGLE_PUBLIC_CONNECTION_FAILED",
            type(exc).__name__,
            retryable=True,
        ) from exc
    decoded = _decode_json(response, max_bytes=max_bytes)
    _check_http(response, decoded)
    return decoded, {
        "request_origin": origin.removeprefix("https://"),
        "request_path": path,
        "http_method": method,
        "credential_mode": "api-key-query-backend-only",
        "credential_environment_variable": API_KEY_ENV,
        "http_status": response.status_code,
        "response_bytes": len(response.content),
        "requests_per_ticket": 1,
        "upstream_called": True,
        "paid_fallback_authorized": False,
        "secret_values_exposed": False,
    }


def _youtube_search(parameters: Mapping[str, Any], *, timeout: int, max_bytes: int) -> tuple[Any, dict[str, Any]]:
    params: dict[str, Any] = {
        "part": "snippet",
        "type": "video",
        "q": str(parameters.get("query") or "").strip(),
        "maxResults": bounded_int(parameters.get("max_results"), default=10, minimum=1, maximum=25, name="max_results"),
        "order": str(parameters.get("order") or "relevance"),
        "fields": "pageInfo(totalResults,resultsPerPage),items(id/videoId,snippet(publishedAt,channelId,channelTitle,title,description,thumbnails/default/url))",
    }
    if not params["q"]:
        raise ValueError("query must not be empty")
    optional = {
        "channelId": parameters.get("channel_id"),
        "regionCode": parameters.get("region_code"),
        "relevanceLanguage": parameters.get("relevance_language"),
        "publishedAfter": parameters.get("published_after"),
    }
    params.update({key: value for key, value in optional.items() if value not in (None, "")})
    return _bounded_request(
        operation="youtube-search-videos",
        origin_key="google",
        method="GET",
        params=params,
        body=None,
        timeout=timeout,
        max_bytes=max_bytes,
    )


def _youtube_video(parameters: Mapping[str, Any], *, timeout: int, max_bytes: int) -> tuple[Any, dict[str, Any]]:
    return _bounded_request(
        operation="youtube-video",
        origin_key="google",
        method="GET",
        params={
            "part": "snippet,statistics,contentDetails,status",
            "id": str(parameters.get("video_id") or ""),
            "fields": "items(id,snippet(publishedAt,channelId,channelTitle,title,description,tags,categoryId,defaultLanguage),contentDetails(duration,definition,caption),statistics,status(privacyStatus,embeddable,publicStatsViewable))",
        },
        body=None,
        timeout=timeout,
        max_bytes=max_bytes,
    )


def _youtube_channel(parameters: Mapping[str, Any], *, timeout: int, max_bytes: int) -> tuple[Any, dict[str, Any]]:
    params: dict[str, Any] = {
        "part": "snippet,statistics,contentDetails,status,brandingSettings",
        "fields": "items(id,snippet(title,description,customUrl,publishedAt,country,thumbnails/default/url),statistics,contentDetails/relatedPlaylists/uploads,status/longUploadsStatus,brandingSettings/channel(keywords,unsubscribedTrailer,defaultLanguage,country))",
    }
    if parameters.get("channel_id"):
        params["id"] = str(parameters["channel_id"])
    elif parameters.get("handle"):
        params["forHandle"] = str(parameters["handle"])
    elif parameters.get("username"):
        params["forUsername"] = str(parameters["username"])
    else:
        raise ValueError("one channel identifier is required")
    return _bounded_request(
        operation="youtube-channel",
        origin_key="google",
        method="GET",
        params=params,
        body=None,
        timeout=timeout,
        max_bytes=max_bytes,
    )


def _factcheck(parameters: Mapping[str, Any], *, timeout: int, max_bytes: int) -> tuple[Any, dict[str, Any]]:
    params: dict[str, Any] = {
        "query": str(parameters.get("query") or "").strip(),
        "pageSize": bounded_int(parameters.get("page_size"), default=10, minimum=1, maximum=20, name="page_size"),
    }
    if not params["query"]:
        raise ValueError("query must not be empty")
    optional = {
        "languageCode": parameters.get("language_code"),
        "maxAgeDays": parameters.get("max_age_days"),
        "reviewPublisherSiteFilter": parameters.get("review_publisher_site"),
    }
    params.update({key: value for key, value in optional.items() if value not in (None, "")})
    return _bounded_request(
        operation="factcheck-search",
        origin_key="factcheck",
        method="GET",
        params=params,
        body=None,
        timeout=timeout,
        max_bytes=max_bytes,
    )


def _pagespeed(parameters: Mapping[str, Any], *, timeout: int, max_bytes: int) -> tuple[Any, dict[str, Any]]:
    target = _validate_public_https(parameters.get("url"))
    categories = parameters.get("categories") or ["performance"]
    params: dict[str, Any] = {
        "url": target,
        "strategy": str(parameters.get("strategy") or "mobile"),
        "category": list(categories),
    }
    if parameters.get("locale"):
        params["locale"] = str(parameters["locale"])
    return _bounded_request(
        operation="pagespeed-analyze",
        origin_key="pagespeed",
        method="GET",
        params=params,
        body=None,
        timeout=timeout,
        max_bytes=max_bytes,
    )


def _crux_body(parameters: Mapping[str, Any], *, history: bool) -> dict[str, Any]:
    body: dict[str, Any] = {}
    if parameters.get("origin"):
        body["origin"] = _validate_public_https(parameters["origin"], origin_only=True)
    elif parameters.get("url"):
        body["url"] = _validate_public_https(parameters["url"])
    else:
        raise ValueError("origin or url is required")
    if parameters.get("form_factor"):
        body["formFactor"] = str(parameters["form_factor"])
    if parameters.get("metrics"):
        body["metrics"] = list(parameters["metrics"])
    if history:
        body["collectionPeriodCount"] = bounded_int(
            parameters.get("collection_period_count"),
            default=25,
            minimum=1,
            maximum=40,
            name="collection_period_count",
        )
    return body


def _crux(parameters: Mapping[str, Any], *, history: bool, timeout: int, max_bytes: int) -> tuple[Any, dict[str, Any]]:
    operation = "crux-history-query" if history else "crux-query"
    return _bounded_request(
        operation=operation,
        origin_key="crux",
        method="POST",
        params={},
        body=_crux_body(parameters, history=history),
        timeout=timeout,
        max_bytes=max_bytes,
    )


def _truncate_list(value: Any, max_rows: int) -> Any:
    if isinstance(value, list):
        return value[:max_rows]
    return value


def _summarize_youtube(payload: Any, max_rows: int) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise GooglePublicIntelligenceError("GOOGLE_PUBLIC_RESULT_INVALID", "YouTube response must be an object")
    return {
        "pageInfo": payload.get("pageInfo"),
        "items": _truncate_list(payload.get("items") or [], max_rows),
    }


def _summarize_factcheck(payload: Any, max_rows: int) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise GooglePublicIntelligenceError("GOOGLE_PUBLIC_RESULT_INVALID", "Fact Check response must be an object")
    return {"claims": _truncate_list(payload.get("claims") or [], max_rows)}


def _audit_summary(audits: Any) -> dict[str, Any]:
    if not isinstance(audits, Mapping):
        return {}
    keys = (
        "first-contentful-paint",
        "largest-contentful-paint",
        "speed-index",
        "total-blocking-time",
        "cumulative-layout-shift",
        "interactive",
        "server-response-time",
    )
    result: dict[str, Any] = {}
    for key in keys:
        row = audits.get(key)
        if isinstance(row, Mapping):
            result[key] = {
                "score": row.get("score"),
                "numericValue": row.get("numericValue"),
                "numericUnit": row.get("numericUnit"),
                "displayValue": row.get("displayValue"),
            }
    return result


def _summarize_pagespeed(payload: Any) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise GooglePublicIntelligenceError("GOOGLE_PUBLIC_RESULT_INVALID", "PageSpeed response must be an object")
    lighthouse = payload.get("lighthouseResult") if isinstance(payload.get("lighthouseResult"), Mapping) else {}
    categories = lighthouse.get("categories") if isinstance(lighthouse.get("categories"), Mapping) else {}
    category_summary = {
        str(key): {"title": value.get("title"), "score": value.get("score")}
        for key, value in categories.items()
        if isinstance(value, Mapping)
    }
    return {
        "id": payload.get("id"),
        "analysisUTCTimestamp": payload.get("analysisUTCTimestamp"),
        "requestedUrl": lighthouse.get("requestedUrl"),
        "finalUrl": lighthouse.get("finalUrl"),
        "fetchTime": lighthouse.get("fetchTime"),
        "lighthouseVersion": lighthouse.get("lighthouseVersion"),
        "userAgent": lighthouse.get("userAgent"),
        "categories": category_summary,
        "audits": _audit_summary(lighthouse.get("audits")),
        "loadingExperience": payload.get("loadingExperience"),
        "originLoadingExperience": payload.get("originLoadingExperience"),
        "runtimeError": lighthouse.get("runtimeError"),
    }


def _summarize_crux(payload: Any) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise GooglePublicIntelligenceError("GOOGLE_PUBLIC_RESULT_INVALID", "CrUX response must be an object")
    return {"record": payload.get("record")}


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(acceptance.get("timeout_seconds"), default=60, minimum=5, maximum=120, name="timeout_seconds")
    max_bytes = bounded_int(acceptance.get("max_response_bytes"), default=1000000, minimum=1024, maximum=2000000, name="max_response_bytes")
    max_rows = bounded_int(acceptance.get("max_rows"), default=20, minimum=1, maximum=100, name="max_rows")

    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_GOOGLE_PUBLIC_FAILED"
    snapshot: Mapping[str, Any] | None = None
    failure: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "fixed_hosts": [
            "www.googleapis.com",
            "factchecktools.googleapis.com",
            "pagespeedonline.googleapis.com",
            "chromeuxreport.googleapis.com",
        ],
        "secret_values_exposed": False,
        "direct_personal_identifiers_redacted": True,
        "one_business_operation_per_ticket": True,
        "requests_per_ticket_max": 1,
        "automatic_pagination_allowed": False,
        "automatic_retries_allowed": False,
        "redirects_allowed": False,
        "write_operations_allowed": False,
        "oauth_user_data_allowed": False,
        "paid_fallback_authorized": False,
        "model_calls": 0,
    }
    try:
        if operation == "catalog-capabilities":
            snapshot = {"provider": provider_row(CATALOG_PATH)}
            metadata.update({"credential_mode": "none", "direct_personal_identifiers_redacted": False})
        elif operation == "quota-policy":
            snapshot = load_json(QUOTA_POLICY_PATH)
            metadata.update({"credential_mode": "none", "direct_personal_identifiers_redacted": False})
        else:
            if operation == "youtube-search-videos":
                payload, request_metadata = _youtube_search(parameters, timeout=timeout, max_bytes=max_bytes)
                data = _summarize_youtube(payload, max_rows)
            elif operation == "youtube-video":
                payload, request_metadata = _youtube_video(parameters, timeout=timeout, max_bytes=max_bytes)
                data = _summarize_youtube(payload, max_rows)
            elif operation == "youtube-channel":
                payload, request_metadata = _youtube_channel(parameters, timeout=timeout, max_bytes=max_bytes)
                data = _summarize_youtube(payload, max_rows)
            elif operation == "factcheck-search":
                payload, request_metadata = _factcheck(parameters, timeout=timeout, max_bytes=max_bytes)
                data = _summarize_factcheck(payload, max_rows)
            elif operation == "pagespeed-analyze":
                payload, request_metadata = _pagespeed(parameters, timeout=timeout, max_bytes=max_bytes)
                data = _summarize_pagespeed(payload)
            elif operation == "crux-query":
                payload, request_metadata = _crux(parameters, history=False, timeout=timeout, max_bytes=max_bytes)
                data = _summarize_crux(payload)
            elif operation == "crux-history-query":
                payload, request_metadata = _crux(parameters, history=True, timeout=timeout, max_bytes=max_bytes)
                data = _summarize_crux(payload)
            else:
                raise ValueError(f"unsupported Google public intelligence operation: {operation}")
            metadata.update(request_metadata)
            snapshot = {
                "provider": "google-public-intelligence",
                "operation": operation,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "data": _redact(data),
            }
        status = "INTEL_GOOGLE_PUBLIC_COMPLETED"
    except Exception as exc:
        message = str(exc)
        secret = str(os.getenv(API_KEY_ENV) or "")
        if secret:
            message = message.replace(secret, "[REDACTED]")
        failure = {
            "type": type(exc).__name__,
            "code": getattr(exc, "code", "GOOGLE_PUBLIC_EXECUTION_ERROR"),
            "retryable": bool(getattr(exc, "retryable", False)),
            "message": message[:2000],
        }
    return finish_execution(
        ticket=ticket,
        output_dir=output_dir,
        status=status,
        snapshot=snapshot,
        metadata=metadata,
        failure=failure,
        started_at=started_at,
        started_perf=started_perf,
        schema_prefix="google-public-intelligence",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-google-public]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="google-public-intelligence-ticket-status-v1",
            display_name="Google公开情报",
        )
    )
