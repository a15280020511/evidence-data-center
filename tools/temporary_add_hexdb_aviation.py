#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROVIDER = ROOT / "api-center" / "hexdb-aviation"
PROVIDER.mkdir(parents=True, exist_ok=True)
(PROVIDER / "tests").mkdir(parents=True, exist_ok=True)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


catalog = {
    "schema_version": "hexdb-aviation-provider-catalog-v1",
    "secret_values_exposed": False,
    "replaced_legacy_connectors": [],
    "providers": [
        {
            "provider_id": "hexdb-aviation",
            "display_name": "HexDB 航空器型号、注册与航线补全",
            "description": "使用 HexDB 的只读 REST API，按 ICAO24、航班呼号或机场代码补全 OpenSky 状态向量缺少的飞机注册号、制造商、具体型号、登记所有人、运营方代码、航线和机场基础信息。",
            "enabled": True,
            "ticket_prefix": "[intel-hexdb]",
            "required_secret_environment_variable": "",
            "catalog_policy": "固定访问 hexdb.io 的公开只读 REST API；不允许任意 URL、批量抓取、图片抓取、后台轮询、自动重试或写操作。数据来自第三方和众包来源，仅作为证据补全，不替代航空主管机关登记。",
            "execution_policy": "每张票据最多一次 GET，只允许单个 ICAO24、单个呼号或单个机场代码。上游当前公开说明为每 5 分钟不超过 1000 次请求，情报中心进一步限制为全局并发 1、无重试、无自动翻页。",
            "official_documentation": "https://hexdb.io/",
            "official_origin": "https://hexdb.io/api/v1",
            "service_status_notice": "HexDB 是公开第三方航空元数据服务；记录可能缺失、陈旧或由众包纠正，不能据此作适航、所有权或监管结论。",
            "limits": {
                "requests_per_ticket_max": 1,
                "transient_retry_max": 0,
                "provider_concurrency_max": 1,
                "timeout_seconds_max": 30,
                "max_response_bytes": 2000000,
                "upstream_requests_per_window_max": 1000,
                "upstream_rate_window_seconds": 300,
                "fixed_api_host": "hexdb.io",
                "single_identifier_per_ticket_required": True,
                "automatic_retry_allowed": False,
                "automatic_pagination_allowed": False,
                "background_polling_allowed": False,
                "bulk_lookup_allowed": False,
                "image_retrieval_allowed": False,
                "legacy_text_endpoints_allowed": False,
                "arbitrary_urls_allowed": False,
                "arbitrary_hosts_allowed": False,
                "arbitrary_headers_allowed": False,
                "client_supplied_credentials_allowed": False,
                "write_operations_allowed": False,
                "secret_values_exposed": False,
                "authentication_required": False,
            },
            "operations": [
                {
                    "operation_id": "catalog-capabilities",
                    "description": "读取本地 HexDB 安全能力目录，不访问上游。",
                    "parameters": [],
                    "parameter_schema": {"type": "object", "additionalProperties": False, "properties": {}},
                    "result_contract": {"provider": "hexdb-aviation", "http_method": "LOCAL", "read_only": True, "credential_mode": "none"},
                },
                {
                    "operation_id": "aircraft-by-icao24",
                    "description": "按六位 ICAO24/Mode-S 地址读取注册号、制造商、ICAO 机型代码、具体机型、登记所有人和运营方代码。",
                    "parameters": ["icao24"],
                    "parameter_schema": {"type": "object", "additionalProperties": False, "properties": {"icao24": {"type": "string", "pattern": "^[0-9A-Fa-f]{6}$"}}, "required": ["icao24"]},
                    "result_contract": {"provider": "hexdb-aviation", "http_method": "GET", "read_only": True, "credential_mode": "none", "quality": "crowdsourced_best_effort"},
                },
                {
                    "operation_id": "route-by-icao-callsign",
                    "description": "按 ICAO 航班呼号读取推定起点—终点机场代码。",
                    "parameters": ["callsign"],
                    "parameter_schema": {"type": "object", "additionalProperties": False, "properties": {"callsign": {"type": "string", "pattern": "^[A-Za-z0-9]{2,12}$"}}, "required": ["callsign"]},
                    "result_contract": {"provider": "hexdb-aviation", "http_method": "GET", "read_only": True, "credential_mode": "none", "quality": "crowdsourced_best_effort"},
                },
                {
                    "operation_id": "route-by-iata-callsign",
                    "description": "按 IATA 航班呼号读取推定起点—终点机场代码。",
                    "parameters": ["callsign"],
                    "parameter_schema": {"type": "object", "additionalProperties": False, "properties": {"callsign": {"type": "string", "pattern": "^[A-Za-z0-9]{2,12}$"}}, "required": ["callsign"]},
                    "result_contract": {"provider": "hexdb-aviation", "http_method": "GET", "read_only": True, "credential_mode": "none", "quality": "crowdsourced_best_effort"},
                },
                {
                    "operation_id": "airport-by-icao",
                    "description": "按四位 ICAO 机场代码读取机场名称、IATA 代码、国家、地区及坐标。",
                    "parameters": ["airport"],
                    "parameter_schema": {"type": "object", "additionalProperties": False, "properties": {"airport": {"type": "string", "pattern": "^[A-Za-z0-9]{4}$"}}, "required": ["airport"]},
                    "result_contract": {"provider": "hexdb-aviation", "http_method": "GET", "read_only": True, "credential_mode": "none", "quality": "crowdsourced_best_effort"},
                },
                {
                    "operation_id": "airport-by-iata",
                    "description": "按三位 IATA 机场代码读取机场名称、ICAO 代码、国家、地区及坐标。",
                    "parameters": ["airport"],
                    "parameter_schema": {"type": "object", "additionalProperties": False, "properties": {"airport": {"type": "string", "pattern": "^[A-Za-z0-9]{3}$"}}, "required": ["airport"]},
                    "result_contract": {"provider": "hexdb-aviation", "http_method": "GET", "read_only": True, "credential_mode": "none", "quality": "crowdsourced_best_effort"},
                },
            ],
        }
    ],
}
write(PROVIDER / "provider-catalog.json", json.dumps(catalog, ensure_ascii=False, separators=(",", ":")))

schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://github.com/a15280020511/evidence-data-center/api-center/hexdb-aviation/ticket.schema.json",
    "title": "HexDB aviation metadata bounded read-only ticket",
    "type": "object",
    "additionalProperties": False,
    "required": ["task_id", "provider", "operation", "objective", "parameters", "data_policy", "acceptance"],
    "properties": {
        "task_id": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$"},
        "provider": {"const": "hexdb-aviation"},
        "operation": {"type": "string", "enum": ["catalog-capabilities", "aircraft-by-icao24", "route-by-icao-callsign", "route-by-iata-callsign", "airport-by-icao", "airport-by-iata"]},
        "objective": {"type": "string", "minLength": 1, "maxLength": 1000},
        "parameters": {"type": "object", "maxProperties": 1},
        "data_policy": {"type": "object", "additionalProperties": False, "required": ["classification", "contains_personal_data"], "properties": {"classification": {"const": "public"}, "contains_personal_data": {"const": False}}},
        "acceptance": {"type": "object", "additionalProperties": False, "required": ["timeout_seconds", "max_response_bytes"], "properties": {"timeout_seconds": {"type": "integer", "minimum": 5, "maximum": 30}, "max_response_bytes": {"type": "integer", "minimum": 1024, "maximum": 2000000}}},
    },
}
write(PROVIDER / "ticket.schema.json", json.dumps(schema, ensure_ascii=False, indent=2))

write(PROVIDER / "requirements.txt", "requests==2.34.2")

write(PROVIDER / "README.md", r'''# HexDB 航空器元数据补全

该 Provider 用于补全 OpenSky 状态向量不包含的静态航空器和航线信息，固定访问：

```text
https://hexdb.io/api/v1
```

无需 API Key，票据前缀：

```text
[intel-hexdb]
```

## 能力

- `aircraft-by-icao24`：注册号、制造商、ICAO 机型代码、具体机型、登记所有人、运营方代码；
- `route-by-icao-callsign`：ICAO 呼号对应的推定航线；
- `route-by-iata-callsign`：IATA 呼号对应的推定航线；
- `airport-by-icao`：ICAO 机场代码对应的机场名称、IATA、国家、地区和坐标；
- `airport-by-iata`：IATA 机场代码对应的机场名称、ICAO、国家、地区和坐标；
- `catalog-capabilities`：本地能力目录。

## 与 OpenSky 的组合

OpenSky 提供实时经纬度、高度、速度、航迹角、垂直速度和 ICAO24。将 OpenSky 返回的 `icao24` 传给 `aircraft-by-icao24`，即可补全飞机注册号、制造商和具体型号；将呼号传给航线操作，可补全推定起讫机场。

## 固定边界

- 每张票据只查询一个标识符，并只发送一次 GET；
- 不自动重试、不自动翻页、不批量抓取、不获取图片；
- 固定主机 `hexdb.io`，禁止任意 URL、主机、请求头和写操作；
- 上游公开说明为每 5 分钟不超过 1000 次请求，情报中心进一步限制并发为 1；
- 数据来自第三方和众包来源，可能缺失、陈旧或有误，不替代民航主管机关登记或适航资料。
''')

write(PROVIDER / "hexdb_aviation_task.py", r'''#!/usr/bin/env python3
"""Bounded read-only HexDB aviation metadata execution."""
from __future__ import annotations

import json
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
ORIGIN = "https://hexdb.io"
ICAO24_RE = re.compile(r"^[0-9A-Fa-f]{6}$")
CALLSIGN_RE = re.compile(r"^[A-Za-z0-9]{2,12}$")
ICAO_AIRPORT_RE = re.compile(r"^[A-Za-z0-9]{4}$")
IATA_AIRPORT_RE = re.compile(r"^[A-Za-z0-9]{3}$")


def _value(parameters: Mapping[str, Any], key: str, pattern: re.Pattern[str]) -> str:
    value = str(parameters.get(key) or "").strip()
    if not pattern.fullmatch(value):
        raise ValueError(f"{key} is invalid")
    return value.upper()


def build_request(operation: str, parameters: Mapping[str, Any]) -> str | None:
    if operation == "catalog-capabilities":
        if parameters:
            raise ValueError("catalog-capabilities does not accept parameters")
        return None
    if operation == "aircraft-by-icao24":
        return "/api/v1/aircraft/" + quote(_value(parameters, "icao24", ICAO24_RE), safe="")
    if operation == "route-by-icao-callsign":
        return "/api/v1/route/icao/" + quote(_value(parameters, "callsign", CALLSIGN_RE), safe="")
    if operation == "route-by-iata-callsign":
        return "/api/v1/route/iata/" + quote(_value(parameters, "callsign", CALLSIGN_RE), safe="")
    if operation == "airport-by-icao":
        return "/api/v1/airport/icao/" + quote(_value(parameters, "airport", ICAO_AIRPORT_RE), safe="")
    if operation == "airport-by-iata":
        return "/api/v1/airport/iata/" + quote(_value(parameters, "airport", IATA_AIRPORT_RE), safe="")
    raise ValueError(f"unsupported operation: {operation}")


def _is_not_found(status_code: int, payload: Any) -> bool:
    if status_code == 404:
        return True
    if isinstance(payload, Mapping):
        return str(payload.get("status") or "") == "404"
    return False


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(acceptance.get("timeout_seconds"), default=20, minimum=5, maximum=30, name="timeout_seconds")
    max_bytes = bounded_int(acceptance.get("max_response_bytes"), default=500_000, minimum=1024, maximum=2_000_000, name="max_response_bytes")
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_HEXDB_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "api_origin": "hexdb.io",
        "credential_mode": "none",
        "secret_values_exposed": False,
        "requests_per_ticket": 1,
        "automatic_retry": False,
        "automatic_pagination": False,
        "bulk_lookup": False,
        "data_quality": "crowdsourced_best_effort",
    }
    try:
        path = build_request(operation, parameters)
        if path is None:
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        else:
            response = requests.get(
                ORIGIN + path,
                headers={"Accept": "application/json", "User-Agent": "intelligence-center-hexdb/1"},
                timeout=timeout,
                allow_redirects=False,
            )
            raw = bytes(response.content or b"")
            if len(raw) > max_bytes:
                raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
            try:
                payload = response.json()
            except ValueError as exc:
                raise RuntimeError("HexDB returned invalid JSON") from exc
            if _is_not_found(response.status_code, payload):
                clean = payload if isinstance(payload, Mapping) else {"status": "404", "error": "not found"}
                snapshot = {"provider": "hexdb-aviation", "operation": operation, "found": False, "record": clean}
            else:
                if not response.ok:
                    raise RuntimeError(f"HexDB HTTP {response.status_code}: {str(payload)[:1000]}")
                if not isinstance(payload, Mapping):
                    raise RuntimeError("HexDB response contract is not an object")
                snapshot = {"provider": "hexdb-aviation", "operation": operation, "found": True, "record": dict(payload)}
            sanitized = (json.dumps(snapshot, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
            if len(sanitized) > max_bytes:
                raise RuntimeError("sanitized response exceeds max_response_bytes")
            (output_dir / "response.json").write_bytes(sanitized)
            metadata.update({
                "upstream_called": True,
                "http_status": response.status_code,
                "request_path": path,
                "response_bytes": len(sanitized),
                "response_sha256": bytes_sha(sanitized),
                "found": bool(snapshot.get("found")),
            })
        status = "INTEL_HEXDB_COMPLETED"
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
        schema_prefix="hexdb-aviation",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-hexdb]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="hexdb-aviation-ticket-status-v1",
            display_name="HexDB Aviation",
        )
    )
''')

write(PROVIDER / "tests" / "test_hexdb_aviation_task.py", r'''from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("hexdb_aviation_task", HERE / "hexdb_aviation_task.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class FakeResponse:
    def __init__(self, status_code: int, payload: object) -> None:
        self.status_code = status_code
        self._payload = payload
        self.content = json.dumps(payload).encode("utf-8")
        self.ok = 200 <= status_code < 300

    def json(self) -> object:
        return self._payload


class HexDbAviationTests(unittest.TestCase):
    def test_fixed_paths(self) -> None:
        self.assertEqual(module.build_request("aircraft-by-icao24", {"icao24": "4010ee"}), "/api/v1/aircraft/4010EE")
        self.assertEqual(module.build_request("route-by-icao-callsign", {"callsign": "ein17a"}), "/api/v1/route/icao/EIN17A")
        self.assertEqual(module.build_request("airport-by-iata", {"airport": "foc"}), "/api/v1/airport/iata/FOC")

    def test_invalid_identifier_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            module.build_request("aircraft-by-icao24", {"icao24": "../bad"})
        with self.assertRaises(ValueError):
            module.build_request("airport-by-icao", {"airport": "ZSFZ?"})

    def _ticket(self, operation: str, parameters: dict) -> dict:
        return {
            "task_id": "hexdb-test-001",
            "provider": "hexdb-aviation",
            "operation": operation,
            "objective": "test",
            "parameters": parameters,
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "acceptance": {"timeout_seconds": 10, "max_response_bytes": 100000},
        }

    @patch.object(module.requests, "get")
    def test_aircraft_success_is_persisted(self, get) -> None:
        get.return_value = FakeResponse(200, {"ICAOTypeCode": "A319", "Manufacturer": "Airbus", "ModeS": "4010EE", "Registration": "G-EZBZ", "Type": "A319 111"})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket = root / "ticket.json"
            out = root / "out"
            ticket.write_text(json.dumps(self._ticket("aircraft-by-icao24", {"icao24": "4010ee"})), encoding="utf-8")
            self.assertEqual(module.execute(ticket, out), 0)
            payload = json.loads((out / "response.json").read_text(encoding="utf-8"))
            self.assertTrue(payload["found"])
            self.assertEqual(payload["record"]["Manufacturer"], "Airbus")
            get.assert_called_once()

    @patch.object(module.requests, "get")
    def test_not_found_is_structured_success(self, get) -> None:
        get.return_value = FakeResponse(404, {"status": "404", "error": "Aircraft not found."})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket = root / "ticket.json"
            out = root / "out"
            ticket.write_text(json.dumps(self._ticket("aircraft-by-icao24", {"icao24": "000000"})), encoding="utf-8")
            self.assertEqual(module.execute(ticket, out), 0)
            payload = json.loads((out / "response.json").read_text(encoding="utf-8"))
            self.assertFalse(payload["found"])

    def test_catalog_contract(self) -> None:
        catalog = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "hexdb-aviation")
        self.assertEqual(provider["ticket_prefix"], "[intel-hexdb]")
        self.assertEqual(len(provider["operations"]), 6)
        self.assertEqual(provider["limits"]["requests_per_ticket_max"], 1)
        self.assertFalse(provider["limits"]["bulk_lookup_allowed"])
        self.assertFalse(provider["limits"]["write_operations_allowed"])


if __name__ == "__main__":
    unittest.main()
''')

write(ROOT / ".github" / "workflows" / "hexdb-aviation-api-ticket.yml", r'''name: Managed HexDB Aviation Intelligence Center

on:
  issues:
    types: [opened, reopened]

permissions:
  contents: read
  issues: write
  actions: read

concurrency:
  group: intel-hexdb-global
  cancel-in-progress: false

jobs:
  execute-hexdb:
    if: >-
      github.actor == github.repository_owner &&
      startsWith(github.event.issue.title, '[intel-hexdb]')
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    env:
      GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      ISSUE_NUMBER: ${{ github.event.issue.number }}
    steps:
      - name: Checkout pinned source
        uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262
        with:
          persist-credentials: false

      - name: Set up isolated Python
        uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: |
            api-center/requirements.txt
            api-center/hexdb-aviation/requirements.txt

      - name: Install pinned dependencies
        run: |
          python -m pip install --disable-pip-version-check --no-input \
            -r api-center/requirements.txt \
            -r api-center/hexdb-aviation/requirements.txt
          python -m pip check

      - name: Compile provider
        run: python -m py_compile api-center/managed_provider_runtime.py api-center/hexdb-aviation/hexdb_aviation_task.py

      - name: Parse and authorize HexDB ticket
        id: prepare
        continue-on-error: true
        run: python api-center/hexdb-aviation/hexdb_aviation_task.py prepare --event-path "$GITHUB_EVENT_PATH" --output-dir hexdb-artifacts

      - name: Comment accepted ticket
        if: steps.prepare.outputs.accepted == 'true'
        run: |
          python api-center/hexdb-aviation/hexdb_aviation_task.py render --output-dir hexdb-artifacts --phase accepted > hexdb-comment.md
          gh api --method POST "repos/${GITHUB_REPOSITORY}/issues/${ISSUE_NUMBER}/comments" -F body=@hexdb-comment.md

      - name: Comment rejected ticket
        if: steps.prepare.outputs.accepted != 'true'
        run: |
          python api-center/hexdb-aviation/hexdb_aviation_task.py render --output-dir hexdb-artifacts --phase rejected > hexdb-comment.md
          gh api --method POST "repos/${GITHUB_REPOSITORY}/issues/${ISSUE_NUMBER}/comments" -F body=@hexdb-comment.md

      - name: Execute one bounded HexDB request
        id: execute
        if: steps.prepare.outputs.accepted == 'true'
        continue-on-error: true
        run: python api-center/hexdb-aviation/hexdb_aviation_task.py execute --ticket hexdb-artifacts/ticket.json --output-dir hexdb-artifacts

      - name: Upload HexDB evidence
        id: upload
        if: always()
        continue-on-error: true
        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02
        with:
          name: hexdb-ticket-${{ github.event.issue.number }}-${{ github.run_id }}
          path: hexdb-artifacts/
          if-no-files-found: error
          retention-days: 30

      - name: Publish verified result or structured failure
        if: always() && steps.prepare.outputs.accepted == 'true'
        env:
          ARTIFACT_URL: ${{ steps.upload.outputs.artifact-url }}
        run: |
          python api-center/hexdb-aviation/hexdb_aviation_task.py render --output-dir hexdb-artifacts --phase completed --artifact-url "$ARTIFACT_URL" > hexdb-comment.md
          gh api --method POST "repos/${GITHUB_REPOSITORY}/issues/${ISSUE_NUMBER}/comments" -F body=@hexdb-comment.md

      - name: Mark rejected or failed execution
        if: >-
          always() &&
          (steps.prepare.outputs.accepted != 'true' ||
           steps.execute.outputs.status != 'INTEL_HEXDB_COMPLETED' ||
           steps.upload.outcome != 'success')
        run: exit 1
''')

write(ROOT / ".github" / "workflows" / "hexdb-aviation-provider-validate.yml", r'''name: Validate HexDB Aviation Provider

on:
  pull_request:
    paths:
      - "api-center/hexdb-aviation/**"
      - "api-center/managed_provider_runtime.py"
      - "api-center/build_catalog_market_search.py"
      - "api-center/api-catalog.json"
      - "api-center/api-catalog.md"
      - ".github/workflows/hexdb-aviation-provider-validate.yml"
      - ".github/workflows/hexdb-aviation-api-ticket.yml"
  push:
    branches: [main]
    paths:
      - "api-center/hexdb-aviation/**"
      - "api-center/managed_provider_runtime.py"
      - "api-center/build_catalog_market_search.py"
      - "api-center/api-catalog.json"
      - "api-center/api-catalog.md"
      - ".github/workflows/hexdb-aviation-provider-validate.yml"
      - ".github/workflows/hexdb-aviation-api-ticket.yml"
  workflow_dispatch:

permissions:
  contents: read

jobs:
  validate:
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262
        with:
          persist-credentials: false
      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: |
          python -m pip install --disable-pip-version-check --no-input \
            -r api-center/requirements.txt \
            -r api-center/hexdb-aviation/requirements.txt
          python -m pip check
      - name: Compile and test provider
        run: |
          python -m py_compile api-center/managed_provider_runtime.py api-center/hexdb-aviation/hexdb_aviation_task.py api-center/hexdb-aviation/tests/*.py
          python -m unittest discover -s api-center/hexdb-aviation/tests -p 'test_*.py' -v
      - name: Validate fixed safe contracts
        run: |
          python - <<'PY'
          import json
          from pathlib import Path
          from jsonschema import Draft202012Validator
          root = Path('api-center/hexdb-aviation')
          schema = json.loads((root / 'ticket.schema.json').read_text(encoding='utf-8'))
          provider = json.loads((root / 'provider-catalog.json').read_text(encoding='utf-8'))['providers'][0]
          Draft202012Validator.check_schema(schema)
          ids = {row['operation_id'] for row in provider['operations']}
          assert provider['provider_id'] == 'hexdb-aviation'
          assert provider['ticket_prefix'] == '[intel-hexdb]'
          assert provider['required_secret_environment_variable'] == ''
          assert len(ids) == 6
          assert provider['limits']['requests_per_ticket_max'] == 1
          assert provider['limits']['fixed_api_host'] == 'hexdb.io'
          assert provider['limits']['bulk_lookup_allowed'] is False
          assert provider['limits']['image_retrieval_allowed'] is False
          assert provider['limits']['automatic_retry_allowed'] is False
          assert provider['limits']['write_operations_allowed'] is False
          assert all(row['result_contract']['read_only'] is True for row in provider['operations'])
          print(json.dumps({'status':'PASS','operations':len(ids),'fixed_host':'hexdb.io'}))
          PY
          git diff --check
''')

# Register provider in the catalog generator.
path = ROOT / "api-center" / "build_catalog_market_search.py"
text = path.read_text(encoding="utf-8")
replacements = [
    (
        'OPENSKY_NETWORK_CATALOG = HERE / "opensky-network/provider-catalog.json"\nKNOWLEDGE_TOOLS_CATALOG',
        'OPENSKY_NETWORK_CATALOG = HERE / "opensky-network/provider-catalog.json"\nHEXDB_AVIATION_CATALOG = HERE / "hexdb-aviation/provider-catalog.json"\nKNOWLEDGE_TOOLS_CATALOG',
    ),
    ('    "opensky-network": 9,\n    "wolfram-alpha": 4,', '    "opensky-network": 9,\n    "hexdb-aviation": 6,\n    "wolfram-alpha": 4,'),
    ('    OPENSKY_NETWORK_CATALOG,\n    KNOWLEDGE_TOOLS_CATALOG,', '    OPENSKY_NETWORK_CATALOG,\n    HEXDB_AVIATION_CATALOG,\n    KNOWLEDGE_TOOLS_CATALOG,'),
    ('        "opensky-network/provider-catalog.json",\n        "knowledge-tools/provider-catalog.json",', '        "opensky-network/provider-catalog.json",\n        "hexdb-aviation/provider-catalog.json",\n        "knowledge-tools/provider-catalog.json",'),
]
for old, new in replacements:
    if old not in text:
        raise RuntimeError(f"catalog generator marker missing: {old[:80]}")
    text = text.replace(old, new, 1)
write(path, text)

# Aggregate catalog tests.
path = ROOT / "api-center" / "tests" / "test_api_catalog.py"
text = path.read_text(encoding="utf-8")
text = text.replace('    "opensky-network": 9,\n    "wolfram-alpha": 4,', '    "opensky-network": 9,\n    "hexdb-aviation": 6,\n    "wolfram-alpha": 4,', 1)
text = text.replace('self.assertEqual(catalog["managed_provider_count"], 41)', 'self.assertEqual(catalog["managed_provider_count"], 42)', 1)
text = text.replace('self.assertEqual(catalog["enabled_managed_provider_count"], 41)', 'self.assertEqual(catalog["enabled_managed_provider_count"], 42)', 1)
text = text.replace('self.assertEqual(catalog["managed_operation_count"], 445)', 'self.assertEqual(catalog["managed_operation_count"], 451)', 1)
write(path, text)

path = ROOT / "api-center" / "tests" / "test_capability_maximization.py"
text = path.read_text(encoding="utf-8")
text = text.replace('            445,', '            451,', 1)
text = text.replace('            "opensky-network": 9,\n            "wolfram-alpha": 4,', '            "opensky-network": 9,\n            "hexdb-aviation": 6,\n            "wolfram-alpha": 4,', 1)
write(path, text)

# Unified CI dependencies and invariants.
path = ROOT / ".github" / "workflows" / "api-catalog-validate.yml"
text = path.read_text(encoding="utf-8")
text = text.replace('            -r api-center/opensky-network/requirements.txt', '            -r api-center/opensky-network/requirements.txt \\\n            -r api-center/hexdb-aviation/requirements.txt', 1)
text = text.replace("assert catalog['managed_provider_count'] == len(providers) == 41", "assert catalog['managed_provider_count'] == len(providers) == 42", 1)
text = text.replace("assert catalog['enabled_managed_provider_count'] == 41", "assert catalog['enabled_managed_provider_count'] == 42", 1)
text = text.replace("assert catalog['managed_operation_count'] == 445", "assert catalog['managed_operation_count'] == 451", 1)
marker = "          assert all(row['result_contract']['read_only'] is True for row in opensky['operations'])\n\n"
insert = marker + "          hexdb = providers['hexdb-aviation']\n          assert hexdb['ticket_prefix'] == '[intel-hexdb]'\n          assert hexdb['required_secret_environment_variable_name'] == ''\n          assert len(hexdb['operations']) == 6\n          assert hexdb['limits']['requests_per_ticket_max'] == 1\n          assert hexdb['limits']['fixed_api_host'] == 'hexdb.io'\n          assert hexdb['limits']['bulk_lookup_allowed'] is False\n          assert hexdb['limits']['image_retrieval_allowed'] is False\n          assert hexdb['limits']['automatic_retry_allowed'] is False\n          assert hexdb['limits']['write_operations_allowed'] is False\n          assert all(row['result_contract']['read_only'] is True for row in hexdb['operations'])\n\n"
if marker not in text:
    raise RuntimeError("unified CI OpenSky assertion marker missing")
text = text.replace(marker, insert, 1)
text = text.replace("              'managed_providers': 41,", "              'managed_providers': 42,", 1)
text = text.replace("              'managed_operations': 445,", "              'managed_operations': 451,", 1)
text = text.replace("              'opensky_operations': 9,", "              'opensky_operations': 9,\n              'hexdb_operations': 6,", 1)
write(path, text)

# Explain the complementary enrichment path in OpenSky docs.
path = ROOT / "api-center" / "opensky-network" / "README.md"
text = path.read_text(encoding="utf-8")
addition = '''\n## 航空器型号与注册信息补全\n\nOpenSky 状态向量本身不保证返回注册号、制造商或具体机型。情报中心同时接入 `hexdb-aviation`：将 OpenSky 返回的 `icao24` 交给 `aircraft-by-icao24`，可补全注册号、制造商、ICAO 机型代码、具体机型、登记所有人和运营方代码；呼号可进一步补全推定航线和机场信息。该补全数据为第三方众包性质，必须保留来源和不确定性说明。\n'''
if "## 航空器型号与注册信息补全" not in text:
    text = text.rstrip() + "\n" + addition
write(path, text)

# Regenerate deterministic public catalog artifacts.
subprocess.run(["python", "api-center/build_catalog_market_search.py"], cwd=ROOT, check=True)
print(json.dumps({"status": "PASS", "provider": "hexdb-aviation", "operations": 6}, ensure_ascii=False))
