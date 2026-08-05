#!/usr/bin/env python3
"""Bounded daily discovery for public APIs, remote MCP and readable data sources."""
from __future__ import annotations
import argparse, hashlib, ipaddress, json, os, re, socket, sys, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

UA="evidence-data-center-source-discovery/1"
URL_RE=re.compile(r"https://[^\s\"'<>)}\]]+",re.I)
BLOCKED={"localhost","metadata.google.internal","metadata.azure.internal","kubernetes.default","instance-data"}
MACHINE=("json","xml","csv","rss","atom","yaml")

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def load(p,d): return json.loads(p.read_text(encoding="utf-8")) if p.exists() else d
def save(p,v): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def safe_url(value,resolve=False):
    try: u=urllib.parse.urlsplit(str(value or "").strip().rstrip(".,;:"))
    except ValueError: return None
    if u.scheme.lower()!="https" or not u.hostname or u.username or u.password or u.port not in (None,443): return None
    host=u.hostname.casefold().rstrip(".")
    if host in BLOCKED or host.endswith((".local",".internal",".localhost",".svc",".cluster.local")): return None
    if resolve:
        try:
            ips={str(x[4][0]).split("%",1)[0] for x in socket.getaddrinfo(host,443,type=socket.SOCK_STREAM,proto=socket.IPPROTO_TCP)}
            if not ips or any(not ipaddress.ip_address(x).is_global for x in ips): return None
        except (socket.gaierror,ValueError): return None
    return urllib.parse.urlunsplit(("https",host,re.sub(r"/{2,}","/",u.path or "/"),u.query,""))

def request_json(url,method="GET",body=None,headers=None,max_bytes=8000000):
    data=None if body is None else json.dumps(body).encode()
    h={"Accept":"application/json","User-Agent":UA,**dict(headers or {})}
    if data is not None: h["Content-Type"]="application/json"
    with urllib.request.urlopen(urllib.request.Request(url,data=data,headers=h,method=method),timeout=25) as r:
        raw=r.read(max_bytes+1)
        if len(raw)>max_bytes: raise RuntimeError("response too large")
        return json.loads(raw.decode())

def trusted(host,cfg): return host in set(cfg.get("trusted_exact_domains") or []) or any(host.endswith(str(x).casefold()) for x in cfg.get("trusted_domain_suffixes") or [])
def kind(text,url):
    b=f"{text} {url}".casefold()
    for k,words in [("remote_mcp",("model context protocol","remote mcp","/mcp")),("openapi",("openapi","swagger")),("graphql",("graphql",)),("ckan",("ckan","/api/3/action/")),("socrata",("socrata","api/views")),("arcgis_rest",("arcgis","/rest/services")),("stac",("stac",)),("sparql",("sparql",)),("sdmx",("sdmx",)),("oai_pmh",("oai-pmh","verb=identify")),("rss_atom",("rss","atom","/feed")),("bulk_download",("bulk download",".csv",".json",".zip")),("rest_api",("rest api","/api/","/v1/","/v2/","/v3/"))]:
        if any(w in b for w in words): return k
    return "web_read"

def score(x):
    v=10+(22 if x["trusted_domain"] else 0)+(16 if x["source_type"]!="web_read" else 0)+(12 if x["auth"]=="none" else 3 if x["auth"]=="required" else 0)+(12 if x["license"]=="open" else -50 if x["license"]=="prohibited" else 0)+(16 if x["probe"].get("ok") else 0)+(8 if x["probe"].get("machine_readable") else 0)+(8 if x["high_value"] else 0)+(8 if x["discovery_engine"]=="apis.guru" else 0)
    return max(0,min(100,v))

def make(url,title,desc,engine,query,cfg):
    url=safe_url(url)
    if not url: return None
    host=urllib.parse.urlsplit(url).hostname or ""; text=f"{title} {desc} {url}".casefold()
    auth="required" if any(x in text for x in cfg.get("auth_terms") or []) else "unknown"
    lic="prohibited" if any(x in text for x in cfg.get("license_negative_terms") or []) else "open" if any(x in text for x in cfg.get("license_positive_terms") or []) else "unknown"
    x={"source_id":hashlib.sha256(url.encode()).hexdigest()[:20],"url":url,"host":host,"title":str(title or host)[:300],"description":str(desc or "")[:1200],"source_type":kind(text,url),"auth":auth,"license":lic,"trusted_domain":trusted(host,cfg),"high_value":any(k in text for k in cfg.get("high_value_terms") or []),"discovery_engine":engine,"discovery_query":query[:500],"first_seen_at":now(),"last_seen_at":now(),"probe":{"ok":False,"machine_readable":False,"checked_at":None},"status":"candidate"}
    x["score"]=score(x); return x

def probe(x):
    url=safe_url(x["url"],True)
    if not url: x["probe"]={"ok":False,"machine_readable":False,"checked_at":now(),"error":"unsafe URL"}; return
    try:
        q=urllib.request.Request(url,headers={"Accept":"application/json, application/xml, text/csv, text/html;q=0.8","Range":"bytes=0-65535","User-Agent":UA})
        with urllib.request.urlopen(q,timeout=15) as r:
            if not safe_url(r.geturl(),True): raise RuntimeError("unsafe redirect")
            raw=r.read(65537); ct=str(r.headers.get("Content-Type") or "").split(";",1)[0].casefold()
            x["probe"]={"ok":200<=int(r.status)<400,"status":int(r.status),"content_type":ct,"machine_readable":any(y in ct for y in MACHINE),"bytes_sampled":min(len(raw),65536),"checked_at":now()}
            if x["auth"]=="unknown" and x["probe"]["ok"]: x["auth"]="none"
    except Exception as e: x["probe"]={"ok":False,"machine_readable":False,"checked_at":now(),"error":f"{type(e).__name__}: {str(e)[:180]}"}

def query_set(cfg,cursor,limit,regions):
    axes=[list(cfg.get(k) or []) for k in ("protocol_keywords","institution_keywords","sector_keywords","publication_keywords")]+[regions]
    if not all(axes): return [],cursor
    total=1
    for a in axes: total*=len(a)
    out=[]
    for d in range(limit):
        n=(cursor+d)%total; vals=[]
        for a in axes: vals.append(a[n%len(a)]); n//=len(a)
        p,i,s,r,g=vals; out.append(f'"{p}" "{s}" ({i} OR "{r}") "{g}"')
    return out,(cursor+limit)%total

def countries(cfg,offline):
    fallback=list(cfg.get("regional_language_keywords") or [])
    if offline: return fallback
    try:
        d=request_json("https://api.worldbank.org/v2/country?format=json&per_page=400",max_bytes=2000000)
        return fallback+sorted({str(x["name"]) for x in d[1] if x.get("region",{}).get("id")!="NA" and x.get("name")})
    except Exception: return fallback

def apis_guru(cfg,cursor):
    d=request_json("https://api.apis.guru/v2/list.json",max_bytes=12000000); services=sorted(d.items()); out=[]
    if not services: return out,cursor
    batch=min(int(cfg.get("apis_guru_batch_size") or 120),len(services))
    for z in range(batch):
        name,s=services[(cursor+z)%len(services)]; versions=s.get("versions") or {}
        if not versions: continue
        item=versions[sorted(versions)[-1]]; info=item.get("info") or {}; x=make(item.get("swaggerUrl") or item.get("swaggerYamlUrl"),info.get("title") or name,info.get("description") or "","apis.guru","rotating catalog",cfg)
        if x: x["source_type"]="openapi"; out.append(x)
    return out,(cursor+batch)%len(services)

def search(engine,q,token):
    if engine=="github": d=request_json("https://api.github.com/search/code?"+urllib.parse.urlencode({"q":q+" (openapi OR swagger OR api OR mcp OR data)","per_page":10}),headers={"Authorization":f"Bearer {token}","X-GitHub-Api-Version":"2022-11-28"})
    elif engine=="tavily": d=request_json("https://api.tavily.com/search","POST",{"api_key":token,"query":q,"search_depth":"advanced","max_results":8,"include_answer":False,"include_raw_content":False})
    else: d=request_json("https://api.exa.ai/search","POST",{"query":q,"numResults":8,"type":"auto","contents":{"text":{"maxCharacters":800}}},{"x-api-key":token})
    return list(d.get("items") or d.get("results") or [])
def extract(engine,q,items,cfg):
    out=[]
    for a in items:
        title=str(a.get("title") or a.get("name") or a.get("path") or ""); text=str(a.get("content") or a.get("text") or a.get("description") or "")
        for url in ([str(a[k]) for k in ("url","html_url","homepage") if a.get(k)]+URL_RE.findall(text))[:6]:
            x=make(url,title,text,engine,q,cfg)
            if x: out.append(x)
    return out

def decide(x,cfg):
    x["score"]=score(x); ok=x["score"]>=int(cfg.get("auto_integrate_score") or 72) and x["trusted_domain"] and x["auth"]=="none" and x["license"]!="prohibited" and x["probe"].get("ok") and x["source_type"] in set(cfg.get("allowed_source_types") or [])
    if ok: x.update(status="integrated",integration_mode="fixed-url-read-only-registry",integrated_at=x.get("integrated_at") or now())
    elif x["auth"]=="required" and x["high_value"] and x["score"]>=int(cfg.get("key_notification_score") or 78): x.update(status="key_required_high_value",integration_mode="notification_only")
    else: x.update(status="candidate",integration_mode="manual_or_future_validation")

def notify(rows,report_url):
    if not rows: return True,"no keyed candidates"
    key=str(os.getenv("SERVERCHAN_SENDKEY") or os.getenv("SERVERCHAN_KEY") or os.getenv("SCKEY") or "").strip(); reason="Server酱 SendKey is not configured"
    if key:
        try:
            text="\n".join(f"- **{x['title']}**（{x['score']}分）\n  {x['url']}" for x in rows[:20]); data=urllib.parse.urlencode({"title":f"情报中心发现 {len(rows)} 个高价值需 Key 来源","desp":text+(f"\n\n完整报告：{report_url}" if report_url else "")}).encode()
            with urllib.request.urlopen(urllib.request.Request(f"https://sctapi.ftqq.com/{urllib.parse.quote(key,safe='')}.send",data=data,headers={"Content-Type":"application/x-www-form-urlencoded","User-Agent":UA},method="POST"),timeout=20) as r:
                if json.loads(r.read(100000).decode(errors="replace")).get("code")==0: return True,"Server酱 delivered"
            reason="Server酱 returned non-zero code"
        except Exception as e: reason=f"Server酱 failed: {type(e).__name__}"
    token,repo=str(os.getenv("GITHUB_TOKEN") or ""),str(os.getenv("GITHUB_REPOSITORY") or "")
    if token and "/" in repo:
        try:
            h={"Authorization":f"Bearer {token}","X-GitHub-Api-Version":"2022-11-28"}; body=reason+"\n\n"+"\n".join(f"- **{x['title']}** | {x['score']}分 | {x['url']}" for x in rows[:30]); found=request_json("https://api.github.com/search/issues?"+urllib.parse.urlencode({"q":f'repo:{repo} is:issue is:open in:title "[source-discovery-key]"',"per_page":1}),headers=h); items=found.get("items") or []
            if items: request_json(f"https://api.github.com/repos/{repo}/issues/{items[0]['number']}/comments","POST",{"body":body},h)
            else: request_json(f"https://api.github.com/repos/{repo}/issues","POST",{"title":f"[source-discovery-key] {datetime.now(timezone.utc).date()} 高价值需 Key 来源","body":body},h)
            reason+="; GitHub issue fallback recorded"
        except Exception as e: reason+=f"; issue fallback failed: {type(e).__name__}"
    return False,reason

def run(a):
    cfg=load(a.config,{}); reg=load(a.registry,{"sources":[]}); cand=load(a.candidates,{"candidates":[]}); state=load(a.state,{"query_cursor":0,"apis_guru_cursor":0,"runs":0}); rows={x["source_id"]:dict(x) for x in list(reg.get("sources") or [])+list(cand.get("candidates") or []) if x.get("source_id")}; qs,nextq=query_set(cfg,int(state.get("query_cursor") or 0),a.max_queries or int(cfg.get("daily_query_limit") or 24),countries(cfg,a.offline)); found=[]; errors=[]; nextapi=int(state.get("apis_guru_cursor") or 0)
    if not a.offline:
        try: x,nextapi=apis_guru(cfg,nextapi); found+=x
        except Exception as e: errors.append(f"apis.guru: {type(e).__name__}: {str(e)[:180]}")
        tokens={"github":str(os.getenv("GITHUB_TOKEN") or ""),"tavily":str(os.getenv("TAVILY_API_KEY") or ""),"exa":str(os.getenv("EXA_API_KEY") or "")}; counts={k:0 for k in tokens}; limits={"github":len(qs),"tavily":min(8,len(qs)),"exa":min(8,len(qs))}
        for n,q in enumerate(qs):
            for engine,token in tokens.items():
                if not token or counts[engine]>=limits[engine] or (engine=="tavily" and n%3!=0) or (engine=="exa" and n%3!=1): continue
                counts[engine]+=1
                try: found+=extract(engine,q,search(engine,q,token),cfg)
                except Exception as e: errors.append(f"{engine}: {type(e).__name__}: {str(e)[:160]}")
    for x in found[:int(cfg.get("max_new_candidates_per_run") or 500)]:
        old=rows.get(x["source_id"])
        if old: old["last_seen_at"]=x["last_seen_at"]; old["trusted_domain"]|=x["trusted_domain"]; old["high_value"]|=x["high_value"]
        else: rows[x["source_id"]]=x
    probed=0
    if not a.offline:
        for x in sorted(rows.values(),key=lambda z:(z.get("probe",{}).get("checked_at") is not None,-int(z.get("score") or 0))):
            if probed>=int(cfg.get("max_probe_count_per_run") or 80): break
            if x["license"]=="prohibited" or (x["source_type"]=="remote_mcp" and not x["trusted_domain"]): continue
            probe(x); probed+=1
            if x["source_type"]=="openapi" and x["probe"].get("ok"):
                try:
                    spec=request_json(x["url"],max_bytes=2000000); c=spec.get("components") or {}; x["auth"]="required" if c.get("securitySchemes") or spec.get("securityDefinitions") or spec.get("security") else "none"
                except Exception: pass
    for x in rows.values(): decide(x,cfg)
    registry=sorted((x for x in rows.values() if x["status"]=="integrated"),key=lambda x:x["source_id"]); candidates=sorted((x for x in rows.values() if x["status"]!="integrated"),key=lambda x:(-x["score"],x["source_id"])); finished=now(); save(a.registry,{"schema_version":"global-source-registry-v1","updated_at":finished,"source_count":len(registry),"sources":registry}); save(a.candidates,{"schema_version":"global-source-candidates-v1","updated_at":finished,"candidate_count":len(candidates),"candidates":candidates}); state.update(schema_version="global-source-discovery-state-v1",query_cursor=nextq,apis_guru_cursor=nextapi,runs=int(state.get("runs") or 0)+1,last_run_at=finished,last_errors=errors[-50:]); save(a.state,state); keyed=[x for x in candidates if x["status"]=="key_required_high_value"]; lines=["# 全球来源自动发现日报","",f"- 运行时间：{finished}",f"- 查询数：{len(qs)}",f"- 本轮发现：{len(found)}",f"- 本轮探测：{probed}",f"- 已自动接入：{len(registry)}",f"- 高价值需 Key：{len(keyed)}",f"- 非阻断错误：{len(errors)}","","仅固定 HTTPS、只读、无需 Key、可信机构域名、条款未禁止且有界探测通过的来源进入执行注册表。未知 MCP 包、命令、Docker/npm/pip 安装、写操作和任意 URL 均不会自动执行。"]
    if registry: lines+=["","## 最近自动接入",""]+[f"- `{x['source_id']}` | {x['source_type']} | {x['score']} | {x['title']} | {x['url']}" for x in registry[-25:]]
    if keyed: lines+=["","## 高价值需 Key",""]+[f"- {x['score']} | {x['title']} | {x['url']}" for x in keyed[:25]]
    if errors: lines+=["","## 非阻断错误",""]+[f"- {x}" for x in errors[:20]]
    a.report.write_text("\n".join(lines)+"\n",encoding="utf-8"); delivered,reason=notify(keyed,str(os.getenv("DISCOVERY_REPORT_URL") or "")); print(json.dumps({"status":"completed","queries":len(qs),"discovered":len(found),"probed":probed,"integrated":len(registry),"candidates":len(candidates),"keyed":len(keyed),"serverchan":{"delivered":delivered,"reason":reason},"errors":errors},ensure_ascii=False)); return 0

def main(argv):
    p=argparse.ArgumentParser()
    for n in ("config","registry","candidates","state","report"): p.add_argument(f"--{n}",type=Path,required=True)
    p.add_argument("--max-queries",type=int,default=0); p.add_argument("--offline",action="store_true"); return run(p.parse_args(argv))
if __name__=="__main__": raise SystemExit(main(sys.argv[1:]))
