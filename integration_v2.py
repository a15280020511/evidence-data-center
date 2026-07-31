#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    Path(path).write_text(text, encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


# Register the managed provider catalog and expose optional-secret metadata.
path = "api-center/build_catalog.py"
text = read(path)
if 'HERE / "web-retrieval/provider-catalog.json",' not in text:
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if 'HERE / "company-intelligence/provider-catalog.json",' in line:
            lines.insert(index + 1, '    HERE / "web-retrieval/provider-catalog.json",\n')
            break
    else:
        raise SystemExit("build_catalog.py managed-provider insertion point not found")
    text = "".join(lines)

if '"optional_secret_environment_variable_name"' not in text:
    marker = '                "secret_value_exposed": False,\n'
    insert = (
        '                "optional_secret_environment_variable_name": str(\n'
        '                    raw_provider.get("optional_secret_environment_variable") or ""\n'
        '                ),\n'
    )
    position = text.find(marker, text.find('"required_secret_environment_variable_name"'))
    require(position >= 0, "build_catalog.py optional-secret insertion point not found")
    text = text[:position] + insert + text[position:]
write(path, text)


# Update deterministic global catalog tests.
path = "api-center/tests/test_api_catalog.py"
text = read(path)
text, n1 = re.subn(
    r'self\.assertEqual\(catalog\["managed_provider_count"\],\s*9\)',
    'self.assertEqual(catalog["managed_provider_count"], 11)',
    text,
    count=1,
)
text, n2 = re.subn(
    r'self\.assertEqual\(catalog\["enabled_managed_provider_count"\],\s*9\)',
    'self.assertEqual(catalog["enabled_managed_provider_count"], 11)',
    text,
    count=1,
)
require(n1 == 1 and n2 == 1, "test_api_catalog.py provider count anchors not found")

if '"jina-reader"' not in text:
    old = (
        '{"bigquery", "earth-engine", "data-commons", "akshare", "ashare", '
        '"aifin-market", "yuandian-law", "qichacha", "tianyancha"}'
    )
    new = (
        '{"bigquery", "earth-engine", "data-commons", "akshare", "ashare", '
        '"aifin-market", "yuandian-law", "qichacha", "tianyancha", '
        '"jina-reader", "exa"}'
    )
    require(old in text, "test_api_catalog.py provider set anchor not found")
    text = text.replace(old, new, 1)

operation_marker = '        self.assertEqual(len(providers["tianyancha"]["operations"]), 3)\n'
if 'len(providers["jina-reader"]["operations"])' not in text:
    require(operation_marker in text, "test_api_catalog.py operation insertion point not found")
    text = text.replace(
        operation_marker,
        operation_marker
        + '        self.assertEqual(len(providers["jina-reader"]["operations"]), 2)\n'
        + '        self.assertEqual(len(providers["exa"]["operations"]), 3)\n',
        1,
    )

if 'providers["exa"]["required_secret_environment_variable_name"]' not in text:
    secret_marker = (
        '        self.assertEqual(\n'
        '            providers["tianyancha"]["required_secret_environment_variable_name"],\n'
        '            "TIANYANCHA_API_TOKEN",\n'
        '        )\n'
    )
    require(secret_marker in text, "test_api_catalog.py secret insertion point not found")
    text = text.replace(
        secret_marker,
        secret_marker
        + '        self.assertEqual(\n'
        + '            providers["jina-reader"]["required_secret_environment_variable_name"],\n'
        + '            "",\n'
        + '        )\n'
        + '        self.assertEqual(\n'
        + '            providers["jina-reader"]["optional_secret_environment_variable_name"],\n'
        + '            "JINA_API_KEY",\n'
        + '        )\n'
        + '        self.assertEqual(\n'
        + '            providers["exa"]["required_secret_environment_variable_name"],\n'
        + '            "EXA_API_KEY",\n'
        + '        )\n',
        1,
    )
write(path, text)


# Update maximum-safe surface tests.
path = "api-center/tests/test_capability_maximization.py"
text = read(path)
text, changed = re.subn(
    r'self\.assertEqual\(sum\(len\(row\["operations"\]\) for row in providers\.values\(\)\),\s*99\)',
    'self.assertEqual(sum(len(row["operations"]) for row in providers.values()), 104)',
    text,
    count=1,
)
require(changed == 1, "test_capability_maximization.py operation total anchor not found")
if 'len(providers["jina-reader"]["operations"])' not in text:
    marker = '        self.assertEqual(len(providers["yuandian-law"]["operations"]), 40)\n'
    require(marker in text, "test_capability_maximization.py provider insertion point not found")
    text = text.replace(
        marker,
        marker
        + '        self.assertEqual(len(providers["jina-reader"]["operations"]), 2)\n'
        + '        self.assertEqual(len(providers["exa"]["operations"]), 3)\n',
        1,
    )
write(path, text)


# Update the GPTs catalog governance workflow.
path = ".github/workflows/api-catalog-validate.yml"
text = read(path)
if "web_providers = load_json('api-center/web-retrieval/provider-catalog.json')" not in text:
    marker = "          company_providers = load_json('api-center/company-intelligence/provider-catalog.json')\n"
    require(marker in text, "api-catalog workflow provider-load anchor not found")
    text = text.replace(
        marker,
        marker + "          web_providers = load_json('api-center/web-retrieval/provider-catalog.json')\n",
        1,
    )

replacements = {
    "          assert catalog['managed_provider_count'] == 9\n":
        "          assert catalog['managed_provider_count'] == 11\n",
    "          assert catalog['enabled_managed_provider_count'] == 9\n":
        "          assert catalog['enabled_managed_provider_count'] == 11\n",
    "          assert sum(len(row['operations']) for row in catalog['managed_providers']) == 99\n":
        "          assert sum(len(row['operations']) for row in catalog['managed_providers']) == 104\n",
    "          assert catalog['exposed_parameter_count'] == 655\n":
        "          assert catalog['exposed_parameter_count'] == 668\n",
    "              'aifin-market', 'yuandian-law', 'qichacha', 'tianyancha'\n":
        "              'aifin-market', 'yuandian-law', 'qichacha', 'tianyancha',\n"
        "              'jina-reader', 'exa'\n",
    "              'managed_providers': 9,\n":
        "              'managed_providers': 11,\n",
    "              'managed_operations': 99,\n":
        "              'managed_operations': 104,\n",
}
for old, new in replacements.items():
    require(old in text or new in text, f"api-catalog workflow anchor missing: {old.strip()}")
    if old in text:
        text = text.replace(old, new, 1)

if "web_providers['secret_values_exposed']" not in text:
    marker = (
        "          assert {row['provider_id'] for row in company_providers['providers']} == {\n"
        "              'qichacha', 'tianyancha'\n"
        "          }\n"
    )
    require(marker in text, "api-catalog workflow web-provider assertion anchor not found")
    text = text.replace(
        marker,
        marker
        + "          assert web_providers['secret_values_exposed'] is False\n"
        + "          assert {row['provider_id'] for row in web_providers['providers']} == {\n"
        + "              'jina-reader', 'exa'\n"
        + "          }\n",
        1,
    )

if "            api-center/web-retrieval/ticket.schema.json\n" not in text:
    marker = "            api-center/company-intelligence/ticket.schema.json\n"
    require(marker in text, "api-catalog workflow artifact anchor not found")
    text = text.replace(
        marker,
        marker
        + "            api-center/web-retrieval/provider-catalog.json\n"
        + "            api-center/web-retrieval/ticket.schema.json\n",
        1,
    )
write(path, text)
