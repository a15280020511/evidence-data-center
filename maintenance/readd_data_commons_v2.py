#!/usr/bin/env python3
"""Reintegrate Data Commons as a standalone REST V2 managed provider."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "api-center"
DC = API / "data-commons"


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"expected marker missing in {path}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


operations = [
    {
        "operation_id": "catalog-capabilities",
        "description": "读取受控能力和中国起步目录，不调用上游。",
        "parameters": [],
        "parameter_schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {},
        },
    },
    {
        "operation_id": "resolve-place",
        "description": "按一个或多个公开地点名称解析 Data Commons 地点 DCID。",
        "parameters": ["nodes_json", "property"],
        "parameter_schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "nodes_json": {"type": "string", "minLength": 2, "maxLength": 6000},
                "property": {"type": "string", "maxLength": 300},
            },
            "required": ["nodes_json"],
        },
        "result_contract": {
            "endpoint": "/v2/resolve",
            "method": "POST",
            "read_only": True,
            "authentication": "X-API-Key backend-only",
        },
    },
    {
        "operation_id": "resolve-indicator",
        "description": "按公开指标名称或描述解析统计变量或主题 DCID。",
        "parameters": ["nodes_json"],
        "parameter_schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "nodes_json": {"type": "string", "minLength": 2, "maxLength": 6000},
            },
            "required": ["nodes_json"],
        },
        "result_contract": {
            "endpoint": "/v2/resolve",
            "method": "POST",
            "read_only": True,
            "authentication": "X-API-Key backend-only",
        },
    },
    {
        "operation_id": "node-properties",
        "description": "按受控关系表达式读取节点属性、相邻实体或行政层级关系。",
        "parameters": ["nodes_json", "property"],
        "parameter_schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "nodes_json": {"type": "string", "minLength": 2, "maxLength": 6000},
                "property": {"type": "string", "minLength": 1, "maxLength": 300},
            },
            "required": ["nodes_json", "property"],
        },
        "result_contract": {
            "endpoint": "/v2/node",
            "method": "POST",
            "read_only": True,
            "authentication": "X-API-Key backend-only",
        },
    },
    {
        "operation_id": "observations",
        "description": "读取公开实体和统计变量的最新值、指定日期或完整时间序列，并保留 facet 来源。",
        "parameters": [
            "entity_dcids_json",
            "variable_dcids_json",
            "date",
            "select_json",
            "facet_ids_json",
            "domains_json",
        ],
        "parameter_schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "entity_dcids_json": {"type": "string", "minLength": 2, "maxLength": 6000},
                "variable_dcids_json": {"type": "string", "minLength": 2, "maxLength": 6000},
                "date": {"type": "string", "maxLength": 40},
                "select_json": {"type": "string", "maxLength": 300},
                "facet_ids_json": {"type": "string", "maxLength": 6000},
                "domains_json": {"type": "string", "maxLength": 6000},
            },
            "required": ["entity_dcids_json", "variable_dcids_json"],
        },
        "result_contract": {
            "endpoint": "/v2/observation",
            "method": "POST",
            "read_only": True,
            "authentication": "X-API-Key backend-only",
        },
    },
]

provider = {
    "schema_version": "data-commons-provider-catalog-v3",
    "secret_values_exposed": False,
    "replaced_legacy_connectors": [],
    "providers": [
        {
            "provider_id": "data-commons",
            "display_name": "Google Data Commons",
            "description": "通过官方 REST V2 查询全球公共统计知识图谱，支持地点与指标解析、图节点关系和统计观测。",
            "enabled": True,
            "ticket_prefix": "[api-dc]",
            "required_secret_environment_variable": "GOOGLE_DATA_COMMONS_API_KEY",
            "catalog_policy": "仅开放 REST V2 的 resolve、node 和 observation 三个固定 POST 端点；优先读取中国起步目录，不假设所有城市或县均有数据。",
            "execution_policy": "API Key 仅以 X-API-Key 后端请求头注入；每张票据只执行一个白名单操作，限制节点数、变量数、关系表达式、超时和响应体积。",
            "official_origin": "https://api.datacommons.org",
            "allowed_endpoints": ["/resolve", "/node", "/observation"],
            "operations": operations,
            "limits": {
                "requests_per_ticket_max": 1,
                "max_nodes": 20,
                "max_variables": 20,
                "max_select_fields": 5,
                "max_relation_expression_characters": 300,
                "max_response_bytes": 1000000,
                "timeout_seconds_max": 60,
                "arbitrary_urls_allowed": False,
                "arbitrary_endpoints_allowed": False,
                "arbitrary_headers_allowed": False,
                "client_supplied_api_key_allowed": False,
                "sparql_allowed": False,
                "natural_language_api_allowed": False,
                "mcp_allowed": False,
                "write_operations_allowed": False,
                "personal_data_allowed": False,
                "secret_values_exposed": False,
            },
        }
    ],
}
write_json(DC / "provider-catalog.json", provider)

schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://github.com/a15280020511/evidence-data-center/api-center/data-commons/ticket.schema.json",
    "title": "Managed Data Commons REST V2 ticket",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "task_id", "provider", "operation", "objective", "parameters",
        "data_policy", "acceptance"
    ],
    "properties": {
        "task_id": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$"},
        "provider": {"const": "data-commons"},
        "operation": {"enum": [row["operation_id"] for row in operations]},
        "objective": {"type": "string", "minLength": 1, "maxLength": 1000},
        "parameters": {"type": "object", "maxProperties": 12},
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
                "timeout_seconds": {"type": "integer", "minimum": 5, "maximum": 60},
                "max_response_bytes": {"type": "integer", "minimum": 1024, "maximum": 1000000},
            },
        },
    },
}
write_json(DC / "ticket.schema.json", schema)

runtime = (DC / "data_commons_task.py").read_text(encoding="utf-8")
old_map = '''def _operation_map() -> dict[str, Mapping[str, Any]]:\n    catalog = load_json(CATALOG_PATH)\n    return {\n        str(row["operation_id"]): row\n        for row in catalog.get("operations", [])\n        if isinstance(row, Mapping)\n    }\n'''
new_map = '''def _operation_map() -> dict[str, Mapping[str, Any]]:\n    catalog = load_json(CATALOG_PATH)\n    providers = catalog.get("providers") if isinstance(catalog, Mapping) else None\n    provider = providers[0] if isinstance(providers, list) and providers else {}\n    operations = provider.get("operations", []) if isinstance(provider, Mapping) else []\n    return {\n        str(row["operation_id"]): row\n        for row in operations\n        if isinstance(row, Mapping)\n    }\n'''
if old_map not in runtime:
    raise RuntimeError("old Data Commons operation map not found")
runtime = runtime.replace(old_map, new_map, 1)
runtime = runtime.replace('"schema_version": "data-commons-api-snapshot-v1"', '"schema_version": "data-commons-api-snapshot-v2"')
(DC / "data_commons_task.py").write_text(runtime, encoding="utf-8")

(DC / "duplicate_guard.py").unlink(missing_ok=True)

(DC / "README.md").write_text(
    """# Google Data Commons managed provider\n\n"
    "Standalone REST V2 provider using Repository Secret `GOOGLE_DATA_COMMONS_API_KEY`. "
    "The key is injected only through the backend `X-API-Key` header and is never written to logs, Issues or Artifacts.\n\n"
    "Allowed operations: `catalog-capabilities`, `resolve-place`, `resolve-indicator`, "
    "`node-properties`, and `observations`. Arbitrary URLs, SPARQL, NL API, MCP, writes and personal-data queries are disabled.\n"
    """,
    encoding="utf-8",
)

# Replace legacy tests with focused standalone V2 regression coverage.
test_text = '''from __future__ import annotations\n\nimport importlib.util\nimport json\nimport os\nimport tempfile\nimport unittest\nfrom pathlib import Path\nfrom unittest.mock import Mock, patch\n\nROOT = Path(__file__).resolve().parents[1]\nSPEC = importlib.util.spec_from_file_location("data_commons_task", ROOT / "data_commons_task.py")\nassert SPEC and SPEC.loader\ndc = importlib.util.module_from_spec(SPEC)\nSPEC.loader.exec_module(dc)\n\n\ndef ticket(operation: str, parameters: dict) -> dict:\n    return {\n        "task_id": "dc-test-001",\n        "provider": "data-commons",\n        "operation": operation,\n        "objective": "validate bounded REST V2 access",\n        "parameters": parameters,\n        "data_policy": {"classification": "public", "contains_personal_data": False},\n        "acceptance": {"timeout_seconds": 20, "max_response_bytes": 200000},\n    }\n\n\nclass DataCommonsTaskTests(unittest.TestCase):\n    def test_catalog_has_five_fixed_operations_and_independent_key(self) -> None:\n        catalog = json.loads((ROOT / "provider-catalog.json").read_text(encoding="utf-8"))\n        provider = catalog["providers"][0]\n        self.assertEqual(provider["provider_id"], "data-commons")\n        self.assertEqual(provider["required_secret_environment_variable"], "GOOGLE_DATA_COMMONS_API_KEY")\n        self.assertEqual(len(provider["operations"]), 5)\n        self.assertFalse(provider["limits"]["arbitrary_urls_allowed"])\n        self.assertFalse(provider["limits"]["sparql_allowed"])\n        self.assertFalse(provider["limits"]["natural_language_api_allowed"])\n        self.assertFalse(provider["limits"]["write_operations_allowed"])\n\n    def test_observation_request_is_fixed_and_bounded(self) -> None:\n        endpoint, body, local = dc._build_operation(\n            "observations",\n            {\n                "entity_dcids_json": '["country/CHN"]',\n                "variable_dcids_json": '["Count_Person"]',\n                "date": "LATEST",\n            },\n        )\n        self.assertEqual(endpoint, "/observation")\n        self.assertEqual(body["entity"]["dcids"], ["country/CHN"])\n        self.assertEqual(body["variable"]["dcids"], ["Count_Person"])\n        self.assertEqual(local, {})\n\n    def test_rejects_non_allowlisted_parameters(self) -> None:\n        with self.assertRaisesRegex(ValueError, "non-allowlisted"):\n            dc.validate_ticket(ticket("resolve-place", {"nodes_json": '["China"]', "url": "https://evil.invalid"}))\n\n    def test_missing_key_is_structured_and_secretless(self) -> None:\n        with tempfile.TemporaryDirectory() as tmp:\n            out = Path(tmp)\n            path = out / "ticket.json"\n            path.write_text(json.dumps(ticket("resolve-place", {"nodes_json": '["China"]'})), encoding="utf-8")\n            with patch.dict(os.environ, {}, clear=True):\n                self.assertEqual(dc.execute(path, out), 1)\n            snap = json.loads((out / "snapshot.json").read_text(encoding="utf-8"))\n            self.assertEqual(snap["failure"]["code"], "DATA_COMMONS_API_KEY_MISSING")\n            self.assertNotIn("api_key", json.dumps(snap).lower())\n\n    def test_successful_request_uses_x_api_key_without_recording_value(self) -> None:\n        response = Mock()\n        response.ok = True\n        response.status_code = 200\n        response.content = b'{"entities":[{"node":"China"}]}'\n        response.headers = {"Content-Type": "application/json"}\n        response.json.return_value = {"entities": [{"node": "China"}]}\n        with patch.object(dc.requests, "post", return_value=response) as post:\n            data, metadata = dc._request_json(\n                "/resolve", api_key="test-visible-key",\n                body={"nodes": ["China"], "resolver": "place"},\n                timeout=20, max_bytes=200000,\n            )\n        self.assertEqual(data["entities"][0]["node"], "China")\n        headers = post.call_args.kwargs["headers"]\n        self.assertEqual(headers["X-API-Key"], "test-visible-key")\n        self.assertNotIn("test-visible-key", json.dumps(metadata))\n\n\nif __name__ == "__main__":\n    unittest.main()\n'''
(DC / "tests").mkdir(exist_ok=True)
(DC / "tests" / "test_data_commons_task.py").write_text(test_text, encoding="utf-8")

# Register the standalone provider in the extended deterministic catalog.
wrapper = API / "build_catalog_market_search.py"
replace_once(wrapper, 'EODHD_CATALOG = HERE / "eodhd/provider-catalog.json"\n', 'EODHD_CATALOG = HERE / "eodhd/provider-catalog.json"\nDATA_COMMONS_CATALOG = HERE / "data-commons/provider-catalog.json"\n')
replace_once(wrapper, '    "eodhd": 25,\n', '    "eodhd": 25,\n    "data-commons": 5,\n')
replace_once(wrapper, '    EODHD_CATALOG,\n    KNOWLEDGE_TOOLS_CATALOG,\n', '    EODHD_CATALOG,\n    DATA_COMMONS_CATALOG,\n    KNOWLEDGE_TOOLS_CATALOG,\n')
replace_once(wrapper, '        "eodhd/provider-catalog.json",\n        "knowledge-tools/provider-catalog.json",\n', '        "eodhd/provider-catalog.json",\n        "data-commons/provider-catalog.json",\n        "knowledge-tools/provider-catalog.json",\n')

# Update catalog regression expectations.
test_catalog = API / "tests" / "test_api_catalog.py"
replace_once(test_catalog, '    "earth-engine": 6,\n', '    "earth-engine": 6,\n    "data-commons": 5,\n')
replace_once(test_catalog, 'self.assertEqual(catalog["managed_provider_count"], 19)', 'self.assertEqual(catalog["managed_provider_count"], 20)')
replace_once(test_catalog, 'self.assertEqual(catalog["enabled_managed_provider_count"], 19)', 'self.assertEqual(catalog["enabled_managed_provider_count"], 20)')
replace_once(test_catalog, 'self.assertEqual(catalog["managed_operation_count"], 190)', 'self.assertEqual(catalog["managed_operation_count"], 195)')
replace_once(test_catalog, '            "earth-engine": "GOOGLE_CLOUD_SERVICE_ACCOUNT_JSON",\n', '            "earth-engine": "GOOGLE_CLOUD_SERVICE_ACCOUNT_JSON",\n            "data-commons": "GOOGLE_DATA_COMMONS_API_KEY",\n')
replace_once(test_catalog, '        self.assertEqual(providers["baostock"]["ticket_prefix"], "[api-baostock]")\n', '        self.assertEqual(providers["data-commons"]["ticket_prefix"], "[api-dc]")\n        self.assertEqual(providers["data-commons"]["required_secret_environment_variable_name"], "GOOGLE_DATA_COMMONS_API_KEY")\n        self.assertFalse(providers["data-commons"]["limits"]["arbitrary_urls_allowed"])\n        self.assertFalse(providers["data-commons"]["limits"]["sparql_allowed"])\n\n        self.assertEqual(providers["baostock"]["ticket_prefix"], "[api-baostock]")\n')
replace_once(test_catalog, '            "eodhd/provider-catalog.json",\n            "knowledge-tools/provider-catalog.json",\n', '            "eodhd/provider-catalog.json",\n            "data-commons/provider-catalog.json",\n            "knowledge-tools/provider-catalog.json",\n')

capability = API / "tests" / "test_capability_maximization.py"
replace_once(capability, '            190,\n', '            195,\n')
replace_once(capability, '            "earth-engine": 6,\n', '            "earth-engine": 6,\n            "data-commons": 5,\n')
replace_once(capability, '        eodhd = json.loads(\n', '        data_commons = json.loads(\n            (ROOT / "data-commons/provider-catalog.json").read_text(encoding="utf-8")\n        )\n        dc_provider = data_commons["providers"][0]\n        self.assertEqual(dc_provider["required_secret_environment_variable"], "GOOGLE_DATA_COMMONS_API_KEY")\n        self.assertFalse(dc_provider["limits"]["arbitrary_urls_allowed"])\n        self.assertFalse(dc_provider["limits"]["arbitrary_endpoints_allowed"])\n        self.assertFalse(dc_provider["limits"]["sparql_allowed"])\n        self.assertFalse(dc_provider["limits"]["write_operations_allowed"])\n\n        eodhd = json.loads(\n')

readme = API / "README.md"
text = readme.read_text(encoding="utf-8")
section = '''\n## Google Data Commons\n\n- Provider: `data-commons`\n- Ticket prefix: `[api-dc]`\n- Secret: `GOOGLE_DATA_COMMONS_API_KEY`\n- Authentication: REST V2 `X-API-Key` header\n- Fixed read-only operations: 5\n- BigQuery and Earth Engine continue to use `GOOGLE_CLOUD_SERVICE_ACCOUNT_JSON`; Data Commons is intentionally isolated.\n'''
if "## Google Data Commons" not in text:
    readme.write_text(text.rstrip() + "\n" + section, encoding="utf-8")

dependabot = ROOT / ".github" / "dependabot.yml"
dep = dependabot.read_text(encoding="utf-8")
block = '''\n  - package-ecosystem: "pip"\n    directory: "/api-center/data-commons"\n    schedule:\n      interval: "weekly"\n    open-pull-requests-limit: 5\n'''
if 'directory: "/api-center/data-commons"' not in dep:
    dependabot.write_text(dep.rstrip() + "\n" + block, encoding="utf-8")

Path(__file__).unlink()
