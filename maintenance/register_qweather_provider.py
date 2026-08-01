#!/usr/bin/env python3
"""Register QWeather in deterministic catalogs and repository validation."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "api-center"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"expected marker missing in {path}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


builder = API / "build_catalog_market_search.py"
replace_once(builder, 'DATA_COMMONS_CATALOG = HERE / "data-commons/provider-catalog.json"\n', 'DATA_COMMONS_CATALOG = HERE / "data-commons/provider-catalog.json"\nQWEATHER_CATALOG = HERE / "qweather/provider-catalog.json"\n')
replace_once(builder, '    "data-commons": 5,\n', '    "data-commons": 5,\n    "qweather": 18,\n')
replace_once(builder, '    DATA_COMMONS_CATALOG,\n    KNOWLEDGE_TOOLS_CATALOG,\n', '    DATA_COMMONS_CATALOG,\n    QWEATHER_CATALOG,\n    KNOWLEDGE_TOOLS_CATALOG,\n')
replace_once(builder, '        "data-commons/provider-catalog.json",\n        "knowledge-tools/provider-catalog.json",\n', '        "data-commons/provider-catalog.json",\n        "qweather/provider-catalog.json",\n        "knowledge-tools/provider-catalog.json",\n')

catalog_test = API / "tests" / "test_api_catalog.py"
replace_once(catalog_test, '    "data-commons": 5,\n', '    "data-commons": 5,\n    "qweather": 18,\n')
replace_once(catalog_test, 'self.assertEqual(catalog["managed_provider_count"], 20)', 'self.assertEqual(catalog["managed_provider_count"], 21)')
replace_once(catalog_test, 'self.assertEqual(catalog["enabled_managed_provider_count"], 20)', 'self.assertEqual(catalog["enabled_managed_provider_count"], 21)')
replace_once(catalog_test, 'self.assertEqual(catalog["managed_operation_count"], 195)', 'self.assertEqual(catalog["managed_operation_count"], 213)')
replace_once(catalog_test, '            "data-commons": "GOOGLE_DATA_COMMONS_API_KEY",\n', '            "data-commons": "GOOGLE_DATA_COMMONS_API_KEY",\n            "qweather": "QWEATHER_API_KEY",\n')
replace_once(
    catalog_test,
    '        self.assertEqual(providers["baostock"]["ticket_prefix"], "[api-baostock]")\n',
    '        self.assertEqual(providers["qweather"]["ticket_prefix"], "[api-qweather]")\n'
    '        self.assertEqual(providers["qweather"]["required_secret_environment_variable_name"], "QWEATHER_API_KEY")\n'
    '        self.assertEqual(providers["qweather"]["limits"]["fixed_api_host"], "ka6r72kcc3.re.qweatherapi.com")\n'
    '        self.assertFalse(providers["qweather"]["limits"]["arbitrary_hosts_allowed"])\n'
    '        self.assertFalse(providers["qweather"]["limits"]["redirects_allowed"])\n\n'
    '        self.assertEqual(providers["baostock"]["ticket_prefix"], "[api-baostock]")\n'
)
replace_once(catalog_test, '            "data-commons/provider-catalog.json",\n            "knowledge-tools/provider-catalog.json",\n', '            "data-commons/provider-catalog.json",\n            "qweather/provider-catalog.json",\n            "knowledge-tools/provider-catalog.json",\n')

capability = API / "tests" / "test_capability_maximization.py"
replace_once(capability, '            195,\n', '            213,\n')
replace_once(capability, '            "data-commons": 5,\n', '            "data-commons": 5,\n            "qweather": 18,\n')
replace_once(
    capability,
    '        eodhd = json.loads(\n',
    '        qweather = json.loads(\n'
    '            (ROOT / "qweather/provider-catalog.json").read_text(encoding="utf-8")\n'
    '        )\n'
    '        qw_provider = qweather["providers"][0]\n'
    '        self.assertEqual(qw_provider["required_secret_environment_variable"], "QWEATHER_API_KEY")\n'
    '        self.assertEqual(qw_provider["limits"]["fixed_api_host"], "ka6r72kcc3.re.qweatherapi.com")\n'
    '        self.assertFalse(qw_provider["limits"]["arbitrary_urls_allowed"])\n'
    '        self.assertFalse(qw_provider["limits"]["arbitrary_hosts_allowed"])\n'
    '        self.assertFalse(qw_provider["limits"]["redirects_allowed"])\n'
    '        self.assertFalse(qw_provider["limits"]["write_operations_allowed"])\n\n'
    '        eodhd = json.loads(\n'
)

workflow = ROOT / ".github" / "workflows" / "api-catalog-validate.yml"
replace_once(workflow, '            api-center/data-commons/requirements.txt\n', '            api-center/data-commons/requirements.txt\n            api-center/qweather/requirements.txt\n')
replace_once(workflow, '            -r api-center/data-commons/requirements.txt\n', '            -r api-center/data-commons/requirements.txt \\\n            -r api-center/qweather/requirements.txt\n')
replace_once(workflow, '            api-center/data-commons/tests/*.py \\\n            api-center/tests/*.py\n', '            api-center/data-commons/tests/*.py \\\n            api-center/qweather/qweather_task.py \\\n            api-center/qweather/tests/*.py \\\n            api-center/tests/*.py\n')
replace_once(workflow, "          python -m unittest discover -s api-center/data-commons/tests -p 'test_*.py' -v\n", "          python -m unittest discover -s api-center/data-commons/tests -p 'test_*.py' -v\n          python -m unittest discover -s api-center/qweather/tests -p 'test_*.py' -v\n")
replace_once(workflow, "              'data-commons': 5,\n", "              'data-commons': 5,\n              'qweather': 18,\n")
replace_once(workflow, "          assert catalog['managed_provider_count'] == 20\n", "          assert catalog['managed_provider_count'] == 21\n")
replace_once(workflow, "          assert catalog['enabled_managed_provider_count'] == 20\n", "          assert catalog['enabled_managed_provider_count'] == 21\n")
replace_once(workflow, "          assert catalog['managed_operation_count'] == 195\n", "          assert catalog['managed_operation_count'] == 213\n")
replace_once(workflow, "          assert sum(len(row['operations']) for row in providers.values()) == 195\n", "          assert sum(len(row['operations']) for row in providers.values()) == 213\n")
replace_once(
    workflow,
    "          baostock = providers['baostock']\n",
    "          qweather = providers['qweather']\n"
    "          assert qweather['ticket_prefix'] == '[api-qweather]'\n"
    "          assert qweather['required_secret_environment_variable_name'] == 'QWEATHER_API_KEY'\n"
    "          assert qweather['limits']['fixed_api_host'] == 'ka6r72kcc3.re.qweatherapi.com'\n"
    "          assert qweather['limits']['arbitrary_urls_allowed'] is False\n"
    "          assert qweather['limits']['arbitrary_hosts_allowed'] is False\n"
    "          assert qweather['limits']['arbitrary_paths_allowed'] is False\n"
    "          assert qweather['limits']['arbitrary_headers_allowed'] is False\n"
    "          assert qweather['limits']['client_supplied_api_key_allowed'] is False\n"
    "          assert qweather['limits']['redirects_allowed'] is False\n"
    "          assert qweather['limits']['write_operations_allowed'] is False\n\n"
    "          baostock = providers['baostock']\n"
)
replace_once(workflow, "              'data-commons/provider-catalog.json',\n", "              'data-commons/provider-catalog.json',\n              'qweather/provider-catalog.json',\n")
replace_once(workflow, "              'managed_providers': 20,\n", "              'managed_providers': 21,\n")
replace_once(workflow, "              'managed_operations': 195,\n", "              'managed_operations': 213,\n")
replace_once(workflow, '            api-center/data-commons/china-starter-pack.json\n', '            api-center/data-commons/china-starter-pack.json\n            api-center/qweather/provider-catalog.json\n            api-center/qweather/ticket.schema.json\n')

readme = API / "README.md"
section = '''\n## 和风天气 QWeather\n\n- Provider: `qweather`\n- Ticket prefix: `[api-qweather]`\n- Secret: `QWEATHER_API_KEY`\n- Fixed Host: `ka6r72kcc3.re.qweatherapi.com`\n- Authentication: backend-only `X-QW-Api-Key`\n- Fixed read-only operations: 18\n'''
text = readme.read_text(encoding="utf-8")
if "## 和风天气 QWeather" not in text:
    readme.write_text(text.rstrip() + "\n" + section, encoding="utf-8")

dependabot = ROOT / ".github" / "dependabot.yml"
dep = dependabot.read_text(encoding="utf-8")
block = '''\n  - package-ecosystem: "pip"\n    directory: "/api-center/qweather"\n    schedule:\n      interval: "weekly"\n    open-pull-requests-limit: 5\n'''
if 'directory: "/api-center/qweather"' not in dep:
    dependabot.write_text(dep.rstrip() + "\n" + block, encoding="utf-8")

Path(__file__).unlink()
