from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
import urllib.parse
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "knowledge_tools_task",
    ROOT / "knowledge_tools_task.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FakeResponse:
    def __init__(
        self,
        payload: dict | str,
        status: int = 200,
        content_type: str = "application/json",
    ):
        self.status = status
        if isinstance(payload, str):
            self.raw = payload.encode("utf-8")
        else:
            self.raw = json.dumps(payload).encode("utf-8")
        self.headers = {"Content-Type": content_type}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, amount: int) -> bytes:
        return self.raw[:amount]


def ticket(provider: str, operation: str, parameters: dict) -> dict:
    return {
        "task_id": f"test-{provider}-{operation}",
        "provider": provider,
        "operation": operation,
        "objective": "deterministic validation",
        "parameters": parameters,
        "data_policy": {
            "classification": "public",
            "contains_personal_data": False,
        },
        "acceptance": {
            "timeout_seconds": 30,
            "max_response_bytes": 1000000,
            "poll_timeout_seconds": 30,
        },
    }


class KnowledgeToolsTaskTests(unittest.TestCase):
    def test_catalog_contract(self):
        catalog = MODULE.load_json(ROOT / "provider-catalog.json")
        providers = {row["provider_id"]: row for row in catalog["providers"]}
        self.assertEqual(set(providers), {"wolfram-alpha", "llamaparse"})
        self.assertEqual(
            providers["wolfram-alpha"]["required_secret_environment_variable"],
            "WOLFRAM_ALPHA_APP_ID",
        )
        self.assertEqual(
            providers["llamaparse"]["required_secret_environment_variable"],
            "LLAMA_CLOUD_API_KEY",
        )
        self.assertEqual(len(providers["wolfram-alpha"]["operations"]), 4)
        self.assertEqual(len(providers["llamaparse"]["operations"]), 3)

    def test_rejects_cross_provider_operation(self):
        with self.assertRaisesRegex(ValueError, "not available"):
            MODULE.validate_ticket(
                ticket(
                    "wolfram-alpha",
                    "parse-public-document",
                    {"source_url": "https://arxiv.org/pdf/1706.03762"},
                )
            )

    def test_prepare_requires_provider_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            event = Path(tmp) / "event.json"
            out = Path(tmp) / "out"
            event.write_text(
                json.dumps(
                    {
                        "issue": {
                            "title": "[api-llamaparse] wrong",
                            "body": json.dumps(
                                ticket(
                                    "wolfram-alpha",
                                    "short-answer",
                                    {"input": "2+2"},
                                )
                            ),
                        }
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(MODULE.prepare(event, out), 1)
            status = MODULE.load_json(out / "ticket-status.json")
            self.assertFalse(status["accepted"])
            self.assertIn("[api-wolfram]", status["reason"])

    def test_public_document_url_allowlist(self):
        self.assertEqual(
            MODULE.validate_public_document_url(
                "https://arxiv.org/pdf/1706.03762#page=1"
            ),
            "https://arxiv.org/pdf/1706.03762",
        )
        self.assertEqual(
            MODULE.validate_public_document_url(
                "https://raw.githubusercontent.com/openai/openai-cookbook/main/README.md"
            ),
            "https://raw.githubusercontent.com/openai/openai-cookbook/main/README.md",
        )
        for unsafe in (
            "http://arxiv.org/pdf/1706.03762",
            "https://127.0.0.1/file.pdf",
            "https://example.com/file.pdf",
            "https://github.com/openai/repo/blob/main/file.pdf",
        ):
            with self.subTest(unsafe=unsafe), self.assertRaises(ValueError):
                MODULE.validate_public_document_url(unsafe)

    def test_wolfram_short_answer_uses_appid_and_scrubs_result(self):
        captured = {}

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            return FakeResponse(
                "4; appid=wolfram-secret",
                content_type="text/plain",
            )

        with patch.dict(
            os.environ,
            {"WOLFRAM_ALPHA_APP_ID": "wolfram-secret"},
            clear=False,
        ), patch.object(
            MODULE.urllib.request,
            "urlopen",
            side_effect=fake_urlopen,
        ):
            data, metadata, secret_name = MODULE.wolfram_query(
                "short-answer",
                {"input": "2+2", "units": "metric"},
                30,
                1000000,
            )
        parsed = urllib.parse.urlsplit(captured["url"])
        query = urllib.parse.parse_qs(parsed.query)
        self.assertEqual(query["appid"], ["wolfram-secret"])
        self.assertEqual(query["i"], ["2+2"])
        self.assertEqual(query["units"], ["metric"])
        self.assertNotIn("wolfram-secret", json.dumps(data))
        self.assertEqual(metadata["request_path"], "/v1/result")
        self.assertEqual(secret_name, "WOLFRAM_ALPHA_APP_ID")

    def test_llamaparse_create_poll_and_scrub(self):
        captured = []
        responses = [
            FakeResponse({"id": "job-12345678", "status": "PENDING"}),
            FakeResponse(
                {
                    "job": {
                        "id": "job-12345678",
                        "status": "COMPLETED",
                        "error_message": None,
                    },
                    "markdown_full": "# Parsed",
                    "result_content_metadata": {
                        "markdown": {
                            "presigned_url": "https://signed.example/secret"
                        }
                    },
                }
            ),
        ]

        def fake_urlopen(request, timeout):
            captured.append(request)
            return responses.pop(0)

        with patch.dict(
            os.environ,
            {"LLAMA_CLOUD_API_KEY": "llama-secret"},
            clear=False,
        ), patch.object(
            MODULE.urllib.request,
            "urlopen",
            side_effect=fake_urlopen,
        ), patch.object(MODULE.time, "sleep", return_value=None):
            data, metadata, secret_name = MODULE.llamaparse_query(
                "parse-public-document",
                {
                    "source_url": "https://arxiv.org/pdf/1706.03762",
                    "tier": "cost_effective",
                    "max_pages": 2,
                },
                30,
                1000000,
                30,
            )

        self.assertEqual(captured[0].method, "POST")
        self.assertEqual(
            captured[0].headers.get("Authorization"),
            "Bearer llama-secret",
        )
        body = json.loads(captured[0].data.decode("utf-8"))
        self.assertEqual(body["tier"], "cost_effective")
        self.assertEqual(body["page_ranges"], {"max_pages": 2})
        self.assertIn(
            "expand=markdown_full%2Cmetadata%2Cjob_metadata",
            captured[1].full_url,
        )
        serialized = json.dumps(data)
        self.assertNotIn("llama-secret", serialized)
        self.assertNotIn("signed.example", serialized)
        self.assertEqual(metadata["job_id"], "job-12345678")
        self.assertEqual(secret_name, "LLAMA_CLOUD_API_KEY")

    def test_execute_missing_secret_is_structured_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            ticket_path.write_text(
                json.dumps(
                    ticket(
                        "wolfram-alpha",
                        "full-results",
                        {"input": "population of France"},
                    )
                ),
                encoding="utf-8",
            )
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(MODULE.execute(ticket_path, root), 1)
            status = MODULE.load_json(root / "execution-status.json")
            self.assertEqual(status["status"], "API_KNOWLEDGE_TOOLS_FAILED")
            self.assertIn("WOLFRAM_ALPHA_APP_ID", status["failure"]["message"])
            self.assertFalse(status["secret_values_exposed"])


if __name__ == "__main__":
    unittest.main()
