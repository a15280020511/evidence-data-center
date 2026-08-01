#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path('.')
CENTER = ROOT / 'api-center'
GAPUP = CENTER / 'gapup-mcp'
DISCOVERY = ROOT / 'gapup-discovery' / 'tools-list.json'

DENIED_OPERATIONS = {
    'crm_connector', 'webhooks_manage', 'job_result', 'workflow_orchestrator',
    'tool_recommend', 'realtime_data_streams',
    'competitive_deep_dive_async', 'competitive_deep_dive_result',
    'kyc_screener_batch', 'kyc_screener_batch_result',
    'ai_governance_full_report_async', 'ai_governance_full_report_result',
    'patent_landscape_async', 'patent_landscape_result',
    'kyc_screener', 'candidate_screening_ranking', 'talent_intelligence',
    'talent_contract_risk_mapper', 'talent_legal_dashboard',
    'talent_litigation_exposure', 'talent_poaching_risk',
    'recruiting_architect', 'onboarding_salaries', 'comp_benchmark_geo_delta',
    'executive_comp_peer_benchmark', 'global_salary_inflation_adjuster',
    'anti_demissions_hr', 'comp_plan_architect', 'diversity_inclusion_metrics',
    'enps_auto', 'ld_architect', 'hr_benefits_esg_aligner',
    'sabbatical_policy_comparator', 'ip_employee_invention_tracker',
    'attack_surface_monitor', 'pentest_scope_estimator',
    'incident_response_evidence_collector', 'safety_violation_incident_logger',
    'crypto_wallet_intel', 'usdc_x402_payments_intel',
    'x402_liquidity_monitor', 'x402_payment_flow_analyzer',
    'x402_payment_fraud_detector', 'dpdp_consent_artifact_generator',
    'lgpd_data_subject_rights_automator', 'clinical_evidence_briefer',
    'clinical_pharma_intel', 'contract_risk_scanner',
    'ip_contract_clause_extractor', 'legal_clause_extractor',
    'email_domain_health_check', 'sanctions_screener_multi', 'fraud_detector',
    'affiliate_fraud_clickstream_detector',
    'social_influencer_fake_follower_detector', 'jailbreak_attempt_detector',
    'ugc_moderation_classifier', 'adversarial_input_stress_tester',
    'bias_amplification_tracker', 'hallucination_confidence_meter',
    'model_behavior_drift_monitor', 'model_safety_certification_checker',
    'safety_guardrail_breach_analyzer',
}

FORBIDDEN_PARAMETER_NAMES = {
    'async', 'webhook', 'webhook_url', 'callback', 'callback_url', 'job_id',
    'payment', 'x_payment', 'x-payment', 'wallet', 'api_key', 'apikey',
    'token', 'secret', 'authorization', 'cookie', 'headers', 'proxy',
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n',
        encoding='utf-8',
    )


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(',', ':'),
            allow_nan=False,
        ).encode('utf-8')
    ).hexdigest()


def sanitize_schema(value: Any, *, property_name: str = '') -> Any:
    if isinstance(value, list):
        return [sanitize_schema(item, property_name=property_name) for item in value]
    if not isinstance(value, dict):
        return value
    result = {str(k): sanitize_schema(v, property_name=str(k)) for k, v in value.items()}
    schema_type = result.get('type')
    if schema_type == 'object' or 'properties' in result:
        properties = dict(result.get('properties') or {})
        forbidden = {item.replace('-', '_') for item in FORBIDDEN_PARAMETER_NAMES}
        for key in list(properties):
            if key.lower().replace('-', '_') in forbidden:
                properties.pop(key, None)
        result['properties'] = properties
        result['additionalProperties'] = False
        result['maxProperties'] = min(int(result.get('maxProperties', 100)), 100)
        required = [item for item in result.get('required', []) if item in properties]
        if required:
            result['required'] = required
        else:
            result.pop('required', None)
    if schema_type == 'string':
        max_length = 2048 if property_name.lower() in {'url', 'website', 'source_url'} else 20000
        result['maxLength'] = min(int(result.get('maxLength', max_length)), max_length)
    if schema_type == 'array':
        result['maxItems'] = min(int(result.get('maxItems', 100)), 100)
    return result


def rename_center_terms() -> None:
    candidates = [
        ROOT / 'README.md',
        ROOT / 'OBSERVABILITY.md',
        ROOT / 'OPERATIONS_RUNBOOK.md',
        CENTER / 'README.md',
        CENTER / 'CAPABILITY_MAXIMIZATION.md',
        CENTER / 'SECRET_ISOLATION_POLICY.md',
        CENTER / 'build_catalog.py',
    ]
    replacements = (
        ('独立外部 API 接入中心', '独立情报中心'),
        ('API 接入中心', '情报中心'),
        ('API 中心', '情报中心'),
        ('API中心', '情报中心'),
    )
    for path in candidates:
        if not path.is_file():
            continue
        text = path.read_text(encoding='utf-8')
        for old, new in replacements:
            text = text.replace(old, new)
        path.write_text(text, encoding='utf-8')

    root_readme = ROOT / 'README.md'
    text = root_readme.read_text(encoding='utf-8')
    if '正式对外名称：`情报中心`' not in text:
        anchor = '本仓库是正式独立的数据证据中心；拆仓来源和固定提交仅记录在迁移证据文件中，不参与日常运行。\n'
        addition = (
            anchor
            + '\n正式对外名称：`情报中心`（Intelligence Center）。技术目录 `api-center/` '
              '作为兼容路径继续保留，不代表对外名称。\n'
        )
        if anchor not in text:
            raise RuntimeError('root README rename anchor missing')
        root_readme.write_text(text.replace(anchor, addition, 1), encoding='utf-8')


def build_provider(discovery: dict[str, Any]) -> tuple[list[str], list[str]]:
    tools = discovery.get('tools')
    if not isinstance(tools, list) or len(tools) != 271:
        raise RuntimeError(f'expected 271 Gapup tools, received {len(tools or [])}')
    names = [str(row.get('name') or '') for row in tools]
    if len(names) != len(set(names)) or any(not name for name in names):
        raise RuntimeError('Gapup discovery contains empty or duplicate names')
    if not DENIED_OPERATIONS <= set(names):
        raise RuntimeError(
            f'Gapup denylist no longer matches official catalog: '
            f'{sorted(DENIED_OPERATIONS - set(names))}'
        )

    allowed_tools: list[dict[str, Any]] = []
    blocked_tools: list[dict[str, Any]] = []
    for tool in tools:
        name = str(tool['name'])
        annotations = dict(tool.get('annotations') or {})
        reason = ''
        if annotations.get('readOnlyHint') is False:
            reason = 'official readOnlyHint=false'
        elif name in DENIED_OPERATIONS:
            reason = 'local maximum-safe-readonly policy'
        if reason:
            blocked_tools.append({'name': name, 'reason': reason})
            continue
        schema = sanitize_schema(copy.deepcopy(tool.get('inputSchema') or {}))
        if not isinstance(schema, dict):
            raise RuntimeError(f'invalid input schema for {name}')
        schema.setdefault('type', 'object')
        schema.setdefault('properties', {})
        schema['additionalProperties'] = False
        allowed_tools.append(
            {
                'operation_id': name,
                'description': str(tool.get('description') or '').strip(),
                'parameters': list(schema.get('properties') or {}),
                'parameter_schema': schema,
                'execution': {
                    'local': False,
                    'mcp_method': 'tools/call',
                    'mcp_tool_name': name,
                    'force_async_false': 'async'
                    in (tool.get('inputSchema') or {}).get('properties', {}),
                },
                'result_contract': {
                    'provider': 'gapup-mcp',
                    'official_endpoint': 'https://mcp.gapup.io/mcp',
                    'protocol': 'MCP Streamable HTTP JSON-RPC 2.0',
                    'read_only': True,
                    'credential_mode': 'x-api-key-backend-only',
                    'billable_or_quota_counted': True,
                    'automatic_x402_payment_allowed': False,
                    'upstream_llm_may_be_used': True,
                },
                'discovery_policy': {
                    'official_annotations': annotations,
                    'official_schema_sha256': canonical_sha(tool.get('inputSchema') or {}),
                    'snapshot_locked': True,
                },
            }
        )

    allowed_names = sorted(row['operation_id'] for row in allowed_tools)
    blocked_names = sorted(row['name'] for row in blocked_tools)
    if len(allowed_names) != 208 or len(blocked_names) != 63:
        raise RuntimeError(
            f'Gapup policy count changed: allowed={len(allowed_names)}, '
            f'blocked={len(blocked_names)}'
        )

    local_operation = {
        'operation_id': 'catalog-capabilities',
        'description': '读取本地固定 Gapup MCP 安全能力目录，不访问上游、不消耗额度。',
        'parameters': [],
        'parameter_schema': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {},
            'maxProperties': 0,
        },
        'execution': {'local': True, 'mcp_method': 'LOCAL'},
        'result_contract': {
            'provider': 'gapup-mcp',
            'read_only': True,
            'credential_mode': 'none',
            'billable_or_quota_counted': False,
        },
    }
    operations = [local_operation, *sorted(allowed_tools, key=lambda row: row['operation_id'])]
    snapshot = {
        'schema_version': 'gapup-mcp-readonly-snapshot-v1',
        'official_repository': 'getgapup/gapup-mcp-public',
        'official_endpoint': 'https://mcp.gapup.io/mcp',
        'official_tool_count': 271,
        'allowed_tool_count': 208,
        'blocked_tool_count': 63,
        'allowed_tool_names': allowed_names,
        'blocked_tools': sorted(blocked_tools, key=lambda row: row['name']),
        'official_tools_sha256': canonical_sha(tools),
        'secret_values_exposed': False,
    }
    write_json(GAPUP / 'readonly-tools.snapshot.json', snapshot)
    snapshot_sha = hashlib.sha256(
        (GAPUP / 'readonly-tools.snapshot.json').read_bytes()
    ).hexdigest()

    provider_catalog = {
        'schema_version': 'gapup-mcp-provider-catalog-v1',
        'secret_values_exposed': False,
        'replaced_legacy_connectors': [],
        'providers': [
            {
                'provider_id': 'gapup-mcp',
                'display_name': 'Gapup MCP 公共商业情报',
                'description': (
                    '通过Gapup官方MCP读取公共商业、市场、贸易、研究、公司、宏观、'
                    '内容和合规情报；仅开放208项固定只读工具。'
                ),
                'enabled': True,
                'ticket_prefix': '[intel-gapup]',
                'required_secret_environment_variable': 'GAPUP_API_KEY',
                'catalog_policy': (
                    '官方271项工具经实时tools/list发现后固化；开放208项只读、公开、'
                    '非个人、非机密工具，阻断63项写入、异步、个人筛查、主动安全、'
                    '支付、医疗和敏感合同工具。'
                ),
                'execution_policy': (
                    '每张票据只允许一次固定tools/call；API Key仅由Repository Secret注入；'
                    '强制同步执行；拒绝任意工具名、任意JSON-RPC方法、回调、Webhook、'
                    '后台任务、x402自动支付、个人数据、机密数据和私网URL。'
                ),
                'official_origin': 'https://mcp.gapup.io',
                'official_endpoint': 'https://mcp.gapup.io/mcp',
                'mcp_protocol_version': '2025-06-18-compatible-streamable-http',
                'readonly_tool_snapshot_file': 'gapup-mcp/readonly-tools.snapshot.json',
                'readonly_tool_snapshot_sha256': snapshot_sha,
                'discovered_readonly_tool_count': 208,
                'limits': {
                    'requests_per_ticket_max': 1,
                    'timeout_seconds_max': 120,
                    'max_request_bytes': 1000000,
                    'max_response_bytes': 20000000,
                    'fixed_api_host': 'mcp.gapup.io',
                    'official_tool_count': 271,
                    'fixed_mcp_tool_count': 208,
                    'blocked_tool_count': 63,
                    'provider_concurrency_max': 1,
                    'transient_retry_max': 1,
                    'arbitrary_jsonrpc_methods_allowed': False,
                    'arbitrary_mcp_tool_names_allowed': False,
                    'client_supplied_credentials_allowed': False,
                    'redirects_allowed': False,
                    'async_jobs_allowed': False,
                    'job_polling_allowed': False,
                    'webhooks_allowed': False,
                    'background_monitoring_allowed': False,
                    'automatic_x402_payment_allowed': False,
                    'wallet_or_payment_credentials_allowed': False,
                    'write_operations_allowed': False,
                    'trading_or_order_execution_allowed': False,
                    'personal_data_allowed': False,
                    'confidential_data_allowed': False,
                    'public_https_url_inputs_allowed': True,
                    'private_network_url_inputs_allowed': False,
                    'secret_values_exposed': False,
                    'upstream_may_use_llm': True,
                    'upstream_calls_are_billable_or_quota_counted': True,
                    'free_tier_calls_per_month_documented': 100,
                },
                'operations': operations,
            }
        ],
    }
    write_json(GAPUP / 'provider-catalog.json', provider_catalog)

    ticket_schema = {
        '$schema': 'https://json-schema.org/draft/2020-12/schema',
        '$id': 'https://github.com/a15280020511/evidence-data-center/api-center/gapup-mcp/ticket.schema.json',
        'title': 'gapup-mcp managed public intelligence ticket',
        'type': 'object',
        'additionalProperties': False,
        'required': [
            'task_id', 'provider', 'operation', 'objective', 'parameters',
            'data_policy', 'payment_policy', 'acceptance',
        ],
        'properties': {
            'task_id': {
                'type': 'string',
                'pattern': '^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$',
            },
            'provider': {'const': 'gapup-mcp'},
            'operation': {'type': 'string', 'enum': ['catalog-capabilities', *allowed_names]},
            'objective': {'type': 'string', 'minLength': 1, 'maxLength': 1000},
            'parameters': {'type': 'object', 'maxProperties': 100},
            'data_policy': {
                'type': 'object',
                'additionalProperties': False,
                'required': [
                    'classification', 'contains_personal_data',
                    'contains_confidential_data',
                ],
                'properties': {
                    'classification': {'const': 'public'},
                    'contains_personal_data': {'const': False},
                    'contains_confidential_data': {'const': False},
                },
            },
            'payment_policy': {
                'type': 'object',
                'additionalProperties': False,
                'required': ['automatic_x402_payment_authorized'],
                'properties': {
                    'automatic_x402_payment_authorized': {'const': False},
                },
            },
            'acceptance': {
                'type': 'object',
                'additionalProperties': False,
                'required': ['timeout_seconds', 'max_response_bytes'],
                'properties': {
                    'timeout_seconds': {'type': 'integer', 'minimum': 5, 'maximum': 120},
                    'max_response_bytes': {
                        'type': 'integer', 'minimum': 1024, 'maximum': 20000000,
                    },
                },
            },
        },
    }
    write_json(GAPUP / 'ticket.schema.json', ticket_schema)
    return allowed_names, blocked_names


def write_runtime() -> None:
    runtime = r'''#!/usr/bin/env python3
"""Bounded synchronous client for Gapup MCP public intelligence tools."""
from __future__ import annotations

import ipaddress
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit

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
MCP_URL = "https://mcp.gapup.io/mcp"
MCP_HOST = "mcp.gapup.io"
API_KEY_ENV = "GAPUP_API_KEY"
MAX_REQUEST_BYTES = 1_000_000
EMAIL_RE = re.compile(r"(?i)(?<![A-Z0-9._%+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![A-Z0-9._%+-])")
SECRET_RE = re.compile(r"(?i)(?:bearer\s+[A-Za-z0-9._~+/=-]{8,}|\b(?:gpk|sk|api)[_-][A-Za-z0-9_-]{8,})")
FORBIDDEN_KEYS = {
    "async", "webhook", "webhook_url", "callback", "callback_url", "job_id",
    "payment", "x_payment", "x-payment", "wallet", "api_key", "apikey",
    "token", "secret", "authorization", "cookie", "headers", "proxy",
}


class GapupMcpError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def api_key() -> str:
    value = str(os.getenv(API_KEY_ENV) or "").strip()
    if not value:
        raise GapupMcpError("GAPUP_API_KEY_MISSING", f"missing repository Secret {API_KEY_ENV}")
    if not value.startswith("gpk_"):
        raise GapupMcpError("GAPUP_API_KEY_INVALID", f"invalid repository Secret {API_KEY_ENV} prefix")
    if not 8 <= len(value) <= 512:
        raise GapupMcpError("GAPUP_API_KEY_INVALID", f"invalid repository Secret {API_KEY_ENV} length")
    if any(ord(char) < 0x21 or ord(char) > 0x7E for char in value):
        raise GapupMcpError("GAPUP_API_KEY_INVALID", f"invalid repository Secret {API_KEY_ENV} characters")
    return value


def operation_row(operation: str) -> Mapping[str, Any]:
    row = operation_map(CATALOG_PATH).get(operation)
    if row is None:
        raise ValueError(f"unsupported Gapup MCP operation: {operation}")
    return row


def validate_public_https_url(value: str) -> None:
    parsed = urlsplit(value)
    if parsed.scheme.lower() != "https":
        raise ValueError("URL inputs must use https")
    if not parsed.hostname:
        raise ValueError("URL input requires a hostname")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URL input must not contain credentials")
    if parsed.port not in (None, 443):
        raise ValueError("URL input must use the default HTTPS port")
    host = parsed.hostname.rstrip(".").lower()
    if host in {"localhost", "localhost.localdomain"}:
        raise ValueError("localhost URL inputs are prohibited")
    if host.endswith((".localhost", ".local", ".internal", ".home", ".lan")):
        raise ValueError("private or local URL hostnames are prohibited")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and (
        address.is_private or address.is_loopback or address.is_link_local
        or address.is_multicast or address.is_reserved or address.is_unspecified
    ):
        raise ValueError("private, loopback, link-local, reserved, or multicast IP URLs are prohibited")


def validate_public_parameters(value: Any, *, depth: int = 0, key_name: str = "") -> None:
    if depth > 20:
        raise ValueError("request body nesting exceeds 20 levels")
    normalized = key_name.lower().replace("-", "_")
    if normalized in {item.replace("-", "_") for item in FORBIDDEN_KEYS}:
        raise ValueError(f"parameter {key_name!r} is prohibited")
    if value is None or isinstance(value, (bool, int, float)):
        return
    if isinstance(value, str):
        if EMAIL_RE.search(value):
            raise ValueError("email addresses and personal identifiers are prohibited")
        if SECRET_RE.search(value):
            raise ValueError("credential-like values are prohibited")
        if value.lower().startswith(("http://", "https://")):
            validate_public_https_url(value)
        return
    if isinstance(value, Mapping):
        if len(value) > 100:
            raise ValueError("request object has too many keys")
        for key, item in value.items():
            if not isinstance(key, str) or len(key) > 128:
                raise ValueError("request object keys must be short strings")
            validate_public_parameters(item, depth=depth + 1, key_name=key)
        return
    if isinstance(value, list):
        if len(value) > 100:
            raise ValueError("request array has too many items")
        for item in value:
            validate_public_parameters(item, depth=depth + 1, key_name=key_name)
        return
    raise ValueError(f"unsupported request value type: {type(value).__name__}")


def parse_mcp_payload(raw: bytes, content_type: str) -> Any:
    if not raw:
        raise GapupMcpError("GAPUP_MCP_EMPTY_RESPONSE", "upstream returned an empty response")
    try:
        text = raw.decode("utf-8")
        if "text/event-stream" not in content_type.lower() and not text.lstrip().startswith(("event:", "data:")):
            return json.loads(text)
        events, data_lines = [], []
        for line in text.splitlines() + [""]:
            if line.startswith("data:"):
                data_lines.append(line[5:].lstrip())
            elif not line.strip() and data_lines:
                data = "\n".join(data_lines)
                data_lines = []
                if data and data != "[DONE]":
                    events.append(json.loads(data))
        if not events:
            raise ValueError("empty SSE response")
        return events[-1]
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise GapupMcpError("GAPUP_MCP_INVALID_RESPONSE", "upstream returned invalid MCP content") from exc


def scrub_secret(value: Any, secret: str) -> Any:
    if isinstance(value, str):
        return value.replace(secret, "[REDACTED]") if secret else value
    if isinstance(value, list):
        return [scrub_secret(item, secret) for item in value]
    if isinstance(value, Mapping):
        return {str(key): scrub_secret(item, secret) for key, item in value.items()}
    return value


def query_gapup(operation: str, parameters: Mapping[str, Any], *, timeout: int, max_bytes: int) -> tuple[Any, dict[str, Any]]:
    row = operation_row(operation)
    execution = dict(row.get("execution") or {})
    if execution.get("local") is True:
        raise ValueError("local operations must not call query_gapup")
    if execution.get("mcp_method") != "tools/call" or execution.get("mcp_tool_name") != operation:
        raise ValueError("provider catalog MCP route does not match operation")
    validate_public_parameters(parameters)
    arguments = dict(parameters)
    if execution.get("force_async_false") is True:
        arguments["async"] = False
    request_payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": 1,
        "params": {"name": operation, "arguments": arguments},
    }
    encoded = json.dumps(request_payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_REQUEST_BYTES:
        raise ValueError(f"request body exceeds {MAX_REQUEST_BYTES} bytes")
    secret = api_key()
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "x-api-key": secret,
        "User-Agent": "evidence-intelligence-center-gapup-mcp/1",
    }
    attempts = 0
    while attempts < 2:
        attempts += 1
        try:
            response = requests.post(
                MCP_URL,
                data=encoded,
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
            raise GapupMcpError("GAPUP_MCP_CONNECTION_FAILED", type(exc).__name__, retryable=True) from exc
        if len(raw) > max_bytes:
            raise GapupMcpError("GAPUP_MCP_RESPONSE_TOO_LARGE", "upstream response exceeded max_response_bytes")
        if response.is_redirect:
            raise GapupMcpError("GAPUP_MCP_REDIRECT_REJECTED", f"upstream attempted HTTP {response.status_code} redirect")
        if response.status_code in {401, 403}:
            raise GapupMcpError("GAPUP_MCP_CREDENTIAL_DENIED", f"upstream HTTP {response.status_code}")
        if response.status_code == 402:
            raise GapupMcpError(
                "GAPUP_MCP_PAYMENT_REQUIRED",
                "upstream requested x402 payment; automatic payment is prohibited",
            )
        if response.status_code == 429:
            raise GapupMcpError("GAPUP_MCP_RATE_LIMITED", "upstream HTTP 429", retryable=True)
        if response.status_code >= 500:
            if attempts < 2:
                time.sleep(1.0)
                continue
            raise GapupMcpError("GAPUP_MCP_HTTP_TRANSIENT", f"upstream HTTP {response.status_code}", retryable=True)
        if not 200 <= response.status_code < 300:
            raise GapupMcpError("GAPUP_MCP_HTTP_ERROR", f"upstream HTTP {response.status_code}")
        content_type = str(response.headers.get("Content-Type") or "")
        parsed = parse_mcp_payload(raw, content_type)
        if isinstance(parsed, Mapping) and parsed.get("error"):
            detail = json.dumps(parsed["error"], ensure_ascii=False)[:2000]
            raise GapupMcpError("GAPUP_MCP_JSONRPC_ERROR", f"upstream JSON-RPC error: {detail}")
        result = parsed.get("result") if isinstance(parsed, Mapping) else None
        if not isinstance(result, Mapping):
            raise GapupMcpError("GAPUP_MCP_RESULT_INVALID", "upstream response did not contain result")
        if result.get("isError") is True:
            raise GapupMcpError("GAPUP_MCP_TOOL_ERROR", "upstream tool returned isError=true")
        content = result.get("content")
        if not isinstance(content, list) or not content:
            raise GapupMcpError("GAPUP_MCP_CONTENT_MISSING", "upstream result did not contain content")
        deliverables = []
        for item in content:
            if not isinstance(item, Mapping):
                continue
            if item.get("type") == "text" and isinstance(item.get("text"), str):
                text = item["text"]
                try:
                    deliverables.append(json.loads(text))
                except json.JSONDecodeError:
                    deliverables.append(text)
            else:
                deliverables.append(dict(item))
        if not deliverables:
            raise GapupMcpError("GAPUP_MCP_CONTENT_INVALID", "upstream content was not usable")
        return scrub_secret(deliverables[0] if len(deliverables) == 1 else deliverables, secret), {
            "request_origin": MCP_HOST,
            "request_path": "/mcp",
            "http_method": "POST",
            "mcp_method": "tools/call",
            "mcp_tool_name": operation,
            "credential_mode": "x-api-key-backend-only",
            "credential_environment_variable": API_KEY_ENV,
            "secret_value_exposed": False,
            "redirects_allowed": False,
            "automatic_x402_payment_allowed": False,
            "async_forced_false": bool(execution.get("force_async_false")),
            "request_bytes": len(encoded),
            "response_bytes": len(raw),
            "http_status": response.status_code,
            "content_type": content_type,
            "attempts": attempts,
            "billable_or_quota_counted": True,
        }
    raise AssertionError("unreachable")


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(acceptance.get("timeout_seconds"), default=60, minimum=5, maximum=120, name="timeout_seconds")
    max_bytes = bounded_int(acceptance.get("max_response_bytes"), default=10_000_000, minimum=1024, maximum=20_000_000, name="max_response_bytes")
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_GAPUP_MCP_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "api_origin": MCP_HOST,
        "credential_mode": "x-api-key-backend-only",
        "secret_values_exposed": False,
        "one_request_per_ticket": True,
        "automatic_x402_payment_allowed": False,
        "async_jobs_allowed": False,
    }
    try:
        if operation == "catalog-capabilities":
            snapshot = {"provider": provider_row(CATALOG_PATH)}
            metadata["credential_mode"] = "none"
        else:
            payload, request_metadata = query_gapup(operation, parameters, timeout=timeout, max_bytes=max_bytes)
            metadata.update(request_metadata)
            metadata["upstream_called"] = True
            snapshot = {"provider": "gapup-mcp", "operation": operation, "data": payload}
        status = "INTEL_GAPUP_MCP_COMPLETED"
    except Exception as exc:
        message = str(exc)
        secret = str(os.getenv(API_KEY_ENV) or "")
        if secret:
            message = message.replace(secret, "[REDACTED]")
        failure = {
            "type": type(exc).__name__,
            "code": getattr(exc, "code", "GAPUP_MCP_EXECUTION_ERROR"),
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
        schema_prefix="gapup-mcp",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-gapup]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="gapup-mcp-ticket-status-v1",
            display_name="Gapup MCP 情报",
        )
    )
'''
    (GAPUP / 'gapup_mcp_task.py').write_text(runtime, encoding='utf-8')


def write_tests(allowed_names: list[str], blocked_names: list[str]) -> None:
    test_source = f'''from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("gapup_mcp_task", ROOT / "gapup_mcp_task.py")
assert SPEC and SPEC.loader
task = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(task)

BLOCKED = {blocked_names!r}


class FakeRaw:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
    def read(self, size: int, decode_content: bool = True) -> bytes:
        return self.payload[:size]


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200, content_type: str = "application/json") -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.raw = FakeRaw(raw)
        self.status_code = status_code
        self.headers = {{"Content-Type": content_type}}
        self.is_redirect = False


class GapupMcpTests(unittest.TestCase):
    def ticket(self, operation="catalog-capabilities", parameters=None):
        return {{
            "task_id": "gapup-test-001",
            "provider": "gapup-mcp",
            "operation": operation,
            "objective": "test bounded Gapup intelligence provider",
            "parameters": parameters or {{}},
            "data_policy": {{
                "classification": "public",
                "contains_personal_data": False,
                "contains_confidential_data": False,
            }},
            "payment_policy": {{"automatic_x402_payment_authorized": False}},
            "acceptance": {{"timeout_seconds": 30, "max_response_bytes": 1_000_000}},
        }}

    def test_catalog_is_fixed_and_excludes_blocked_tools(self):
        catalog = json.loads((ROOT / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        ids = {{row["operation_id"] for row in provider["operations"]}}
        self.assertEqual(provider["provider_id"], "gapup-mcp")
        self.assertEqual(provider["required_secret_environment_variable"], "GAPUP_API_KEY")
        self.assertEqual(len(ids), 209)
        self.assertEqual(provider["limits"]["fixed_mcp_tool_count"], 208)
        self.assertEqual(provider["limits"]["official_tool_count"], 271)
        self.assertFalse(set(BLOCKED) & ids)
        self.assertIn("china_market_data", ids)
        self.assertIn("competitive_deep_dive", ids)
        self.assertIn("research_paper_qa", ids)
        self.assertFalse(provider["limits"]["automatic_x402_payment_allowed"])
        self.assertFalse(provider["limits"]["async_jobs_allowed"])
        self.assertFalse(provider["limits"]["write_operations_allowed"])

    def test_ticket_schema_rejects_every_blocked_operation(self):
        for operation in BLOCKED:
            with self.subTest(operation=operation):
                with self.assertRaises(ValueError):
                    task.validate_ticket(self.ticket(operation, {{}}), schema_path=task.SCHEMA_PATH, catalog_path=task.CATALOG_PATH)

    def test_key_is_backend_only_and_prefixed(self):
        with patch.dict(os.environ, {{"GAPUP_API_KEY": "gpk_test_key_12345"}}, clear=False):
            self.assertEqual(task.api_key(), "gpk_test_key_12345")
        with patch.dict(os.environ, {{"GAPUP_API_KEY": "wrong"}}, clear=False):
            with self.assertRaises(task.GapupMcpError):
                task.api_key()

    def test_parameter_guard_blocks_private_urls_personal_data_and_control_fields(self):
        for payload in (
            {{"url": "http://example.com"}},
            {{"url": "https://127.0.0.1/a"}},
            {{"url": "https://169.254.169.254/latest"}},
            {{"contact": "analyst@example.com"}},
            {{"api_key": "gpk_secret_123456"}},
            {{"async": True}},
            {{"callback_url": "https://example.com/callback"}},
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    task.validate_public_parameters(payload)
        task.validate_public_parameters({{"url": "https://example.com/public", "company": "Yonghui Superstores"}})

    def test_local_catalog_needs_no_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            ticket_path = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket_path.write_text(json.dumps(self.ticket()), encoding="utf-8")
            self.assertEqual(task.execute(ticket_path, out), 0)
            diagnostics = json.loads((out / "diagnostics.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostics["status"], "INTEL_GAPUP_MCP_COMPLETED")
            self.assertFalse(diagnostics["metadata"]["upstream_called"])

    def test_mocked_tool_call_succeeds_and_never_persists_key(self):
        response = {{
            "jsonrpc": "2.0",
            "id": 1,
            "result": {{"content": [{{"type": "text", "text": json.dumps({{"classification": "Retail Trade"}})}}]}},
        }}
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ, {{"GAPUP_API_KEY": "gpk_test_key_12345"}}, clear=False
        ), patch.object(task.requests, "post", return_value=FakeResponse(response)):
            ticket_path = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket_path.write_text(
                json.dumps(self.ticket("industry_classifier_naics_sic", {{"company_description": "public supermarket retailer", "company_name": "Yonghui Superstores"}})),
                encoding="utf-8",
            )
            self.assertEqual(task.execute(ticket_path, out), 0)
            diagnostics = json.loads((out / "diagnostics.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostics["status"], "INTEL_GAPUP_MCP_COMPLETED")
            self.assertTrue(diagnostics["metadata"]["upstream_called"])
            for path in out.iterdir():
                if path.is_file():
                    self.assertNotIn(b"gpk_test_key_12345", path.read_bytes())

    def test_x402_payment_is_fail_closed(self):
        with patch.dict(os.environ, {{"GAPUP_API_KEY": "gpk_test_key_12345"}}, clear=False), patch.object(
            task.requests, "post", return_value=FakeResponse({{"error": "payment_required"}}, status_code=402)
        ):
            with self.assertRaises(task.GapupMcpError) as caught:
                task.query_gapup("industry_classifier_naics_sic", {{"company_description": "retailer"}}, timeout=30, max_bytes=100000)
            self.assertEqual(caught.exception.code, "GAPUP_MCP_PAYMENT_REQUIRED")


if __name__ == "__main__":
    unittest.main()
'''
    tests_dir = GAPUP / 'tests'
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / 'test_gapup_mcp_task.py').write_text(test_source, encoding='utf-8')


def write_docs(allowed_names: list[str], blocked_names: list[str]) -> None:
    GAPUP.mkdir(parents=True, exist_ok=True)
    (GAPUP / 'requirements.txt').write_text('jsonschema==4.26.0\nrequests==2.34.2\n', encoding='utf-8')
    readme = f'''# Gapup MCP 公共商业情报

正式票据前缀：

```text
[intel-gapup]
```

独立 Repository Secret：

```text
GAPUP_API_KEY
```

固定官方端点：

```text
POST https://mcp.gapup.io/mcp
```

官方目录探测得到271项工具。情报中心按 `maximum-safe-readonly` 固化开放 **209项操作**：

- 1项本地能力目录；
- 208项固定上游只读工具；
- 阻断63项不符合本中心边界的工具。

开放范围覆盖公共商业情报、市场与竞争分析、宏观经济、贸易与供应链、公司与证券公开信息、科研文献、专利、房地产、天气气候、内容数据、ESG和公开合规研究。

被阻断的类别包括：CRM写入、Webhook、异步批处理和结果轮询、个人KYC与候选人筛选、HR个人数据、主动攻击面与渗透范围、钱包和x402支付、医疗个案、敏感合同、个人邮箱、自动编排及其他可能绕过固定白名单的能力。

安全边界：

- 每张票据最多一次固定 `tools/call`；
- 只允许目录中固化的工具名和参数Schema；
- 强制 `async=false`，不创建后台作业，不轮询 `job_result`；
- 遇到HTTP 402只返回结构化失败，绝不自动支付USDC/EURC；
- 只允许公开、非个人、非机密输入；
- 所有URL必须是公开HTTPS地址，拒绝localhost、私网、保留IP、凭据URL和自定义端口；
- 禁止客户端提交API Key、Authorization、Cookie、Webhook、回调、钱包或支付证明；
- 禁止写入、交易、下单、CRM变更和后台监控；
- 上游调用会消耗Gapup免费额度或产生套餐费用；情报中心不自动循环调用。

官方文档当前说明免费层为每月100次调用。实际额度、价格、工具可用性和上游数据覆盖以Gapup账户与实时返回为准。

## 已开放工具

```text
{chr(10).join(allowed_names)}
```

## 已阻断工具

```text
{chr(10).join(blocked_names)}
```
'''
    (GAPUP / 'README.md').write_text(readme, encoding='utf-8')


def write_workflows() -> None:
    ticket_workflow = '''name: Managed Gapup MCP Intelligence Center

on:
  issues:
    types: [opened, reopened]

permissions:
  contents: read
  issues: write
  actions: read

concurrency:
  group: intel-gapup-global
  cancel-in-progress: false

jobs:
  execute-gapup-mcp:
    if: >-
      github.actor == github.repository_owner &&
      startsWith(github.event.issue.title, '[intel-gapup]')
    runs-on: ubuntu-24.04
    timeout-minutes: 25
    env:
      GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      ISSUE_NUMBER: ${{ github.event.issue.number }}
      GAPUP_API_KEY: ${{ secrets.GAPUP_API_KEY }}
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
          cache-dependency-path: api-center/gapup-mcp/requirements.txt

      - name: Install pinned dependencies
        run: |
          python -m pip install --disable-pip-version-check --no-input -r api-center/gapup-mcp/requirements.txt
          python -m pip check

      - name: Compile managed provider control plane
        run: python -m py_compile api-center/managed_provider_runtime.py api-center/gapup-mcp/gapup_mcp_task.py

      - name: Parse and authorize Gapup ticket
        id: prepare
        continue-on-error: true
        run: |
          python api-center/gapup-mcp/gapup_mcp_task.py prepare --event-path "$GITHUB_EVENT_PATH" --output-dir gapup-artifacts

      - name: Comment accepted ticket
        if: steps.prepare.outputs.accepted == 'true'
        run: |
          python api-center/gapup-mcp/gapup_mcp_task.py render --output-dir gapup-artifacts --phase accepted > gapup-comment.md
          gh api --method POST "repos/${GITHUB_REPOSITORY}/issues/${ISSUE_NUMBER}/comments" -F body=@gapup-comment.md

      - name: Comment rejected ticket
        if: steps.prepare.outputs.accepted != 'true'
        run: |
          python api-center/gapup-mcp/gapup_mcp_task.py render --output-dir gapup-artifacts --phase rejected > gapup-comment.md
          gh api --method POST "repos/${GITHUB_REPOSITORY}/issues/${ISSUE_NUMBER}/comments" -F body=@gapup-comment.md

      - name: Execute one bounded Gapup MCP tool
        id: execute
        if: steps.prepare.outputs.accepted == 'true'
        continue-on-error: true
        run: |
          python api-center/gapup-mcp/gapup_mcp_task.py execute --ticket gapup-artifacts/ticket.json --output-dir gapup-artifacts

      - name: Upload Gapup evidence
        id: upload
        if: always()
        continue-on-error: true
        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4
        with:
          name: gapup-mcp-ticket-${{ github.event.issue.number }}-${{ github.run_id }}
          path: gapup-artifacts/
          if-no-files-found: error
          retention-days: 30

      - name: Publish verified result or structured failure
        if: always() && steps.prepare.outputs.accepted == 'true'
        env:
          ARTIFACT_URL: ${{ steps.upload.outputs.artifact-url }}
        run: |
          python api-center/gapup-mcp/gapup_mcp_task.py render --output-dir gapup-artifacts --phase completed --artifact-url "$ARTIFACT_URL" > gapup-comment.md
          gh api --method POST "repos/${GITHUB_REPOSITORY}/issues/${ISSUE_NUMBER}/comments" -F body=@gapup-comment.md

      - name: Mark rejected or failed execution
        if: >-
          always() &&
          (steps.prepare.outputs.accepted != 'true' ||
           steps.execute.outputs.status != 'INTEL_GAPUP_MCP_COMPLETED' ||
           steps.upload.outcome != 'success')
        run: |
          echo "Gapup MCP intelligence ticket did not complete successfully."
          exit 1
'''
    (ROOT / '.github/workflows/gapup-mcp-api-ticket.yml').write_text(ticket_workflow, encoding='utf-8')

    validate_workflow = '''name: Validate Gapup MCP Provider

on:
  pull_request:
    paths:
      - "api-center/gapup-mcp/**"
      - "api-center/managed_provider_runtime.py"
      - "api-center/build_catalog.py"
      - "api-center/build_catalog_market_search.py"
      - "api-center/api-catalog.json"
      - "api-center/api-catalog.md"
      - ".github/workflows/gapup-mcp-provider-validate.yml"
      - ".github/workflows/gapup-mcp-api-ticket.yml"
  push:
    branches: [main]
    paths:
      - "api-center/gapup-mcp/**"
      - "api-center/managed_provider_runtime.py"
      - "api-center/build_catalog.py"
      - "api-center/build_catalog_market_search.py"
      - "api-center/api-catalog.json"
      - "api-center/api-catalog.md"
      - ".github/workflows/gapup-mcp-provider-validate.yml"
      - ".github/workflows/gapup-mcp-api-ticket.yml"
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
          cache-dependency-path: api-center/gapup-mcp/requirements.txt
      - name: Install dependencies
        run: |
          python -m pip install --disable-pip-version-check --no-input -r api-center/gapup-mcp/requirements.txt
          python -m pip check
      - name: Compile and test provider
        run: |
          python -m py_compile api-center/build_catalog.py api-center/build_catalog_market_search.py api-center/managed_provider_runtime.py api-center/gapup-mcp/gapup_mcp_task.py api-center/gapup-mcp/tests/*.py
          python -m unittest discover -s api-center/gapup-mcp/tests -p 'test_*.py' -v
      - name: Validate fixed safe contracts
        run: |
          python - <<'PY'
          import json
          from pathlib import Path
          from jsonschema import Draft202012Validator
          root = Path('api-center/gapup-mcp')
          schema = json.loads((root / 'ticket.schema.json').read_text(encoding='utf-8'))
          catalog = json.loads((root / 'provider-catalog.json').read_text(encoding='utf-8'))
          snapshot = json.loads((root / 'readonly-tools.snapshot.json').read_text(encoding='utf-8'))
          Draft202012Validator.check_schema(schema)
          provider = catalog['providers'][0]
          ids = {row['operation_id'] for row in provider['operations']}
          blocked = {row['name'] for row in snapshot['blocked_tools']}
          assert provider['provider_id'] == 'gapup-mcp'
          assert provider['ticket_prefix'] == '[intel-gapup]'
          assert provider['required_secret_environment_variable'] == 'GAPUP_API_KEY'
          assert len(ids) == 209
          assert len(blocked) == 63
          assert not ids.intersection(blocked)
          assert provider['limits']['fixed_api_host'] == 'mcp.gapup.io'
          assert provider['limits']['fixed_mcp_tool_count'] == 208
          assert provider['limits']['arbitrary_mcp_tool_names_allowed'] is False
          assert provider['limits']['automatic_x402_payment_allowed'] is False
          assert provider['limits']['async_jobs_allowed'] is False
          assert provider['limits']['write_operations_allowed'] is False
          print(json.dumps({'status':'PASS','operations':len(ids),'upstream_tools':208,'blocked':63}))
          PY
          git diff --check
          ! git grep -nE 'gpk_[A-Za-z0-9_-]{12,}' -- ':!api-center/gapup-mcp/tests/**'
'''
    (ROOT / '.github/workflows/gapup-mcp-provider-validate.yml').write_text(validate_workflow, encoding='utf-8')


def patch_catalog_and_tests() -> None:
    wrapper = CENTER / 'build_catalog_market_search.py'
    text = wrapper.read_text(encoding='utf-8')
    if 'GAPUP_MCP_CATALOG' not in text:
        text = text.replace(
            'ALPHAFEED_CATALOG = HERE / "alphafeed/provider-catalog.json"\n',
            'ALPHAFEED_CATALOG = HERE / "alphafeed/provider-catalog.json"\nGAPUP_MCP_CATALOG = HERE / "gapup-mcp/provider-catalog.json"\n',
            1,
        )
        text = text.replace(
            '    "alphafeed": 10,\n',
            '    "alphafeed": 10,\n    "gapup-mcp": 209,\n',
            1,
        )
        text = text.replace(
            '    ALPHAFEED_CATALOG,\n    KNOWLEDGE_TOOLS_CATALOG,\n',
            '    ALPHAFEED_CATALOG,\n    GAPUP_MCP_CATALOG,\n    KNOWLEDGE_TOOLS_CATALOG,\n',
            1,
        )
        text = text.replace(
            '        "alphafeed/provider-catalog.json",\n        "knowledge-tools/provider-catalog.json",\n',
            '        "alphafeed/provider-catalog.json",\n        "gapup-mcp/provider-catalog.json",\n        "knowledge-tools/provider-catalog.json",\n',
            1,
        )
        wrapper.write_text(text, encoding='utf-8')

    build = CENTER / 'build_catalog.py'
    text = build.read_text(encoding='utf-8')
    text = text.replace('Generate the deterministic maximum-safe API-center capability catalog.', 'Generate the deterministic maximum-safe Intelligence Center capability catalog.')
    if '"center_display_name_zh"' not in text:
        text = text.replace('"schema_version": "api-catalog-v3",\n', '"schema_version": "api-catalog-v3",\n        "center_display_name_zh": "情报中心",\n        "center_display_name_en": "Intelligence Center",\n        "technical_compatibility_path": "api-center/",\n', 1)
    text = text.replace('"# API 中心能力目录",', '"# 情报中心能力目录",')
    build.write_text(text, encoding='utf-8')

    api_test = CENTER / 'tests/test_api_catalog.py'
    text = api_test.read_text(encoding='utf-8')
    if '"gapup-mcp": 209' not in text:
        text = text.replace('    "agent-toolbelt": 21,\n', '    "agent-toolbelt": 21,\n    "gapup-mcp": 209,\n', 1)
        text = text.replace('catalog["managed_provider_count"], 30', 'catalog["managed_provider_count"], 31')
        text = text.replace('catalog["enabled_managed_provider_count"], 30', 'catalog["enabled_managed_provider_count"], 31')
        text = text.replace('catalog["managed_operation_count"], 360', 'catalog["managed_operation_count"], 569')
        text = text.replace('            "agent-toolbelt": "AGENT_TOOLBELT_KEY",\n', '            "agent-toolbelt": "AGENT_TOOLBELT_KEY",\n            "gapup-mcp": "GAPUP_API_KEY",\n', 1)
        anchor = '        self.assertFalse(\n            agent_toolbelt["limits"]["trading_or_order_execution_allowed"]\n        )\n\n'
        addition = '''        gapup = providers["gapup-mcp"]
        gapup_ids = {row["operation_id"] for row in gapup["operations"]}
        self.assertEqual(gapup["ticket_prefix"], "[intel-gapup]")
        self.assertEqual(gapup["required_secret_environment_variable_name"], "GAPUP_API_KEY")
        self.assertEqual(len(gapup_ids), 209)
        self.assertEqual(gapup["limits"]["fixed_mcp_tool_count"], 208)
        self.assertFalse(gapup["limits"]["automatic_x402_payment_allowed"])
        self.assertFalse(gapup["limits"]["async_jobs_allowed"])
        self.assertFalse(gapup["limits"]["write_operations_allowed"])
        self.assertNotIn("crm_connector", gapup_ids)
        self.assertNotIn("webhooks_manage", gapup_ids)

'''
        if anchor not in text:
            raise RuntimeError('Gapup API catalog test insertion anchor missing')
        text = text.replace(anchor, anchor + addition, 1)
        text = text.replace('        self.assertEqual(catalog["schema_version"], "api-catalog-v3")\n', '        self.assertEqual(catalog["schema_version"], "api-catalog-v3")\n        self.assertEqual(catalog["center_display_name_zh"], "情报中心")\n        self.assertEqual(catalog["center_display_name_en"], "Intelligence Center")\n', 1)
        api_test.write_text(text, encoding='utf-8')

    capability = CENTER / 'tests/test_capability_maximization.py'
    text = capability.read_text(encoding='utf-8')
    if '"gapup-mcp": 209' not in text:
        text = text.replace('            360,\n', '            569,\n', 1)
        text = text.replace('            "agent-toolbelt": 21,\n', '            "agent-toolbelt": 21,\n            "gapup-mcp": 209,\n', 1)
        capability.write_text(text, encoding='utf-8')


def patch_api_catalog_workflow() -> None:
    path = ROOT / '.github/workflows/api-catalog-validate.yml'
    text = path.read_text(encoding='utf-8')
    if 'api-center/gapup-mcp/requirements.txt' not in text:
        text = text.replace(
            '            api-center/agent-toolbelt/requirements.txt\n',
            '            api-center/agent-toolbelt/requirements.txt\n            api-center/gapup-mcp/requirements.txt\n',
        )
        text = text.replace(
            '            -r api-center/agent-toolbelt/requirements.txt\n',
            '            -r api-center/agent-toolbelt/requirements.txt \\\n            -r api-center/gapup-mcp/requirements.txt\n',
            1,
        )
        text = text.replace(
            '            api-center/agent-toolbelt/agent_toolbelt_task.py \\\n',
            '            api-center/agent-toolbelt/agent_toolbelt_task.py \\\n            api-center/gapup-mcp/gapup_mcp_task.py \\\n',
            1,
        )
        text = text.replace(
            '            api-center/agent-toolbelt/tests/*.py\n',
            '            api-center/agent-toolbelt/tests/*.py \\\n            api-center/gapup-mcp/tests/*.py\n',
            1,
        )
        text = text.replace(
            "          python -m unittest discover -s api-center/agent-toolbelt/tests -p 'test_*.py' -v\n",
            "          python -m unittest discover -s api-center/agent-toolbelt/tests -p 'test_*.py' -v\n          python -m unittest discover -s api-center/gapup-mcp/tests -p 'test_*.py' -v\n",
            1,
        )
        text = text.replace("== 360", "== 569", 1)
        text = text.replace("len(providers) == 30", "len(providers) == 31", 1)
        text = text.replace("enabled_managed_provider_count'] == 30", "enabled_managed_provider_count'] == 31", 1)
        insertion_anchor = "          print(json.dumps({\n"
        gapup_block = '''          gapup = providers['gapup-mcp']
          gapup_ids = {row['operation_id'] for row in gapup['operations']}
          assert gapup['ticket_prefix'] == '[intel-gapup]'
          assert gapup['required_secret_environment_variable_name'] == 'GAPUP_API_KEY'
          assert len(gapup_ids) == 209
          assert gapup['limits']['fixed_mcp_tool_count'] == 208
          assert gapup['limits']['automatic_x402_payment_allowed'] is False
          assert gapup['limits']['async_jobs_allowed'] is False
          assert gapup['limits']['write_operations_allowed'] is False
          assert 'crm_connector' not in gapup_ids
          assert 'webhooks_manage' not in gapup_ids

'''
        if insertion_anchor not in text:
            raise RuntimeError('API catalog workflow insertion anchor missing')
        text = text.replace(insertion_anchor, gapup_block + insertion_anchor, 1)
        text = text.replace("'managed_operations': 360", "'managed_operations': 569", 1)
        text = text.replace("'agent_toolbelt_stock_operations': 0,\n", "'agent_toolbelt_stock_operations': 0,\n              'gapup_mcp_operations': 209,\n              'gapup_mcp_upstream_tools': 208,\n", 1)
        text = text.replace(
            '            api-center/agent-toolbelt/ticket.schema.json\n',
            '            api-center/agent-toolbelt/ticket.schema.json\n            api-center/gapup-mcp/provider-catalog.json\n            api-center/gapup-mcp/ticket.schema.json\n            api-center/gapup-mcp/readonly-tools.snapshot.json\n',
            1,
        )
        path.write_text(text, encoding='utf-8')


def patch_docs() -> None:
    api_readme = CENTER / 'README.md'
    text = api_readme.read_text(encoding='utf-8')
    if 'GAPUP_API_KEY' not in text:
        text = text.replace('AGENT_TOOLBELT_KEY\n', 'AGENT_TOOLBELT_KEY\nGAPUP_API_KEY\n', 1) if 'AGENT_TOOLBELT_KEY\n' in text else text.replace('EM_API_KEY\n', 'EM_API_KEY\nGAPUP_API_KEY\n', 1)
    section = '''## Gapup MCP 公共商业情报

`api-center/gapup-mcp/` 固定访问Gapup官方MCP：

```text
[intel-gapup]
POST https://mcp.gapup.io/mcp
Repository Secret: GAPUP_API_KEY
```

官方 `tools/list` 实测返回271项工具。情报中心固化开放209项操作（1项本地目录、208项上游只读工具），覆盖公共商业、竞争、市场、贸易、公司、宏观、科研、专利、房地产、天气气候、内容数据与ESG情报。63项CRM写入、Webhook、异步批处理、个人KYC/HR、主动攻击面、钱包与x402支付、医疗个案、敏感合同和自动编排能力被明确阻断。

每张票据只执行一次固定 `tools/call`；强制同步模式；遇到HTTP 402只返回失败，不自动支付；仅允许公开、非个人、非机密数据和公开HTTPS URL。

'''
    if '## Gapup MCP 公共商业情报' not in text:
        anchor = '## 正式数据任务\n'
        if anchor not in text:
            raise RuntimeError('API README formal task anchor missing')
        text = text.replace(anchor, section + anchor, 1)
    api_readme.write_text(text, encoding='utf-8')

    policy = CENTER / 'SECRET_ISOLATION_POLICY.md'
    text = policy.read_text(encoding='utf-8')
    if 'GAPUP_API_KEY' not in text:
        text = text.replace('AGENT_TOOLBELT_KEY\n', 'AGENT_TOOLBELT_KEY\nGAPUP_API_KEY\n', 1) if 'AGENT_TOOLBELT_KEY\n' in text else text.replace('LLAMA_CLOUD_API_KEY\n', 'LLAMA_CLOUD_API_KEY\nGAPUP_API_KEY\n', 1)
        text += '''

## Gapup MCP

```text
Repository Secret: GAPUP_API_KEY
```

该Key只允许作为 `x-api-key` 请求头发送至 `https://mcp.gapup.io/mcp`。客户端不得提交或覆盖Key。情报中心不保存钱包、不生成x402付款证明、不自动支付，也不把Key、Authorization或支付信息写入Issue、日志、目录或Artifact。
'''
    policy.write_text(text, encoding='utf-8')


def main() -> int:
    discovery = load_json(DISCOVERY)
    if discovery.get('secret_values_exposed') is not False or discovery.get('business_tool_calls') != 0:
        raise RuntimeError('unsafe Gapup discovery snapshot')
    rename_center_terms()
    allowed_names, blocked_names = build_provider(discovery)
    write_runtime()
    write_tests(allowed_names, blocked_names)
    write_docs(allowed_names, blocked_names)
    write_workflows()
    patch_catalog_and_tests()
    patch_api_catalog_workflow()
    patch_docs()
    print(json.dumps({
        'status': 'PASS',
        'official_tools': 271,
        'allowed_upstream_tools': len(allowed_names),
        'blocked_tools': len(blocked_names),
        'provider_operations': len(allowed_names) + 1,
        'center_display_name_zh': '情报中心',
        'secret_values_exposed': False,
    }, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
