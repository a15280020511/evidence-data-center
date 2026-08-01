#!/usr/bin/env python3
"""One-shot deterministic migration for the bounded Xweather provider."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API = ROOT / "api-center"
XW = API / "xweather"
XW.mkdir(parents=True, exist_ok=True)

LOCATION = {
    "type": "string",
    "minLength": 1,
    "maxLength": 120,
    "pattern": r"^[^/?#\\&=%]{1,120}$",
}
TIME_VALUE = {
    "type": "string",
    "minLength": 1,
    "maxLength": 32,
    "pattern": r"^[A-Za-z0-9:+._-]{1,32}$",
}
FIELDS = {
    "type": "string",
    "minLength": 1,
    "maxLength": 500,
    "pattern": r"^[A-Za-z0-9._,-]{1,500}$",
}
GENERIC_FILTER = {
    "type": "string",
    "minLength": 1,
    "maxLength": 64,
    "pattern": r"^[A-Za-z0-9._,-]{1,64}$",
}
LIMIT_20 = {"type": "integer", "minimum": 1, "maximum": 20}
LIMIT_31 = {"type": "integer", "minimum": 1, "maximum": 31}
LIMIT_72 = {"type": "integer", "minimum": 1, "maximum": 72}


def operation(
    operation_id: str,
    description: str,
    path_template: str,
    properties: dict,
    *,
    required: list[str] | None = None,
    query_parameter_map: dict[str, str] | None = None,
    local: bool = False,
) -> dict:
    parameters = list(properties)
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
    }
    if required:
        schema["required"] = required
    return {
        "operation_id": operation_id,
        "description": description,
        "parameters": parameters,
        "parameter_schema": schema,
        "execution": {
            "local": local,
            "path_template": path_template,
            "path_parameters": ["location"] if "{location}" in path_template else [],
            "query_parameter_map": query_parameter_map or {},
        },
        "result_contract": {
            "provider": "xweather",
            "official_origin": "https://data.api.xweather.com",
            "http_method": "LOCAL" if local else "GET",
            "read_only": True,
            "credential_mode": "none" if local else "client-id-variable-plus-client-secret-backend-only",
        },
    }


OPERATIONS = [
    operation(
        "catalog-capabilities",
        "读取本地 Xweather 安全能力目录，不访问上游。",
        "",
        {},
        local=True,
    ),
    operation(
        "places-closest",
        "按城市、邮编、站点或经纬度查询最近地理位置。",
        "/places/closest",
        {"p": LOCATION, "limit": LIMIT_20, "fields": FIELDS},
        required=["p"],
    ),
    operation(
        "observations-current",
        "读取指定位置最近的全球气象站实时观测。",
        "/observations/{location}",
        {"location": LOCATION, "filter": GENERIC_FILTER, "fields": FIELDS},
        required=["location"],
    ),
    operation(
        "conditions",
        "读取全球位置当前、历史、未来逐小时条件或分钟级降水条件。",
        "/conditions/{location}",
        {
            "location": LOCATION,
            "from": TIME_VALUE,
            "to": TIME_VALUE,
            "at_time": TIME_VALUE,
            "filter": {
                "type": "string",
                "enum": ["1hr", "minutelyprecip"],
            },
            "limit": LIMIT_72,
            "fields": FIELDS,
        },
        required=["location"],
        query_parameter_map={"at_time": "for"},
    ),
    operation(
        "forecasts",
        "读取全球位置最长 15 日的日、昼夜或小时天气预报。",
        "/forecasts/{location}",
        {
            "location": LOCATION,
            "filter": {
                "type": "string",
                "enum": ["day", "daynight", "mdnt2mdnt", "1hr", "3hr", "6hr"],
            },
            "limit": LIMIT_31,
            "fields": FIELDS,
        },
        required=["location"],
    ),
    operation(
        "alerts",
        "读取指定位置当前有效的官方天气预警。",
        "/alerts/{location}",
        {"location": LOCATION, "limit": LIMIT_20, "fields": FIELDS},
        required=["location"],
    ),
    operation(
        "air-quality",
        "读取全球位置当前空气质量、AQI、AQHI 和污染物信息。",
        "/airquality/{location}",
        {"location": LOCATION, "filter": GENERIC_FILTER, "fields": FIELDS},
        required=["location"],
    ),
    operation(
        "sunmoon",
        "读取全球位置日出日落、曙暮光和月升月落数据。",
        "/sunmoon/{location}",
        {"location": LOCATION, "from": TIME_VALUE, "to": TIME_VALUE, "limit": LIMIT_31},
        required=["location"],
    ),
    operation(
        "moon-phases",
        "读取全球位置主要月相发生时间。",
        "/sunmoon/moonphases/{location}",
        {"location": LOCATION, "from": TIME_VALUE, "to": TIME_VALUE, "limit": LIMIT_31},
        required=["location"],
    ),
    operation(
        "observations-summary",
        "读取指定位置最多 30 日的历史观测日汇总。",
        "/observations/summary/{location}",
        {
            "location": LOCATION,
            "from": TIME_VALUE,
            "to": TIME_VALUE,
            "limit": LIMIT_31,
            "fields": FIELDS,
        },
        required=["location"],
    ),
]

PROVIDER = {
    "schema_version": "xweather-provider-catalog-v1",
    "secret_values_exposed": False,
    "replaced_legacy_connectors": [],
    "providers": [
        {
            "provider_id": "xweather",
            "display_name": "Xweather 全球专业天气数据",
            "description": "通过 Xweather 官方 Weather API 读取全球地点、实时观测、插值条件、15 日预报、官方预警、空气质量、日月和历史观测汇总。",
            "enabled": True,
            "ticket_prefix": "[api-xweather]",
            "required_secret_environment_variable": "XWEATHER_CLIENT_SECRET",
            "required_repository_variable": "XWEATHER_CLIENT_ID",
            "catalog_policy": "固定开放 10 项核心只读能力；所有端点、路径、参数、时间范围、返回条数和响应体积受白名单与硬上限约束。",
            "execution_policy": "Client ID 由 GitHub Repository Variable 注入，Client Secret 仅由 Repository Secret 注入；不接受客户端凭据、任意 URL、任意查询、路线批量、写操作或 Webhook。",
            "official_origin": "https://data.api.xweather.com",
            "limits": {
                "requests_per_ticket_max": 1,
                "timeout_seconds_max": 120,
                "max_response_bytes": 20000000,
                "max_rows": 5000,
                "arbitrary_urls_allowed": False,
                "arbitrary_hosts_allowed": False,
                "arbitrary_paths_allowed": False,
                "arbitrary_headers_allowed": False,
                "arbitrary_query_parameters_allowed": False,
                "redirects_allowed": False,
                "write_operations_allowed": False,
                "webhooks_allowed": False,
                "route_queries_allowed": False,
                "client_supplied_credentials_allowed": False,
                "personal_data_allowed": False,
                "secret_values_exposed": False,
                "fixed_api_host": "data.api.xweather.com",
                "provider_concurrency_max": 1,
                "transient_retry_max": 1,
                "plan_or_multiplier_dependent_endpoints": True,
            },
            "operations": OPERATIONS,
        }
    ],
}

TICKET_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://github.com/a15280020511/evidence-data-center/api-center/xweather/ticket.schema.json",
    "title": "xweather managed read-only ticket",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "task_id",
        "provider",
        "operation",
        "objective",
        "parameters",
        "data_policy",
        "acceptance",
    ],
    "properties": {
        "task_id": {
            "type": "string",
            "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$",
        },
        "provider": {"const": "xweather"},
        "operation": {"type": "string", "enum": [row["operation_id"] for row in OPERATIONS]},
        "objective": {"type": "string", "minLength": 1, "maxLength": 1000},
        "parameters": {"type": "object", "maxProperties": 7},
        "data_policy": {
            "type": "object",
            "additionalProperties": False,
            "required": ["classification", "contains_personal_data"],
            "properties": {
                "classification": {"const": "public"},
                "contains_personal_data": {"const": False},
            },
        },
        "acceptance": {
            "type": "object",
            "additionalProperties": False,
            "required": ["timeout_seconds", "max_response_bytes", "max_rows"],
            "properties": {
                "timeout_seconds": {"type": "integer", "minimum": 5, "maximum": 120},
                "max_response_bytes": {"type": "integer", "minimum": 1024, "maximum": 20000000},
                "max_rows": {"type": "integer", "minimum": 1, "maximum": 5000},
            },
        },
    },
}

TASK = r'''#!/usr/bin/env python3
"""Bounded read-only Xweather Weather API execution."""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import quote

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
ORIGIN = "https://data.api.xweather.com"
CLIENT_ID_ENV = "XWEATHER_CLIENT_ID"
CLIENT_SECRET_ENV = "XWEATHER_CLIENT_SECRET"


class XweatherError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def credentials() -> tuple[str, str]:
    client_id = str(os.getenv(CLIENT_ID_ENV) or "").strip()
    client_secret = str(os.getenv(CLIENT_SECRET_ENV) or "").strip()
    if not client_id:
        raise XweatherError(
            "XWEATHER_CLIENT_ID_MISSING",
            f"missing repository Variable {CLIENT_ID_ENV}",
        )
    if not client_secret:
        raise XweatherError(
            "XWEATHER_CLIENT_SECRET_MISSING",
            f"missing repository Secret {CLIENT_SECRET_ENV}",
        )
    for name, value in ((CLIENT_ID_ENV, client_id), (CLIENT_SECRET_ENV, client_secret)):
        if not 8 <= len(value) <= 512:
            raise XweatherError("XWEATHER_CREDENTIAL_INVALID", f"invalid {name} length")
        if any(ord(char) < 0x21 or ord(char) > 0x7E for char in value):
            raise XweatherError("XWEATHER_CREDENTIAL_INVALID", f"invalid {name} characters")
    return client_id, client_secret


def operation_row(operation: str) -> Mapping[str, Any]:
    row = operation_map(CATALOG_PATH).get(operation)
    if row is None:
        raise ValueError(f"unsupported Xweather operation: {operation}")
    return row


def build_request(operation: str, parameters: Mapping[str, Any]) -> tuple[str | None, dict[str, str], dict[str, Any]]:
    row = operation_row(operation)
    execution = row["execution"]
    if execution.get("local") is True:
        return None, {}, {
            "request_origin": "local",
            "http_method": "LOCAL",
            "credential_mode": "none",
            "secret_value_exposed": False,
        }
    path = str(execution["path_template"])
    clean = dict(parameters)
    for name in execution.get("path_parameters") or []:
        value = clean.pop(name)
        path = path.replace("{" + name + "}", quote(str(value), safe=",._@+-"))
    query_map = dict(execution.get("query_parameter_map") or {})
    query: dict[str, str] = {}
    for name, value in clean.items():
        if value in (None, ""):
            continue
        query[str(query_map.get(name) or name)] = str(value)
    return ORIGIN + path, query, {
        "request_origin": "data.api.xweather.com",
        "request_path": path,
        "http_method": "GET",
        "credential_mode": "client-id-variable-plus-client-secret-backend-only",
        "credential_environment_variables": [CLIENT_ID_ENV, CLIENT_SECRET_ENV],
        "secret_value_exposed": False,
        "redirects_allowed": False,
        "query_parameter_names": sorted(query),
    }


def result_rows(payload: Any) -> int:
    if not isinstance(payload, Mapping):
        return len(payload) if isinstance(payload, list) else 1
    response = payload.get("response")
    if isinstance(response, list):
        total = len(response)
        for item in response:
            if isinstance(item, Mapping):
                periods = item.get("periods")
                if isinstance(periods, list):
                    total += len(periods)
        return total
    return 1


def query_xweather(
    operation: str,
    parameters: Mapping[str, Any],
    *,
    timeout: int,
    max_bytes: int,
    max_rows: int,
) -> tuple[Any, dict[str, Any]]:
    client_id, client_secret = credentials()
    url, query, metadata = build_request(operation, parameters)
    if url is None:
        raise ValueError("local operations must not call query_xweather")
    upstream_query = dict(query)
    upstream_query["client_id"] = client_id
    upstream_query["client_secret"] = client_secret
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "User-Agent": "gpts-evidence-data-center-xweather/1",
    }
    attempts = 0
    while attempts < 2:
        attempts += 1
        try:
            response = requests.get(
                url,
                params=upstream_query,
                headers=headers,
                timeout=timeout,
                allow_redirects=False,
                stream=True,
            )
            raw = response.raw.read(max_bytes + 1, decode_content=True)
        except requests.RequestException as exc:
            if attempts < 2:
                time.sleep(1.0)
                continue
            raise XweatherError(
                "XWEATHER_CONNECTION_FAILED",
                f"upstream connection failed: {type(exc).__name__}",
                retryable=True,
            ) from exc
        if len(raw) > max_bytes:
            raise XweatherError(
                "XWEATHER_RESPONSE_TOO_LARGE",
                "upstream response exceeded max_response_bytes",
            )
        if response.is_redirect:
            raise XweatherError(
                "XWEATHER_REDIRECT_REJECTED",
                f"upstream attempted HTTP {response.status_code} redirect",
            )
        if response.status_code == 429 or 500 <= response.status_code <= 599:
            if attempts < 2:
                time.sleep(1.0)
                continue
            raise XweatherError(
                "XWEATHER_HTTP_TRANSIENT",
                f"upstream HTTP {response.status_code}",
                retryable=True,
            )
        if response.status_code in {401, 403}:
            raise XweatherError(
                "XWEATHER_CREDENTIAL_OR_PLAN_DENIED",
                f"upstream HTTP {response.status_code}",
            )
        if not 200 <= response.status_code < 300:
            raise XweatherError("XWEATHER_HTTP_ERROR", f"upstream HTTP {response.status_code}")
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else None
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise XweatherError("XWEATHER_INVALID_JSON", "upstream returned invalid JSON") from exc
        if isinstance(payload, Mapping) and payload.get("success") is False:
            error = payload.get("error") if isinstance(payload.get("error"), Mapping) else {}
            code = str(error.get("code") or "unknown")
            description = str(error.get("description") or error.get("message") or "request failed")
            raise XweatherError("XWEATHER_BUSINESS_ERROR", f"Xweather {code}: {description[:500]}")
        rows = result_rows(payload)
        if rows > max_rows:
            raise XweatherError(
                "XWEATHER_RESULT_TOO_MANY_ROWS",
                f"upstream result has {rows} rows; max_rows is {max_rows}",
            )
        metadata.update(
            {
                "http_status": response.status_code,
                "content_type": response.headers.get("Content-Type", ""),
                "response_bytes": len(raw),
                "result_rows": rows,
                "attempts": attempts,
            }
        )
        return payload, metadata
    raise AssertionError("unreachable")


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(
        acceptance.get("timeout_seconds"),
        default=45,
        minimum=5,
        maximum=120,
        name="timeout_seconds",
    )
    max_bytes = bounded_int(
        acceptance.get("max_response_bytes"),
        default=5_000_000,
        minimum=1024,
        maximum=20_000_000,
        name="max_response_bytes",
    )
    max_rows = bounded_int(
        acceptance.get("max_rows"),
        default=500,
        minimum=1,
        maximum=5000,
        name="max_rows",
    )
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "API_XWEATHER_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "api_origin": "data.api.xweather.com",
        "credential_mode": "client-id-variable-plus-client-secret-backend-only",
        "secret_values_exposed": False,
    }
    try:
        if operation == "catalog-capabilities":
            snapshot = {"provider": provider_row(CATALOG_PATH)}
            metadata["credential_mode"] = "none"
        else:
            payload, request_metadata = query_xweather(
                operation,
                parameters,
                timeout=timeout,
                max_bytes=max_bytes,
                max_rows=max_rows,
            )
            metadata.update(request_metadata)
            metadata["upstream_called"] = True
            snapshot = {
                "provider": "xweather",
                "operation": operation,
                "data": payload,
            }
        status = "API_XWEATHER_COMPLETED"
    except Exception as exc:
        message = str(exc)
        for env_name in (CLIENT_ID_ENV, CLIENT_SECRET_ENV):
            value = str(os.getenv(env_name) or "")
            if value:
                message = message.replace(value, "[REDACTED]")
        failure = {
            "type": type(exc).__name__,
            "code": getattr(exc, "code", "XWEATHER_EXECUTION_ERROR"),
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
        schema_prefix="xweather",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[api-xweather]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="xweather-ticket-status-v1",
            display_name="Xweather",
        )
    )
'''

TEST = r'''from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("xweather_task", ROOT / "xweather_task.py")
assert SPEC and SPEC.loader
task = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(task)


class XweatherTests(unittest.TestCase):
    def ticket(self, operation="catalog-capabilities", parameters=None):
        return {
            "task_id": "xweather-test-001",
            "provider": "xweather",
            "operation": operation,
            "objective": "test bounded Xweather provider",
            "parameters": parameters or {},
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "acceptance": {
                "timeout_seconds": 30,
                "max_response_bytes": 1000000,
                "max_rows": 100,
            },
        }

    def test_catalog_and_schema_are_fixed(self):
        catalog = json.loads((ROOT / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "xweather")
        self.assertEqual(provider["required_secret_environment_variable"], "XWEATHER_CLIENT_SECRET")
        self.assertEqual(provider["required_repository_variable"], "XWEATHER_CLIENT_ID")
        self.assertEqual(len(provider["operations"]), 10)
        self.assertEqual(provider["limits"]["fixed_api_host"], "data.api.xweather.com")
        self.assertFalse(provider["limits"]["arbitrary_query_parameters_allowed"])
        self.assertFalse(provider["limits"]["client_supplied_credentials_allowed"])
        task.validate_ticket(
            self.ticket(), schema_path=task.SCHEMA_PATH, catalog_path=task.CATALOG_PATH
        )

    def test_request_builder_keeps_fixed_origin_and_redacts_credentials(self):
        url, query, metadata = task.build_request(
            "forecasts",
            {"location": "26.08,119.30", "filter": "1hr", "limit": 24},
        )
        self.assertEqual(url, "https://data.api.xweather.com/forecasts/26.08,119.30")
        self.assertEqual(query, {"filter": "1hr", "limit": "24"})
        self.assertNotIn("client_id", query)
        self.assertNotIn("client_secret", query)
        self.assertEqual(metadata["request_origin"], "data.api.xweather.com")
        with patch.dict(
            os.environ,
            {
                "XWEATHER_CLIENT_ID": "test-client-id",
                "XWEATHER_CLIENT_SECRET": "test-client-secret",
            },
            clear=False,
        ):
            self.assertEqual(task.credentials(), ("test-client-id", "test-client-secret"))

    def test_schema_rejects_path_escape(self):
        bad = self.ticket("forecasts", {"location": "https://example.com", "limit": 1})
        with self.assertRaises(ValueError):
            task.validate_ticket(bad, schema_path=task.SCHEMA_PATH, catalog_path=task.CATALOG_PATH)

    def test_local_catalog_execution_needs_no_credentials(self):
        with tempfile.TemporaryDirectory() as tmp:
            ticket = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket.write_text(json.dumps(self.ticket()), encoding="utf-8")
            self.assertEqual(task.execute(ticket, out), 0)
            diagnostics = json.loads((out / "diagnostics.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostics["status"], "API_XWEATHER_COMPLETED")
            self.assertFalse(diagnostics["metadata"]["upstream_called"])


if __name__ == "__main__":
    unittest.main()
'''

README = '''# Xweather 全球专业天气数据

正式票据前缀：

```text
[api-xweather]
```

Xweather Weather API 每次调用需要两项配置：

```text
Repository Variable: XWEATHER_CLIENT_ID
Repository Secret:   XWEATHER_CLIENT_SECRET
```

Client ID 不是写入仓库的常量；Client Secret 只由 GitHub Actions 后端注入。Provider 固定访问：

```text
https://data.api.xweather.com
```

固定开放 10 项核心只读能力：地点解析、实时观测、插值条件、15 日预报、官方预警、空气质量、日月数据、月相和历史观测日汇总。部分端点可能受套餐、区域或调用倍率约束；权限不足会输出结构化失败，不会伪造数据。

禁止任意 URL、任意主机、任意查询参数、路线批量、客户端凭据、Webhook 和写操作。
'''


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected one match in {path}: found {count} for {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


write(XW / "provider-catalog.json", json.dumps(PROVIDER, ensure_ascii=False, indent=2) + "\n")
write(XW / "ticket.schema.json", json.dumps(TICKET_SCHEMA, ensure_ascii=False, indent=2) + "\n")
write(XW / "xweather_task.py", TASK)
write(XW / "tests/test_xweather_task.py", TEST)
write(XW / "requirements.txt", "jsonschema>=4.23,<5\nrequests>=2.32,<3\n")
write(XW / "README.md", README)

build_path = API / "build_catalog_market_search.py"
replace_once(
    build_path,
    'QWEATHER_CATALOG = HERE / "qweather/provider-catalog.json"\n',
    'QWEATHER_CATALOG = HERE / "qweather/provider-catalog.json"\nXWEATHER_CATALOG = HERE / "xweather/provider-catalog.json"\n',
)
replace_once(
    build_path,
    '    "qweather": 18,\n',
    '    "qweather": 18,\n    "xweather": 10,\n',
)
replace_once(
    build_path,
    '    QWEATHER_CATALOG,\n',
    '    QWEATHER_CATALOG,\n    XWEATHER_CATALOG,\n',
)
replace_once(
    build_path,
    '        "qweather/provider-catalog.json",\n',
    '        "qweather/provider-catalog.json",\n        "xweather/provider-catalog.json",\n',
)

readme_path = API / "README.md"
replace_once(
    readme_path,
    'ALPHAFEED_API_KEY\nWOLFRAM_ALPHA_APP_ID\n',
    'ALPHAFEED_API_KEY\nXWEATHER_CLIENT_SECRET\nWOLFRAM_ALPHA_APP_ID\n',
)
replace_once(
    readme_path,
    '## Wolfram|Alpha 计算知识\n',
    '''## Xweather 全球专业天气数据

`api-center/xweather/` 固定访问 Xweather Weather API：

```text
[api-xweather]
Repository Variable: XWEATHER_CLIENT_ID
Repository Secret:   XWEATHER_CLIENT_SECRET
```

固定开放 10 项核心只读能力，覆盖地点解析、实时观测、插值天气条件、最长 15 日预报、官方天气预警、空气质量、日月、月相和历史观测日汇总。部分端点受账户套餐、区域和调用倍率约束；禁止任意 URL、路线批量、Webhook 和写操作。

## Wolfram|Alpha 计算知识
''',
)

secret_path = API / "SECRET_ISOLATION_POLICY.md"
replace_once(
    secret_path,
    'ALPHAFEED_API_KEY\nWOLFRAM_ALPHA_APP_ID\n',
    'ALPHAFEED_API_KEY\nXWEATHER_CLIENT_SECRET\nWOLFRAM_ALPHA_APP_ID\n',
)
secret_text = secret_path.read_text(encoding="utf-8")
secret_text = secret_text.rstrip() + '''

Xweather 的公开 Client ID 作为 GitHub Repository Variable `XWEATHER_CLIENT_ID` 注入，唯一敏感凭据为 Repository Secret `XWEATHER_CLIENT_SECRET`。两者只发送至 `https://data.api.xweather.com` 的固定白名单 GET 端点，不写入仓库、Issue、日志或 Artifact。
'''
secret_path.write_text(secret_text, encoding="utf-8")

test_catalog = API / "tests/test_api_catalog.py"
replace_once(
    test_catalog,
    '    "qweather": 18,\n',
    '    "qweather": 18,\n    "xweather": 10,\n',
)
replace_once(test_catalog, 'catalog["managed_provider_count"], 28', 'catalog["managed_provider_count"], 29')
replace_once(test_catalog, 'catalog["enabled_managed_provider_count"], 28', 'catalog["enabled_managed_provider_count"], 29')
replace_once(test_catalog, 'catalog["managed_operation_count"], 329', 'catalog["managed_operation_count"], 339')
replace_once(
    test_catalog,
    '            "qweather": "QWEATHER_API_KEY",\n',
    '            "qweather": "QWEATHER_API_KEY",\n            "xweather": "XWEATHER_CLIENT_SECRET",\n',
)
replace_once(
    test_catalog,
    '        self.assertEqual(providers["miaoxiang-mcp"]["ticket_prefix"], "[api-mx-mcp]")\n',
    '''        xweather = providers["xweather"]
        self.assertEqual(xweather["ticket_prefix"], "[api-xweather]")
        self.assertEqual(
            xweather["required_secret_environment_variable_name"],
            "XWEATHER_CLIENT_SECRET",
        )
        self.assertEqual(xweather["required_repository_variable"], "XWEATHER_CLIENT_ID")
        self.assertEqual(len(xweather["operations"]), 10)
        self.assertEqual(xweather["limits"]["fixed_api_host"], "data.api.xweather.com")
        self.assertFalse(xweather["limits"]["arbitrary_query_parameters_allowed"])
        self.assertFalse(xweather["limits"]["client_supplied_credentials_allowed"])
        self.assertFalse(xweather["limits"]["write_operations_allowed"])

        self.assertEqual(providers["miaoxiang-mcp"]["ticket_prefix"], "[api-mx-mcp]")
''',
)
replace_once(
    test_catalog,
    '            "qweather/provider-catalog.json",\n',
    '            "qweather/provider-catalog.json",\n            "xweather/provider-catalog.json",\n',
)

capability = API / "tests/test_capability_maximization.py"
replace_once(capability, '            329,\n', '            339,\n')
replace_once(
    capability,
    '            "qweather": 18,\n',
    '            "qweather": 18,\n            "xweather": 10,\n',
)
replace_once(
    capability,
    '        miaoxiang_mcp = json.loads(\n',
    '''        xweather = json.loads(
            (ROOT / "xweather/provider-catalog.json").read_text(encoding="utf-8")
        )
        xw_provider = xweather["providers"][0]
        self.assertEqual(
            xw_provider["required_secret_environment_variable"],
            "XWEATHER_CLIENT_SECRET",
        )
        self.assertEqual(xw_provider["required_repository_variable"], "XWEATHER_CLIENT_ID")
        self.assertEqual(xw_provider["limits"]["fixed_api_host"], "data.api.xweather.com")
        self.assertFalse(xw_provider["limits"]["arbitrary_urls_allowed"])
        self.assertFalse(xw_provider["limits"]["arbitrary_query_parameters_allowed"])
        self.assertFalse(xw_provider["limits"]["client_supplied_credentials_allowed"])
        self.assertFalse(xw_provider["limits"]["write_operations_allowed"])

        miaoxiang_mcp = json.loads(
''',
)

print(json.dumps({
    "status": "PASS",
    "provider": "xweather",
    "operations": 10,
    "managed_provider_count_after": 29,
    "managed_operation_count_after": 339,
}))
