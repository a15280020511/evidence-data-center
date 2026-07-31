#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one anchor in {path}, found {count}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def patch_bigquery() -> None:
    path = Path("api-center/google-cloud/google_cloud_task.py")
    old = '''    result, exec_meta = _http_json(
        "POST",
        url,
        token=token,
        body={
            **common,
            "dryRun": False,
            "maxResults": max_rows,
            "timeoutMs": timeout_ms,
            "useQueryCache": True,
            "jobTimeoutMs": str(timeout_ms),
            "requestId": hashlib.sha256(sql.encode("utf-8")).hexdigest()[:32],
        },
        timeout=max(timeout, (timeout_ms // 1000) + 5),
    )
    if not result.get("jobComplete", False):
        raise RuntimeError("BigQuery job did not complete within the allowed synchronous timeout")
    return {
'''
    new = '''    result, exec_meta = _http_json(
        "POST",
        url,
        token=token,
        body={
            **common,
            "dryRun": False,
            "maxResults": max_rows,
            "timeoutMs": timeout_ms,
            "useQueryCache": True,
            "jobTimeoutMs": str(timeout_ms),
            "requestId": hashlib.sha256(sql.encode("utf-8")).hexdigest()[:32],
        },
        timeout=max(timeout, (timeout_ms // 1000) + 5),
    )
    poll_count = 0
    if not result.get("jobComplete", False):
        job_reference = result.get("jobReference")
        if not isinstance(job_reference, Mapping):
            raise RuntimeError("BigQuery returned an incomplete job without jobReference")
        job_project = str(job_reference.get("projectId") or billing_project)
        job_id = str(job_reference.get("jobId") or "")
        job_location = str(job_reference.get("location") or location)
        if not PROJECT_ID_RE.fullmatch(job_project) or not job_id:
            raise RuntimeError("BigQuery returned an invalid jobReference")
        poll_url = (
            "https://bigquery.googleapis.com/bigquery/v2/projects/"
            f"{quote(job_project)}/queries/{quote(job_id)}"
        )
        deadline = time.monotonic() + max(
            1.0,
            min(float(timeout), timeout_ms / 1000.0 + 5.0),
        )
        while not result.get("jobComplete", False):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError("BigQuery job did not complete before the polling deadline")
            poll_timeout_ms = max(1000, min(10_000, int(remaining * 1000)))
            result, poll_meta = _http_json(
                "GET",
                poll_url,
                token=token,
                params={
                    "location": job_location,
                    "maxResults": max_rows,
                    "timeoutMs": poll_timeout_ms,
                },
                timeout=max(5, min(timeout, (poll_timeout_ms // 1000) + 5)),
            )
            exec_meta = poll_meta
            poll_count += 1
            if not result.get("jobComplete", False):
                time.sleep(min(1.0, max(0.05, remaining / 10.0)))
    return {
'''
    replace_once(path, old, new)
    replace_once(
        path,
        '    }, {**exec_meta, "dry_run_http_status": dry_meta["http_status"]}\n',
        '    }, {\n        **exec_meta,\n        "dry_run_http_status": dry_meta["http_status"],\n        "poll_count": poll_count,\n    }\n',
    )
    replace_once(
        path,
        'raise RuntimeError(f"missing repository Secret {SERVICE_ACCOUNT_ENV}")',
        'raise RuntimeError(f"missing repository Secret {EARTH_ENGINE_SERVICE_ACCOUNT_ENV}")',
    )


def patch_data_commons() -> None:
    path = Path("api-center/data-commons/data_commons_task.py")
    marker = '''def _request_json(endpoint: str, *, api_key: str, body: Mapping[str, Any], timeout: int, max_bytes: int) -> tuple[dict[str, Any], dict[str, Any]]:
'''
    replacement = '''def _validate_api_key(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise RuntimeError(f"missing repository Secret {API_KEY_ENV}")
    if not 8 <= len(text) <= 512:
        raise RuntimeError(
            f"invalid repository Secret {API_KEY_ENV}: expected 8 to 512 visible ASCII characters"
        )
    if any(ord(character) < 0x21 or ord(character) > 0x7E for character in text):
        raise RuntimeError(
            f"invalid repository Secret {API_KEY_ENV}: only visible ASCII characters are allowed"
        )
    return text


def _request_json(endpoint: str, *, api_key: str, body: Mapping[str, Any], timeout: int, max_bytes: int) -> tuple[dict[str, Any], dict[str, Any]]:
'''
    replace_once(path, marker, replacement)
    replace_once(
        path,
        '''            api_key = str(os.getenv(API_KEY_ENV) or "").strip()
            if not api_key:
                raise RuntimeError(f"missing repository Secret {API_KEY_ENV}")
''',
        '''            api_key = _validate_api_key(os.getenv(API_KEY_ENV))
''',
    )
    replace_once(
        path,
        '''        blocked = text.startswith("missing repository Secret")
        status = "API_DATA_COMMONS_BLOCKED" if blocked else "API_DATA_COMMONS_FAILED"
        failure = {
            "code": "DATA_COMMONS_API_KEY_MISSING" if blocked else "DATA_COMMONS_UPSTREAM_ERROR",
            "message": text,
            "retryable": not blocked,
        }
''',
        '''        missing = text.startswith("missing repository Secret")
        invalid = text.startswith("invalid repository Secret")
        blocked = missing or invalid
        status = "API_DATA_COMMONS_BLOCKED" if blocked else "API_DATA_COMMONS_FAILED"
        if missing:
            code = "DATA_COMMONS_API_KEY_MISSING"
        elif invalid:
            code = "DATA_COMMONS_API_KEY_INVALID"
        else:
            code = "DATA_COMMONS_UPSTREAM_ERROR"
        failure = {
            "code": code,
            "message": text,
            "retryable": not blocked,
        }
''',
    )


def write_tests() -> None:
    Path("api-center/google-cloud/tests/test_google_runtime_repair.py").write_text(
        '''from __future__ import annotations

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
''',
        encoding="utf-8",
    )
    Path("api-center/data-commons/tests/test_data_commons_key_validation.py").write_text(
        '''from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("data_commons_key_validation_tests", ROOT / "data_commons_task.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class DataCommonsKeyValidationTests(unittest.TestCase):
    def ticket(self) -> dict:
        return {
            "task_id": "dc-invalid-key-test",
            "provider": "data-commons",
            "operation": "resolve-place",
            "objective": "validate key handling",
            "parameters": {"nodes_json": '["Fuzhou"]'},
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "acceptance": {"timeout_seconds": 30, "max_response_bytes": 500000},
        }

    def test_visible_ascii_key_is_accepted(self) -> None:
        self.assertEqual(module._validate_api_key("AIza_valid-key_123"), "AIza_valid-key_123")

    def test_non_ascii_placeholder_is_blocked_before_http(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "visible ASCII"):
            module._validate_api_key("你的Data Commons API Key")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            output_dir = root / "out"
            ticket_path.write_text(json.dumps(self.ticket()), encoding="utf-8")
            with mock.patch.dict(os.environ, {module.API_KEY_ENV: "你的Data Commons API Key"}, clear=True), mock.patch.object(
                module.requests, "post"
            ) as post:
                rc = module.execute(ticket_path, output_dir)
            self.assertEqual(rc, 1)
            post.assert_not_called()
            snapshot = json.loads((output_dir / "data-commons-snapshot.json").read_text(encoding="utf-8"))
            self.assertEqual(snapshot["status"], "API_DATA_COMMONS_BLOCKED")
            self.assertEqual(snapshot["failure"]["code"], "DATA_COMMONS_API_KEY_INVALID")
            self.assertFalse(snapshot["failure"]["retryable"])


if __name__ == "__main__":
    unittest.main()
''',
        encoding="utf-8",
    )


def main() -> None:
    patch_bigquery()
    patch_data_commons()
    write_tests()


if __name__ == "__main__":
    main()
