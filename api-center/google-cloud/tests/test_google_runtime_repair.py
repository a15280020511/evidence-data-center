from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("google_runtime_repair_tests", ROOT / "google_cloud_task.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class GoogleRuntimeRepairTests(unittest.TestCase):
    def test_bigquery_polls_incomplete_job_until_complete(self) -> None:
        responses = [
            ({"totalBytesProcessed": "0"}, {"http_status": 200}),
            (
                {
                    "jobComplete": False,
                    "jobReference": {
                        "projectId": "billing-project",
                        "jobId": "job_123",
                        "location": "US",
                    },
                },
                {"http_status": 200},
            ),
            ({"jobComplete": False}, {"http_status": 200}),
            (
                {
                    "jobComplete": True,
                    "totalRows": "1",
                    "totalBytesProcessed": "0",
                    "totalBytesBilled": "0",
                    "schema": {"fields": [{"name": "value", "type": "INTEGER"}]},
                    "rows": [{"f": [{"v": "1"}]}],
                },
                {"http_status": 200},
            ),
        ]
        with mock.patch.object(module, "_http_json", side_effect=responses) as mocked, mock.patch.object(
            module.time, "sleep", return_value=None
        ):
            result, metadata = module._bigquery_query(
                {
                    "sql": "SELECT 1 AS value",
                    "maximum_bytes_billed": 1000000,
                    "max_rows": 1,
                    "timeout_ms": 30000,
                },
                "token",
                "billing-project",
                30,
            )
        self.assertEqual(mocked.call_count, 4)
        self.assertEqual(result["rows"], [{"value": 1}])
        self.assertEqual(metadata["poll_count"], 2)
        poll_call = mocked.call_args_list[2]
        self.assertEqual(poll_call.args[0], "GET")
        self.assertIn("/projects/billing-project/queries/job_123", poll_call.args[1])
        self.assertEqual(poll_call.kwargs["params"]["location"], "US")

    def test_incomplete_job_requires_reference(self) -> None:
        responses = [
            ({"totalBytesProcessed": "0"}, {"http_status": 200}),
            ({"jobComplete": False}, {"http_status": 200}),
        ]
        with mock.patch.object(module, "_http_json", side_effect=responses):
            with self.assertRaisesRegex(RuntimeError, "without jobReference"):
                module._bigquery_query(
                    {"sql": "SELECT 1", "maximum_bytes_billed": 1000000},
                    "token",
                    "billing-project",
                    30,
                )


if __name__ == "__main__":
    unittest.main()
