from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


api_ticket = load_module("api_ticket", ROOT / "api_ticket.py")


class ApiTicketTests(unittest.TestCase):
    def packet(self) -> dict:
        return {
            "task_id": "api-ticket-0001",
            "objective": "collect public geocoding data",
            "data_policy": {
                "classification": "public",
                "contains_personal_data": False,
            },
            "requests": [
                {
                    "request_id": "geo-1",
                    "connector_id": "amap-geocode",
                    "parameters": {"address": "public place", "city": "public city"},
                }
            ],
            "acceptance": {
                "require_all": True,
                "minimum_successful_requests": 1,
            },
        }

    def test_builds_allowlisted_plan(self) -> None:
        packet = self.packet()
        errors = list(api_ticket.VALIDATOR.iter_errors(packet))
        self.assertEqual(errors, [])
        plan = api_ticket._validate_and_plan(packet, ROOT)
        self.assertEqual(plan["requests"][0]["endpoint"], "/data/amap/geocode")
        self.assertEqual(plan["required_secret_environment_variables"], ["AMAP_API_KEY"])
        self.assertIn("response_contract", plan["requests"][0])

    def test_accepts_integer_number_and_boolean_parameters(self) -> None:
        packet = self.packet()
        packet["requests"][0] = {
            "request_id": "amap-place-1",
            "connector_id": "amap-place-text",
            "parameters": {
                "keywords": "商场",
                "region": "福州市",
                "page_size": 20,
                "city_limit": True,
            },
        }
        errors = list(api_ticket.VALIDATOR.iter_errors(packet))
        self.assertEqual(errors, [])
        plan = api_ticket._validate_and_plan(packet, ROOT)
        self.assertEqual(plan["requests"][0]["parameters"]["page_size"], 20)
        self.assertIs(plan["requests"][0]["parameters"]["city_limit"], True)
        self.assertEqual(plan["required_secret_environment_variables"], ["AMAP_API_KEY"])

    def test_rejects_unknown_parameter(self) -> None:
        packet = self.packet()
        packet["requests"][0]["parameters"]["key"] = "client-secret"
        with self.assertRaisesRegex(ValueError, "backend-only secret parameter"):
            api_ticket._validate_and_plan(packet, ROOT)

    def test_rejects_unknown_connector(self) -> None:
        packet = self.packet()
        for connector_id in ("example-api", "baidu-place-region", "not-installed"):
            packet["requests"][0]["connector_id"] = connector_id
            with self.assertRaisesRegex(ValueError, "not in the connector inventory"):
                api_ticket._validate_and_plan(packet, ROOT)

    def test_requires_public_non_personal_data(self) -> None:
        packet = self.packet()
        packet["data_policy"]["contains_personal_data"] = True
        errors = list(api_ticket.VALIDATOR.iter_errors(packet))
        self.assertTrue(errors)

    def test_rejected_ticket_body_is_not_copied_to_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            event = {
                "issue": {
                    "number": 7,
                    "title": "[api] rejected personal data",
                    "body": json.dumps({
                        **self.packet(),
                        "data_policy": {
                            "classification": "public",
                            "contains_personal_data": True,
                        },
                    }),
                },
                "sender": {"login": "owner"},
            }
            event_path = root / "event.json"
            event_path.write_text(json.dumps(event), encoding="utf-8")
            args = type("Args", (), {
                "event_path": str(event_path),
                "output_dir": str(root / "out"),
            })()
            with mock.patch.dict(
                api_ticket.os.environ,
                {"REPOSITORY_OWNER": "owner", "GITHUB_TOKEN": ""},
                clear=False,
            ):
                rc = api_ticket.prepare(args)
            self.assertEqual(rc, 2)
            self.assertFalse((root / "out/ticket.json").exists())
            self.assertTrue((root / "out/ticket-status.json").is_file())


if __name__ == "__main__":
    unittest.main()
