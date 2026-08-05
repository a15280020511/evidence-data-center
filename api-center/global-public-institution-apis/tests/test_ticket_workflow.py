from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github/workflows/global-public-institution-apis-ticket.yml"


class GlobalPublicInstitutionWorkflowTests(unittest.TestCase):
    def test_irrelevant_issues_cannot_cancel_pending_provider_ticket(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            "startsWith(github.event.issue.title, '[intel-public-institution]')",
            text,
        )
        self.assertIn(
            "format('intel-global-public-institution-ignored-{0}', github.run_id)",
            text,
        )
        self.assertIn("cancel-in-progress: false", text)

    def test_job_still_requires_owner_and_ticket_prefix(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("github.actor == github.repository_owner", text)
        self.assertIn(
            "startsWith(github.event.issue.title, '[intel-public-institution]')",
            text,
        )


if __name__ == "__main__":
    unittest.main()
