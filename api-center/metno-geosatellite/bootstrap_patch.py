#!/usr/bin/env python3
"""One-shot repository patch for MET Norway Geosatellite integration."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/api-catalog-validate.yml"
README = ROOT / "api-center/README.md"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one marker, found {count}")
    return text.replace(old, new, 1)


def patch_workflow() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "            api-center/nasa/requirements.txt\n",
        "            api-center/nasa/requirements.txt\n"
        "            api-center/metno-geosatellite/requirements.txt\n",
        "cache dependency",
    )
    text = replace_once(
        text,
        "            -r api-center/nasa/requirements.txt\n",
        "            -r api-center/nasa/requirements.txt \\\n"
        "            -r api-center/metno-geosatellite/requirements.txt\n",
        "dependency install",
    )
    text = replace_once(
        text,
        "          python -m unittest discover -s api-center/nasa/tests -p 'test_*.py' -v\n"
        "          python -m unittest discover -s api-center/tests -p 'test_*.py' -v\n",
        "          python -m unittest discover -s api-center/nasa/tests -p 'test_*.py' -v\n"
        "          python -m unittest discover -s api-center/metno-geosatellite/tests -p 'test_*.py' -v\n"
        "          python -m unittest discover -s api-center/tests -p 'test_*.py' -v\n",
        "test discovery",
    )
    text = replace_once(
        text,
        "          assert catalog['managed_provider_count'] == len(providers) == 36\n",
        "          assert catalog['managed_provider_count'] == len(providers) == 37\n",
        "provider count",
    )
    text = replace_once(
        text,
        "          assert catalog['enabled_managed_provider_count'] == 36\n",
        "          assert catalog['enabled_managed_provider_count'] == 37\n",
        "enabled provider count",
    )
    text = replace_once(
        text,
        "          ) == 409\n",
        "          ) == 413\n",
        "operation count",
    )
    metno_block = """          metno = providers['metno-geosatellite']
          assert metno['ticket_prefix'] == '[intel-metno-geosatellite]'
          assert metno['required_secret_environment_variable_name'] == ''
          assert len(metno['operations']) == 4
          assert metno['limits']['requests_per_ticket_max'] == 1
          assert metno['limits']['fixed_api_host'] == 'api.met.no'
          assert metno['limits']['small_size_images_allowed'] is False
          assert metno['limits']['unfiltered_availability_listing_allowed'] is False
          assert metno['limits']['bulk_download_allowed'] is False
          assert metno['limits']['write_operations_allowed'] is False

"""
    if "          metno = providers['metno-geosatellite']\n" not in text:
        marker = "          aisstream = providers['aisstream']\n"
        if text.count(marker) != 1:
            raise RuntimeError("provider invariant marker not found exactly once")
        text = text.replace(marker, metno_block + marker, 1)
    text = replace_once(
        text,
        "              'managed_providers': 36,\n",
        "              'managed_providers': 37,\n",
        "reported provider count",
    )
    text = replace_once(
        text,
        "              'managed_operations': 409,\n",
        "              'managed_operations': 413,\n",
        "reported operation count",
    )
    text = replace_once(
        text,
        "              'nasa_operations': 25,\n",
        "              'nasa_operations': 25,\n"
        "              'metno_geosatellite_operations': 4,\n",
        "reported metno operations",
    )
    WORKFLOW.write_text(text, encoding="utf-8")


def patch_readme() -> None:
    text = README.read_text(encoding="utf-8")
    heading = "## 挪威气象研究所 Geosatellite\n"
    if heading in text:
        return
    section = """## 挪威气象研究所 Geosatellite

`api-center/metno-geosatellite/` 固定访问 MET Norway 官方 Geosatellite 1.4：

```text
[intel-metno-geosatellite]
无需 Repository Secret
```

固定开放 4 项只读能力：本地能力目录、指定区域/光谱/可选 UTC 时刻的静态 PNG、欧洲 MP4/WebM 卫星动画，以及按区域过滤的静态影像可用清单。请求使用可识别 `User-Agent`，每张票据最多一次 GET，不自动重试或翻页；不开放已于 2026-03-01 移除的 `small` 图、不允许无过滤拉取完整可用清单、任意 URL、后台轮询或写入。数据按 CC BY 4.0 使用并保留 MET Norway 署名。

"""
    marker = "## World Bank 世界银行开放数据\n"
    if text.count(marker) != 1:
        raise RuntimeError("README insertion marker not found exactly once")
    README.write_text(text.replace(marker, section + marker, 1), encoding="utf-8")


def main() -> None:
    patch_workflow()
    patch_readme()
    subprocess.run(
        ["python", "api-center/build_catalog_market_search.py"],
        cwd=ROOT,
        check=True,
    )


if __name__ == "__main__":
    main()
