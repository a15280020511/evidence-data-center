from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOCKED = {"nbs-search", "nbs-query-data", "nbs-new-tree", "nbs-new-indicators"}


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"missing patch anchor in {path}: {old!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


catalog_path = ROOT / "api-center/public-data-geospatial/provider-catalog.json"
catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
provider = catalog["providers"][0]
provider["operations"] = [row for row in provider["operations"] if row["operation_id"] not in BLOCKED]
provider["limits"]["china_first_operations"] = [
    row for row in provider["limits"].get("china_first_operations", []) if row not in BLOCKED
]
provider["limits"]["known_upstream_constraints"] = [
    {
        "provider": "China National Bureau of Statistics National Data",
        "status": "not_exposed_as_production_operation",
        "reason": "Official upstream WAF returned HTTP 403 UrlACL to the GitHub Actions public-cloud egress during production acceptance on 2026-08-03.",
        "evidence_issue": 527,
    }
]
catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

schema_path = ROOT / "api-center/public-data-geospatial/ticket.schema.json"
schema = json.loads(schema_path.read_text(encoding="utf-8"))
schema["properties"]["operation"]["enum"] = [
    row for row in schema["properties"]["operation"]["enum"] if row not in BLOCKED
]
schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

runtime_path = ROOT / "api-center/public-data-geospatial/public_data_geospatial_task.py"
runtime = runtime_path.read_text(encoding="utf-8")
old_runtime = """    if operation=='nbs-search':
        return Spec('GET','https://data.stats.gov.cn/search.htm',params=[('s',text(p,'query',100,True)),('m','searchdata')])
    if operation=='nbs-query-data':
        q=[('m','QueryData'),('dbcode',text(p,'dbcode',4,True)),('rowcode',text(p,'rowcode',4,True)),('colcode',text(p,'colcode',4,True)),('wds',json.dumps(p.get('wds') or [],ensure_ascii=False,separators=(',',':'))),('dfwds',json.dumps(p.get('dfwds') or [],ensure_ascii=False,separators=(',',':'))),('k1',str(int(time.time()*1000))),('h','1')]
        return Spec('GET','https://data.stats.gov.cn/easyquery.htm',params=q,headers={'Referer':'https://data.stats.gov.cn/'})
    if operation=='nbs-new-tree':
        return Spec('GET','https://data.stats.gov.cn/dg/website/publicrelease/web/external/new/queryIndexTreeAsync',params=[('pid',text(p,'parent_id',80)),('code',str(integer(p,'code',1,1,14)))],headers={'Referer':'https://data.stats.gov.cn/dg/website/page.html'})
    if operation=='nbs-new-indicators':
        return Spec('GET','https://data.stats.gov.cn/dg/website/publicrelease/web/external/new/queryIndicatorsByCid',params=[('cid',text(p,'catalog_id',80,True)),('dt',''),('name',text(p,'name',100)),('rootId',text(p,'root_id',80))],headers={'Referer':'https://data.stats.gov.cn/dg/website/page.html'})
"""
if old_runtime not in runtime:
    raise SystemExit("NBS runtime block not found")
runtime_path.write_text(runtime.replace(old_runtime, "", 1), encoding="utf-8")

replace_once(
    "api-center/public-data-geospatial/tests/test_public_data_geospatial.py",
    'self.assertEqual(len(c["providers"][0]["operations"]),39)',
    'self.assertEqual(len(c["providers"][0]["operations"]),35)',
)
replace_once(
    "api-center/public-data-geospatial/tests/test_public_data_geospatial.py",
    """    def test_nbs_query_is_fixed_host(self):
        s=mod.build("nbs-query-data",{"dbcode":"hgnd","rowcode":"sj","colcode":"zb","wds":[],"dfwds":[{"wdcode":"zb","valuecode":"A020101"}]})
        self.assertEqual(s.url,"https://data.stats.gov.cn/easyquery.htm")
        self.assertEqual(s.method,"GET")
""",
    """    def test_nbs_waf_blocked_operations_are_not_exposed(self):
        c=json.loads((ROOT/"provider-catalog.json").read_text())
        operation_ids={row["operation_id"] for row in c["providers"][0]["operations"]}
        self.assertTrue({"nbs-search","nbs-query-data","nbs-new-tree","nbs-new-indicators"}.isdisjoint(operation_ids))
        with self.assertRaises(ValueError): mod.build("nbs-search",{"query":"GDP"})
""",
)

replace_once(
    "api-center/build_catalog_market_search.py",
    '    "public-data-geospatial": 39,',
    '    "public-data-geospatial": 35,',
)
replace_once(
    "api-center/tests/test_api_catalog.py",
    '    "public-data-geospatial": 39,',
    '    "public-data-geospatial": 35,',
)
replace_once(
    "api-center/tests/test_api_catalog.py",
    'catalog["managed_operation_count"], 526',
    'catalog["managed_operation_count"], 522',
)
replace_once(
    "api-center/tests/test_capability_maximization.py",
    '            526,',
    '            522,',
)
replace_once(
    "api-center/tests/test_capability_maximization.py",
    '            "public-data-geospatial": 39,',
    '            "public-data-geospatial": 35,',
)

readme_path = ROOT / "api-center/public-data-geospatial/README.md"
readme = readme_path.read_text(encoding="utf-8")
readme = readme.replace("当前开放 **39** 项固定只读能力", "当前开放 **35** 项固定只读能力")
readme += """

## 中国国家统计局直连状态

2026-08-03 的生产验收中，`data.stats.gov.cn` 对 GitHub Actions 公网出口返回 `HTTP 403 / WAF UrlACL`。因此 `nbs-search`、`nbs-query-data`、`nbs-new-tree`、`nbs-new-indicators` 已从生产票据目录移除，避免向 GPTs 暴露已知不可用能力。中国数据继续通过地方政府开放数据目录、国家科学数据中心目录及现有 AKShare、Tushare、East Asia Econ、World Bank、IMF、OECD、UN、ILO、FAO 等来源提供。
"""
readme_path.write_text(readme, encoding="utf-8")
