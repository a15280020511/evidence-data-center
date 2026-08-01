from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "un_comtrade_task", HERE / "un_comtrade_task.py"
)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class UnComtradeProviderTests(unittest.TestCase):
    def test_catalog_contract(self) -> None:
        catalog = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "un-comtrade")
        self.assertEqual(provider["ticket_prefix"], "[intel-un-comtrade]")
        self.assertEqual(
            provider["required_secret_environment_variable"],
            "UN_COMTRADE_API_KEY",
        )
        self.assertEqual(len(provider["operations"]), 10)
        self.assertEqual(provider["limits"]["preview_records_max"], 500)
        self.assertEqual(provider["limits"]["records_per_request_max"], 5000)
        self.assertEqual(provider["limits"]["free_api_calls_per_day"], 500)
        self.assertFalse(provider["limits"]["bulk_api_allowed"])
        self.assertFalse(provider["limits"]["async_api_allowed"])
        self.assertFalse(provider["limits"]["write_operations_allowed"])

    def test_preview_request_is_keyless_and_bounded(self) -> None:
        path, query, requires_key = module.build_request(
            "preview-trade",
            {
                "type_code": "C",
                "frequency": "A",
                "classification": "HS",
                "periods": [2023],
                "reporter_codes": [156],
                "commodity_codes": ["TOTAL"],
                "flow_codes": ["X"],
                "partner_codes": [0],
                "max_records": 500,
            },
        )
        values = dict(query)
        self.assertEqual(path, "/public/v1/preview/C/A/HS")
        self.assertFalse(requires_key)
        self.assertEqual(values["period"], "2023")
        self.assertEqual(values["reporterCode"], "156")
        self.assertEqual(values["maxRecords"], "500")
        self.assertNotIn("subscription-key", values)

    def test_preview_rejects_multiple_periods_or_commodities(self) -> None:
        base = {
            "type_code": "C",
            "frequency": "A",
            "classification": "HS",
            "periods": [2022, 2023],
            "reporter_codes": [156],
            "commodity_codes": ["TOTAL"],
            "flow_codes": ["X"],
        }
        with self.assertRaises(ValueError):
            module.build_request("preview-trade", base)
        base["periods"] = [2023]
        base["commodity_codes"] = ["01", "02"]
        with self.assertRaises(ValueError):
            module.build_request("preview-trade", base)

    def test_final_trade_supports_bounded_multi_value_filters(self) -> None:
        path, query, requires_key = module.build_request(
            "final-trade",
            {
                "type_code": "c",
                "frequency": "a",
                "classification": "h6",
                "periods": [2022, 2023],
                "reporter_codes": [156, 840],
                "commodity_codes": ["27", "2711"],
                "flow_codes": ["M", "X"],
                "partner_codes": [0, 392],
                "include_descriptions": True,
                "max_records": 5000,
            },
        )
        values = dict(query)
        self.assertEqual(path, "/data/v1/get/C/A/H6")
        self.assertTrue(requires_key)
        self.assertEqual(values["period"], "2022,2023")
        self.assertEqual(values["reporterCode"], "156,840")
        self.assertEqual(values["cmdCode"], "27,2711")
        self.assertEqual(values["includeDesc"], "true")
        self.assertNotIn("subscription-key", values)

    def test_tariffline_and_trade_balance_are_goods_only(self) -> None:
        parameters = {
            "type_code": "S",
            "frequency": "A",
            "classification": "EB",
            "periods": [2023],
            "reporter_codes": [156],
            "commodity_codes": ["TOTAL"],
            "flow_codes": ["X"],
        }
        with self.assertRaises(ValueError):
            module.build_request("tariffline-trade", parameters)
        parameters.pop("flow_codes")
        with self.assertRaises(ValueError):
            module.build_request("trade-balance", parameters)

    def test_availability_metadata_and_live_update_paths(self) -> None:
        path, query, requires_key = module.build_request(
            "data-availability",
            {
                "type_code": "C",
                "frequency": "M",
                "classification": "HS",
                "periods": [202501, 202502],
                "reporter_codes": [156],
                "published_date_from": "2026-01-01",
                "published_date_to": "2026-08-01",
            },
        )
        self.assertEqual(path, "/data/v1/getDa/C/M/HS")
        self.assertTrue(requires_key)
        self.assertEqual(dict(query)["period"], "202501,202502")
        self.assertEqual(
            module.build_request(
                "metadata",
                {
                    "type_code": "C",
                    "frequency": "A",
                    "classification": "HS",
                    "periods": [2023],
                    "reporter_codes": [156],
                },
            )[0],
            "/data/v1/getMetadata/C/A/HS",
        )
        self.assertEqual(
            module.build_request("live-updates", {})[0],
            "/data/v1/getLiveUpdate",
        )

    def test_reversed_dates_and_oversized_queries_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            module.build_request(
                "data-availability",
                {
                    "type_code": "C",
                    "frequency": "A",
                    "classification": "HS",
                    "published_date_from": "2026-08-02",
                    "published_date_to": "2026-08-01",
                },
            )
        with self.assertRaises(ValueError):
            module.build_request(
                "final-trade",
                {
                    "type_code": "C",
                    "frequency": "A",
                    "classification": "HS",
                    "periods": [2023],
                    "reporter_codes": [156],
                    "commodity_codes": ["TOTAL"],
                    "flow_codes": ["X"],
                    "max_records": 5001,
                },
            )

    def test_reference_paths_are_fixed_and_keyless(self) -> None:
        self.assertEqual(
            module.build_request("reporters-reference", {}),
            ("/files/v1/app/reference/Reporters.json", [], False),
        )
        self.assertEqual(
            module.build_request("partners-reference", {}),
            ("/files/v1/app/reference/partnerAreas.json", [], False),
        )

    def test_recursive_secret_scrubbing(self) -> None:
        secret = "private-subscription-key"
        value = {
            "request": {"subscription-key": secret},
            "data": [f"prefix-{secret}-suffix"],
        }
        cleaned = module._scrub(value, secret)
        rendered = json.dumps(cleaned)
        self.assertNotIn(secret, rendered)
        self.assertIn("[REDACTED]", rendered)


if __name__ == "__main__":
    unittest.main()
