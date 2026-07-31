from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CapabilityMaximizationTests(unittest.TestCase):
    def test_maximum_safe_readonly_surface_is_registered(self) -> None:
        manifest = json.loads((ROOT / "connector-manifest.json").read_text(encoding="utf-8"))
        rows = manifest["connectors"]
        self.assertEqual(manifest["connector_count"], 69)
        self.assertEqual(manifest["enabled_connector_count"], 69)
        counts = {
            prefix: sum(row["id"].startswith(prefix) for row in rows)
            for prefix in (
                "amap-", "baidu-", "openmeteo-", "worldbank-",
                "wikidata-", "dbnomics-", "osm-", "newsapi-",
            )
        }
        self.assertEqual(counts, {
            "amap-": 19, "baidu-": 15, "openmeteo-": 11,
            "worldbank-": 9, "wikidata-": 4, "dbnomics-": 3,
            "osm-": 3, "newsapi-": 3,
        })
        self.assertTrue(all(row["method"] == "GET" for row in rows if row["enabled"]))
        self.assertTrue(all(not row["write_approved"] for row in rows))

    def test_managed_providers_expose_fixed_readonly_operations_only(self) -> None:
        catalog = json.loads((ROOT / "api-catalog.json").read_text(encoding="utf-8"))
        providers = {row["provider_id"]: row for row in catalog["managed_providers"]}
        self.assertEqual(sum(len(row["operations"]) for row in providers.values()), 93)
        self.assertEqual(len(providers["aifin-market"]["operations"]), 17)
        self.assertEqual(len(providers["akshare"]["operations"]), 17)
        self.assertEqual(len(providers["bigquery"]["operations"]), 7)
        self.assertEqual(len(providers["earth-engine"]["operations"]), 6)
        self.assertEqual(len(providers["yuandian-law"]["operations"]), 40)
        self.assertEqual(providers["yuandian-law"]["discovered_readonly_tool_count"], 37)
        self.assertFalse(any(row["secret_value_exposed"] for row in providers.values()))

    def test_no_unbounded_escape_hatch_is_introduced(self) -> None:
        aifin = json.loads((ROOT / "aifin-market/provider-catalog.json").read_text(encoding="utf-8"))
        wind_limits = aifin["providers"][0]["limits"]
        self.assertEqual(wind_limits["upstream_tools_exposed"], 15)
        self.assertFalse(wind_limits["arbitrary_tool_names_allowed"])
        self.assertFalse(wind_limits["arbitrary_urls_allowed"])
        self.assertFalse(wind_limits["trading_or_order_execution_allowed"])
        akshare = json.loads((ROOT / "akshare/provider-catalog.json").read_text(encoding="utf-8"))
        ak_limits = next(row for row in akshare["providers"] if row["provider_id"] == "akshare")["limits"]
        self.assertFalse(ak_limits["arbitrary_functions_allowed"])
        self.assertFalse(ak_limits["arbitrary_urls_allowed"])
        self.assertFalse(ak_limits["brokerage_execution_allowed"])
        yuandian = json.loads((ROOT / "yuandian/provider-catalog.json").read_text(encoding="utf-8"))
        legal_limits = yuandian["providers"][0]["limits"]
        self.assertFalse(legal_limits["arbitrary_urls_allowed"])
        self.assertFalse(legal_limits["arbitrary_headers_allowed"])
        self.assertFalse(legal_limits["write_operations_allowed"])
        self.assertFalse(legal_limits["secret_values_exposed"])
        self.assertTrue(legal_limits["direct_personal_identifiers_redacted"])


if __name__ == "__main__":
    unittest.main()
