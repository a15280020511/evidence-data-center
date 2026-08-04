#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "api-center"
PKG = API / "open-intelligence-toolkit"
PKG.mkdir(parents=True, exist_ok=True)
(PKG / "tests").mkdir(exist_ok=True)

OPS = [
    ("catalog-capabilities", "读取本地开放情报工具包能力目录。", [], "LOCAL", "none"),
    ("source-access-matrix", "读取来源、费用、许可和生产状态矩阵。", [], "LOCAL", "none"),
    ("toolchain-status", "读取浏览、解析、索引和条件工具状态。", [], "LOCAL", "none"),
    ("common-crawl-collinfo", "读取 Common Crawl 可用索引集合。", [], "https://index.commoncrawl.org/collinfo.json", "none"),
    ("common-crawl-index", "在指定 Common Crawl 索引中查找历史网页记录。", ["index", "url", "match_type", "limit"], "https://index.commoncrawl.org/{index}-index", "none"),
    ("gdacs-events", "读取 GDACS 当前全球灾害事件 GeoJSON。", [], "https://www.gdacs.org/contentdata/xml/gdacsAPP_Home.geojson", "none"),
    ("sec-submissions", "读取 SEC EDGAR 公司提交记录。", ["cik"], "https://data.sec.gov/submissions/CIK{cik}.json", "none"),
    ("sec-company-facts", "读取 SEC EDGAR XBRL Company Facts。", ["cik"], "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json", "none"),
    ("bls-series", "读取美国 BLS v1 时间序列。", ["series_ids", "start_year", "end_year"], "https://api.bls.gov/publicAPI/v1/timeseries/data/", "none"),
    ("ecb-sdmx-data", "读取 ECB Data Portal SDMX 数据。", ["flow", "key", "start_period", "end_period", "format"], "https://data-api.ecb.europa.eu/service/data/{flow}/{key}", "none"),
    ("wikimedia-pageviews", "读取 Wikimedia 聚合页面浏览量。", ["project", "access", "agent", "article", "granularity", "start", "end"], "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/...", "none"),
    ("hackernews-topstories", "读取 Hacker News 热门条目编号。", ["limit"], "https://hacker-news.firebaseio.com/v0/topstories.json", "none"),
    ("hackernews-item", "读取单个 Hacker News 条目。", ["item_id"], "https://hacker-news.firebaseio.com/v0/item/{item_id}.json", "none"),
    ("ror-search", "搜索 ROR v2 全球研究机构。", ["query", "limit"], "https://api.ror.org/v2/organizations", "none"),
    ("uk-legislation-search", "搜索英国 legislation.gov.uk 机器可读法规目录。", ["title", "year", "number", "type", "limit"], "https://www.legislation.gov.uk/search/data.feed", "none"),
    ("ted-search", "搜索欧盟 TED 公共采购公告。", ["query", "limit"], "https://api.ted.europa.eu/v3/notices/search", "none"),
    ("ckan-package-search", "在固定 CKAN 开放数据门户中搜索数据集。", ["portal", "query", "limit"], "fixed CKAN allowlist", "none"),
    ("socrata-dataset-rows", "读取固定 Socrata 门户的公开数据集行。", ["portal", "dataset_id", "query", "limit"], "fixed Socrata allowlist", "none"),
    ("stackexchange-search", "搜索 Stack Exchange 技术问答。", ["query", "site", "tagged", "sort", "limit"], "https://api.stackexchange.com/2.3/search/advanced", "none"),
    ("bluesky-search-posts", "通过 Bluesky 公共 AppView 搜索公开帖子。", ["query", "sort", "limit"], "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts", "none"),
    ("cas-data-centers", "读取中国科学院科学数据中心公开目录页。", [], "https://www.casdc.cn/dataV/", "none"),
    ("html-structure-extract", "离线提取给定 HTML 的正文、可读内容和结构化元数据。", ["html", "base_url"], "LOCAL", "none"),
]

parameter_schemas = {
    "catalog-capabilities": {}, "source-access-matrix": {}, "toolchain-status": {},
    "common-crawl-collinfo": {}, "gdacs-events": {}, "cas-data-centers": {},
    "common-crawl-index": {"index":{"type":"string","pattern":"^CC-MAIN-[0-9]{4}-[0-9]{2}$"},"url":{"type":"string","minLength":1,"maxLength":500},"match_type":{"enum":["exact","prefix","host","domain"]},"limit":{"type":"integer","minimum":1,"maximum":100}},
    "sec-submissions": {"cik":{"type":"string","pattern":"^[0-9]{10}$"}},
    "sec-company-facts": {"cik":{"type":"string","pattern":"^[0-9]{10}$"}},
    "bls-series": {"series_ids":{"type":"array","minItems":1,"maxItems":25,"items":{"type":"string","pattern":"^[A-Za-z0-9._-]{1,80}$"}},"start_year":{"type":"integer","minimum":1900,"maximum":2100},"end_year":{"type":"integer","minimum":1900,"maximum":2100}},
    "ecb-sdmx-data": {"flow":{"type":"string","pattern":"^[A-Za-z0-9_.-]{1,100}$"},"key":{"type":"string","pattern":"^[A-Za-z0-9_.+-]{1,500}$"},"start_period":{"type":"string","maxLength":30},"end_period":{"type":"string","maxLength":30},"format":{"enum":["csvdata","jsondata"]}},
    "wikimedia-pageviews": {"project":{"type":"string","pattern":"^[a-z0-9.-]{1,80}$"},"access":{"enum":["all-access","desktop","mobile-app","mobile-web"]},"agent":{"enum":["all-agents","user","spider","automated"]},"article":{"type":"string","minLength":1,"maxLength":300},"granularity":{"enum":["daily","monthly"]},"start":{"type":"string","pattern":"^[0-9]{8}(?:[0-9]{2})?$"},"end":{"type":"string","pattern":"^[0-9]{8}(?:[0-9]{2})?$"}},
    "hackernews-topstories": {"limit":{"type":"integer","minimum":1,"maximum":500}},
    "hackernews-item": {"item_id":{"type":"integer","minimum":1,"maximum":2147483647}},
    "ror-search": {"query":{"type":"string","minLength":1,"maxLength":300},"limit":{"type":"integer","minimum":1,"maximum":100}},
    "uk-legislation-search": {"title":{"type":"string","minLength":1,"maxLength":300},"year":{"type":"integer","minimum":1000,"maximum":2100},"number":{"type":"integer","minimum":1,"maximum":999999},"type":{"type":"string","pattern":"^[a-z-]{1,60}$"},"limit":{"type":"integer","minimum":1,"maximum":50}},
    "ted-search": {"query":{"type":"string","minLength":1,"maxLength":500},"limit":{"type":"integer","minimum":1,"maximum":100}},
    "ckan-package-search": {"portal":{"enum":["uk","hdx","open-africa"]},"query":{"type":"string","minLength":1,"maxLength":300},"limit":{"type":"integer","minimum":1,"maximum":100}},
    "socrata-dataset-rows": {"portal":{"enum":["nyc","cdc","chicago"]},"dataset_id":{"type":"string","pattern":"^[a-z0-9]{4}-[a-z0-9]{4}$"},"query":{"type":"string","maxLength":200},"limit":{"type":"integer","minimum":1,"maximum":1000}},
    "stackexchange-search": {"query":{"type":"string","minLength":1,"maxLength":300},"site":{"type":"string","pattern":"^[a-z0-9.-]{1,80}$"},"tagged":{"type":"string","pattern":"^[A-Za-z0-9+#_.;-]{1,200}$"},"sort":{"enum":["activity","creation","votes","relevance"]},"limit":{"type":"integer","minimum":1,"maximum":100}},
    "bluesky-search-posts": {"query":{"type":"string","minLength":1,"maxLength":300},"sort":{"enum":["top","latest"]},"limit":{"type":"integer","minimum":1,"maximum":100}},
    "html-structure-extract": {"html":{"type":"string","minLength":1,"maxLength":200000},"base_url":{"type":"string","pattern":"^https://[^\\s]{1,500}$"}},
}
required = {
    "common-crawl-index":["index","url"], "sec-submissions":["cik"], "sec-company-facts":["cik"],
    "bls-series":["series_ids"], "ecb-sdmx-data":["flow","key"],
    "wikimedia-pageviews":["project","article","start","end"], "hackernews-item":["item_id"],
    "ror-search":["query"], "uk-legislation-search":["title"], "ted-search":["query"],
    "ckan-package-search":["portal","query"], "socrata-dataset-rows":["portal","dataset_id"],
    "stackexchange-search":["query"], "bluesky-search-posts":["query"], "html-structure-extract":["html"],
}
operations=[]
for op, desc, params, endpoint, cred in OPS:
    properties=parameter_schemas.get(op,{})
    schema={"type":"object","additionalProperties":False,"properties":properties}
    if required.get(op): schema["required"]=required[op]
    operations.append({"operation_id":op,"description":desc,"parameters":params,"parameter_schema":schema,"result_contract":{"source":"open-intelligence-toolkit","official_endpoint":endpoint,"http_method":"LOCAL" if endpoint=="LOCAL" else ("POST" if op in {"bls-series","ted-search"} else "GET"),"read_only":True,"credential_mode":cred}})

catalog={
 "schema_version":"open-intelligence-toolkit-provider-catalog-v1","secret_values_exposed":False,
 "providers":[{"provider_id":"open-intelligence-toolkit","display_name":"开放情报采集与解析工具包","description":"统一提供免Key公共情报API、固定门户检索和离线HTML正文/结构化数据提取；重型浏览与文档服务仅注册状态，不伪报联通。","enabled":True,"ticket_prefix":"[intel-open-toolkit]","required_secret_environment_variable":"","optional_secret_environment_variables":[],"catalog_policy":"只允许22项固定只读或本地操作；禁止任意主机、任意URL、登录、Cookie、验证码绕过、自动分页、自动重试、持续流、个人画像、写入和交易。","execution_policy":"每票最多一次上游请求；固定端点或固定门户枚举；HTML解析完全离线；所有结果生成哈希、诊断和Artifact回执。","limits":{"requests_per_ticket_max":1,"timeout_seconds_max":90,"max_response_bytes":5000000,"automatic_retry_allowed":False,"automatic_pagination_allowed":False,"redirects_allowed":False,"arbitrary_urls_allowed":False,"arbitrary_hosts_allowed":False,"arbitrary_paths_allowed":False,"arbitrary_headers_allowed":False,"client_supplied_credentials_allowed":False,"login_allowed":False,"cookie_persistence_allowed":False,"captcha_bypass_allowed":False,"write_operations_allowed":False,"personal_profiling_allowed":False,"model_calls":0,"secret_values_exposed":False},"operations":operations}]
}
(PKG/"provider-catalog.json").write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

matrix={
 "schema_version":"open-intelligence-source-access-matrix-v1","enabled_no_key_sources":["common-crawl","gdacs","sec-edgar","bls-v1","ecb-sdmx","wikimedia-pageviews","hacker-news","ror-v2","uk-legislation","ted-search","fixed-ckan-portals","fixed-socrata-portals","stack-exchange-anonymous","bluesky-public-appview","cas-data-center-catalog"],
 "existing_capabilities_reused_without_duplication":["browserless","cloudflare-browser-run","internet-archive","gdelt","eurostat","openalex","datacite","opencitations","unpaywall","usaspending","transitland"],
 "conditional_not_directly_invokable":[
  {"id":"browsertrix","reason":"requires a self-hosted browser service and evidence storage"},
  {"id":"crawl4ai","reason":"requires a controlled self-hosted browser runtime"},
  {"id":"playwright-mcp","reason":"browser control must remain behind the existing bounded browser layer"},
  {"id":"searxng","reason":"requires a maintained self-hosted metasearch instance"},
  {"id":"docling","reason":"heavy local document runtime; activate only in a dedicated file pipeline"},
  {"id":"grobid","reason":"requires a separately pinned Java service"},
  {"id":"apache-tika","reason":"requires a separately pinned Java service"},
  {"id":"opensearch","reason":"requires persistent service/storage; not needed for source-of-truth retrieval"},
  {"id":"scrapy","reason":"allowed only for future fixed-domain collectors, never arbitrary crawling"},
  {"id":"phda","reason":"official interface requires uniqueNum verification parameter"},
  {"id":"sciencedb-open-api","reason":"public Open API/OAI-PMH endpoint contract not yet frozen"},
  {"id":"national-dataset-platform","reason":"portal is operational but no stable public API is documented"},
  {"id":"wikimedia-eventstreams","reason":"continuous streaming conflicts with one-request bounded execution"}
 ],
 "licence_and_use_notes":{"bluesky":"public AppView; no pagination cursor is exposed","stack-exchange":"anonymous quota only; no app key","sec-edgar":"fair-access user agent and one request per ticket","cas-data-centers":"catalog discovery only; downstream center policies vary"},
 "secret_values_exposed":False
}
(PKG/"source-access-matrix.json").write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

toolchain={
 "schema_version":"open-intelligence-toolchain-status-v1","production_local":[
  {"id":"trafilatura","role":"main text and metadata extraction","network":False},
  {"id":"extruct","role":"JSON-LD, Microdata, RDFa and OpenGraph extraction","network":False},
  {"id":"readability-lxml","role":"readable article fallback","network":False}
 ],"production_remote_fixed":["common-crawl","gdacs","sec-edgar","bls","ecb","wikimedia","hacker-news","ror","uk-legislation","ted","ckan-allowlist","socrata-allowlist","stack-exchange","bluesky","casdc"],"conditional":["browsertrix","crawl4ai","playwright-mcp","searxng","docling","grobid","apache-tika","opensearch","scrapy"],"arbitrary_code_allowed":False,"arbitrary_url_allowed":False,"model_calls":0
}
(PKG/"toolchain-status.json").write_text(json.dumps(toolchain,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

schema={"$schema":"https://json-schema.org/draft/2020-12/schema","title":"Open Intelligence Toolkit Ticket","type":"object","additionalProperties":False,"required":["task_id","provider","operation","objective","parameters","data_policy","acceptance"],"properties":{"task_id":{"type":"string","pattern":"^[A-Za-z0-9][A-Za-z0-9._-]{7,127}$"},"provider":{"const":"open-intelligence-toolkit"},"operation":{"enum":[x[0] for x in OPS]},"objective":{"type":"string","minLength":1,"maxLength":3000},"parameters":{"type":"object","maxProperties":16,"additionalProperties":True},"data_policy":{"type":"object","additionalProperties":False,"required":["classification","contains_personal_data"],"properties":{"classification":{"const":"public"},"contains_personal_data":{"const":False},"notes":{"type":"string","maxLength":2000}}},"acceptance":{"type":"object","additionalProperties":False,"properties":{"timeout_seconds":{"type":"integer","minimum":5,"maximum":90},"max_response_bytes":{"type":"integer","minimum":1024,"maximum":5000000}}}}}
(PKG/"ticket.schema.json").write_text(json.dumps(schema,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
(PKG/"requirements.txt").write_text("requests==2.32.5\ntrafilatura==2.0.0\nextruct==0.18.0\nreadability-lxml==0.8.4.1\n",encoding="utf-8")

runtime=r'''#!/usr/bin/env python3
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
'''
(PKG/"open_intelligence_toolkit_task.py").write_text(runtime,encoding="utf-8")

samples={
 "catalog-capabilities":{},"source-access-matrix":{},"toolchain-status":{},"common-crawl-collinfo":{},"common-crawl-index":{"index":"CC-MAIN-2026-30","url":"example.com","limit":2},"gdacs-events":{},"sec-submissions":{"cik":"0000320193"},"sec-company-facts":{"cik":"0000320193"},"bls-series":{"series_ids":["CUUR0000SA0"],"start_year":2024,"end_year":2025},"ecb-sdmx-data":{"flow":"EXR","key":"D.USD.EUR.SP00.A","format":"csvdata"},"wikimedia-pageviews":{"project":"en.wikipedia.org","article":"Artificial_intelligence","start":"20260801","end":"20260802"},"hackernews-topstories":{"limit":5},"hackernews-item":{"item_id":1},"ror-search":{"query":"OpenAI","limit":5},"uk-legislation-search":{"title":"data protection","limit":5},"ted-search":{"query":"text ~ \"artificial intelligence\"","limit":5},"ckan-package-search":{"portal":"uk","query":"transport","limit":5},"socrata-dataset-rows":{"portal":"cdc","dataset_id":"9mfq-cb36","limit":5},"stackexchange-search":{"query":"python json","site":"stackoverflow","limit":5},"bluesky-search-posts":{"query":"open data","limit":5},"cas-data-centers":{},"html-structure-extract":{"base_url":"https://example.com/","html":"<html><head><title>Example</title><script type='application/ld+json'>{\"@type\":\"Article\",\"headline\":\"Example\"}</script></head><body><main><h1>Example</h1><p>This is a sufficiently long article paragraph for deterministic extraction and validation.</p></main></body></html>"}}
validator=r'''#!/usr/bin/env python3
import argparse,json,os,tempfile
from pathlib import Path
import open_intelligence_toolkit_task as runtime
SAMPLES='''+repr(samples)+r'''
def main():
 p=argparse.ArgumentParser();p.add_argument("--operation",required=True,choices=sorted(SAMPLES));p.add_argument("--output",required=True);a=p.parse_args();os.environ["OPEN_INTELLIGENCE_FIXTURE_MODE"]="1"
 ticket={"task_id":f"fixture-{a.operation}-20260804","provider":"open-intelligence-toolkit","operation":a.operation,"objective":"zero-cost bounded validation","parameters":SAMPLES[a.operation],"data_policy":{"classification":"public","contains_personal_data":False},"acceptance":{"timeout_seconds":30,"max_response_bytes":1000000}}
 runtime.validate_ticket(ticket,schema_path=runtime.SCHEMA_PATH,catalog_path=runtime.CATALOG_PATH)
 method,url,headers,query,body,local=runtime.build(a.operation,ticket["parameters"])
 if not local:assert url.startswith("https://") and method in {"GET","POST"}
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp);tp=root/"ticket.json";out=root/"out";tp.write_text(json.dumps(ticket,ensure_ascii=False),encoding="utf-8");assert runtime.execute(tp,out)==0
  d=json.loads((out/"diagnostics.json").read_text());m=json.loads((out/"manifest.json").read_text());s=json.loads((out/"snapshot.json").read_text())
  assert d["status"]=="INTEL_OPEN_TOOLKIT_COMPLETED";assert d["model_calls"]==0;assert m["secret_values_exposed"] is False
  if a.operation=="html-structure-extract":assert s["data"]["text_markdown"] and s["data"]["structured_data"]["json-ld"]
 result={"status":"PASS","operation":a.operation,"fixture_mode":True,"model_calls":0,"secret_values_exposed":False,"request_contract":{"method":method,"origin":"LOCAL" if local else "/".join(url.split("/")[:3]),"local":local}}
 outp=Path(a.output);outp.parent.mkdir(parents=True,exist_ok=True);outp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
if __name__=="__main__":main()
'''
(PKG/"validate_open_intelligence_toolkit.py").write_text(validator,encoding="utf-8")

test=r'''import importlib.util,json,os,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import open_intelligence_toolkit_task as runtime
class ToolkitTests(unittest.TestCase):
 def test_catalog_is_no_key_and_bounded(self):
  c=json.loads((HERE/"provider-catalog.json").read_text());p=c["providers"][0]
  self.assertEqual(len(p["operations"]),22);self.assertEqual(p["required_secret_environment_variable"],"");self.assertFalse(p["limits"]["arbitrary_urls_allowed"]);self.assertFalse(p["limits"]["write_operations_allowed"])
 def test_fixed_portal_allowlists(self):
  for op,p in [("ckan-package-search",{"portal":"uk","query":"x"}),("socrata-dataset-rows",{"portal":"cdc","dataset_id":"9mfq-cb36"})]:
   _,u,_,_,_,_=runtime.build(op,p);self.assertTrue(u.startswith("https://"))
  with self.assertRaises(ValueError):runtime.build("ckan-package-search",{"portal":"evil","query":"x"})
 def test_html_is_offline_and_structured(self):
  data=runtime.html_extract({"html":"<html><head><script type='application/ld+json'>{\"@type\":\"Article\"}</script></head><body><main><p>A long public article body used for extraction validation without any network call.</p></main></body></html>","base_url":"https://example.com/"})
  self.assertIn("json-ld",data["structured_data"]);self.assertTrue(data["text_markdown"])
 def test_schema_operation_set_matches_catalog(self):
  c=json.loads((HERE/"provider-catalog.json").read_text())["providers"][0];s=json.loads((HERE/"ticket.schema.json").read_text())
  self.assertEqual({x["operation_id"] for x in c["operations"]},set(s["properties"]["operation"]["enum"]))
if __name__=="__main__":unittest.main()
'''
(PKG/"tests/test_open_intelligence_toolkit.py").write_text(test,encoding="utf-8")
(PKG/"README.md").write_text("""# 开放情报采集与解析工具包\n\n22项免Key、固定端点或离线操作。每张票据最多一次上游请求；不允许任意URL、登录、Cookie、验证码绕过、持续流、自动分页或写入。\n\n重型工具 Browsertrix、Crawl4AI、Playwright MCP、SearXNG、Docling、GROBID、Tika、OpenSearch和Scrapy仅进入条件能力矩阵；已有Browserless、Cloudflare Browser Run和Internet Archive直接复用，不重复建设。\n\nPHDA因`uniqueNum`验证参数、ScienceDB因端点合同尚未冻结、国家数据集平台因尚无稳定公共API，均不伪报为生产接口。\n""",encoding="utf-8")

build=API/"build_catalog_market_search.py"
s=build.read_text(encoding="utf-8")
if "OPEN_INTELLIGENCE_TOOLKIT_CATALOG" not in s:
 s=s.replace('GLOBAL_SENSOR_BACKBONE_CATALOG = HERE / "global-sensor-backbone/provider-catalog.json"', 'GLOBAL_SENSOR_BACKBONE_CATALOG = HERE / "global-sensor-backbone/provider-catalog.json"\nOPEN_INTELLIGENCE_TOOLKIT_CATALOG = HERE / "open-intelligence-toolkit/provider-catalog.json"')
 s=s.replace('    "noaa-cdo": 5,\n}', '    "noaa-cdo": 5,\n    "open-intelligence-toolkit": 22,\n}')
 s=s.replace('    COPERNICUS_MARINE_CATALOG,\n)', '    COPERNICUS_MARINE_CATALOG,\n    OPEN_INTELLIGENCE_TOOLKIT_CATALOG,\n)')
 s=s.replace('        "global-sensor-backbone/provider-catalog.json",\n', '        "global-sensor-backbone/provider-catalog.json",\n        "open-intelligence-toolkit/provider-catalog.json",\n')
build.write_text(s,encoding="utf-8")

subprocess.run(["python","api-center/build_config.py"],cwd=ROOT,check=True)
subprocess.run(["python","api-center/build_catalog_market_search.py"],cwd=ROOT,check=True)
print(json.dumps({"status":"PASS","provider":"open-intelligence-toolkit","operations":len(OPS)},ensure_ascii=False))
