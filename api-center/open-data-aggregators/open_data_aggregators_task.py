#!/usr/bin/env python3
"""Bounded runtime for eleven fixed open-data sources."""
from __future__ import annotations
import os, sys, time
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import quote
import requests
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from managed_provider_runtime import bounded_int,bytes_sha,finish_execution,load_json,provider_row,run_cli,utc_now,validate_ticket
SCHEMA_PATH=HERE/"ticket.schema.json"; CATALOG_PATH=HERE/"provider-catalog.json"; MATRIX_PATH=HERE/"source-access-matrix.json"

def text(value:Any,name:str,maximum:int)->str:
    value=str(value or "").strip()
    if not value or len(value)>maximum or any(ord(c)<32 for c in value): raise ValueError(f"{name} is invalid")
    return value

def env(name:str,required:bool=True)->str:
    value=str(os.getenv(name) or "").strip()
    if required and not value: raise RuntimeError(f"required backend credential is not configured: {name}")
    if len(value)>4096 or any(ord(c)<32 for c in value): raise RuntimeError(f"invalid backend credential: {name}")
    return value

def build(operation:str,p:Mapping[str,Any]):
    method="GET"; headers={"Accept":"application/json, text/csv;q=0.8","User-Agent":"evidence-data-center-open-data/1.0"}; query=[]; body=None; credentials=[]
    limit=lambda default,maximum: str(bounded_int(p.get("limit"),default=default,minimum=1,maximum=maximum,name="limit"))
    if operation=="gleif-search":
        url="https://api.gleif.org/api/v1/lei-records"; query=[("filter[entity.legalName]",text(p.get("query"),"query",200)),("page[size]",limit(20,50))]
    elif operation=="gdelt-search":
        url="https://api.gdeltproject.org/api/v2/doc/doc"; query=[("query",text(p.get("query"),"query",500)),("mode","ArtList"),("format","json"),("maxrecords",limit(50,250))]
        if p.get("timespan"): query.append(("timespan",text(p["timespan"],"timespan",20)))
    elif operation=="sdmx-eurostat-data":
        flow=text(p.get("dataflow"),"dataflow",80); key=text(p.get("key"),"key",300)
        url=f"https://ec.europa.eu/eurostat/api/dissemination/sdmx/3.0/data/{quote(flow,safe='')}/{quote(key,safe='.+-')}"; query=[("format","csvdata")]
        if p.get("start_period"): query.append(("startPeriod",text(p["start_period"],"start_period",20)))
        if p.get("end_period"): query.append(("endPeriod",text(p["end_period"],"end_period",20)))
    elif operation=="mobility-search":
        token=env("MOBILITY_DATABASE_ACCESS_TOKEN"); credentials=["MOBILITY_DATABASE_ACCESS_TOKEN"]; headers["Authorization"]=f"Bearer {token}"
        url="https://api.mobilitydatabase.org/v1/search"; query=[("query",text(p.get("query"),"query",200)),("limit",limit(20,50))]
    elif operation=="openalex-search":
        key=env("OPENALEX_API_KEY"); credentials=["OPENALEX_API_KEY"]
        url="https://api.openalex.org/works"; query=[("api_key",key),("search",text(p.get("query"),"query",300)),("per-page",limit(25,50))]
    elif operation=="datacite-search":
        url="https://api.datacite.org/dois"; query=[("query",text(p.get("query"),"query",300)),("page[size]",limit(25,100))]
    elif operation=="opencitations-citations":
        doi=text(p.get("doi"),"doi",255); url=f"https://opencitations.net/index/api/v2/citations/{quote(doi,safe='')}"
        token=env("OPENCITATIONS_TOKEN",False)
        if token: headers["authorization"]=token; credentials=["OPENCITATIONS_TOKEN"]
    elif operation=="unpaywall-get":
        doi=text(p.get("doi"),"doi",255); email=env("UNPAYWALL_EMAIL")
        if "@" not in email: raise RuntimeError("UNPAYWALL_EMAIL must be a contact email")
        credentials=["UNPAYWALL_EMAIL"]; url=f"https://api.unpaywall.org/v2/{quote(doi,safe='')}"; query=[("email",email)]
    elif operation=="usaspending-search":
        method="POST"; url="https://api.usaspending.gov/api/v2/search/spending_by_award/"
        body={"filters":{"time_period":[{"start_date":text(p.get("start_date"),"start_date",10),"end_date":text(p.get("end_date"),"end_date",10)}],"keywords":[text(p.get("keyword"),"keyword",100)],"award_type_codes":["A","B","C","D","02","03","04","05"]},"fields":["Award ID","Recipient Name","Award Amount","Awarding Agency","Start Date","End Date"],"page":1,"limit":int(limit(25,100)),"subawards":False}
    elif operation=="transitland-search":
        key=env("TRANSITLAND_API_KEY"); credentials=["TRANSITLAND_API_KEY"]; url="https://transit.land/api/v2/rest/feeds"
        query=[("apikey",key),("search",text(p.get("query"),"query",200)),("limit",limit(25,50))]
        if p.get("spec"): query.append(("spec",text(p["spec"],"spec",10)))
    elif operation=="china-data-get":
        dataset=text(p.get("dataset"),"dataset",100); url=f"https://chinadata.live/api/v2/data/{quote(dataset,safe='')}"
        if p.get("format")=="csv": query=[("format","csv")]
    else: raise ValueError(f"unsupported operation: {operation}")
    return method,url,headers,query,body,credentials

def execute(ticket_path:Path,output_dir:Path)->int:
    output_dir.mkdir(parents=True,exist_ok=True); ticket=load_json(ticket_path)
    validate_ticket(ticket,schema_path=SCHEMA_PATH,catalog_path=CATALOG_PATH)
    operation=str(ticket["operation"]); started_at=utc_now(); started_perf=time.perf_counter()
    fixture=os.getenv("OPEN_DATA_FIXTURE_MODE")=="1"; snapshot=None; failure=None
    metadata={"fixture_mode":fixture,"network_used":False,"upstream_called":False,"request_count":0,"credential_names":[]}
    status="INTEL_OPEN_DATA_FAILED"
    try:
        if operation=="catalog-capabilities": snapshot=provider_row(CATALOG_PATH)
        elif operation=="source-access-matrix": snapshot=load_json(MATRIX_PATH)
        elif fixture: snapshot={"fixture":True,"operation":operation,"results":[{"id":"fixture-1","source":operation.split("-",1)[0]}]}
        else:
            method,url,headers,query,body,credentials=build(operation,ticket.get("parameters") or {})
            acceptance=ticket.get("acceptance") or {}; timeout=bounded_int(acceptance.get("timeout_seconds"),default=60,minimum=5,maximum=90,name="timeout_seconds"); max_bytes=bounded_int(acceptance.get("max_response_bytes"),default=5000000,minimum=1024,maximum=5000000,name="max_response_bytes")
            response=requests.request(method,url,headers=headers,params=query,json=body,timeout=timeout,allow_redirects=False)
            metadata.update({"network_used":True,"upstream_called":True,"request_count":1,"credential_names":credentials,"http_status":response.status_code,"response_bytes":len(response.content),"response_sha256":bytes_sha(response.content),"request_origin":"/".join(url.split("/")[:3])})
            if 300<=response.status_code<400: raise RuntimeError("redirects are forbidden")
            response.raise_for_status()
            if len(response.content)>max_bytes: raise RuntimeError("response exceeds max_response_bytes")
            ctype=response.headers.get("content-type","").lower()
            data=response.json() if "json" in ctype else {"content_type":ctype,"text":response.text}
            snapshot={"provider":"open-data-aggregators","operation":operation,"secondary_source_warning":operation=="china-data-get","data":data}
        status="INTEL_OPEN_DATA_COMPLETED"
    except Exception as exc: failure={"type":type(exc).__name__,"message":str(exc)[:1000]}
    return finish_execution(ticket=ticket,output_dir=output_dir,status=status,snapshot=snapshot,metadata=metadata,failure=failure,started_at=started_at,started_perf=started_perf,schema_prefix="intel-open-data")

def main()->int:
    return run_cli(execute=execute,ticket_prefix="[intel-open-data]",schema_path=SCHEMA_PATH,catalog_path=CATALOG_PATH,status_schema="intel-open-data-ticket-status-v1",display_name="全球开放聚合数据层")
if __name__=="__main__": raise SystemExit(main())
