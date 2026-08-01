#!/usr/bin/env python3
from __future__ import annotations

import json
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "api-center"
BROWSERLESS = API / "browserless"
WORKFLOWS = ROOT / ".github" / "workflows"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


provider = {
    "provider_id": "browserless",
    "display_name": "Browserless REST API",
    "description": "通过 Browserless 托管无头浏览器读取 JavaScript 渲染网页、结构化抓取、生成截图和 PDF、执行 Lighthouse 审计，并提供受限的搜索与站点地图能力。",
    "enabled": True,
    "ticket_prefix": "[api-browserless]",
    "required_secret_environment_variable": "BROWSERLESS_TOKEN",
    "catalog_policy": "仅允许固定 Browserless Cloud REST 主机和公开 HTTPS 目标；禁止任意 JavaScript、Function、Download、Export、BQL、BaaS、WebSocket、Profile、Cookie、Authorization、自定义请求头、代理、地理代理、Unblock、CAPTCHA 求解和登录态页面。",
    "execution_policy": "BROWSERLESS_TOKEN 仅在后端固定查询参数中注入且不进入日志或 Artifact；每张票据只调用一个固定 REST 端点；目标 URL 必须通过公开 HTTPS 与 SSRF 防护；二进制结果只作为 Artifact 文件保存。",
    "limits": {
        "requests_per_ticket": 1,
        "timeout_seconds_max": 120,
        "max_response_bytes": 10000000,
        "target_urls_max": 1,
        "selectors_max": 20,
        "search_results_max": 3,
        "map_links_max": 100,
        "fixed_api_host": "production-sfo.browserless.io",
        "arbitrary_api_hosts_allowed": False,
        "arbitrary_code_allowed": False,
        "websocket_sessions_allowed": False,
        "profiles_allowed": False,
        "custom_headers_allowed": False,
        "cookies_allowed": False,
        "proxy_configuration_allowed": False,
        "captcha_or_unblock_allowed": False,
        "write_operations_allowed": False,
    },
    "operations": [
        {
            "operation_id": "catalog-capabilities",
            "description": "读取 Browserless 本地安全能力目录，不访问上游且不需要密钥。",
            "parameters": [],
            "parameter_schema": {"type": "object", "additionalProperties": False, "properties": {}},
            "result_contract": {"provider": "browserless", "read_only": True, "upstream_called": False},
            "discovery_policy": {"source": "official-documentation", "documentation_url": "https://docs.browserless.io/rest-apis/intro"},
        },
        {
            "operation_id": "content",
            "description": "调用 /content 返回一个公开 HTTPS 页面的完整 JavaScript 渲染 HTML。",
            "parameters": ["url"],
            "parameter_schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {"url": {"type": "string", "minLength": 9, "maxLength": 2048, "pattern": "^https://"}},
                "required": ["url"],
            },
            "result_contract": {"provider": "browserless", "official_endpoint": "https://production-sfo.browserless.io/content", "http_method": "POST", "response_type": "text/html", "read_only": True},
            "discovery_policy": {"source": "official-documentation", "documentation_url": "https://docs.browserless.io/rest-apis/content"},
        },
        {
            "operation_id": "scrape",
            "description": "调用 /scrape 在完整渲染后按最多20个 CSS 选择器提取结构化 JSON。",
            "parameters": ["url", "selectors"],
            "parameter_schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "url": {"type": "string", "minLength": 9, "maxLength": 2048, "pattern": "^https://"},
                    "selectors": {"type": "array", "minItems": 1, "maxItems": 20, "uniqueItems": True, "items": {"type": "string", "minLength": 1, "maxLength": 500}},
                },
                "required": ["url", "selectors"],
            },
            "result_contract": {"provider": "browserless", "official_endpoint": "https://production-sfo.browserless.io/scrape", "http_method": "POST", "response_type": "application/json", "read_only": True},
            "discovery_policy": {"source": "official-documentation", "documentation_url": "https://docs.browserless.io/rest-apis/scrape"},
        },
        {
            "operation_id": "screenshot",
            "description": "调用 /screenshot 为一个公开 HTTPS 页面生成 PNG、JPEG 或 WebP 截图 Artifact。",
            "parameters": ["url", "image_type", "full_page", "quality"],
            "parameter_schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "url": {"type": "string", "minLength": 9, "maxLength": 2048, "pattern": "^https://"},
                    "image_type": {"type": "string", "enum": ["png", "jpeg", "webp"]},
                    "full_page": {"type": "boolean"},
                    "quality": {"type": "integer", "minimum": 1, "maximum": 100},
                },
                "required": ["url"],
            },
            "result_contract": {"provider": "browserless", "official_endpoint": "https://production-sfo.browserless.io/screenshot", "http_method": "POST", "response_type": "image/*", "read_only": True, "artifact_binary": True},
            "discovery_policy": {"source": "official-documentation", "documentation_url": "https://docs.browserless.io/rest-apis/screenshot-api"},
        },
        {
            "operation_id": "pdf",
            "description": "调用 /pdf 为一个公开 HTTPS 页面生成受限 PDF Artifact。",
            "parameters": ["url", "format", "landscape", "print_background"],
            "parameter_schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "url": {"type": "string", "minLength": 9, "maxLength": 2048, "pattern": "^https://"},
                    "format": {"type": "string", "enum": ["A4", "Letter", "Legal", "A3", "A5"]},
                    "landscape": {"type": "boolean"},
                    "print_background": {"type": "boolean"},
                },
                "required": ["url"],
            },
            "result_contract": {"provider": "browserless", "official_endpoint": "https://production-sfo.browserless.io/pdf", "http_method": "POST", "response_type": "application/pdf", "read_only": True, "artifact_binary": True},
            "discovery_policy": {"source": "official-documentation", "documentation_url": "https://docs.browserless.io/rest-apis/pdf-api"},
        },
        {
            "operation_id": "performance",
            "description": "调用 /performance 对公开 HTTPS 页面执行受限 Lighthouse 分类审计。",
            "parameters": ["url", "categories"],
            "parameter_schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "url": {"type": "string", "minLength": 9, "maxLength": 2048, "pattern": "^https://"},
                    "categories": {"type": "array", "minItems": 1, "maxItems": 5, "uniqueItems": True, "items": {"type": "string", "enum": ["accessibility", "best-practices", "performance", "pwa", "seo"]}},
                },
                "required": ["url"],
            },
            "result_contract": {"provider": "browserless", "official_endpoint": "https://production-sfo.browserless.io/performance", "http_method": "POST", "response_type": "application/json", "read_only": True},
            "discovery_policy": {"source": "official-documentation", "documentation_url": "https://docs.browserless.io/rest-apis/performance"},
        },
        {
            "operation_id": "search",
            "description": "调用 Cloud /search 对公开网页执行受限 Web 搜索，最多3条结果且不自动抓取结果页。",
            "parameters": ["query", "limit"],
            "parameter_schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "query": {"type": "string", "minLength": 1, "maxLength": 1000},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 3},
                },
                "required": ["query"],
            },
            "result_contract": {"provider": "browserless", "official_endpoint": "https://production-sfo.browserless.io/search", "http_method": "POST", "response_type": "application/json", "read_only": True, "cloud_plan_may_be_required": True},
            "discovery_policy": {"source": "official-documentation", "documentation_url": "https://docs.browserless.io/rest-apis/search"},
        },
        {
            "operation_id": "map",
            "description": "调用 Cloud /map 发现一个公开 HTTPS 站点的受限 URL 结构，最多100条。",
            "parameters": ["url", "search", "limit", "sitemap", "include_subdomains", "ignore_query_parameters"],
            "parameter_schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "url": {"type": "string", "minLength": 9, "maxLength": 2048, "pattern": "^https://"},
                    "search": {"type": "string", "minLength": 1, "maxLength": 500},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                    "sitemap": {"type": "string", "enum": ["include", "skip", "only"]},
                    "include_subdomains": {"type": "boolean"},
                    "ignore_query_parameters": {"type": "boolean"},
                },
                "required": ["url"],
            },
            "result_contract": {"provider": "browserless", "official_endpoint": "https://production-sfo.browserless.io/map", "http_method": "POST", "response_type": "application/json", "read_only": True, "cloud_plan_may_be_required": True},
            "discovery_policy": {"source": "official-documentation", "documentation_url": "https://docs.browserless.io/rest-apis/map"},
        },
    ],
}

catalog_path = API / "web-retrieval" / "provider-catalog.json"
catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
catalog["providers"] = [row for row in catalog["providers"] if row.get("provider_id") != "browserless"]
catalog["providers"].append(provider)
catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

write(BROWSERLESS / "requirements.txt", """
jsonschema==4.23.0
""")

write(BROWSERLESS / "ticket.schema.json", r'''
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/a15280020511/evidence-data-center/api-center/browserless/ticket.schema.json",
  "title": "Browserless managed read-only ticket",
  "type": "object",
  "additionalProperties": false,
  "required": ["task_id", "provider", "operation", "objective", "parameters", "data_policy", "acceptance"],
  "properties": {
    "task_id": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$"},
    "provider": {"const": "browserless"},
    "operation": {"type": "string", "enum": ["catalog-capabilities", "content", "scrape", "screenshot", "pdf", "performance", "search", "map"]},
    "objective": {"type": "string", "minLength": 1, "maxLength": 1000},
    "parameters": {"type": "object", "maxProperties": 10},
    "data_policy": {
      "type": "object",
      "additionalProperties": false,
      "required": ["classification", "contains_personal_data"],
      "properties": {
        "classification": {"const": "public"},
        "contains_personal_data": {"const": false}
      }
    },
    "acceptance": {
      "type": "object",
      "additionalProperties": false,
      "required": ["timeout_seconds", "max_response_bytes"],
      "properties": {
        "timeout_seconds": {"type": "integer", "minimum": 5, "maximum": 120},
        "max_response_bytes": {"type": "integer", "minimum": 1024, "maximum": 10000000}
      }
    }
  }
}
''')

write(BROWSERLESS / "browserless_task.py", r'''
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
''')

write(BROWSERLESS / "README.md", r'''
# Browserless managed API provider

Browserless is integrated as a bounded, read-only web-rendering provider.

- Ticket prefix: `[api-browserless]`
- Repository Secret: `BROWSERLESS_TOKEN`
- Fixed REST origin: `https://production-sfo.browserless.io`
- Operations: `catalog-capabilities`, `content`, `scrape`, `screenshot`, `pdf`, `performance`, `search`, `map`

The provider accepts only public HTTPS targets. It does not expose BrowserQL, BaaS/WebSocket sessions, `/function`, `/download`, `/export`, `/unblock`, profiles, arbitrary JavaScript, cookies, Authorization headers, custom headers, proxy configuration, geo-proxy configuration, form submission, or write operations.

`search` and `map` may require a Browserless Cloud plan. Actual quota, concurrency and availability are controlled by the Browserless account.
''')

write(BROWSERLESS / "tests" / "test_browserless_task.py", r'''
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("browserless_task", HERE / "browserless_task.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def ticket(operation: str, parameters: dict) -> dict:
    return {
        "task_id": "browserless-test-001",
        "provider": "browserless",
        "operation": operation,
        "objective": "test bounded Browserless provider",
        "parameters": parameters,
        "data_policy": {"classification": "public", "contains_personal_data": False},
        "acceptance": {"timeout_seconds": 30, "max_response_bytes": 1000000},
    }


class BrowserlessTaskTests(unittest.TestCase):
    def test_catalog_contains_expected_safe_operations(self) -> None:
        provider = module.provider_catalog()
        self.assertEqual(provider["required_secret_environment_variable"], "BROWSERLESS_TOKEN")
        self.assertEqual({row["operation_id"] for row in provider["operations"]}, {"catalog-capabilities", "content", "scrape", "screenshot", "pdf", "performance", "search", "map"})
        self.assertFalse(provider["limits"]["arbitrary_code_allowed"])
        self.assertFalse(provider["limits"]["captcha_or_unblock_allowed"])
        self.assertFalse(provider["limits"]["profiles_allowed"])

    @mock.patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("93.184.216.34", 443))])
    def test_public_https_url_is_normalized(self, _resolver: mock.Mock) -> None:
        self.assertEqual(module.validate_public_https_url("https://example.com"), "https://example.com/")

    def test_private_and_credential_urls_are_rejected(self) -> None:
        for value in ("http://example.com", "https://127.0.0.1/", "https://user:pass@example.com/"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                module.validate_public_https_url(value)

    def test_unknown_parameter_is_rejected_by_operation_schema(self) -> None:
        value = ticket("content", {"url": "https://example.com", "headers": {"x": "y"}})
        with self.assertRaises(ValueError):
            module.validate_ticket(value)

    def test_binary_result_is_written_as_artifact_not_json_payload(self) -> None:
        value = ticket("screenshot", {"url": "https://example.com", "image_type": "png"})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            ticket_path.write_text(json.dumps(value), encoding="utf-8")
            with mock.patch.object(module, "validate_public_https_url", return_value="https://example.com/"), mock.patch.object(module, "call_upstream", return_value=(200, b"\x89PNG\r\n", "image/png")):
                self.assertEqual(module.execute(ticket_path, root), 0)
            snapshot = json.loads((root / "snapshot.json").read_text(encoding="utf-8"))
            self.assertEqual(snapshot["artifact_file"], "result.png")
            self.assertTrue((root / "result.png").is_file())
            self.assertNotIn("content", snapshot)

    def test_missing_secret_fails_without_exposing_value(self) -> None:
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "BROWSERLESS_TOKEN"):
                module.token()


if __name__ == "__main__":
    unittest.main()
''')

write(WORKFLOWS / "browserless-api-ticket.yml", r'''
name: Managed Browserless API Center

on:
  issues:
    types: [opened, reopened]

permissions:
  contents: read
  issues: write
  actions: read

concurrency:
  group: api-browserless-ticket-${{ github.event.issue.number }}
  cancel-in-progress: false

jobs:
  execute-browserless-api:
    if: >-
      github.actor == github.repository_owner &&
      startsWith(github.event.issue.title, '[api-browserless]')
    runs-on: ubuntu-24.04
    timeout-minutes: 20
    env:
      GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      ISSUE_NUMBER: ${{ github.event.issue.number }}
      BROWSERLESS_TOKEN: ${{ secrets.BROWSERLESS_TOKEN }}
    steps:
      - name: Checkout pinned source
        uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4
        with:
          persist-credentials: false

      - name: Set up isolated Python
        uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: api-center/browserless/requirements.txt

      - name: Install pinned dependencies
        run: |
          python -m pip install --disable-pip-version-check --no-input -r api-center/browserless/requirements.txt
          python -m pip check

      - name: Compile managed provider control plane
        run: python -m py_compile api-center/browserless/browserless_task.py

      - name: Parse and authorize Browserless ticket
        id: prepare
        continue-on-error: true
        run: |
          python api-center/browserless/browserless_task.py prepare --event-path "$GITHUB_EVENT_PATH" --output-dir browserless-artifacts

      - name: Comment accepted ticket
        if: steps.prepare.outputs.accepted == 'true'
        run: |
          python api-center/browserless/browserless_task.py render --output-dir browserless-artifacts --phase accepted > browserless-comment.md
          gh api --method POST "repos/${GITHUB_REPOSITORY}/issues/${ISSUE_NUMBER}/comments" -F body=@browserless-comment.md

      - name: Comment rejected ticket
        if: steps.prepare.outputs.accepted != 'true'
        run: |
          python api-center/browserless/browserless_task.py render --output-dir browserless-artifacts --phase rejected > browserless-comment.md
          gh api --method POST "repos/${GITHUB_REPOSITORY}/issues/${ISSUE_NUMBER}/comments" -F body=@browserless-comment.md

      - name: Execute bounded read-only Browserless operation
        id: execute
        if: steps.prepare.outputs.accepted == 'true'
        continue-on-error: true
        run: |
          python api-center/browserless/browserless_task.py execute --ticket browserless-artifacts/ticket.json --output-dir browserless-artifacts

      - name: Upload Browserless evidence
        id: upload
        if: always()
        continue-on-error: true
        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4
        with:
          name: browserless-api-ticket-${{ github.event.issue.number }}-${{ github.run_id }}
          path: browserless-artifacts/
          if-no-files-found: error
          retention-days: 30

      - name: Publish verified result or structured failure
        if: always() && steps.prepare.outputs.accepted == 'true'
        env:
          ARTIFACT_URL: ${{ steps.upload.outputs.artifact-url }}
        run: |
          python api-center/browserless/browserless_task.py render --output-dir browserless-artifacts --phase completed --artifact-url "$ARTIFACT_URL" > browserless-comment.md
          gh api --method POST "repos/${GITHUB_REPOSITORY}/issues/${ISSUE_NUMBER}/comments" -F body=@browserless-comment.md

      - name: Mark rejected or failed execution
        if: >-
          always() &&
          (steps.prepare.outputs.accepted != 'true' ||
           steps.execute.outputs.status != 'API_BROWSERLESS_COMPLETED' ||
           steps.upload.outcome != 'success')
        run: |
          echo "Browserless API ticket did not complete successfully."
          exit 1
''')

write(WORKFLOWS / "browserless-provider-validate.yml", r'''
name: Validate Browserless Provider

on:
  pull_request:
    paths:
      - "api-center/browserless/**"
      - "api-center/web-retrieval/provider-catalog.json"
      - ".github/workflows/browserless-*.yml"
      - "api-center/tests/test_api_catalog.py"
      - "api-center/api-catalog.json"
      - "api-center/api-catalog.md"
  push:
    branches: [main]
    paths:
      - "api-center/browserless/**"
      - "api-center/web-retrieval/provider-catalog.json"

permissions:
  contents: read

jobs:
  validate:
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4
      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: api-center/browserless/requirements.txt
      - run: |
          python -m pip install --disable-pip-version-check --no-input -r api-center/browserless/requirements.txt
          python -m pip check
          python -m py_compile api-center/browserless/browserless_task.py
          python -m unittest discover -s api-center/browserless/tests -p 'test_*.py' -v
          python -m unittest api-center.tests.test_api_catalog -v
          python api-center/build_catalog_market_search.py
          git diff --exit-code -- api-center/api-catalog.json api-center/api-catalog.md
''')

readme = API / "README.md"
readme_text = readme.read_text(encoding="utf-8")
marker = "## Browserless 托管浏览器 API"
if marker not in readme_text:
    readme_text += textwrap.dedent(r'''

## Browserless 托管浏览器 API

`api-center/browserless/` 使用 Browserless Cloud 固定 REST 主机：

```text
https://production-sfo.browserless.io
```

正式票据前缀和独立 Repository Secret：

```text
[api-browserless]
BROWSERLESS_TOKEN
```

固定开放 8 项操作：本地能力目录、JavaScript 渲染 HTML、CSS 选择器结构化抓取、截图、PDF、Lighthouse 性能审计、受限 Web 搜索和站点地图。Search 与 Map 可能要求 Browserless Cloud 套餐。

安全边界禁止 BrowserQL、BaaS/WebSocket、Function、Download、Export、Unblock、任意 JavaScript、Profile、Cookie、Authorization、自定义请求头、代理配置、CAPTCHA 求解和登录态页面。目标只允许公开 HTTPS URL；二进制截图和 PDF 只进入 Artifact。
''')
    readme.write_text(readme_text, encoding="utf-8")

test_path = API / "tests" / "test_api_catalog.py"
test_text = test_path.read_text(encoding="utf-8")
replacements = {
    '    "firecrawl": 4,\n': '    "firecrawl": 4,\n    "browserless": 8,\n',
    'self.assertEqual(catalog["managed_provider_count"], 22)': 'self.assertEqual(catalog["managed_provider_count"], 23)',
    'self.assertEqual(catalog["enabled_managed_provider_count"], 22)': 'self.assertEqual(catalog["enabled_managed_provider_count"], 23)',
    'self.assertEqual(catalog["managed_operation_count"], 226)': 'self.assertEqual(catalog["managed_operation_count"], 234)',
    '            "firecrawl": "FIRECRAWL_API_KEY",\n': '            "firecrawl": "FIRECRAWL_API_KEY",\n            "browserless": "BROWSERLESS_TOKEN",\n',
}
for old, new in replacements.items():
    if old not in test_text and new not in test_text:
        raise RuntimeError(f"expected test marker not found: {old!r}")
    test_text = test_text.replace(old, new)
assertion_marker = '        self.assertEqual(providers["data-commons"]["ticket_prefix"], "[api-dc]")\n'
if 'providers["browserless"]["ticket_prefix"]' not in test_text:
    browserless_assertions = '''        self.assertEqual(providers["browserless"]["ticket_prefix"], "[api-browserless]")
        self.assertEqual(providers["browserless"]["required_secret_environment_variable_name"], "BROWSERLESS_TOKEN")
        self.assertEqual(providers["browserless"]["limits"]["fixed_api_host"], "production-sfo.browserless.io")
        self.assertFalse(providers["browserless"]["limits"]["arbitrary_code_allowed"])
        self.assertFalse(providers["browserless"]["limits"]["captcha_or_unblock_allowed"])
        self.assertFalse(providers["browserless"]["limits"]["profiles_allowed"])

'''
    if assertion_marker not in test_text:
        raise RuntimeError("browserless assertion insertion marker missing")
    test_text = test_text.replace(assertion_marker, browserless_assertions + assertion_marker)
test_path.write_text(test_text, encoding="utf-8")

print(json.dumps({"status": "prepared", "provider": "browserless", "operations": 8}, ensure_ascii=False))
