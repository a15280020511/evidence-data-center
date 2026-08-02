from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("hexdb_aviation_task", HERE / "hexdb_aviation_task.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class FakeResponse:
    def __init__(self, status_code: int, payload: object) -> None:
        self.status_code = status_code
        self._payload = payload
        self.content = json.dumps(payload).encode("utf-8")
        self.ok = 200 <= status_code < 300

    def json(self) -> object:
        return self._payload


class HexDbAviationTests(unittest.TestCase):
    def test_fixed_paths(self) -> None:
        self.assertEqual(module.build_request("aircraft-by-icao24", {"icao24": "4010ee"}), "/api/v1/aircraft/4010EE")
        self.assertEqual(module.build_request("route-by-icao-callsign", {"callsign": "ein17a"}), "/api/v1/route/icao/EIN17A")
        self.assertEqual(module.build_request("airport-by-iata", {"airport": "foc"}), "/api/v1/airport/iata/FOC")

    def test_invalid_identifier_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            module.build_request("aircraft-by-icao24", {"icao24": "../bad"})
        with self.assertRaises(ValueError):
            module.build_request("airport-by-icao", {"airport": "ZSFZ?"})

    def _ticket(self, operation: str, parameters: dict) -> dict:
        return {
            "task_id": "hexdb-test-001",
            "provider": "hexdb-aviation",
            "operation": operation,
            "objective": "test",
            "parameters": parameters,
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "acceptance": {"timeout_seconds": 10, "max_response_bytes": 100000},
        }

    @patch.object(module.requests, "get")
    def test_aircraft_success_is_persisted(self, get) -> None:
        get.return_value = FakeResponse(200, {"ICAOTypeCode": "A319", "Manufacturer": "Airbus", "ModeS": "4010EE", "Registration": "G-EZBZ", "Type": "A319 111"})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket = root / "ticket.json"
            out = root / "out"
            ticket.write_text(json.dumps(self._ticket("aircraft-by-icao24", {"icao24": "4010ee"})), encoding="utf-8")
            self.assertEqual(module.execute(ticket, out), 0)
            payload = json.loads((out / "response.json").read_text(encoding="utf-8"))
            self.assertTrue(payload["found"])
            self.assertEqual(payload["record"]["Manufacturer"], "Airbus")
            get.assert_called_once()

    @patch.object(module.requests, "get")
    def test_not_found_is_structured_success(self, get) -> None:
        get.return_value = FakeResponse(404, {"status": "404", "error": "Aircraft not found."})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket = root / "ticket.json"
            out = root / "out"
            ticket.write_text(json.dumps(self._ticket("aircraft-by-icao24", {"icao24": "000000"})), encoding="utf-8")
            self.assertEqual(module.execute(ticket, out), 0)
            payload = json.loads((out / "response.json").read_text(encoding="utf-8"))
            self.assertFalse(payload["found"])

    def test_catalog_contract(self) -> None:
        catalog = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "hexdb-aviation")
        self.assertEqual(provider["ticket_prefix"], "[intel-hexdb]")
        self.assertEqual(len(provider["operations"]), 6)
        self.assertEqual(provider["limits"]["requests_per_ticket_max"], 1)
        self.assertFalse(provider["limits"]["bulk_lookup_allowed"])
        self.assertFalse(provider["limits"]["write_operations_allowed"])


if __name__ == "__main__":
    unittest.main()
