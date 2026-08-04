#!/usr/bin/env python3
"""Generate frozen Baidu search, model-summary, and Baike provider contracts."""
from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def text(max_length: int, min_length: int = 1) -> dict[str, Any]:
    return {"type": "string", "minLength": min_length, "maxLength": max_length}


def integer(minimum: int, maximum: int, default: int | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"type": "integer", "minimum": minimum, "maximum": maximum}
    if default is not None:
        row["default"] = default
    return row


def enum(values: list[str], default: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"type": "string", "enum": values}
    if default is not None:
        row["default"] = default
    return row


def operation(
    operation_id: str,
    description: str,
    parameters: list[tuple[str, dict[str, Any], bool]],
    *,
    origin: str = "local",
    path: str = "",
    method: str = "LOCAL",
    content_type: str = "LOCAL",
    credential_mode: str = "none",
    local: bool = False,
) -> dict[str, Any]:
    properties: OrderedDict[str, Any] = OrderedDict()
    required: list[str] = []
    for name, schema, is_required in parameters:
        properties[name] = schema
        if is_required:
            required.append(name)
    parameter_schema: dict[str, Any] = {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "maxProperties": len(properties),
    }
    if required:
        parameter_schema["required"] = required
    return {
        "operation_id": operation_id,
        "description": description,
        "parameters": list(properties),
        "parameter_schema": parameter_schema,
        "execution": {
            "local": local,
            "path_template": path,
            "http_method": method,
            "credential_mode": credential_mode,
            "content_type": content_type,
            "official_origin": origin,
        },
        "result_contract": {
            "provider": "baidu-ai-cloud",
            "official_origin": origin,
            "http_method": method,
            "read_only": True,
            "credential_mode": credential_mode,
            "secret_values_exposed": False,
            "direct_personal_identifiers_redacted": not local,
        },
    }


def operations() -> list[dict[str, Any]]:
    rows = [
        operation(
            "catalog-capabilities",
            "读取当前保留的百度能力、安全边界和操作参数，不访问上游。",
            [],
            local=True,
        ),
        operation(
            "quota-policy",
            "读取百度网页搜索免费额度与零付费策略，不访问上游。",
            [],
            local=True,
        ),
        operation(
            "web-search",
            "百度AI搜索V2：检索中国大陆公开网页并返回标题、摘要、网址和引用。",
            [
                ("query", text(256), True),
                ("top_k", integer(1, 20, 10), False),
                ("edition", enum(["standard", "lite"], "standard"), False),
                ("recency", enum(["week", "month", "semiyear", "year"]), False),
            ],
            origin="https://qianfan.baidubce.com",
            path="/v2/ai_search/web_search",
            method="POST",
            content_type="application/json",
            credential_mode="unified-api-key-bearer",
        ),
        operation(
            "web-summary",
            "百度智能搜索生成高性能版：实时检索公开网页，由模型生成摘要并返回引用。",
            [
                ("query", text(256), True),
                ("top_k", integer(1, 10, 3), False),
                ("instruction", text(4000), False),
            ],
            origin="https://qianfan.baidubce.com",
            path="/v2/ai_search/web_summary",
            method="POST",
            content_type="application/json",
            credential_mode="unified-api-key-bearer",
        ),
        operation(
            "baike-lemma-list",
            "按词条名查询百度百科义项列表，返回词条ID、名称、义项说明和公开URL。",
            [
                ("lemma_title", text(200), True),
                ("top_k", integer(1, 20, 5), False),
            ],
            origin="https://appbuilder.baidu.com",
            path="/v2/baike/lemma/get_list_by_title",
            method="GET",
            content_type="application/json",
            credential_mode="unified-api-key-bearer",
        ),
        operation(
            "baike-lemma-content",
            "按词条名或词条ID读取百度百科结构化正文、摘要、基本信息和关系。",
            [
                ("search_type", enum(["lemmaTitle", "lemmaId"], "lemmaTitle"), True),
                ("search_key", text(200), True),
            ],
            origin="https://appbuilder.baidu.com",
            path="/v2/baike/lemma/get_content",
            method="GET",
            content_type="application/json",
            credential_mode="unified-api-key-bearer",
        ),
        operation(
            "baike-starmap-list",
            "按主题查询百度百科星图列表，返回星图ID和主题名。",
            [
                ("starmap_title", text(200), False),
                ("page", integer(1, 100, 1), False),
            ],
            origin="https://qianfan.baidubce.com",
            path="/v2/tools/baike/starmap/get_starmap_by_title",
            method="GET",
            content_type="application/json",
            credential_mode="unified-api-key-bearer",
        ),
        operation(
            "baike-starmap-detail",
            "按星图ID读取百度百科星图详情和分页实体关系。",
            [
                ("starmap_id", text(128), True),
                ("page", integer(1, 100, 1), False),
            ],
            origin="https://qianfan.baidubce.com",
            path="/v2/tools/baike/starmap/get_starmap_by_id",
            method="GET",
            content_type="application/json",
            credential_mode="unified-api-key-bearer",
        ),
    ]
    assert len(rows) == 8
    return rows


def quota_policy() -> dict[str, Any]:
    return {
        "schema_version": "baidu-ai-cloud-free-quota-policy-v3",
        "reviewed_at": "2026-08-04",
        "policy": {
            "free_only": True,
            "paid_fallback_authorized": False,
            "remaining_quota_api_available": False,
            "operator_action": "仅调用已实测通过的百度网页搜索、智能摘要和百科结构化读取；百度控制台不得启用按量后付费。",
            "quota_exhaustion_behavior": "立即失败，不重试、不切换模型或其他付费接口。",
        },
        "families": [
            {
                "family": "baidu-ai-search",
                "operations": ["web-search", "web-summary"],
                "quota": "使用百度账户当前网页搜索与智能搜索生成免费额度；官方页面口径可能调整，以控制台为最终依据。",
                "reset": "daily_or_control_plane_defined",
                "verified_with_current_key": True,
            }
            ,{
                "family": "baidu-baike",
                "operations": ["baike-lemma-list", "baike-lemma-content", "baike-starmap-list", "baike-starmap-detail"],
                "quota": "百度百科正文常规免费额度1500次/月；词条义项和百科星图常规免费额度100次/天，以控制台为最终依据。",
                "reset": "daily_or_control_plane_defined",
                "verified_with_current_key": True,
            }
        ],
        "excluded": [
            {
                "family": "deep-search-deep-research-and-arbitrary-model-search",
                "reason": "未完成免费且可用的真实验收，或可能产生多次搜索及额外模型费用。",
            },
            {
                "family": "nlp-ocr-image-recognition",
                "reason": "当前Key真实调用返回IAM权限错误。",
            },
            {
                "family": "models",
                "reason": "未发现当前账户可长期免费且未退役的模型服务证据。",
            },
            {
                "family": "face-speech-generation-cloud-management",
                "reason": "高敏感、生成式、写入或非公开情报能力。",
            },
        ],
    }


def provider_catalog(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "baidu-ai-cloud-provider-catalog-v5",
        "secret_values_exposed": False,
        "replaced_legacy_connectors": [],
        "providers": [
            {
                "provider_id": "baidu-ai-cloud",
                "display_name": "百度AI搜索、模型摘要与百科",
                "description": "当前统一API Key已真实验证可用的百度公开网页搜索、模型搜索摘要与百科结构化知识。",
                "enabled": True,
                "ticket_prefix": "[intel-baidu-ai]",
                "required_secret_environment_variable": "BAIDU_AI_CLOUD_API_KEY",
                "required_secret_environment_variables": ["BAIDU_AI_CLOUD_API_KEY"],
                "credential_matrix": {
                    "web-search": ["BAIDU_AI_CLOUD_API_KEY"],
                    "web-summary": ["BAIDU_AI_CLOUD_API_KEY"],
                    "baike-lemma-list": ["BAIDU_AI_CLOUD_API_KEY"],
                    "baike-lemma-content": ["BAIDU_AI_CLOUD_API_KEY"],
                    "baike-starmap-list": ["BAIDU_AI_CLOUD_API_KEY"],
                    "baike-starmap-detail": ["BAIDU_AI_CLOUD_API_KEY"],
                    "local-governance": [],
                },
                "catalog_policy": "只开放当前Key已实测通过的6项上游高价值能力和2项本地治理能力。",
                "execution_policy": "每张票据一个操作、最多一次固定HTTPS请求；网页搜索和百科读取为零模型调用，模型摘要固定记1次模型调用；禁止重试和付费兜底。",
                "official_origins": ["https://qianfan.baidubce.com", "https://appbuilder.baidu.com"],
                "limits": {
                    "requests_per_ticket_max": 1,
                    "provider_concurrency_max": 1,
                    "transient_retry_max": 0,
                    "timeout_seconds_max": 90,
                    "max_response_bytes": 2000000,
                    "max_search_results": 20,
                    "fixed_api_hosts": ["qianfan.baidubce.com", "appbuilder.baidu.com"],
                    "fixed_paths": ["/v2/ai_search/web_search", "/v2/ai_search/web_summary", "/v2/baike/lemma/get_list_by_title", "/v2/baike/lemma/get_content", "/v2/tools/baike/starmap/get_starmap_by_title", "/v2/tools/baike/starmap/get_starmap_by_id"],
                    "arbitrary_urls_allowed": False,
                    "arbitrary_hosts_allowed": False,
                    "arbitrary_paths_allowed": False,
                    "arbitrary_headers_allowed": False,
                    "client_supplied_credentials_allowed": False,
                    "redirects_allowed": False,
                    "automatic_pagination_allowed": False,
                    "automatic_retries_allowed": False,
                    "background_monitoring_allowed": False,
                    "cloud_resource_management_allowed": False,
                    "paid_fallback_authorized": False,
                    "generative_model_chat_allowed": False,
                    "generative_search_summary_allowed": True,
                    "model_calls_per_web_summary": 1,
                    "baike_structured_read_allowed": True,
                    "baike_video_allowed": False,
                    "nlp_operations_allowed": False,
                    "ocr_operations_allowed": False,
                    "image_recognition_operations_allowed": False,
                    "face_or_biometric_operations_allowed": False,
                    "identity_document_ocr_allowed": False,
                    "speech_operations_allowed": False,
                    "image_or_video_generation_allowed": False,
                    "write_operations_allowed": False,
                    "secret_values_exposed": False,
                    "direct_personal_identifiers_redacted": True,
                },
                "operations": rows,
            }
        ],
    }


def ticket_schema(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://github.com/a15280020511/evidence-data-center/api-center/baidu-ai-cloud/ticket.schema.json",
        "title": "baidu search and baike managed free read-only ticket",
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
            "provider": {"const": "baidu-ai-cloud"},
            "operation": {
                "type": "string",
                "enum": [row["operation_id"] for row in rows],
            },
            "objective": {"type": "string", "minLength": 1, "maxLength": 1000},
            "parameters": {"type": "object", "maxProperties": 4},
            "data_policy": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "classification",
                    "contains_personal_data",
                    "contains_confidential_data",
                ],
                "properties": {
                    "classification": {"const": "public"},
                    "contains_personal_data": {"const": False},
                    "contains_confidential_data": {"const": False},
                },
            },
            "acceptance": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "timeout_seconds",
                    "max_response_bytes",
                    "max_rows",
                ],
                "properties": {
                    "timeout_seconds": {
                        "type": "integer",
                        "minimum": 5,
                        "maximum": 90,
                    },
                    "max_response_bytes": {
                        "type": "integer",
                        "minimum": 1024,
                        "maximum": 2000000,
                    },
                    "max_rows": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                    },
                },
            },
        },
    }


def main() -> None:
    rows = operations()
    artifacts = {
        "provider-catalog.json": provider_catalog(rows),
        "ticket.schema.json": ticket_schema(rows),
        "free-quota-policy.json": quota_policy(),
    }
    for name, payload in artifacts.items():
        (HERE / name).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
