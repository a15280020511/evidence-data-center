from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("east_asia_econ_task", ROOT / "east_asia_econ_task.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def ticket(operation: str, parameters: dict) -> dict:
    return {
        "task_id": "east-asia-econ-test-001",
        "provider": "east-asia-econ",
        "operation": operation,
        "objective": "test",
        "parameters": parameters,
        "data_policy": {"classification": "public", "contains_personal_data": False},
        "acceptance": {"timeout_seconds": 30, "max_response_bytes": 1000000},
    }


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.content = json.dumps(payload).encode("utf-8")
        self.status_code = status_code
        self.headers = {"Content-Type": "application/json"}
        self.ok = 200 <= status_code < 300

    def json(self) -> dict:
        return self._payload


class EastAsiaEconTaskTests(unittest.TestCase):
    def test_catalog_has_fixed_six_operation_surface(self) -> None:
        catalog = module.provider_catalog()
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "east-asia-econ")
        self.assertEqual(provider["required_secret_environment_variable"], "EAST_ASIA_ECON_API_KEY")
        self.assertEqual(
            {row["operation_id"] for row in provider["operations"]},
            {"catalog-capabilities", "search-series", "series-info", "database-stats", "series-data", "usage"},
        )
        search = next(row for row in provider["operations"] if row["operation_id"] == "search-series")
        self.assertEqual(
            search["parameter_schema"]["properties"]["country"]["enum"],
            ["cn", "jp", "kr", "tw", "region"],
        )
        self.assertEqual(provider["limits"]["fixed_api_host"], "data-api.eastasiaecon.com")
        self.assertFalse(provider["limits"]["arbitrary_urls_allowed"])
        self.assertFalse(provider["limits"]["arbitrary_headers_allowed"])
        self.assertFalse(provider["limits"]["write_operations_allowed"])

    def test_rejects_unknown_parameter_and_bad_date_order(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-allowlisted"):
            module.validate_ticket(ticket("search-series", {"q": "CPI", "url": "https://example.com"}))
        with self.assertRaisesRegex(ValueError, "start must not be after"):
            module.validate_ticket(ticket("series-data", {"series_name": "China, CPI", "start": "2025-01-01", "end": "2024-01-01"}))

    def test_catalog_execution_needs_no_secret_or_upstream(self) -> None:
        value = ticket("catalog-capabilities", {})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            ticket_path.write_text(json.dumps(value), encoding="utf-8")
            with mock.patch.dict("os.environ", {}, clear=True), mock.patch.object(module.requests, "get") as request:
                self.assertEqual(module.execute(ticket_path, root), 0)
            request.assert_not_called()
            diagnostics = json.loads((root / "diagnostics.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostics["status"], "API_EAST_ASIA_ECON_COMPLETED")
            self.assertFalse(diagnostics["metadata"]["upstream_called"])
            self.assertIsNone(diagnostics["failure"])

    def test_public_search_uses_fixed_host_without_api_key(self) -> None:
        response = FakeResponse({"count": 1, "results": [{"name": "China, CPI", "country": "cn", "frequencies": ["m"]}]})
        with mock.patch.dict("os.environ", {}, clear=True), mock.patch.object(module.requests, "get", return_value=response) as request:
            payload, metadata = module.request_json("/v3/search", {"q": "CPI", "country": "cn", "limit": 1}, authenticated=False, timeout=30, max_bytes=1000000)
        args, kwargs = request.call_args
        self.assertEqual(args[0], "https://data-api.eastasiaecon.com/v3/search")
        self.assertNotIn("X-API-Key", kwargs["headers"])
        self.assertFalse(kwargs["allow_redirects"])
        self.assertEqual(payload["count"], 1)
        self.assertEqual(metadata["authentication"], "none")

    def test_series_data_requires_independent_key(self) -> None:
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "EAST_ASIA_ECON_API_KEY"):
                module.request_json("/v3/series/China%2C%20CPI", {"freq": "m"}, authenticated=True, timeout=30, max_bytes=1000000)

    def test_authenticated_request_injects_header_without_recording_value(self) -> None:
        secret = "eae_test_secret_123"
        response = FakeResponse({"series_name": "China, CPI", "count": 1, "data": [{"Date": "2025-01-01", "value": 1.2}]})
        with mock.patch.dict("os.environ", {"EAST_ASIA_ECON_API_KEY": secret}, clear=True), mock.patch.object(module.requests, "get", return_value=response) as request:
            payload, metadata = module.request_json("/v3/series/China%2C%20CPI", {"freq": "m"}, authenticated=True, timeout=30, max_bytes=1000000)
        headers = request.call_args.kwargs["headers"]
        self.assertEqual(headers["X-API-Key"], secret)
        serialized = json.dumps({"payload": payload, "metadata": metadata})
        self.assertNotIn(secret, serialized)
        self.assertEqual(metadata["authentication"], "X-API-Key header; value not recorded")


if __name__ == "__main__":
    unittest.main()
