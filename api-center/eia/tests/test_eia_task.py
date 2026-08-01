from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("eia_task", HERE / "eia_task.py")
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class EiaProviderTests(unittest.TestCase):
    def test_catalog_contract(self) -> None:
        catalog = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "eia")
        self.assertEqual(provider["ticket_prefix"], "[intel-eia]")
        self.assertEqual(provider["required_secret_environment_variable"], "EIA_API_KEY")
        self.assertEqual(len(provider["operations"]), 6)
        self.assertEqual(provider["limits"]["rows_per_response_max"], 5000)
        self.assertEqual(provider["limits"]["route_segments_max"], 8)
        self.assertFalse(provider["limits"]["automatic_pagination_allowed"])
        self.assertFalse(provider["limits"]["bulk_download_allowed"])
        self.assertFalse(provider["limits"]["write_operations_allowed"])

    def test_root_and_route_metadata_are_fixed(self) -> None:
        self.assertEqual(module.build_request("api-root", {}), ("/v2/", []))
        path, query = module.build_request("route-metadata", {"route": "electricity/retail-sales"})
        self.assertEqual(path, "/v2/electricity/retail-sales/")
        self.assertEqual(query, [])

    def test_route_traversal_and_reserved_segments_are_rejected(self) -> None:
        for route in ("../secret", "electricity//retail-sales", "electricity/data", "electricity/facet"):
            with self.assertRaises(ValueError):
                module.build_request("route-metadata", {"route": route})
        with self.assertRaises(ValueError):
            module.build_request("route-metadata", {"route": "/".join(["a"] * 9)})

    def test_facet_values_path_and_bounds(self) -> None:
        path, query = module.build_request(
            "facet-values",
            {"route": "electricity/retail-sales", "facet": "sectorid", "offset": 10, "length": 100},
        )
        self.assertEqual(path, "/v2/electricity/retail-sales/facet/sectorid/")
        self.assertEqual(query, [("offset", "10"), ("length", "100")])
        with self.assertRaises(ValueError):
            module.build_request("facet-values", {"route": "electricity", "facet": "../../x"})

    def test_data_query_supports_columns_facets_sort_and_pagination(self) -> None:
        path, query = module.build_request(
            "route-data",
            {
                "route": "electricity/retail-sales",
                "data": ["price", "sales"],
                "frequency": "monthly",
                "facets": {"sectorid": ["RES"], "stateid": ["CO", "US"]},
                "start": "2024-01",
                "end": "2026-07",
                "sort": [{"column": "period", "direction": "DESC"}],
                "offset": 0,
                "length": 24,
            },
        )
        self.assertEqual(path, "/v2/electricity/retail-sales/data/")
        self.assertIn(("data[]", "price"), query)
        self.assertIn(("data[]", "sales"), query)
        self.assertIn(("facets[sectorid][]", "RES"), query)
        self.assertIn(("facets[stateid][]", "CO"), query)
        self.assertIn(("sort[0][direction]", "desc"), query)
        self.assertIn(("length", "24"), query)
        self.assertNotIn(("api_key", "anything"), query)

    def test_data_limits_are_enforced(self) -> None:
        with self.assertRaises(ValueError):
            module.build_request("route-data", {"route": "petroleum/pri/spt", "data": [f"x{i}" for i in range(21)]})
        with self.assertRaises(ValueError):
            module.build_request("route-data", {"route": "petroleum/pri/spt", "data": ["value"], "length": 5001})
        with self.assertRaises(ValueError):
            module.build_request(
                "route-data",
                {"route": "petroleum/pri/spt", "data": ["value"], "facets": {"x": [str(i) for i in range(51)]}},
            )

    def test_series_id_and_secret_scrubbing(self) -> None:
        path, query = module.build_request("series-by-id", {"series_id": "ELEC.SALES.CO-RES.A"})
        self.assertEqual(path, "/v2/seriesid/ELEC.SALES.CO-RES.A")
        self.assertEqual(query, [])
        secret = "test-secret-key"
        payload = {"request": {"params": {"api_key": secret}}, "nested": [f"x-{secret}-y"]}
        clean = module._scrub(payload, secret)
        self.assertEqual(clean["request"]["params"]["api_key"], "[REDACTED]")
        self.assertNotIn(secret, json.dumps(clean))


if __name__ == "__main__":
    unittest.main()
