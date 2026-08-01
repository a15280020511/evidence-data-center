from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "mediastack_task",
    ROOT / "mediastack_task.py",
)
assert SPEC and SPEC.loader
task = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(task)


class FakeRaw:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def read(self, size: int, decode_content: bool = True) -> bytes:
        return self.payload[:size]


class FakeResponse:
    def __init__(
        self,
        payload: dict,
        status_code: int = 200,
        content_type: str = "application/json",
    ) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.raw = FakeRaw(raw)
        self.status_code = status_code
        self.headers = {"Content-Type": content_type}
        self.is_redirect = False


class MediastackTests(unittest.TestCase):
    def ticket(self, operation="catalog-capabilities", parameters=None):
        return {
            "task_id": "mediastack-test-001",
            "provider": "mediastack",
            "operation": operation,
            "objective": "test bounded Mediastack news intelligence",
            "parameters": parameters or {},
            "data_policy": {
                "classification": "public",
                "contains_personal_data": False,
                "contains_confidential_data": False,
            },
            "acceptance": {
                "timeout_seconds": 30,
                "max_response_bytes": 1_000_000,
                "max_rows": 100,
            },
        }

    def test_catalog_is_fixed_and_read_only(self):
        catalog = json.loads(
            (ROOT / "provider-catalog.json").read_text(encoding="utf-8")
        )
        provider = catalog["providers"][0]
        ids = {row["operation_id"] for row in provider["operations"]}
        self.assertEqual(provider["provider_id"], "mediastack")
        self.assertEqual(
            provider["required_secret_environment_variable"],
            "MEDIASTACK_API_KEY",
        )
        self.assertEqual(
            ids,
            {
                "catalog-capabilities",
                "latest-news",
                "search-news",
                "historical-news",
                "list-sources",
            },
        )
        self.assertEqual(provider["limits"]["fixed_api_host"], "api.mediastack.com")
        self.assertFalse(provider["limits"]["automatic_pagination_allowed"])
        self.assertFalse(provider["limits"]["article_body_fetching_allowed"])
        self.assertFalse(provider["limits"]["write_operations_allowed"])
        self.assertFalse(provider["limits"]["secret_values_exposed"])

    def test_key_is_backend_only(self):
        with patch.dict(
            os.environ,
            {"MEDIASTACK_API_KEY": "abcdef1234567890"},
            clear=False,
        ):
            self.assertEqual(task.api_key(), "abcdef1234567890")
        with patch.dict(os.environ, {"MEDIASTACK_API_KEY": ""}, clear=False):
            with self.assertRaises(task.MediastackError) as caught:
                task.api_key()
            self.assertEqual(caught.exception.code, "MEDIASTACK_API_KEY_MISSING")

    def test_build_request_uses_fixed_paths_and_bounded_pagination(self):
        url, query, metadata = task.build_request(
            "search-news",
            {
                "keywords": "永辉超市",
                "countries": ["cn"],
                "languages": ["zh"],
                "categories": ["business"],
                "limit": 25,
                "offset": 0,
            },
        )
        self.assertEqual(url, "https://api.mediastack.com/v1/news")
        self.assertEqual(query["countries"], "cn")
        self.assertEqual(query["languages"], "zh")
        self.assertEqual(query["categories"], "business")
        self.assertNotIn("access_key", query)
        self.assertEqual(metadata["request_origin"], "api.mediastack.com")
        self.assertFalse(metadata["secret_value_exposed"])
        with self.assertRaises(ValueError):
            task.build_request("latest-news", {"limit": 101})

    def test_historical_range_is_bounded(self):
        task.build_request(
            "historical-news",
            {"date": "2025-01-01,2025-12-31", "limit": 10},
        )
        with self.assertRaises(ValueError):
            task.build_request(
                "historical-news",
                {"date": "2024-01-01,2025-12-31", "limit": 10},
            )
        with self.assertRaises(ValueError):
            task.build_request(
                "historical-news",
                {"date": "2025-12-31,2025-01-01", "limit": 10},
            )

    def test_local_catalog_needs_no_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            ticket_path = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket_path.write_text(
                json.dumps(self.ticket()),
                encoding="utf-8",
            )
            self.assertEqual(task.execute(ticket_path, out), 0)
            diagnostics = json.loads(
                (out / "diagnostics.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                diagnostics["status"],
                "INTEL_MEDIASTACK_COMPLETED",
            )
            self.assertFalse(diagnostics["metadata"]["upstream_called"])

    def test_mocked_news_call_succeeds_and_never_persists_key(self):
        response = {
            "pagination": {"limit": 1, "offset": 0, "count": 1, "total": 1},
            "data": [{
                "author": "Public Reporter",
                "title": "Yonghui Superstores public business update",
                "description": "Public market news test.",
                "url": "https://example.com/yonghui",
                "source": "Example News",
                "image": None,
                "category": "business",
                "language": "en",
                "country": "cn",
                "published_at": "2026-08-01T00:00:00+00:00",
            }],
        }
        secret = "abcdef1234567890"
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {"MEDIASTACK_API_KEY": secret},
            clear=False,
        ), patch.object(
            task.requests,
            "get",
            return_value=FakeResponse(response),
        ):
            ticket_path = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket_path.write_text(
                json.dumps(
                    self.ticket(
                        "search-news",
                        {
                            "keywords": "Yonghui Superstores",
                            "countries": ["cn"],
                            "limit": 1,
                            "offset": 0,
                        },
                    )
                ),
                encoding="utf-8",
            )
            self.assertEqual(task.execute(ticket_path, out), 0)
            diagnostics = json.loads(
                (out / "diagnostics.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                diagnostics["status"],
                "INTEL_MEDIASTACK_COMPLETED",
            )
            self.assertTrue(diagnostics["metadata"]["upstream_called"])
            for path in out.iterdir():
                if path.is_file():
                    self.assertNotIn(secret.encode(), path.read_bytes())

    def test_plan_error_is_classified(self):
        payload = {
            "error": {
                "code": "function_access_restricted",
                "message": "Historical data requires a paid plan.",
            }
        }
        with patch.dict(
            os.environ,
            {"MEDIASTACK_API_KEY": "abcdef1234567890"},
            clear=False,
        ), patch.object(
            task.requests,
            "get",
            return_value=FakeResponse(payload, status_code=403),
        ):
            with self.assertRaises(task.MediastackError) as caught:
                task.query_mediastack(
                    "historical-news",
                    {"date": "2025-01-01", "limit": 1},
                    timeout=30,
                    max_bytes=1_000_000,
                    max_rows=100,
                )
            self.assertEqual(caught.exception.code, "MEDIASTACK_PLAN_REQUIRED")


if __name__ == "__main__":
    unittest.main()
