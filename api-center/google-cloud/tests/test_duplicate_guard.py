from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "google_cloud_duplicate_guard_tests", ROOT / "duplicate_guard.py"
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class DuplicateGuardTests(unittest.TestCase):
    def ticket(self, task_id: str = "gcp-duplicate-0001") -> dict:
        return {
            "task_id": task_id,
            "provider": "bigquery",
            "operation": "catalog-projects",
            "parameters": {},
            "data_policy": {
                "classification": "public",
                "contains_personal_data": False,
            },
            "acceptance": {},
        }

    def test_rejects_same_task_id_in_prior_gcp_issue(self) -> None:
        ticket = self.ticket()
        rows = [
            {
                "number": 12,
                "title": "[api-gcp] prior",
                "body": json.dumps({**ticket, "parameters": {"different": True}}),
            }
        ]
        with mock.patch.object(module, "_api_json", return_value=rows):
            reason = module.duplicate_reason(
                ticket,
                repository="owner/repo",
                current_issue=13,
                token="token",
            )
        self.assertIn("duplicate task_id", reason)
        self.assertIn("#12", reason)

    def test_rejects_same_content_with_different_task_id(self) -> None:
        ticket = self.ticket("gcp-new-id-0002")
        prior = self.ticket("gcp-old-id-0001")
        rows = [{"number": 7, "title": "[api-gcp] prior", "body": json.dumps(prior)}]
        with mock.patch.object(module, "_api_json", return_value=rows):
            reason = module.duplicate_reason(
                ticket,
                repository="owner/repo",
                current_issue=8,
                token="token",
            )
        self.assertIn("duplicate ticket content", reason)
        self.assertIn("#7", reason)
        self.assertEqual(module.ticket_fingerprint(ticket), module.ticket_fingerprint(prior))

    def test_different_content_is_not_rejected_by_fingerprint(self) -> None:
        ticket = self.ticket("gcp-new-id-0002")
        prior = self.ticket("gcp-old-id-0001")
        prior["operation"] = "catalog-datasets"
        prior["parameters"] = {"project_id": "bigquery-public-data"}
        rows = [{"number": 7, "title": "[api-gcp] prior", "body": json.dumps(prior)}]
        with mock.patch.object(module, "_api_json", return_value=rows):
            reason = module.duplicate_reason(
                ticket,
                repository="owner/repo",
                current_issue=8,
                token="token",
            )
        self.assertEqual(reason, "")

    def test_ignores_current_issue_pull_requests_and_other_prefixes(self) -> None:
        ticket = self.ticket()
        rows = [
            {"number": 3, "title": "[api-gcp] current", "body": json.dumps(ticket)},
            {"number": 4, "title": "[api] ordinary", "body": json.dumps(ticket)},
            {
                "number": 5,
                "title": "[api-gcp] pull request",
                "body": json.dumps(ticket),
                "pull_request": {},
            },
        ]
        with mock.patch.object(module, "_api_json", return_value=rows):
            reason = module.duplicate_reason(
                ticket,
                repository="owner/repo",
                current_issue=3,
                token="token",
            )
        self.assertEqual(reason, "")

    def test_check_updates_status_without_copying_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            status_path = root / "ticket-status.json"
            ticket_path.write_text(json.dumps(self.ticket()), encoding="utf-8")
            status_path.write_text(
                json.dumps({"accepted": True, "reason": ""}), encoding="utf-8"
            )
            with mock.patch.object(
                module,
                "duplicate_reason",
                return_value="duplicate task_id; previously submitted in Issue #2",
            ), mock.patch.dict(
                os.environ,
                {
                    "GITHUB_REPOSITORY": "owner/repo",
                    "ISSUE_NUMBER": "3",
                    "GITHUB_TOKEN": "not-written",
                },
                clear=False,
            ):
                rc = module.check(ticket_path, status_path)
            self.assertEqual(rc, 2)
            status = json.loads(status_path.read_text(encoding="utf-8"))
            self.assertFalse(status["accepted"])
            self.assertNotIn("not-written", status_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
