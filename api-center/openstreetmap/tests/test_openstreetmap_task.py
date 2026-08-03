from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("openstreetmap_task", ROOT / "openstreetmap_task.py")
assert SPEC and SPEC.loader
task = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(task)


class FakeResponse:
    ok = True
    status_code = 200
    headers = {"Content-Type": "application/json"}
    content = b'{"version":0.6,"elements":[]}'

    def json(self):
        return json.loads(self.content)


class FakeListResponse(FakeResponse):
    content = b'[{"place_id":1,"lat":"26.08","lon":"119.30"}]'


class OpenStreetMapTests(unittest.TestCase):
    def ticket(self, operation="catalog-capabilities", parameters=None):
        return {
            "task_id": "osm-test-001",
            "provider": "openstreetmap",
            "operation": operation,
            "objective": "test bounded OSM provider",
            "parameters": parameters or {},
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "acceptance": {"timeout_seconds": 30, "max_response_bytes": 1000000},
        }

    def test_catalog_and_schema(self):
        catalog = json.loads((ROOT / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "openstreetmap")
        self.assertEqual(provider["ticket_prefix"], "[intel-osm]")
        self.assertEqual(len(provider["operations"]), 6)
        self.assertEqual(provider["limits"]["provider_concurrency_max"], 1)
        self.assertFalse(provider["limits"]["raw_overpass_ql_allowed"])
        self.assertFalse(provider["limits"]["nominatim_bulk_geocoding_allowed"])
        task.validate_ticket(self.ticket(), schema_path=task.SCHEMA_PATH, catalog_path=task.CATALOG_PATH)

    def test_overpass_builder_is_template_only(self):
        url, method, body = task.build_request("overpass-nearby", {
            "lat": 26.08, "lon": 119.30, "radius_m": 500,
            "tag_key": "amenity", "tag_value": "hospital", "limit": 25,
        })
        self.assertEqual(url, "https://overpass-api.de/api/interpreter")
        self.assertEqual(method, "POST")
        self.assertIn('["amenity"="hospital"]', body)
        self.assertIn("out body 25", body)
        with self.assertRaises(ValueError):
            task.build_request("overpass-nearby", {
                "lat": 26.08, "lon": 119.30, "tag_key": 'amenity"];out;node["x',
            })
        with self.assertRaises(ValueError):
            task.build_request("overpass-bbox", {
                "south": 20, "west": 110, "north": 25, "east": 120, "tag_key": "shop",
            })

    def test_local_catalog_needs_no_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            ticket = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket.write_text(json.dumps(self.ticket()), encoding="utf-8")
            self.assertEqual(task.execute(ticket, out), 0)
            diagnostics = json.loads((out / "diagnostics.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostics["status"], "INTEL_OPENSTREETMAP_COMPLETED")
            self.assertFalse(diagnostics["metadata"]["upstream_called"])

    def test_nominatim_is_one_get_with_user_agent(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(task.requests, "get", return_value=FakeListResponse()) as get:
            ticket = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket.write_text(json.dumps(self.ticket("nominatim-search", {"query": "Fuzhou", "limit": 1})), encoding="utf-8")
            self.assertEqual(task.execute(ticket, out), 0)
            self.assertEqual(get.call_count, 1)
            kwargs = get.call_args.kwargs
            self.assertFalse(kwargs["allow_redirects"])
            self.assertIn("a15280020511-evidence-data-center", kwargs["headers"]["User-Agent"])

    def test_overpass_is_one_post(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(task.requests, "post", return_value=FakeResponse()) as post:
            ticket = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket.write_text(json.dumps(self.ticket("overpass-nearby", {
                "lat": 26.08, "lon": 119.30, "tag_key": "amenity", "tag_value": "hospital",
            })), encoding="utf-8")
            self.assertEqual(task.execute(ticket, out), 0)
            self.assertEqual(post.call_count, 1)
            body = post.call_args.kwargs["data"]["data"]
            self.assertNotIn("{{", body)
            self.assertIn("[out:json]", body)


if __name__ == "__main__":
    unittest.main()
