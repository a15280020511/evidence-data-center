from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

MODULE_PATH = Path(__file__).resolve().parents[1] / "build_governance_baseline_export.py"
SPEC = importlib.util.spec_from_file_location("build_governance_baseline_export", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class GovernanceBaselineExportTests(unittest.TestCase):
    def test_numeric_export_builds_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            schema = pa.schema(
                [
                    pa.field("provenance_id", pa.uint64(), nullable=False),
                    pa.field("value", pa.float64(), nullable=False),
                ]
            )
            table = pa.Table.from_arrays(
                [pa.array([1], type=pa.uint64()), pa.array([3.5], type=pa.float64())],
                schema=schema,
            )
            pq.write_table(table, source / "observations.parquet", compression="zstd", use_dictionary=False)
            receipt = MODULE.build(
                source,
                root / "export",
                source_run_id=123,
                batch_id="batch-123",
                mode="append_batch",
            )
            self.assertEqual(receipt["status"], "GOVERNANCE_BASELINE_EXPORT_READY")
            self.assertFalse(receipt["direct_huggingface_write"])
            manifest = json.loads((root / "export" / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["producer_repository"], "a15280020511/evidence-data-center")
            self.assertTrue(manifest["numeric_only"])
            self.assertFalse(manifest["raw_text_included"])
            self.assertEqual(manifest["files"][0]["table_id"], "observations")

    def test_text_column_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            schema = pa.schema([pa.field("text", pa.string(), nullable=False)])
            table = pa.Table.from_arrays([pa.array(["bad"], type=pa.string())], schema=schema)
            pq.write_table(table, source / "observations.parquet")
            with self.assertRaisesRegex(MODULE.ExportError, "non-numeric column"):
                MODULE.build(
                    source,
                    root / "export",
                    source_run_id=123,
                    batch_id="batch-123",
                    mode="append_batch",
                )

    def test_nullable_schema_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            pq.write_table(pa.table({"value": [1.0]}), source / "observations.parquet")
            with self.assertRaisesRegex(MODULE.ExportError, "nullable schema"):
                MODULE.build(
                    source,
                    root / "export",
                    source_run_id=123,
                    batch_id="batch-123",
                    mode="append_batch",
                )


if __name__ == "__main__":
    unittest.main()
