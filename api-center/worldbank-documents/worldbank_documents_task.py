\
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
