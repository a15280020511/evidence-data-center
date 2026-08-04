from __future__ import annotations
import importlib.util, json, os, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("public_data",ROOT/"public_data_geospatial_task.py")
assert SPEC and SPEC.loader
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)
class PublicDataTests(unittest.TestCase):
    def test_catalog_operation_count(self):
        c=json.loads((ROOT/"provider-catalog.json").read_text())
        self.assertEqual(len(c["providers"][0]["operations"]),34)
        self.assertFalse(c["secret_values_exposed"])
    def test_openrouteservice_new_host_and_no_client_key(self):
        os.environ["OPENROUTESERVICE_API_KEY"]="test"
        s=mod.build("openrouteservice-directions",{"profile":"driving-car","coordinates":[[119.29,26.08],[119.31,26.10]]})
        self.assertEqual(s.url,"https://api.heigit.org/openrouteservice/v2/directions/driving-car/geojson")
        self.assertNotIn("test",s.url)
    def test_nbs_waf_blocked_operations_are_not_exposed(self):
        c=json.loads((ROOT/"provider-catalog.json").read_text())
        operation_ids={row["operation_id"] for row in c["providers"][0]["operations"]}
        self.assertTrue({"nbs-search","nbs-query-data","nbs-new-tree","nbs-new-indicators"}.isdisjoint(operation_ids))
        with self.assertRaises(ValueError): mod.build("nbs-search",{"query":"GDP"})
    def test_overpass_rejects_non_json(self):
        with self.assertRaises(ValueError): mod.build("overpass-query",{"query":"[out:xml];node(1);out;"})
    def test_local_china_catalogs(self):
        self.assertGreaterEqual(len(mod.build("china-local-open-data-catalog",{})["portals"]),6)
        self.assertGreaterEqual(len(mod.build("china-science-data-centers",{})["centers"]),9)
if __name__=="__main__": unittest.main()
