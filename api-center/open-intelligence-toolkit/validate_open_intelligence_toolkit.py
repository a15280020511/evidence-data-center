#!/usr/bin/env python3
import argparse,json,os,tempfile
from pathlib import Path
import open_intelligence_toolkit_task as runtime
SAMPLES={'catalog-capabilities': {}, 'source-access-matrix': {}, 'toolchain-status': {}, 'common-crawl-collinfo': {}, 'common-crawl-index': {'index': 'CC-MAIN-2026-30', 'url': 'example.com', 'limit': 2}, 'gdacs-events': {}, 'bls-series': {'series_ids': ['CUUR0000SA0'], 'start_year': 2024, 'end_year': 2025}, 'ecb-sdmx-data': {'flow': 'EXR', 'key': 'D.USD.EUR.SP00.A', 'format': 'csvdata'}, 'wikimedia-pageviews': {'project': 'en.wikipedia.org', 'article': 'Artificial_intelligence', 'start': '20260801', 'end': '20260802'}, 'hackernews-topstories': {'limit': 5}, 'hackernews-item': {'item_id': 1}, 'ror-search': {'query': 'OpenAI', 'limit': 5}, 'uk-legislation-search': {'title': 'data protection', 'limit': 5}, 'ted-search': {'query': 'text ~ "artificial intelligence"', 'limit': 5}, 'ckan-package-search': {'portal': 'uk', 'query': 'transport', 'limit': 5}, 'socrata-dataset-rows': {'portal': 'cdc', 'dataset_id': '9mfq-cb36', 'limit': 5}, 'stackexchange-search': {'query': 'python json', 'site': 'stackoverflow', 'limit': 5}, 'bluesky-search-posts': {'query': 'open data', 'limit': 5}, 'cas-data-centers': {}, 'html-structure-extract': {'base_url': 'https://example.com/', 'html': '<html><head><title>Example</title><script type=\'application/ld+json\'>{"@type":"Article","headline":"Example"}</script></head><body><main><h1>Example</h1><p>This is a sufficiently long article paragraph for deterministic extraction and validation.</p></main></body></html>'}}
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
