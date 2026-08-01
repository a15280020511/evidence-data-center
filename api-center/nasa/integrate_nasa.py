#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def patch(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if new in text:
        return
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected exactly one match in {path}: {count} for {old!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


# Deterministic catalog registration.
patch(
    "api-center/build_catalog_market_search.py",
    'MARKETSTACK_CATALOG = HERE / "marketstack/provider-catalog.json"\nKNOWLEDGE_TOOLS_CATALOG',
    'MARKETSTACK_CATALOG = HERE / "marketstack/provider-catalog.json"\nNASA_CATALOG = HERE / "nasa/provider-catalog.json"\nKNOWLEDGE_TOOLS_CATALOG',
)
patch(
    "api-center/build_catalog_market_search.py",
    '    "marketstack": 11,\n    "wolfram-alpha": 4,',
    '    "marketstack": 11,\n    "nasa": 25,\n    "wolfram-alpha": 4,',
)
patch(
    "api-center/build_catalog_market_search.py",
    '    MARKETSTACK_CATALOG,\n    KNOWLEDGE_TOOLS_CATALOG,',
    '    MARKETSTACK_CATALOG,\n    NASA_CATALOG,\n    KNOWLEDGE_TOOLS_CATALOG,',
)
patch(
    "api-center/build_catalog_market_search.py",
    '        "marketstack/provider-catalog.json",\n        "knowledge-tools/provider-catalog.json",',
    '        "marketstack/provider-catalog.json",\n        "nasa/provider-catalog.json",\n        "knowledge-tools/provider-catalog.json",',
)

# Main catalog tests and counts.
patch(
    "api-center/tests/test_api_catalog.py",
    '    "marketstack": 11,\n    "wolfram-alpha": 4,',
    '    "marketstack": 11,\n    "nasa": 25,\n    "wolfram-alpha": 4,',
)
patch(
    "api-center/tests/test_api_catalog.py",
    '        self.assertEqual(catalog["managed_provider_count"], 35)',
    '        self.assertEqual(catalog["managed_provider_count"], 36)',
)
patch(
    "api-center/tests/test_api_catalog.py",
    '        self.assertEqual(catalog["enabled_managed_provider_count"], 35)',
    '        self.assertEqual(catalog["enabled_managed_provider_count"], 36)',
)
patch(
    "api-center/tests/test_api_catalog.py",
    '        self.assertEqual(catalog["managed_operation_count"], 384)',
    '        self.assertEqual(catalog["managed_operation_count"], 409)',
)
patch(
    "api-center/tests/test_api_catalog.py",
    '            "marketstack": "MARKETSTACK_ACCESS_KEY",\n            "wolfram-alpha":',
    '            "marketstack": "MARKETSTACK_ACCESS_KEY",\n            "nasa": "NASA_API_KEY",\n            "wolfram-alpha":',
)
patch(
    "api-center/tests/test_api_catalog.py",
    '\n\n        aisstream = providers["aisstream"]',
    '''\n\n        nasa = providers["nasa"]
        self.assertEqual(nasa["ticket_prefix"], "[intel-nasa]")
        self.assertEqual(
            nasa["required_secret_environment_variable_name"],
            "NASA_API_KEY",
        )
        self.assertEqual(len(nasa["operations"]), 25)
        self.assertEqual(nasa["limits"]["requests_per_ticket_max"], 1)
        self.assertEqual(nasa["limits"]["neo_feed_span_days_max"], 7)
        self.assertEqual(nasa["limits"]["donki_date_span_days_max"], 31)
        self.assertEqual(nasa["limits"]["gibs_tiles_per_ticket_max"], 1)
        self.assertFalse(nasa["limits"]["bulk_download_allowed"])
        self.assertFalse(nasa["limits"]["archived_earth_api_allowed"])
        self.assertFalse(nasa["limits"]["archived_mars_rover_api_allowed"])
        self.assertFalse(nasa["limits"]["write_operations_allowed"])

        aisstream = providers["aisstream"]''',
)

# Capability maximization regression.
patch(
    "api-center/tests/test_capability_maximization.py",
    '            384,',
    '            409,',
)
patch(
    "api-center/tests/test_capability_maximization.py",
    '            "marketstack": 11,\n            "wolfram-alpha": 4,',
    '            "marketstack": 11,\n            "nasa": 25,\n            "wolfram-alpha": 4,',
)
patch(
    "api-center/tests/test_capability_maximization.py",
    '\n        east_asia = json.loads(',
    '''
        nasa = json.loads(
            (ROOT / "nasa/provider-catalog.json").read_text(encoding="utf-8")
        )
        nasa_provider = nasa["providers"][0]
        nasa_limits = nasa_provider["limits"]
        self.assertEqual(
            nasa_provider["required_secret_environment_variable"],
            "NASA_API_KEY",
        )
        self.assertEqual(nasa_limits["requests_per_ticket_max"], 1)
        self.assertEqual(nasa_limits["gibs_tiles_per_ticket_max"], 1)
        self.assertFalse(nasa_limits["automatic_pagination_allowed"])
        self.assertFalse(nasa_limits["bulk_download_allowed"])
        self.assertFalse(nasa_limits["arbitrary_urls_allowed"])
        self.assertFalse(nasa_limits["archived_earth_api_allowed"])
        self.assertFalse(nasa_limits["archived_mars_rover_api_allowed"])
        self.assertFalse(nasa_limits["write_operations_allowed"])

        east_asia = json.loads(''',
)

# Human documentation and credential contract.
patch(
    "api-center/README.md",
    'MARKETSTACK_ACCESS_KEY\nXWEATHER_CLIENT_SECRET',
    'MARKETSTACK_ACCESS_KEY\nNASA_API_KEY\nXWEATHER_CLIENT_SECRET',
)
patch(
    "api-center/README.md",
    '\n## World Bank 世界银行开放数据\n',
    '''
## NASA Open APIs 与 Earthdata GIBS

`api-center/nasa/` 固定访问 NASA 官方只读主机：

```text
[intel-nasa]
NASA_API_KEY
```

固定开放 25 项操作，覆盖 APOD、近地小行星 NeoWs、DONKI 空间天气、EPIC 地球影像元数据、NASA 图像与视频资料库，以及 Earthdata GIBS 的 WMTS/WMS 能力、图层元数据和单瓦片影像。旧 Earth API 和 Mars Rover Photos API 已归档，不予接入；地球影像由官方替代的 GIBS 提供。每张票据只发送一次请求、不自动重试或翻页，GIBS 每票据最多一张瓦片，禁止整图层下载、任意 URL、后台轮询和写入。

## World Bank 世界银行开放数据
''',
)
patch(
    "api-center/SECRET_ISOLATION_POLICY.md",
    'MARKETSTACK_ACCESS_KEY\nXWEATHER_CLIENT_SECRET',
    'MARKETSTACK_ACCESS_KEY\nNASA_API_KEY\nXWEATHER_CLIENT_SECRET',
)
patch(
    "api-center/SECRET_ISOLATION_POLICY.md",
    '\n## AISstream\n',
    '''
## NASA Open APIs

```text
Repository Secret: NASA_API_KEY
```

该Key只允许作为`api_key`查询参数注入`https://api.nasa.gov`的固定只读端点。NASA Image Library与Earthdata GIBS为免密固定主机，不接收该Key。旧Earth API和Mars Rover Photos API已归档且禁止调用；Key不得进入Issue、目录、日志、诊断或Artifact。

## AISstream
''',
)

subprocess.run(["python", "api-center/build_config.py"], cwd=ROOT, check=True)
subprocess.run(["python", "api-center/build_catalog_market_search.py"], cwd=ROOT, check=True)
subprocess.run(["python", "-m", "compileall", "-q", "api-center"], cwd=ROOT, check=True)
subprocess.run(
    ["python", "-m", "unittest", "discover", "-s", "api-center/nasa/tests", "-p", "test_*.py", "-v"],
    cwd=ROOT,
    check=True,
)
subprocess.run(
    ["python", "-m", "unittest", "discover", "-s", "api-center/tests", "-p", "test_*.py", "-v"],
    cwd=ROOT,
    check=True,
)
