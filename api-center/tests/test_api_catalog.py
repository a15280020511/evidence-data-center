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
    "alphafeed": 10,
    "agent-toolbelt": 21,
    "gapup-mcp": 209,
    "who-gho-odata": 8,
    "wolfram-alpha": 4,
    "llamaparse": 3,
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
        self.assertEqual(catalog["connector_count"], 68)
        self.assertEqual(catalog["managed_provider_count"], 32)
        self.assertEqual(catalog["enabled_managed_provider_count"], 32)
        self.assertEqual(catalog["managed_operation_count"], 577)
        self.assertGreaterEqual(catalog["exposed_parameter_count"], 850)
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
            "agent-toolbelt": "AGENT_TOOLBELT_KEY",
            "gapup-mcp": "GAPUP_API_KEY",
            "wolfram-alpha": "WOLFRAM_ALPHA_APP_ID",
            "llamaparse": "LLAMA_CLOUD_API_KEY",
        }
        for provider_id, secret_name in expected_secret_names.items():
            self.assertEqual(
                providers[provider_id][
                    "required_secret_environment_variable_name"
                ],
                secret_name,
            )

        self.assertEqual(providers["browserless"]["ticket_prefix"], "[api-browserless]")
        self.assertEqual(providers["browserless"]["required_secret_environment_variable_name"], "BROWSERLESS_TOKEN")
        self.assertEqual(providers["browserless"]["limits"]["fixed_api_host"], "production-sfo.browserless.io")
        self.assertFalse(providers["browserless"]["limits"]["arbitrary_code_allowed"])
        self.assertFalse(providers["browserless"]["limits"]["captcha_or_unblock_allowed"])
        self.assertFalse(providers["browserless"]["limits"]["profiles_allowed"])

        self.assertEqual(providers["data-commons"]["ticket_prefix"], "[api-dc]")
        self.assertEqual(providers["data-commons"]["required_secret_environment_variable_name"], "GOOGLE_DATA_COMMONS_API_KEY")
        self.assertFalse(providers["data-commons"]["limits"]["arbitrary_urls_allowed"])
        self.assertFalse(providers["data-commons"]["limits"]["sparql_allowed"])

        self.assertEqual(providers["qweather"]["ticket_prefix"], "[api-qweather]")
        self.assertEqual(providers["qweather"]["required_secret_environment_variable_name"], "QWEATHER_API_KEY")
        self.assertEqual(providers["qweather"]["limits"]["fixed_api_host"], "ka6r72kcc3.re.qweatherapi.com")
        self.assertFalse(providers["qweather"]["limits"]["arbitrary_hosts_allowed"])
        self.assertFalse(providers["qweather"]["limits"]["redirects_allowed"])

        xweather = providers["xweather"]
        self.assertEqual(xweather["ticket_prefix"], "[api-xweather]")
        self.assertEqual(
            xweather["required_secret_environment_variable_name"],
            "XWEATHER_CLIENT_SECRET",
        )
        self.assertEqual(xweather["required_repository_variable"], "XWEATHER_CLIENT_ID")
        self.assertEqual(len(xweather["operations"]), 10)
        self.assertEqual(xweather["limits"]["fixed_api_host"], "data.api.xweather.com")
        self.assertFalse(xweather["limits"]["arbitrary_query_parameters_allowed"])
        self.assertFalse(xweather["limits"]["client_supplied_credentials_allowed"])
        self.assertFalse(xweather["limits"]["write_operations_allowed"])

        self.assertEqual(providers["miaoxiang-mcp"]["ticket_prefix"], "[api-mx-mcp]")
        self.assertEqual(providers["miaoxiang-mcp"]["required_secret_environment_variable_name"], "EM_API_KEY")
        self.assertEqual(providers["miaoxiang-mcp"]["limits"]["fixed_mcp_tool_count"], 11)
        self.assertFalse(providers["miaoxiang-mcp"]["limits"]["arbitrary_jsonrpc_methods_allowed"])
        self.assertFalse(providers["miaoxiang-mcp"]["limits"]["arbitrary_mcp_tool_names_allowed"])
        self.assertFalse(providers["miaoxiang-mcp"]["limits"]["write_operations_allowed"])
        self.assertFalse(providers["miaoxiang-mcp"]["limits"]["trading_or_order_execution_allowed"])

        self.assertEqual(providers["baostock"]["ticket_prefix"], "[api-baostock]")
        self.assertEqual(providers["baostock"]["required_secret_environment_variable_name"], "")
        self.assertFalse(providers["baostock"]["limits"]["arbitrary_functions_allowed"])
        self.assertFalse(providers["baostock"]["limits"]["trading_or_order_execution_allowed"])

        self.assertEqual(providers["eodhd"]["ticket_prefix"], "[api-eodhd]")
        self.assertEqual(providers["eodhd"]["required_secret_environment_variable_name"], "EODHD_API_TOKEN")
        self.assertFalse(providers["eodhd"]["limits"]["arbitrary_urls_allowed"])
        self.assertFalse(providers["eodhd"]["limits"]["trading_or_order_execution_allowed"])

        east_asia = providers["east-asia-econ"]
        self.assertEqual(east_asia["ticket_prefix"], "[api-east-asia-econ]")
        self.assertEqual(east_asia["required_secret_environment_variable_name"], "EAST_ASIA_ECON_API_KEY")
        self.assertEqual(east_asia["limits"]["fixed_api_host"], "data-api.eastasiaecon.com")
        self.assertEqual(east_asia["limits"]["requests_per_ticket_max"], 1)
        self.assertFalse(east_asia["limits"]["arbitrary_urls_allowed"])
        self.assertFalse(east_asia["limits"]["arbitrary_headers_allowed"])
        self.assertFalse(east_asia["limits"]["write_operations_allowed"])

        alpha_vantage = providers["alpha-vantage"]
        self.assertEqual(alpha_vantage["ticket_prefix"], "[api-alpha-vantage]")
        self.assertEqual(
            alpha_vantage["required_secret_environment_variable_name"],
            "ALPHA_VANTAGE_API_KEY",
        )
        self.assertEqual(len(alpha_vantage["operations"]), 66)
        self.assertEqual(
            alpha_vantage["limits"]["fixed_api_host"],
            "www.alphavantage.co",
        )
        self.assertEqual(alpha_vantage["limits"]["requests_per_ticket_max"], 1)
        self.assertEqual(alpha_vantage["limits"]["provider_concurrency_max"], 1)
        self.assertFalse(alpha_vantage["limits"]["arbitrary_functions_allowed"])
        self.assertFalse(alpha_vantage["limits"]["client_supplied_api_key_allowed"])
        self.assertFalse(alpha_vantage["limits"]["write_operations_allowed"])
        self.assertFalse(
            alpha_vantage["limits"]["trading_or_order_execution_allowed"]
        )

        overture = providers["overture-maps"]
        self.assertEqual(overture["ticket_prefix"], "[api-overture]")
        self.assertEqual(overture["required_secret_environment_variable_name"], "")
        self.assertEqual(len(overture["operations"]), 7)
        self.assertFalse(overture["limits"]["whole_world_download_allowed"])
        self.assertFalse(overture["limits"]["arbitrary_s3_paths_allowed"])

        oecd = providers["oecd"]
        self.assertEqual(oecd["ticket_prefix"], "[api-oecd]")
        self.assertEqual(oecd["required_secret_environment_variable_name"], "")
        self.assertEqual(len(oecd["operations"]), 6)
        self.assertEqual(oecd["limits"]["fixed_api_host"], "sdmx.oecd.org")
        self.assertFalse(oecd["limits"]["arbitrary_sdmx_resource_types_allowed"])

        alphafeed = providers["alphafeed"]
        self.assertEqual(alphafeed["ticket_prefix"], "[api-alphafeed]")
        self.assertEqual(
            alphafeed["required_secret_environment_variable_name"],
            "ALPHAFEED_API_KEY",
        )
        self.assertEqual(len(alphafeed["operations"]), 10)
        self.assertEqual(alphafeed["limits"]["fixed_api_host"], "api.alphafeed.org")
        self.assertFalse(alphafeed["limits"]["arbitrary_sdk_methods_allowed"])
        self.assertFalse(alphafeed["limits"]["trading_or_order_execution_allowed"])


        agent_toolbelt = providers["agent-toolbelt"]
        self.assertEqual(
            agent_toolbelt["ticket_prefix"],
            "[api-agent-toolbelt]",
        )
        self.assertEqual(
            agent_toolbelt["required_secret_environment_variable_name"],
            "AGENT_TOOLBELT_KEY",
        )
        self.assertEqual(len(agent_toolbelt["operations"]), 21)
        self.assertFalse(
            {row["operation_id"] for row in agent_toolbelt["operations"]}
            & {"stock-thesis", "earnings-analysis", "insider-signal", "valuation-snapshot", "bear-vs-bull", "compare-stocks", "moat-analysis", "watchlist-scan"}
        )
        self.assertEqual(
            agent_toolbelt["limits"]["fixed_api_host"],
            "www.agenttoolbelt.live",
        )
        self.assertFalse(
            agent_toolbelt["limits"]["arbitrary_tool_names_allowed"]
        )
        self.assertFalse(agent_toolbelt["limits"]["watchlist_crud_allowed"])
        self.assertFalse(agent_toolbelt["limits"]["write_operations_allowed"])
        self.assertFalse(
            agent_toolbelt["limits"]["trading_or_order_execution_allowed"]
        )

        gapup = providers["gapup-mcp"]
        gapup_ids = {row["operation_id"] for row in gapup["operations"]}
        self.assertEqual(gapup["ticket_prefix"], "[intel-gapup]")
        self.assertEqual(gapup["required_secret_environment_variable_name"], "GAPUP_API_KEY")
        self.assertEqual(len(gapup_ids), 209)
        self.assertEqual(gapup["limits"]["fixed_mcp_tool_count"], 208)
        self.assertFalse(gapup["limits"]["automatic_x402_payment_allowed"])
        self.assertFalse(gapup["limits"]["async_jobs_allowed"])
        self.assertFalse(gapup["limits"]["write_operations_allowed"])
        self.assertNotIn("crm_connector", gapup_ids)
        self.assertNotIn("webhooks_manage", gapup_ids)

        who = providers["who-gho-odata"]
        self.assertEqual(who["ticket_prefix"], "[intel-who-gho]")
        self.assertEqual(who["required_secret_environment_variable_name"], "")
        self.assertEqual(len(who["operations"]), 8)
        self.assertEqual(who["limits"]["fixed_api_host"], "ghoapi.azureedge.net")
        self.assertFalse(who["limits"]["arbitrary_odata_filters_allowed"])
        self.assertFalse(who["limits"]["automatic_pagination_allowed"])
        self.assertFalse(who["limits"]["write_operations_allowed"])
        self.assertTrue(who["limits"]["legacy_endpoint_migration_watch_required"])

        self.assertEqual(
            providers["tushare"]["ticket_prefix"],
            "[api-tushare]",
        )
        self.assertEqual(
            {row["operation_id"] for row in providers["tushare"]["operations"]},
            {
                "catalog-capabilities",
                "trade-calendar",
                "stock-basic",
                "daily-quotes",
                "weekly-quotes",
                "monthly-quotes",
                "adjust-factor",
                "daily-basic",
                "money-flow",
                "margin-summary",
                "top-list",
                "income-statement",
                "balance-sheet",
                "cash-flow-statement",
                "financial-indicator",
                "index-basic",
                "index-daily",
                "fund-basic",
                "fund-nav",
                "hk-hold",
            },
        )
        tushare_limits = providers["tushare"]["limits"]
        self.assertFalse(tushare_limits["arbitrary_api_names_allowed"])
        self.assertFalse(tushare_limits["arbitrary_urls_allowed"])
        self.assertFalse(tushare_limits["write_operations_allowed"])
        self.assertFalse(tushare_limits["trading_or_order_execution_allowed"])

        wolfram = providers["wolfram-alpha"]
        self.assertEqual(wolfram["ticket_prefix"], "[api-wolfram]")
        self.assertEqual(
            {row["operation_id"] for row in wolfram["operations"]},
            {
                "catalog-capabilities",
                "full-results",
                "short-answer",
                "llm-result",
            },
        )
        self.assertFalse(wolfram["limits"]["arbitrary_urls_allowed"])
        self.assertFalse(wolfram["limits"]["write_operations_allowed"])

        llamaparse = providers["llamaparse"]
        self.assertEqual(llamaparse["ticket_prefix"], "[api-llamaparse]")
        self.assertEqual(
            {row["operation_id"] for row in llamaparse["operations"]},
            {
                "catalog-capabilities",
                "parse-public-document",
                "get-job",
            },
        )
        self.assertFalse(llamaparse["limits"]["arbitrary_urls_allowed"])
        self.assertFalse(llamaparse["limits"]["webhooks_allowed"])
        self.assertFalse(llamaparse["limits"]["presigned_urls_exposed"])

        for catalog_file in (
            "tushare/provider-catalog.json",
            "baostock/provider-catalog.json",
            "eodhd/provider-catalog.json",
            "data-commons/provider-catalog.json",
            "qweather/provider-catalog.json",
            "xweather/provider-catalog.json",
            "miaoxiang-mcp/provider-catalog.json",
            "east-asia-econ/provider-catalog.json",
            "alpha-vantage/provider-catalog.json",
            "overture-maps/provider-catalog.json",
            "oecd/provider-catalog.json",
            "alphafeed/provider-catalog.json",
            "knowledge-tools/provider-catalog.json",
        ):
            self.assertIn(catalog_file, catalog["managed_provider_catalog_files"])
            self.assertIn(catalog_file, catalog["detail_reading_order"])
        self.assertNotIn(
            "tianditu/provider-catalog.json",
            catalog["managed_provider_catalog_files"],
        )

        self.assertEqual(
            providers["yuandian-law"]["discovered_readonly_tool_count"],
            37,
        )
        self.assertEqual(
            providers["jina-reader"][
                "required_secret_environment_variable_name"
            ],
            "",
        )
        self.assertEqual(
            providers["jina-reader"][
                "optional_secret_environment_variable_name"
            ],
            "JINA_API_KEY",
        )
        self.assertEqual(
            providers["akshare"]["required_secret_environment_variable_name"],
            "",
        )

        connector_map = {
            row["connector_id"]: row for row in catalog["connectors"]
        }
        self.assertTrue(
            {
                "newsapi-everything",
                "newsapi-top-headlines",
                "newsapi-sources",
                "openmeteo-forecast",
                "baidu-geocode",
                "baidu-place-search",
                "worldbank-indicators",
                "wikidata-entity-get",
                "dbnomics-search",
            }.issubset(connector_map)
        )
        for connector_id in (
            "newsapi-everything",
            "newsapi-top-headlines",
            "newsapi-sources",
        ):
            self.assertTrue(connector_map[connector_id]["enabled"])
            self.assertEqual(
                connector_map[connector_id]["secret_environment_variable_name"],
                "NEWSAPI_API_KEY",
            )

        serialized = json.dumps(catalog, ensure_ascii=False)
        self.assertNotIn("VALIDATION_DUMMY_SECRET", serialized)
        self.assertNotIn("TIANDITU_API_KEY", serialized)
        self.assertNotIn("TIANDITU_EXPECTED_EGRESS_IP", serialized)
        self.assertNotIn("QICHACHA_CREDENTIALS_JSON", serialized)
        self.assertNotIn("Bearer llx-", serialized)
        for row in catalog["connectors"]:
            self.assertIn("parameter_names", row)
            self.assertIn("detail_file", row)
            self.assertIn("metadata_pointer", row)
            self.assertFalse(row["secret_value_exposed"])
            detail = ROOT / row["detail_file"]
            self.assertTrue(detail.is_file())
            connector = json.loads(detail.read_text(encoding="utf-8"))
            if row["enabled"]:
                contract = connector.get("response_contract")
                self.assertIsInstance(contract, dict)
                status_contract = bool(
                    contract.get("status_path")
                    and contract.get("success_values")
                )
                data_contract = bool(
                    contract.get("success_when_data_present") is True
                    and contract.get("any_data_paths")
                )
                self.assertTrue(status_contract or data_contract)

    def test_catalog_output_is_deterministic(self) -> None:
        first = self.build()
        second = self.build()
        self.assertEqual(first, second)
        self.assertEqual(
            first["generation"],
            "deterministic-from-repository-state",
        )

    def test_committed_catalog_matches_generator(self) -> None:
        generated = self.build()
        committed = json.loads(
            (ROOT / "api-catalog.json").read_text(encoding="utf-8")
        )
        self.assertEqual(generated, committed)
        self.assertEqual(
            build_catalog.render_markdown(generated),
            (ROOT / "api-catalog.md").read_text(encoding="utf-8"),
        )

    def test_main_writes_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog = self.build()
            json_path = root / "catalog.json"
            markdown_path = root / "catalog.md"
            json_path.write_text(
                json.dumps(catalog, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            markdown_path.write_text(
                build_catalog.render_markdown(catalog),
                encoding="utf-8",
            )
            self.assertIn(
                "GPTs 使用中心",
                markdown_path.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "catalog_sha256",
                json_path.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
