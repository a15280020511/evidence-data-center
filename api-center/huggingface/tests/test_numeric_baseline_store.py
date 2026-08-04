from __future__ import annotations

import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

MODULE_PATH = Path(__file__).resolve().parents[1] / "numeric_baseline_store.py"
SPEC = importlib.util.spec_from_file_location("numeric_baseline_store", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class NumericBaselineStoreTests(unittest.TestCase):
    def test_control_plane_covers_entire_compute_catalog(self) -> None:
        result = MODULE.validate_control_plane()
        self.assertEqual(len(result["operations"]), 29)
        self.assertEqual(len(result["tables"]), 31)
        self.assertEqual(
            result["matrix"]["compute_catalog"]["effective_managed_mode_count"], 185
        )
        self.assertFalse(result["matrix"]["compute_runtime_network_allowed"])
        self.assertFalse(
            result["matrix"]["direct_center_to_center_connection_allowed"]
        )
        self.assertEqual(
            result["matrix"]["selection_and_relay_owner"], "gpts-usage-center"
        )

    def test_bootstrap_is_deterministic_and_numeric_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = MODULE.build_bootstrap(root / "first")
            second = MODULE.build_bootstrap(root / "second")
            self.assertEqual(first["content_sha256"], second["content_sha256"])
            self.assertEqual(first["table_count"], 31)
            self.assertEqual(first["operation_count"], 29)
            self.assertEqual(first["managed_mode_count"], 185)
            self.assertTrue(first["huggingface_payloads_numeric_only"])
            self.assertFalse(first["huggingface_control_json_uploaded"])
            self.assertFalse(first["compute_runtime_network_allowed"])
            self.assertFalse(first["direct_center_connection_allowed"])
            self.assertEqual(
                [row["sha256"] for row in first["files"]],
                [row["sha256"] for row in second["files"]],
            )
            for row in first["files"]:
                path = root / "first" / "data" / f"{row['table_id']}.parquet"
                schema = pq.read_schema(path)
                self.assertGreater(len(schema), 0)
                table = pq.read_table(path)
                self.assertEqual(table.num_rows, 0)
                for field in schema:
                    self.assertTrue(
                        pa.types.is_integer(field.type)
                        or pa.types.is_floating(field.type)
                    )

    def test_text_column_contract_is_rejected(self) -> None:
        registry = copy.deepcopy(MODULE._load_json(MODULE.REGISTRY_PATH))
        registry["tables"][0]["columns"].append("raw_text:string")
        with self.assertRaisesRegex(
            MODULE.NumericBaselineStoreError, "non-numeric or unsupported type"
        ):
            MODULE.validate_control_plane(
                registry=registry, matrix=MODULE._load_json(MODULE.MATRIX_PATH)
            )

    def test_missing_compute_operation_is_rejected(self) -> None:
        matrix = copy.deepcopy(MODULE._load_json(MODULE.MATRIX_PATH))
        matrix["operations"].pop()
        with self.assertRaisesRegex(
            MODULE.NumericBaselineStoreError, "exactly 29 operations"
        ):
            MODULE.validate_control_plane(
                registry=MODULE._load_json(MODULE.REGISTRY_PATH), matrix=matrix
            )

    def test_unknown_table_reference_is_rejected(self) -> None:
        matrix = copy.deepcopy(MODULE._load_json(MODULE.MATRIX_PATH))
        matrix["operations"][0]["required_tables"].append("raw_documents")
        with self.assertRaisesRegex(
            MODULE.NumericBaselineStoreError, "unknown tables"
        ):
            MODULE.validate_control_plane(
                registry=MODULE._load_json(MODULE.REGISTRY_PATH), matrix=matrix
            )

    def test_string_parquet_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.parquet"
            pq.write_table(pa.table({"value": ["text"]}), path)
            with self.assertRaises(MODULE.NumericBaselineStoreError):
                MODULE.validate_numeric_parquet(path, [("value", pa.float64())])

    def test_null_numeric_payload_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "null.parquet"
            pq.write_table(
                pa.Table.from_arrays(
                    [pa.array([1.0, None], type=pa.float64())],
                    names=["value"],
                ),
                path,
                compression="zstd",
            )
            with self.assertRaisesRegex(
                MODULE.NumericBaselineStoreError, "null values rejected"
            ):
                MODULE.validate_numeric_parquet(path, [("value", pa.float64())])

    def test_render_receipt_has_architecture_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            MODULE.build_bootstrap(root)
            rendered = MODULE.render_receipt(root)
            self.assertIn("Numeric-only payloads: `true`", rendered)
            self.assertIn("HF control JSON uploaded: `false`", rendered)
            self.assertIn("Compute network allowed: `false`", rendered)
            self.assertIn("Direct center connection allowed: `false`", rendered)
            self.assertIn("GPTs relay owner: `gpts-usage-center`", rendered)


if __name__ == "__main__":
    unittest.main()
