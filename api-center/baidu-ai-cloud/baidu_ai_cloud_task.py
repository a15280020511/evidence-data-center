#!/usr/bin/env python3
"""Bounded execution for verified Baidu search, model-summary, and Baike reads."""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Mapping

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
QUOTA_POLICY_PATH = HERE / "free-quota-policy.json"

QIANFAN_ORIGIN = "https://qianfan.baidubce.com"
APPBUILDER_ORIGIN = "https://appbuilder.baidu.com"
WEB_SEARCH_PATH = "/v2/ai_search/web_search"
WEB_SUMMARY_PATH = "/v2/ai_search/web_summary"
BAIKE_LEMMA_LIST_PATH = "/v2/baike/lemma/get_list_by_title"
BAIKE_LEMMA_CONTENT_PATH = "/v2/baike/lemma/get_content"
BAIKE_STARMAP_LIST_PATH = "/v2/tools/baike/starmap/get_starmap_by_title"
BAIKE_STARMAP_DETAIL_PATH = "/v2/tools/baike/starmap/get_starmap_by_id"
API_KEY_ENV = "BAIDU_AI_CLOUD_API_KEY"

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


class BaiduAICloudError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def _secret() -> str:
    value = str(os.getenv(API_KEY_ENV) or "").strip()
    if not value:
        raise BaiduAICloudError(
            "BAIDU_CREDENTIAL_MISSING",
            f"missing repository Secret {API_KEY_ENV}",
        )
    if not 8 <= len(value) <= 2048:
        raise BaiduAICloudError(
            "BAIDU_CREDENTIAL_INVALID",
            f"invalid repository Secret {API_KEY_ENV} length",
        )
    if any(ord(char) < 0x21 or ord(char) > 0x7E for char in value):
        raise BaiduAICloudError(
            "BAIDU_CREDENTIAL_INVALID",
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


def _safe_message(payload: Any) -> str:
    if not isinstance(payload, Mapping):
        return ""
    return str(
        payload.get("error_msg")
        or payload.get("error_description")
        or payload.get("message")
        or payload.get("msg")
        or payload.get("error")
        or ""
    )[:1000]


def _decode_json(response: requests.Response, *, max_bytes: int) -> Any:
    raw = response.content
    if len(raw) > max_bytes:
        raise BaiduAICloudError(
            "BAIDU_RESPONSE_TOO_LARGE",
            "upstream response exceeded max_response_bytes",
        )
    if response.is_redirect:
        raise BaiduAICloudError(
            "BAIDU_REDIRECT_REJECTED",
            f"upstream attempted HTTP {response.status_code} redirect",
        )
    try:
        return json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BaiduAICloudError(
            "BAIDU_INVALID_JSON",
            "upstream returned invalid JSON",
        ) from exc


def _check_http(response: requests.Response, payload: Any | None = None) -> None:
    message = _safe_message(payload)
    if response.status_code in {401, 403}:
        raise BaiduAICloudError(
            "BAIDU_CREDENTIAL_OR_PERMISSION_DENIED",
            message or f"upstream HTTP {response.status_code}",
        )
    if response.status_code == 429:
        raise BaiduAICloudError(
            "BAIDU_FREE_QUOTA_OR_RATE_LIMIT_REACHED",
            message or "upstream HTTP 429",
        )
    if response.status_code >= 500:
        raise BaiduAICloudError(
            "BAIDU_HTTP_TRANSIENT",
            f"upstream HTTP {response.status_code}",
            retryable=True,
        )
    if not 200 <= response.status_code < 300:
        raise BaiduAICloudError(
            "BAIDU_HTTP_ERROR",
            message or f"upstream HTTP {response.status_code}",
        )
    if isinstance(payload, Mapping):
        error_code = payload.get("error_code")
        if error_code not in (None, 0, "0"):
            if str(error_code) in {"17", "18", "19"}:
                raise BaiduAICloudError(
                    "BAIDU_FREE_QUOTA_OR_RATE_LIMIT_REACHED",
                    f"{error_code}: {message or 'quota or rate limit reached'}",
                )
            raise BaiduAICloudError(
                "BAIDU_BUSINESS_ERROR",
                f"{error_code}: {message or 'business error'}",
            )
        code = payload.get("code")
        if code not in (None, "", 0, "0", 200, "200", 201, "201"):
            raise BaiduAICloudError(
                "BAIDU_BUSINESS_ERROR",
                f"{code}: {message or 'business error'}",
            )


def _operation_row(operation: str) -> Mapping[str, Any]:
    row = operation_map(CATALOG_PATH).get(operation)
    if row is None:
        raise ValueError(f"unsupported Baidu operation: {operation}")
    return row


def _web_search_body(parameters: Mapping[str, Any]) -> dict[str, Any]:
    query = str(parameters.get("query") or "").strip()
    if not query:
        raise ValueError("query must not be empty")
    top_k = bounded_int(
        parameters.get("top_k"),
        default=10,
        minimum=1,
        maximum=20,
        name="top_k",
    )
    body: dict[str, Any] = {
        "messages": [{"content": query, "role": "user"}],
        "search_source": "baidu_search_v2",
        "edition": str(parameters.get("edition") or "standard"),
        "resource_type_filter": [{"type": "web", "top_k": top_k}],
    }
    recency = parameters.get("recency")
    if recency:
        body["search_recency_filter"] = str(recency)
    return body


def _post_web_search(
    parameters: Mapping[str, Any],
    *,
    timeout: int,
    max_bytes: int,
) -> tuple[Mapping[str, Any], dict[str, Any]]:
    row = _operation_row("web-search")
    execution = row.get("execution") or {}
    if execution.get("official_origin") != QIANFAN_ORIGIN:
        raise ValueError("provider catalog origin is not approved")
    if execution.get("path_template") != WEB_SEARCH_PATH:
        raise ValueError("provider catalog path is not approved")
    key = _secret()
    try:
        response = requests.post(
            QIANFAN_ORIGIN + WEB_SEARCH_PATH,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "User-Agent": "evidence-intelligence-center-baidu-search/3",
            },
            json=_web_search_body(parameters),
            timeout=timeout,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        raise BaiduAICloudError(
            "BAIDU_CONNECTION_FAILED",
            type(exc).__name__,
            retryable=True,
        ) from exc
    decoded = _decode_json(response, max_bytes=max_bytes)
    _check_http(response, decoded)
    if not isinstance(decoded, Mapping):
        raise BaiduAICloudError(
            "BAIDU_RESULT_INVALID",
            "upstream response must be a JSON object",
        )
    return decoded, {
        "request_origin": "qianfan.baidubce.com",
        "request_path": WEB_SEARCH_PATH,
        "http_method": "POST",
        "credential_mode": "unified-api-key-bearer-backend-only",
        "credential_environment_variable": API_KEY_ENV,
        "http_status": response.status_code,
        "response_bytes": len(response.content),
        "requests_per_ticket": 1,
        "upstream_called": True,
        "paid_fallback_authorized": False,
        "secret_values_exposed": False,
    }


def _web_summary_body(parameters: Mapping[str, Any]) -> dict[str, Any]:
    query = str(parameters.get("query") or "").strip()
    if not query:
        raise ValueError("query must not be empty")
    top_k = bounded_int(
        parameters.get("top_k"),
        default=3,
        minimum=1,
        maximum=10,
        name="top_k",
    )
    instruction = str(
        parameters.get("instruction")
        or "仅基于公开网页生成简明、可核验的事实摘要，并保留引用。"
    ).strip()
    if not instruction or len(instruction) > 4000:
        raise ValueError("instruction must contain 1 to 4000 characters")
    return {
        "instruction": instruction,
        "messages": [{"content": query, "role": "user"}],
        "stream": False,
        "resource_type_filter": [{"type": "web", "top_k": top_k}],
        "enable_full_content": False,
    }


def _post_web_summary(
    parameters: Mapping[str, Any],
    *,
    timeout: int,
    max_bytes: int,
) -> tuple[Mapping[str, Any], dict[str, Any]]:
    row = _operation_row("web-summary")
    execution = row.get("execution") or {}
    if execution.get("official_origin") != QIANFAN_ORIGIN:
        raise ValueError("provider catalog origin is not approved")
    if execution.get("path_template") != WEB_SUMMARY_PATH:
        raise ValueError("provider catalog path is not approved")
    key = _secret()
    try:
        response = requests.post(
            QIANFAN_ORIGIN + WEB_SUMMARY_PATH,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "User-Agent": "evidence-intelligence-center-baidu-summary/1",
            },
            json=_web_summary_body(parameters),
            timeout=timeout,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        raise BaiduAICloudError(
            "BAIDU_CONNECTION_FAILED",
            type(exc).__name__,
            retryable=True,
        ) from exc
    decoded = _decode_json(response, max_bytes=max_bytes)
    _check_http(response, decoded)
    if not isinstance(decoded, Mapping):
        raise BaiduAICloudError(
            "BAIDU_RESULT_INVALID",
            "upstream response must be a JSON object",
        )
    choices = decoded.get("choices")
    content = ""
    if isinstance(choices, list) and choices:
        first = choices[0] if isinstance(choices[0], Mapping) else {}
        message = first.get("message") if isinstance(first.get("message"), Mapping) else {}
        content = str(message.get("content") or "")
    if not content.strip():
        raise BaiduAICloudError(
            "BAIDU_RESULT_INVALID",
            "model-search response contained no generated content",
        )
    return decoded, {
        "request_origin": "qianfan.baidubce.com",
        "request_path": WEB_SUMMARY_PATH,
        "http_method": "POST",
        "credential_mode": "unified-api-key-bearer-backend-only",
        "credential_environment_variable": API_KEY_ENV,
        "http_status": response.status_code,
        "response_bytes": len(response.content),
        "requests_per_ticket": 1,
        "upstream_called": True,
        "paid_fallback_authorized": False,
        "model_calls": 1,
        "secret_values_exposed": False,
    }


def _get_baike(
    operation: str,
    parameters: Mapping[str, Any],
    *,
    timeout: int,
    max_bytes: int,
) -> tuple[Mapping[str, Any], dict[str, Any]]:
    contracts = {
        "baike-lemma-list": (APPBUILDER_ORIGIN, BAIKE_LEMMA_LIST_PATH),
        "baike-lemma-content": (APPBUILDER_ORIGIN, BAIKE_LEMMA_CONTENT_PATH),
        "baike-starmap-list": (QIANFAN_ORIGIN, BAIKE_STARMAP_LIST_PATH),
        "baike-starmap-detail": (QIANFAN_ORIGIN, BAIKE_STARMAP_DETAIL_PATH),
    }
    origin, path = contracts[operation]
    row = _operation_row(operation)
    execution = row.get("execution") or {}
    if execution.get("official_origin") != origin or execution.get("path_template") != path:
        raise ValueError("provider catalog endpoint is not approved")
    if operation == "baike-lemma-list":
        title = str(parameters.get("lemma_title") or "").strip()
        if not title or len(title) > 200:
            raise ValueError("lemma_title must contain 1 to 200 characters")
        query = {"lemma_title": title, "top_k": bounded_int(parameters.get("top_k"), default=5, minimum=1, maximum=20, name="top_k")}
    elif operation == "baike-lemma-content":
        search_type = str(parameters.get("search_type") or "lemmaTitle")
        if search_type not in {"lemmaTitle", "lemmaId"}:
            raise ValueError("search_type is not allowed")
        search_key = str(parameters.get("search_key") or "").strip()
        if not search_key or len(search_key) > 200:
            raise ValueError("search_key must contain 1 to 200 characters")
        query = {"search_type": search_type, "search_key": search_key}
    elif operation == "baike-starmap-list":
        title = str(parameters.get("starmap_title") or "").strip()
        if len(title) > 200:
            raise ValueError("starmap_title is too long")
        query = {"page": bounded_int(parameters.get("page"), default=1, minimum=1, maximum=100, name="page")}
        if title:
            query["starmap_title"] = title
    else:
        starmap_id = str(parameters.get("starmap_id") or "").strip()
        if not starmap_id or len(starmap_id) > 128:
            raise ValueError("starmap_id must contain 1 to 128 characters")
        query = {"starmap_id": starmap_id, "page": bounded_int(parameters.get("page"), default=1, minimum=1, maximum=100, name="page")}
    key = _secret()
    try:
        response = requests.get(
            origin + path,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {key}",
                "User-Agent": "evidence-intelligence-center-baidu-baike/1",
            },
            params=query,
            timeout=timeout,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        raise BaiduAICloudError("BAIDU_CONNECTION_FAILED", type(exc).__name__, retryable=True) from exc
    decoded = _decode_json(response, max_bytes=max_bytes)
    _check_http(response, decoded)
    if not isinstance(decoded, Mapping):
        raise BaiduAICloudError("BAIDU_RESULT_INVALID", "upstream response must be a JSON object")
    return decoded, {
        "request_origin": origin.removeprefix("https://"),
        "request_path": path,
        "http_method": "GET",
        "credential_mode": "unified-api-key-bearer-backend-only",
        "credential_environment_variable": API_KEY_ENV,
        "http_status": response.status_code,
        "response_bytes": len(response.content),
        "requests_per_ticket": 1,
        "upstream_called": True,
        "paid_fallback_authorized": False,
        "model_calls": 0,
        "secret_values_exposed": False,
    }


def _truncate(payload: Mapping[str, Any], max_rows: int) -> Mapping[str, Any]:
    result = dict(payload)
    for key in ("references", "items", "results", "list", "result"):
        value = result.get(key)
        if isinstance(value, list) and len(value) > max_rows:
            result[key] = value[:max_rows]
            result[f"{key}_truncated_to"] = max_rows
    return result


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(
        acceptance.get("timeout_seconds"),
        default=30,
        minimum=5,
        maximum=90,
        name="timeout_seconds",
    )
    max_bytes = bounded_int(
        acceptance.get("max_response_bytes"),
        default=500000,
        minimum=1024,
        maximum=2000000,
        name="max_response_bytes",
    )
    max_rows = bounded_int(
        acceptance.get("max_rows"),
        default=20,
        minimum=1,
        maximum=100,
        name="max_rows",
    )
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_BAIDU_AI_FAILED"
    snapshot: Mapping[str, Any] | None = None
    failure: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "fixed_hosts": ["qianfan.baidubce.com", "appbuilder.baidu.com"],
        "secret_values_exposed": False,
        "direct_personal_identifiers_redacted": True,
        "one_business_operation_per_ticket": True,
        "requests_per_ticket_max": 1,
        "automatic_pagination_allowed": False,
        "automatic_retries_allowed": False,
        "redirects_allowed": False,
        "write_operations_allowed": False,
        "paid_fallback_authorized": False,
        "model_calls": 0,
    }
    try:
        if operation == "catalog-capabilities":
            snapshot = {"provider": provider_row(CATALOG_PATH)}
            metadata.update(
                {
                    "credential_mode": "none",
                    "direct_personal_identifiers_redacted": False,
                }
            )
        elif operation == "quota-policy":
            snapshot = load_json(QUOTA_POLICY_PATH)
            metadata.update(
                {
                    "credential_mode": "none",
                    "direct_personal_identifiers_redacted": False,
                }
            )
        elif operation == "web-search":
            payload, request_metadata = _post_web_search(
                parameters,
                timeout=timeout,
                max_bytes=max_bytes,
            )
            metadata.update(request_metadata)
            snapshot = {
                "provider": "baidu-ai-cloud",
                "operation": operation,
                "data": _redact(_truncate(payload, max_rows)),
            }
        elif operation == "web-summary":
            payload, request_metadata = _post_web_summary(
                parameters,
                timeout=timeout,
                max_bytes=max_bytes,
            )
            metadata.update(request_metadata)
            snapshot = {
                "provider": "baidu-ai-cloud",
                "operation": operation,
                "data": _redact(_truncate(payload, max_rows)),
            }
        elif operation in {"baike-lemma-list", "baike-lemma-content", "baike-starmap-list", "baike-starmap-detail"}:
            payload, request_metadata = _get_baike(
                operation,
                parameters,
                timeout=timeout,
                max_bytes=max_bytes,
            )
            metadata.update(request_metadata)
            snapshot = {
                "provider": "baidu-ai-cloud",
                "operation": operation,
                "data": _redact(_truncate(payload, max_rows)),
            }
        else:
            raise ValueError(f"unsupported Baidu operation: {operation}")
        status = "INTEL_BAIDU_AI_COMPLETED"
    except Exception as exc:
        message = str(exc)
        secret = str(os.getenv(API_KEY_ENV) or "")
        if secret:
            message = message.replace(secret, "[REDACTED]")
        failure = {
            "type": type(exc).__name__,
            "code": getattr(exc, "code", "BAIDU_AI_EXECUTION_ERROR"),
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
        schema_prefix="baidu-ai-cloud",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-baidu-ai]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="baidu-ai-cloud-ticket-status-v3",
            display_name="百度AI搜索、模型摘要与百科",
        )
    )
