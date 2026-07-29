from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

API_CENTER = Path(__file__).resolve().parents[1]


def load_module():
    spec = importlib.util.spec_from_file_location("api_center_build_config_test", API_CENTER / "build_config.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


build_config = load_module()


class ApiCenterBuildConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.connectors = Path(directory.name)
        original = build_config.CONNECTORS_DIR
        build_config.CONNECTORS_DIR = self.connectors
        self.addCleanup(setattr, build_config, "CONNECTORS_DIR", original)

    def connector(self, **overrides):
        value = {
            "id": "weather-api",
            "enabled": True,
            "endpoint": "/data/weather",
            "method": "GET",
            "timeout": "3s",
            "input_query_strings": ["city"],
            "secret_header": {"name": "X-API-Key", "env": "WEATHER_API_KEY"},
            "backend": {
                "host": "https://api.example.com",
                "url_pattern": "/v1/weather",
                "method": "GET",
                "encoding": "json",
                "allow": ["temperature", "updated_at"],
            },
        }
        for key, item in overrides.items():
            if key == "backend":
                value["backend"] = {**value["backend"], **item}
            else:
                value[key] = item
        return value

    def write(self, filename: str, value) -> None:
        (self.connectors / filename).write_text(
            json.dumps(value, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def test_enabled_connector_gets_default_circuit_breaker(self) -> None:
        self.write("weather.connector.json", self.connector())
        config, rows, env_names = build_config.build()
        self.assertEqual(env_names, ["WEATHER_API_KEY"])
        self.assertEqual(len(config["endpoints"]), 1)
        extra = config["endpoints"][0]["backend"][0]["extra_config"]
        self.assertEqual(
            extra["qos/circuit-breaker"],
            {
                "interval": 60,
                "timeout": 30,
                "max_errors": 3,
                "name": "cb-weather-api",
                "log_status_change": True,
            },
        )
        self.assertTrue(rows[0]["default_circuit_breaker"])
        self.assertFalse(rows[0]["backend_rate_limit"])
        self.assertFalse(rows[0]["write_approved"])
        self.assertEqual(rows[0]["secret_injection"], "header")

    def test_rate_limit_is_allowlisted_and_rendered(self) -> None:
        connector = self.connector(
            backend={
                "resilience": {
                    "circuit_breaker": {"max_errors": 5, "timeout": 20},
                    "rate_limit": {"max_rate": 10, "every": "1s", "capacity": 10},
                }
            }
        )
        self.write("weather.connector.json", connector)
        config, rows, _ = build_config.build()
        extra = config["endpoints"][0]["backend"][0]["extra_config"]
        self.assertEqual(extra["qos/circuit-breaker"]["max_errors"], 5)
        self.assertEqual(extra["qos/circuit-breaker"]["timeout"], 20)
        self.assertEqual(
            extra["qos/ratelimit/proxy"],
            {"max_rate": 10.0, "every": "1s", "capacity": 10},
        )
        self.assertTrue(rows[0]["backend_rate_limit"])

    def test_template_contains_secret_reference_not_value(self) -> None:
        self.write("weather.connector.json", self.connector())
        with tempfile.TemporaryDirectory() as output:
            root = Path(output)
            template = root / "krakend.tmpl"
            validation = root / "krakend.validation.json"
            manifest = root / "connector-manifest.json"
            build_config.write_outputs(template, validation, manifest)
            template_text = template.read_text(encoding="utf-8")
            validation_text = validation.read_text(encoding="utf-8")
            manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertIn('{{ env "WEATHER_API_KEY" | quote }}', template_text)
            self.assertNotIn("VALIDATION_DUMMY_SECRET", template_text)
            self.assertIn("VALIDATION_DUMMY_SECRET", validation_text)
            self.assertEqual(manifest_data["version"], 4)
            self.assertFalse(manifest_data["connector_policy"]["put_patch_delete_allowed"])
            self.assertFalse(manifest_data["connector_policy"]["client_supplied_secret_parameters_allowed"])

    def test_secret_query_is_backend_only_and_rendered(self) -> None:
        connector = self.connector()
        connector.pop("secret_header")
        connector["secret_query"] = {"name": "key", "env": "AMAP_API_KEY"}
        self.write("amap.connector.json", connector)
        config, rows, env_names = build_config.build()
        self.assertEqual(env_names, ["AMAP_API_KEY"])
        endpoint = config["endpoints"][0]
        self.assertNotIn("key", endpoint["input_query_strings"])
        modifier = endpoint["backend"][0]["extra_config"]["modifier/martian"]["querystring.Modifier"]
        self.assertEqual(modifier["name"], "key")
        self.assertEqual(modifier["value"], "__API_CENTER_ENV_AMAP_API_KEY__")
        self.assertEqual(rows[0]["secret_injection"], "query")

    def test_client_cannot_forward_secret_query_parameter(self) -> None:
        connector = self.connector(input_query_strings=["city", "key"])
        connector.pop("secret_header")
        connector["secret_query"] = {"name": "key", "env": "AMAP_API_KEY"}
        self.write("amap.connector.json", connector)
        with self.assertRaisesRegex(ValueError, "exposes its secret query parameter"):
            build_config.build()

    def test_client_cannot_forward_secret_header(self) -> None:
        connector = self.connector(input_headers=["X-API-Key"])
        self.write("weather.connector.json", connector)
        with self.assertRaisesRegex(ValueError, "exposes its secret header"):
            build_config.build()

    def test_arbitrary_extra_config_is_rejected(self) -> None:
        connector = self.connector(backend={"extra_config": {"modifier/lua-backend": {"allow_open_libs": True}}})
        self.write("weather.connector.json", connector)
        with self.assertRaisesRegex(ValueError, "Additional properties"):
            build_config.build()

    def test_literal_secret_is_rejected(self) -> None:
        connector = self.connector()
        connector.pop("secret_header")
        connector["backend"]["url_pattern"] = "/v1/weather?" + "api_" + "key=" + "actual-secret-value-123456"
        self.write("weather.connector.json", connector)
        with self.assertRaisesRegex(ValueError, "literal secret-like value"):
            build_config.build()

    def test_enabled_remote_plain_http_is_rejected(self) -> None:
        self.write(
            "weather.connector.json",
            self.connector(backend={"host": "http://api.example.com"}),
        )
        with self.assertRaisesRegex(ValueError, "must use HTTPS"):
            build_config.build()

    def test_loopback_http_is_allowed_for_integration_tests(self) -> None:
        self.write(
            "weather.connector.json",
            self.connector(backend={"host": "http://127.0.0.1:19090"}),
        )
        config, _, _ = build_config.build()
        self.assertEqual(config["endpoints"][0]["backend"][0]["host"], ["http://127.0.0.1:19090"])

    def test_private_and_metadata_targets_are_rejected(self) -> None:
        for index, host in enumerate(("https://10.0.0.2", "https://169.254.169.254", "https://metadata.google.internal")):
            self.connectors.mkdir(exist_ok=True)
            self.write(f"blocked-{index}.connector.json", self.connector(id=f"blocked-{index}", backend={"host": host}))
            with self.assertRaisesRegex(ValueError, "blocked"):
                build_config.build()
            for path in self.connectors.glob("*.connector.json"):
                path.unlink()

    def test_dangerous_forwarded_headers_are_rejected(self) -> None:
        for header in ("Authorization", "Cookie", "Host", "X-Forwarded-For"):
            self.write("weather.connector.json", self.connector(input_headers=[header]))
            with self.assertRaisesRegex(ValueError, "forbidden request header"):
                build_config.build()
            (self.connectors / "weather.connector.json").unlink()

    def test_post_requires_explicit_write_approval(self) -> None:
        connector = self.connector(method="POST", backend={"method": "POST"})
        self.write("weather.connector.json", connector)
        with self.assertRaisesRegex(ValueError, "requires write_approved=true"):
            build_config.build()
        connector["write_approved"] = True
        self.write("weather.connector.json", connector)
        config, rows, _ = build_config.build()
        self.assertEqual(config["endpoints"][0]["method"], "POST")
        self.assertTrue(rows[0]["write_approved"])

    def test_put_patch_delete_are_rejected_by_schema(self) -> None:
        for method in ("PUT", "PATCH", "DELETE"):
            self.write("weather.connector.json", self.connector(method=method, backend={"method": method}))
            with self.assertRaisesRegex(ValueError, "is not one of"):
                build_config.build()
            (self.connectors / "weather.connector.json").unlink()

    def test_endpoint_and_backend_methods_must_match(self) -> None:
        self.write("weather.connector.json", self.connector(method="GET", backend={"method": "POST"}))
        with self.assertRaisesRegex(ValueError, "same endpoint and backend method"):
            build_config.build()

    def test_duplicate_enabled_route_is_rejected(self) -> None:
        self.write("one.connector.json", self.connector(id="weather-one"))
        self.write("two.connector.json", self.connector(id="weather-two"))
        with self.assertRaisesRegex(ValueError, "duplicate enabled route"):
            build_config.build()

    def test_disabled_connector_does_not_create_runtime_endpoint(self) -> None:
        self.write("weather.connector.json", self.connector(enabled=False))
        config, rows, env_names = build_config.build()
        self.assertEqual(config["endpoints"], [])
        self.assertEqual(env_names, [])
        self.assertFalse(rows[0]["enabled"])

    def test_output_is_deterministic(self) -> None:
        self.write("weather.connector.json", self.connector())
        first = build_config.build()
        second = build_config.build()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
