#!/usr/bin/env python3
"""One-shot deterministic EODHD managed-provider integration."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "api-center"
TARGET = API / "eodhd"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, value: object) -> None:
    write(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def string(max_length: int = 200, pattern: str | None = None, enum: list[str] | None = None) -> dict:
    out: dict[str, object] = {"type": "string", "maxLength": max_length}
    if pattern:
        out["pattern"] = pattern
    if enum:
        out["enum"] = enum
    return out


DATE = string(10, r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
SYMBOL = string(64, r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")
SYMBOLS = string(1000, r"^[A-Za-z0-9._,:-]+$")
EXCHANGE = string(32, r"^[A-Za-z0-9][A-Za-z0-9 _.-]{0,31}$")
QUERY = string(120, r"^[^/?#\\]{1,120}$")


def schema(properties: dict[str, object], required: list[str] | None = None) -> dict:
    value: dict[str, object] = {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
    }
    if required:
        value["required"] = required
    return value


operations: list[dict[str, object]] = []


def add(
    operation_id: str,
    description: str,
    path_template: str,
    properties: dict[str, object],
    *,
    required: list[str] | None = None,
    path_parameters: list[str] | None = None,
    query_parameter_map: dict[str, str] | None = None,
    local: bool = False,
) -> None:
    operations.append({
        "operation_id": operation_id,
        "description": description,
        "parameters": list(properties),
        "parameter_schema": schema(properties, required),
        "execution": {
            "local": local,
            "path_template": path_template,
            "path_parameters": path_parameters or [],
            "query_parameter_map": query_parameter_map or {},
            "force_query": {} if local else {"fmt": "json"},
        },
        "result_contract": {
            "provider": "eodhd",
            "official_origin": "https://eodhd.com",
            "http_method": "LOCAL" if local else "GET",
            "read_only": True,
            "credential_mode": "none" if local else "api_token_query_backend_only",
        },
    })


add("catalog-capabilities", "读取本地 EODHD 安全能力目录，不访问上游。", "", {}, local=True)
add("exchanges-list", "读取 EODHD 支持的全球交易所、虚拟市场和基础元数据。", "/api/exchanges-list/", {})
add(
    "exchange-symbols",
    "读取指定交易所当前或退市证券目录。",
    "/api/exchange-symbol-list/{exchange}",
    {
        "exchange": EXCHANGE,
        "delisted": {"type": "boolean"},
        "type": string(32, enum=["common_stock", "preferred_stock", "stock", "etf", "fund"]),
    },
    required=["exchange"],
    path_parameters=["exchange"],
)
add(
    "symbol-search",
    "按代码或名称搜索全球证券、基金、指数、外汇、债券和数字资产。",
    "/api/search/{query}",
    {
        "query": QUERY,
        "exchange": EXCHANGE,
        "limit": {"type": "integer", "minimum": 1, "maximum": 100},
        "bonds_only": {"type": "boolean"},
    },
    required=["query"],
    path_parameters=["query"],
)
add(
    "eod-history",
    "读取单一证券的日、周或月末历史 OHLCV 与复权价格。",
    "/api/eod/{symbol}",
    {
        "symbol": SYMBOL,
        "from_date": DATE,
        "to_date": DATE,
        "period": string(1, enum=["d", "w", "m"]),
        "order": string(1, enum=["a", "d"]),
    },
    required=["symbol"],
    path_parameters=["symbol"],
    query_parameter_map={"from_date": "from", "to_date": "to"},
)
add(
    "intraday-history",
    "读取单一证券的分钟或小时级历史行情。",
    "/api/intraday/{symbol}",
    {
        "symbol": SYMBOL,
        "interval": string(2, enum=["1m", "5m", "1h"]),
        "from_timestamp": {"type": "integer", "minimum": 0, "maximum": 4102444800},
        "to_timestamp": {"type": "integer", "minimum": 0, "maximum": 4102444800},
    },
    required=["symbol", "interval"],
    path_parameters=["symbol"],
    query_parameter_map={"from_timestamp": "from", "to_timestamp": "to"},
)
add(
    "real-time-quote",
    "读取单一证券的实时或延迟报价快照；数据权限由 EODHD 套餐决定。",
    "/api/real-time/{symbol}",
    {"symbol": SYMBOL},
    required=["symbol"],
    path_parameters=["symbol"],
)
add(
    "fundamentals",
    "读取股票、ETF、基金或指数的结构化基本面数据。",
    "/api/v1.1/fundamentals/{symbol}",
    {
        "symbol": SYMBOL,
        "filter": string(300, r"^[A-Za-z0-9._,-]+$"),
    },
    required=["symbol"],
    path_parameters=["symbol"],
)
add(
    "dividends-history",
    "读取单一证券的历史分红记录。",
    "/api/div/{symbol}",
    {"symbol": SYMBOL, "from_date": DATE, "to_date": DATE},
    required=["symbol"],
    path_parameters=["symbol"],
    query_parameter_map={"from_date": "from", "to_date": "to"},
)
add(
    "splits-history",
    "读取单一证券的历史拆股和合股记录。",
    "/api/splits/{symbol}",
    {"symbol": SYMBOL, "from_date": DATE, "to_date": DATE},
    required=["symbol"],
    path_parameters=["symbol"],
    query_parameter_map={"from_date": "from", "to_date": "to"},
)
add(
    "bulk-eod",
    "按交易所和日期读取整市场 EOD、拆股或分红批量数据。",
    "/api/eod-bulk-last-day/{exchange}",
    {
        "exchange": EXCHANGE,
        "date": DATE,
        "type": string(16, enum=["eod", "splits", "dividends"]),
        "symbols": SYMBOLS,
    },
    required=["exchange"],
    path_parameters=["exchange"],
)
add(
    "historical-market-cap",
    "读取美国股票或数字资产的历史市值序列。",
    "/api/historical-market-cap/{symbol}",
    {"symbol": SYMBOL, "from_date": DATE, "to_date": DATE},
    required=["symbol"],
    path_parameters=["symbol"],
    query_parameter_map={"from_date": "from", "to_date": "to"},
)
add(
    "technical-indicator",
    "在固定证券和日期范围上计算 EODHD 技术指标。",
    "/api/technical/{symbol}",
    {
        "symbol": SYMBOL,
        "function": string(24, enum=[
            "sma", "ema", "wma", "volatility", "rsi", "stddev", "stoch",
            "stochrsi", "slope", "dmi", "adx", "macd", "atr", "cci", "sar", "beta", "bbands",
        ]),
        "period": {"type": "integer", "minimum": 2, "maximum": 1000},
        "from_date": DATE,
        "to_date": DATE,
        "order": string(1, enum=["a", "d"]),
        "splitadjusted": {"type": "boolean"},
    },
    required=["symbol", "function"],
    path_parameters=["symbol"],
    query_parameter_map={"from_date": "from", "to_date": "to"},
)
add(
    "financial-news",
    "读取按证券或主题过滤的金融新闻。",
    "/api/news",
    {
        "symbols": SYMBOLS,
        "tag": string(120, r"^[^/?#\\]{1,120}$"),
        "from_date": DATE,
        "to_date": DATE,
        "limit": {"type": "integer", "minimum": 1, "maximum": 1000},
        "offset": {"type": "integer", "minimum": 0, "maximum": 100000},
    },
    query_parameter_map={"symbols": "s", "tag": "t", "from_date": "from", "to_date": "to"},
)
add(
    "sentiments",
    "读取一个或多个证券的每日新闻情绪分数。",
    "/api/sentiments",
    {"symbols": SYMBOLS, "from_date": DATE, "to_date": DATE},
    required=["symbols"],
    query_parameter_map={"symbols": "s", "from_date": "from", "to_date": "to"},
)
add(
    "screener",
    "使用受控字段和比较运算筛选全球股票。",
    "/api/screener",
    {
        "filters_json": string(4000),
        "sort": string(80, r"^[A-Za-z0-9_]+\.(asc|desc)$"),
        "signals": string(500, r"^[A-Za-z0-9_,.-]+$"),
        "limit": {"type": "integer", "minimum": 1, "maximum": 1000},
        "offset": {"type": "integer", "minimum": 0, "maximum": 100000},
    },
    query_parameter_map={"filters_json": "filters"},
)
for operation_id, description, endpoint in (
    ("calendar-earnings", "读取历史和未来财报发布日期。", "/api/calendar/earnings"),
    ("calendar-trends", "读取证券盈利预期趋势。", "/api/calendar/trends"),
    ("calendar-ipos", "读取历史和未来 IPO 日历。", "/api/calendar/ipos"),
    ("calendar-splits", "读取历史和未来拆股日历。", "/api/calendar/splits"),
):
    add(
        operation_id,
        description,
        endpoint,
        {"symbols": SYMBOLS, "from_date": DATE, "to_date": DATE},
        query_parameter_map={"symbols": "symbols", "from_date": "from", "to_date": "to"},
    )
add(
    "calendar-dividends",
    "读取历史和未来分红日历并支持分页。",
    "/api/calendar/dividends",
    {
        "symbol": SYMBOL,
        "from_date": DATE,
        "to_date": DATE,
        "limit": {"type": "integer", "minimum": 1, "maximum": 1000},
        "offset": {"type": "integer", "minimum": 0, "maximum": 100000},
    },
    query_parameter_map={
        "symbol": "filter[symbol]",
        "from_date": "filter[date_from]",
        "to_date": "filter[date_to]",
    },
)
add(
    "macro-indicator",
    "读取指定国家和宏观指标的历史序列。",
    "/api/macro-indicator/{country}",
    {
        "country": string(80, r"^[A-Za-z][A-Za-z ._-]{1,79}$"),
        "indicator": string(80, r"^[A-Za-z0-9_ -]{1,80}$"),
    },
    required=["country", "indicator"],
    path_parameters=["country"],
)
add(
    "economic-events",
    "读取受控日期、国家和事件范围内的宏观经济事件。",
    "/api/economic-events",
    {
        "from_date": DATE,
        "to_date": DATE,
        "country": string(80, r"^[A-Za-z][A-Za-z ,._-]{1,79}$"),
        "comparison": string(16, enum=["mom", "qoq", "yoy"]),
        "limit": {"type": "integer", "minimum": 1, "maximum": 1000},
        "offset": {"type": "integer", "minimum": 0, "maximum": 100000},
    },
    query_parameter_map={"from_date": "from", "to_date": "to"},
)
add("exchange-details-list", "读取 EODHD v2 交易所详情目录。", "/api/v2/exchange-details", {})
add(
    "exchange-details",
    "读取指定交易所时区、交易时段、节假日和提前收市信息。",
    "/api/v2/exchange-details/{exchange}",
    {"exchange": EXCHANGE},
    required=["exchange"],
    path_parameters=["exchange"],
)

assert len(operations) == 25

provider_catalog = {
    "schema_version": "eodhd-provider-catalog-v1",
    "secret_values_exposed": False,
    "replaced_legacy_connectors": [],
    "providers": [{
        "provider_id": "eodhd",
        "display_name": "EODHD 全球金融市场数据",
        "description": "通过 EODHD 官方 HTTPS REST API 读取全球交易所、证券目录、历史和实时行情、基本面、公司行动、技术指标、新闻情绪、筛选器、企业日历、宏观事件及交易时段。",
        "enabled": True,
        "ticket_prefix": "[api-eodhd]",
        "required_secret_environment_variable": "EODHD_API_TOKEN",
        "catalog_policy": "仅开放显式登记的固定 GET 路径和参数 Schema；禁止任意 URL、任意路径、任意请求头、用户自定义 api_token、WebSocket、交易、下单、账户修改和数据写入。",
        "execution_policy": "EODHD_API_TOKEN 仅在后端查询参数中注入且不会进入日志、Issue 或 Artifact；每张票据最多一次正常请求和一次瞬态故障重试，并限制超时、响应体积、结果行数和筛选器结构。",
        "limits": {
            "requests_per_ticket_max": 2,
            "timeout_seconds_max": 60,
            "max_response_bytes": 20000000,
            "max_rows": 50000,
            "arbitrary_urls_allowed": False,
            "arbitrary_paths_allowed": False,
            "arbitrary_headers_allowed": False,
            "client_supplied_token_allowed": False,
            "websocket_allowed": False,
            "write_operations_allowed": False,
            "trading_or_order_execution_allowed": False,
            "secret_values_exposed": False,
        },
        "operations": operations,
    }],
}
write_json(TARGET / "provider-catalog.json", provider_catalog)

operation_ids = [row["operation_id"] for row in operations]
ticket_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://github.com/a15280020511/evidence-data-center/api-center/eodhd/ticket.schema.json",
    "title": "EODHD managed read-only ticket",
    "type": "object",
    "additionalProperties": False,
    "required": ["task_id", "provider", "operation", "objective", "parameters", "data_policy", "acceptance"],
    "properties": {
        "task_id": {"type": "string", "pattern": r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$"},
        "provider": {"const": "eodhd"},
        "operation": {"type": "string", "enum": operation_ids},
        "objective": {"type": "string", "minLength": 1, "maxLength": 1000},
        "parameters": {"type": "object"},
        "data_policy": {
            "type": "object",
            "additionalProperties": False,
            "required": ["classification", "contains_personal_data"],
            "properties": {"classification": {"const": "public"}, "contains_personal_data": {"const": False}},
        },
        "acceptance": {
            "type": "object",
            "additionalProperties": False,
            "required": ["timeout_seconds", "max_response_bytes", "max_rows"],
            "properties": {
                "timeout_seconds": {"type": "integer", "minimum": 5, "maximum": 60},
                "max_response_bytes": {"type": "integer", "minimum": 1024, "maximum": 20000000},
                "max_rows": {"type": "integer", "minimum": 1, "maximum": 50000},
            },
        },
    },
}
write_json(TARGET / "ticket.schema.json", ticket_schema)
write(TARGET / "requirements.txt", "jsonschema==4.26.0\n")
write(TARGET / "README.md", """# EODHD 全球金融市场数据\n\n- Provider：`eodhd`\n- 票据前缀：`[api-eodhd]`\n- Repository Secret：`EODHD_API_TOKEN`\n- 协议：固定 `GET https://eodhd.com/api/...`，后端注入 `api_token`。\n- 当前开放 25 项固定只读操作。\n- 禁止任意 URL、任意路径、任意请求头、WebSocket、交易、下单、账户修改和写入。\n\n每张正式票据生成 Snapshot、Diagnostics、Manifest、摘要与 GitHub Actions Artifact；上游套餐、调用额度和数据范围由 EODHD 账户决定。\n""")

runtime = r'''#!/usr/bin/env python3
"""Bounded read-only EODHD REST API execution control plane."""
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
from typing import Any, Callable, Mapping

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE / "ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"
ORIGIN = "https://eodhd.com"
TOKEN_ENV = "EODHD_API_TOKEN"
ALLOWED_SCREENER_FIELDS = {
    "code", "name", "exchange", "sector", "industry", "market_capitalization",
    "earnings_share", "dividend_yield", "adjusted_close", "refund_1d_p", "refund_5d_p",
    "avgvol_1d", "avgvol_200d",
}
ALLOWED_SCREENER_OPERATORS = {"=", "!=", ">", "<", ">=", "<=", "match", "not_match"}


class EodhdError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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


def provider_catalog() -> Mapping[str, Any]:
    return load_json(CATALOG_PATH)["providers"][0]


def operation_catalog(operation: str) -> Mapping[str, Any]:
    for row in provider_catalog()["operations"]:
        if row["operation_id"] == operation:
            return row
    raise ValueError(f"unsupported EODHD operation: {operation}")


def validate_screener(parameters: Mapping[str, Any]) -> None:
    raw = parameters.get("filters_json")
    if raw in (None, ""):
        return
    try:
        value = json.loads(str(raw))
    except json.JSONDecodeError as exc:
        raise ValueError("parameters.filters_json must contain valid JSON") from exc
    if not isinstance(value, list) or len(value) > 20:
        raise ValueError("parameters.filters_json must be a list with at most 20 filters")
    for item in value:
        if not isinstance(item, list) or len(item) != 3:
            raise ValueError("each screener filter must be [field, operator, value]")
        field, operator, _ = item
        if str(field) not in ALLOWED_SCREENER_FIELDS:
            raise ValueError(f"unsupported screener field: {field}")
        if str(operator) not in ALLOWED_SCREENER_OPERATORS:
            raise ValueError(f"unsupported screener operator: {operator}")


def validate_ticket(ticket: Mapping[str, Any]) -> None:
    errors = sorted(Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(ticket), key=lambda item: list(item.absolute_path))
    if errors:
        raise ValueError("; ".join(
            f"{'.'.join(str(x) for x in item.absolute_path) or '$'}: {item.message}"
            for item in errors[:20]
        ))
    operation = str(ticket["operation"])
    schema = operation_catalog(operation)["parameter_schema"]
    parameter_errors = sorted(Draft202012Validator(schema).iter_errors(ticket.get("parameters") or {}), key=lambda item: list(item.absolute_path))
    if parameter_errors:
        raise ValueError("; ".join(
            f"parameters.{'.'.join(str(x) for x in item.absolute_path)}: {item.message}"
            for item in parameter_errors[:20]
        ))
    if operation == "screener":
        validate_screener(ticket.get("parameters") or {})


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
        if not title.startswith("[api-eodhd]"):
            raise ValueError("issue title must start with [api-eodhd]")
        ticket = parsed
        accepted = True
        write_json(output_dir / "ticket.json", ticket)
    except (json.JSONDecodeError, ValueError) as exc:
        reason = str(exc)
    status = {
        "schema_version": "eodhd-ticket-status-v1",
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


def token() -> str:
    value = str(os.getenv(TOKEN_ENV) or "").strip()
    if not value:
        raise EodhdError("EODHD_TOKEN_MISSING", f"missing repository Secret {TOKEN_ENV}")
    return value


def scrub(value: str, secret: str) -> str:
    return value.replace(secret, "[REDACTED]") if secret else value


def encode_query_value(value: Any) -> str:
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)


def build_request(operation: str, parameters: Mapping[str, Any], secret: str) -> tuple[urllib.request.Request, dict[str, Any]]:
    row = operation_catalog(operation)
    execution = row["execution"]
    path = str(execution["path_template"])
    clean = dict(parameters)
    for name in execution.get("path_parameters") or []:
        value = clean.pop(name)
        path = path.replace("{" + name + "}", urllib.parse.quote(str(value), safe="._-"))
    query_map = dict(execution.get("query_parameter_map") or {})
    query: dict[str, str] = {}
    for name, value in clean.items():
        if value in (None, ""):
            continue
        target = str(query_map.get(name) or name)
        if operation == "screener" and name == "filters_json":
            parsed = json.loads(str(value))
            value = json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
        query[target] = encode_query_value(value)
    for name, value in dict(execution.get("force_query") or {}).items():
        query[str(name)] = str(value)
    query["api_token"] = secret
    url = ORIGIN + path + "?" + urllib.parse.urlencode(query, doseq=False, safe="[],")
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "gpts-evidence-data-center-eodhd/1"}, method="GET")
    metadata = {
        "request_origin": "eodhd.com",
        "request_path": path,
        "http_method": "GET",
        "credential_mode": "api_token_query_backend_only",
        "credential_environment_variable": TOKEN_ENV,
        "secret_value_exposed": False,
    }
    return request, metadata


def _read_once(request: urllib.request.Request, *, timeout: int, max_bytes: int, opener: Callable[..., Any]) -> tuple[int, bytes, str]:
    try:
        with opener(request, timeout=timeout) as response:
            status = int(getattr(response, "status", 200))
            raw = response.read(max_bytes + 1)
            content_type = str(response.headers.get("Content-Type") or "")
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        raw = exc.read(max_bytes + 1)
        content_type = str(exc.headers.get("Content-Type") or "") if exc.headers else ""
    if len(raw) > max_bytes:
        raise EodhdError("EODHD_RESPONSE_TOO_LARGE", "upstream response exceeded max_response_bytes")
    return status, raw, content_type


def row_count(payload: Any) -> int:
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, Mapping):
        for key in ("data", "results", "items"):
            nested = payload.get(key)
            if isinstance(nested, list):
                return len(nested)
        return len(payload)
    return 1


def query_eodhd(
    operation: str,
    parameters: Mapping[str, Any],
    *,
    timeout: int,
    max_bytes: int,
    max_rows: int,
    opener: Callable[..., Any] = urllib.request.urlopen,
    sleeper: Callable[[float], None] = time.sleep,
) -> tuple[Any, dict[str, Any]]:
    secret = token()
    request, metadata = build_request(operation, parameters, secret)
    attempts = 0
    while attempts < 2:
        attempts += 1
        try:
            status, raw, content_type = _read_once(request, timeout=timeout, max_bytes=max_bytes, opener=opener)
        except urllib.error.URLError as exc:
            if attempts < 2:
                sleeper(1.0)
                continue
            raise EodhdError("EODHD_CONNECTION_FAILED", f"upstream connection failed: {type(exc.reason).__name__}", retryable=True) from exc
        if status == 429 or 500 <= status <= 599:
            if attempts < 2:
                sleeper(1.0)
                continue
            raise EodhdError("EODHD_HTTP_TRANSIENT", f"upstream HTTP {status}", retryable=True)
        if status in {401, 403}:
            raise EodhdError("EODHD_AUTH_FAILED", f"upstream HTTP {status}")
        if not 200 <= status < 300:
            detail = scrub(raw[:1000].decode("utf-8", errors="replace"), secret)
            raise EodhdError("EODHD_HTTP_ERROR", f"upstream HTTP {status}: {detail}")
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else None
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise EodhdError("EODHD_INVALID_JSON", "upstream returned invalid JSON") from exc
        if isinstance(payload, Mapping):
            error_message = payload.get("error") or payload.get("message")
            code = payload.get("code")
            if error_message and (code is not None or len(payload) <= 3):
                raise EodhdError("EODHD_BUSINESS_ERROR", scrub(str(error_message), secret))
        count = row_count(payload)
        if count > max_rows:
            raise EodhdError("EODHD_RESULT_TOO_MANY_ROWS", f"upstream result has {count} rows; max_rows is {max_rows}")
        metadata.update({
            "http_status": status,
            "content_type": content_type,
            "upstream_called": True,
            "transport_attempts": attempts,
            "row_count": count,
            "response_bytes": len(raw),
        })
        return payload, metadata
    raise EodhdError("EODHD_CONNECTION_FAILED", "upstream connection failed", retryable=True)


def write_manifest(output_dir: Path, snapshot_sha: str | None = None) -> None:
    files = sorted(path.name for path in output_dir.iterdir() if path.is_file() and path.name != "artifact-manifest.json")
    write_json(output_dir / "artifact-manifest.json", {
        "schema_version": "eodhd-artifact-manifest-v1",
        "files": files,
        "snapshot_sha256": snapshot_sha,
        "secret_values_included": False,
        "model_calls": 0,
    })


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket)
    operation = str(ticket["operation"])
    started_at = utc_now()
    try:
        if operation == "catalog-capabilities":
            result = load_json(CATALOG_PATH)
            metadata = {"upstream_called": False, "credential_mode": "none", "secret_value_exposed": False, "operation_count": len(provider_catalog()["operations"]), "row_count": len(provider_catalog()["operations"])}
        else:
            acceptance = ticket["acceptance"]
            result, metadata = query_eodhd(
                operation,
                ticket.get("parameters") or {},
                timeout=int(acceptance["timeout_seconds"]),
                max_bytes=int(acceptance["max_response_bytes"]),
                max_rows=int(acceptance["max_rows"]),
            )
        snapshot = {
            "schema_version": "eodhd-api-snapshot-v1",
            "status": "API_EODHD_COMPLETED",
            "task_id": ticket["task_id"],
            "provider": "eodhd",
            "operation": operation,
            "started_at": started_at,
            "completed_at": utc_now(),
            "ticket_sha256": canonical_sha(ticket),
            "metadata": metadata,
            "result": result,
            "secret_values_exposed": False,
            "model_calls": 0,
        }
        snapshot["snapshot_sha256"] = canonical_sha(snapshot)
        write_json(output_dir / "eodhd-snapshot.json", snapshot)
        write_json(output_dir / "eodhd-diagnostics.json", {"schema_version": "eodhd-diagnostics-v1", "status": snapshot["status"], "failure": None, "secret_values_exposed": False, "model_calls": 0})
        (output_dir / "eodhd-summary.md").write_text(
            "\n".join(["# API_EODHD_COMPLETED", "", f"- Task ID: `{snapshot['task_id']}`", f"- Operation: `{operation}`", f"- Rows: `{metadata.get('row_count', 0)}`", f"- Snapshot SHA-256: `{snapshot['snapshot_sha256']}`", "- Secret values exposed: `false`", "- Model calls: `0`", ""]),
            encoding="utf-8",
        )
        write_manifest(output_dir, snapshot["snapshot_sha256"])
        write_output("status", snapshot["status"])
        write_output("snapshot_sha256", snapshot["snapshot_sha256"])
        return 0
    except EodhdError as exc:
        failure = {
            "schema_version": "eodhd-diagnostics-v1",
            "status": "API_EODHD_FAILED",
            "task_id": ticket.get("task_id"),
            "provider": "eodhd",
            "operation": operation,
            "started_at": started_at,
            "failed_at": utc_now(),
            "error": {"code": exc.code, "message": str(exc)[:4000], "retryable": exc.retryable},
            "secret_values_exposed": False,
            "model_calls": 0,
        }
        failure["diagnostics_sha256"] = canonical_sha(failure)
        write_json(output_dir / "eodhd-diagnostics.json", failure)
        (output_dir / "eodhd-summary.md").write_text(
            "\n".join(["# API_EODHD_FAILED", "", f"- Task ID: `{failure['task_id']}`", f"- Operation: `{operation}`", f"- Error code: `{exc.code}`", f"- Message: {str(exc)[:1000]}", "- Secret values exposed: `false`", "- Model calls: `0`", ""]),
            encoding="utf-8",
        )
        write_manifest(output_dir)
        write_output("status", failure["status"])
        write_output("error_code", exc.code)
        return 1


def render(output_dir: Path, phase: str, artifact_url: str = "") -> int:
    if phase in {"accepted", "rejected"}:
        status = load_json(output_dir / "ticket-status.json")
        heading = "API_EODHD_ACCEPTED" if status["accepted"] else "API_EODHD_REJECTED"
        print(f"## {heading}\n")
        print(f"- Task ID: `{status.get('task_id') or 'unknown'}`")
        print(f"- Operation: `{status.get('operation') or 'unknown'}`")
        print(f"- Ticket SHA-256: `{status.get('ticket_sha256') or 'unavailable'}`")
        if not status["accepted"]:
            print(f"- Reason: `{status.get('reason') or 'invalid ticket'}`")
        print("- Secret values exposed: `false`")
        print("- Model calls: `0`")
        return 0
    snapshot_path = output_dir / "eodhd-snapshot.json"
    if snapshot_path.exists():
        snapshot = load_json(snapshot_path)
        metadata = snapshot.get("metadata") or {}
        print("## API_EODHD_COMPLETED\n")
        print(f"- Task ID: `{snapshot['task_id']}`")
        print(f"- Operation: `{snapshot['operation']}`")
        print(f"- Upstream called: `{str(bool(metadata.get('upstream_called'))).lower()}`")
        print(f"- Rows: `{metadata.get('row_count', 0)}`")
        print(f"- Snapshot SHA-256: `{snapshot['snapshot_sha256']}`")
        if artifact_url:
            print(f"- Artifact: {artifact_url}")
        print("- Secret values exposed: `false`")
        print("- Model calls: `0`")
        return 0
    failure = load_json(output_dir / "eodhd-diagnostics.json")
    error = failure.get("error") or {}
    print("## API_EODHD_FAILED\n")
    print(f"- Task ID: `{failure.get('task_id') or 'unknown'}`")
    print(f"- Operation: `{failure.get('operation') or 'unknown'}`")
    print(f"- Error code: `{error.get('code') or 'EODHD_UNKNOWN'}`")
    print(f"- Message: {error.get('message') or 'unknown failure'}")
    if artifact_url:
        print(f"- Artifact: {artifact_url}")
    print("- Secret values exposed: `false`")
    print("- Model calls: `0`")
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
'''
write(TARGET / "eodhd_task.py", runtime)

tests = r'''from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("eodhd_task", ROOT / "eodhd_task.py")
assert SPEC and SPEC.loader
eodhd = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(eodhd)


class FakeResponse:
    status = 200
    headers = {"Content-Type": "application/json"}

    def __init__(self, payload: object) -> None:
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, limit: int) -> bytes:
        return self.payload[:limit]


class EodhdTests(unittest.TestCase):
    def ticket(self, operation: str, parameters: dict) -> dict:
        return {
            "task_id": "eodhd-test-001",
            "provider": "eodhd",
            "operation": operation,
            "objective": "test bounded read-only EODHD provider",
            "parameters": parameters,
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "acceptance": {"timeout_seconds": 10, "max_response_bytes": 100000, "max_rows": 100},
        }

    def test_catalog_has_fixed_readonly_surface(self) -> None:
        provider = eodhd.provider_catalog()
        self.assertEqual(provider["required_secret_environment_variable"], "EODHD_API_TOKEN")
        self.assertEqual(len(provider["operations"]), 25)
        self.assertFalse(provider["limits"]["arbitrary_urls_allowed"])
        self.assertFalse(provider["limits"]["trading_or_order_execution_allowed"])

    def test_rejects_arbitrary_parameters_and_bad_screener(self) -> None:
        with self.assertRaises(ValueError):
            eodhd.validate_ticket(self.ticket("eod-history", {"symbol": "AAPL.US", "url": "https://evil.test"}))
        with self.assertRaises(ValueError):
            eodhd.validate_ticket(self.ticket("screener", {"filters_json": '[["unknown",">",1]]'}))

    def test_build_request_injects_token_without_metadata_leak(self) -> None:
        request, metadata = eodhd.build_request(
            "eod-history",
            {"symbol": "AAPL.US", "from_date": "2026-07-01", "to_date": "2026-07-31"},
            "secret-token",
        )
        parsed = urllib.parse.urlsplit(request.full_url)
        query = urllib.parse.parse_qs(parsed.query)
        self.assertEqual(parsed.netloc, "eodhd.com")
        self.assertEqual(parsed.path, "/api/eod/AAPL.US")
        self.assertEqual(query["api_token"], ["secret-token"])
        self.assertEqual(query["fmt"], ["json"])
        self.assertNotIn("secret-token", json.dumps(metadata))

    def test_mocked_upstream_execution_and_catalog_mode(self) -> None:
        with mock.patch.dict(os.environ, {"EODHD_API_TOKEN": "secret-token"}, clear=False):
            result, metadata = eodhd.query_eodhd(
                "eod-history",
                {"symbol": "AAPL.US"},
                timeout=10,
                max_bytes=100000,
                max_rows=100,
                opener=lambda *_args, **_kwargs: FakeResponse([{"date": "2026-07-31", "close": 1.0}]),
                sleeper=lambda _: None,
            )
        self.assertEqual(len(result), 1)
        self.assertEqual(metadata["row_count"], 1)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            ticket_path.write_text(json.dumps(self.ticket("catalog-capabilities", {})), encoding="utf-8")
            self.assertEqual(eodhd.execute(ticket_path, root / "out"), 0)
            snapshot = json.loads((root / "out/eodhd-snapshot.json").read_text(encoding="utf-8"))
            self.assertFalse(snapshot["metadata"]["upstream_called"])


if __name__ == "__main__":
    unittest.main()
'''
write(TARGET / "tests/test_eodhd_task.py", tests)

# Register provider in the deterministic catalog wrapper.
builder = API / "build_catalog_market_search.py"
text = builder.read_text(encoding="utf-8")
text = text.replace(
    'BAOSTOCK_CATALOG = HERE / "baostock/provider-catalog.json"\n',
    'BAOSTOCK_CATALOG = HERE / "baostock/provider-catalog.json"\nEODHD_CATALOG = HERE / "eodhd/provider-catalog.json"\n',
)
text = text.replace('    "baostock": 20,\n', '    "baostock": 20,\n    "eodhd": 25,\n')
text = text.replace('    BAOSTOCK_CATALOG,\n', '    BAOSTOCK_CATALOG,\n    EODHD_CATALOG,\n')
text = text.replace('        "baostock/provider-catalog.json",\n', '        "baostock/provider-catalog.json",\n        "eodhd/provider-catalog.json",\n')
write(builder, text)

# Update deterministic tests.
path = API / "tests/test_api_catalog.py"
text = path.read_text(encoding="utf-8")
text = text.replace('    "baostock": 20,\n', '    "baostock": 20,\n    "eodhd": 25,\n')
text = text.replace('self.assertEqual(catalog["managed_provider_count"], 18)', 'self.assertEqual(catalog["managed_provider_count"], 19)')
text = text.replace('self.assertEqual(catalog["enabled_managed_provider_count"], 18)', 'self.assertEqual(catalog["enabled_managed_provider_count"], 19)')
text = text.replace('self.assertEqual(catalog["managed_operation_count"], 165)', 'self.assertEqual(catalog["managed_operation_count"], 190)')
text = text.replace('            "tushare": "TUSHARE_API_TOKEN",\n', '            "tushare": "TUSHARE_API_TOKEN",\n            "eodhd": "EODHD_API_TOKEN",\n')
anchor = '        self.assertFalse(providers["baostock"]["limits"]["trading_or_order_execution_allowed"])\n'
text = text.replace(anchor, anchor + '\n        self.assertEqual(providers["eodhd"]["ticket_prefix"], "[api-eodhd]")\n        self.assertEqual(providers["eodhd"]["required_secret_environment_variable_name"], "EODHD_API_TOKEN")\n        self.assertFalse(providers["eodhd"]["limits"]["arbitrary_urls_allowed"])\n        self.assertFalse(providers["eodhd"]["limits"]["trading_or_order_execution_allowed"])\n')
text = text.replace('            "baostock/provider-catalog.json",\n', '            "baostock/provider-catalog.json",\n            "eodhd/provider-catalog.json",\n')
write(path, text)

path = API / "tests/test_capability_maximization.py"
text = path.read_text(encoding="utf-8")
text = text.replace('            165,\n', '            190,\n', 1)
text = text.replace('            "baostock": 20,\n', '            "baostock": 20,\n            "eodhd": 25,\n')
anchor = '        self.assertFalse(tushare_limits["secret_values_exposed"])\n'
insert = '''\n        eodhd = json.loads(\n            (ROOT / "eodhd/provider-catalog.json").read_text(encoding="utf-8")\n        )\n        eodhd_provider = eodhd["providers"][0]\n        self.assertEqual(eodhd_provider["required_secret_environment_variable"], "EODHD_API_TOKEN")\n        self.assertFalse(eodhd_provider["limits"]["arbitrary_urls_allowed"])\n        self.assertFalse(eodhd_provider["limits"]["arbitrary_headers_allowed"])\n        self.assertFalse(eodhd_provider["limits"]["write_operations_allowed"])\n        self.assertFalse(eodhd_provider["limits"]["trading_or_order_execution_allowed"])\n'''
text = text.replace(anchor, anchor + insert)
write(path, text)

# Document the independent Secret and provider.
path = API / "README.md"
text = path.read_text(encoding="utf-8")
text = text.replace('TUSHARE_API_TOKEN\n', 'TUSHARE_API_TOKEN\nEODHD_API_TOKEN\n', 1)
marker = '## Wolfram|Alpha 计算知识\n'
section = '''## EODHD 全球金融市场数据\n\n`api-center/eodhd/` 使用固定官方 HTTPS GET 接口，票据前缀和独立 Secret 为：\n\n```text\n[api-eodhd]\nEODHD_API_TOKEN\n```\n\n开放 25 项只读操作，覆盖全球交易所和证券目录、历史与实时行情、基本面、公司行动、技术指标、新闻情绪、股票筛选、企业日历、宏观事件以及交易时段和节假日。上游套餐决定实际数据范围与额度；API 中心不开放 WebSocket、交易、下单、账户操作、任意 URL 或任意请求头。\n\n'''
text = text.replace(marker, section + marker)
write(path, text)

# Remove this one-shot generator from the resulting branch.
Path(__file__).unlink()
