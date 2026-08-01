from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("aisstream_task", HERE / "aisstream_task.py")
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class AISstreamProviderTests(unittest.TestCase):
    def test_catalog_contract(self) -> None:
        catalog = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "aisstream")
        self.assertEqual(provider["required_secret_environment_variable"], "AISSTREAM_API_KEY")
        self.assertEqual(len(provider["operations"]), 4)
        self.assertFalse(provider["limits"]["worldwide_subscription_allowed"])
        self.assertFalse(provider["limits"]["background_streaming_allowed"])

    def test_build_subscription_redacts_key_from_safe_shape(self) -> None:
        subscription = module.build_subscription(
            "collect-messages",
            {
                "bounding_boxes": [[[25.8, 119.0], [26.2, 119.6]]],
                "mmsi": ["123456789"],
                "message_types": ["PositionReport"],
            },
            "secret-value",
        )
        self.assertEqual(subscription["APIKey"], "secret-value")
        safe = {key: value for key, value in subscription.items() if key != "APIKey"}
        self.assertNotIn("secret-value", json.dumps(safe))

    def test_worldwide_and_large_boxes_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            module.normalize_boxes({"bounding_boxes": [[[-90, -180], [90, 180]]]})

    def test_invalid_mmsi_and_message_type_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            module.normalize_mmsi({"mmsi": ["123"]})
        with self.assertRaises(ValueError):
            module.normalize_message_types({"message_types": ["NotARealType"]})

    def test_position_operation_forces_position_types(self) -> None:
        subscription = module.build_subscription(
            "collect-vessel-positions",
            {"bounding_boxes": [[[25.8, 119.0], [26.2, 119.6]]]},
            "x",
        )
        self.assertEqual(
            subscription["FilterMessageTypes"],
            ["PositionReport", "StandardClassBPositionReport", "ExtendedClassBPositionReport"],
        )


if __name__ == "__main__":
    unittest.main()
