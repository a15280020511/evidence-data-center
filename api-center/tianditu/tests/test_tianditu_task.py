from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("tianditu_task", ROOT / "tianditu_task.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.status = 200
        self._raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.headers = {"Content-Type": "application/json", "Server": "Tianditu"}

    def read(self, _size: int) -> bytes:
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class TiandituTaskTests(unittest.TestCase):
    def ticket(self, operation: str, parameters: dict) -> dict:
        return {
            "task_id": "tianditu-test-001",
            "provider": "tianditu",
            "operation": operation,
            "objective": "test bounded read-only Tianditu operation",
            "parameters": parameters,
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "acceptance": {"timeout_seconds": 30, "max_response_bytes": 1000000},
        }

    def test_catalog_contract(self) -> None:
        catalog = json.loads((ROOT / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "tianditu")
        self.assertEqual(provider["required_secret_environment_variable"], "TIANDITU_API_KEY")
        self.assertFalse(catalog["secret_values_exposed"])
        self.assertEqual(len(provider["operations"]), 8)
        self.assertFalse(provider["limits"]["arbitrary_urls_allowed"])
        self.assertFalse(provider["limits"]["tile_bulk_download_allowed"])
        self.assertTrue(provider["limits"]["direct_phone_fields_redacted"])

    def test_build_normal_and_nearby_post_str(self) -> None:
        normal = module.build_post_str(
            "normal-search",
            {
                "keyword": "北京大学",
                "map_bound": [116.0, 39.8, 116.7, 40.0],
                "level": 12,
                "place_only": True,
                "count": 10,
            },
        )
        self.assertEqual(normal["queryType"], 7)
        self.assertEqual(normal["show"], 1)
        nearby = module.build_post_str(
            "nearby-search",
            {
                "keyword": "公园",
                "center": [116.48016, 39.93136],
                "radius": 5000,
                "level": 12,
            },
        )
        self.assertEqual(nearby["queryType"], 3)
        self.assertEqual(nearby["queryRadius"], 5000)
        self.assertEqual(nearby["pointLonlat"], "116.48016,39.93136")

    def test_rejects_unbounded_or_invalid_geometry(self) -> None:
        with self.assertRaisesRegex(ValueError, "radius"):
            module.build_post_str(
                "nearby-search",
                {"keyword": "医院", "center": [116.4, 39.9], "radius": 10001, "level": 12},
            )
        with self.assertRaisesRegex(ValueError, "closed"):
            module.build_post_str(
                "polygon-search",
                {
                    "keyword": "学校",
                    "polygon": [[116, 39], [117, 39], [117, 40], [116, 40]],
                },
            )
        with self.assertRaisesRegex(ValueError, r"start \+ count"):
            module.build_post_str(
                "administrative-search",
                {"keyword": "商厦", "specify": "156110108", "start": 300, "count": 300},
            )
        with self.assertRaisesRegex(ValueError, "minimums"):
            module.build_post_str(
                "viewport-search",
                {"keyword": "医院", "map_bound": [117, 40, 116, 39], "level": 12},
            )

    def test_prepare_accepts_valid_ticket(self) -> None:
        ticket = self.ticket(
            "administrative-search",
            {"keyword": "商厦", "specify": "156110108", "count": 10},
        )
        event = {"issue": {"title": "[api-tianditu] test", "body": json.dumps(ticket, ensure_ascii=False)}}
        with tempfile.TemporaryDirectory() as tmp:
            event_path = Path(tmp) / "event.json"
            out = Path(tmp) / "out"
            event_path.write_text(json.dumps(event, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(module.prepare(event_path, out), 0)
            status = json.loads((out / "ticket-status.json").read_text(encoding="utf-8"))
            self.assertTrue(status["accepted"])
            self.assertFalse(status["secret_values_exposed"])

    def test_execute_missing_secret_is_structured_and_redacted(self) -> None:
        ticket = self.ticket(
            "statistics-search",
            {"keyword": "学校", "specify": "156110108"},
        )
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {}, clear=True):
            ticket_path = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket_path.write_text(json.dumps(ticket, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(module.execute(ticket_path, out), 1)
            result = json.loads((out / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "API_TIANDITU_FAILED")
            self.assertIn("TIANDITU_API_KEY", result["failure"]["message"])
            serialized = json.dumps(result, ensure_ascii=False)
            self.assertNotIn("secret-value", serialized)
            self.assertFalse(result["secret_values_exposed"])

    def test_successful_call_redacts_phone_and_hides_token(self) -> None:
        payload = {
            "count": "1",
            "pois": [{"name": "测试公园", "phone": "010-12345678", "lonlat": "116.4,39.9"}],
            "status": {"infocode": 1000, "cndesc": "服务正常"},
        }
        ticket = self.ticket(
            "nearby-search",
            {"keyword": "公园", "center": [116.4, 39.9], "radius": 1000, "level": 12},
        )
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(
            os.environ, {"TIANDITU_API_KEY": "secret-value"}, clear=True
        ), mock.patch.object(module.urllib.request, "urlopen", return_value=FakeResponse(payload)) as mocked:
            ticket_path = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket_path.write_text(json.dumps(ticket, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(module.execute(ticket_path, out), 0)
            result = json.loads((out / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "API_TIANDITU_COMPLETED")
            self.assertEqual(result["data"]["pois"][0]["phone"], "[REDACTED_PUBLIC_PHONE]")
            self.assertEqual(result["metadata"]["business_status"], "1000")
            serialized = json.dumps(result, ensure_ascii=False)
            self.assertNotIn("secret-value", serialized)
            request_url = mocked.call_args.args[0].full_url
            self.assertIn("tk=secret-value", request_url)
            self.assertNotIn("secret-value", json.dumps(result["metadata"]))

    def test_business_failure_rejects_result(self) -> None:
        payload = {"status": {"infocode": 2001, "cndesc": "请求参数错误"}}
        with mock.patch.dict(os.environ, {"TIANDITU_API_KEY": "secret-value"}, clear=True), mock.patch.object(
            module.urllib.request, "urlopen", return_value=FakeResponse(payload)
        ):
            with self.assertRaisesRegex(module.TiandituRequestError, "business status 2001") as raised:
                module.call_tianditu(
                    "administrative-search",
                    {"keyword": "学校", "specify": "156110108"},
                    30,
                    1000000,
                )
            self.assertEqual(raised.exception.code, "TIANDITU_BUSINESS_ERROR")

    def test_waf_failure_records_real_upstream_attempt_and_curl_retry(self) -> None:
        ticket = self.ticket(
            "administrative-search",
            {"keyword": "学校", "specify": "福州市", "count": 1},
        )
        waf = module.TiandituRequestError(
            "TIANDITU_WAF_BLOCKED",
            "Tianditu CloudWAF blocked both bounded direct transports",
            {
                "upstream_called": True,
                "http_status": 418,
                "waf_blocked": True,
                "transport": "curl-http1.1",
                "transport_attempts": ["python-urllib", "curl-http1.1"],
            },
        )
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(
            os.environ, {"TIANDITU_API_KEY": "secret-value"}, clear=True
        ), mock.patch.object(module, "call_tianditu", side_effect=waf):
            ticket_path = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket_path.write_text(json.dumps(ticket, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(module.execute(ticket_path, out), 1)
            result = json.loads((out / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(result["failure"]["code"], "TIANDITU_WAF_BLOCKED")
            self.assertTrue(result["metadata"]["upstream_called"])
            self.assertEqual(result["metadata"]["http_status"], 418)
            self.assertEqual(
                result["metadata"]["transport_attempts"],
                ["python-urllib", "curl-http1.1"],
            )

    def test_browser_compatible_headers_are_used(self) -> None:
        payload = {"count": "0", "status": {"infocode": 1000, "cndesc": "服务正常"}}
        with mock.patch.dict(os.environ, {"TIANDITU_API_KEY": "secret-value"}, clear=True), mock.patch.object(
            module.urllib.request, "urlopen", return_value=FakeResponse(payload)
        ) as mocked:
            module.call_tianditu(
                "administrative-search",
                {"keyword": "学校", "specify": "福州市", "count": 1},
                30,
                1000000,
            )
            request = mocked.call_args.args[0]
            self.assertIn("Mozilla/5.0", request.headers["User-agent"])
            self.assertEqual(request.headers["Referer"], "https://lbs.tianditu.gov.cn/")
            self.assertNotIn("+", request.full_url.split("postStr=", 1)[1].split("&type=", 1)[0])


if __name__ == "__main__":
    unittest.main()
