from __future__ import annotations
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
