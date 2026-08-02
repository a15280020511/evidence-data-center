from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CENTER = ROOT / "api-center"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"missing patch anchor in {path}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


build = CENTER / "build_catalog_market_search.py"
replace_once(
    build,
    'PUBLIC_DATA_GEOSPATIAL_CATALOG = HERE / "public-data-geospatial/provider-catalog.json"\n',
    'PUBLIC_DATA_GEOSPATIAL_CATALOG = HERE / "public-data-geospatial/provider-catalog.json"\nCLOUDFLARE_CATALOG = HERE / "cloudflare/provider-catalog.json"\n',
)
replace_once(
    build,
    '    "public-data-geospatial": 35,\n}',
    '    "public-data-geospatial": 35,\n    "cloudflare": 22,\n}',
)
replace_once(
    build,
    '    PUBLIC_DATA_GEOSPATIAL_CATALOG,\n)',
    '    PUBLIC_DATA_GEOSPATIAL_CATALOG,\n    CLOUDFLARE_CATALOG,\n)',
)
replace_once(
    build,
    '        "public-data-geospatial/provider-catalog.json",\n    ):',
    '        "public-data-geospatial/provider-catalog.json",\n        "cloudflare/provider-catalog.json",\n    ):',
)

catalog_test = CENTER / "tests/test_api_catalog.py"
replace_once(
    catalog_test,
    '    "public-data-geospatial": 35,\n}',
    '    "public-data-geospatial": 35,\n    "cloudflare": 22,\n}',
)
replace_once(catalog_test, 'self.assertEqual(catalog["managed_provider_count"], 48)', 'self.assertEqual(catalog["managed_provider_count"], 49)')
replace_once(catalog_test, 'self.assertEqual(catalog["enabled_managed_provider_count"], 48)', 'self.assertEqual(catalog["enabled_managed_provider_count"], 49)')
replace_once(catalog_test, 'self.assertEqual(catalog["managed_operation_count"], 522)', 'self.assertEqual(catalog["managed_operation_count"], 544)')
replace_once(
    catalog_test,
    '            "llamaparse": "LLAMA_CLOUD_API_KEY",\n',
    '            "llamaparse": "LLAMA_CLOUD_API_KEY",\n            "cloudflare": "CLOUDFLARE_API_TOKEN",\n',
)
replace_once(
    catalog_test,
    '        self.assertEqual(providers["browserless"]["ticket_prefix"], "[api-browserless]")\n',
    '        cloudflare = providers["cloudflare"]\n        self.assertEqual(cloudflare["ticket_prefix"], "[intel-cloudflare]")\n        self.assertEqual(cloudflare["required_secret_environment_variable_name"], "CLOUDFLARE_API_TOKEN")\n        self.assertEqual(len(cloudflare["operations"]), 22)\n        self.assertEqual(cloudflare["limits"]["fixed_api_hosts"], ["api.cloudflare.com"])\n        self.assertEqual(cloudflare["limits"]["requests_per_ticket_max"], 1)\n        self.assertFalse(cloudflare["limits"]["write_operations_allowed"])\n        self.assertFalse(cloudflare["limits"]["urlscanner_submission_allowed"])\n        self.assertFalse(cloudflare["limits"]["arbitrary_cloudflare_paths_allowed"])\n        self.assertFalse(cloudflare["limits"]["custom_cookies_allowed"])\n        self.assertFalse(cloudflare["limits"]["custom_browser_scripts_allowed"])\n        self.assertTrue(all(row["result_contract"]["read_only"] for row in cloudflare["operations"]))\n\n        self.assertEqual(providers["browserless"]["ticket_prefix"], "[api-browserless]")\n',
)
