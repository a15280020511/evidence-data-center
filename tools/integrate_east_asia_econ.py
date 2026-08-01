#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"expected exactly one match in {path}: {old!r}; found {text.count(old)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> int:
    api_test = ROOT / "api-center/tests/test_api_catalog.py"
    replace_once(api_test, '    "eodhd": 25,\n    "wolfram-alpha": 4,', '    "eodhd": 25,\n    "east-asia-econ": 6,\n    "wolfram-alpha": 4,')
    replace_once(api_test, 'self.assertEqual(catalog["managed_provider_count"], 23)', 'self.assertEqual(catalog["managed_provider_count"], 24)')
    replace_once(api_test, 'self.assertEqual(catalog["enabled_managed_provider_count"], 23)', 'self.assertEqual(catalog["enabled_managed_provider_count"], 24)')
    replace_once(api_test, 'self.assertEqual(catalog["managed_operation_count"], 234)', 'self.assertEqual(catalog["managed_operation_count"], 240)')
    replace_once(api_test, '            "eodhd": "EODHD_API_TOKEN",\n            "wolfram-alpha":', '            "eodhd": "EODHD_API_TOKEN",\n            "east-asia-econ": "EAST_ASIA_ECON_API_KEY",\n            "wolfram-alpha":')
    replace_once(
        api_test,
        '        self.assertFalse(providers["eodhd"]["limits"]["trading_or_order_execution_allowed"])\n\n        self.assertEqual(\n            providers["tushare"]',
        '        self.assertFalse(providers["eodhd"]["limits"]["trading_or_order_execution_allowed"])\n\n        east_asia = providers["east-asia-econ"]\n        self.assertEqual(east_asia["ticket_prefix"], "[api-east-asia-econ]")\n        self.assertEqual(east_asia["required_secret_environment_variable_name"], "EAST_ASIA_ECON_API_KEY")\n        self.assertEqual(east_asia["limits"]["fixed_api_host"], "data-api.eastasiaecon.com")\n        self.assertEqual(east_asia["limits"]["requests_per_ticket_max"], 1)\n        self.assertFalse(east_asia["limits"]["arbitrary_urls_allowed"])\n        self.assertFalse(east_asia["limits"]["arbitrary_headers_allowed"])\n        self.assertFalse(east_asia["limits"]["write_operations_allowed"])\n\n        self.assertEqual(\n            providers["tushare"]',
    )
    replace_once(api_test, '            "miaoxiang-mcp/provider-catalog.json",\n            "knowledge-tools/provider-catalog.json",', '            "miaoxiang-mcp/provider-catalog.json",\n            "east-asia-econ/provider-catalog.json",\n            "knowledge-tools/provider-catalog.json",')

    capability = ROOT / "api-center/tests/test_capability_maximization.py"
    replace_once(capability, '            234,\n', '            240,\n')
    replace_once(capability, '            "eodhd": 25,\n            "wolfram-alpha": 4,', '            "eodhd": 25,\n            "east-asia-econ": 6,\n            "wolfram-alpha": 4,')
    replace_once(
        capability,
        '        self.assertFalse(eodhd_provider["limits"]["trading_or_order_execution_allowed"])\n\n        baostock = json.loads(',
        '        self.assertFalse(eodhd_provider["limits"]["trading_or_order_execution_allowed"])\n\n        east_asia = json.loads(\n            (ROOT / "east-asia-econ/provider-catalog.json").read_text(encoding="utf-8")\n        )\n        east_asia_provider = east_asia["providers"][0]\n        self.assertEqual(east_asia_provider["required_secret_environment_variable"], "EAST_ASIA_ECON_API_KEY")\n        self.assertEqual(east_asia_provider["limits"]["fixed_api_host"], "data-api.eastasiaecon.com")\n        self.assertEqual(east_asia_provider["limits"]["requests_per_ticket_max"], 1)\n        self.assertFalse(east_asia_provider["limits"]["arbitrary_urls_allowed"])\n        self.assertFalse(east_asia_provider["limits"]["arbitrary_headers_allowed"])\n        self.assertFalse(east_asia_provider["limits"]["write_operations_allowed"])\n\n        baostock = json.loads(',
    )

    subprocess.run(["python", "api-center/build_catalog_market_search.py"], cwd=ROOT, check=True)
    subprocess.run(["python", "-m", "unittest", "discover", "-s", "api-center/east-asia-econ/tests", "-p", "test_*.py", "-v"], cwd=ROOT, check=True)
    subprocess.run(["python", "-m", "unittest", "discover", "-s", "api-center/tests", "-p", "test_*.py", "-v"], cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
