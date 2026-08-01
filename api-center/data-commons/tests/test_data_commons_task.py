from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("data_commons_task", ROOT / "data_commons_task.py")
assert SPEC and SPEC.loader
dc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dc)


def ticket(operation: str, parameters: dict) -> dict:
    return {
        "task_id": "dc-test-001",
        "provider": "data-commons",
        "operation": operation,
        "objective": "validate bounded REST V2 access",
        "parameters": parameters,
        "data_policy": {"classification": "public", "contains_personal_data": False},
        "acceptance": {"timeout_seconds": 20, "max_response_bytes": 200000},
    }


class DataCommonsTaskTests(unittest.TestCase):
    def test_catalog_has_five_fixed_operations_and_independent_key(self) -> None:
        catalog = json.loads((ROOT / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "data-commons")
        self.assertEqual(provider["required_secret_environment_variable"], "GOOGLE_DATA_COMMONS_API_KEY")
        self.assertEqual(len(provider["operations"]), 5)
        self.assertFalse(provider["limits"]["arbitrary_urls_allowed"])
        self.assertFalse(provider["limits"]["sparql_allowed"])
        self.assertFalse(provider["limits"]["natural_language_api_allowed"])
        self.assertFalse(provider["limits"]["write_operations_allowed"])

    def test_observation_request_is_fixed_and_bounded(self) -> None:
        endpoint, body, local = dc._build_operation(
            "observations",
            {
                "entity_dcids_json": '["country/CHN"]',
                "variable_dcids_json": '["Count_Person"]',
                "date": "LATEST",
            },
        )
        self.assertEqual(endpoint, "/observation")
        self.assertEqual(body["entity"]["dcids"], ["country/CHN"])
        self.assertEqual(body["variable"]["dcids"], ["Count_Person"])
        self.assertEqual(local, {})

    def test_rejects_non_allowlisted_parameters(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-allowlisted"):
            dc.validate_ticket(ticket("resolve-place", {"nodes_json": '["China"]', "url": "https://evil.invalid"}))

    def test_missing_key_is_structured_and_secretless(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            path = out / "ticket.json"
            path.write_text(json.dumps(ticket("resolve-place", {"nodes_json": '["China"]'})), encoding="utf-8")
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(dc.execute(path, out), 1)
            snap = json.loads((out / "data-commons-snapshot.json").read_text(encoding="utf-8"))
            self.assertEqual(snap["failure"]["code"], "DATA_COMMONS_API_KEY_MISSING")
            self.assertFalse(snap["security"]["secret_values_included"])
            self.assertFalse(snap["security"]["api_key_recorded"])

    def test_successful_request_uses_x_api_key_without_recording_value(self) -> None:
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.content = b'{"entities":[{"node":"China"}]}'
        response.headers = {"Content-Type": "application/json"}
        response.json.return_value = {"entities": [{"node": "China"}]}
        with patch.object(dc.requests, "post", return_value=response) as post:
            data, metadata = dc._request_json(
                "/resolve", api_key="test-visible-key",
                body={"nodes": ["China"], "resolver": "place"},
                timeout=20, max_bytes=200000,
            )
        self.assertEqual(data["entities"][0]["node"], "China")
        headers = post.call_args.kwargs["headers"]
        self.assertEqual(headers["X-API-Key"], "test-visible-key")
        self.assertNotIn("test-visible-key", json.dumps(metadata))


if __name__ == "__main__":
    unittest.main()
