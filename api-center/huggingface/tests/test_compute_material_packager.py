from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "compute_material_packager.py"
SPEC = importlib.util.spec_from_file_location("compute_material_packager", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ComputeMaterialPackagerTests(unittest.TestCase):
    def fixture(self, root: Path) -> tuple[dict, Path]:
        payload = root / "external-reality/v1/data/macroeconomy/sample.csv"
        payload.parent.mkdir(parents=True, exist_ok=True)
        payload.write_text("period,value\n2026-01,1\n", encoding="utf-8")
        record = {
            "record_id": "macro-sample-001",
            "version": "1.0.0",
            "material_type": "sample_snapshot",
            "status": "verified",
            "quality_status": "pass",
            "source_center": "intelligence-center",
            "source_root": "external-reality/v1",
            "title": "Verified macro sample",
            "valid_from": "2026-01-01",
            "valid_to": "2026-12-31",
            "geographic_scope": ["CN"],
            "time_range": {"start": "2026-01-01", "end": "2026-01-31"},
            "license": {
                "name": "reviewed-private-use",
                "reviewed": True,
                "redistribution_allowed": False,
                "commercial_use_allowed": True,
                "attribution_required": True,
                "use_scope": ["compute-analysis", "internal-research"],
            },
            "files": [{
                "path": "external-reality/v1/data/macroeconomy/sample.csv",
                "sha256": file_sha(payload),
                "bytes": payload.stat().st_size,
                "media_type": "text/csv",
            }],
            "contains_personal_data": False,
            "review_due_at": "2026-12-31",
            "point_in_time_safe": True,
            "publication_date": "2026-02-01",
            "revision_vintage": "2026-02-01",
            "known_limitations": ["fixture"],
            "source_manifest_path": None,
        }
        record_path = root / "external-reality/v1/records/macro-sample-001.json"
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_path.write_text(
            json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        selection_base = {
            "package_id": "package-0001",
            "task_id": "task-000001",
            "material_type": "sample_snapshot",
            "version": "1.0.0",
            "created_at": "2026-08-04T00:00:00Z",
            "record_paths": ["external-reality/v1/records/macro-sample-001.json"],
            "valid_from": "2026-01-01",
            "valid_to": "2026-12-31",
            "geographic_scope": ["CN"],
            "time_range": {"start": "2026-01-01", "end": "2026-01-31"},
            "decision_use": "deterministic test",
        }
        selection_sha = MODULE._canonical_sha(selection_base)
        selection = {
            **selection_base,
            "gpts_validation": {
                "status": "PASS",
                "validator": "gpts-usage-center",
                "validated_at": "2026-08-04T00:01:00Z",
                "task_id": "task-000001",
                "selection_sha256": selection_sha,
            },
        }
        return selection, record_path

    def test_build_is_deterministic_and_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            selection, _ = self.fixture(root)
            first = root / "out-one"
            second = root / "out-two"
            one = MODULE.build_package(
                selection=selection,
                source_root=root,
                output_dir=first,
                source_repository_reference="hf-dataset:James147258/cloudflare-intelligence-archive",
            )
            two = MODULE.build_package(
                selection=selection,
                source_root=root,
                output_dir=second,
                source_repository_reference="hf-dataset:James147258/cloudflare-intelligence-archive",
            )
            self.assertEqual(one["package_sha256"], two["package_sha256"])
            self.assertEqual(one["file_count"], 1)
            envelope = json.loads((first / "envelope.json").read_text(encoding="utf-8"))
            manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(envelope["gpts_validation"]["status"], "PASS")
            self.assertEqual(envelope["manifest_sha256"], file_sha(first / "manifest.json"))
            self.assertEqual(manifest["total_bytes"], one["total_bytes"])
            payload_file = first / envelope["files"][0]["path"]
            self.assertEqual(file_sha(payload_file), envelope["files"][0]["sha256"])

    def test_source_hash_mismatch_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            selection, _ = self.fixture(root)
            payload = root / "external-reality/v1/data/macroeconomy/sample.csv"
            payload.write_text("tampered\n", encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ComputeMaterialPackagerError, "integrity mismatch"):
                MODULE.build_package(
                    selection=selection,
                    source_root=root,
                    output_dir=root / "out",
                    source_repository_reference="hf-dataset:test/repo",
                )

    def test_gpts_selection_hash_mismatch_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            selection, _ = self.fixture(root)
            selection["decision_use"] = "changed after approval"
            with self.assertRaisesRegex(MODULE.ComputeMaterialPackagerError, "selection SHA256"):
                MODULE.build_package(
                    selection=selection,
                    source_root=root,
                    output_dir=root / "out",
                    source_repository_reference="hf-dataset:test/repo",
                )

    def test_expired_material_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            selection, record_path = self.fixture(root)
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["valid_to"] = "2026-07-31"
            record_path.write_text(json.dumps(record), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ComputeMaterialPackagerError, "expired"):
                MODULE.build_package(
                    selection=selection,
                    source_root=root,
                    output_dir=root / "out",
                    source_repository_reference="hf-dataset:test/repo",
                )

    def test_executable_payload_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            selection, record_path = self.fixture(root)
            script = root / "external-reality/v1/data/macroeconomy/run.py"
            script.write_text("print('x')\n", encoding="utf-8")
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["files"] = [{
                "path": "external-reality/v1/data/macroeconomy/run.py",
                "sha256": file_sha(script),
                "bytes": script.stat().st_size,
                "media_type": "application/json",
            }]
            record_path.write_text(json.dumps(record), encoding="utf-8")
            with self.assertRaises(MODULE.ComputeMaterialPackagerError):
                MODULE.build_package(
                    selection=selection,
                    source_root=root,
                    output_dir=root / "out",
                    source_repository_reference="hf-dataset:test/repo",
                )


if __name__ == "__main__":
    unittest.main()
