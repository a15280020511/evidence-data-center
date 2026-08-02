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
        raise RuntimeError(f"expected text not found in {path}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def regex_once(path: Path, pattern: str, replacement: str) -> None:
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError(f"expected one regex match in {path}, got {count}: {pattern}")
    path.write_text(updated, encoding="utf-8")


# Remove the complete standalone provider implementation.
for relative in (
    "faostat/README.md",
    "faostat/faostat_task.py",
    "faostat/provider-catalog.json",
    "faostat/requirements.txt",
    "faostat/ticket.schema.json",
):
    path = API / relative
    if not path.exists():
        raise RuntimeError(f"expected provider file missing before removal: {path}")
    path.unlink()
(API / "faostat").rmdir()

# Remove the provider from the unified managed-provider catalog.
builder = API / "build_catalog_market_search.py"
for old in (
    'FAOSTAT_CATALOG = HERE / "faostat/provider-catalog.json"\n',
    '    "faostat": 7,\n',
    '    FAOSTAT_CATALOG,\n',
    '        "faostat/provider-catalog.json",\n',
):
    replace_once(builder, old, "")

# Remove the legacy shared runtime branch while retaining WTO and IMF.
shared = API / "international-statistics" / "provider_task.py"
replace_once(
    shared,
    '"""Bounded read-only runtime for WTO, IMF DataMapper and FAOSTAT."""',
    '"""Bounded read-only runtime for WTO and IMF statistics providers."""',
)
replace_once(shared, 'DATASET_RE = re.compile(r"^[A-Z0-9_]{1,16}$")\n', "")
regex_once(
    shared,
    r'\n    "faostat": \{\n.*?\n    \},\n(?=\})',
    "",
)
regex_once(
    shared,
    r'\n    if provider == "faostat":\n.*?(?=\n    raise ValueError\(f"unsupported provider: \{provider\}"\))',
    "",
)
replace_once(
    shared,
    '    username = str(os.getenv(cfg.get("username", "")) or "").strip() if cfg.get("username") else ""\n    token = ""\n',
    "",
)
regex_once(
    shared,
    r'\n            elif provider == "faostat":\n.*?(?=\n            response = requests\.get)',
    "",
)
replace_once(
    shared,
    '                "credential_used": provider in {"wto", "imf", "faostat"},',
    '                "credential_used": provider in {"wto", "imf"},',
)

# Keep the shared provider regression focused on the two remaining providers.
shared_test = API / "international-statistics" / "tests" / "test_international_statistics.py"
shared_test.write_text(
    '''from __future__ import annotations
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHARED = ROOT / "international-statistics" / "provider_task.py"
SPEC = importlib.util.spec_from_file_location("provider_task", SHARED)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class InternationalStatisticsTests(unittest.TestCase):
    def test_catalog_contracts(self):
        expected = {"wto": 7, "imf": 6}
        self.assertEqual(set(mod.PROVIDERS), set(expected))
        for provider, count in expected.items():
            row = json.loads((ROOT / provider / "provider-catalog.json").read_text())["providers"][0]
            self.assertEqual(row["provider_id"], provider)
            self.assertEqual(len(row["operations"]), count)
            self.assertFalse(row["limits"]["write_operations_allowed"])
            self.assertFalse(row["limits"]["automatic_retry_allowed"])
            self.assertFalse(row["limits"]["automatic_pagination_allowed"])

    def test_fixed_request_builders(self):
        self.assertEqual(mod.build_request("wto", "indicators", {})[0], "/indicator")
        self.assertEqual(
            mod.build_request(
                "imf", "get-dataflow", {"agency": "IMF.RES", "flow": "WEO"}
            )[0],
            "/structure/dataflow/IMF.RES/WEO/+",
        )
        path, query = mod.build_request(
            "imf",
            "get-data",
            {
                "agency": "IMF.RES",
                "flow": "WEO",
                "version": "+",
                "key": "CHN.NGDP_RPCH.A",
                "start_period": "2024",
                "end_period": "2026",
            },
        )
        self.assertEqual(path, "/data/dataflow/IMF.RES/WEO/+/CHN.NGDP_RPCH.A")
        self.assertEqual(query, [("startPeriod", "2024"), ("endPeriod", "2026")])

    def test_unbounded_inputs_rejected(self):
        with self.assertRaises(ValueError):
            mod.build_request("wto", "data", {"indicator_codes": ["bad/value"]})
        with self.assertRaises(ValueError):
            mod.build_request(
                "imf",
                "get-data",
                {"agency": "IMF.RES", "flow": "WEO", "key": "https://example.com"},
            )


if __name__ == "__main__":
    unittest.main()
''',
    encoding="utf-8",
)

# Update unified catalog invariants.
catalog_test = API / "tests" / "test_api_catalog.py"
for old, new in (
    ('    "faostat": 7,\n', ""),
    ('        self.assertEqual(catalog["managed_provider_count"], 46)\n', '        self.assertEqual(catalog["managed_provider_count"], 45)\n'),
    ('        self.assertEqual(catalog["enabled_managed_provider_count"], 46)\n', '        self.assertEqual(catalog["enabled_managed_provider_count"], 45)\n'),
    ('        self.assertEqual(catalog["managed_operation_count"], 479)\n', '        self.assertEqual(catalog["managed_operation_count"], 472)\n'),
    ('            "faostat": "FAOSTAT_PASSWORD",\n', ""),
):
    replace_once(catalog_test, old, new)

capability_test = API / "tests" / "test_capability_maximization.py"
replace_once(capability_test, '            479,\n', '            472,\n')
replace_once(capability_test, '            "faostat": 7,\n', "")

# Rebuild deterministic catalog artifacts after the provider has been removed.
subprocess.run(["python", str(API / "build_catalog_market_search.py")], check=True)

# No executable, catalog, test or generated contract under api-center may retain the removed provider.
remaining: list[str] = []
for path in API.rglob("*"):
    if not path.is_file() or path.suffix == ".pyc":
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    if "faostat" in text.lower():
        remaining.append(str(path.relative_to(ROOT)))
if remaining:
    raise RuntimeError(f"removed-provider references remain: {remaining}")

print("Provider removed; unified catalog regenerated to 45 providers / 472 operations")
