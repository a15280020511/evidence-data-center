from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "data_commons_task_tests", ROOT / "data_commons_task.py"
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class DataCommonsTaskTests(unittest.TestCase):
    def ticket(self, operation: str = "catalog-capabilities") -> dict:
        return {
            "task_id": "dc-test-0001",
            "provider": "data-commons",
            "operation": operation,
            "objective": "validate managed public statistics access",
            "parameters": {},
            "data_policy": {
                "classification": "public",
                "contains_personal_data": False,
            },
            "acceptance": {
                "timeout_seconds": 30,
                "max_response_bytes": 500000,
            },
        }

    def test_catalog_exposes_only_fixed_rest_v2_operations(self) -> None:
        catalog = module.load_json(ROOT / "provider-catalog.json")
        self.assertEqual(catalog["allowed_endpoints"], ["/resolve", "/node", "/observation"])
        self.assertEqual(
            {row["operation_id"] for row in catalog["operations"]},
            {
                "catalog-capabilities",
                "resolve-place",
                "resolve-indicator",
                "node-properties",
                "observations",
            },
        )
        self.assertFalse(catalog["secret_values_exposed"])
        self.assertFalse(catalog["security"]["sparql_allowed"])
        self.assertFalse(catalog["security"]["arbitrary_url_allowed"])

    def test_ticket_validation_rejects_unknown_parameter(self) -> None:
        ticket = self.ticket("resolve-place")
        ticket["parameters"] = {"nodes_json": '["Fuzhou"]'}
        module.validate_ticket(ticket)
        ticket["parameters"]["url"] = "https://example.com"
        with self.assertRaisesRegex(ValueError, "non-allowlisted parameters"):
            module.validate_ticket(ticket)

    def test_resolve_and_observation_bodies_are_bounded(self) -> None:
        endpoint, body, local = module._build_operation(
            "resolve-place",
            {
                "nodes_json": '["Fuzhou, Fujian, China"]',
                "property": "<-description{typeOf:City}->dcid",
            },
        )
        self.assertEqual(endpoint, "/resolve")
        self.assertEqual(body["resolver"], "place")
        self.assertEqual(local, {})

        endpoint, body, _ = module._build_operation(
            "observations",
            {
                "entity_dcids_json": '["country/CHN"]',
                "variable_dcids_json": '["Count_Person"]',
                "date": "LATEST",
                "select_json": '["date","entity","variable","value","facet"]',
            },
        )
        self.assertEqual(endpoint, "/observation")
        self.assertEqual(body["entity"]["dcids"], ["country/CHN"])
        self.assertEqual(body["variable"]["dcids"], ["Count_Person"])
        with self.assertRaisesRegex(ValueError, "must not contain URLs"):
            module._build_operation("resolve-place", {"nodes_json": '["https://example.com"]'})
        with self.assertRaisesRegex(ValueError, "select_json may contain only"):
            module._build_operation(
                "observations",
                {
                    "entity_dcids_json": '["country/CHN"]',
                    "variable_dcids_json": '["Count_Person"]',
                    "select_json": '["value","secret"]',
                },
            )

    def test_upstream_request_uses_header_without_recording_key(self) -> None:
        response = mock.Mock()
        response.content = b'{"entities": []}'
        response.status_code = 200
        response.ok = True
        response.headers = {"Content-Type": "application/json"}
        response.json.return_value = {"entities": []}
        with mock.patch.object(module.requests, "post", return_value=response) as post:
            payload, metadata = module._request_json(
                "/resolve",
                api_key="secret-value",
                body={"nodes": ["Fuzhou"], "resolver": "place"},
                timeout=30,
                max_bytes=500000,
            )
        self.assertEqual(payload, {"entities": []})
        headers = post.call_args.kwargs["headers"]
        self.assertEqual(headers["X-API-Key"], "secret-value")
        self.assertNotIn("secret-value", json.dumps(metadata))
        self.assertEqual(metadata["request_url"], "https://api.datacommons.org/v2/resolve")

    def test_catalog_executes_without_secret_and_live_operation_blocks_without_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            output_dir = root / "out"
            ticket_path.write_text(json.dumps(self.ticket()), encoding="utf-8")
            with mock.patch.dict(os.environ, {}, clear=True):
                rc = module.execute(ticket_path, output_dir)
            self.assertEqual(rc, 0)
            snapshot = json.loads((output_dir / "data-commons-snapshot.json").read_text(encoding="utf-8"))
            self.assertEqual(snapshot["status"], "API_DATA_COMMONS_COMPLETED")
            self.assertIn("china_starter_pack", snapshot["data"])

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket = self.ticket("resolve-place")
            ticket["parameters"] = {"nodes_json": '["Fuzhou"]'}
            ticket_path = root / "ticket.json"
            output_dir = root / "out"
            ticket_path.write_text(json.dumps(ticket), encoding="utf-8")
            with mock.patch.dict(os.environ, {}, clear=True):
                rc = module.execute(ticket_path, output_dir)
            self.assertEqual(rc, 1)
            snapshot = json.loads((output_dir / "data-commons-snapshot.json").read_text(encoding="utf-8"))
            self.assertEqual(snapshot["status"], "API_DATA_COMMONS_BLOCKED")
            self.assertEqual(snapshot["failure"]["code"], "DATA_COMMONS_API_KEY_MISSING")
            self.assertFalse(snapshot["security"]["secret_values_included"])


if __name__ == "__main__":
    unittest.main()
