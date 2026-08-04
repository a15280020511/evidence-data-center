from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("noaa_cdo_task", HERE / "noaa_cdo_task.py")
assert SPEC and SPEC.loader
noaa_cdo_task = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(noaa_cdo_task)


class FakeResponse:
    ok = True
    status_code = 200
    content = b'{"results":[{"id":"GHCND"}],"metadata":{"resultset":{"count":1}}}'
    headers = {"Content-Type": "application/json"}

    def json(self):
        return json.loads(self.content)


class NoaaCdoProviderTests(unittest.TestCase):
    def test_catalog_has_five_bounded_readonly_operations(self) -> None:
        provider = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))["providers"][0]
        operations = provider["operations"]
        self.assertEqual(provider["provider_id"], "noaa-cdo")
        self.assertEqual(provider["ticket_prefix"], "[intel-noaa-cdo]")
        self.assertEqual(provider["required_secret_environment_variable"], "NOAA_CDO_TOKEN")
        self.assertEqual(len(operations), 5)
        self.assertTrue(all(row["result_contract"]["read_only"] for row in operations))
        self.assertFalse(provider["limits"]["write_operations_allowed"])
        self.assertFalse(provider["limits"]["automatic_pagination_allowed"])
        self.assertEqual(provider["limits"]["rows_per_request_max"], 1000)

    def test_station_extent_must_stay_in_china(self) -> None:
        path, query = noaa_cdo_task.build_request(
            "stations",
            {"datasetid": "GHCND", "extent": "25.8,118.9,26.3,119.7"},
        )
        self.assertEqual(path, "/cdo-web/api/v2/stations")
        self.assertIn(("extent", "25.8,118.9,26.3,119.7"), query)
        with self.assertRaisesRegex(ValueError, "China geographic envelope"):
            noaa_cdo_task.build_request(
                "stations",
                {"datasetid": "GHCND", "extent": "40,-75,41,-74"},
            )

    def test_data_range_is_bounded_and_station_prefix_matches(self) -> None:
        path, query = noaa_cdo_task.build_request(
            "data",
            {
                "datasetid": "GHCND",
                "stationid": "GHCND:CHM00058847",
                "startdate": "2024-01-01",
                "enddate": "2024-12-31",
                "datatypeid": ["TAVG", "TMAX", "TMIN", "PRCP"],
                "units": "metric",
            },
        )
        self.assertEqual(path, "/cdo-web/api/v2/data")
        self.assertEqual(sum(1 for name, _ in query if name == "datatypeid"), 4)
        with self.assertRaisesRegex(ValueError, "max 1 year"):
            noaa_cdo_task.build_request(
                "data",
                {
                    "datasetid": "GHCND",
                    "stationid": "GHCND:CHM00058847",
                    "startdate": "2020-01-01",
                    "enddate": "2022-01-01",
                },
            )
        with self.assertRaisesRegex(ValueError, "prefix must match"):
            noaa_cdo_task.build_request(
                "data",
                {
                    "datasetid": "GHCND",
                    "stationid": "GSOM:CHM00058847",
                    "startdate": "2024-01-01",
                    "enddate": "2024-01-02",
                },
            )

    def test_token_is_backend_header_only_and_redacted(self) -> None:
        ticket = {
            "task_id": "noaa-cdo-test-001",
            "provider": "noaa-cdo",
            "operation": "datasets",
            "parameters": {"limit": 1},
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "acceptance": {"timeout_seconds": 10, "max_response_bytes": 1000000},
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            output_dir = root / "out"
            ticket_path.write_text(json.dumps(ticket), encoding="utf-8")
            token = "A" * 32
            with mock.patch.dict(os.environ, {"NOAA_CDO_TOKEN": token}, clear=False), mock.patch.object(
                noaa_cdo_task.requests, "get", return_value=FakeResponse()
            ) as get:
                code = noaa_cdo_task.execute(ticket_path, output_dir)
            self.assertEqual(code, 0)
            headers = get.call_args.kwargs["headers"]
            self.assertEqual(headers["token"], token)
            artifact_text = "\n".join(
                path.read_text(encoding="utf-8", errors="replace")
                for path in output_dir.glob("*.json")
            )
            self.assertNotIn(token, artifact_text)


if __name__ == "__main__":
    unittest.main()
