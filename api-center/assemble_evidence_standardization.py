#!/usr/bin/env python3
"""One-shot registrar for the local evidence-standardization provider."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CENTER = ROOT / "api-center"
PROVIDER = CENTER / "evidence-standardization"

OPERATION_SCHEMAS = {
    "catalog-capabilities": {"type": "object", "additionalProperties": False, "properties": {}, "maxProperties": 0},
    "normalize-evidence-records": {"type": "object", "additionalProperties": False, "required": ["records"], "properties": {"records": {"type": "array", "minItems": 1, "maxItems": 1000, "items": {"type": "object"}}}},
    "content-fingerprint": {"type": "object", "additionalProperties": False, "required": ["texts"], "properties": {"texts": {"type": "array", "minItems": 1, "maxItems": 1000, "items": {"type": "string", "minLength": 1, "maxLength": 200000}}, "near_duplicate_hamming_threshold": {"type": "integer", "minimum": 0, "maximum": 16}}},
    "provenance-lineage": {"type": "object", "additionalProperties": False, "required": ["nodes", "edges"], "properties": {"nodes": {"type": "array", "minItems": 1, "maxItems": 5000, "items": {"type": "object"}}, "edges": {"type": "array", "maxItems": 20000, "items": {"type": "object"}}}},
    "timeline-version-diff": {"type": "object", "additionalProperties": False, "required": ["versions"], "properties": {"versions": {"type": "array", "minItems": 2, "maxItems": 200, "items": {"type": "object"}}}},
    "stix-bundle-validate": {"type": "object", "additionalProperties": False, "required": ["bundle"], "properties": {"bundle": {"type": "object"}}},
    "transfer-package-manifest": {"type": "object", "additionalProperties": False, "required": ["files"], "properties": {"files": {"type": "array", "minItems": 1, "maxItems": 1000, "items": {"type": "object"}}}},
    "source-quality-profile": {"type": "object", "additionalProperties": False, "required": ["sources"], "properties": {"sources": {"type": "array", "minItems": 1, "maxItems": 1000, "items": {"type": "object"}}}},
}

DESCRIPTIONS = {
    "catalog-capabilities": "读取本地证据标准化能力目录，不访问外部网络。",
    "normalize-evidence-records": "将公开、非个人的来源记录规范化为统一证据记录并生成内容哈希和稳定记录ID。",
    "content-fingerprint": "生成SHA-256和64位SimHash，识别精确重复和受限近重复内容。",
    "provenance-lineage": "验证来源、快照、处理和传输节点形成的有向无环谱系图。",
    "timeline-version-diff": "按UTC时间排序公开文档版本并计算逐版本变更摘要。",
    "stix-bundle-validate": "离线验证STIX 2.1 Bundle的对象身份、重复项和内部引用完整性。",
    "transfer-package-manifest": "为GPTs证据中继生成公开、非个人文件清单和规范哈希。",
    "source-quality-profile": "按权威性、直接性、时效性、交叉印证和方法透明度形成来源质量画像。",
}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_provider_catalog() -> None:
    operations = []
    for operation_id in OPERATION_SCHEMAS:
        operations.append({
            "operation_id": operation_id,
            "description": DESCRIPTIONS[operation_id],
            "parameters": sorted(OPERATION_SCHEMAS[operation_id].get("properties", {})),
            "parameter_schema": OPERATION_SCHEMAS[operation_id],
            "result_contract": {
                "provider": "evidence-standardization",
                "http_method": "LOCAL",
                "read_only": True,
                "network_used": False,
                "model_calls": 0,
                "secret_used": False,
            },
            "discovery_policy": {"source": "repository-governed-local-capability"},
        })
    catalog = {
        "schema_version": "evidence-standardization-provider-catalog-v1",
        "secret_values_exposed": False,
        "replaced_legacy_connectors": [],
        "providers": [{
            "provider_id": "evidence-standardization",
            "display_name": "证据标准化、去重、谱系与传输清单",
            "description": "对已采集的公开、非个人证据执行本地规范化、指纹去重、来源谱系、版本差异、STIX离线校验、来源质量画像和传输清单生成。",
            "enabled": True,
            "ticket_prefix": "[intel-evidence-standardize]",
            "required_secret_environment_variable": "",
            "catalog_policy": "仅处理票据内已提供的公开、非个人结构化证据；不访问网络、不读取文件路径、不接受代码、不推断个人身份。",
            "execution_policy": "每张票据执行一个固定本地操作；输入有界，输出包含哈希、状态和零网络零模型调用回执。",
            "limits": {
                "requests_per_ticket": 0,
                "timeout_seconds_max": 60,
                "max_response_bytes": 10000000,
                "records_max": 1000,
                "graph_nodes_max": 5000,
                "graph_edges_max": 20000,
                "arbitrary_urls_allowed": False,
                "arbitrary_files_allowed": False,
                "arbitrary_code_allowed": False,
                "network_allowed": False,
                "personal_data_allowed": False,
                "secret_values_exposed": False,
            },
            "operations": operations,
        }],
    }
    write_json(PROVIDER / "provider-catalog.json", catalog)


def build_ticket_schema() -> None:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://github.com/a15280020511/evidence-data-center/api-center/evidence-standardization/ticket.schema.json",
        "title": "Local evidence standardization ticket",
        "type": "object",
        "additionalProperties": False,
        "required": ["task_id", "provider", "operation", "parameters", "data_policy", "acceptance"],
        "properties": {
            "task_id": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$"},
            "provider": {"const": "evidence-standardization"},
            "operation": {"type": "string", "enum": list(OPERATION_SCHEMAS)},
            "objective": {"type": "string", "minLength": 1, "maxLength": 1000},
            "parameters": {"type": "object", "maxProperties": 8},
            "data_policy": {
                "type": "object",
                "additionalProperties": False,
                "required": ["classification", "contains_personal_data"],
                "properties": {"classification": {"const": "public"}, "contains_personal_data": {"const": False}},
            },
            "acceptance": {
                "type": "object",
                "additionalProperties": False,
                "required": ["timeout_seconds", "max_response_bytes"],
                "properties": {"timeout_seconds": {"type": "integer", "minimum": 5, "maximum": 60}, "max_response_bytes": {"type": "integer", "minimum": 1024, "maximum": 10000000}},
            },
        },
        "allOf": [{"if": {"properties": {"operation": {"const": operation}}}, "then": {"properties": {"parameters": parameter_schema}}} for operation, parameter_schema in OPERATION_SCHEMAS.items()],
    }
    write_json(PROVIDER / "ticket.schema.json", schema)


def patch_catalog_builder() -> None:
    path = CENTER / "build_catalog_market_search.py"
    text = path.read_text(encoding="utf-8")
    if "EVIDENCE_STANDARDIZATION_CATALOG" not in text:
        text = text.replace(
            'HUGGINGFACE_CATALOG = HERE / "huggingface/provider-catalog.json"\n',
            'HUGGINGFACE_CATALOG = HERE / "huggingface/provider-catalog.json"\nEVIDENCE_STANDARDIZATION_CATALOG = HERE / "evidence-standardization/provider-catalog.json"\n',
        )
    if '"evidence-standardization": 8,' not in text:
        text = text.replace('    "huggingface-hub": 11,\n', '    "huggingface-hub": 11,\n    "evidence-standardization": 8,\n')
    if "    EVIDENCE_STANDARDIZATION_CATALOG,\n" not in text:
        text = text.replace("    HUGGINGFACE_CATALOG,\n)", "    HUGGINGFACE_CATALOG,\n    EVIDENCE_STANDARDIZATION_CATALOG,\n)")
    if '"evidence-standardization/provider-catalog.json",' not in text:
        text = text.replace('        "huggingface/provider-catalog.json",\n    ):', '        "huggingface/provider-catalog.json",\n        "evidence-standardization/provider-catalog.json",\n    ):')
    path.write_text(text, encoding="utf-8")


def patch_count_contracts() -> None:
    allowed = {".py", ".yml", ".yaml", ".json", ".md", ".txt"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in allowed or ".git" in path.parts:
            continue
        if path in {CENTER / "api-catalog.json", CENTER / "api-catalog.md", CENTER / "build_catalog_market_search.py"}:
            continue
        text = path.read_text(encoding="utf-8")
        original = text
        text = re.sub(r'("managed_provider_count"\s*:\s*)51\b', r'\g<1>52', text)
        text = re.sub(r'("enabled_managed_provider_count"\s*:\s*)51\b', r'\g<1>52', text)
        text = re.sub(r'("managed_operation_count"\s*:\s*)580\b', r'\g<1>588', text)
        text = re.sub(r"(['\"]managed_provider_count['\"]\s*(?:==|:|=)\s*)51\b", r"\g<1>52", text)
        text = re.sub(r"(['\"]managed_operation_count['\"]\s*(?:==|:|=)\s*)580\b", r"\g<1>588", text)
        text = re.sub(r"(?i)(managed providers?\s*[:=/|` ]+?)51\b", r"\g<1>52", text)
        text = re.sub(r"(?i)(managed operations?\s*[:=/|` ]+?)580\b", r"\g<1>588", text)
        if text != original:
            path.write_text(text, encoding="utf-8")


def patch_readme() -> None:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    heading = "## 证据标准化能力层"
    if heading not in text:
        text += """

## 证据标准化能力层

`api-center/evidence-standardization/` 提供8项零密钥本地能力：目录读取、证据记录规范化、内容指纹与近重复、来源谱系DAG、时间版本差异、STIX 2.1离线结构校验、GPTs传输清单和来源质量画像。该层不采集外部数据、不访问网络、不读取票据文件路径、不处理个人数据，也不执行模型调用。

仓库根目录 `CENTER_CAPABILITY_OWNERSHIP.json` 是计算中心与情报中心的权威工具归属合同。
"""
        path.write_text(text, encoding="utf-8")


def main() -> int:
    build_provider_catalog()
    build_ticket_schema()
    patch_catalog_builder()
    patch_count_contracts()
    patch_readme()
    subprocess.run(["python", str(CENTER / "build_catalog_market_search.py")], check=True, cwd=ROOT)
    print(json.dumps({"status": "PASS", "provider": "evidence-standardization", "operations": 8, "managed_providers": 52, "managed_operations": 588}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
