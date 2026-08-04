from __future__ import annotations

import unittest
from pathlib import Path


class RealityObservationWorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = (
            Path(__file__).resolve().parents[3]
            / ".github"
            / "workflows"
            / "reality-observation-api-ticket.yml"
        ).read_text(encoding="utf-8")

    def test_duplicate_admission_is_fail_closed(self) -> None:
        self.assertIn("ADMISSION_REJECTED_DUPLICATE", self.workflow)
        self.assertIn("New upstream request executed: `false`", self.workflow)
        self.assertIn("steps.admission.outputs.duplicate == 'true'", self.workflow)
        self.assertIn("run: exit 1", self.workflow)

    def test_duplicate_path_skips_execution_and_upload(self) -> None:
        self.assertIn(
            "steps.admission.outputs.duplicate != 'true' && steps.prepare.outputs.accepted == 'true'",
            self.workflow,
        )
        self.assertIn(
            "if: always() && steps.admission.outputs.duplicate != 'true'",
            self.workflow,
        )

    def test_serial_global_lock_remains(self) -> None:
        self.assertIn("group: intel-reality-observation-global", self.workflow)
        self.assertIn("cancel-in-progress: false", self.workflow)


if __name__ == "__main__":
    unittest.main()
