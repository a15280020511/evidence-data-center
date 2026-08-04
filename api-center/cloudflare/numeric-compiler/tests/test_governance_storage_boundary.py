from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "cloudflare_numeric_compiler_runtime_boundary",
    ROOT / "cloudflare_numeric_compiler_runtime.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class GovernanceStorageBoundaryTests(unittest.TestCase):
    def test_configuration_requires_governance_gateway(self) -> None:
        receipt = MODULE.validate_configuration()
        self.assertEqual(
            receipt["storage_gateway_owner"],
            "a15280020511/decision-system-governance",
        )
        self.assertFalse(receipt["direct_huggingface_write_allowed"])
        self.assertTrue(receipt["governance_artifact_required"])

    def test_legacy_direct_commit_flag_is_rejected_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(
                MODULE.NumericCompilerError,
                "direct Hugging Face commit is forbidden",
            ):
                MODULE.execute(
                    root / "missing-ticket.json",
                    root / "out",
                    commit_to_hf=True,
                )


if __name__ == "__main__":
    unittest.main()
