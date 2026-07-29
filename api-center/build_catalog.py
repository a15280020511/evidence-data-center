#!/usr/bin/env python3
"""Generate a safe, deterministic GPTs-facing API capability index.

The index exposes ordinary HTTP connectors and managed provider operations while
never copying credential values into repository artifacts.
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
                safe_operations.append({
                    "operation_id": operation_id,
                    "description": str(operation.get("description") or ""),
                    "parameter_names": [str(item) for item in operation.get("parameters") or []],
                })
            rows.append({
                "provider_id": provider_id,
                "display_name": str(raw_provider.get("display_name") or provider_id),
                "description": str(raw_provider.get("description") or ""),
                "enabled": bool(raw_provider.get("enabled")),
                "ticket_prefix": str(raw_provider.get("ticket_prefix") or catalog_ticket_prefix),
                "catalog_policy": str(raw_provider.get("catalog_policy") or ""),
                "execution_policy": str(raw_provider.get("execution_policy") or ""),
                "operations": safe_operations,
                "limits": dict(raw_provider.get("limits") or {}),
                "required_secret_environment_variable_name": str(
                    raw_provider.get("required_secret_environment_variable") or catalog_secret_name
                ),
                "secret_value_exposed": False,
                "provider_sha256": canonical_sha(raw_provider),
                "catalog_file": str(path.relative_to(HERE)),
            })
    combined = {
        "schema_version": "managed-provider-catalog-index-v1",
        "catalogs": catalogs,
        "providers": rows,
        "replaced_legacy_connectors": replaced,
        "secret_values_exposed": False,
    }
    return combined, rows


def build(
    manifest_path: Path,
    metadata_path: Path,
    connector_root: Path,
) -> dict[str, Any]:
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
                "parameter_names": list((meta.get("parameter_notes") or {}).keys()),
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
    catalog = {
        "schema_version": "api-catalog-v2",
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
        "enabled_managed_provider_count": sum(
            bool(row["enabled"]) for row in managed_rows
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
            "catalog-metadata.json",
            "connector-manifest.json",
            "connectors/<connector>.connector.json",
        ],
        "safe_exposure_policy": {
            "capabilities": True,
            "parameters": True,
            "response_contracts_in_detail_files": True,
            "managed_provider_operations": True,
            "managed_provider_limits": True,
            "health_metadata": True,
            "secret_environment_variable_names": True,
            "secret_values": False,
            "authorization_values": False,
        },
        "managed_providers": managed_rows,
        "replaced_legacy_connectors": list(
            managed_catalog.get("replaced_legacy_connectors") or []
        ),
        "connectors": catalog_rows,
    }
    catalog["catalog_sha256"] = canonical_sha(catalog)
    return catalog


def render_markdown(catalog: Mapping[str, Any]) -> str:
    lines = [
        "# API 中心能力目录",
        "",
        f"- 普通连接器总数：`{catalog['connector_count']}`",
        f"- 普通连接器已启用：`{catalog['enabled_connector_count']}`",
        f"- 托管提供方总数：`{catalog['managed_provider_count']}`",
        f"- 托管提供方已启用：`{catalog['enabled_managed_provider_count']}`",
        f"- 目录 SHA-256：`{catalog['catalog_sha256']}`",
        "- 选择者：`GPTs 使用中心`",
        "- 维修者：`普通网页 GPT + GitHub 插件`",
        "- Secret 值：`不暴露`",
        "",
        "GPTs先读本目录。BigQuery、Earth Engine、AKShare、Ashare与AIFin Market的完整操作目录分别在 "
        "`google-cloud/provider-catalog.json`、`akshare/provider-catalog.json`和"
        "`aifin-market/provider-catalog.json`；普通接口详情仍在连接器和元数据文件中。",
        "",
        "## 托管提供方",
        "",
        "| 提供方 | ID | 状态 | 票据前缀 | 操作数量 |",
        "|---|---|---|---|---|",
    ]
    for provider in catalog["managed_providers"]:
        state = "启用" if provider["enabled"] else "停用"
        lines.append(
            f"| {provider['display_name']} | `{provider['provider_id']}` | {state} | "
            f"`{provider['ticket_prefix']}` | `{len(provider['operations'])}` |"
        )
    lines.extend(
        [
            "",
            "## 普通连接器",
            "",
            "| 能力 | ID | 状态 | 分类 | 端点 | 参数 |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in catalog["connectors"]:
        state = "启用" if row["enabled"] else "停用"
        lines.append(
            f"| {row['display_name']} | `{row['connector_id']}` | {state} | "
            f"`{row['data_category']}` | `{row['method']} {row['endpoint']}` | "
            f"`{', '.join(row['parameter_names']) or '无'}` |"
        )
    lines.extend(["", "## 使用规则", ""])
    lines.extend(
        [
            "1. GPTs只能选择已启用能力；",
            "2. BigQuery和Earth Engine使用 `[api-gcp]` 票据，并先读完整托管目录；",
            "3. BigQuery执行必须先dry-run，受扫描费用、项目和行数上限约束；",
            "4. Earth Engine只允许目录读取和只读值计算，禁止导出或修改资产；",
            "5. AKShare使用 `[api-akshare]`，Ashare使用 `[api-ashare]`，AIFin Market使用 `[api-aifin]`；",
            "6. 普通连接器继续使用 `[api]` 票据和固定参数白名单；",
            "7. 所有目录只暴露Secret环境变量名称，不暴露值。",
            "",
        ]
    )
    for provider in catalog["managed_providers"]:
        state = "启用" if provider["enabled"] else "停用"
        lines.extend(
            [
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
            ]
        )
        for operation in provider["operations"]:
            lines.append(
                f"| `{operation['operation_id']}` | {operation['description']} | "
                f"`{', '.join(operation['parameter_names']) or '无'}` |"
            )
        lines.extend(
            [
                "",
                "限制：",
                "",
                "```json",
                json.dumps(provider["limits"], ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        )
    if catalog.get("replaced_legacy_connectors"):
        lines.extend(["## 已由托管提供方替代的旧连接器", ""])
        for item in catalog["replaced_legacy_connectors"]:
            lines.append(
                f"- `{item['connector_id']}` → {item['replacement']}"
            )
        lines.append("")
    for row in catalog["connectors"]:
        state = "启用" if row["enabled"] else "停用"
        lines.extend(
            [
                f"## {row['display_name']} (`{row['connector_id']}`)",
                "",
                f"- 状态：`{state}`",
                f"- 说明：{row['description']}",
                f"- 适用：{'；'.join(row['use_cases'])}",
                f"- 地域：{row['geographic_coverage']}",
                f"- 新鲜度：{row['freshness']}",
                f"- 成本等级：`{row['cost_class']}`",
                f"- 详情文件：`{row['detail_file']}`",
                f"- 元数据位置：`{row['metadata_pointer']}`",
                "- Secret环境变量名："
                f"`{row['secret_environment_variable_name'] or '无'}`（仅名称）",
                f"- 连接器SHA-256：`{row['connector_sha256']}`",
                "",
                "示例参数：",
                "",
                "```json",
                json.dumps(row["example_parameters"], ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        )
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
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    Path(args.markdown_output).write_text(
        render_markdown(catalog), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "catalog_sha256": catalog["catalog_sha256"],
                "connector_count": catalog["connector_count"],
                "enabled_connector_count": catalog["enabled_connector_count"],
                "managed_provider_count": catalog["managed_provider_count"],
                "enabled_managed_provider_count": catalog[
                    "enabled_managed_provider_count"
                ],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
