#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "api-center"
WF = ROOT / ".github" / "workflows"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: object) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"expected exactly one match in {path}: {old!r}, got {text.count(old)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# Fix the WTO metadata endpoint. The live data endpoint already works; the indicator
# catalogue is the plural /indicators endpoint.
wto_runtime = API / "international-statistics" / "provider_task.py"
replace_once(wto_runtime, '"indicators": "/indicator",', '"indicators": "/indicators",')
wto_test = API / "international-statistics" / "tests" / "test_international_statistics.py"
replace_once(
    wto_test,
    'self.assertEqual(mod.build_request("wto", "indicators", {})[0], "/indicator")',
    'self.assertEqual(mod.build_request("wto", "indicators", {})[0], "/indicators")',
)

COMMON_ACCEPTANCE = {
    "type": "object",
    "additionalProperties": False,
    "required": ["timeout_seconds", "max_response_bytes"],
    "properties": {
        "timeout_seconds": {"type": "integer", "minimum": 5, "maximum": 120},
        "max_response_bytes": {"type": "integer", "minimum": 1024, "maximum": 20000000},
    },
}
COMMON_DATA_POLICY = {
    "type": "object",
    "additionalProperties": False,
    "required": ["classification", "contains_personal_data"],
    "properties": {
        "classification": {"const": "public"},
        "contains_personal_data": {"const": False},
    },
}

WB_FIELDS = [
    "id", "guid", "display_title", "docdt", "docty", "majdocty", "count",
    "countcode", "lang", "authr", "abstracts", "projectid", "projn", "repnb",
    "repnme", "pdfurl", "txturl", "url", "topicv3", "keywd", "src_cit",
]
WB_FILTER_PROPERTIES = {
    "query": {"type": "string", "minLength": 1, "maxLength": 300},
    "country": {"type": "string", "minLength": 1, "maxLength": 120},
    "language": {"type": "string", "minLength": 1, "maxLength": 80},
    "document_type": {"type": "string", "minLength": 1, "maxLength": 120},
    "project_id": {"type": "string", "pattern": "^[A-Za-z0-9._-]{1,80}$"},
    "report_number": {"type": "string", "pattern": "^[A-Za-z0-9._/-]{1,80}$"},
    "start_date": {"type": "string", "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"},
    "end_date": {"type": "string", "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"},
    "rows": {"type": "integer", "minimum": 1, "maximum": 50},
    "offset": {"type": "integer", "minimum": 0, "maximum": 10000},
    "fields": {
        "type": "array", "minItems": 1, "maxItems": 20, "uniqueItems": True,
        "items": {"type": "string", "enum": WB_FIELDS},
    },
    "sort": {"type": "string", "enum": ["docdt", "display_title", "repnb", "docty"]},
    "order": {"type": "string", "enum": ["asc", "desc"]},
}

def wb_op(operation_id: str, description: str, properties: dict, required: list[str] | None = None, method: str = "GET") -> dict:
    return {
        "operation_id": operation_id,
        "description": description,
        "parameters": list(properties),
        "parameter_schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": properties,
            **({"required": required} if required else {}),
        },
        "result_contract": {
            "provider": "worldbank-documents",
            "official_origin": "https://search.worldbank.org/api/v3/wds",
            "http_method": method,
            "read_only": True,
            "credential_mode": "none",
        },
    }

wb_operations = [
    wb_op("catalog-capabilities", "读取本地 World Bank Documents & Reports 安全能力目录，不访问上游。", {}, method="LOCAL"),
    wb_op("search-documents", "按关键词、国家、语言、文件类型、项目、日期等受约束条件检索世界银行公开文档。", WB_FILTER_PROPERTIES, ["query"]),
    wb_op("get-document", "按 Documents & Reports 文档 ID 读取公开文档元数据。", {
        "document_id": {"type": "string", "pattern": "^[A-Za-z0-9_:-]{1,120}$"},
        "fields": WB_FILTER_PROPERTIES["fields"],
    }, ["document_id"]),
    wb_op("project-documents", "按世界银行项目 ID 检索公开项目文件。", {
        "project_id": WB_FILTER_PROPERTIES["project_id"], "rows": WB_FILTER_PROPERTIES["rows"],
        "offset": WB_FILTER_PROPERTIES["offset"], "fields": WB_FILTER_PROPERTIES["fields"],
        "start_date": WB_FILTER_PROPERTIES["start_date"], "end_date": WB_FILTER_PROPERTIES["end_date"],
    }, ["project_id"]),
    wb_op("report-documents", "按报告编号检索公开报告及卷册元数据。", {
        "report_number": WB_FILTER_PROPERTIES["report_number"], "rows": WB_FILTER_PROPERTIES["rows"],
        "offset": WB_FILTER_PROPERTIES["offset"], "fields": WB_FILTER_PROPERTIES["fields"],
    }, ["report_number"]),
    wb_op("recent-documents", "按日期范围读取最新公开文档。", {
        "start_date": WB_FILTER_PROPERTIES["start_date"], "end_date": WB_FILTER_PROPERTIES["end_date"],
        "query": WB_FILTER_PROPERTIES["query"], "rows": WB_FILTER_PROPERTIES["rows"],
        "offset": WB_FILTER_PROPERTIES["offset"], "fields": WB_FILTER_PROPERTIES["fields"],
        "sort": WB_FILTER_PROPERTIES["sort"], "order": WB_FILTER_PROPERTIES["order"],
    }, ["start_date"]),
    wb_op("document-facets", "读取受约束检索结果的国家、语言、文件类型、主题或行业 Facet。", {
        "query": WB_FILTER_PROPERTIES["query"],
        "facets": {
            "type": "array", "minItems": 1, "maxItems": 6, "uniqueItems": True,
            "items": {"type": "string", "enum": ["count_exact", "lang_exact", "docty_exact", "majdocty_exact", "topic_exact", "sectr_exact"]},
        },
        "start_date": WB_FILTER_PROPERTIES["start_date"], "end_date": WB_FILTER_PROPERTIES["end_date"],
    }, ["facets"]),
]

wb_catalog = {
    "schema_version": "worldbank-documents-provider-catalog-v1",
    "secret_values_exposed": False,
    "replaced_legacy_connectors": [],
    "providers": [{
        "provider_id": "worldbank-documents",
        "display_name": "World Bank Documents & Reports API",
        "description": "检索世界银行 Documents & Reports 官方公开报告、项目文件、研究论文、董事会文件和元数据。",
        "enabled": True,
        "ticket_prefix": "[intel-worldbank-docs]",
        "required_secret_environment_variable": "",
        "catalog_policy": "固定访问 search.worldbank.org/api/v3/wds；仅返回公开元数据和官方文档链接，不抓取或批量下载文档正文。",
        "execution_policy": "每张票据最多一次 HTTPS GET；不自动重试或翻页；每页最多50条、offset最多10000；字段、Facet、筛选条件均采用固定白名单。",
        "official_documentation": "https://documents.worldbank.org/en/publication/documents-reports/api",
        "official_origin": "https://search.worldbank.org/api/v3/wds",
        "limits": {
            "requests_per_ticket_max": 1, "provider_concurrency_max": 1,
            "records_per_ticket_max": 50, "offset_max": 10000,
            "fields_per_ticket_max": 20, "facets_per_ticket_max": 6,
            "timeout_seconds_max": 120, "max_response_bytes": 20000000,
            "fixed_api_host": "search.worldbank.org", "fixed_api_prefix": "/api/v3/wds",
            "document_body_download_allowed": False, "automatic_retry_allowed": False,
            "automatic_pagination_allowed": False, "arbitrary_urls_allowed": False,
            "arbitrary_hosts_allowed": False, "arbitrary_paths_allowed": False,
            "arbitrary_headers_allowed": False, "redirects_allowed": False,
            "write_operations_allowed": False, "personal_data_allowed": False,
            "secret_values_exposed": False,
        },
        "operations": wb_operations,
    }],
}
write_json(API / "worldbank-documents" / "provider-catalog.json", wb_catalog)
write_json(API / "worldbank-documents" / "ticket.schema.json", {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://github.com/a15280020511/evidence-data-center/api-center/worldbank-documents/ticket.schema.json",
    "title": "World Bank Documents & Reports bounded read-only Intelligence Center ticket",
    "type": "object", "additionalProperties": False,
    "required": ["task_id", "provider", "operation", "objective", "parameters", "data_policy", "acceptance"],
    "properties": {
        "task_id": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$"},
        "provider": {"const": "worldbank-documents"},
        "operation": {"type": "string", "enum": [op["operation_id"] for op in wb_operations]},
        "objective": {"type": "string", "minLength": 1, "maxLength": 1000},
        "parameters": {"type": "object", "maxProperties": 16},
        "data_policy": COMMON_DATA_POLICY,
        "acceptance": COMMON_ACCEPTANCE,
    },
})
write(API / "worldbank-documents" / "requirements.txt", "requests>=2.32,<3\n")
write(API / "worldbank-documents" / "README.md", textwrap.dedent("""\
# World Bank Documents & Reports API

固定访问世界银行官方公开检索端点 `https://search.worldbank.org/api/v3/wds`，无需 API Key。

票据前缀：`[intel-worldbank-docs]`。

开放 7 项只读能力：本地目录、综合检索、按文档 ID、按项目 ID、按报告编号、按日期范围及 Facet 查询。每张票据最多一次 GET，不自动翻页或重试，每次最多 50 条。仅保存公开元数据和官方链接，不批量下载 PDF/TXT 正文。
"""))

write(API / "worldbank-documents" / "worldbank_documents_task.py", textwrap.dedent(r'''\
#!/usr/bin/env python3
"""Bounded read-only World Bank Documents & Reports execution."""
from __future__ import annotations
import json
import re
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any, Mapping
import requests
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from managed_provider_runtime import bounded_int, bytes_sha, finish_execution, load_json, provider_row, run_cli, utc_now, validate_ticket
SCHEMA_PATH = HERE / "ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"
ORIGIN = "https://search.worldbank.org"
PATH = "/api/v3/wds"
SAFE_FIELDS = {"id","guid","display_title","docdt","docty","majdocty","count","countcode","lang","authr","abstracts","projectid","projn","repnb","repnme","pdfurl","txturl","url","topicv3","keywd","src_cit"}
SAFE_FACETS = {"count_exact","lang_exact","docty_exact","majdocty_exact","topic_exact","sectr_exact"}
TOKEN_RE = re.compile(r"^[A-Za-z0-9_./:-]{1,120}$")
DEFAULT_FIELDS = ["id","display_title","docdt","docty","count","lang","projectid","repnb","pdfurl","url","abstracts"]

def text(value: Any, name: str, maximum: int = 300) -> str:
    value = str(value or "").strip()
    if not value or len(value) > maximum or any(ord(ch) < 32 for ch in value):
        raise ValueError(f"{name} is invalid")
    return value

def date_value(value: Any, name: str) -> str | None:
    if value in (None, ""):
        return None
    value = str(value)
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be YYYY-MM-DD") from exc
    return value

def fields(value: Any) -> list[str]:
    if value in (None, []):
        return DEFAULT_FIELDS
    if not isinstance(value, list) or not 1 <= len(value) <= 20:
        raise ValueError("fields must contain 1 to 20 names")
    result = [str(v) for v in value]
    if len(result) != len(set(result)) or any(v not in SAFE_FIELDS for v in result):
        raise ValueError("fields contains an unsupported or duplicate field")
    return result

def common_query(p: Mapping[str, Any]) -> list[tuple[str,str]]:
    query: list[tuple[str,str]] = [("format","json"), ("rows",str(bounded_int(p.get("rows"),default=10,minimum=1,maximum=50,name="rows"))), ("os",str(bounded_int(p.get("offset"),default=0,minimum=0,maximum=10000,name="offset"))), ("fl",",".join(fields(p.get("fields"))))]
    mapping = {"query":"qterm","country":"count_exact","language":"lang_exact","document_type":"docty_exact","project_id":"projectid","report_number":"repnb"}
    for source,target in mapping.items():
        if p.get(source) not in (None, ""):
            value = text(p[source], source, 300 if source == "query" else 120)
            if source in {"project_id","report_number"} and not TOKEN_RE.fullmatch(value):
                raise ValueError(f"{source} is invalid")
            query.append((target,value))
    start,end = date_value(p.get("start_date"),"start_date"), date_value(p.get("end_date"),"end_date")
    if start and end and start > end:
        raise ValueError("start_date must not exceed end_date")
    if start: query.append(("strdate",start))
    if end: query.append(("enddate",end))
    sort = str(p.get("sort") or "")
    if sort:
        if sort not in {"docdt","display_title","repnb","docty"}: raise ValueError("sort is invalid")
        query.append(("sort",sort))
    order = str(p.get("order") or "")
    if order:
        if order not in {"asc","desc"}: raise ValueError("order is invalid")
        query.append(("order",order))
    return query

def build_request(operation: str, p: Mapping[str,Any]) -> list[tuple[str,str]] | None:
    if operation == "catalog-capabilities":
        if p: raise ValueError("catalog-capabilities accepts no parameters")
        return None
    if operation == "search-documents":
        if not p.get("query"): raise ValueError("query is required")
        return common_query(p)
    if operation == "get-document":
        value = text(p.get("document_id"),"document_id",120)
        if not re.fullmatch(r"^[A-Za-z0-9_:-]{1,120}$",value): raise ValueError("document_id is invalid")
        return [("format","json"),("id",value),("rows","5"),("os","0"),("fl",",".join(fields(p.get("fields"))))]
    if operation == "project-documents":
        if not p.get("project_id"): raise ValueError("project_id is required")
        return common_query(p)
    if operation == "report-documents":
        if not p.get("report_number"): raise ValueError("report_number is required")
        return common_query(p)
    if operation == "recent-documents":
        if not p.get("start_date"): raise ValueError("start_date is required")
        q = common_query(p)
        if not any(k == "sort" for k,_ in q): q.append(("sort","docdt"))
        if not any(k == "order" for k,_ in q): q.append(("order","desc"))
        return q
    if operation == "document-facets":
        raw = p.get("facets")
        if not isinstance(raw,list) or not 1 <= len(raw) <= 6: raise ValueError("facets must contain 1 to 6 values")
        vals = [str(v) for v in raw]
        if len(vals) != len(set(vals)) or any(v not in SAFE_FACETS for v in vals): raise ValueError("facets contains an unsupported value")
        q = [("format","json"),("rows","0"),("os","0"),("fct",",".join(vals))]
        if p.get("query"): q.append(("qterm",text(p["query"],"query")))
        start,end = date_value(p.get("start_date"),"start_date"),date_value(p.get("end_date"),"end_date")
        if start and end and start > end: raise ValueError("start_date must not exceed end_date")
        if start: q.append(("strdate",start))
        if end: q.append(("enddate",end))
        return q
    raise ValueError(f"unsupported operation: {operation}")

def count_rows(payload: Any) -> int:
    if isinstance(payload, Mapping):
        docs = payload.get("documents")
        if isinstance(docs, list): return len(docs)
        if isinstance(docs, Mapping): return len(docs)
        for key in ("total","count"):
            if isinstance(payload.get(key),int): return int(payload[key])
        return 1
    if isinstance(payload,list): return len(payload)
    return 0

def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True,exist_ok=True)
    ticket=load_json(ticket_path); validate_ticket(ticket,schema_path=SCHEMA_PATH,catalog_path=CATALOG_PATH)
    operation=str(ticket["operation"]); params=dict(ticket.get("parameters") or {}); acceptance=dict(ticket["acceptance"])
    timeout=bounded_int(acceptance.get("timeout_seconds"),default=30,minimum=5,maximum=120,name="timeout_seconds")
    max_bytes=bounded_int(acceptance.get("max_response_bytes"),default=10000000,minimum=1024,maximum=20000000,name="max_response_bytes")
    started_at,started_perf=utc_now(),time.perf_counter(); status="INTEL_WORLDBANK_DOCUMENTS_FAILED"; failure=None; snapshot=None
    metadata={"upstream_called":False,"api_origin":"search.worldbank.org","credential_mode":"none","requests_per_ticket_max":1,"automatic_retry":False,"automatic_pagination":False,"document_body_downloaded":False,"secret_values_exposed":False}
    try:
        query=build_request(operation,params)
        if query is None: snapshot={"provider":provider_row(CATALOG_PATH)}
        else:
            response=requests.get(ORIGIN+PATH,params=query,headers={"Accept":"application/json","User-Agent":"intelligence-center-worldbank-documents/1"},timeout=timeout,allow_redirects=False)
            raw=bytes(response.content or b""); metadata.update({"upstream_called":True,"http_status":response.status_code,"content_type":response.headers.get("Content-Type",""),"request_path":PATH,"query_parameter_names":sorted({k for k,_ in query}),"response_bytes_raw":len(raw)})
            if len(raw)>max_bytes: raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
            if not response.ok: raise RuntimeError(f"World Bank Documents HTTP {response.status_code}: {raw[:1200].decode('utf-8',errors='replace')}")
            try: payload=response.json()
            except ValueError as exc: raise RuntimeError("World Bank Documents returned invalid JSON") from exc
            stored=(json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode()
            if len(stored)>max_bytes: raise RuntimeError("sanitized response exceeds max_response_bytes")
            (output_dir/"response.json").write_bytes(stored); rows=count_rows(payload)
            snapshot={"provider":"worldbank-documents","operation":operation,"row_count":rows,"data":payload}
            metadata.update({"response_bytes":len(stored),"response_sha256":bytes_sha(stored),"row_count":rows})
        status="INTEL_WORLDBANK_DOCUMENTS_COMPLETED"
    except Exception as exc: failure={"type":type(exc).__name__,"message":str(exc)[:2000]}
    return finish_execution(ticket=ticket,output_dir=output_dir,status=status,snapshot=snapshot,metadata=metadata,failure=failure,started_at=started_at,started_perf=started_perf,schema_prefix="worldbank-documents")
if __name__ == "__main__":
    raise SystemExit(run_cli(execute=execute,ticket_prefix="[intel-worldbank-docs]",schema_path=SCHEMA_PATH,catalog_path=CATALOG_PATH,status_schema="worldbank-documents-ticket-status-v1",display_name="World Bank Documents & Reports"))
'''))

SDMX_COMPONENT = {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}$"}
SDMX_VERSION = {"type": "string", "pattern": "^(?:latest|[0-9]+(?:\\.[0-9]+){0,3})$"}

def bis_op(operation_id: str, description: str, properties: dict, required: list[str] | None = None, method: str = "GET") -> dict:
    return {
        "operation_id": operation_id, "description": description, "parameters": list(properties),
        "parameter_schema": {"type":"object","additionalProperties":False,"properties":properties, **({"required":required} if required else {})},
        "result_contract": {"provider":"bis","official_origin":"https://stats.bis.org/api/v2","http_method":method,"read_only":True,"credential_mode":"none"},
    }

bis_operations = [
    bis_op("catalog-capabilities","读取本地 BIS SDMX 安全能力目录，不访问上游。",{},method="LOCAL"),
    bis_op("list-dataflows","读取 BIS 公开 SDMX 数据流目录。",{"references":{"type":"string","enum":["none","parents","ancestors","children","descendants","all"]}}),
    bis_op("get-dataflow","读取指定 BIS 数据流定义。",{"agency":SDMX_COMPONENT,"flow":SDMX_COMPONENT,"version":SDMX_VERSION,"references":{"type":"string","enum":["none","parents","ancestors","children","descendants","all"]}},["flow"]),
    bis_op("get-datastructure","读取指定 BIS 数据结构定义。",{"agency":SDMX_COMPONENT,"structure_id":SDMX_COMPONENT,"version":SDMX_VERSION,"references":{"type":"string","enum":["none","parents","ancestors","children","descendants","all"]}},["structure_id"]),
    bis_op("get-codelist","读取指定 BIS 代码表。",{"agency":SDMX_COMPONENT,"codelist_id":SDMX_COMPONENT,"version":SDMX_VERSION,"references":{"type":"string","enum":["none","parents","ancestors","children","descendants","all"]}},["codelist_id"]),
    bis_op("get-conceptscheme","读取指定 BIS 概念表。",{"agency":SDMX_COMPONENT,"conceptscheme_id":SDMX_COMPONENT,"version":SDMX_VERSION,"references":{"type":"string","enum":["none","parents","ancestors","children","descendants","all"]}},["conceptscheme_id"]),
    bis_op("get-data","按 SDMX 数据流、序列键和时间范围读取 BIS 统计。",{
        "context":{"type":"string","enum":["dataflow","datastructure"]},"agency":SDMX_COMPONENT,"flow":SDMX_COMPONENT,"version":SDMX_VERSION,
        "key":{"type":"string","pattern":"^[A-Za-z0-9*+.,_@-]{1,500}$"},"start_period":{"type":"string","pattern":"^[0-9]{4}(?:-(?:M[0-9]{2}|Q[1-4]|S[12]))?$"},"end_period":{"type":"string","pattern":"^[0-9]{4}(?:-(?:M[0-9]{2}|Q[1-4]|S[12]))?$"},
        "format":{"type":"string","enum":["json","csv"]},"detail":{"type":"string","enum":["full","dataonly","serieskeysonly","nodata"]},"dimension_at_observation":{"type":"string","enum":["AllDimensions","TimeDimension","MeasureDimension"]},
    },["flow","key"]),
    bis_op("get-availability","读取指定 BIS 数据集和序列键的数据可用性约束。",{
        "context":{"type":"string","enum":["dataflow","datastructure"]},"agency":SDMX_COMPONENT,"flow":SDMX_COMPONENT,"version":SDMX_VERSION,"key":{"type":"string","pattern":"^[A-Za-z0-9*+.,_@-]{1,500}$"},"component_id":{"type":"string","pattern":"^(?:[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}|all)$"},
    },["flow","key"]),
]

bis_catalog = {
    "schema_version":"bis-provider-catalog-v1","secret_values_exposed":False,"replaced_legacy_connectors":[],
    "providers":[{
        "provider_id":"bis","display_name":"Bank for International Settlements SDMX API","description":"读取国际清算银行公开的国际银行、全球流动性、信贷、汇率、衍生品、消费价格和央行资产等统计与结构元数据。","enabled":True,"ticket_prefix":"[intel-bis]","required_secret_environment_variable":"",
        "catalog_policy":"固定访问 stats.bis.org/api/v2；仅开放 SDMX v2.1 数据、可用性和结构查询；禁止任意 URL、主机、请求头和批量下载。",
        "execution_policy":"每张票据最多一次 HTTPS GET；不自动重试或翻页；序列键和时间范围必须显式提供；响应最大20MB。",
        "official_documentation":"https://stats.bis.org/api-doc/v2/","official_origin":"https://stats.bis.org/api/v2",
        "limits":{"requests_per_ticket_max":1,"provider_concurrency_max":1,"timeout_seconds_max":120,"max_response_bytes":20000000,"key_length_max":500,"fixed_api_host":"stats.bis.org","fixed_api_prefix":"/api/v2","sdmx_rest_version":"2.1.0","automatic_retry_allowed":False,"automatic_pagination_allowed":False,"arbitrary_urls_allowed":False,"arbitrary_hosts_allowed":False,"arbitrary_paths_allowed":False,"arbitrary_headers_allowed":False,"bulk_download_allowed":False,"redirects_allowed":False,"write_operations_allowed":False,"personal_data_allowed":False,"source_citation_required":True,"secret_values_exposed":False},
        "operations":bis_operations,
    }],
}
write_json(API / "bis" / "provider-catalog.json", bis_catalog)
write_json(API / "bis" / "ticket.schema.json", {
    "$schema":"https://json-schema.org/draft/2020-12/schema","$id":"https://github.com/a15280020511/evidence-data-center/api-center/bis/ticket.schema.json","title":"BIS SDMX bounded read-only Intelligence Center ticket","type":"object","additionalProperties":False,
    "required":["task_id","provider","operation","objective","parameters","data_policy","acceptance"],
    "properties":{"task_id":{"type":"string","pattern":"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$"},"provider":{"const":"bis"},"operation":{"type":"string","enum":[op["operation_id"] for op in bis_operations]},"objective":{"type":"string","minLength":1,"maxLength":1000},"parameters":{"type":"object","maxProperties":16},"data_policy":COMMON_DATA_POLICY,"acceptance":COMMON_ACCEPTANCE},
})
write(API / "bis" / "requirements.txt", "requests>=2.32,<3\n")
write(API / "bis" / "README.md", textwrap.dedent("""\
# BIS SDMX API

固定访问国际清算银行官方 `https://stats.bis.org/api/v2`，无需 API Key。票据前缀为 `[intel-bis]`。

开放 8 项只读能力：能力目录、数据流、数据流定义、数据结构、代码表、概念表、数据读取和数据可用性。每票据最多一次 GET，不自动翻页、重试或批量下载。引用 BIS 数据时必须注明 BIS 为来源。
"""))

write(API / "bis" / "bis_task.py", textwrap.dedent(r'''\
#!/usr/bin/env python3
"""Bounded read-only BIS SDMX API execution."""
from __future__ import annotations
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import quote
import requests
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from managed_provider_runtime import bounded_int,bytes_sha,finish_execution,load_json,provider_row,run_cli,utc_now,validate_ticket
SCHEMA_PATH=HERE/"ticket.schema.json"; CATALOG_PATH=HERE/"provider-catalog.json"; ORIGIN="https://stats.bis.org"; PREFIX="/api/v2"
COMPONENT_RE=re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}$"); VERSION_RE=re.compile(r"^(?:latest|[0-9]+(?:\.[0-9]+){0,3})$"); KEY_RE=re.compile(r"^[A-Za-z0-9*+.,_@-]{1,500}$"); PERIOD_RE=re.compile(r"^[0-9]{4}(?:-(?:M[0-9]{2}|Q[1-4]|S[12]))?$")
def comp(value:Any,name:str,default:str|None=None)->str:
    value=str(value or default or "")
    if not COMPONENT_RE.fullmatch(value): raise ValueError(f"{name} is invalid")
    return quote(value,safe="._@-")
def version(value:Any)->str:
    value=str(value or "latest")
    if not VERSION_RE.fullmatch(value): raise ValueError("version is invalid")
    return value
def refs(value:Any)->str:
    value=str(value or "none")
    if value not in {"none","parents","ancestors","children","descendants","all"}: raise ValueError("references is invalid")
    return value
def build_request(operation:str,p:Mapping[str,Any])->tuple[str|None,list[tuple[str,str]],str]:
    if operation=="catalog-capabilities":
        if p: raise ValueError("catalog-capabilities accepts no parameters")
        return None,[],"json"
    if operation=="list-dataflows": return f"{PREFIX}/structure/dataflow/all/all/latest",[("references",refs(p.get("references")))],"structure-json"
    structures={"get-dataflow":("dataflow","flow"),"get-datastructure":("datastructure","structure_id"),"get-codelist":("codelist","codelist_id"),"get-conceptscheme":("conceptscheme","conceptscheme_id")}
    if operation in structures:
        typ,name=structures[operation]; path=f"{PREFIX}/structure/{typ}/{comp(p.get('agency'),'agency','BIS')}/{comp(p.get(name),name)}/{version(p.get('version'))}"
        return path,[("references",refs(p.get("references")))],"structure-json"
    if operation in {"get-data","get-availability"}:
        context=str(p.get("context") or "dataflow")
        if context not in {"dataflow","datastructure"}: raise ValueError("context is invalid")
        agency=comp(p.get("agency"),"agency","BIS"); flow=comp(p.get("flow"),"flow"); ver=version(p.get("version")); key=str(p.get("key") or "")
        if not KEY_RE.fullmatch(key): raise ValueError("key is invalid")
        safe_key=quote(key,safe="*+.,_@-")
        if operation=="get-availability":
            component=str(p.get("component_id") or "all")
            if component!="all" and not COMPONENT_RE.fullmatch(component): raise ValueError("component_id is invalid")
            return f"{PREFIX}/availability/{context}/{agency}/{flow}/{ver}/{safe_key}/{quote(component,safe='._@-')}",[],"structure-json"
        fmt=str(p.get("format") or "json")
        if fmt not in {"json","csv"}: raise ValueError("format is invalid")
        query=[]
        for source,target in (("start_period","startPeriod"),("end_period","endPeriod")):
            if p.get(source) not in (None,""):
                value=str(p[source])
                if not PERIOD_RE.fullmatch(value): raise ValueError(f"{source} is invalid")
                query.append((target,value))
        start=dict(query).get("startPeriod"); end=dict(query).get("endPeriod")
        if start and end and start>end: raise ValueError("start_period must not exceed end_period")
        detail=str(p.get("detail") or "full")
        if detail not in {"full","dataonly","serieskeysonly","nodata"}: raise ValueError("detail is invalid")
        query.append(("detail",detail))
        dim=p.get("dimension_at_observation")
        if dim not in (None,""):
            if dim not in {"AllDimensions","TimeDimension","MeasureDimension"}: raise ValueError("dimension_at_observation is invalid")
            query.append(("dimensionAtObservation",str(dim)))
        return f"{PREFIX}/data/{context}/{agency}/{flow}/{ver}/{safe_key}",query,fmt
    raise ValueError(f"unsupported operation: {operation}")
def row_count(payload:Any)->int:
    if isinstance(payload,list): return len(payload)
    if isinstance(payload,Mapping):
        for key in ("data","dataSets","series","structures"):
            value=payload.get(key)
            if isinstance(value,list): return len(value)
            if isinstance(value,Mapping): return len(value)
        return 1
    return 0
def execute(ticket_path:Path,output_dir:Path)->int:
    output_dir.mkdir(parents=True,exist_ok=True); ticket=load_json(ticket_path); validate_ticket(ticket,schema_path=SCHEMA_PATH,catalog_path=CATALOG_PATH)
    operation=str(ticket["operation"]); params=dict(ticket.get("parameters") or {}); acceptance=dict(ticket["acceptance"])
    timeout=bounded_int(acceptance.get("timeout_seconds"),default=45,minimum=5,maximum=120,name="timeout_seconds"); max_bytes=bounded_int(acceptance.get("max_response_bytes"),default=10000000,minimum=1024,maximum=20000000,name="max_response_bytes")
    started_at,started_perf=utc_now(),time.perf_counter(); status="INTEL_BIS_FAILED"; failure=None; snapshot=None
    metadata={"upstream_called":False,"api_origin":"stats.bis.org","credential_mode":"none","requests_per_ticket_max":1,"automatic_retry":False,"automatic_pagination":False,"source_citation_required":True,"secret_values_exposed":False}
    try:
        path,query,fmt=build_request(operation,params)
        if path is None: snapshot={"provider":provider_row(CATALOG_PATH)}
        else:
            accept={"structure-json":"application/vnd.sdmx.structure+json;version=2.0.0","json":"application/vnd.sdmx.data+json;version=2.0.0","csv":"text/csv"}[fmt]
            response=requests.get(ORIGIN+path,params=query,headers={"Accept":accept,"User-Agent":"intelligence-center-bis/1"},timeout=timeout,allow_redirects=False)
            raw=bytes(response.content or b""); metadata.update({"upstream_called":True,"http_status":response.status_code,"content_type":response.headers.get("Content-Type",""),"request_path":path,"query_parameter_names":sorted({k for k,_ in query}),"response_bytes_raw":len(raw)})
            if len(raw)>max_bytes: raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
            if not response.ok: raise RuntimeError(f"BIS HTTP {response.status_code}: {raw[:1200].decode('utf-8',errors='replace')}")
            if fmt=="csv":
                (output_dir/"response.csv").write_bytes(raw); rows=max(0,len(raw.splitlines())-1); stored=raw; snapshot={"provider":"bis","operation":operation,"row_count":rows,"artifact_file":"response.csv"}
            else:
                try: payload=response.json()
                except ValueError as exc: raise RuntimeError(f"BIS returned non-JSON content-type {response.headers.get('Content-Type','unknown')}") from exc
                stored=(json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode();
                if len(stored)>max_bytes: raise RuntimeError("sanitized response exceeds max_response_bytes")
                (output_dir/"response.json").write_bytes(stored); rows=row_count(payload); snapshot={"provider":"bis","operation":operation,"row_count":rows,"data":payload}
            metadata.update({"response_bytes":len(stored),"response_sha256":bytes_sha(stored),"row_count":rows})
        status="INTEL_BIS_COMPLETED"
    except Exception as exc: failure={"type":type(exc).__name__,"message":str(exc)[:2000]}
    return finish_execution(ticket=ticket,output_dir=output_dir,status=status,snapshot=snapshot,metadata=metadata,failure=failure,started_at=started_at,started_perf=started_perf,schema_prefix="bis")
if __name__=="__main__": raise SystemExit(run_cli(execute=execute,ticket_prefix="[intel-bis]",schema_path=SCHEMA_PATH,catalog_path=CATALOG_PATH,status_schema="bis-ticket-status-v1",display_name="BIS SDMX"))
'''))


def ticket_workflow(provider: str, display: str, prefix: str, script: str, status: str, timeout: int = 15) -> str:
    safe = provider.replace("-", "_")
    return textwrap.dedent(f'''\
name: Managed {display} Intelligence Center

on:
  issues:
    types: [opened, reopened]

permissions:
  contents: read
  issues: write
  actions: read

concurrency:
  group: intel-{provider}-global
  cancel-in-progress: false

jobs:
  execute-{provider}:
    if: >-
      github.actor == github.repository_owner &&
      startsWith(github.event.issue.title, '{prefix}')
    runs-on: ubuntu-24.04
    timeout-minutes: {timeout}
    env:
      GH_TOKEN: ${{{{ secrets.GITHUB_TOKEN }}}}
      GITHUB_TOKEN: ${{{{ secrets.GITHUB_TOKEN }}}}
      ISSUE_NUMBER: ${{{{ github.event.issue.number }}}}
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
            api-center/{provider}/requirements.txt
      - name: Install pinned dependencies
        run: |
          python -m pip install --disable-pip-version-check --no-input \\
            -r api-center/requirements.txt \\
            -r api-center/{provider}/requirements.txt
          python -m pip check
      - name: Compile provider
        run: python -m py_compile api-center/managed_provider_runtime.py api-center/{provider}/{script}
      - name: Parse and authorize ticket
        id: prepare
        continue-on-error: true
        run: python api-center/{provider}/{script} prepare --event-path "$GITHUB_EVENT_PATH" --output-dir {safe}-artifacts
      - name: Comment accepted ticket
        if: steps.prepare.outputs.accepted == 'true'
        run: |
          python api-center/{provider}/{script} render --output-dir {safe}-artifacts --phase accepted > provider-comment.md
          gh api --method POST "repos/${{{{ GITHUB_REPOSITORY }}}}/issues/${{{{ ISSUE_NUMBER }}}}/comments" -F body=@provider-comment.md
      - name: Comment rejected ticket
        if: steps.prepare.outputs.accepted != 'true'
        run: |
          python api-center/{provider}/{script} render --output-dir {safe}-artifacts --phase rejected > provider-comment.md
          gh api --method POST "repos/${{{{ GITHUB_REPOSITORY }}}}/issues/${{{{ ISSUE_NUMBER }}}}/comments" -F body=@provider-comment.md
      - name: Execute one bounded request
        id: execute
        if: steps.prepare.outputs.accepted == 'true'
        continue-on-error: true
        run: python api-center/{provider}/{script} execute --ticket {safe}-artifacts/ticket.json --output-dir {safe}-artifacts
      - name: Upload evidence
        id: upload
        if: always()
        continue-on-error: true
        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02
        with:
          name: {provider}-ticket-${{{{ github.event.issue.number }}}}-${{{{ github.run_id }}}}
          path: {safe}-artifacts/
          if-no-files-found: error
          retention-days: 30
      - name: Publish verified result or structured failure
        if: always() && steps.prepare.outputs.accepted == 'true'
        env:
          ARTIFACT_URL: ${{{{ steps.upload.outputs.artifact-url }}}}
        run: |
          python api-center/{provider}/{script} render --output-dir {safe}-artifacts --phase completed --artifact-url "$ARTIFACT_URL" > provider-comment.md
          gh api --method POST "repos/${{{{ GITHUB_REPOSITORY }}}}/issues/${{{{ ISSUE_NUMBER }}}}/comments" -F body=@provider-comment.md
      - name: Mark rejected or failed execution
        if: >-
          always() &&
          (steps.prepare.outputs.accepted != 'true' ||
           steps.execute.outputs.status != '{status}' ||
           steps.upload.outcome != 'success')
        run: exit 1
''')

write(WF / "worldbank-documents-api-ticket.yml", ticket_workflow("worldbank-documents","World Bank Documents & Reports","[intel-worldbank-docs]","worldbank_documents_task.py","INTEL_WORLDBANK_DOCUMENTS_COMPLETED"))
write(WF / "bis-api-ticket.yml", ticket_workflow("bis","BIS SDMX","[intel-bis]","bis_task.py","INTEL_BIS_COMPLETED"))

write(WF / "worldbank-bis-provider-validate.yml", textwrap.dedent("""\
name: Validate World Bank Documents and BIS Providers

on:
  pull_request:
    paths:
      - "api-center/worldbank-documents/**"
      - "api-center/bis/**"
      - "api-center/international-statistics/**"
      - "api-center/build_catalog_market_search.py"
      - ".github/workflows/worldbank-documents-api-ticket.yml"
      - ".github/workflows/bis-api-ticket.yml"
      - ".github/workflows/worldbank-bis-provider-validate.yml"
  push:
    branches: [main]
    paths:
      - "api-center/worldbank-documents/**"
      - "api-center/bis/**"
      - "api-center/international-statistics/**"
      - "api-center/build_catalog_market_search.py"
      - ".github/workflows/worldbank-documents-api-ticket.yml"
      - ".github/workflows/bis-api-ticket.yml"
      - ".github/workflows/worldbank-bis-provider-validate.yml"
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
          python -m pip install --disable-pip-version-check --no-input -r api-center/requirements.txt -r api-center/worldbank-documents/requirements.txt -r api-center/bis/requirements.txt
          python -m pip check
      - name: Compile and validate contracts
        run: |
          python -m py_compile api-center/worldbank-documents/worldbank_documents_task.py api-center/bis/bis_task.py api-center/international-statistics/provider_task.py
          python - <<'PY'
          import importlib.util, json
          from pathlib import Path
          from jsonschema import Draft202012Validator
          root=Path('api-center')
          expected={'worldbank-documents':7,'bis':8}
          for provider,count in expected.items():
              row=json.loads((root/provider/'provider-catalog.json').read_text())['providers'][0]
              schema=json.loads((root/provider/'ticket.schema.json').read_text())
              Draft202012Validator.check_schema(schema)
              assert row['provider_id']==provider and len(row['operations'])==count
              assert row['required_secret_environment_variable']==''
              assert row['limits']['requests_per_ticket_max']==1
              assert row['limits']['automatic_retry_allowed'] is False
              assert row['limits']['automatic_pagination_allowed'] is False
              assert row['limits']['write_operations_allowed'] is False
              assert all(op['result_contract']['read_only'] is True for op in row['operations'])
          spec=importlib.util.spec_from_file_location('wto',root/'international-statistics/provider_task.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
          assert mod.build_request('wto','indicators',{})[0]=='/indicators'
          print(json.dumps({'status':'PASS','providers':2,'operations':15,'wto_indicator_path':'/indicators'}))
          PY
          git diff --check
"""))

# Register both providers in the deterministic catalog builder.
builder = API / "build_catalog_market_search.py"
replace_once(builder, 'IMF_CATALOG = HERE / "imf/provider-catalog.json"\nADB_CATALOG', 'IMF_CATALOG = HERE / "imf/provider-catalog.json"\nWORLDBANK_DOCUMENTS_CATALOG = HERE / "worldbank-documents/provider-catalog.json"\nBIS_CATALOG = HERE / "bis/provider-catalog.json"\nADB_CATALOG')
replace_once(builder, '    "imf": 6,\n    "adb": 8,', '    "imf": 6,\n    "worldbank-documents": 7,\n    "bis": 8,\n    "adb": 8,')
replace_once(builder, '    IMF_CATALOG,\n    ADB_CATALOG,', '    IMF_CATALOG,\n    WORLDBANK_DOCUMENTS_CATALOG,\n    BIS_CATALOG,\n    ADB_CATALOG,')
replace_once(builder, '        "imf/provider-catalog.json",\n        "adb/provider-catalog.json",', '        "imf/provider-catalog.json",\n        "worldbank-documents/provider-catalog.json",\n        "bis/provider-catalog.json",\n        "adb/provider-catalog.json",')

catalog_test = API / "tests" / "test_api_catalog.py"
replace_once(catalog_test, '    "imf": 6,\n    "adb": 8,', '    "imf": 6,\n    "worldbank-documents": 7,\n    "bis": 8,\n    "adb": 8,')
replace_once(catalog_test, 'self.assertEqual(catalog["managed_provider_count"], 45)', 'self.assertEqual(catalog["managed_provider_count"], 47)')
replace_once(catalog_test, 'self.assertEqual(catalog["enabled_managed_provider_count"], 45)', 'self.assertEqual(catalog["enabled_managed_provider_count"], 47)')
replace_once(catalog_test, 'self.assertEqual(catalog["managed_operation_count"], 472)', 'self.assertEqual(catalog["managed_operation_count"], 487)')

cap_test = API / "tests" / "test_capability_maximization.py"
replace_once(cap_test, '            472,\n', '            487,\n')
replace_once(cap_test, '            "imf": 6,\n            "adb": 8,', '            "imf": 6,\n            "worldbank-documents": 7,\n            "bis": 8,\n            "adb": 8,')

catalog_wf = WF / "api-catalog-validate.yml"
replace_once(catalog_wf, '            -r api-center/imf/requirements.txt \\\n            -r api-center/adb/requirements.txt', '            -r api-center/imf/requirements.txt \\\n            -r api-center/worldbank-documents/requirements.txt \\\n            -r api-center/bis/requirements.txt \\\n            -r api-center/adb/requirements.txt')
replace_once(catalog_wf, "assert catalog['managed_provider_count'] == len(providers) == 45", "assert catalog['managed_provider_count'] == len(providers) == 47")
replace_once(catalog_wf, "assert catalog['enabled_managed_provider_count'] == 45", "assert catalog['enabled_managed_provider_count'] == 47")
replace_once(catalog_wf, "assert catalog['managed_operation_count'] == 472", "assert catalog['managed_operation_count'] == 487")
replace_once(catalog_wf, "              'managed_providers': 45,\n              'managed_operations': 472,", "              'managed_providers': 47,\n              'managed_operations': 487,")
replace_once(catalog_wf, "              'imf_operations': 6,\n              'oecd_operations': 6,", "              'imf_operations': 6,\n              'worldbank_documents_operations': 7,\n              'bis_operations': 8,\n              'oecd_operations': 6,")
replace_once(catalog_wf, "          oecd = providers['oecd']", "          worldbank_documents = providers['worldbank-documents']\n          assert len(worldbank_documents['operations']) == 7\n          assert worldbank_documents['limits']['fixed_api_host'] == 'search.worldbank.org'\n          assert worldbank_documents['limits']['document_body_download_allowed'] is False\n          assert worldbank_documents['limits']['write_operations_allowed'] is False\n\n          bis = providers['bis']\n          assert len(bis['operations']) == 8\n          assert bis['limits']['fixed_api_host'] == 'stats.bis.org'\n          assert bis['limits']['sdmx_rest_version'] == '2.1.0'\n          assert bis['limits']['write_operations_allowed'] is False\n\n          oecd = providers['oecd']")

# Generate committed catalog artifacts.
subprocess.run(["python", str(API / "build_catalog_market_search.py")], check=True)
print(json.dumps({"status":"PASS","managed_providers":47,"managed_operations":487,"wto_indicator_path":"/indicators"}))
