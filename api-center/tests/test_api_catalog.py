from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_catalog",
    ROOT / "build_catalog_market_search.py",
)
assert SPEC and SPEC.loader
build_catalog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_catalog)

EXPECTED_OPERATION_COUNTS = {
    "bigquery": 7,
    "earth-engine": 6,
    "data-commons": 5,
    "qweather": 18,
    "xweather": 10,
    "akshare": 17,
    "ashare": 1,
    "aifin-market": 17,
    "yuandian-law": 40,
    "tianyancha": 3,
    "miaoxiang": 4,
    "miaoxiang-mcp": 13,
    "jina-reader": 2,
    "exa": 3,
    "tavily": 5,
    "firecrawl": 4,
    "browserless": 8,
    "tickflow": 5,
    "serpapi": 4,
    "tushare": 20,
    "baostock": 20,
    "eodhd": 25,
    "east-asia-econ": 6,
    "alpha-vantage": 66,
    "overture-maps": 7,
    "oecd": 6,
    "adb": 8,
    "alphafeed": 10,
    "who-gho-odata": 8,
    "mediastack": 5,
    "statistics-of-the-world": 11,
    "aisstream": 4,
    "internet-archive": 6,
    "marketstack": 11,
    "nasa": 25,
    "metno-geosatellite": 4,
    "copernicus-cdse": 7,
    "eia": 6,
    "un-comtrade": 10,
    "opensky-network": 9,
    "hexdb-aviation": 6,
    "wto": 7,
    "imf": 6,
    "worldbank-documents": 7,
    "bis": 8,
    "wolfram-alpha": 4,
    "llamaparse": 3,
    "public-data-geospatial": 34,
    "cloudflare": 22,
    "fred": 25,
    "huggingface-hub": 11,
    "evidence-standardization": 8,
    "global-research-intelligence": 23,
    "openbb-free": 7,
    "open-data-aggregators": 13,
    "nih-public-health": 6,
    "openstreetmap": 6,
    "gnews": 3,
    "global-literature-libraries": 10,
    "global-knowledge-archives": 9,
    "global-knowledge-fabric": 9,
    "baidu-ai-cloud": 8,
    "open-software-security-knowledge": 11,
    "google-public-intelligence": 9,
    "reality-observation": 27,
    "copernicus-marine": 3,
    "noaa-cdo": 5,
}


class ApiCatalogTests(unittest.TestCase):
    def build(self) -> dict:
        return build_catalog.build(
            ROOT / "connector-manifest.json",
            ROOT / "catalog-metadata.json",
            ROOT / "connectors",
        )

    def test_catalog_covers_every_connector_and_exposes_no_secret_values(self) -> None:
        catalog = self.build()
        manifest = json.loads(
            (ROOT / "connector-manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(catalog["connector_count"], manifest["connector_count"])
        self.assertEqual(
            catalog["enabled_connector_count"],
            manifest["enabled_connector_count"],
        )
        self.assertEqual(catalog["connector_count"], 72)
        self.assertEqual(catalog["managed_provider_count"], len(EXPECTED_OPERATION_COUNTS))
        self.assertEqual(catalog["enabled_managed_provider_count"], len(EXPECTED_OPERATION_COUNTS))
        self.assertEqual(catalog["managed_operation_count"], sum(EXPECTED_OPERATION_COUNTS.values()))
        self.assertGreaterEqual(catalog["exposed_parameter_count"], 500)
        self.assertFalse(catalog["direct_center_to_center_calls_allowed"])
        self.assertFalse(catalog["secret_values_exposed"])
        self.assertEqual(catalog["selection_owner"], "gpts-usage-center")
        self.assertEqual(catalog["maintenance_owner"], "web-gpt-github-plugin")
        self.assertEqual(catalog["schema_version"], "api-catalog-v3")
        self.assertEqual(catalog["center_display_name_zh"], "情报中心")
        self.assertEqual(catalog["center_display_name_en"], "Intelligence Center")

        providers = {
            row["provider_id"]: row for row in catalog["managed_providers"]
        }
        self.assertEqual(set(providers), set(EXPECTED_OPERATION_COUNTS))
        self.assertNotIn("tianditu", providers)
        self.assertNotIn("qichacha", providers)
        for provider_id, expected in EXPECTED_OPERATION_COUNTS.items():
            self.assertEqual(len(providers[provider_id]["operations"]), expected)
            self.assertFalse(providers[provider_id]["secret_value_exposed"])

        expected_secret_names = {
            "bigquery": "GOOGLE_CLOUD_SERVICE_ACCOUNT_JSON",
            "earth-engine": "GOOGLE_CLOUD_SERVICE_ACCOUNT_JSON",
            "data-commons": "GOOGLE_DATA_COMMONS_API_KEY",
            "qweather": "QWEATHER_API_KEY",
            "xweather": "XWEATHER_CLIENT_SECRET",
            "aifin-market": "WIND_API_KEY",
            "yuandian-law": "YUANDIAN_API_KEY",
            "tianyancha": "TIANYANCHA_API_TOKEN",
            "miaoxiang": "MX_APIKEY",
            "miaoxiang-mcp": "EM_API_KEY",
            "exa": "EXA_API_KEY",
            "tavily": "TAVILY_API_KEY",
            "firecrawl": "FIRECRAWL_API_KEY",
            "browserless": "BROWSERLESS_TOKEN",
            "tickflow": "TICKFLOW_API_KEY",
            "serpapi": "SERPAPI_API_KEY",
            "tushare": "TUSHARE_API_TOKEN",
            "eodhd": "EODHD_API_TOKEN",
            "east-asia-econ": "EAST_ASIA_ECON_API_KEY",
            "alpha-vantage": "ALPHA_VANTAGE_API_KEY",
            "alphafeed": "ALPHAFEED_API_KEY",
            "mediastack": "MEDIASTACK_API_KEY",
            "marketstack": "MARKETSTACK_API_KEY",
            "copernicus-cdse": "COPERNICUS_CLIENT_ID",
            "eia": "EIA_API_KEY",
            "un-comtrade": "UN_COMTRADE_API_KEY",
            "opensky-network": "OPENSKY_CLIENT_ID",
            "hexdb-aviation": "HEXDB_API_KEY",
            "wolfram-alpha": "WOLFRAM_APP_ID",
            "llamaparse": "LLAMA_CLOUD_API_KEY",
            "cloudflare": "CLOUDFLARE_API_TOKEN",
            "fred": "FRED_API_KEY",
            "huggingface-hub": "HF_TOKEN",
            "gnews": "GNEWS_API_KEY",
            "baidu-ai-cloud": "BAIDU_API_KEY",
            "google-public-intelligence": "GOOGLE_API_KEY",
            "noaa-cdo": "NOAA_CDO_TOKEN",
        }
        for provider_id, expected in expected_secret_names.items():
            self.assertEqual(
                providers[provider_id]["required_secret_environment_variable"],
                expected,
            )

    def test_catalog_output_is_deterministic(self) -> None:
        self.assertEqual(self.build(), self.build())

    def test_committed_catalog_matches_generator(self) -> None:
        committed = json.loads(
            (ROOT / "api-catalog.json").read_text(encoding="utf-8")
        )
        self.assertEqual(committed, self.build())

    def test_main_writes_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            catalog = self.build()
            (output / "api-catalog.json").write_text(
                json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (output / "api-catalog.md").write_text(
                build_catalog.render_markdown(catalog),
                encoding="utf-8",
            )
            self.assertTrue((output / "api-catalog.json").exists())
            self.assertTrue((output / "api-catalog.md").exists())


if __name__ == "__main__":
    unittest.main()
