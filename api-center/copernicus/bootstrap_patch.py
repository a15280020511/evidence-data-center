#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one marker, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def fix_provider_catalog() -> None:
    path = ROOT / "api-center/copernicus/provider-catalog.json"
    catalog = json.loads(path.read_text(encoding="utf-8"))
    provider = catalog["providers"][0]
    render_schema = copy.deepcopy(provider.pop("$defs")["renderParameters"])
    for operation in provider["operations"]:
        schema = operation.get("parameter_schema")
        if isinstance(schema, dict) and schema.get("$ref") == "#/$defs/renderParameters":
            operation["parameter_schema"] = copy.deepcopy(render_schema)
    path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_build_catalog() -> None:
    path = ROOT / "api-center/build_catalog_market_search.py"
    replace_once(
        path,
        'METNO_GEOSATELLITE_CATALOG = HERE / "metno-geosatellite/provider-catalog.json"\n',
        'METNO_GEOSATELLITE_CATALOG = HERE / "metno-geosatellite/provider-catalog.json"\nCOPERNICUS_CATALOG = HERE / "copernicus/provider-catalog.json"\n',
        "catalog constant",
    )
    replace_once(
        path,
        '    "metno-geosatellite": 4,\n',
        '    "metno-geosatellite": 4,\n    "copernicus-cdse": 7,\n',
        "expected count",
    )
    replace_once(
        path,
        '    METNO_GEOSATELLITE_CATALOG,\n',
        '    METNO_GEOSATELLITE_CATALOG,\n    COPERNICUS_CATALOG,\n',
        "catalog path tuple",
    )
    replace_once(
        path,
        '        "metno-geosatellite/provider-catalog.json",\n',
        '        "metno-geosatellite/provider-catalog.json",\n        "copernicus/provider-catalog.json",\n',
        "reading order",
    )


def patch_tests() -> None:
    path = ROOT / "api-center/tests/test_api_catalog.py"
    replace_once(path, '    "metno-geosatellite": 4,\n', '    "metno-geosatellite": 4,\n    "copernicus-cdse": 7,\n', "catalog test provider")
    replace_once(path, 'catalog["managed_provider_count"], 37', 'catalog["managed_provider_count"], 38', "catalog provider count")
    replace_once(path, 'catalog["enabled_managed_provider_count"], 37', 'catalog["enabled_managed_provider_count"], 38', "enabled provider count")
    replace_once(path, 'catalog["managed_operation_count"], 413', 'catalog["managed_operation_count"], 420', "operation count")
    replace_once(path, '            "nasa": "NASA_API_KEY",\n', '            "nasa": "NASA_API_KEY",\n            "copernicus-cdse": "COPERNICUS_CLIENT_SECRET",\n', "secret map")

    path = ROOT / "api-center/tests/test_capability_maximization.py"
    replace_once(path, '            413,\n', '            420,\n', "capability total")
    replace_once(path, '            "metno-geosatellite": 4,\n', '            "metno-geosatellite": 4,\n            "copernicus-cdse": 7,\n', "capability provider")


def patch_readme() -> None:
    path = ROOT / "api-center/README.md"
    heading = "## 哥白尼数据空间 Copernicus CDSE\n"
    text = path.read_text(encoding="utf-8")
    if heading in text:
        return
    section = """## 哥白尼数据空间 Copernicus CDSE

`api-center/copernicus/` 接入 Copernicus Data Space Ecosystem：

```text
[intel-copernicus]
Repository Variable: COPERNICUS_CLIENT_ID
Repository Secret: COPERNICUS_CLIENT_SECRET
```

公开 STAC 集合目录、区域/时间/云量产品搜索和单产品元数据无需凭据；Sentinel-2 L2A 真彩色、近红外假彩色和 NDVI PNG 渲染使用 OAuth2 Client Credentials。每张票据最多一次公开目录请求，或一次令牌请求加一次处理请求；范围、时间、像素、结果条数和响应体积均有硬上限。不开放任意 evalscript、原始整景批量下载、自动翻页、后台任务、令牌持久化或写操作。

"""
    marker = "## 挪威气象研究所 Geosatellite\n"
    if text.count(marker) != 1:
        raise RuntimeError("README insertion marker not found exactly once")
    path.write_text(text.replace(marker, section + marker, 1), encoding="utf-8")


def main() -> None:
    fix_provider_catalog()
    patch_build_catalog()
    patch_tests()
    patch_readme()
    subprocess.run(["python", "api-center/build_catalog_market_search.py"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
