#!/usr/bin/env python3
"""Build the deterministic YuanDian managed-provider catalog from the frozen safe API snapshot."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SNAPSHOT_PATH = HERE / "readonly-apis.snapshot.json"
OUTPUT_PATH = HERE / "provider-catalog.json"


def _schema(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
    }
    if required:
        row["required"] = required
    return row


def _bounded_call_schema(*, route_key: bool = False) -> dict[str, Any]:
    properties: dict[str, Any] = {
        "arguments": {"type": "object", "maxProperties": 60, "additionalProperties": True},
        "timeout_seconds": {"type": "integer", "minimum": 5, "maximum": 120},
        "max_response_bytes": {"type": "integer", "minimum": 1024, "maximum": 5_000_000},
    }
    required: list[str] = []
    if route_key:
        properties = {
            "route_key": {"type": "string", "pattern": "^[A-Za-z][A-Za-z0-9_]{2,95}$"},
            **properties,
        }
        required = ["route_key"]
    return _schema(properties, required)


def build(snapshot: dict[str, Any]) -> dict[str, Any]:
    apis = snapshot["apis"]
    operations: list[dict[str, Any]] = [
        {
            "operation_id": "catalog-capabilities",
            "description": "读取元典适配器的本地完整安全目录、37项冻结只读API和限制，不访问上游。",
            "parameters": [],
            "parameter_schema": _schema({}),
        },
        {
            "operation_id": "catalog-live",
            "description": "从元典官方公开JSON目录读取当前API、方法、分类、价格及请求/响应参数元数据；不需要业务API密钥。",
            "parameters": ["category_id", "page_size"],
            "parameter_schema": _schema({
                "category_id": {"type": "integer", "enum": [6, 7, 9, 10]},
                "page_size": {"type": "integer", "minimum": 1, "maximum": 200},
            }),
        },
        {
            "operation_id": "invoke-readonly-api",
            "description": "按元典官方实时目录选择任一GET/POST只读API并调用；固定官方主机，不接受任意URL、请求头或代码。",
            "parameters": ["route_key", "arguments", "timeout_seconds", "max_response_bytes"],
            "parameter_schema": _bounded_call_schema(route_key=True),
        },
    ]
    for api in apis:
        operations.append({
            "operation_id": api["operation_id"],
            "description": f"{api['display_name']}：{api['description']}",
            "parameters": ["arguments", "timeout_seconds", "max_response_bytes"],
            "parameter_schema": _bounded_call_schema(),
            "result_contract": {
                "provider": "yuandian-law",
                "route_key": api["route_key"],
                "http_method": api["http_method"],
                "read_only": True,
            },
            "discovery_policy": {
                "source": "repository-snapshot-and-official-live-catalog",
                "full_contract_url": api["full_contract_discovery"],
            },
        })
    snapshot_sha = hashlib.sha256(SNAPSHOT_PATH.read_bytes()).hexdigest()
    provider = {
        "provider_id": "yuandian-law",
        "display_name": "元典法律智能开放平台",
        "description": "通过元典官方开放平台读取中国法律法规、案例文书、企业公开信息和法律幻觉校验数据；冻结37项只读API，并通过官方实时目录自动发现后续安全只读能力。",
        "enabled": True,
        "ticket_prefix": "[api-yuandian]",
        "catalog_policy": "GPTs可读取冻结API快照和官方实时JSON目录；固定操作直接映射冻结routeKey，通用调用只允许官方目录当前登记的GET/POST接口。",
        "execution_policy": "每张票据只执行一个只读调用；固定https://open.chineselaw.com主机，使用后端X-API-Key；限制参数深度、条数、超时和响应大小；过滤密钥和直接个人标识字段。",
        "readonly_tool_snapshot_file": "yuandian/readonly-apis.snapshot.json",
        "readonly_tool_snapshot_sha256": snapshot_sha,
        "discovered_readonly_tool_count": len(apis),
        "discovered_readonly_tools_by_server": snapshot["categories"],
        "operations": operations,
        "limits": {
            "max_operations_per_ticket": 1,
            "max_response_bytes_default": 1_000_000,
            "max_response_bytes_hard": 5_000_000,
            "timeout_seconds_default": 60,
            "timeout_seconds_hard": 120,
            "max_argument_properties": 60,
            "max_argument_depth": 6,
            "max_array_items": 200,
            "fixed_origin": "https://open.chineselaw.com",
            "snapshot_api_count": len(apis),
            "live_catalog_page_size_hard": 200,
            "arbitrary_urls_allowed": False,
            "arbitrary_headers_allowed": False,
            "arbitrary_code_allowed": False,
            "write_operations_allowed": False,
            "secret_values_exposed": False,
            "direct_personal_identifiers_redacted": True,
            "billing_unit": "POINT",
            "documented_cost_range_points_per_call": [1, 50],
        },
    }
    return {
        "schema_version": "yuandian-provider-catalog-v1",
        "ticket_prefix": "[api-yuandian]",
        "required_secret_environment_variable": "YUANDIAN_API_KEY",
        "secret_values_exposed": False,
        "replaced_legacy_connectors": [],
        "providers": [provider],
    }


def main() -> int:
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    catalog = build(snapshot)
    OUTPUT_PATH.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
