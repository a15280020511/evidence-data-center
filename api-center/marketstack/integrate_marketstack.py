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
    'INTERNET_ARCHIVE_CATALOG = HERE / "internet-archive/provider-catalog.json"\nKNOWLEDGE_TOOLS_CATALOG',
    'INTERNET_ARCHIVE_CATALOG = HERE / "internet-archive/provider-catalog.json"\nMARKETSTACK_CATALOG = HERE / "marketstack/provider-catalog.json"\nKNOWLEDGE_TOOLS_CATALOG',
)
patch(
    "api-center/build_catalog_market_search.py",
    '    "internet-archive": 6,\n    "wolfram-alpha": 4,',
    '    "internet-archive": 6,\n    "marketstack": 11,\n    "wolfram-alpha": 4,',
)
patch(
    "api-center/build_catalog_market_search.py",
    '    INTERNET_ARCHIVE_CATALOG,\n    KNOWLEDGE_TOOLS_CATALOG,',
    '    INTERNET_ARCHIVE_CATALOG,\n    MARKETSTACK_CATALOG,\n    KNOWLEDGE_TOOLS_CATALOG,',
)
patch(
    "api-center/build_catalog_market_search.py",
    '        "internet-archive/provider-catalog.json",\n        "knowledge-tools/provider-catalog.json",',
    '        "internet-archive/provider-catalog.json",\n        "marketstack/provider-catalog.json",\n        "knowledge-tools/provider-catalog.json",',
)

# Main catalog tests and counts.
patch(
    "api-center/tests/test_api_catalog.py",
    '    "internet-archive": 6,\n    "wolfram-alpha": 4,',
    '    "internet-archive": 6,\n    "marketstack": 11,\n    "wolfram-alpha": 4,',
)
patch(
    "api-center/tests/test_api_catalog.py",
    '        self.assertEqual(catalog["managed_provider_count"], 34)',
    '        self.assertEqual(catalog["managed_provider_count"], 35)',
)
patch(
    "api-center/tests/test_api_catalog.py",
    '        self.assertEqual(catalog["enabled_managed_provider_count"], 34)',
    '        self.assertEqual(catalog["enabled_managed_provider_count"], 35)',
)
patch(
    "api-center/tests/test_api_catalog.py",
    '        self.assertEqual(catalog["managed_operation_count"], 373)',
    '        self.assertEqual(catalog["managed_operation_count"], 384)',
)
patch(
    "api-center/tests/test_api_catalog.py",
    '            "aisstream": "AISSTREAM_API_KEY",\n            "wolfram-alpha":',
    '            "aisstream": "AISSTREAM_API_KEY",\n            "marketstack": "MARKETSTACK_ACCESS_KEY",\n            "wolfram-alpha":',
)
patch(
    "api-center/tests/test_api_catalog.py",
    '\n\n        aisstream = providers["aisstream"]',
    '''\n\n        marketstack = providers["marketstack"]
        self.assertEqual(marketstack["ticket_prefix"], "[intel-marketstack]")
        self.assertEqual(
            marketstack["required_secret_environment_variable_name"],
            "MARKETSTACK_ACCESS_KEY",
        )
        self.assertEqual(len(marketstack["operations"]), 11)
        self.assertEqual(marketstack["limits"]["fixed_api_host"], "api.marketstack.com")
        self.assertEqual(marketstack["limits"]["free_plan_requests_per_month"], 100)
        self.assertEqual(marketstack["limits"]["historical_span_days_max"], 366)
        self.assertFalse(marketstack["limits"]["automatic_pagination_allowed"])
        self.assertFalse(marketstack["limits"]["intraday_or_realtime_operations_allowed"])
        self.assertFalse(marketstack["limits"]["write_operations_allowed"])
        self.assertFalse(marketstack["limits"]["trading_or_order_execution_allowed"])

        aisstream = providers["aisstream"]''',
)

# Capability maximization regression.
patch(
    "api-center/tests/test_capability_maximization.py",
    '            373,',
    '            384,',
)
patch(
    "api-center/tests/test_capability_maximization.py",
    '            "internet-archive": 6,\n            "wolfram-alpha": 4,',
    '            "internet-archive": 6,\n            "marketstack": 11,\n            "wolfram-alpha": 4,',
)
patch(
    "api-center/tests/test_capability_maximization.py",
    '\n        east_asia = json.loads(',
    '''
        marketstack = json.loads(
            (ROOT / "marketstack/provider-catalog.json").read_text(encoding="utf-8")
        )
        marketstack_provider = marketstack["providers"][0]
        self.assertEqual(
            marketstack_provider["required_secret_environment_variable"],
            "MARKETSTACK_ACCESS_KEY",
        )
        self.assertEqual(marketstack_provider["limits"]["requests_per_ticket_max"], 1)
        self.assertEqual(marketstack_provider["limits"]["symbols_per_ticket_max"], 5)
        self.assertFalse(marketstack_provider["limits"]["automatic_pagination_allowed"])
        self.assertFalse(marketstack_provider["limits"]["intraday_or_realtime_operations_allowed"])
        self.assertFalse(marketstack_provider["limits"]["write_operations_allowed"])
        self.assertFalse(
            marketstack_provider["limits"]["trading_or_order_execution_allowed"]
        )

        east_asia = json.loads(''',
)

# Unified CI dependency, tests and invariants.
patch(
    ".github/workflows/api-catalog-validate.yml",
    '            api-center/internet-archive/requirements.txt\n',
    '            api-center/internet-archive/requirements.txt\n            api-center/marketstack/requirements.txt\n',
)
patch(
    ".github/workflows/api-catalog-validate.yml",
    '            -r api-center/internet-archive/requirements.txt\n',
    '            -r api-center/internet-archive/requirements.txt \\\n            -r api-center/marketstack/requirements.txt\n',
)
patch(
    ".github/workflows/api-catalog-validate.yml",
    "          python -m unittest discover -s api-center/internet-archive/tests -p 'test_*.py' -v\n          python -m unittest discover -s api-center/tests",
    "          python -m unittest discover -s api-center/internet-archive/tests -p 'test_*.py' -v\n          python -m unittest discover -s api-center/marketstack/tests -p 'test_*.py' -v\n          python -m unittest discover -s api-center/tests",
)
patch(
    ".github/workflows/api-catalog-validate.yml",
    "          assert catalog['managed_provider_count'] == len(providers) == 34",
    "          assert catalog['managed_provider_count'] == len(providers) == 35",
)
patch(
    ".github/workflows/api-catalog-validate.yml",
    "          assert catalog['enabled_managed_provider_count'] == 34",
    "          assert catalog['enabled_managed_provider_count'] == 35",
)
patch(
    ".github/workflows/api-catalog-validate.yml",
    "          ) == 373",
    "          ) == 384",
)
patch(
    ".github/workflows/api-catalog-validate.yml",
    "\n          aisstream = providers['aisstream']",
    '''
          marketstack = providers['marketstack']
          assert marketstack['ticket_prefix'] == '[intel-marketstack]'
          assert marketstack['required_secret_environment_variable_name'] == 'MARKETSTACK_ACCESS_KEY'
          assert len(marketstack['operations']) == 11
          assert marketstack['limits']['requests_per_ticket_max'] == 1
          assert marketstack['limits']['free_plan_requests_per_month'] == 100
          assert marketstack['limits']['historical_span_days_max'] == 366
          assert marketstack['limits']['automatic_pagination_allowed'] is False
          assert marketstack['limits']['intraday_or_realtime_operations_allowed'] is False
          assert marketstack['limits']['write_operations_allowed'] is False

          aisstream = providers['aisstream']''',
)
patch(
    ".github/workflows/api-catalog-validate.yml",
    "              'managed_providers': 34,\n              'managed_operations': 373,",
    "              'managed_providers': 35,\n              'managed_operations': 384,",
)
patch(
    ".github/workflows/api-catalog-validate.yml",
    "              'internet_archive_operations': 6,\n              'removed_providers'",
    "              'internet_archive_operations': 6,\n              'marketstack_operations': 11,\n              'removed_providers'",
)

# Human documentation and credential contract.
patch(
    "api-center/README.md",
    'ALPHAFEED_API_KEY\nXWEATHER_CLIENT_SECRET',
    'ALPHAFEED_API_KEY\nMARKETSTACK_ACCESS_KEY\nXWEATHER_CLIENT_SECRET',
)
patch(
    "api-center/README.md",
    '\n## World Bank 世界银行开放数据\n',
    '''
## Marketstack 全球股票 EOD 与免费历史数据

`api-center/marketstack/` 固定访问 Marketstack v2 HTTPS REST API：

```text
[intel-marketstack]
MARKETSTACK_ACCESS_KEY
```

固定开放 11 项免费计划只读能力，覆盖最新 EOD、最大一年历史 EOD、指定日期 EOD、拆股、分红、证券目录、单一证券信息、交易所、币种和时区。为保护免费计划每月 100 次请求额度，每张票据只发送一次请求、不自动重试或翻页、最多 5 个证券代码、历史跨度最多 366 天。盘中、实时轮询、债券、ETF、商品、企业基本面、EDGAR、交易和写入能力均不开放。

## World Bank 世界银行开放数据
''',
)
patch(
    "api-center/SECRET_ISOLATION_POLICY.md",
    'ALPHAFEED_API_KEY\nXWEATHER_CLIENT_SECRET',
    'ALPHAFEED_API_KEY\nMARKETSTACK_ACCESS_KEY\nXWEATHER_CLIENT_SECRET',
)
patch(
    "api-center/SECRET_ISOLATION_POLICY.md",
    '\n## AISstream\n',
    '''
## Marketstack

```text
Repository Secret: MARKETSTACK_ACCESS_KEY
```

该Key只允许作为`access_key`查询参数注入`https://api.marketstack.com/v2`的11项固定免费计划GET端点。客户端不得提交或覆盖Key；Key不得进入Issue、目录、日志、诊断或Artifact。每张票据单请求、不自动重试，最多5个证券代码和366天历史范围。

## AISstream
''',
)

subprocess.run(["python", "api-center/build_config.py"], cwd=ROOT, check=True)
subprocess.run(["python", "api-center/build_catalog_market_search.py"], cwd=ROOT, check=True)
subprocess.run(["python", "-m", "compileall", "-q", "api-center"], cwd=ROOT, check=True)
subprocess.run(
    ["python", "-m", "unittest", "discover", "-s", "api-center/marketstack/tests", "-p", "test_*.py", "-v"],
    cwd=ROOT,
    check=True,
)
subprocess.run(
    ["python", "-m", "unittest", "discover", "-s", "api-center/tests", "-p", "test_*.py", "-v"],
    cwd=ROOT,
    check=True,
)
