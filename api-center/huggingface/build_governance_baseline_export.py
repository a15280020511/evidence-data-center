#!/usr/bin/env python3
"""Build a governance-ingestible pure-numeric baseline Artifact."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

SCHEMA_VERSION = "governance-baseline-export-v1"
PRODUCER_REPOSITORY = "a15280020511/evidence-data-center"
TABLE_ID_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
BATCH_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,120}$")


class ExportError(RuntimeError):
    pass


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _write_output(name: str, value: Any) -> None:
    target = os.getenv("GITHUB_OUTPUT", "")
    if not target:
        return
    normalized = str(value).replace("\r", " ").replace("\n", " ")
    with open(target, "a", encoding="utf-8") as handle:
        handle.write(f"{name}={normalized}\n")


def _validate_numeric(path: Path) -> tuple[pa.Table, dict[str, Any]]:
    schema = pq.read_schema(path)
    if not schema.names:
        raise ExportError(f"empty schema: {path}")
    for field in schema:
        if not (pa.types.is_integer(field.type) or pa.types.is_floating(field.type)):
            raise ExportError(f"non-numeric column rejected: {path.name}:{field.name}")
        if field.nullable:
            raise ExportError(f"nullable schema rejected: {path.name}:{field.name}")
    table = pq.read_table(path)
    if any(column.null_count for column in table.columns):
        raise ExportError(f"null values rejected: {path.name}")
    return table, {
        "rows": table.num_rows,
        "columns": table.num_columns,
        "bytes": path.stat().st_size,
        "sha256": _sha(path),
    }


def build(
    input_dir: Path,
    output_dir: Path,
    *,
    source_run_id: int,
    batch_id: str,
    mode: str,
) -> dict[str, Any]:
    if source_run_id <= 0:
        raise ExportError("source_run_id must be positive")
    if not BATCH_ID_RE.fullmatch(batch_id):
        raise ExportError("batch_id contains invalid characters")
    if mode not in {"append_batch", "replace_snapshot"}:
        raise ExportError("mode must be append_batch or replace_snapshot")
    source = input_dir.resolve()
    if not source.is_dir():
        raise ExportError("input directory does not exist")
    parquet_files = sorted(path for path in source.rglob("*.parquet") if path.is_file())
    if not 1 <= len(parquet_files) <= 256:
        raise ExportError("export must contain 1 to 256 Parquet parts")

    grouped: dict[str, list[pa.Table]] = defaultdict(list)
    part_count: dict[str, int] = defaultdict(int)
    for source_path in parquet_files:
        table_id = source_path.stem
        if not TABLE_ID_RE.fullmatch(table_id):
            raise ExportError(f"invalid table id: {table_id}")
        table, _ = _validate_numeric(source_path)
        if grouped[table_id] and grouped[table_id][0].schema != table.schema:
            raise ExportError(f"schema mismatch between parts for table: {table_id}")
        grouped[table_id].append(table)
        part_count[table_id] += 1
    if len(grouped) > 64:
        raise ExportError("export must contain at most 64 unique tables")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    rows: list[dict[str, Any]] = []
    for table_id in sorted(grouped):
        tables = grouped[table_id]
        table = tables[0] if len(tables) == 1 else pa.concat_tables(tables, promote_options="none")
        target = output_dir / f"{table_id}.parquet"
        pq.write_table(
            table,
            target,
            compression="zstd",
            use_dictionary=False,
            write_statistics=True,
            version="2.6",
            data_page_version="2.0",
        )
        _, normalized = _validate_numeric(target)
        rows.append(
            {
                "table_id": table_id,
                "path": target.name,
                "sha256": normalized["sha256"],
                "rows": normalized["rows"],
                "columns": normalized["columns"],
                "bytes": normalized["bytes"],
                "source_part_count": part_count[table_id],
            }
        )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "producer_repository": PRODUCER_REPOSITORY,
        "source_run_id": source_run_id,
        "batch_id": batch_id,
        "mode": mode,
        "numeric_only": True,
        "raw_text_included": False,
        "control_json_for_hf": False,
        "files": rows,
        "secret_values_exposed": False,
        "model_calls": 0,
    }
    manifest_path = output_dir / "manifest.json"
    _dump(manifest_path, manifest)
    receipt = {
        "status": "GOVERNANCE_BASELINE_EXPORT_READY",
        "source_run_id": source_run_id,
        "batch_id": batch_id,
        "mode": mode,
        "source_part_count": len(parquet_files),
        "file_count": len(rows),
        "row_count": sum(row["rows"] for row in rows),
        "manifest_sha256": _sha(manifest_path),
        "artifact_name": f"compute-baseline-export-{batch_id}-{source_run_id}",
        "storage_gateway": "a15280020511/decision-system-governance",
        "direct_huggingface_write": False,
        "secret_values_exposed": False,
        "model_calls": 0,
    }
    _dump(output_dir.parent / f"{output_dir.name}-receipt.json", receipt)
    for key in (
        "manifest_sha256",
        "artifact_name",
        "batch_id",
        "source_part_count",
        "file_count",
        "row_count",
    ):
        _write_output(key, receipt[key])
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--source-run-id", type=int, required=True)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--mode", choices=["append_batch", "replace_snapshot"], default="append_batch")
    args = parser.parse_args()
    try:
        result = build(
            Path(args.input_dir),
            Path(args.output_dir),
            source_run_id=args.source_run_id,
            batch_id=args.batch_id,
            mode=args.mode,
        )
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
