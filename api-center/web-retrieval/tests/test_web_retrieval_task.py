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
    "web_retrieval_task", ROOT / "web_retrieval_task.py"
)
assert SPEC and SPEC.loader
task = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(task)


def ticket(provider: str, operation: str, parameters: dict) -> dict:
    return {
        "task_id": "web-task-0001",
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


class WebRetrievalTaskTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ.pop("JINA_API_KEY", None)
        os.environ.pop("EXA_API_KEY", None)

    def test_catalog_operations_need_no_secret(self) -> None:
        for provider in ("jina-reader", "exa"):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                path = root / "ticket.json"
                path.write_text(
                    json.dumps(ticket(provider, "catalog-capabilities", {})),
                    encoding="utf-8",
                )
                self.assertEqual(task.execute(path, root), 0)
                result = json.loads((root / "result.json").read_text())
                self.assertEqual(result["status"], "API_WEB_COMPLETED")
                self.assertFalse(result["metadata"]["upstream_called"])

    def test_missing_exa_secret_is_structured_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "ticket.json"
            path.write_text(
                json.dumps(ticket("exa", "search", {"query": "AI news"})),
                encoding="utf-8",
            )
            self.assertEqual(task.execute(path, root), 1)
            result = json.loads((root / "result.json").read_text())
            self.assertEqual(result["status"], "API_WEB_BLOCKED")
            self.assertIn("EXA_API_KEY", result["failure"]["message"])
            self.assertFalse(result["secret_values_exposed"])

    def test_provider_operation_pair_is_enforced(self) -> None:
        with self.assertRaisesRegex(ValueError, "not available"):
            task.validate_ticket(ticket("jina-reader", "search", {"query": "x"}))

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
        resolver.return_value = [
            (2, 1, 6, "", ("93.184.216.34", 443)),
        ]
        self.assertEqual(
            task.validate_public_https_url("https://example.com"),
            "https://example.com/",
        )

    @patch("socket.getaddrinfo")
    @patch("urllib.request.urlopen")
    def test_jina_reader_works_anonymously(self, urlopen, resolver) -> None:
        resolver.return_value = [
            (2, 1, 6, "", ("93.184.216.34", 443)),
        ]
        urlopen.return_value = FakeResponse(
            {"data": {"title": "Example", "content": "Hello"}}
        )
        data, metadata = task._jina_read(
            {"url": "https://example.com", "max_tokens": 1000}, 30, 500000
        )
        request = urlopen.call_args.args[0]
        self.assertNotIn("Authorization", request.headers)
        self.assertEqual(metadata["credential_mode"], "anonymous")
        self.assertIn("data", data)

    @patch("urllib.request.urlopen")
    def test_exa_key_is_backend_only(self, urlopen) -> None:
        os.environ["EXA_API_KEY"] = "test-secret-value"
        urlopen.return_value = FakeResponse({"results": [{"title": "A"}]})
        payload, metadata = task._exa_search(
            {"query": "AI", "num_results": 1, "content_mode": "none"},
            30,
            500000,
        )
        request = urlopen.call_args.args[0]
        self.assertEqual(request.headers["X-api-key"], "test-secret-value")
        self.assertNotIn("test-secret-value", json.dumps(payload))
        self.assertEqual(metadata["result_count"], 1)


if __name__ == "__main__":
    unittest.main()
