\
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
