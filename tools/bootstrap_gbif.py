#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"pattern not found in {path}: {old[:80]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


builder = ROOT / "api-center/build_catalog_market_search.py"
replace_once(
    builder,
    'COPERNICUS_CATALOG = HERE / "copernicus/provider-catalog.json"\n',
    'COPERNICUS_CATALOG = HERE / "copernicus/provider-catalog.json"\nGBIF_CATALOG = HERE / "gbif/provider-catalog.json"\n',
)
replace_once(
    builder,
    '    "copernicus-cdse": 7,\n',
    '    "copernicus-cdse": 7,\n    "gbif": 10,\n',
)
replace_once(
    builder,
    '    COPERNICUS_CATALOG,\n    KNOWLEDGE_TOOLS_CATALOG,\n',
    '    COPERNICUS_CATALOG,\n    GBIF_CATALOG,\n    KNOWLEDGE_TOOLS_CATALOG,\n',
)
replace_once(
    builder,
    '        "copernicus/provider-catalog.json",\n        "knowledge-tools/provider-catalog.json",\n',
    '        "copernicus/provider-catalog.json",\n        "gbif/provider-catalog.json",\n        "knowledge-tools/provider-catalog.json",\n',
)

api_test = ROOT / "api-center/tests/test_api_catalog.py"
replace_once(
    api_test,
    '    "copernicus-cdse": 7,\n',
    '    "copernicus-cdse": 7,\n    "gbif": 10,\n',
)
replace_once(
    api_test,
    '        self.assertEqual(catalog["managed_provider_count"], 38)\n',
    '        self.assertEqual(catalog["managed_provider_count"], 39)\n',
)
replace_once(
    api_test,
    '        self.assertEqual(catalog["enabled_managed_provider_count"], 38)\n',
    '        self.assertEqual(catalog["enabled_managed_provider_count"], 39)\n',
)
replace_once(
    api_test,
    '        self.assertEqual(catalog["managed_operation_count"], 420)\n',
    '        self.assertEqual(catalog["managed_operation_count"], 430)\n',
)
anchor = '        aisstream = providers["aisstream"]\n'
block = '''        gbif = providers["gbif"]
        self.assertEqual(gbif["ticket_prefix"], "[intel-gbif]")
        self.assertEqual(gbif["required_secret_environment_variable_name"], "")
        self.assertEqual(len(gbif["operations"]), 10)
        self.assertEqual(gbif["limits"]["fixed_api_host"], "api.gbif.org")
        self.assertEqual(gbif["limits"]["occurrence_page_size_max"], 300)
        self.assertFalse(gbif["limits"]["automatic_pagination_allowed"])
        self.assertFalse(gbif["limits"]["authenticated_occurrence_downloads_allowed"])
        self.assertFalse(gbif["limits"]["bulk_download_allowed"])
        self.assertFalse(gbif["limits"]["write_operations_allowed"])

'''
replace_once(api_test, anchor, block + anchor)

cap_test = ROOT / "api-center/tests/test_capability_maximization.py"
replace_once(cap_test, '            420,\n', '            430,\n')
replace_once(
    cap_test,
    '            "copernicus-cdse": 7,\n',
    '            "copernicus-cdse": 7,\n            "gbif": 10,\n',
)

readme = ROOT / "api-center/README.md"
text = readme.read_text(encoding="utf-8")
section = '''
## 全球生物多样性信息设施 GBIF

`api-center/gbif/` 接入GBIF官方公开REST API：

```text
[intel-gbif]
无需API Key
```

固定开放10项只读操作，覆盖物种名称匹配、分类检索、出现记录的有限时空搜索与计数、单记录读取以及数据集元数据查询。每票据最多一次请求，出现记录单页最多300条，不自动翻页；不开放需要账号的异步Occurrence Download、批量导出、发布、修改、删除、实验端点或网页抓取。
'''
if "## 全球生物多样性信息设施 GBIF" not in text:
    readme.write_text(text.rstrip() + "\n" + section, encoding="utf-8")

subprocess.run(
    ["python", "api-center/build_catalog_market_search.py"],
    cwd=ROOT,
    check=True,
)
