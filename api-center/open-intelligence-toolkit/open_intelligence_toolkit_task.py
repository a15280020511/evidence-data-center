#!/usr/bin/env python3
"""Bounded no-key public intelligence and offline HTML extraction runtime."""
from __future__ import annotations
import json, os, re, sys, time
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import quote
import requests
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from managed_provider_runtime import bounded_int,bytes_sha,finish_execution,load_json,provider_row,run_cli,utc_now,validate_ticket
SCHEMA_PATH=HERE/"ticket.schema.json";CATALOG_PATH=HERE/"provider-catalog.json";MATRIX_PATH=HERE/"source-access-matrix.json";TOOLCHAIN_PATH=HERE/"toolchain-status.json"
CKAN={"uk":"https://ckan.publishing.service.gov.uk/api/3/action/package_search","hdx":"https://data.humdata.org/api/3/action/package_search","open-africa":"https://open.africa/api/3/action/package_search"}
SOCRATA={"nyc":"https://data.cityofnewyork.us","cdc":"https://data.cdc.gov","chicago":"https://data.cityofchicago.org"}

def text(v:Any,n:str,m:int)->str:
 s=str(v or "").strip()
 if not s or len(s)>m or any(ord(c)<32 for c in s):raise ValueError(f"{n} is invalid")
 return s

def integer(v:Any,n:str,d:int,lo:int,hi:int)->int:
 return bounded_int(v,default=d,minimum=lo,maximum=hi,name=n)

def build(op:str,p:Mapping[str,Any]):
 h={"Accept":"application/json, application/atom+xml;q=0.9, text/html;q=0.7, text/plain;q=0.6","User-Agent":"evidence-data-center/1.0 (https://github.com/a15280020511/evidence-data-center)"};q=[];b=None;m="GET";local=False
 if op in {"catalog-capabilities","source-access-matrix","toolchain-status","html-structure-extract"}:return m,"local",h,q,b,True
 if op=="common-crawl-collinfo":u="https://index.commoncrawl.org/collinfo.json"
 elif op=="common-crawl-index":
  idx=text(p.get("index"),"index",20)
  if not re.fullmatch(r"CC-MAIN-[0-9]{4}-[0-9]{2}",idx):raise ValueError("invalid Common Crawl index")
  u=f"https://index.commoncrawl.org/{idx}-index";q=[("url",text(p.get("url"),"url",500)),("output","json"),("matchType",str(p.get("match_type") or "exact")),("pageSize",str(integer(p.get("limit"),"limit",20,1,100)))]
 elif op=="gdacs-events":u="https://www.gdacs.org/contentdata/xml/gdacsAPP_Home.geojson"
 elif op in {"sec-submissions","sec-company-facts"}:
  cik=text(p.get("cik"),"cik",10)
  if not re.fullmatch(r"[0-9]{10}",cik):raise ValueError("cik must contain exactly 10 digits")
  u=f"https://data.sec.gov/{'submissions' if op=='sec-submissions' else 'api/xbrl/companyfacts'}/CIK{cik}.json"
 elif op=="bls-series":
  ids=p.get("series_ids")
  if not isinstance(ids,list) or not 1<=len(ids)<=25:raise ValueError("series_ids must contain 1 to 25 values")
  parsed=[text(x,"series_id",80) for x in ids];sy=integer(p.get("start_year"),"start_year",2020,1900,2100);ey=integer(p.get("end_year"),"end_year",2026,1900,2100)
  if sy>ey:raise ValueError("start_year cannot exceed end_year")
  m="POST";u="https://api.bls.gov/publicAPI/v1/timeseries/data/";b={"seriesid":parsed,"startyear":str(sy),"endyear":str(ey)}
 elif op=="ecb-sdmx-data":
  flow=text(p.get("flow"),"flow",100);key=text(p.get("key"),"key",500);u=f"https://data-api.ecb.europa.eu/service/data/{quote(flow,safe='')}/{quote(key,safe='.+-')}";q=[("format",str(p.get("format") or "csvdata"))]
  if p.get("start_period"):q.append(("startPeriod",text(p["start_period"],"start_period",30)))
  if p.get("end_period"):q.append(("endPeriod",text(p["end_period"],"end_period",30)))
 elif op=="wikimedia-pageviews":
  project=text(p.get("project"),"project",80);article=quote(text(p.get("article"),"article",300).replace(" ","_"),safe="")
  access=str(p.get("access") or "all-access");agent=str(p.get("agent") or "user");gran=str(p.get("granularity") or "daily");start=text(p.get("start"),"start",10);end=text(p.get("end"),"end",10)
  u=f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{project}/{access}/{agent}/{article}/{gran}/{start}/{end}"
 elif op=="hackernews-topstories":u="https://hacker-news.firebaseio.com/v0/topstories.json"
 elif op=="hackernews-item":u=f"https://hacker-news.firebaseio.com/v0/item/{integer(p.get('item_id'),'item_id',1,1,2147483647)}.json"
 elif op=="ror-search":u="https://api.ror.org/v2/organizations";q=[("query",text(p.get("query"),"query",300)),("page_size",str(integer(p.get("limit"),"limit",20,1,100)))]
 elif op=="uk-legislation-search":
  u="https://www.legislation.gov.uk/search/data.feed";q=[("title",text(p.get("title"),"title",300))]
  for k in ("year","number","type"):
   if p.get(k) not in (None,""):q.append((k,str(p[k])))
  q.append(("results-count",str(integer(p.get("limit"),"limit",20,1,50))))
 elif op=="ted-search":m="POST";u="https://api.ted.europa.eu/v3/notices/search";b={"query":text(p.get("query"),"query",500),"page":1,"limit":integer(p.get("limit"),"limit",20,1,100)}
 elif op=="ckan-package-search":
  portal=str(p.get("portal") or "");u=CKAN.get(portal) or (_ for _ in ()).throw(ValueError("unsupported CKAN portal"));q=[("q",text(p.get("query"),"query",300)),("rows",str(integer(p.get("limit"),"limit",20,1,100))), ("start","0")]
 elif op=="socrata-dataset-rows":
  portal=str(p.get("portal") or "");host=SOCRATA.get(portal)
  if not host:raise ValueError("unsupported Socrata portal")
  ds=text(p.get("dataset_id"),"dataset_id",9)
  if not re.fullmatch(r"[a-z0-9]{4}-[a-z0-9]{4}",ds):raise ValueError("invalid Socrata dataset_id")
  u=f"{host}/resource/{ds}.json";q=[("$limit",str(integer(p.get("limit"),"limit",100,1,1000)))]
  if p.get("query"):q.append(("$q",text(p["query"],"query",200)))
 elif op=="stackexchange-search":
  u="https://api.stackexchange.com/2.3/search/advanced";q=[("q",text(p.get("query"),"query",300)),("site",str(p.get("site") or "stackoverflow")),("sort",str(p.get("sort") or "relevance")),("order","desc"),("pagesize",str(integer(p.get("limit"),"limit",30,1,100)))]
  if p.get("tagged"):q.append(("tagged",text(p["tagged"],"tagged",200)))
 elif op=="bluesky-search-posts":u="https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts";q=[("q",text(p.get("query"),"query",300)),("sort",str(p.get("sort") or "latest")),("limit",str(integer(p.get("limit"),"limit",25,1,100)))]
 elif op=="cas-data-centers":u="https://www.casdc.cn/dataV/"
 else:raise ValueError(f"unsupported operation: {op}")
 return m,u,h,q,b,local

def html_extract(p:Mapping[str,Any])->dict[str,Any]:
 import extruct,trafilatura
 from readability import Document
 html=text(p.get("html"),"html",200000);base=str(p.get("base_url") or "") or None
 extracted=trafilatura.extract(html,url=base,output_format="markdown",include_comments=False,include_tables=True,with_metadata=False) or ""
 structured=extruct.extract(html,base_url=base,syntaxes=["json-ld","microdata","opengraph","rdfa"],uniform=True)
 doc=Document(html)
 return {"text_markdown":extracted[:200000],"readable_title":doc.short_title()[:1000],"readable_html":doc.summary(html_partial=True)[:200000],"structured_data":structured}

def execute(ticket_path:Path,output_dir:Path)->int:
 output_dir.mkdir(parents=True,exist_ok=True);ticket=load_json(ticket_path);validate_ticket(ticket,schema_path=SCHEMA_PATH,catalog_path=CATALOG_PATH)
 op=str(ticket["operation"]);p=ticket.get("parameters") or {};started_at=utc_now();started_perf=time.perf_counter();fixture=os.getenv("OPEN_INTELLIGENCE_FIXTURE_MODE")=="1";snapshot=None;failure=None;status="INTEL_OPEN_TOOLKIT_FAILED";meta={"fixture_mode":fixture,"network_used":False,"upstream_called":False,"request_count":0,"model_calls":0,"secret_values_exposed":False,"operation":op}
 try:
  method,url,headers,query,body,local=build(op,p)
  if op=="catalog-capabilities":snapshot=provider_row(CATALOG_PATH)
  elif op=="source-access-matrix":snapshot=load_json(MATRIX_PATH)
  elif op=="toolchain-status":snapshot=load_json(TOOLCHAIN_PATH)
  elif op=="html-structure-extract":snapshot={"provider":"open-intelligence-toolkit","operation":op,"data":html_extract(p)}
  elif fixture:snapshot={"fixture":True,"operation":op,"request":{"method":method,"origin":"/".join(url.split("/")[:3]),"query_names":[k for k,_ in query],"has_body":body is not None}}
  else:
   a=ticket.get("acceptance") or {};timeout=integer(a.get("timeout_seconds"),"timeout_seconds",45,5,90);maxb=integer(a.get("max_response_bytes"),"max_response_bytes",5000000,1024,5000000)
   r=requests.request(method,url,headers=headers,params=query,json=body,timeout=timeout,allow_redirects=False);raw=bytes(r.content or b"")
   meta.update({"network_used":True,"upstream_called":True,"request_count":1,"request_origin":"/".join(url.split("/")[:3]),"http_status":r.status_code,"response_bytes":len(raw),"response_sha256":bytes_sha(raw),"query_parameter_names":sorted({k for k,_ in query})})
   if 300<=r.status_code<400:raise RuntimeError("redirects are forbidden")
   r.raise_for_status()
   if len(raw)>maxb:raise RuntimeError("response exceeds max_response_bytes")
   ct=r.headers.get("content-type","").lower()
   if op=="common-crawl-index":data=[json.loads(line) for line in r.text.splitlines() if line.strip()][:100]
   elif "json" in ct or raw.lstrip().startswith((b"{",b"[")):data=r.json()
   else:data={"content_type":ct,"text":r.text}
   if op=="hackernews-topstories" and isinstance(data,list):data=data[:integer(p.get("limit"),"limit",100,1,500)]
   snapshot={"provider":"open-intelligence-toolkit","operation":op,"data":data}
  status="INTEL_OPEN_TOOLKIT_COMPLETED"
 except Exception as exc:failure={"type":type(exc).__name__,"message":str(exc)[:1200]}
 return finish_execution(ticket=ticket,output_dir=output_dir,status=status,snapshot=snapshot,metadata=meta,failure=failure,started_at=started_at,started_perf=started_perf,schema_prefix="intel-open-toolkit")

def main()->int:return run_cli(execute=execute,ticket_prefix="[intel-open-toolkit]",schema_path=SCHEMA_PATH,catalog_path=CATALOG_PATH,status_schema="intel-open-toolkit-ticket-status-v1",display_name="开放情报采集与解析工具包")
if __name__=="__main__":raise SystemExit(main())
