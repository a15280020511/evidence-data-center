#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "api-center"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"expected text not found in {path}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def regex_once(path: Path, pattern: str, replacement: str) -> None:
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError(f"expected one match in {path}, got {count}: {pattern}")
    path.write_text(updated, encoding="utf-8")


test_path = API / "tests" / "test_api_catalog.py"
replace_once(test_path, '    "oecd": 6,\n', '    "oecd": 6,\n    "adb": 8,\n')
replace_once(test_path, 'self.assertEqual(catalog["managed_provider_count"], 45)', 'self.assertEqual(catalog["managed_provider_count"], 46)')
replace_once(test_path, 'self.assertEqual(catalog["enabled_managed_provider_count"], 45)', 'self.assertEqual(catalog["enabled_managed_provider_count"], 46)')
replace_once(test_path, 'self.assertEqual(catalog["managed_operation_count"], 471)', 'self.assertEqual(catalog["managed_operation_count"], 479)')
replace_once(
    test_path,
    '        self.assertFalse(oecd["limits"]["arbitrary_sdmx_resource_types_allowed"])\n\n        alphafeed = providers["alphafeed"]',
    '        self.assertFalse(oecd["limits"]["arbitrary_sdmx_resource_types_allowed"])\n\n'
    '        adb = providers["adb"]\n'
    '        self.assertEqual(adb["ticket_prefix"], "[intel-adb]")\n'
    '        self.assertEqual(adb["required_secret_environment_variable_name"], "")\n'
    '        self.assertEqual(len(adb["operations"]), 8)\n'
    '        self.assertEqual(adb["limits"]["fixed_api_host"], "kidb.adb.org")\n'
    '        self.assertEqual(adb["limits"]["official_rate_limit_queries_per_minute"], 20)\n'
    '        self.assertEqual(adb["limits"]["requests_per_ticket_max"], 1)\n'
    '        self.assertFalse(adb["limits"]["empty_dimension_bulk_queries_allowed"])\n'
    '        self.assertFalse(adb["limits"]["automatic_retry_allowed"])\n'
    '        self.assertFalse(adb["limits"]["automatic_pagination_allowed"])\n'
    '        self.assertFalse(adb["limits"]["write_operations_allowed"])\n\n'
    '        alphafeed = providers["alphafeed"]',
)

workflow = ROOT / ".github" / "workflows" / "api-catalog-validate.yml"
replace_once(
    workflow,
    '            -r api-center/faostat/requirements.txt\n',
    '            -r api-center/faostat/requirements.txt \\\n            -r api-center/adb/requirements.txt\n',
)
replace_once(workflow, "assert catalog['managed_provider_count'] == len(providers) == 45", "assert catalog['managed_provider_count'] == len(providers) == 46")
replace_once(workflow, "assert catalog['enabled_managed_provider_count'] == 45", "assert catalog['enabled_managed_provider_count'] == 46")
replace_once(workflow, "assert catalog['managed_operation_count'] == 471", "assert catalog['managed_operation_count'] == 479")
replace_once(
    workflow,
    "          assert oecd['limits']['write_operations_allowed'] is False\n\n          print(json.dumps({",
    "          assert oecd['limits']['write_operations_allowed'] is False\n\n"
    "          adb = providers['adb']\n"
    "          assert adb['ticket_prefix'] == '[intel-adb]'\n"
    "          assert adb['required_secret_environment_variable_name'] == ''\n"
    "          assert len(adb['operations']) == 8\n"
    "          assert adb['limits']['fixed_api_host'] == 'kidb.adb.org'\n"
    "          assert adb['limits']['fixed_api_prefix'] == '/api/v4/sdmx'\n"
    "          assert adb['limits']['official_rate_limit_queries_per_minute'] == 20\n"
    "          assert adb['limits']['requests_per_ticket_max'] == 1\n"
    "          assert adb['limits']['empty_dimension_bulk_queries_allowed'] is False\n"
    "          assert adb['limits']['automatic_retry_allowed'] is False\n"
    "          assert adb['limits']['automatic_pagination_allowed'] is False\n"
    "          assert adb['limits']['write_operations_allowed'] is False\n\n"
    "          print(json.dumps({",
)
replace_once(
    workflow,
    "              'oecd_operations': 6,\n",
    "              'oecd_operations': 6,\n              'adb_operations': 8,\n",
)

subprocess.run(["python", str(API / "build_catalog_market_search.py")], check=True)
print("ADB catalog integration generated successfully")
