from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "google_public_intelligence_task",
    HERE / "google_public_intelligence_task.py",
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class FakeResponse:
    def __init__(self, payload: object, status_code: int = 200) -> None:
        self.content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.status_code = status_code
        self.is_redirect = 300 <= status_code < 400


class GooglePublicIntelligenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original = os.environ.get(module.API_KEY_ENV)
        os.environ[module.API_KEY_ENV] = "test_google_public_key_1234567890"

    def tearDown(self) -> None:
        if self.original is None:
            os.environ.pop(module.API_KEY_ENV, None)
        else:
            os.environ[module.API_KEY_ENV] = self.original

    def test_catalog_has_exact_governed_operations(self) -> None:
        provider = module.provider_row(module.CATALOG_PATH)
        operations = [row["operation_id"] for row in provider["operations"]]
        self.assertEqual(
            operations,
            [
                "catalog-capabilities",
                "quota-policy",
                "youtube-search-videos",
                "youtube-video",
                "youtube-channel",
                "factcheck-search",
                "pagespeed-analyze",
                "crux-query",
                "crux-history-query",
            ],
        )
        self.assertFalse(provider["limits"]["write_operations_allowed"])
        self.assertFalse(provider["limits"]["automatic_retries_allowed"])
        self.assertFalse(provider["limits"]["automatic_pagination_allowed"])
        self.assertFalse(provider["limits"]["paid_fallback_authorized"])

    def test_public_https_validation_rejects_unsafe_targets(self) -> None:
        rejected = [
            "http://example.com",
            "https://localhost/",
            "https://127.0.0.1/",
            "https://10.0.0.1/",
            "https://example.local/",
            "https://user:pass@example.com/",
            "https://example.com:8443/",
        ]
        for value in rejected:
            with self.subTest(value=value), self.assertRaises(ValueError):
                module._validate_public_https(value)
        self.assertEqual(
            module._validate_public_https("https://example.com/path"),
            "https://example.com/path",
        )
        self.assertEqual(
            module._validate_public_https("https://example.com", origin_only=True),
            "https://example.com",
        )
        with self.assertRaises(ValueError):
            module._validate_public_https("https://example.com/path", origin_only=True)

    def test_crux_body_allows_exactly_one_identifier(self) -> None:
        body = module._crux_body(
            {
                "origin": "https://example.com",
                "form_factor": "PHONE",
                "metrics": ["largest_contentful_paint"],
                "collection_period_count": 12,
            },
            history=True,
        )
        self.assertEqual(body["origin"], "https://example.com")
        self.assertEqual(body["formFactor"], "PHONE")
        self.assertEqual(body["collectionPeriodCount"], 12)

    def test_one_request_and_backend_only_key(self) -> None:
        calls: list[dict] = []

        def fake_request(method: str, url: str, **kwargs: object) -> FakeResponse:
            calls.append({"method": method, "url": url, **kwargs})
            return FakeResponse(
                {
                    "pageInfo": {"totalResults": 1, "resultsPerPage": 1},
                    "items": [
                        {
                            "id": {"videoId": "dQw4w9WgXcQ"},
                            "snippet": {"title": "public result"},
                        }
                    ],
                }
            )

        with patch.object(module.requests, "request", side_effect=fake_request):
            payload, metadata = module._youtube_search(
                {"query": "public policy", "max_results": 1},
                timeout=30,
                max_bytes=100000,
            )
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["method"], "GET")
        self.assertEqual(calls[0]["url"], "https://www.googleapis.com/youtube/v3/search")
        params = calls[0]["params"]
        self.assertEqual(params["key"], os.environ[module.API_KEY_ENV])
        self.assertEqual(payload["items"][0]["id"]["videoId"], "dQw4w9WgXcQ")
        self.assertEqual(metadata["requests_per_ticket"], 1)
        self.assertFalse(metadata["secret_values_exposed"])
        self.assertFalse(metadata["paid_fallback_authorized"])

    def test_execute_local_and_remote_artifacts_do_not_leak_key(self) -> None:
        base = {
            "provider": "google-public-intelligence",
            "objective": "test",
            "data_policy": {
                "classification": "public",
                "contains_personal_data": False,
                "contains_confidential_data": False,
            },
            "acceptance": {
                "timeout_seconds": 30,
                "max_response_bytes": 200000,
                "max_rows": 5,
            },
        }
        tickets = [
            {
                **base,
                "task_id": "test-catalog",
                "operation": "catalog-capabilities",
                "parameters": {},
            },
            {
                **base,
                "task_id": "test-youtube",
                "operation": "youtube-search-videos",
                "parameters": {"query": "public policy", "max_results": 1},
            },
        ]

        def fake_request(method: str, url: str, **kwargs: object) -> FakeResponse:
            return FakeResponse(
                {
                    "pageInfo": {"totalResults": 1, "resultsPerPage": 1},
                    "items": [{"id": {"videoId": "dQw4w9WgXcQ"}, "snippet": {"title": "result"}}],
                }
            )

        with tempfile.TemporaryDirectory() as temp, patch.object(
            module.requests, "request", side_effect=fake_request
        ):
            root = Path(temp)
            for ticket in tickets:
                folder = root / ticket["task_id"]
                folder.mkdir()
                ticket_path = folder / "ticket.json"
                ticket_path.write_text(json.dumps(ticket), encoding="utf-8")
                self.assertEqual(module.execute(ticket_path, folder), 0)
                diagnostics = json.loads((folder / "diagnostics.json").read_text())
                self.assertEqual(diagnostics["status"], "INTEL_GOOGLE_PUBLIC_COMPLETED")
                self.assertEqual(diagnostics["model_calls"], 0)
                self.assertFalse(diagnostics["secret_values_exposed"])
                for path in folder.iterdir():
                    if path.is_file():
                        self.assertNotIn(
                            os.environ[module.API_KEY_ENV].encode(),
                            path.read_bytes(),
                        )

    def test_redaction_removes_direct_identifiers_and_secret_fields(self) -> None:
        result = module._redact(
            {
                "email": "person@example.com",
                "phone": "13800138000",
                "api_key": "never-show",
                "text": "联系 person@example.com 或 13800138000",
            }
        )
        self.assertEqual(result["email"], "[REDACTED]")
        self.assertEqual(result["phone"], "[REDACTED]")
        self.assertEqual(result["api_key"], "[REDACTED_SECRET]")
        self.assertNotIn("person@example.com", result["text"])
        self.assertNotIn("13800138000", result["text"])


if __name__ == "__main__":
    unittest.main()
