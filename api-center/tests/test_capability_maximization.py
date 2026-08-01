from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CapabilityMaximizationTests(unittest.TestCase):
    def test_maximum_safe_readonly_surface_is_registered(self) -> None:
        manifest = json.loads(
            (ROOT / "connector-manifest.json").read_text(encoding="utf-8")
        )
        rows = manifest["connectors"]
        self.assertEqual(manifest["connector_count"], 68)
        self.assertEqual(manifest["enabled_connector_count"], 68)
        counts = {
            prefix: sum(row["id"].startswith(prefix) for row in rows)
            for prefix in (
                "amap-",
                "baidu-",
                "openmeteo-",
                "worldbank-",
                "wikidata-",
                "dbnomics-",
                "osm-",
                "newsapi-",
            )
        }
        self.assertEqual(
            counts,
            {
                "amap-": 19,
                "baidu-": 15,
                "openmeteo-": 11,
                "worldbank-": 9,
                "wikidata-": 4,
                "dbnomics-": 3,
                "osm-": 3,
                "newsapi-": 3,
            },
        )
        self.assertTrue(
            all(row["method"] == "GET" for row in rows if row["enabled"])
        )
        self.assertTrue(all(not row["write_approved"] for row in rows))

    def test_managed_providers_expose_fixed_readonly_operations_only(self) -> None:
        catalog = json.loads(
            (ROOT / "api-catalog.json").read_text(encoding="utf-8")
        )
        providers = {
            row["provider_id"]: row for row in catalog["managed_providers"]
        }
        self.assertEqual(
            sum(len(row["operations"]) for row in providers.values()),
            190,
        )
        self.assertNotIn("qichacha", providers)
        self.assertNotIn("tianditu", providers)
        expected_counts = {
            "miaoxiang": 4,
            "aifin-market": 17,
            "akshare": 17,
            "bigquery": 7,
            "earth-engine": 6,
            "yuandian-law": 40,
            "jina-reader": 2,
            "exa": 3,
            "tavily": 5,
            "firecrawl": 4,
            "tickflow": 5,
            "serpapi": 4,
            "tushare": 20,
            "baostock": 20,
            "eodhd": 25,
            "wolfram-alpha": 4,
            "llamaparse": 3,
        }
        for provider_id, count in expected_counts.items():
            self.assertEqual(len(providers[provider_id]["operations"]), count)
        self.assertEqual(
            providers["yuandian-law"]["discovered_readonly_tool_count"],
            37,
        )
        self.assertFalse(
            any(row["secret_value_exposed"] for row in providers.values())
        )

    def test_no_unbounded_escape_hatch_is_introduced(self) -> None:
        aifin = json.loads(
            (ROOT / "aifin-market/provider-catalog.json").read_text(
                encoding="utf-8"
            )
        )
        wind_limits = aifin["providers"][0]["limits"]
        self.assertEqual(wind_limits["upstream_tools_exposed"], 15)
        self.assertFalse(wind_limits["arbitrary_tool_names_allowed"])
        self.assertFalse(wind_limits["arbitrary_urls_allowed"])
        self.assertFalse(wind_limits["trading_or_order_execution_allowed"])

        akshare = json.loads(
            (ROOT / "akshare/provider-catalog.json").read_text(encoding="utf-8")
        )
        ak_limits = next(
            row for row in akshare["providers"] if row["provider_id"] == "akshare"
        )["limits"]
        self.assertFalse(ak_limits["arbitrary_functions_allowed"])
        self.assertFalse(ak_limits["arbitrary_urls_allowed"])
        self.assertFalse(ak_limits["brokerage_execution_allowed"])

        yuandian = json.loads(
            (ROOT / "yuandian/provider-catalog.json").read_text(encoding="utf-8")
        )
        legal_limits = yuandian["providers"][0]["limits"]
        self.assertFalse(legal_limits["arbitrary_urls_allowed"])
        self.assertFalse(legal_limits["arbitrary_headers_allowed"])
        self.assertFalse(legal_limits["write_operations_allowed"])
        self.assertFalse(legal_limits["secret_values_exposed"])
        self.assertTrue(legal_limits["direct_personal_identifiers_redacted"])

        miaoxiang = json.loads(
            (ROOT / "miaoxiang/provider-catalog.json").read_text(encoding="utf-8")
        )
        provider = miaoxiang["providers"][0]
        operation_ids = {row["operation_id"] for row in provider["operations"]}
        self.assertEqual(
            operation_ids,
            {
                "catalog-capabilities",
                "financial-search",
                "financial-data",
                "stock-screen",
            },
        )
        policy = provider["execution_policy"].lower()
        self.assertIn("禁止", policy)
        for operation_id in operation_ids:
            self.assertNotIn("trade", operation_id)
            self.assertNotIn("order", operation_id)
            self.assertNotIn("watchlist", operation_id)

        web = json.loads(
            (ROOT / "web-retrieval/provider-catalog.json").read_text(
                encoding="utf-8"
            )
        )
        providers = {row["provider_id"]: row for row in web["providers"]}
        tavily_limits = providers["tavily"]["limits"]
        firecrawl_limits = providers["firecrawl"]["limits"]
        self.assertFalse(tavily_limits["research_allowed"])
        self.assertFalse(tavily_limits["auto_parameters_allowed"])
        self.assertEqual(tavily_limits["crawl_pages_max"], 20)
        self.assertEqual(tavily_limits["crawl_depth_max"], 2)
        self.assertFalse(firecrawl_limits["browser_interaction_allowed"])
        self.assertFalse(firecrawl_limits["actions_allowed"])
        self.assertFalse(firecrawl_limits["arbitrary_headers_allowed"])
        self.assertFalse(firecrawl_limits["async_crawl_allowed"])

        market = json.loads(
            (ROOT / "market-search/provider-catalog.json").read_text(
                encoding="utf-8"
            )
        )
        market_providers = {
            row["provider_id"]: row for row in market["providers"]
        }
        tickflow_limits = market_providers["tickflow"]["limits"]
        serpapi_limits = market_providers["serpapi"]["limits"]
        self.assertFalse(tickflow_limits["write_or_trade_allowed"])
        self.assertFalse(tickflow_limits["websocket_allowed"])
        self.assertFalse(serpapi_limits["async_allowed"])
        self.assertFalse(serpapi_limits["html_output_allowed"])
        self.assertFalse(serpapi_limits["arbitrary_engine_allowed"])

        tushare = json.loads(
            (ROOT / "tushare/provider-catalog.json").read_text(encoding="utf-8")
        )
        tushare_provider = tushare["providers"][0]
        tushare_limits = tushare_provider["limits"]
        self.assertEqual(
            tushare_provider["required_secret_environment_variable"],
            "TUSHARE_API_TOKEN",
        )
        self.assertFalse(tushare_limits["arbitrary_api_names_allowed"])
        self.assertFalse(tushare_limits["arbitrary_urls_allowed"])
        self.assertFalse(tushare_limits["arbitrary_headers_allowed"])
        self.assertFalse(tushare_limits["write_operations_allowed"])
        self.assertFalse(tushare_limits["trading_or_order_execution_allowed"])
        self.assertFalse(tushare_limits["secret_values_exposed"])

        eodhd = json.loads(
            (ROOT / "eodhd/provider-catalog.json").read_text(encoding="utf-8")
        )
        eodhd_provider = eodhd["providers"][0]
        self.assertEqual(eodhd_provider["required_secret_environment_variable"], "EODHD_API_TOKEN")
        self.assertFalse(eodhd_provider["limits"]["arbitrary_urls_allowed"])
        self.assertFalse(eodhd_provider["limits"]["arbitrary_headers_allowed"])
        self.assertFalse(eodhd_provider["limits"]["write_operations_allowed"])
        self.assertFalse(eodhd_provider["limits"]["trading_or_order_execution_allowed"])

        baostock = json.loads(
            (ROOT / "baostock/provider-catalog.json").read_text(encoding="utf-8")
        )
        baostock_provider = baostock["providers"][0]
        self.assertEqual(baostock_provider["required_secret_environment_variable"], "")
        self.assertFalse(baostock_provider["limits"]["arbitrary_functions_allowed"])
        self.assertFalse(baostock_provider["limits"]["arbitrary_hosts_allowed"])
        self.assertFalse(baostock_provider["limits"]["write_operations_allowed"])
        self.assertFalse(baostock_provider["limits"]["trading_or_order_execution_allowed"])

        knowledge = json.loads(
            (ROOT / "knowledge-tools/provider-catalog.json").read_text(
                encoding="utf-8"
            )
        )
        knowledge_providers = {
            row["provider_id"]: row for row in knowledge["providers"]
        }
        wolfram = knowledge_providers["wolfram-alpha"]
        wolfram_limits = wolfram["limits"]
        self.assertEqual(
            wolfram["required_secret_environment_variable"],
            "WOLFRAM_ALPHA_APP_ID",
        )
        self.assertFalse(wolfram_limits["arbitrary_urls_allowed"])
        self.assertFalse(wolfram_limits["arbitrary_headers_allowed"])
        self.assertFalse(wolfram_limits["write_operations_allowed"])
        self.assertFalse(wolfram_limits["image_endpoints_enabled"])

        llamaparse = knowledge_providers["llamaparse"]
        llama_limits = llamaparse["limits"]
        self.assertEqual(
            llamaparse["required_secret_environment_variable"],
            "LLAMA_CLOUD_API_KEY",
        )
        self.assertFalse(llama_limits["arbitrary_urls_allowed"])
        self.assertFalse(llama_limits["arbitrary_headers_allowed"])
        self.assertFalse(llama_limits["webhooks_allowed"])
        self.assertFalse(llama_limits["write_operations_allowed"])
        self.assertFalse(llama_limits["presigned_urls_exposed"])
        self.assertLessEqual(llama_limits["max_pages"], 200)
        self.assertLessEqual(llama_limits["poll_timeout_seconds_max"], 600)


if __name__ == "__main__":
    unittest.main()
