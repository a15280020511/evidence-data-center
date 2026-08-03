#!/usr/bin/env python3
import argparse,json,os,tempfile
from pathlib import Path
import open_data_aggregators_task as runtime
SAMPLES={"catalog-capabilities":{},"source-access-matrix":{},"gleif-search":{"query":"OpenAI","limit":5},"gdelt-search":{"query":"global trade","limit":5,"timespan":"7d"},"sdmx-eurostat-data":{"dataflow":"nama_10_gdp","key":"A.CLV10_MEUR.B1GQ.EU27_2020","start_period":"2020","end_period":"2025"},"mobility-search":{"query":"Seoul","limit":5},"openalex-search":{"query":"supply chain","limit":5},"datacite-search":{"query":"economic policy","limit":5},"opencitations-citations":{"doi":"10.1038/nphys1170"},"unpaywall-get":{"doi":"10.1038/nphys1170"},"usaspending-search":{"keyword":"semiconductor","start_date":"2025-01-01","end_date":"2026-01-01","limit":5},"transitland-search":{"query":"Seoul","spec":"gtfs","limit":5},"china-data-get":{"dataset":"china-gdp","format":"json"}}
def main():
 p=argparse.ArgumentParser();p.add_argument("--operation",required=True,choices=sorted(SAMPLES));p.add_argument("--output",required=True);a=p.parse_args()
 os.environ.update({"OPEN_DATA_FIXTURE_MODE":"1","OPENALEX_API_KEY":"fixture-openalex","MOBILITY_DATABASE_ACCESS_TOKEN":"fixture-mobility","TRANSITLAND_API_KEY":"fixture-transitland","OPENCITATIONS_TOKEN":"fixture-opencitations","UNPAYWALL_EMAIL":"fixture@example.com"})
 ticket={"task_id":f"fixture-{a.operation}-20260803","provider":"open-data-aggregators","operation":a.operation,"objective":"zero-network validation","parameters":SAMPLES[a.operation],"data_policy":{"classification":"public","contains_personal_data":False},"acceptance":{"timeout_seconds":30,"max_response_bytes":1000000}}
 runtime.validate_ticket(ticket,schema_path=runtime.SCHEMA_PATH,catalog_path=runtime.CATALOG_PATH)
 contract=None
 if a.operation not in {"catalog-capabilities","source-access-matrix"}:
  method,url,headers,query,body,credentials=runtime.build(a.operation,ticket["parameters"]);assert url.startswith("https://");assert method in {"GET","POST"};assert len(credentials)<=1
  contract={"method":method,"origin":"/".join(url.split("/")[:3]),"credential_names":credentials,"has_body":body is not None}
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp);tp=root/"ticket.json";out=root/"out";tp.write_text(json.dumps(ticket,ensure_ascii=False),encoding="utf-8");assert runtime.execute(tp,out)==0
  d=json.loads((out/"diagnostics.json").read_text());m=json.loads((out/"manifest.json").read_text());s=(out/"snapshot.json").read_text()
  assert d["status"]=="INTEL_OPEN_DATA_COMPLETED";assert d["metadata"]["network_used"] is False;assert d["model_calls"]==0;assert m["secret_values_exposed"] is False
  for secret in ["fixture-openalex","fixture-mobility","fixture-transitland","fixture-opencitations","fixture@example.com"]:assert secret not in s
 result={"status":"PASS","operation":a.operation,"network_used":False,"fixture_mode":True,"model_calls":0,"secret_values_exposed":False,"request_contract":contract}
 outp=Path(a.output);outp.parent.mkdir(parents=True,exist_ok=True);outp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
if __name__=="__main__":main()
