#!/usr/bin/env python3
"""Bounded Baidu AI Cloud free-quota intelligence execution."""
from __future__ import annotations

import base64
import binascii
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
AIP_ORIGIN = "https://aip.baidubce.com"
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

LOCAL_OPERATIONS = {"catalog-capabilities", "quota-policy"}
SEARCH_OPERATIONS = {
    "web-search",
    "intelligent-search",
    "deep-search",
    "web-summary",
    "deep-research-lite",
}
GATED_FREE_QUOTA_OPERATIONS = {
    "intelligent-search",
    "deep-search",
    "web-summary",
    "deep-research-lite",
}
OCR_OPERATIONS = {
    "ocr-general-basic",
    "ocr-general",
    "ocr-accurate-basic",
    "ocr-accurate",
    "ocr-office",
    "ocr-webimage",
    "ocr-webimage-location",
    "ocr-handwriting",
    "ocr-table-v2",
    "ocr-seal",
    "ocr-numbers",
    "ocr-qrcode",
}
IMAGE_OPERATIONS = {
    "image-general-scene",
    "image-object-detect",
    "image-animal",
    "image-plant",
    "image-logo",
    "image-landmark",
    "image-vehicle-detect",
}
FORM_OPERATIONS = OCR_OPERATIONS | IMAGE_OPERATIONS


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


def _validate_base64_image(value: Any) -> str:
    text = str(value or "").strip()
    if len(text) > 8_000_000:
        raise ValueError("image_base64 exceeds 8000000 characters")
    if text.startswith("data:") or "," in text[:128]:
        raise ValueError("image_base64 must not include a data URL prefix")
    try:
        raw = base64.b64decode(text, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("image_base64 must be valid base64") from exc
    if not 12 <= len(raw) <= 6_000_000:
        raise ValueError("decoded image must contain 12 to 6000000 bytes")
    return text


def _bool_text(value: Any) -> str:
    return "true" if bool(value) else "false"


def _operation_row(operation: str) -> Mapping[str, Any]:
    row = operation_map(CATALOG_PATH).get(operation)
    if row is None:
        raise ValueError(f"unsupported Baidu AI Cloud operation: {operation}")
    return row


def _origin_and_path(operation: str) -> tuple[str, str]:
    row = _operation_row(operation)
    execution = row.get("execution") or {}
    origin = str(execution.get("official_origin") or "")
    path = str(execution.get("path_template") or "")
    if origin not in {QIANFAN_ORIGIN, AIP_ORIGIN}:
        raise ValueError("provider catalog origin is not an approved Baidu host")
    if not path.startswith("/") or "://" in path or ".." in path:
        raise ValueError("provider catalog path is invalid")
    return origin, path


def _assert_free_quota_guard(operation: str, parameters: Mapping[str, Any]) -> None:
    if operation not in GATED_FREE_QUOTA_OPERATIONS:
        return
    if parameters.get("free_quota_confirmed") is not True:
        raise BaiduAICloudError(
            "BAIDU_FREE_QUOTA_NOT_CONFIRMED",
            "free_quota_confirmed must be true",
        )
    if parameters.get("paid_fallback_authorized") is not False:
        raise BaiduAICloudError(
            "BAIDU_PAID_FALLBACK_REJECTED",
            "paid fallback is not authorized",
        )


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


def _intelligent_search_body(
    operation: str,
    parameters: Mapping[str, Any],
) -> dict[str, Any]:
    _assert_free_quota_guard(operation, parameters)
    query = str(parameters.get("query") or "").strip()
    model = str(parameters.get("model") or "").strip()
    if not query or not model:
        raise ValueError("query and model must not be empty")
    top_k = bounded_int(
        parameters.get("top_k"),
        default=10,
        minimum=1,
        maximum=20,
        name="top_k",
    )
    body: dict[str, Any] = {
        "messages": [{"content": query, "role": "user"}],
        "model": model,
        "stream": False,
        "search_source": "baidu_search_v2",
        "resource_type_filter": [{"type": "web", "top_k": top_k}],
        "enable_followup_query": False,
        "enable_corner_markers": True,
        "enable_deep_search": operation == "deep-search",
    }
    instruction = str(parameters.get("instruction") or "").strip()
    if instruction:
        body["instruction"] = instruction
    if operation == "deep-search":
        body["max_search_query_num"] = bounded_int(
            parameters.get("max_search_query_num"),
            default=3,
            minimum=1,
            maximum=3,
            name="max_search_query_num",
        )
    return body


def _web_summary_body(parameters: Mapping[str, Any]) -> dict[str, Any]:
    _assert_free_quota_guard("web-summary", parameters)
    query = str(parameters.get("query") or "").strip()
    if not query:
        raise ValueError("query must not be empty")
    top_k = bounded_int(
        parameters.get("top_k"),
        default=5,
        minimum=1,
        maximum=20,
        name="top_k",
    )
    return {
        "instruction": str(
            parameters.get("instruction")
            or "仅依据公开检索结果总结，明确列出引用，不补造事实。"
        ),
        "messages": [{"content": query, "role": "user"}],
        "stream": False,
        "resource_type_filter": [{"type": "web", "top_k": top_k}],
    }


def _deep_research_body(parameters: Mapping[str, Any]) -> dict[str, Any]:
    _assert_free_quota_guard("deep-research-lite", parameters)
    query = str(parameters.get("query") or "").strip()
    if not query:
        raise ValueError("query must not be empty")
    return {"query": query, "version": "lite"}


def _json_body(operation: str, parameters: Mapping[str, Any]) -> dict[str, Any]:
    if operation == "web-search":
        return _web_search_body(parameters)
    if operation in {"intelligent-search", "deep-search"}:
        return _intelligent_search_body(operation, parameters)
    if operation == "web-summary":
        return _web_summary_body(parameters)
    if operation == "deep-research-lite":
        return _deep_research_body(parameters)
    body = dict(parameters)
    for key, value in body.items():
        if isinstance(value, str) and not value.strip():
            raise ValueError(f"{key} must not be empty")
    return body


def _form_body(parameters: Mapping[str, Any]) -> dict[str, str]:
    image = _validate_base64_image(parameters.get("image_base64"))
    body: dict[str, str] = {"image": image}
    for key, value in parameters.items():
        if key == "image_base64" or value in (None, ""):
            continue
        body[key] = _bool_text(value) if isinstance(value, bool) else str(value)
    return body


def _parse_sse(
    response: requests.Response,
    *,
    max_bytes: int,
    max_events: int = 400,
) -> dict[str, Any]:
    _check_http(response)
    events: list[Any] = []
    total = 0
    for line in response.iter_lines(decode_unicode=False):
        if not line:
            continue
        total += len(line)
        if total > max_bytes:
            raise BaiduAICloudError(
                "BAIDU_RESPONSE_TOO_LARGE",
                "SSE response exceeded max_response_bytes",
            )
        if not line.startswith(b"data:"):
            continue
        data = line[5:].strip()
        if not data or data == b"[DONE]":
            continue
        try:
            event = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            event = {"raw": data.decode("utf-8", errors="replace")[:4000]}
        events.append(event)
        if len(events) >= max_events:
            break
    return {
        "events": events,
        "event_count": len(events),
        "response_bytes": total,
        "completed_in_single_request": any(
            isinstance(item, Mapping) and str(item.get("status") or "") == "done"
            for item in events
        ),
        "interrupt_returned": any(
            isinstance(item, Mapping) and str(item.get("status") or "") == "interrupt"
            for item in events
        ),
    }


def _post(
    operation: str,
    parameters: Mapping[str, Any],
    *,
    timeout: int,
    max_bytes: int,
) -> tuple[Mapping[str, Any], dict[str, Any]]:
    origin, path = _origin_and_path(operation)
    key = _secret()
    headers = {
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {key}",
        "Content-Type": (
            "application/x-www-form-urlencoded"
            if operation in FORM_OPERATIONS
            else "application/json"
        ),
        "User-Agent": "evidence-intelligence-center-baidu-ai/2",
    }
    kwargs: dict[str, Any] = {
        "headers": headers,
        "timeout": timeout,
        "allow_redirects": False,
    }
    if operation in FORM_OPERATIONS:
        kwargs["data"] = _form_body(parameters)
    else:
        kwargs["json"] = _json_body(operation, parameters)
    if operation == "deep-research-lite":
        kwargs["stream"] = True
    try:
        response = requests.post(origin + path, **kwargs)
    except requests.RequestException as exc:
        raise BaiduAICloudError(
            "BAIDU_CONNECTION_FAILED",
            type(exc).__name__,
            retryable=True,
        ) from exc

    if operation == "deep-research-lite":
        payload: Mapping[str, Any] = _parse_sse(
            response,
            max_bytes=max_bytes,
        )
        response_bytes = int(payload.get("response_bytes") or 0)
    else:
        decoded = _decode_json(response, max_bytes=max_bytes)
        _check_http(response, decoded)
        if not isinstance(decoded, Mapping):
            raise BaiduAICloudError(
                "BAIDU_RESULT_INVALID",
                "upstream response must be a JSON object",
            )
        payload = decoded
        response_bytes = len(response.content)

    return payload, {
        "request_origin": origin.removeprefix("https://"),
        "request_path": path,
        "http_method": "POST",
        "credential_mode": "unified-api-key-bearer-backend-only",
        "credential_environment_variable": API_KEY_ENV,
        "http_status": response.status_code,
        "response_bytes": response_bytes,
        "requests_per_ticket": 1,
        "upstream_called": True,
        "free_quota_guard_required": operation in GATED_FREE_QUOTA_OPERATIONS,
        "paid_fallback_authorized": False,
        "secret_values_exposed": False,
    }


def _truncate_top_level(payload: Mapping[str, Any], max_rows: int) -> Mapping[str, Any]:
    result = dict(payload)
    for key in (
        "references",
        "items",
        "results",
        "words_result",
        "result",
        "events",
    ):
        value = result.get(key)
        if isinstance(value, list) and len(value) > max_rows:
            result[key] = value[:max_rows]
            result[f"{key}_truncated_to"] = max_rows
    return result


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(
        ticket,
        schema_path=SCHEMA_PATH,
        catalog_path=CATALOG_PATH,
    )
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(
        acceptance.get("timeout_seconds"),
        default=60,
        minimum=5,
        maximum=180,
        name="timeout_seconds",
    )
    max_bytes = bounded_int(
        acceptance.get("max_response_bytes"),
        default=5_000_000,
        minimum=1024,
        maximum=10_000_000,
        name="max_response_bytes",
    )
    max_rows = bounded_int(
        acceptance.get("max_rows"),
        default=100,
        minimum=1,
        maximum=1000,
        name="max_rows",
    )
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_BAIDU_AI_FAILED"
    snapshot: Mapping[str, Any] | None = None
    failure: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "fixed_hosts": ["qianfan.baidubce.com", "aip.baidubce.com"],
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
        else:
            payload, request_metadata = _post(
                operation,
                parameters,
                timeout=timeout,
                max_bytes=max_bytes,
            )
            metadata.update(request_metadata)
            if operation in {"intelligent-search", "deep-search", "web-summary", "deep-research-lite"}:
                metadata["model_calls"] = 1
            snapshot = {
                "provider": "baidu-ai-cloud",
                "operation": operation,
                "data": _redact(_truncate_top_level(payload, max_rows)),
            }
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
            status_schema="baidu-ai-cloud-ticket-status-v2",
            display_name="百度智能云免费情报能力",
        )
    )
