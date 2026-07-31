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
    "context_retrieval_task", ROOT / "context_retrieval_task.py"
)
assert SPEC and SPEC.loader
task = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(task)


def ticket(provider: str, operation: str, parameters: dict) -> dict:
    return {
        "task_id": "context-task-0001",
        "provider": provider,
        "operation": operation,
        "objective": "test",
        "parameters": parameters,
        "data_policy": {
            "classification": "public",
            "contains_personal_data": False,
        },
        "acceptance": {
            "timeout_seconds": 30,
            "max_response_bytes": 500000,
        },
    }


class FakeResponse:
    status = 200
    headers = {"Content-Type": "application/json"}

    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, _limit: int) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class ContextRetrievalTaskTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ.pop("TAVILY_API_KEY", None)
        os.environ.pop("FIRECRAWL_API_KEY", None)

    def test_catalog_operations_need_no_secret(self) -> None:
        for provider in ("tavily", "firecrawl"):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                path = root / "ticket.json"
                path.write_text(
                    json.dumps(ticket(provider, "catalog-capabilities", {})),
                    encoding="utf-8",
                )
                self.assertEqual(task.execute(path, root), 0)
                result = json.loads((root / "result.json").read_text())
                self.assertEqual(result["status"], "API_CONTEXT_COMPLETED")
                self.assertFalse(result["metadata"]["upstream_called"])

    def test_missing_tavily_secret_is_structured_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "ticket.json"
            path.write_text(
                json.dumps(ticket("tavily", "search", {"query": "AI news"})),
                encoding="utf-8",
            )
            self.assertEqual(task.execute(path, root), 1)
            result = json.loads((root / "result.json").read_text())
            self.assertEqual(result["status"], "API_CONTEXT_BLOCKED")
            self.assertIn("TAVILY_API_KEY", result["failure"]["message"])
            self.assertFalse(result["secret_values_exposed"])

    def test_missing_firecrawl_secret_is_structured_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "ticket.json"
            path.write_text(
                json.dumps(ticket("firecrawl", "search", {"query": "AI news"})),
                encoding="utf-8",
            )
            self.assertEqual(task.execute(path, root), 1)
            result = json.loads((root / "result.json").read_text())
            self.assertEqual(result["status"], "API_CONTEXT_BLOCKED")
            self.assertIn("FIRECRAWL_API_KEY", result["failure"]["message"])

    def test_provider_operation_pair_is_enforced(self) -> None:
        with self.assertRaisesRegex(ValueError, "not available"):
            task.validate_ticket(ticket("firecrawl", "crawl", {"url": "https://example.com"}))

    def test_private_and_local_urls_are_rejected(self) -> None:
        for url in (
            "https://127.0.0.1/private",
            "https://10.0.0.1/private",
            "https://localhost/private",
            "https://metadata.google.internal/",
            "http://example.com/",
        ):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    task.validate_public_https_url(url)

    @patch("socket.getaddrinfo")
    def test_public_url_is_normalized(self, resolver) -> None:
        resolver.return_value = [(2, 1, 6, "", ("93.184.216.34", 443))]
        self.assertEqual(
            task.validate_public_https_url("https://example.com"),
            "https://example.com/",
        )

    @patch("urllib.request.urlopen")
    def test_tavily_key_is_backend_only(self, urlopen) -> None:
        os.environ["TAVILY_API_KEY"] = "test-tavily-secret"
        urlopen.return_value = FakeResponse(
            {"results": [{"title": "A"}], "usage": {"credits": 1}}
        )
        payload, metadata = task._tavily_search(
            {"query": "AI", "max_results": 1}, 30, 500000
        )
        request = urlopen.call_args.args[0]
        self.assertEqual(request.headers["Authorization"], "Bearer test-tavily-secret")
        self.assertNotIn("test-tavily-secret", json.dumps(payload))
        self.assertEqual(metadata["result_count"], 1)

    @patch("urllib.request.urlopen")
    def test_firecrawl_search_uses_fixed_endpoint_and_body(self, urlopen) -> None:
        os.environ["FIRECRAWL_API_KEY"] = "test-firecrawl-secret"
        urlopen.return_value = FakeResponse(
            {"success": True, "data": {"web": [{"title": "A"}]}}
        )
        payload, metadata = task._firecrawl_search(
            {"query": "AI", "limit": 1}, 30, 500000
        )
        request = urlopen.call_args.args[0]
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(request.full_url, "https://api.firecrawl.dev/v2/search")
        self.assertEqual(request.headers["Authorization"], "Bearer test-firecrawl-secret")
        self.assertEqual(body["sources"], ["web"])
        self.assertNotIn("headers", body)
        self.assertEqual(metadata["result_count"], 1)
        self.assertTrue(payload["success"])

    @patch("socket.getaddrinfo")
    @patch("urllib.request.urlopen")
    def test_firecrawl_scrape_forbids_actions_and_headers(self, urlopen, resolver) -> None:
        resolver.return_value = [(2, 1, 6, "", ("93.184.216.34", 443))]
        os.environ["FIRECRAWL_API_KEY"] = "test-firecrawl-secret"
        urlopen.return_value = FakeResponse(
            {"success": True, "data": {"markdown": "hello"}}
        )
        task._firecrawl_scrape(
            {"url": "https://example.com", "formats": ["markdown"]},
            30,
            500000,
        )
        request = urlopen.call_args.args[0]
        body = json.loads(request.data.decode("utf-8"))
        self.assertNotIn("actions", body)
        self.assertNotIn("headers", body)
        self.assertTrue(body["zeroDataRetention"])
        self.assertFalse(body["skipTlsVerification"])


if __name__ == "__main__":
    unittest.main()
