#!/usr/bin/env python3
"""Generate the deterministic maximum-safe API-center capability catalog.

The catalog embeds every repository-declared read-only request/response contract
and every managed-provider operation schema. Credential names may be shown;
credential or authorization values are never copied into the catalog.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

HERE = Path(__file__).resolve().parent
MANAGED_PROVIDER_CATALOG_PATHS = (
    HERE / "google-cloud/provider-catalog.json",
    HERE / "akshare/provider-catalog.json",
    HERE / "aifin-market/provider-catalog.json",
    HERE / "yuandian/provider-catalog.json",
    HERE / "company-intelligence/provider-catalog.json",
    HERE / "web-retrieval/provider-catalog.json",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_sha(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _fallback_parameter_schema(names: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            name: {"type": ["string", "integer", "number", "boolean"]}
            for name in names
        },
    }


def _load_provider_snapshot(raw_provider: Mapping[str, Any]) -> tuple[str, dict[str, Any] | None]:
    relative = str(raw_provider.get("readonly_tool_snapshot_file") or "")
    if not relative:
        return "", None
    path = HERE / relative
    if not path.is_file():
        raise ValueError(f"managed provider snapshot does not exist: {relative}")
    snapshot = load_json(path)
    if not isinstance(snapshot, Mapping):
        raise ValueError(f"managed provider snapshot must be an object: {relative}")
    if snapshot.get("secret_values_exposed") is not False:
        raise ValueError(f"managed provider snapshot must forbid secret exposure: {relative}")
    expected = str(raw_provider.get("readonly_tool_snapshot_sha256") or "")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if expected and expected != actual:
        raise ValueError(f"managed provider snapshot SHA mismatch: {relative}")
    return relative, dict(snapshot)


def _build_managed_providers() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    catalogs: list[dict[str, Any]] = []
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    replaced: list[dict[str, Any]] = []
    for path in MANAGED_PROVIDER_CATALOG_PATHS:
        if not path.is_file():
            continue
        catalog = load_json(path)
        if not isinstance(catalog, Mapping):
            raise ValueError(f"managed provider catalog must be a JSON object: {path}")
        if catalog.get("secret_values_exposed") is not False:
            raise ValueError(f"managed provider catalog must forbid secret exposure: {path}")
        providers = catalog.get("providers")
        if not isinstance(providers, list):
            raise ValueError(f"managed provider catalog has no providers array: {path}")
        catalogs.append({"file": str(path.relative_to(HERE)), "sha256": canonical_sha(catalog)})
        replaced.extend(list(catalog.get("replaced_legacy_connectors") or []))
        catalog_ticket_prefix = str(catalog.get("ticket_prefix") or "")
        catalog_secret_name = str(catalog.get("required_secret_environment_variable") or "")
        for raw_provider in providers:
            if not isinstance(raw_provider, Mapping):
                raise ValueError("managed provider row must be an object")
            provider_id = str(raw_provider.get("provider_id") or "")
            if not provider_id or provider_id in seen:
                raise ValueError(f"invalid or duplicate managed provider id: {provider_id}")
            seen.add(provider_id)
            operations = raw_provider.get("operations")
            if not isinstance(operations, list) or not operations:
                raise ValueError(f"managed provider {provider_id} has no operations")
            operation_ids: set[str] = set()
            safe_operations: list[dict[str, Any]] = []
            for operation in operations:
                if not isinstance(operation, Mapping):
                    raise ValueError(f"managed provider {provider_id} operation must be an object")
                operation_id = str(operation.get("operation_id") or "")
                if not operation_id or operation_id in operation_ids:
                    raise ValueError(
                        f"managed provider {provider_id} has invalid or duplicate operation {operation_id}"
                    )
                operation_ids.add(operation_id)
                parameter_names = [str(item) for item in operation.get("parameters") or []]
                parameter_schema = operation.get("parameter_schema")
                if not isinstance(parameter_schema, Mapping):
                    parameter_schema = _fallback_parameter_schema(parameter_names)
                safe_operation = {
                    "operation_id": operation_id,
                    "description": str(operation.get("description") or ""),
                    "parameter_names": parameter_names,
                    "parameter_schema": dict(parameter_schema),
                }
                for optional_key in ("examples", "result_contract", "discovery_policy"):
                    if optional_key in operation:
                        safe_operation[optional_key] = operation[optional_key]
                safe_operations.append(safe_operation)
            snapshot_file, snapshot = _load_provider_snapshot(raw_provider)
            row = {
                "provider_id": provider_id,
                "display_name": str(raw_provider.get("display_name") or provider_id),
                "description": str(raw_provider.get("description") or ""),
                "enabled": bool(raw_provider.get("enabled")),
                "ticket_prefix": str(raw_provider.get("ticket_prefix") or catalog_ticket_prefix),
                "catalog_policy": str(raw_provider.get("catalog_policy") or ""),
                "execution_policy": str(raw_provider.get("execution_policy") or ""),
                "operation_count": len(safe_operations),
                "operations": safe_operations,
                "limits": dict(raw_provider.get("limits") or {}),
                "required_secret_environment_variable_name": str(
                    raw_provider.get("required_secret_environment_variable") or catalog_secret_name
                ),
                "optional_secret_environment_variable_name": str(
                    raw_provider.get("optional_secret_environment_variable") or ""
                ),
                "secret_value_exposed": False,
                "provider_sha256": canonical_sha(raw_provider),
                "catalog_file": str(path.relative_to(HERE)),
            }
            for key in (
                "discovered_readonly_tool_count",
                "discovered_readonly_tools_by_server",
            ):
                if key in raw_provider:
                    row[key] = raw_provider[key]
            if snapshot is not None:
                row["readonly_tool_snapshot_file"] = snapshot_file
                row["readonly_tool_snapshot"] = snapshot
            rows.append(row)
    combined = {
        "schema_version": "managed-provider-catalog-index-v2",
        "catalogs": catalogs,
        "providers": rows,
        "operation_count": sum(row["operation_count"] for row in rows),
        "replaced_legacy_connectors": replaced,
        "secret_values_exposed": False,
    }
    return combined, rows


def _ordered_unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _safe_credential_contract(connector: Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(connector.get("secret_query"), Mapping):
        secret = connector["secret_query"]
        return {
            "injection": "query",
            "parameter_name": str(secret.get("name") or ""),
            "environment_variable_name": str(secret.get("env") or ""),
            "value_exposed": False,
        }
    if isinstance(connector.get("secret_header"), Mapping):
        secret = connector["secret_header"]
        return {
            "injection": "header",
            "parameter_name": str(secret.get("name") or ""),
            "environment_variable_name": str(secret.get("env") or ""),
            "value_exposed": False,
        }
    return {"injection": "none", "value_exposed": False}


def build(manifest_path: Path, metadata_path: Path, connector_root: Path) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    metadata = load_json(metadata_path)
    rows = manifest.get("connectors") if isinstance(manifest, Mapping) else None
    metadata_rows = metadata.get("connectors") if isinstance(metadata, Mapping) else None
    if not isinstance(rows, list):
        raise ValueError("connector manifest has no connectors array")
    if not isinstance(metadata_rows, Mapping):
        raise ValueError("catalog metadata has no connectors object")

    manifest_ids = {str(row.get("id") or "") for row in rows if isinstance(row, Mapping)}
    metadata_ids = {str(key) for key in metadata_rows}
    missing = sorted(manifest_ids - metadata_ids)
    extra = sorted(metadata_ids - manifest_ids)
    if missing or extra:
        raise ValueError(f"catalog metadata mismatch; missing={missing}; extra={extra}")

    catalog_rows: list[dict[str, Any]] = []
    for manifest_row in rows:
        connector_id = str(manifest_row["id"])
        detail_file = str(manifest_row["file"])
        connector_path = HERE / detail_file
        if not connector_path.is_file():
            connector_path = connector_root / Path(detail_file).name
        connector = load_json(connector_path)
        meta = metadata_rows[connector_id]
        if not isinstance(meta, Mapping):
            raise ValueError(f"catalog metadata for {connector_id} must be an object")
        if str(connector.get("id") or "") != connector_id:
            raise ValueError(f"connector detail mismatch for {connector_id}")
        query_parameters = [str(item) for item in connector.get("input_query_strings") or []]
        path_contract = connector.get("path_parameters") or {}
        path_parameter_names = [str(item) for item in manifest_row.get("path_parameter_names") or []]
        if isinstance(path_contract, Mapping):
            path_parameter_names = _ordered_unique(
                path_parameter_names + [str(item) for item in path_contract]
            )
        notes = dict(meta.get("parameter_notes") or {})
        parameter_names = _ordered_unique(path_parameter_names + query_parameters + list(notes))
        backend = dict(connector.get("backend") or {})
        catalog_rows.append(
            {
                "connector_id": connector_id,
                "display_name": str(meta["display_name"]),
                "description": str(meta["description"]),
                "data_category": str(meta["data_category"]),
                "use_cases": list(meta.get("use_cases") or []),
                "enabled": bool(manifest_row["enabled"]),
                "endpoint": str(manifest_row["endpoint"]),
                "method": str(manifest_row["method"]),
                "output_encoding": str(connector.get("output_encoding") or "json"),
                "timeout": str(connector.get("timeout") or ""),
                "write_approved": bool(manifest_row.get("write_approved")),
                "parameter_names": parameter_names,
                "request_contract": {
                    "path_parameter_names": path_parameter_names,
                    "path_parameters": dict(path_contract) if isinstance(path_contract, Mapping) else {},
                    "query_parameter_names": query_parameters,
                    "parameter_rules": dict(connector.get("parameter_rules") or {}),
                    "parameter_notes": notes,
                    "example_parameters": dict(meta.get("example_parameters") or {}),
                    "input_headers": list(connector.get("input_headers") or []),
                    "additional_parameters_allowed": False,
                },
                "response_contract": dict(connector.get("response_contract") or {}),
                "response_quality": dict(connector.get("response_quality") or {}),
                "backend_contract": {
                    "host": str(backend.get("host") or ""),
                    "url_pattern": str(backend.get("url_pattern") or ""),
                    "method": str(backend.get("method") or ""),
                    "encoding": str(backend.get("encoding") or ""),
                    "allowed_response_fields": list(backend.get("allow") or []),
                    "resilience": dict(backend.get("resilience") or {}),
                    "rate_limit_enabled": bool(manifest_row.get("backend_rate_limit")),
                    "circuit_breaker_enabled": bool(manifest_row.get("default_circuit_breaker")),
                    "ssrf_static_policy": str(manifest_row.get("ssrf_static_policy") or ""),
                },
                "credential_contract": _safe_credential_contract(connector),
                "example_parameters": dict(meta.get("example_parameters") or {}),
                "geographic_coverage": str(meta.get("geographic_coverage") or "unknown"),
                "freshness": str(meta.get("freshness") or "unknown"),
                "cost_class": str(meta.get("cost_class") or "unknown"),
                "limitations": list(meta.get("limitations") or []),
                "detail_file": detail_file,
                "metadata_pointer": f"catalog-metadata.json#/connectors/{connector_id}",
                "secret_environment_variable_name": manifest_row.get(
                    "secret_environment_variable"
                ),
                "secret_value_exposed": False,
                "connector_sha256": str(
                    manifest_row.get("connector_sha256") or canonical_sha(connector)
                ),
            }
        )

    managed_catalog, managed_rows = _build_managed_providers()
    operation_count = sum(row["operation_count"] for row in managed_rows)
    catalog = {
        "schema_version": "api-catalog-v3",
        "exposure_mode": "maximum-safe-readonly",
        "generation": "deterministic-from-repository-state",
        "source_manifest_file": "connector-manifest.json",
        "source_metadata_file": "catalog-metadata.json",
        "source_manifest_version": manifest.get("version"),
        "source_manifest_sha256": canonical_sha(manifest),
        "source_metadata_sha256": canonical_sha(metadata),
        "managed_provider_catalog_file": "managed-provider-index",
        "managed_provider_catalog_files": [item["file"] for item in managed_catalog.get("catalogs", [])],
        "managed_provider_catalog_sha256": canonical_sha(managed_catalog),
        "connector_count": len(catalog_rows),
        "enabled_connector_count": sum(bool(row["enabled"]) for row in catalog_rows),
        "managed_provider_count": len(managed_rows),
        "enabled_managed_provider_count": sum(bool(row["enabled"]) for row in managed_rows),
        "managed_operation_count": operation_count,
        "exposed_parameter_count": sum(len(row["parameter_names"]) for row in catalog_rows)
        + sum(
            len(operation["parameter_names"])
            for provider in managed_rows
            for operation in provider["operations"]
        ),
        "selection_owner": "gpts-usage-center",
        "maintenance_owner": "web-gpt-github-plugin",
        "direct_center_to_center_calls_allowed": False,
        "secret_values_exposed": False,
        "detail_reading_order": [
            "api-catalog.json",
            "google-cloud/provider-catalog.json",
            "akshare/provider-catalog.json",
            "aifin-market/provider-catalog.json",
            "aifin-market/readonly-tools.snapshot.json",
            "yuandian/provider-catalog.json",
            "yuandian/readonly-apis.snapshot.json",
            "catalog-metadata.json",
            "connector-manifest.json",
            "connectors/<connector>.connector.json",
        ],
        "safe_exposure_policy": {
            "all_enabled_capabilities": True,
            "full_parameter_contracts_embedded": True,
            "full_response_contracts_embedded": True,
            "safe_backend_contracts_embedded": True,
            "managed_provider_operation_schemas_embedded": True,
            "live_readonly_tool_or_function_discovery": True,
            "health_metadata": True,
            "secret_environment_variable_names": True,
            "secret_values": False,
            "authorization_values": False,
            "arbitrary_urls": False,
            "arbitrary_code": False,
            "write_or_trade_operations": False,
            "direct_center_to_center_calls": False,
        },
        "managed_providers": managed_rows,
        "replaced_legacy_connectors": list(managed_catalog.get("replaced_legacy_connectors") or []),
        "connectors": catalog_rows,
    }
    catalog["catalog_sha256"] = canonical_sha(catalog)
    return catalog


def render_markdown(catalog: Mapping[str, Any]) -> str:
    lines = [
        "# API 中心能力目录",
        "",
        f"- 开放模式：`{catalog['exposure_mode']}`",
        f"- 普通连接器：`{catalog['enabled_connector_count']}/{catalog['connector_count']}` 已启用",
        f"- 托管提供方：`{catalog['enabled_managed_provider_count']}/{catalog['managed_provider_count']}` 已启用",
        f"- 托管操作总数：`{catalog['managed_operation_count']}`",
        f"- 已公开参数总数：`{catalog['exposed_parameter_count']}`",
        f"- 目录 SHA-256：`{catalog['catalog_sha256']}`",
        "- 选择者：`GPTs 使用中心`",
        "- 维修者：`普通网页 GPT + GitHub 插件`",
        "- Secret/Authorization 值：`不暴露`",
        "- 写入、交易、任意URL、任意代码、跨中心直连：`不开放`",
        "",
        "本目录直接嵌入普通连接器的请求、响应、字段、韧性和安全契约，以及托管提供方每个操作的完整参数Schema。",
        "",
        "## 托管提供方",
        "",
        "| 提供方 | ID | 状态 | 票据前缀 | 操作数量 | 动态只读发现 |",
        "|---|---|---|---|---|---|",
    ]
    for provider in catalog["managed_providers"]:
        state = "启用" if provider["enabled"] else "停用"
        dynamic = "是" if any(
            provider["limits"].get(key)
            for key in (
                "catalog_discovered_readonly_tool_names_allowed",
                "catalog_discovered_readonly_functions_allowed",
            )
        ) else "否"
        lines.append(
            f"| {provider['display_name']} | `{provider['provider_id']}` | {state} | "
            f"`{provider['ticket_prefix']}` | `{provider['operation_count']}` | {dynamic} |"
        )
    lines.extend([
        "",
        "## 普通连接器",
        "",
        "| 能力 | ID | 状态 | 分类 | 端点 | 参数数 |",
        "|---|---|---|---|---|---|",
    ])
    for row in catalog["connectors"]:
        state = "启用" if row["enabled"] else "停用"
        lines.append(
            f"| {row['display_name']} | `{row['connector_id']}` | {state} | "
            f"`{row['data_category']}` | `{row['method']} {row['endpoint']}` | "
            f"`{len(row['parameter_names'])}` |"
        )
    lines.extend([
        "",
        "## 不可取消的安全边界",
        "",
        "1. 只读公开数据能力最大化开放；",
        "2. Secret与Authorization只显示环境变量名称，绝不显示值；",
        "3. 动态工具/函数必须先从固定上游或固定安装包发现，再通过只读、签名和Schema校验；",
        "4. 禁止任意URL、请求头、文件路径、脚本、代码、写入、交易和下单；",
        "5. 三中心继续隔离，只能由GPTs传递任务与结果。",
        "",
    ])
    for provider in catalog["managed_providers"]:
        state = "启用" if provider["enabled"] else "停用"
        lines.extend([
            f"## {provider['display_name']} (`{provider['provider_id']}`)",
            "",
            f"- 状态：`{state}`",
            f"- 说明：{provider['description']}",
            f"- 目录策略：{provider['catalog_policy']}",
            f"- 执行策略：{provider['execution_policy']}",
            f"- 票据前缀：`{provider['ticket_prefix']}`",
            "- Secret环境变量名："
            f"`{provider['required_secret_environment_variable_name'] or '无'}`（仅名称）",
            f"- 提供方SHA-256：`{provider['provider_sha256']}`",
            "",
            "| 操作 | 说明 | 参数 |",
            "|---|---|---|",
        ])
        for operation in provider["operations"]:
            lines.append(
                f"| `{operation['operation_id']}` | {operation['description']} | "
                f"`{', '.join(operation['parameter_names']) or '无'}` |"
            )
            lines.extend([
                "",
                f"`{operation['operation_id']}` 参数Schema：",
                "",
                "```json",
                json.dumps(operation["parameter_schema"], ensure_ascii=False, indent=2),
                "```",
                "",
            ])
        if provider.get("readonly_tool_snapshot"):
            lines.extend([
                "最近一次受控只读工具快照：",
                "",
                "```json",
                json.dumps(provider["readonly_tool_snapshot"], ensure_ascii=False, indent=2),
                "```",
                "",
            ])
        lines.extend([
            "限制：",
            "",
            "```json",
            json.dumps(provider["limits"], ensure_ascii=False, indent=2),
            "```",
            "",
        ])
    for row in catalog["connectors"]:
        state = "启用" if row["enabled"] else "停用"
        lines.extend([
            f"## {row['display_name']} (`{row['connector_id']}`)",
            "",
            f"- 状态：`{state}`",
            f"- 说明：{row['description']}",
            f"- 适用：{'；'.join(row['use_cases'])}",
            f"- 地域：{row['geographic_coverage']}",
            f"- 新鲜度：{row['freshness']}",
            f"- 成本等级：`{row['cost_class']}`",
            f"- 详情文件：`{row['detail_file']}`",
            f"- Secret环境变量名：`{row['secret_environment_variable_name'] or '无'}`（仅名称）",
            f"- 连接器SHA-256：`{row['connector_sha256']}`",
            "",
            "请求契约：",
            "",
            "```json",
            json.dumps(row["request_contract"], ensure_ascii=False, indent=2),
            "```",
            "",
            "响应契约：",
            "",
            "```json",
            json.dumps(row["response_contract"], ensure_ascii=False, indent=2),
            "```",
            "",
            "安全后端契约：",
            "",
            "```json",
            json.dumps(row["backend_contract"], ensure_ascii=False, indent=2),
            "```",
            "",
        ])
        if row["limitations"]:
            lines.append("限制：")
            for item in row["limitations"]:
                lines.append(f"- {item}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(HERE / "connector-manifest.json"))
    parser.add_argument("--metadata", default=str(HERE / "catalog-metadata.json"))
    parser.add_argument("--json-output", default=str(HERE / "api-catalog.json"))
    parser.add_argument("--markdown-output", default=str(HERE / "api-catalog.md"))
    args = parser.parse_args()
    catalog = build(Path(args.manifest), Path(args.metadata), HERE / "connectors")
    Path(args.json_output).write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    Path(args.markdown_output).write_text(render_markdown(catalog), encoding="utf-8")
    print(json.dumps({
        "catalog_sha256": catalog["catalog_sha256"],
        "connector_count": catalog["connector_count"],
        "enabled_connector_count": catalog["enabled_connector_count"],
        "managed_provider_count": catalog["managed_provider_count"],
        "enabled_managed_provider_count": catalog["enabled_managed_provider_count"],
        "managed_operation_count": catalog["managed_operation_count"],
        "exposed_parameter_count": catalog["exposed_parameter_count"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
