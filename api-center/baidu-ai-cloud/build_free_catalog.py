#!/usr/bin/env python3
"""Generate the frozen Baidu AI Cloud free-quota provider contracts."""
from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def text(max_length: int, min_length: int = 1) -> dict[str, Any]:
    return {"type": "string", "minLength": min_length, "maxLength": max_length}


def integer(minimum: int, maximum: int, default: int | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {
        "type": "integer",
        "minimum": minimum,
        "maximum": maximum,
    }
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
    rows: list[dict[str, Any]] = [
        operation(
            "catalog-capabilities",
            "读取本地百度智能云安全能力目录，不访问上游。",
            [],
            local=True,
        ),
        operation(
            "quota-policy",
            "读取本地免费额度、重置周期和付费风险策略，不访问上游。",
            [],
            local=True,
        ),
    ]
    rows.extend(
        [
            operation(
                "web-search",
                "百度AI搜索V2，返回实时公开网页摘要，不生成模型答案。",
                [
                    ("query", text(256), True),
                    ("top_k", integer(1, 20, 10), False),
                    ("edition", enum(["standard", "lite"], "standard"), False),
                    (
                        "recency",
                        enum(["week", "month", "semiyear", "year"]),
                        False,
                    ),
                ],
                origin="https://qianfan.baidubce.com",
                path="/v2/ai_search/web_search",
                method="POST",
                content_type="application/json",
                credential_mode="unified-api-key-bearer",
            ),
            operation(
                "intelligent-search",
                "智能搜索生成：实时检索并由指定模型总结，要求确认搜索和模型免费额度。",
                [
                    ("query", text(2000), True),
                    ("model", text(128), True),
                    ("top_k", integer(1, 20, 10), False),
                    ("instruction", text(4000), False),
                    ("free_quota_confirmed", {"const": True}, True),
                    ("paid_fallback_authorized", {"const": False}, True),
                ],
                origin="https://qianfan.baidubce.com",
                path="/v2/ai_search/chat/completions",
                method="POST",
                content_type="application/json",
                credential_mode="unified-api-key-bearer",
            ),
            operation(
                "deep-search",
                "深度搜索：拆分复杂问题并多次检索总结；最多3个子查询。",
                [
                    ("query", text(2000), True),
                    ("model", text(128), True),
                    ("top_k", integer(1, 20, 10), False),
                    ("instruction", text(4000), False),
                    ("free_quota_confirmed", {"const": True}, True),
                    ("paid_fallback_authorized", {"const": False}, True),
                    ("max_search_query_num", integer(1, 3, 3), False),
                ],
                origin="https://qianfan.baidubce.com",
                path="/v2/ai_search/chat/completions",
                method="POST",
                content_type="application/json",
                credential_mode="unified-api-key-bearer",
            ),
            operation(
                "web-summary",
                "智能搜索生成高性能版：一次实时搜索总结，要求确认每日免费额度。",
                [
                    ("query", text(2000), True),
                    ("top_k", integer(1, 20, 5), False),
                    ("instruction", text(4000), False),
                    ("free_quota_confirmed", {"const": True}, True),
                    ("paid_fallback_authorized", {"const": False}, True),
                ],
                origin="https://qianfan.baidubce.com",
                path="/v2/ai_search/web_summary",
                method="POST",
                content_type="application/json",
                credential_mode="unified-api-key-bearer",
            ),
            operation(
                "deep-research-lite",
                "深度研究Agent轻量版首轮：只发起一次研究并返回SSE事件。",
                [
                    ("query", text(4000), True),
                    ("free_quota_confirmed", {"const": True}, True),
                    ("paid_fallback_authorized", {"const": False}, True),
                ],
                origin="https://qianfan.baidubce.com",
                path="/v2/agent/deepresearch/run",
                method="POST",
                content_type="text/event-stream",
                credential_mode="unified-api-key-bearer",
            ),
        ]
    )
    nlp = [
        ("nlp-lexer", "中文词法分析。", "/rpc/2.0/nlp/v1/lexer", [("text", text(20000), True)]),
        ("nlp-sentiment", "情感倾向分析。", "/rpc/2.0/nlp/v1/sentiment_classify", [("text", text(2048), True)]),
        ("nlp-article-tags", "文章标签提取。", "/rpc/2.0/nlp/v1/keyword", [("title", text(80), True), ("content", text(60000), True)]),
        ("nlp-article-classify", "文章分类。", "/rpc/2.0/nlp/v1/topic", [("title", text(80), True), ("content", text(60000), True)]),
        ("nlp-entity-analysis", "实体识别与百科关联。", "/rpc/2.0/nlp/v1/entity_analysis", [("text", text(10000), True)]),
        ("nlp-short-similarity", "短文本相似度。", "/rpc/2.0/nlp/v2/simnet", [("text_1", text(1024), True), ("text_2", text(1024), True)]),
        ("nlp-dialogue-emotion", "对话情绪识别。", "/rpc/2.0/nlp/v1/emotion", [("text", text(2048), True)]),
        ("nlp-comment-opinion", "评论观点抽取。", "/rpc/2.0/nlp/v2/comment_tag", [("text", text(10240), True), ("type", integer(1, 13), False)]),
        ("nlp-text-correction", "文本纠错。", "/rpc/2.0/nlp/v1/ecnet", [("text", text(2000), True)]),
        ("nlp-text-correction-advanced", "文本纠错高级版。", "/rpc/2.0/nlp/v2/text_correction", [("text", text(2000), True)]),
        ("nlp-keyword-extraction", "关键词提取。", "/rpc/2.0/nlp/v1/txt_keywords_extraction", [("text", text(20000), True), ("num", integer(1, 20, 5), False)]),
        ("nlp-information-extraction", "文本信息提取。", "/rpc/2.0/nlp/v1/txt_monet", [("text", text(20000), True), ("query", text(1024), False)]),
        ("nlp-news-summary", "新闻摘要。", "/rpc/2.0/nlp/v1/news_summary", [("content", text(60000), True), ("max_summary_len", integer(50, 1000, 300), False)]),
        ("nlp-address", "地址识别与结构化。", "/rpc/2.0/nlp/v1/address", [("text", text(1000), True)]),
        ("nlp-article-title", "文章标题生成。", "/rpc/2.0/nlp/v1/titlepredictor", [("doc", text(10000), True)]),
    ]
    for op_id, description, path, parameters in nlp:
        rows.append(
            operation(
                op_id,
                description,
                parameters,
                origin="https://aip.baidubce.com",
                path=path,
                method="POST",
                content_type="application/json",
                credential_mode="unified-api-key-bearer",
            )
        )
    image_parameter = [
        ("image_base64", text(8_000_000, 16), True),
        (
            "language_type",
            enum(
                ["CHN_ENG", "ENG", "JAP", "KOR", "FRE", "SPA", "POR", "GER", "ITA", "RUS"],
                "CHN_ENG",
            ),
            False,
        ),
        ("detect_direction", {"type": "boolean", "default": False}, False),
    ]
    ocr = [
        ("ocr-general-basic", "通用文字识别标准版。", "/rest/2.0/ocr/v1/general_basic"),
        ("ocr-general", "通用文字识别标准含位置版。", "/rest/2.0/ocr/v1/general"),
        ("ocr-accurate-basic", "通用文字识别高精度版。", "/rest/2.0/ocr/v1/accurate_basic"),
        ("ocr-accurate", "通用文字识别高精度含位置版。", "/rest/2.0/ocr/v1/accurate"),
        ("ocr-office", "办公文档版面、表格、印章识别。", "/rest/2.0/ocr/v1/doc_analysis_office"),
        ("ocr-webimage", "复杂网络图片文字识别。", "/rest/2.0/ocr/v1/webimage"),
        ("ocr-webimage-location", "复杂网络图片文字识别含位置。", "/rest/2.0/ocr/v1/webimage_loc"),
        ("ocr-handwriting", "手写文字识别。", "/rest/2.0/ocr/v1/handwriting"),
        ("ocr-table-v2", "表格文字识别V2。", "/rest/2.0/ocr/v1/table"),
        ("ocr-seal", "印章文字与位置识别。", "/rest/2.0/ocr/v1/seal"),
        ("ocr-numbers", "数字识别。", "/rest/2.0/ocr/v1/numbers"),
        ("ocr-qrcode", "二维码与条形码识别。", "/rest/2.0/ocr/v1/qrcode"),
    ]
    for op_id, description, path in ocr:
        parameters = list(image_parameter)
        if op_id == "ocr-office":
            parameters.extend(
                [
                    ("layout_analysis", {"type": "boolean", "default": True}, False),
                    ("recg_tables", {"type": "boolean", "default": True}, False),
                    ("recog_seal", {"type": "boolean", "default": False}, False),
                ]
            )
        rows.append(
            operation(
                op_id,
                description,
                parameters,
                origin="https://aip.baidubce.com",
                path=path,
                method="POST",
                content_type="application/x-www-form-urlencoded",
                credential_mode="unified-api-key-bearer",
            )
        )
    image_recognition = [
        ("image-general-scene", "通用物体与场景识别。", "/rest/2.0/image-classify/v2/advanced_general"),
        ("image-object-detect", "图像单主体位置检测。", "/rest/2.0/image-classify/v1/object_detect"),
        ("image-animal", "动物识别。", "/rest/2.0/image-classify/v1/animal"),
        ("image-plant", "植物识别。", "/rest/2.0/image-classify/v1/plant"),
        ("image-logo", "品牌Logo识别，仅检索。", "/rest/2.0/image-classify/v2/logo"),
        ("image-landmark", "地标识别。", "/rest/2.0/image-classify/v1/landmark"),
        ("image-vehicle-detect", "车辆检测与计数。", "/rest/2.0/image-classify/v1/vehicle_detect"),
    ]
    for op_id, description, path in image_recognition:
        rows.append(
            operation(
                op_id,
                description,
                [("image_base64", text(8_000_000, 16), True)],
                origin="https://aip.baidubce.com",
                path=path,
                method="POST",
                content_type="application/x-www-form-urlencoded",
                credential_mode="unified-api-key-bearer",
            )
        )
    assert len(rows) == 41
    return rows


def quota_policy() -> dict[str, Any]:
    return {
        "schema_version": "baidu-ai-cloud-free-quota-policy-v1",
        "reviewed_at": "2026-08-03",
        "policy": {
            "free_only": True,
            "paid_fallback_authorized": False,
            "remaining_quota_api_available": False,
            "operator_action": "关闭或不启用按量后付费；执行高成本或一次性额度操作前核对控制台剩余额度。",
            "quota_exhaustion_behavior": "不自动重试或切换接口；若控制台启用后付费，上游仍可能计费。",
        },
        "families": [
            {
                "family": "baidu-ai-search",
                "quota": "最新总价页为每日共享免费池；端点页另载每月1500次按天发放，采用更保守口径。",
                "reset": "daily",
                "notes": "智能搜索生成需额外模型额度；深搜索仓库限制最多3个子查询。",
            },
            {
                "family": "deep-research-agent",
                "quota": "Lite免费50次",
                "reset": "one_time_or_unspecified",
            },
            {
                "family": "nlp-personal",
                "quota": "不同API为总量10、200、500或50万次",
                "reset": "one_time_365_days",
            },
            {
                "family": "nlp-enterprise",
                "quota": "部分接口为每日5万或50万次",
                "reset": "daily_during_365_day_validity",
            },
            {
                "family": "ocr-monthly",
                "quota": "个人通常500或1000次/月；企业通常1000或2000次/月",
                "reset": "natural_month",
            },
            {
                "family": "ocr-one-time",
                "quota": "个人通常500次；企业通常1000次",
                "reset": "one_time_or_unspecified",
            },
            {
                "family": "image-recognition",
                "quota": "多数能力为累计赠送1000至10000次，企业更多",
                "reset": "one_time_12_months_or_unspecified",
            },
            {
                "family": "new-user-model-tokens",
                "quota": "指定模型各100万tokens",
                "reset": "one_time_3_months",
            },
        ],
        "excluded": [
            {"family": "face-and-biometric", "reason": "高敏感生物识别。"},
            {"family": "identity-and-financial-document-ocr", "reason": "直接身份和金融标识。"},
            {"family": "speech-and-voice", "reason": "声纹、隐私及异步长任务风险。"},
            {"family": "image-video-generation", "reason": "生成内容且可能产生模型费用。"},
            {"family": "write-and-cloud-management", "reason": "不属于只读公开情报。"},
        ],
    }


def provider_catalog(rows: list[dict[str, Any]]) -> dict[str, Any]:
    paths = [
        str(row["execution"]["path_template"])
        for row in rows
        if not row["execution"]["local"]
    ]
    return {
        "schema_version": "baidu-ai-cloud-provider-catalog-v3",
        "secret_values_exposed": False,
        "replaced_legacy_connectors": [],
        "providers": [
            {
                "provider_id": "baidu-ai-cloud",
                "display_name": "百度智能云免费情报能力",
                "description": "统一API Key访问受控百度搜索、研究、NLP、公共文档OCR和非生物图像识别。",
                "enabled": True,
                "ticket_prefix": "[intel-baidu-ai]",
                "required_secret_environment_variable": "BAIDU_AI_CLOUD_API_KEY",
                "required_secret_environment_variables": ["BAIDU_AI_CLOUD_API_KEY"],
                "credential_matrix": {
                    "all-business-operations": ["BAIDU_AI_CLOUD_API_KEY"]
                },
                "catalog_policy": "开放41项有明确免费额度且适合情报中心的受控只读能力。",
                "execution_policy": "每票据一个操作和一次固定HTTPS请求；高成本操作必须确认免费额度，禁止付费兜底。",
                "official_origins": [
                    "https://qianfan.baidubce.com",
                    "https://aip.baidubce.com",
                ],
                "limits": {
                    "requests_per_ticket_max": 1,
                    "provider_concurrency_max": 1,
                    "transient_retry_max": 0,
                    "timeout_seconds_max": 180,
                    "max_response_bytes": 10_000_000,
                    "max_search_results": 20,
                    "max_deep_search_queries": 3,
                    "max_text_characters": 60_000,
                    "max_image_base64_characters": 8_000_000,
                    "fixed_api_hosts": [
                        "qianfan.baidubce.com",
                        "aip.baidubce.com",
                    ],
                    "fixed_paths": paths,
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
        "title": "baidu ai cloud managed free-quota read-only ticket",
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
            "parameters": {"type": "object", "maxProperties": 10},
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
                        "maximum": 180,
                    },
                    "max_response_bytes": {
                        "type": "integer",
                        "minimum": 1024,
                        "maximum": 10_000_000,
                    },
                    "max_rows": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 1000,
                    },
                },
            },
        },
    }


def write_json(path: Path, payload: Any, *, compact: bool = False) -> None:
    if compact:
        content = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        )
    else:
        content = json.dumps(payload, ensure_ascii=False, indent=2)
    path.write_text(content + "\n", encoding="utf-8")


def main() -> int:
    rows = operations()
    write_json(HERE / "provider-catalog.json", provider_catalog(rows), compact=True)
    write_json(HERE / "ticket.schema.json", ticket_schema(rows))
    write_json(HERE / "free-quota-policy.json", quota_policy())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
