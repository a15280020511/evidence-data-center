#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API = ROOT / "api-center"
WHO = API / "who-gho"
BRANCH = "feat/add-overture-oecd-alphafeed"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, value: object) -> None:
    write(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"replacement anchor missing in {path}: {old[:120]!r}")
    write(path, text.replace(old, new, 1))


COMMON_RESULT = {
    "provider": "who-gho-odata",
    "official_origin": "https://ghoapi.azureedge.net/api",
    "http_method": "GET",
    "read_only": True,
    "credential_mode": "none",
}


def op(operation_id: str, description: str, properties: dict, required: list[str] | None = None):
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
        "parameters": list(properties),
        "parameter_schema": schema,
        "result_contract": dict(COMMON_RESULT),
    }


TOP = {"type": "integer", "minimum": 1, "maximum": 1000, "default": 100}
SMALL_TOP = {"type": "integer", "minimum": 1, "maximum": 200, "default": 50}
SKIP = {"type": "integer", "minimum": 0, "maximum": 100000, "default": 0}
DIMENSION = {
    "type": "string",
    "enum": [
        "COUNTRY",
        "REGION",
        "SEX",
        "AGEGROUP",
        "GHO",
        "PUBLISHSTATE",
        "WORLDBANKINCOMEGROUP",
    ],
}

operations = [
    {
        "operation_id": "catalog-capabilities",
        "description": "读取本地 WHO GHO OData 安全能力目录，不访问上游。",
        "parameters": [],
        "parameter_schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {},
            "maxProperties": 0,
        },
        "result_contract": {
            "provider": "who-gho-odata",
            "official_origin": "https://ghoapi.azureedge.net/api",
            "http_method": "LOCAL",
            "read_only": True,
            "credential_mode": "none",
        },
    },
    op("list-dimensions", "读取 WHO GHO 可用维度目录。", {"top": TOP, "skip": SKIP}),
    op(
        "list-dimension-values",
        "读取固定公共维度的代码和值。",
        {"dimension": DIMENSION, "top": TOP, "skip": SKIP},
        ["dimension"],
    ),
    op("list-indicators", "分页读取 WHO GHO 指标代码和名称目录。", {"top": TOP, "skip": SKIP}),
    op(
        "search-indicators",
        "按受控文本条件搜索 WHO GHO 指标名称。",
        {
            "query": {
                "type": "string",
                "minLength": 2,
                "maxLength": 120,
                "pattern": "^[A-Za-z0-9 .,/()%-]+$",
            },
            "match": {"type": "string", "enum": ["contains", "exact"], "default": "contains"},
            "top": SMALL_TOP,
            "skip": SKIP,
        },
        ["query"],
    ),
    op(
        "get-indicator-data",
        "按指标、国家或地区、年份和性别读取 WHO GHO 观测值；只构造固定 OData 条件。",
        {
            "indicator_code": {
                "type": "string",
                "minLength": 2,
                "maxLength": 128,
                "pattern": "^[A-Z0-9][A-Z0-9_]{1,127}$",
            },
            "country": {"type": "string", "pattern": "^[A-Z]{3}$"},
            "region": {
                "type": "string",
                "enum": ["AFR", "AMR", "SEAR", "EUR", "EMR", "WPR", "GLOBAL"],
            },
            "year_from": {"type": "integer", "minimum": 1900, "maximum": 2100},
            "year_to": {"type": "integer", "minimum": 1900, "maximum": 2100},
            "sex": {"type": "string", "enum": ["BTSX", "MLE", "FMLE"]},
            "top": TOP,
            "skip": SKIP,
        },
        ["indicator_code"],
    ),
    op("get-countries", "读取 WHO GHO 国家代码和值目录。", {"top": TOP, "skip": SKIP}),
    op("get-regions", "读取 WHO GHO 地区代码和值目录。", {"top": TOP, "skip": SKIP}),
]

provider_catalog = {
    "schema_version": "who-gho-odata-provider-catalog-v1",
    "secret_values_exposed": False,
    "replaced_legacy_connectors": [],
    "providers": [
        {
            "provider_id": "who-gho-odata",
            "display_name": "WHO GHO OData 全球卫生数据",
            "description": "通过世界卫生组织 Global Health Observatory 公开 OData 接口读取全球卫生指标、维度、国家、地区和历史观测值。",
            "enabled": True,
            "ticket_prefix": "[intel-who-gho]",
            "required_secret_environment_variable": "",
            "catalog_policy": "开放8项固定免密只读操作；指标代码、维度、国家、地区、年份、性别和分页均受Schema约束，不接受任意OData表达式。",
            "execution_policy": "每张票据最多一次固定HTTPS GET；不跟随重定向，不接受任意URL、主机、路径、请求头、$filter、$select、$expand、函数或写操作。",
            "official_documentation": "https://www.who.int/data/gho/info/gho-odata-api",
            "official_origin": "https://ghoapi.azureedge.net/api",
            "service_status_notice": "WHO官方页面说明当前GHO OData接口计划在2025年底前后迁移到World Health Data Hub的新OData实现；本Provider按2026年8月仍可访问的兼容端点接入，并要求后续迁移审计。",
            "limits": {
                "requests_per_ticket_max": 1,
                "timeout_seconds_max": 120,
                "max_response_bytes": 20000000,
                "provider_concurrency_max": 1,
                "transient_retry_max": 0,
                "fixed_api_host": "ghoapi.azureedge.net",
                "fixed_api_prefix": "/api",
                "arbitrary_urls_allowed": False,
                "arbitrary_hosts_allowed": False,
                "arbitrary_paths_allowed": False,
                "arbitrary_headers_allowed": False,
                "arbitrary_odata_filters_allowed": False,
                "arbitrary_odata_select_allowed": False,
                "arbitrary_odata_expand_allowed": False,
                "arbitrary_odata_functions_allowed": False,
                "redirects_allowed": False,
                "write_operations_allowed": False,
                "personal_data_allowed": False,
                "secret_values_exposed": False,
                "authentication_required": False,
                "automatic_pagination_allowed": False,
                "whole_database_download_allowed": False,
                "legacy_endpoint_migration_watch_required": True,
            },
            "operations": operations,
        }
    ],
}
write_json(WHO / "provider-catalog.json", provider_catalog)

operation_ids = [row["operation_id"] for row in operations]
ticket_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://github.com/a15280020511/evidence-data-center/api-center/who-gho/ticket.schema.json",
    "title": "WHO GHO OData managed read-only ticket",
    "type": "object",
    "additionalProperties": False,
    "required": ["task_id", "provider", "operation", "objective", "parameters", "data_policy", "acceptance"],
    "properties": {
        "task_id": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$"},
        "provider": {"const": "who-gho-odata"},
        "operation": {"type": "string", "enum": operation_ids},
        "objective": {"type": "string", "minLength": 1, "maxLength": 1000},
        "parameters": {"type": "object", "maxProperties": 8},
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
            "required": ["timeout_seconds", "max_response_bytes"],
            "properties": {
                "timeout_seconds": {"type": "integer", "minimum": 5, "maximum": 120},
                "max_response_bytes": {"type": "integer", "minimum": 1024, "maximum": 20000000},
            },
        },
    },
}
write_json(WHO / "ticket.schema.json", ticket_schema)
write(WHO / "requirements.txt", "jsonschema==4.26.0\nrequests==2.34.2\n")

TASK = r'''#!/usr/bin/env python3
"""Bounded read-only WHO GHO OData execution for Intelligence Center tickets."""
from __future__ import annotations

import re
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
    bytes_sha,
    finish_execution,
    load_json,
    provider_row,
    run_cli,
    utc_now,
    validate_ticket,
)

SCHEMA_PATH = HERE / "ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"
BASE_URL = "https://ghoapi.azureedge.net/api"
INDICATOR_RE = re.compile(r"^[A-Z0-9][A-Z0-9_]{1,127}$")
SEARCH_RE = re.compile(r"^[A-Za-z0-9 .,/()%-]{2,120}$")
DIMENSIONS = {
    "COUNTRY", "REGION", "SEX", "AGEGROUP", "GHO", "PUBLISHSTATE",
    "WORLDBANKINCOMEGROUP",
}
REGIONS = {"AFR", "AMR", "SEAR", "EUR", "EMR", "WPR", "GLOBAL"}
SEXES = {"BTSX", "MLE", "FMLE"}


def page(parameters: Mapping[str, Any], *, default_top: int = 100, max_top: int = 1000) -> dict[str, str]:
    top = bounded_int(parameters.get("top"), default=default_top, minimum=1, maximum=max_top, name="top")
    skip = bounded_int(parameters.get("skip"), default=0, minimum=0, maximum=100000, name="skip")
    return {"$top": str(top), "$skip": str(skip), "$format": "json"}


def build_request(operation: str, parameters: Mapping[str, Any]) -> tuple[str | None, dict[str, str]]:
    if operation == "catalog-capabilities":
        return None, {}
    if operation == "list-dimensions":
        return "/Dimension", page(parameters)
    if operation == "list-dimension-values":
        dimension = str(parameters.get("dimension") or "")
        if dimension not in DIMENSIONS:
            raise ValueError("dimension is not allowlisted")
        return f"/DIMENSION/{dimension}/DimensionValues", page(parameters)
    if operation == "list-indicators":
        return "/Indicator", page(parameters)
    if operation == "search-indicators":
        query_text = str(parameters.get("query") or "")
        if not SEARCH_RE.fullmatch(query_text):
            raise ValueError("query contains unsupported characters")
        match = str(parameters.get("match") or "contains")
        if match not in {"contains", "exact"}:
            raise ValueError("match is invalid")
        escaped = query_text.replace("'", "''")
        query = page(parameters, default_top=50, max_top=200)
        query["$filter"] = (
            f"contains(IndicatorName,'{escaped}')"
            if match == "contains"
            else f"IndicatorName eq '{escaped}'"
        )
        return "/Indicator", query
    if operation == "get-countries":
        return "/DIMENSION/COUNTRY/DimensionValues", page(parameters)
    if operation == "get-regions":
        return "/DIMENSION/REGION/DimensionValues", page(parameters)
    if operation == "get-indicator-data":
        code = str(parameters.get("indicator_code") or "")
        if not INDICATOR_RE.fullmatch(code):
            raise ValueError("indicator_code is invalid")
        country = parameters.get("country")
        region = parameters.get("region")
        if country and region:
            raise ValueError("country and region are mutually exclusive")
        terms: list[str] = []
        if country:
            country_text = str(country)
            if not re.fullmatch(r"[A-Z]{3}", country_text):
                raise ValueError("country must be an ISO alpha-3 code")
            terms.extend(["SpatialDimType eq 'COUNTRY'", f"SpatialDim eq '{country_text}'"])
        if region:
            region_text = str(region)
            if region_text not in REGIONS:
                raise ValueError("region is invalid")
            terms.append(f"SpatialDim eq '{region_text}'")
        year_from = parameters.get("year_from")
        year_to = parameters.get("year_to")
        if year_from is not None:
            year_from = bounded_int(year_from, default=1900, minimum=1900, maximum=2100, name="year_from")
            terms.append(f"TimeDim ge {year_from}")
        if year_to is not None:
            year_to = bounded_int(year_to, default=2100, minimum=1900, maximum=2100, name="year_to")
            terms.append(f"TimeDim le {year_to}")
        if year_from is not None and year_to is not None and year_from > year_to:
            raise ValueError("year_from must not exceed year_to")
        sex = parameters.get("sex")
        if sex:
            sex_text = str(sex)
            if sex_text not in SEXES:
                raise ValueError("sex is invalid")
            terms.extend(["Dim1Type eq 'SEX'", f"Dim1 eq '{sex_text}'"])
        query = page(parameters)
        if terms:
            query["$filter"] = " and ".join(terms)
        query["$orderby"] = "TimeDim desc"
        return "/" + quote(code, safe="_"), query
    raise ValueError(f"unsupported operation: {operation}")


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(acceptance.get("timeout_seconds"), default=45, minimum=5, maximum=120, name="timeout_seconds")
    max_bytes = bounded_int(acceptance.get("max_response_bytes"), default=5_000_000, minimum=1024, maximum=20_000_000, name="max_response_bytes")
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_WHO_GHO_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "api_origin": "ghoapi.azureedge.net",
        "credential_mode": "none",
        "secret_values_exposed": False,
        "automatic_pagination": False,
        "legacy_endpoint_migration_watch_required": True,
    }
    try:
        path, query = build_request(operation, parameters)
        if path is None:
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        else:
            response = requests.get(
                BASE_URL + path,
                params=query,
                headers={"Accept": "application/json", "User-Agent": "intelligence-center-who-gho/1"},
                timeout=timeout,
                allow_redirects=False,
            )
            raw = response.content
            if len(raw) > max_bytes:
                raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
            if not response.ok:
                text = raw[:1000].decode("utf-8", errors="replace")
                raise RuntimeError(f"WHO GHO HTTP {response.status_code}: {text}")
            try:
                data = response.json()
            except ValueError as exc:
                raise RuntimeError("WHO GHO returned invalid JSON") from exc
            if not isinstance(data, Mapping) or not isinstance(data.get("value"), list):
                raise RuntimeError("WHO GHO response does not match OData value contract")
            (output_dir / "response.json").write_bytes(raw)
            snapshot = {
                "provider": "who-gho-odata",
                "operation": operation,
                "request_path": path,
                "row_count": len(data["value"]),
                "has_next_link": bool(data.get("@odata.nextLink")),
                "data": data,
            }
            metadata.update({
                "upstream_called": True,
                "http_status": response.status_code,
                "content_type": response.headers.get("Content-Type", ""),
                "request_path": path,
                "response_bytes": len(raw),
                "response_sha256": bytes_sha(raw),
                "row_count": len(data["value"]),
                "has_next_link": bool(data.get("@odata.nextLink")),
            })
        status = "INTEL_WHO_GHO_COMPLETED"
    except Exception as exc:
        failure = {"type": type(exc).__name__, "message": str(exc)[:2000]}
    return finish_execution(
        ticket=ticket,
        output_dir=output_dir,
        status=status,
        snapshot=snapshot,
        metadata=metadata,
        failure=failure,
        started_at=started_at,
        started_perf=started_perf,
        schema_prefix="who-gho",
    )


if __name__ == "__main__":
    raise SystemExit(run_cli(
        execute=execute,
        ticket_prefix="[intel-who-gho]",
        schema_path=SCHEMA_PATH,
        catalog_path=CATALOG_PATH,
        status_schema="who-gho-ticket-status-v1",
        display_name="WHO GHO OData",
    ))
'''
write(WHO / "who_gho_task.py", TASK)

TEST = r'''from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("who_gho_task", ROOT / "who_gho_task.py")
assert SPEC and SPEC.loader
task = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(task)


class FakeResponse:
    ok = True
    status_code = 200
    headers = {"Content-Type": "application/json"}
    content = b'{"@odata.context":"x","value":[{"IndicatorCode":"WHOSIS_000001","SpatialDim":"CHN","TimeDim":2021,"NumericValue":78.2}]}'
    def json(self):
        return json.loads(self.content)


class WhoGhoTests(unittest.TestCase):
    def ticket(self, operation="catalog-capabilities", parameters=None):
        return {
            "task_id": "who-gho-test-001",
            "provider": "who-gho-odata",
            "operation": operation,
            "objective": "test bounded WHO GHO provider",
            "parameters": parameters or {},
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "acceptance": {"timeout_seconds": 30, "max_response_bytes": 1000000},
        }

    def test_catalog_and_schema_are_fixed_and_keyless(self):
        catalog = json.loads((ROOT / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "who-gho-odata")
        self.assertEqual(provider["ticket_prefix"], "[intel-who-gho]")
        self.assertEqual(provider["required_secret_environment_variable"], "")
        self.assertEqual(len(provider["operations"]), 8)
        self.assertEqual(provider["limits"]["fixed_api_host"], "ghoapi.azureedge.net")
        self.assertFalse(provider["limits"]["arbitrary_odata_filters_allowed"])
        self.assertTrue(provider["limits"]["legacy_endpoint_migration_watch_required"])
        task.validate_ticket(self.ticket(), schema_path=task.SCHEMA_PATH, catalog_path=task.CATALOG_PATH)

    def test_request_builder_only_constructs_fixed_odata(self):
        path, query = task.build_request("get-indicator-data", {
            "indicator_code": "WHOSIS_000001",
            "country": "CHN",
            "year_from": 2015,
            "year_to": 2022,
            "sex": "BTSX",
            "top": 25,
        })
        self.assertEqual(path, "/WHOSIS_000001")
        self.assertEqual(query["$top"], "25")
        self.assertIn("SpatialDim eq 'CHN'", query["$filter"])
        self.assertIn("TimeDim ge 2015", query["$filter"])
        self.assertIn("Dim1 eq 'BTSX'", query["$filter"])
        self.assertEqual(query["$orderby"], "TimeDim desc")
        with self.assertRaises(ValueError):
            task.build_request("get-indicator-data", {"indicator_code": "https://evil.test"})
        with self.assertRaises(ValueError):
            task.build_request("search-indicators", {"query": "x' or 1 eq 1"})
        with self.assertRaises(ValueError):
            task.build_request("get-indicator-data", {"indicator_code": "WHOSIS_000001", "country": "CHN", "region": "WPR"})

    def test_local_catalog_execution_needs_no_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            ticket = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket.write_text(json.dumps(self.ticket()), encoding="utf-8")
            self.assertEqual(task.execute(ticket, out), 0)
            diagnostics = json.loads((out / "diagnostics.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostics["status"], "INTEL_WHO_GHO_COMPLETED")
            self.assertFalse(diagnostics["metadata"]["upstream_called"])

    def test_mocked_upstream_execution_is_single_keyless_get(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(task.requests, "get", return_value=FakeResponse()) as get:
            ticket = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket.write_text(json.dumps(self.ticket("get-indicator-data", {"indicator_code": "WHOSIS_000001", "country": "CHN", "top": 1})), encoding="utf-8")
            self.assertEqual(task.execute(ticket, out), 0)
            self.assertEqual(get.call_count, 1)
            kwargs = get.call_args.kwargs
            self.assertFalse(kwargs["allow_redirects"])
            self.assertNotIn("Authorization", kwargs["headers"])
            diagnostics = json.loads((out / "diagnostics.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostics["status"], "INTEL_WHO_GHO_COMPLETED")
            self.assertEqual(diagnostics["metadata"]["row_count"], 1)


if __name__ == "__main__":
    unittest.main()
'''
write(WHO / "tests/test_who_gho_task.py", TEST)

README = '''# WHO GHO OData 全球卫生数据

正式票据前缀：

```text
[intel-who-gho]
```

固定官方兼容端点：

```text
https://ghoapi.azureedge.net/api
```

无需 API Key 或 Repository Secret。

固定开放 8 项能力：本地能力目录、维度目录、维度值、指标目录、指标搜索、指标观测值、国家目录和地区目录。指标数据可按国家或 WHO 地区、年份范围、性别和分页读取。

安全边界：每张票据最多一次 GET；不自动跟随 `@odata.nextLink`；不接受任意 `$filter`、`$select`、`$expand`、函数、URL、主机、路径、请求头或写操作；不允许整库下载。

迁移提示：WHO 官方页面说明当前 GHO OData 接口计划在 2025 年底前后迁移至 World Health Data Hub 的新 OData 实现。2026 年 8 月接入时兼容端点仍可响应，但必须保留迁移监测，未来仅在验证新官方端点和字段映射后切换。
'''
write(WHO / "README.md", README)

TICKET_WORKFLOW = '''name: Managed WHO GHO OData Intelligence Center

on:
  issues:
    types: [opened, reopened]

permissions:
  contents: read
  issues: write
  actions: read

concurrency:
  group: intel-who-gho-global
  cancel-in-progress: false

jobs:
  execute-who-gho:
    if: >-
      github.actor == github.repository_owner &&
      startsWith(github.event.issue.title, '[intel-who-gho]')
    runs-on: ubuntu-24.04
    timeout-minutes: 20
    env:
      GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      ISSUE_NUMBER: ${{ github.event.issue.number }}
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
          cache-dependency-path: api-center/who-gho/requirements.txt
      - name: Install pinned dependencies
        run: |
          python -m pip install --disable-pip-version-check --no-input -r api-center/who-gho/requirements.txt
          python -m pip check
      - name: Compile provider
        run: python -m py_compile api-center/managed_provider_runtime.py api-center/who-gho/who_gho_task.py
      - name: Parse and authorize WHO GHO ticket
        id: prepare
        continue-on-error: true
        run: python api-center/who-gho/who_gho_task.py prepare --event-path "$GITHUB_EVENT_PATH" --output-dir who-gho-artifacts
      - name: Comment accepted ticket
        if: steps.prepare.outputs.accepted == 'true'
        run: |
          python api-center/who-gho/who_gho_task.py render --output-dir who-gho-artifacts --phase accepted > who-gho-comment.md
          gh api --method POST "repos/${GITHUB_REPOSITORY}/issues/${ISSUE_NUMBER}/comments" -F body=@who-gho-comment.md
      - name: Comment rejected ticket
        if: steps.prepare.outputs.accepted != 'true'
        run: |
          python api-center/who-gho/who_gho_task.py render --output-dir who-gho-artifacts --phase rejected > who-gho-comment.md
          gh api --method POST "repos/${GITHUB_REPOSITORY}/issues/${ISSUE_NUMBER}/comments" -F body=@who-gho-comment.md
      - name: Execute one bounded WHO GHO request
        id: execute
        if: steps.prepare.outputs.accepted == 'true'
        continue-on-error: true
        run: python api-center/who-gho/who_gho_task.py execute --ticket who-gho-artifacts/ticket.json --output-dir who-gho-artifacts
      - name: Upload WHO GHO evidence
        id: upload
        if: always()
        continue-on-error: true
        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4
        with:
          name: who-gho-ticket-${{ github.event.issue.number }}-${{ github.run_id }}
          path: who-gho-artifacts/
          if-no-files-found: error
          retention-days: 30
      - name: Publish verified result or structured failure
        if: always() && steps.prepare.outputs.accepted == 'true'
        env:
          ARTIFACT_URL: ${{ steps.upload.outputs.artifact-url }}
        run: |
          python api-center/who-gho/who_gho_task.py render --output-dir who-gho-artifacts --phase completed --artifact-url "$ARTIFACT_URL" > who-gho-comment.md
          gh api --method POST "repos/${GITHUB_REPOSITORY}/issues/${ISSUE_NUMBER}/comments" -F body=@who-gho-comment.md
      - name: Mark rejected or failed execution
        if: >-
          always() &&
          (steps.prepare.outputs.accepted != 'true' ||
           steps.execute.outputs.status != 'INTEL_WHO_GHO_COMPLETED' ||
           steps.upload.outcome != 'success')
        run: exit 1
'''
write(ROOT / ".github/workflows/who-gho-api-ticket.yml", TICKET_WORKFLOW)

VALIDATE_WORKFLOW = '''name: Validate WHO GHO OData Provider

on:
  pull_request:
    paths:
      - "api-center/who-gho/**"
      - "api-center/managed_provider_runtime.py"
      - "api-center/build_catalog_market_search.py"
      - "api-center/api-catalog.json"
      - "api-center/api-catalog.md"
      - ".github/workflows/who-gho-provider-validate.yml"
      - ".github/workflows/who-gho-api-ticket.yml"
  push:
    branches: [main]
    paths:
      - "api-center/who-gho/**"
      - "api-center/managed_provider_runtime.py"
      - "api-center/build_catalog_market_search.py"
      - "api-center/api-catalog.json"
      - "api-center/api-catalog.md"
      - ".github/workflows/who-gho-provider-validate.yml"
      - ".github/workflows/who-gho-api-ticket.yml"
  workflow_dispatch:

permissions:
  contents: read

jobs:
  validate:
    runs-on: ubuntu-24.04
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4
        with:
          persist-credentials: false
      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: api-center/who-gho/requirements.txt
      - name: Install dependencies
        run: |
          python -m pip install --disable-pip-version-check --no-input -r api-center/who-gho/requirements.txt
          python -m pip check
      - name: Compile and test provider
        run: |
          python -m py_compile api-center/managed_provider_runtime.py api-center/who-gho/who_gho_task.py api-center/who-gho/tests/*.py
          python -m unittest discover -s api-center/who-gho/tests -p 'test_*.py' -v
      - name: Validate fixed safe contracts
        run: |
          python - <<'PY'
          import json
          from pathlib import Path
          from jsonschema import Draft202012Validator
          root = Path('api-center/who-gho')
          schema = json.loads((root / 'ticket.schema.json').read_text(encoding='utf-8'))
          catalog = json.loads((root / 'provider-catalog.json').read_text(encoding='utf-8'))
          Draft202012Validator.check_schema(schema)
          provider = catalog['providers'][0]
          ids = {row['operation_id'] for row in provider['operations']}
          assert provider['provider_id'] == 'who-gho-odata'
          assert provider['ticket_prefix'] == '[intel-who-gho]'
          assert provider['required_secret_environment_variable'] == ''
          assert len(ids) == 8
          assert provider['limits']['fixed_api_host'] == 'ghoapi.azureedge.net'
          assert provider['limits']['arbitrary_odata_filters_allowed'] is False
          assert provider['limits']['automatic_pagination_allowed'] is False
          assert provider['limits']['write_operations_allowed'] is False
          assert provider['limits']['legacy_endpoint_migration_watch_required'] is True
          print(json.dumps({'status':'PASS','operations':len(ids),'authentication':'none'}))
          PY
          git diff --check
'''
write(ROOT / ".github/workflows/who-gho-provider-validate.yml", VALIDATE_WORKFLOW)

# Register the provider in the deterministic catalog generator.
build = API / "build_catalog_market_search.py"
replace_once(build, 'GAPUP_MCP_CATALOG = HERE / "gapup-mcp/provider-catalog.json"\n', 'GAPUP_MCP_CATALOG = HERE / "gapup-mcp/provider-catalog.json"\nWHO_GHO_CATALOG = HERE / "who-gho/provider-catalog.json"\n')
replace_once(build, '    "gapup-mcp": 209,\n', '    "gapup-mcp": 209,\n    "who-gho-odata": 8,\n')
replace_once(build, '    GAPUP_MCP_CATALOG,\n    KNOWLEDGE_TOOLS_CATALOG,\n', '    GAPUP_MCP_CATALOG,\n    WHO_GHO_CATALOG,\n    KNOWLEDGE_TOOLS_CATALOG,\n')
replace_once(build, '        "gapup-mcp/provider-catalog.json",\n        "knowledge-tools/provider-catalog.json",\n', '        "gapup-mcp/provider-catalog.json",\n        "who-gho/provider-catalog.json",\n        "knowledge-tools/provider-catalog.json",\n')

# Update deterministic catalog regressions.
test_catalog = API / "tests/test_api_catalog.py"
replace_once(test_catalog, '    "gapup-mcp": 209,\n', '    "gapup-mcp": 209,\n    "who-gho-odata": 8,\n')
replace_once(test_catalog, 'self.assertEqual(catalog["managed_provider_count"], 31)', 'self.assertEqual(catalog["managed_provider_count"], 32)')
replace_once(test_catalog, 'self.assertEqual(catalog["enabled_managed_provider_count"], 31)', 'self.assertEqual(catalog["enabled_managed_provider_count"], 32)')
replace_once(test_catalog, 'self.assertEqual(catalog["managed_operation_count"], 569)', 'self.assertEqual(catalog["managed_operation_count"], 577)')
replace_once(
    test_catalog,
    '        self.assertNotIn("webhooks_manage", gapup_ids)\n\n        self.assertEqual(\n            providers["tushare"]',
    '''        self.assertNotIn("webhooks_manage", gapup_ids)\n\n        who = providers["who-gho-odata"]\n        self.assertEqual(who["ticket_prefix"], "[intel-who-gho]")\n        self.assertEqual(who["required_secret_environment_variable_name"], "")\n        self.assertEqual(len(who["operations"]), 8)\n        self.assertEqual(who["limits"]["fixed_api_host"], "ghoapi.azureedge.net")\n        self.assertFalse(who["limits"]["arbitrary_odata_filters_allowed"])\n        self.assertFalse(who["limits"]["automatic_pagination_allowed"])\n        self.assertFalse(who["limits"]["write_operations_allowed"])\n        self.assertTrue(who["limits"]["legacy_endpoint_migration_watch_required"])\n\n        self.assertEqual(\n            providers["tushare"]'''
)

cap = API / "tests/test_capability_maximization.py"
replace_once(cap, '            569,\n', '            577,\n')
replace_once(cap, '            "gapup-mcp": 209,\n', '            "gapup-mcp": 209,\n            "who-gho-odata": 8,\n')
replace_once(
    cap,
    '\n\nif __name__ == "__main__":\n',
    '''\n\n    def test_who_gho_odata_has_no_unbounded_query_escape_hatch(self) -> None:\n        provider = json.loads(\n            (ROOT / "who-gho/provider-catalog.json").read_text(encoding="utf-8")\n        )["providers"][0]\n        limits = provider["limits"]\n        self.assertEqual(provider["required_secret_environment_variable"], "")\n        self.assertEqual(limits["fixed_api_host"], "ghoapi.azureedge.net")\n        self.assertFalse(limits["arbitrary_urls_allowed"])\n        self.assertFalse(limits["arbitrary_odata_filters_allowed"])\n        self.assertFalse(limits["arbitrary_odata_select_allowed"])\n        self.assertFalse(limits["automatic_pagination_allowed"])\n        self.assertFalse(limits["whole_database_download_allowed"])\n        self.assertFalse(limits["write_operations_allowed"])\n        self.assertTrue(limits["legacy_endpoint_migration_watch_required"])\n\n\nif __name__ == "__main__":\n'''
)

# Add documentation without renaming compatibility paths.
api_readme = API / "README.md"
with api_readme.open("a", encoding="utf-8") as handle:
    handle.write('''\n\n## WHO GHO OData 全球卫生数据\n\n`api-center/who-gho/` 通过 WHO Global Health Observatory 的公开 OData 兼容端点读取全球卫生指标：\n\n```text\n[intel-who-gho]\nhttps://ghoapi.azureedge.net/api\n无需 Repository Secret\n```\n\n固定开放 8 项只读操作，覆盖维度、维度值、指标目录、指标搜索、国家、地区和按国家/地区、年份、性别筛选的指标观测值。禁止客户端提交任意 OData 表达式、任意 URL、自动翻页和整库下载。WHO 已公告旧 GHO OData 将迁移至 World Health Data Hub 新实现，因此该 Provider 保留迁移监测标记，不把当前兼容端点视为永久合同。\n''')
root_readme = ROOT / "README.md"
with root_readme.open("a", encoding="utf-8") as handle:
    handle.write('''\n\n### WHO GHO OData\n\n情报中心新增免密、只读的 WHO Global Health Observatory OData Provider，固定开放 8 项受控操作并保留官方接口迁移监测。\n''')
cap_doc = API / "CAPABILITY_MAXIMIZATION.md"
with cap_doc.open("a", encoding="utf-8") as handle:
    handle.write('''\n\n## WHO GHO OData\n\n开放固定维度、指标和观测值读取；不开放任意 `$filter`、`$select`、`$expand`、函数、自动分页或整库下载。当前兼容端点带有强制迁移监测标记。\n''')

# Extend the unified catalog validation workflow; it will be staged as a template by the one-shot workflow.
workflow = ROOT / ".github/workflows/api-catalog-validate.yml"
replace_once(workflow, '            api-center/gapup-mcp/requirements.txt\n', '            api-center/gapup-mcp/requirements.txt\n            api-center/who-gho/requirements.txt\n')
replace_once(workflow, '            -r api-center/gapup-mcp/requirements.txt\n', '            -r api-center/gapup-mcp/requirements.txt \\\n            -r api-center/who-gho/requirements.txt\n')
replace_once(workflow, '            api-center/gapup-mcp/gapup_mcp_task.py \\\n', '            api-center/gapup-mcp/gapup_mcp_task.py \\\n            api-center/who-gho/who_gho_task.py \\\n')
replace_once(workflow, '            api-center/gapup-mcp/tests/*.py\n', '            api-center/gapup-mcp/tests/*.py \\\n            api-center/who-gho/tests/*.py\n')
replace_once(workflow, "          python -m unittest discover -s api-center/gapup-mcp/tests -p 'test_*.py' -v\n", "          python -m unittest discover -s api-center/gapup-mcp/tests -p 'test_*.py' -v\n          python -m unittest discover -s api-center/who-gho/tests -p 'test_*.py' -v\n")
replace_once(workflow, "assert catalog['managed_provider_count'] == len(providers) == 31", "assert catalog['managed_provider_count'] == len(providers) == 32")
replace_once(workflow, "assert catalog['enabled_managed_provider_count'] == 31", "assert catalog['enabled_managed_provider_count'] == 32")
replace_once(workflow, ") == 569", ") == 577")
replace_once(
    workflow,
    "          assert 'webhooks_manage' not in gapup_ids\n\n          print(json.dumps({",
    """          assert 'webhooks_manage' not in gapup_ids\n\n          who = providers['who-gho-odata']\n          assert who['ticket_prefix'] == '[intel-who-gho]'\n          assert who['required_secret_environment_variable_name'] == ''\n          assert len(who['operations']) == 8\n          assert who['limits']['fixed_api_host'] == 'ghoapi.azureedge.net'\n          assert who['limits']['arbitrary_odata_filters_allowed'] is False\n          assert who['limits']['automatic_pagination_allowed'] is False\n          assert who['limits']['write_operations_allowed'] is False\n          assert who['limits']['legacy_endpoint_migration_watch_required'] is True\n\n          print(json.dumps({"""
)
replace_once(workflow, "              'managed_providers': 30,", "              'managed_providers': 32,")
replace_once(workflow, "              'managed_operations': 569,", "              'managed_operations': 577,")
replace_once(workflow, "              'gapup_mcp_upstream_tools': 208,\n", "              'gapup_mcp_upstream_tools': 208,\n              'who_gho_operations': 8,\n")
replace_once(workflow, '            api-center/gapup-mcp/readonly-tools.snapshot.json\n', '            api-center/gapup-mcp/readonly-tools.snapshot.json\n            api-center/who-gho/provider-catalog.json\n            api-center/who-gho/ticket.schema.json\n')

print(json.dumps({
    "status": "PASS",
    "provider": "who-gho-odata",
    "operations": 8,
    "required_secret": "",
    "ticket_prefix": "[intel-who-gho]",
    "migration_watch": True,
}))
