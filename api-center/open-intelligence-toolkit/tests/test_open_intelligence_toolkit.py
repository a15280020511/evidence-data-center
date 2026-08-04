import importlib.util,json,os,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import open_intelligence_toolkit_task as runtime
class ToolkitTests(unittest.TestCase):
 def test_catalog_is_no_key_and_bounded(self):
  c=json.loads((HERE/"provider-catalog.json").read_text());p=c["providers"][0]
  self.assertEqual(len(p["operations"]),20);self.assertEqual(p["required_secret_environment_variable"],"");self.assertFalse(p["limits"]["arbitrary_urls_allowed"]);self.assertFalse(p["limits"]["write_operations_allowed"])
 def test_fixed_portal_allowlists(self):
  for op,p in [("ckan-package-search",{"portal":"uk","query":"x"}),("socrata-dataset-rows",{"portal":"cdc","dataset_id":"9mfq-cb36"})]:
   _,u,_,_,_,_=runtime.build(op,p);self.assertTrue(u.startswith("https://"))
  with self.assertRaises(ValueError):runtime.build("ckan-package-search",{"portal":"evil","query":"x"})
 def test_html_is_offline_and_structured(self):
  data=runtime.html_extract({"html":"<html><head><script type='application/ld+json'>{\"@type\":\"Article\"}</script></head><body><main><p>A long public article body used for extraction validation without any network call.</p></main></body></html>","base_url":"https://example.com/"})
  self.assertIn("json-ld",data["structured_data"]);self.assertTrue(data["text_markdown"])
 def test_schema_operation_set_matches_catalog(self):
  c=json.loads((HERE/"provider-catalog.json").read_text())["providers"][0];s=json.loads((HERE/"ticket.schema.json").read_text())
  self.assertEqual({x["operation_id"] for x in c["operations"]},set(s["properties"]["operation"]["enum"]))
if __name__=="__main__":unittest.main()
