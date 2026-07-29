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
    "runtime_diagnostics", ROOT / "runtime_diagnostics.py"
)
assert SPEC and SPEC.loader
runtime_diagnostics = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime_diagnostics)


class RuntimeDiagnosticsTests(unittest.TestCase):
    def _write_required(self, root: Path) -> None:
        (root / "api-center").mkdir(parents=True)
        (root / "api-center/connector-manifest.json").write_text(
            json.dumps(
                {
                    "connector_count": 2,
                    "enabled_connector_count": 1,
                }
            ),
            encoding="utf-8",
        )
        (root / "api-center/krakend.validation.json").write_text(
            "{}", encoding="utf-8"
        )
        (root / "api-center-unit-tests.log").write_text("ok\n", encoding="utf-8")
        (root / "api-center-base-image-requested.txt").write_text(
            "krakend:example@sha256:" + "a" * 64 + "\n",
            encoding="utf-8",
        )
        (root / "api-center-base-image-resolved.txt").write_text(
            "krakend@sha256:" + "a" * 64 + "\n",
            encoding="utf-8",
        )
        (root / "api-center-health.json").write_text(
            '{"status":"ok"}', encoding="utf-8"
        )
        (root / "api-center-container-inspect.json").write_text(
            "[]", encoding="utf-8"
        )
        (root / "api-center-runtime.log").write_text(
            "runtime healthy\n", encoding="utf-8"
        )

    def test_pass_requires_all_stages_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_required(root)
            result = runtime_diagnostics.build(
                root,
                registry_outcome="success",
                base_image_outcome="success",
                config_outcome="success",
                image_outcome="success",
                runtime_outcome="success",
                health="healthy",
                container_id="container-1",
            )
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["primary_failure"]["code"], "NONE")
            self.assertEqual(result["missing_evidence"], [])
            self.assertTrue((root / "api-center-audit.json").is_file())

    def test_failure_identifies_runtime_and_does_not_leak_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_required(root)
            with mock.patch.dict(
                os.environ,
                {"API_SECRET_VALUE": "must-not-leak", "GITHUB_RUN_ID": "55"},
                clear=False,
            ):
                result = runtime_diagnostics.build(
                    root,
                    registry_outcome="success",
                    base_image_outcome="success",
                    config_outcome="success",
                    image_outcome="success",
                    runtime_outcome="failure",
                    health="unhealthy",
                    container_id="container-2",
                )
            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(
                result["primary_failure"]["code"],
                "API_RUNTIME_HEALTH_FAILED",
            )
            serialized = json.dumps(result, ensure_ascii=False)
            self.assertNotIn("must-not-leak", serialized)
            self.assertFalse(result["security"]["secret_values_included"])


if __name__ == "__main__":
    unittest.main()
