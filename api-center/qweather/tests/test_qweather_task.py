from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("qweather_task", ROOT / "qweather_task.py")
assert SPEC and SPEC.loader
qw = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qw)


def ticket(operation: str, parameters: dict) -> dict:
    return {
        "task_id": "qweather-test-001",
        "provider": "qweather",
        "operation": operation,
        "objective": "validate bounded QWeather access",
        "parameters": parameters,
        "data_policy": {"classification": "public", "contains_personal_data": False},
        "acceptance": {"timeout_seconds": 20, "max_response_bytes": 200000, "max_rows": 100},
    }


class QWeatherTaskTests(unittest.TestCase):
    def test_catalog_has_fixed_host_and_eighteen_operations(self) -> None:
        catalog = json.loads((ROOT / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "qweather")
        self.assertEqual(provider["required_secret_environment_variable"], "QWEATHER_API_KEY")
        self.assertEqual(provider["limits"]["fixed_api_host"], "ka6r72kcc3.re.qweatherapi.com")
        self.assertEqual(len(provider["operations"]), 18)
        self.assertFalse(provider["limits"]["arbitrary_urls_allowed"])
        self.assertFalse(provider["limits"]["arbitrary_hosts_allowed"])
        self.assertFalse(provider["limits"]["redirects_allowed"])
        self.assertFalse(provider["limits"]["write_operations_allowed"])

    def test_weather_now_request_is_fixed(self) -> None:
        url, params, metadata = qw.build_request(
            "weather-now", {"location": "101230101", "lang": "zh", "unit": "m"}
        )
        self.assertEqual(url, "https://ka6r72kcc3.re.qweatherapi.com/v7/weather/now")
        self.assertEqual(params, {"location": "101230101", "lang": "zh", "unit": "m"})
        self.assertEqual(metadata["request_origin"], "ka6r72kcc3.re.qweatherapi.com")
        self.assertFalse(metadata["redirects_allowed"])

    def test_air_quality_path_rounds_coordinates(self) -> None:
        url, params, _ = qw.build_request(
            "air-quality-current", {"latitude": 26.0745, "longitude": 119.2965, "lang": "zh"}
        )
        self.assertEqual(url, "https://ka6r72kcc3.re.qweatherapi.com/airquality/v1/current/26.07/119.30")
        self.assertEqual(params, {"lang": "zh"})

    def test_rejects_non_allowlisted_parameters(self) -> None:
        with self.assertRaisesRegex(ValueError, "Additional properties"):
            qw.validate_ticket(ticket("weather-now", {"location": "101230101", "url": "https://evil.invalid"}))

    def test_poa_requires_tilt_and_azimuth(self) -> None:
        with self.assertRaisesRegex(ValueError, "tilt"):
            qw.validate_ticket(ticket(
                "solar-radiation-forecast",
                {"latitude": 26.08, "longitude": 119.30, "extra": "poa"},
            ))

    def test_missing_key_is_structured_and_secretless(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            path = out / "ticket.json"
            path.write_text(json.dumps(ticket("weather-now", {"location": "101230101"})), encoding="utf-8")
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(qw.execute(path, out), 1)
            diag = json.loads((out / "qweather-diagnostics.json").read_text(encoding="utf-8"))
            self.assertEqual(diag["error"]["code"], "QWEATHER_API_KEY_MISSING")
            self.assertFalse(diag["security"]["secret_values_exposed"])
            self.assertFalse(diag["security"]["api_key_header_recorded"])

    def test_success_uses_header_without_recording_key(self) -> None:
        response = Mock()
        response.status_code = 200
        response.is_redirect = False
        response.headers = {"Content-Type": "application/json", "Content-Encoding": "gzip"}
        response.raw.read.return_value = b'{"code":"200","now":{"temp":"30"}}'
        with patch.dict(os.environ, {"QWEATHER_API_KEY": "visible-test-key"}, clear=True):
            with patch.object(qw.requests, "get", return_value=response) as get:
                payload, metadata = qw.query_qweather(
                    "weather-now", {"location": "101230101"},
                    timeout=20, max_bytes=200000, max_rows=100,
                )
        self.assertEqual(payload["code"], "200")
        self.assertEqual(get.call_args.kwargs["headers"]["X-QW-Api-Key"], "visible-test-key")
        self.assertNotIn("visible-test-key", json.dumps(metadata))
        self.assertFalse(get.call_args.kwargs["allow_redirects"])


if __name__ == "__main__":
    unittest.main()
