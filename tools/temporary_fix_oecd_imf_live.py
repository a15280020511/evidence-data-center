#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "api-center"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected one match in {path}: found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# OECD: SDMX structure JSON is version 1.0, not data JSON 2.0.
oecd_task = API / "oecd" / "oecd_task.py"
replace_once(
    oecd_task,
    '''def accept_header(operation: str, fmt: str) -> str:\n    data = operation == "get-data"\n    if fmt == "csv":\n        return (\n            "application/vnd.sdmx.data+csv;version=2.0.0"\n            if data\n            else "application/vnd.sdmx.structure+csv;version=2.0.0"\n        )\n    return (\n        "application/vnd.sdmx.data+json;version=2.0.0"\n        if data\n        else "application/vnd.sdmx.structure+json;version=2.0.0"\n    )\n''',
    '''def accept_header(operation: str, fmt: str) -> str:\n    data = operation == "get-data"\n    if not data and fmt != "json":\n        raise ValueError("OECD structure resources support json format only")\n    if fmt == "csv":\n        return "application/vnd.sdmx.data+csv;version=2.0.0"\n    return (\n        "application/vnd.sdmx.data+json;version=2.0.0"\n        if data\n        else "application/vnd.sdmx.structure+json;version=1.0"\n    )\n''',
)

oecd_catalog_path = API / "oecd" / "provider-catalog.json"
oecd_catalog = json.loads(oecd_catalog_path.read_text(encoding="utf-8"))
for operation in oecd_catalog["providers"][0]["operations"]:
    if operation["operation_id"] in {
        "list-dataflows", "get-dataflow", "get-datastructure", "get-codelist"
    }:
        operation["parameter_schema"]["properties"]["format"]["enum"] = ["json"]
oecd_catalog["providers"][0]["service_status_notice"] = (
    "OECD structure resources use SDMX-JSON 1.0; data resources use SDMX-JSON or SDMX-CSV 2.0."
)
oecd_catalog_path.write_text(
    json.dumps(oecd_catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)

oecd_tests = API / "oecd" / "tests" / "test_oecd_task.py"
replace_once(
    oecd_tests,
    '''        self.assertEqual(fmt, "json")\n        with self.assertRaises(ValueError):\n''',
    '''        self.assertEqual(fmt, "json")\n        self.assertEqual(\n            task.accept_header("list-dataflows", "json"),\n            "application/vnd.sdmx.structure+json;version=1.0",\n        )\n        with self.assertRaises(ValueError):\n            task.accept_header("list-dataflows", "csv")\n        with self.assertRaises(ValueError):\n''',
)

# IMF: move from cloud-blocked DataMapper to the current official SDMX 3.0 API.
shared = API / "international-statistics" / "provider_task.py"
replace_once(
    shared,
    '''    "imf": {\n        "origin": "https://www.imf.org/external/datamapper/api/v2",\n        "prefix": "[intel-imf]",\n        "status": "INTEL_IMF",\n        "secret": "",\n        "max_requests": 1,\n    },\n''',
    '''    "imf": {\n        "origin": "https://api.imf.org/external/sdmx/3.0",\n        "prefix": "[intel-imf]",\n        "status": "INTEL_IMF",\n        "secret": "IMF_API_KEY",\n        "secret_header": "Ocp-Apim-Subscription-Key",\n        "max_requests": 1,\n    },\n''',
)
start = shared.read_text(encoding="utf-8")
old_imf_start = start.index('    if provider == "imf":\n')
old_imf_end = start.index('    if provider == "faostat":\n', old_imf_start)
new_imf = '''    if provider == "imf":\n        structure_ops = {\n            "get-dataflow": ("dataflow", "flow"),\n            "get-datastructure": ("datastructure", "structure_id"),\n            "get-codelist": ("codelist", "codelist_id"),\n            "get-conceptscheme": ("conceptscheme", "conceptscheme_id"),\n        }\n        if operation in structure_ops:\n            resource_type, parameter_name = structure_ops[operation]\n            agency = str(p.get("agency") or "")\n            resource_id = str(p.get(parameter_name) or "")\n            version = str(p.get("version") or "+")\n            if not CODE_RE.fullmatch(agency) or not CODE_RE.fullmatch(resource_id):\n                raise ValueError(f"agency and {parameter_name} are required")\n            if not re.fullmatch(r"^(?:\\+|latest|[0-9]+(?:\\.[0-9]+){0,3})$", version):\n                raise ValueError("version is invalid")\n            path = "/structure/" + "/".join(\n                quote(value, safe="._@+-")\n                for value in (resource_type, agency, resource_id, version)\n            )\n            return path, []\n        if operation != "get-data":\n            raise ValueError(f"unsupported IMF operation: {operation}")\n        agency = str(p.get("agency") or "")\n        flow = str(p.get("flow") or "")\n        version = str(p.get("version") or "+")\n        key = str(p.get("key") or "")\n        if not CODE_RE.fullmatch(agency) or not CODE_RE.fullmatch(flow):\n            raise ValueError("agency and flow are required")\n        if not re.fullmatch(r"^(?:\\+|latest|[0-9]+(?:\\.[0-9]+){0,3})$", version):\n            raise ValueError("version is invalid")\n        if not re.fullmatch(r"^[A-Za-z0-9*+._@-]{1,500}$", key):\n            raise ValueError("key is invalid")\n        path = "/data/dataflow/" + "/".join(\n            quote(value, safe="*+._@-") for value in (agency, flow, version, key)\n        )\n        query: list[tuple[str, str]] = []\n        start_period = p.get("start_period")\n        end_period = p.get("end_period")\n        if start_period not in (None, ""):\n            if not PERIOD_RE.fullmatch(str(start_period)):\n                raise ValueError("start_period is invalid")\n            query.append(("startPeriod", str(start_period)))\n        if end_period not in (None, ""):\n            if not PERIOD_RE.fullmatch(str(end_period)):\n                raise ValueError("end_period is invalid")\n            query.append(("endPeriod", str(end_period)))\n        dimension = p.get("dimension_at_observation")\n        if dimension not in (None, ""):\n            if dimension not in {"AllDimensions", "TimeDimension", "MeasureDimension"}:\n                raise ValueError("dimension_at_observation is invalid")\n            query.append(("dimensionAtObservation", str(dimension)))\n        return path, query\n\n'''
shared.write_text(start[:old_imf_start] + new_imf + start[old_imf_end:], encoding="utf-8")
replace_once(
    shared,
    '''            headers = {"Accept": "application/json", "User-Agent": f"intelligence-center-{provider}/1"}\n            if provider == "wto":\n                if not password:\n                    raise RuntimeError("WTO_API_KEY is not configured")\n                headers[cfg["secret_header"]] = password\n            elif provider == "faostat":\n''',
    '''            headers = {"Accept": "application/json", "User-Agent": f"intelligence-center-{provider}/1"}\n            if provider in {"wto", "imf"}:\n                if not password:\n                    raise RuntimeError(f"{cfg['secret']} is not configured")\n                headers[cfg["secret_header"]] = password\n                if provider == "imf":\n                    headers["Accept"] = (\n                        "application/json, application/vnd.sdmx.data+json, "\n                        "application/vnd.sdmx.structure+json, */*;q=0.8"\n                    )\n            elif provider == "faostat":\n''',
)
replace_once(
    shared,
    '''            raw = bytes(response.content or b"")\n            if len(raw) > max_bytes:\n                raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")\n            try:\n                payload = response.json()\n            except ValueError as exc:\n                raise RuntimeError(f"{provider.upper()} returned invalid JSON") from exc\n            clean = _scrub(payload, secrets)\n            if not response.ok:\n                raise RuntimeError(f"{provider.upper()} HTTP {response.status_code}: {str(clean)[:1200]}")\n''',
    '''            raw = bytes(response.content or b"")\n            metadata.update({\n                "upstream_called": True,\n                "http_status": response.status_code,\n                "content_type": response.headers.get("Content-Type", ""),\n                "request_path": path,\n                "query_parameter_names": sorted({k for k, _ in query}),\n            })\n            if len(raw) > max_bytes:\n                raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")\n            if not response.ok:\n                try:\n                    error_payload = _scrub(response.json(), secrets)\n                    detail = str(error_payload)[:1200]\n                except ValueError:\n                    detail = _scrub(raw[:1200].decode("utf-8", errors="replace"), secrets)\n                raise RuntimeError(f"{provider.upper()} HTTP {response.status_code}: {detail}")\n            try:\n                payload = response.json()\n            except ValueError as exc:\n                content_type = response.headers.get("Content-Type", "")\n                raise RuntimeError(\n                    f"{provider.upper()} HTTP {response.status_code} returned non-JSON "\n                    f"content-type {content_type or 'unknown'}"\n                ) from exc\n            clean = _scrub(payload, secrets)\n''',
)
replace_once(
    shared,
    '''                "upstream_called": True,\n                "http_status": response.status_code,\n                "content_type": response.headers.get("Content-Type", ""),\n                "request_path": path,\n                "query_parameter_names": sorted({k for k, _ in query}),\n                "response_bytes": len(sanitized),\n''',
    '''                "response_bytes": len(sanitized),\n''',
)
replace_once(
    shared,
    '''                "credential_used": provider in {"wto", "faostat"},\n''',
    '''                "credential_used": provider in {"wto", "imf", "faostat"},\n''',
)

imf_catalog = {
    "schema_version": "imf-provider-catalog-v2",
    "secret_values_exposed": False,
    "replaced_legacy_connectors": ["imf-datamapper-v2"],
    "providers": [{
        "provider_id": "imf",
        "display_name": "IMF SDMX 3.0 全球宏观、财政与金融统计",
        "description": "通过 IMF 当前官方 SDMX 3.0 API 读取 WEO、CPI、BOP、财政、货币金融、贸易及其他公开统计数据流、结构、代码表、概念表和观测值。",
        "enabled": True,
        "ticket_prefix": "[intel-imf]",
        "required_secret_environment_variable": "IMF_API_KEY",
        "catalog_policy": "固定访问 api.imf.org/external/sdmx/3.0；订阅密钥仅通过 Ocp-Apim-Subscription-Key 后端请求头发送，不进入 URL、Issue、日志或 Artifact。",
        "execution_policy": "每张票据最多一次 GET；无自动重试、无自动翻页；只允许固定 SDMX 结构资源和单一受限数据键。",
        "official_documentation": "https://data.imf.org/en/Resource-Pages/IMF-API",
        "official_origin": "https://api.imf.org/external/sdmx/3.0",
        "service_status_notice": "旧 DataMapper 接口会拒绝 GitHub 云端出口，生产连接已切换至 IMF 当前 SDMX 3.0 API。",
        "limits": {
            "requests_per_ticket_max": 1,
            "transient_retry_max": 0,
            "provider_concurrency_max": 1,
            "timeout_seconds_max": 120,
            "max_response_bytes": 20000000,
            "fixed_api_host": "api.imf.org",
            "fixed_api_prefix": "/external/sdmx/3.0",
            "subscription_key_header": "Ocp-Apim-Subscription-Key",
            "data_key_length_max": 500,
            "automatic_retry_allowed": False,
            "automatic_pagination_allowed": False,
            "bulk_download_allowed": False,
            "arbitrary_sdmx_resource_types_allowed": False,
            "arbitrary_urls_allowed": False,
            "arbitrary_hosts_allowed": False,
            "arbitrary_headers_allowed": False,
            "client_supplied_credentials_allowed": False,
            "write_operations_allowed": False,
            "secret_values_exposed": False,
            "authentication_required": True,
        },
        "operations": []
    }]
}
provider = imf_catalog["providers"][0]
local = {
    "operation_id": "catalog-capabilities",
    "description": "读取本地 IMF SDMX 安全能力目录，不访问上游。",
    "parameters": [],
    "parameter_schema": {"type": "object", "additionalProperties": False, "properties": {}},
    "result_contract": {"provider": "imf", "http_method": "LOCAL", "read_only": True, "credential_mode": "none"},
}
provider["operations"].append(local)
common_component = {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@+-]{0,79}$"}
version_schema = {"type": "string", "pattern": "^(?:\\+|latest|[0-9]+(?:\\.[0-9]+){0,3})$"}
for op_id, description, parameter_name in [
    ("get-dataflow", "读取指定 IMF SDMX 数据流定义。", "flow"),
    ("get-datastructure", "读取指定 IMF SDMX 数据结构定义。", "structure_id"),
    ("get-codelist", "读取指定 IMF SDMX 代码表。", "codelist_id"),
    ("get-conceptscheme", "读取指定 IMF SDMX 概念表。", "conceptscheme_id"),
]:
    provider["operations"].append({
        "operation_id": op_id,
        "description": description,
        "parameters": ["agency", parameter_name, "version"],
        "parameter_schema": {
            "type": "object", "additionalProperties": False,
            "properties": {"agency": common_component, parameter_name: common_component, "version": version_schema},
            "required": ["agency", parameter_name],
        },
        "result_contract": {"provider": "imf", "http_method": "GET", "read_only": True, "credential_mode": "subscription_key_header"},
    })
provider["operations"].append({
    "operation_id": "get-data",
    "description": "按固定数据流、版本、受限维度键和可选时期范围读取 IMF SDMX 观测数据。",
    "parameters": ["agency", "flow", "version", "key", "start_period", "end_period", "dimension_at_observation"],
    "parameter_schema": {
        "type": "object", "additionalProperties": False,
        "properties": {
            "agency": common_component,
            "flow": common_component,
            "version": version_schema,
            "key": {"type": "string", "minLength": 1, "maxLength": 500, "pattern": "^[A-Za-z0-9*+._@-]+$"},
            "start_period": {"type": "string", "pattern": "^[0-9]{4}(?:-(?:M[0-9]{2}|Q[1-4]))?$"},
            "end_period": {"type": "string", "pattern": "^[0-9]{4}(?:-(?:M[0-9]{2}|Q[1-4]))?$"},
            "dimension_at_observation": {"type": "string", "enum": ["AllDimensions", "TimeDimension", "MeasureDimension"]},
        },
        "required": ["agency", "flow", "key"],
    },
    "result_contract": {"provider": "imf", "http_method": "GET", "read_only": True, "credential_mode": "subscription_key_header"},
})
(API / "imf" / "provider-catalog.json").write_text(
    json.dumps(imf_catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)

imf_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://github.com/a15280020511/evidence-data-center/api-center/imf/ticket.schema.json",
    "title": "IMF SDMX 3.0 bounded read-only Intelligence Center ticket",
    "type": "object",
    "additionalProperties": False,
    "required": ["task_id", "provider", "operation", "objective", "parameters", "data_policy", "acceptance"],
    "properties": {
        "task_id": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$"},
        "provider": {"const": "imf"},
        "operation": {"type": "string", "enum": [op["operation_id"] for op in provider["operations"]]},
        "objective": {"type": "string", "minLength": 1, "maxLength": 1000},
        "parameters": {"type": "object", "maxProperties": 12},
        "data_policy": {
            "type": "object", "additionalProperties": False,
            "required": ["classification", "contains_personal_data"],
            "properties": {"classification": {"const": "public"}, "contains_personal_data": {"const": False}},
        },
        "acceptance": {
            "type": "object", "additionalProperties": False,
            "required": ["timeout_seconds", "max_response_bytes"],
            "properties": {
                "timeout_seconds": {"type": "integer", "minimum": 5, "maximum": 120},
                "max_response_bytes": {"type": "integer", "minimum": 1024, "maximum": 20000000},
            },
        },
    },
}
(API / "imf" / "ticket.schema.json").write_text(
    json.dumps(imf_schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
(API / "imf" / "README.md").write_text(
    "# IMF SDMX 3.0\n\n通过 IMF 当前官方 SDMX 3.0 API 读取全球宏观、财政、贸易、价格、货币金融与国际收支统计。\n\n"
    "- Secret：`IMF_API_KEY`\n- 票据前缀：`[intel-imf]`\n- 固定主机：`api.imf.org`\n"
    "- 密钥仅通过 `Ocp-Apim-Subscription-Key` 后端请求头发送。\n"
    "- 每票据一次 GET，不自动翻页或重试，不允许任意 URL、资源类型或请求头。\n",
    encoding="utf-8",
)

intl_tests = API / "international-statistics" / "tests" / "test_international_statistics.py"
text = intl_tests.read_text(encoding="utf-8")
text = text.replace(
    'self.assertEqual(self.mod.build_request("imf", "list-countries", {})[0], "/countries")',
    'self.assertEqual(\n            self.mod.build_request("imf", "get-dataflow", {"agency": "IMF.RES", "flow": "WEO"})[0],\n            "/structure/dataflow/IMF.RES/WEO/%2B",\n        )'
)
intl_tests.write_text(text, encoding="utf-8")

api_tests = API / "tests" / "test_api_catalog.py"
replace_once(
    api_tests,
    '            "wto": "WTO_API_KEY",\n            "faostat": "FAOSTAT_PASSWORD",',
    '            "wto": "WTO_API_KEY",\n            "imf": "IMF_API_KEY",\n            "faostat": "FAOSTAT_PASSWORD",',
)

subprocess.run(["python", str(API / "build_catalog_market_search.py")], check=True)
print(json.dumps({"status": "PASS", "fixes": ["oecd-sdmx-mime", "imf-sdmx-3.0"]}))
