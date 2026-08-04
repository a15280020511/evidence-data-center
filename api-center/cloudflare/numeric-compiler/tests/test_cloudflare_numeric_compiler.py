from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pyarrow as pa

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
API_CENTER = ROOT.parents[1]
if str(API_CENTER / "huggingface") not in sys.path:
    sys.path.insert(0, str(API_CENTER / "huggingface"))
SPEC = importlib.util.spec_from_file_location(
    "cloudflare_numeric_compiler", ROOT / "cloudflare_numeric_compiler.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CloudflareNumericCompilerTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["CLOUDFLARE_API_TOKEN"] = "test-token-not-real"
        os.environ["CLOUDFLARE_ACCOUNT_ID"] = "0123456789abcdef0123456789abcdef"

    def test_configuration_is_fixed_and_complete(self) -> None:
        receipt = MODULE.validate_configuration()
        self.assertEqual(receipt["profile_count"], 13)
        self.assertGreaterEqual(receipt["variable_count"], 100)
        self.assertFalse(receipt["arbitrary_prompt_allowed"])
        self.assertFalse(receipt["arbitrary_schema_allowed"])
        self.assertFalse(receipt["raw_text_persisted"])
        self.assertTrue(receipt["numeric_hf_payload_only"])
        self.assertFalse(receipt["direct_center_connection_allowed"])

    def test_all_response_schemas_are_closed(self) -> None:
        profiles = MODULE._profile_map()
        for profile in profiles.values():
            schema = MODULE.response_schema(profile)
            self.assertFalse(schema["additionalProperties"])
            self.assertIn("publication_date", schema["required"])

    def test_metric_result_converts_to_numeric_observation(self) -> None:
        profile = MODULE._profile_map()["cn-listed-company-financial-report"]
        ticket = {
            "profile_id": profile["id"],
            "url": "https://example.com/report",
            "acceptance": {"minimum_confidence": 0.7}
        }
        result = {
            "publication_date": "2026-04-30",
            "entity_key": "SH:600000",
            "geography_id": 310000,
            "records": [{
                "metric_code": "REVENUE",
                "period_start": "2025-01-01",
                "period_end": "2025-12-31",
                "value": 100.0,
                "lower_bound": 100.0,
                "upper_bound": 100.0,
                "unit_code": "CNY_100M",
                "confidence": 0.95
            }]
        }
        table_id, rows, provenance = MODULE._convert(ticket, profile, result)
        self.assertEqual(table_id, "observations")
        self.assertEqual(len(rows), 1)
        self.assertIsInstance(rows[0]["entity_id"], int)
        self.assertIsInstance(rows[0]["variable_id"], int)
        self.assertEqual(rows[0]["missing_flag"], 0)
        self.assertGreater(provenance["confidence"], 0.9)
        table = MODULE._table_from_rows(table_id, rows)
        for field in table.schema:
            self.assertTrue(pa.types.is_integer(field.type) or pa.types.is_floating(field.type))

    def test_event_result_converts_to_numeric_event(self) -> None:
        profile = MODULE._profile_map()["cn-corporate-events"]
        ticket = {
            "profile_id": profile["id"],
            "url": "https://example.com/event",
            "acceptance": {"minimum_confidence": 0.6}
        }
        result = {
            "publication_date": "2026-05-01",
            "entity_key": "SZ:000001",
            "geography_id": 440000,
            "events": [{
                "event_code": "DIVIDEND",
                "start_date": "2026-05-01",
                "end_date": "2026-05-01",
                "magnitude": 0.5,
                "direction_code": 1,
                "probability": 1.0,
                "status_code": 1,
                "confidence": 0.98
            }]
        }
        table_id, rows, _ = MODULE._convert(ticket, profile, result)
        self.assertEqual(table_id, "regime_events")
        self.assertEqual(len(rows), 1)
        self.assertIsInstance(rows[0]["event_type_id"], int)

    def test_link_result_converts_to_numeric_link(self) -> None:
        profile = MODULE._profile_map()["cn-ownership-business-links"]
        ticket = {
            "profile_id": profile["id"],
            "url": "https://example.com/link",
            "acceptance": {"minimum_confidence": 0.6}
        }
        result = {
            "publication_date": "2026-05-01",
            "links": [{
                "source_entity_key": "SH:600000",
                "target_entity_key": "USCC:91310000132201328T",
                "relation_code": "HOLDS_SHARES",
                "weight": 0.25,
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
                "confidence": 0.9
            }]
        }
        table_id, rows, _ = MODULE._convert(ticket, profile, result)
        self.assertEqual(table_id, "entity_links")
        self.assertNotEqual(rows[0]["source_entity_id"], rows[0]["target_entity_id"])

    def test_low_confidence_and_invalid_bounds_are_rejected(self) -> None:
        profile = MODULE._profile_map()["cn-business-operations"]
        ticket = {
            "profile_id": profile["id"],
            "url": "https://example.com/business",
            "acceptance": {"minimum_confidence": 0.8}
        }
        low = {
            "publication_date": "2026-01-01",
            "entity_key": "USCC:TEST-COMPANY",
            "geography_id": 350100,
            "records": [{
                "metric_code": "STORE_COUNT",
                "period_start": "2026-01-01",
                "period_end": "2026-01-01",
                "value": 5,
                "lower_bound": 5,
                "upper_bound": 5,
                "unit_code": "COUNT",
                "confidence": 0.5
            }]
        }
        with self.assertRaisesRegex(MODULE.NumericCompilerError, "no records"):
            MODULE._convert(ticket, profile, low)
        bad = json.loads(json.dumps(low))
        bad["records"][0]["confidence"] = 0.9
        bad["records"][0]["lower_bound"] = 6
        with self.assertRaisesRegex(MODULE.NumericCompilerError, "bounds"):
            MODULE._convert(ticket, profile, bad)

    def test_ticket_rejects_unknown_profile_and_private_target(self) -> None:
        records = [(2, 1, 6, "", ("93.184.216.34", 443))]
        ticket = {
            "task_id": "test-1",
            "profile_id": "cn-not-allowlisted",
            "url": "https://example.com/",
            "data_policy": {
                "classification": "public",
                "contains_personal_data": False,
                "investment_recommendation_requested": False
            },
            "acceptance": {
                "timeout_seconds": 60,
                "max_response_bytes": 1000000,
                "minimum_confidence": 0.8
            }
        }
        with patch.object(MODULE.socket, "getaddrinfo", return_value=records):
            with self.assertRaisesRegex(MODULE.NumericCompilerError, "not allowlisted"):
                MODULE._load_ticket(ticket)
        with self.assertRaises(MODULE.NumericCompilerError):
            MODULE.validate_public_https_url("https://127.0.0.1/private")

    def test_prepare_persists_ticket_but_not_page_content(self) -> None:
        records = [(2, 1, 6, "", ("93.184.216.34", 443))]
        ticket = {
            "task_id": "test-prepare",
            "profile_id": "cn-a-share-market-data",
            "url": "https://example.com/market",
            "data_policy": {
                "classification": "public",
                "contains_personal_data": False,
                "investment_recommendation_requested": False
            },
            "acceptance": {
                "timeout_seconds": 60,
                "max_response_bytes": 1000000,
                "minimum_confidence": 0.8
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            event_path = root / "event.json"
            event_path.write_text(json.dumps({"issue": {"body": json.dumps(ticket)}}), encoding="utf-8")
            with patch.object(MODULE.socket, "getaddrinfo", return_value=records):
                receipt = MODULE.prepare(event_path, root / "out")
            self.assertEqual(receipt["status"], "CLOUDFLARE_NUMERIC_TICKET_ACCEPTED")
            self.assertFalse(receipt["raw_text_persisted"])
            self.assertFalse((root / "out" / "raw-page.txt").exists())


if __name__ == "__main__":
    unittest.main()
