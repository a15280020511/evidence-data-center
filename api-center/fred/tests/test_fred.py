from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("fred_task", HERE / "fred_task.py")
assert SPEC is not None and SPEC.loader is not None
fred = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fred)


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code
        self.content = json.dumps(payload).encode("utf-8")
        self.headers = {"Content-Type": "application/json"}

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> dict:
        return self._payload


class FredProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
        self.schema = json.loads((HERE / "ticket.schema.json").read_text(encoding="utf-8"))

    def _ticket(self, operation: str, parameters: dict) -> dict:
        return {
            "task_id": "fred-test-001",
            "provider": "fred",
            "operation": operation,
            "parameters": parameters,
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "acceptance": {"timeout_seconds": 30, "max_response_bytes": 1000000},
        }

    def test_catalog_schema_and_security_invariants(self) -> None:
        provider = self.catalog["providers"][0]
        operations = provider["operations"]
        ids = [row["operation_id"] for row in operations]
        self.assertEqual(provider["provider_id"], "fred")
        self.assertEqual(provider["ticket_prefix"], "[intel-fred]")
        self.assertEqual(provider["required_secret_environment_variable"], "FRED_API_KEY")
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), 25)
        self.assertEqual(set(ids), set(self.schema["properties"]["operation"]["enum"]))
        self.assertTrue(all(row["result_contract"]["read_only"] for row in operations))
        limits = provider["limits"]
        self.assertEqual(limits["requests_per_ticket_max"], 1)
        self.assertFalse(limits["automatic_pagination_allowed"])
        self.assertFalse(limits["bulk_v2_release_download_allowed"])
        self.assertFalse(limits["maps_shapefile_download_allowed"])
        self.assertFalse(limits["arbitrary_paths_allowed"])
        self.assertFalse(limits["write_operations_allowed"])
        self.assertFalse(limits["secret_values_exposed"])

    def test_request_is_fixed_json_and_bounded(self) -> None:
        path, query = fred.build_request(
            "series-observations",
            {
                "series_id": "GDP",
                "observation_start": "2020-01-01",
                "observation_end": "2024-12-31",
                "vintage_dates": ["2024-01-01", "2024-06-01"],
            },
        )
        self.assertEqual(path, "/fred/series/observations")
        self.assertEqual(query["file_type"], "json")
        self.assertEqual(query["limit"], "1000")
        self.assertEqual(query["offset"], "0")
        self.assertEqual(query["vintage_dates"], "2024-01-01,2024-06-01")
        self.assertNotIn("api_key", query)

    def test_rejects_reversed_date_range(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not be after"):
            fred.build_request(
                "series-observations",
                {"series_id": "GDP", "observation_start": "2025-01-01", "observation_end": "2024-01-01"},
            )

    def test_missing_secret_is_structured_failure_without_upstream(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            output_dir = root / "out"
            ticket_path.write_text(json.dumps(self._ticket("series", {"series_id": "GDP"})), encoding="utf-8")
            with patch.dict(os.environ, {}, clear=True), patch.object(fred.requests, "get") as request:
                code = fred.execute(ticket_path, output_dir)
            self.assertEqual(code, 1)
            request.assert_not_called()
            diagnostics = json.loads((output_dir / "diagnostics.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostics["status"], "INTEL_FRED_FAILED")
            self.assertIn("FRED_API_KEY is not configured", diagnostics["failure"]["message"])
            self.assertFalse(diagnostics["secret_values_exposed"])

    def test_success_uses_one_request_and_does_not_expose_key(self) -> None:
        key = "a" * 32
        payload = {"seriess": [{"id": "GDP", "title": "Gross Domestic Product"}]}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            output_dir = root / "out"
            ticket_path.write_text(json.dumps(self._ticket("series", {"series_id": "GDP"})), encoding="utf-8")
            with patch.dict(os.environ, {"FRED_API_KEY": key}, clear=True), patch.object(
                fred.requests, "get", return_value=FakeResponse(payload)
            ) as request:
                code = fred.execute(ticket_path, output_dir)
            self.assertEqual(code, 0)
            self.assertEqual(request.call_count, 1)
            kwargs = request.call_args.kwargs
            self.assertEqual(kwargs["params"]["api_key"], key)
            self.assertFalse(kwargs["allow_redirects"])
            diagnostics_text = (output_dir / "diagnostics.json").read_text(encoding="utf-8")
            snapshot_text = (output_dir / "snapshot.json").read_text(encoding="utf-8")
            manifest_text = (output_dir / "manifest.json").read_text(encoding="utf-8")
            self.assertNotIn(key, diagnostics_text + snapshot_text + manifest_text)
            diagnostics = json.loads(diagnostics_text)
            self.assertEqual(diagnostics["status"], "INTEL_FRED_COMPLETED")
            self.assertEqual(diagnostics["metadata"]["row_count"], 1)
            self.assertNotIn("api_key", diagnostics["metadata"]["query_parameter_names"])


if __name__ == "__main__":
    unittest.main()
