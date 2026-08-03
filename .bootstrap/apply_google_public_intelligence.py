#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace(path: str, old: str, new: str, *, expected: int = 1) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{path}: expected {expected} occurrences, found {count}: {old!r}")
    target.write_text(text.replace(old, new), encoding="utf-8")


# Migrate Google Books to the unified public-intelligence key.
replace(
    "api-center/global-knowledge-archives/source-access-matrix.json",
    '"credential_env": "GOOGLE_API_KEY"',
    '"credential_env": "GOOGLE_PUBLIC_INTELLIGENCE_API_KEY"',
)
replace(
    "api-center/global-knowledge-archives/provider-catalog.json",
    '"GOOGLE_API_KEY",\n        "BHL_API_KEY"',
    '"GOOGLE_PUBLIC_INTELLIGENCE_API_KEY",\n        "BHL_API_KEY"',
)
replace(
    ".github/workflows/global-knowledge-archives-ticket.yml",
    "GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}",
    "GOOGLE_PUBLIC_INTELLIGENCE_API_KEY: ${{ secrets.GOOGLE_PUBLIC_INTELLIGENCE_API_KEY }}",
)
replace(
    ".github/workflows/global-knowledge-archives-validate.yml",
    "GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}",
    "GOOGLE_PUBLIC_INTELLIGENCE_API_KEY: ${{ secrets.GOOGLE_PUBLIC_INTELLIGENCE_API_KEY }}",
)
replace(
    ".github/workflows/global-knowledge-archives-validate.yml",
    "assert provider['optional_secret_environment_variables']==['GOOGLE_API_KEY','BHL_API_KEY']",
    "assert provider['optional_secret_environment_variables']==['GOOGLE_PUBLIC_INTELLIGENCE_API_KEY','BHL_API_KEY']",
)

# Register the new managed provider in the authoritative catalog builder.
replace(
    "api-center/build_catalog_market_search.py",
    'OPEN_SOFTWARE_SECURITY_KNOWLEDGE_CATALOG = HERE / "open-software-security-knowledge/provider-catalog.json"\nOPEN_SOFTWARE_SECURITY_KNOWLEDGE_CATALOG = HERE / "open-software-security-knowledge/provider-catalog.json"\n',
    'OPEN_SOFTWARE_SECURITY_KNOWLEDGE_CATALOG = HERE / "open-software-security-knowledge/provider-catalog.json"\nGOOGLE_PUBLIC_INTELLIGENCE_CATALOG = HERE / "google-public-intelligence/provider-catalog.json"\n',
)
replace(
    "api-center/build_catalog_market_search.py",
    '    "open-software-security-knowledge": 11,\n}',
    '    "open-software-security-knowledge": 11,\n    "google-public-intelligence": 9,\n}',
)
replace(
    "api-center/build_catalog_market_search.py",
    "    OPEN_SOFTWARE_SECURITY_KNOWLEDGE_CATALOG,\n)",
    "    OPEN_SOFTWARE_SECURITY_KNOWLEDGE_CATALOG,\n    GOOGLE_PUBLIC_INTELLIGENCE_CATALOG,\n)",
)
replace(
    "api-center/build_catalog_market_search.py",
    '        "open-software-security-knowledge/provider-catalog.json",\n    ):',
    '        "open-software-security-knowledge/provider-catalog.json",\n        "google-public-intelligence/provider-catalog.json",\n    ):',
)

# Extend the aggregate catalog regression expectations.
replace(
    "api-center/tests/test_api_catalog.py",
    '    "open-software-security-knowledge": 11,\n}',
    '    "open-software-security-knowledge": 11,\n    "google-public-intelligence": 9,\n}',
)
replace(
    "api-center/tests/test_api_catalog.py",
    '            "fred": "FRED_API_KEY",\n',
    '            "fred": "FRED_API_KEY",\n            "google-public-intelligence": "GOOGLE_PUBLIC_INTELLIGENCE_API_KEY",\n',
)

subprocess.run(
    [
        "python",
        str(ROOT / "api-center/build_catalog_market_search.py"),
        "--json-output",
        str(ROOT / "api-center/api-catalog.json"),
        "--markdown-output",
        str(ROOT / "api-center/api-catalog.md"),
    ],
    cwd=ROOT,
    check=True,
)
