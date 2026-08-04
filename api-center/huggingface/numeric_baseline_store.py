#!/usr/bin/env python3
"""Build, validate and synchronize the pure-numeric Hugging Face baseline library.

Only numeric Parquet payloads are uploaded to Hugging Face. Human-readable control
metadata stays in GitHub. The Compute Center remains network-denied and receives
only GPT-selected immutable artifacts through the usage center.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any, Mapping

import pyarrow as pa
import pyarrow.parquet as pq
from huggingface_hub import CommitOperationAdd, CommitOperationDelete, HfApi, hf_hub_download

HERE = Path(__file__).resolve().parent
CONTROL_ROOT = HERE / "numeric-baseline-library"
REGISTRY_PATH = CONTROL_ROOT / "numeric-table-registry.json"
MATRIX_PATH = CONTROL_ROOT / "operation-data-matrix.json"

HF_TOKEN_ENV = "HF_TOKEN"
HF_REPO_ENV = "HF_NUMERIC_BASELINE_DATASET_REPO"
DEFAULT_REPO_NAME = "compute-numeric-baselines"
REMOTE_ROOT = "numeric-baselines/v1/data"
EXPECTED_OPERATION_COUNT = 29
EXPECTED_MANAGED_MODE_COUNT = 185
EXPECTED_TABLE_COUNT = 31

TYPE_MAP = {
    "int8": pa.int8(),
    "int16": pa.int16(),
    "int32": pa.int32(),
    "int64": pa.int64(),
    "uint8": pa.uint8(),
    "uint16": pa.uint16(),
    "uint32": pa.uint32(),
    "uint64": pa.uint64(),
    "float32": pa.float32(),
    "float64": pa.float64(),
}


class NumericBaselineStoreError(RuntimeError):
    """Raised when the numeric baseline contract or payload is invalid."""


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _canonical_sha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _redact(message: str, token: str) -> str:
    text = str(message)
    if token:
        text = text.replace(token, "[REDACTED]")
    return text.replace("\n", " ")[:1600]


def _parse_column(spec: str) -> tuple[str, pa.DataType]:
    if not isinstance(spec, str) or spec.count(":") != 1:
        raise NumericBaselineStoreError(f"invalid column specification: {spec!r}")
    name, type_name = spec.split(":", 1)
    if not name or not name.replace("_", "").isalnum() or name[0].isdigit():
        raise NumericBaselineStoreError(f"invalid numeric column name: {name!r}")
    if type_name not in TYPE_MAP:
        raise NumericBaselineStoreError(f"non-numeric or unsupported type: {type_name!r}")
    return name, TYPE_MAP[type_name]


def validate_control_plane(
    registry: Mapping[str, Any] | None = None,
    matrix: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    registry = registry or _load_json(REGISTRY_PATH)
    matrix = matrix or _load_json(MATRIX_PATH)

    if registry.get("schema_version") != "numeric-baseline-table-registry-v1":
        raise NumericBaselineStoreError("unsupported numeric table registry")
    if registry.get("status") != "production-control":
        raise NumericBaselineStoreError("numeric table registry is not production-control")
    if registry.get("private_dataset_required") is not True:
        raise NumericBaselineStoreError("numeric baseline dataset must remain private")
    if registry.get("remote_root") != REMOTE_ROOT:
        raise NumericBaselineStoreError("numeric baseline remote root mismatch")

    encoding = registry.get("encoding")
    if not isinstance(encoding, Mapping):
        raise NumericBaselineStoreError("numeric encoding contract missing")
    required_encoding = {
        "format": "parquet",
        "compression": "zstd",
        "dictionary": False,
        "nulls": False,
        "categories": "integer_codes",
        "time": "int64",
        "control_metadata": "github-only",
    }
    for key, expected in required_encoding.items():
        if encoding.get(key) != expected:
            raise NumericBaselineStoreError(f"invalid numeric encoding policy: {key}")

    allowed = registry.get("allowed_types")
    if not isinstance(allowed, list) or set(allowed) != set(TYPE_MAP):
        raise NumericBaselineStoreError("allowed numeric types do not match implementation")

    raw_tables = registry.get("tables")
    if not isinstance(raw_tables, list) or len(raw_tables) != EXPECTED_TABLE_COUNT:
        raise NumericBaselineStoreError("numeric table registry must contain exactly 31 tables")

    tables: dict[str, list[tuple[str, pa.DataType]]] = {}
    for row in raw_tables:
        if not isinstance(row, Mapping):
            raise NumericBaselineStoreError("numeric table row must be an object")
        table_id = str(row.get("id") or "")
        columns = row.get("columns")
        if (
            not table_id
            or not table_id.replace("_", "").isalnum()
            or not isinstance(columns, list)
            or not columns
            or table_id in tables
        ):
            raise NumericBaselineStoreError(f"invalid or duplicate numeric table: {table_id!r}")
        parsed = [_parse_column(item) for item in columns]
        names = [name for name, _ in parsed]
        if len(names) != len(set(names)):
            raise NumericBaselineStoreError(f"duplicate columns in table {table_id}")
        if table_id != "provenance_index" and "provenance_id" not in names:
            raise NumericBaselineStoreError(f"table {table_id} lacks numeric provenance_id")
        tables[table_id] = parsed

    if "provenance_index" not in tables:
        raise NumericBaselineStoreError("numeric provenance table is required")

    if matrix.get("schema_version") != "compute-numeric-data-matrix-v1":
        raise NumericBaselineStoreError("unsupported operation data matrix")
    if matrix.get("status") != "production-control":
        raise NumericBaselineStoreError("operation data matrix is not production-control")
    if matrix.get("compute_runtime_network_allowed") is not False:
        raise NumericBaselineStoreError("compute runtime network must remain denied")
    if matrix.get("direct_center_to_center_connection_allowed") is not False:
        raise NumericBaselineStoreError("direct center-to-center transfer is forbidden")
    if matrix.get("selection_and_relay_owner") != "gpts-usage-center":
        raise NumericBaselineStoreError("GPTs usage center must own selection and relay")

    catalog = matrix.get("compute_catalog")
    if not isinstance(catalog, Mapping):
        raise NumericBaselineStoreError("compute catalog snapshot missing")
    if int(catalog.get("operation_count") or 0) != EXPECTED_OPERATION_COUNT:
        raise NumericBaselineStoreError("compute operation count mismatch")
    if int(catalog.get("effective_managed_mode_count") or 0) != EXPECTED_MANAGED_MODE_COUNT:
        raise NumericBaselineStoreError("compute managed mode count mismatch")
    if len(str(catalog.get("sha256") or "")) != 64:
        raise NumericBaselineStoreError("compute catalog hash missing")

    policy = matrix.get("payload_policy")
    required_policy = {
        "numeric_payload_only": True,
        "text_columns_allowed": False,
        "object_columns_allowed": False,
        "null_values_allowed": False,
        "primary_format": "parquet-zstd",
        "control_metadata_storage": "github-only",
        "huggingface_control_json_allowed": False,
    }
    if not isinstance(policy, Mapping):
        raise NumericBaselineStoreError("numeric payload policy missing")
    for key, expected in required_policy.items():
        if policy.get(key) != expected:
            raise NumericBaselineStoreError(f"invalid numeric payload policy: {key}")

    operations = matrix.get("operations")
    if not isinstance(operations, list) or len(operations) != EXPECTED_OPERATION_COUNT:
        raise NumericBaselineStoreError("operation data matrix must cover exactly 29 operations")
    operation_ids: list[str] = []
    referenced_tables: set[str] = set()
    operation_rows: list[dict[str, Any]] = []
    for row in operations:
        if not isinstance(row, Mapping):
            raise NumericBaselineStoreError("operation data row must be an object")
        operation_id = str(row.get("operation_id") or "")
        required_tables = row.get("required_tables")
        if not operation_id or not isinstance(required_tables, list) or not required_tables:
            raise NumericBaselineStoreError(f"invalid operation data row: {operation_id!r}")
        normalized = [str(item) for item in required_tables]
        if len(normalized) != len(set(normalized)):
            raise NumericBaselineStoreError(f"duplicate table requirement for {operation_id}")
        unknown = sorted(set(normalized) - set(tables))
        if unknown:
            raise NumericBaselineStoreError(
                f"operation {operation_id} references unknown tables: {', '.join(unknown)}"
            )
        operation_ids.append(operation_id)
        referenced_tables.update(normalized)
        operation_rows.append({"operation_id": operation_id, "required_tables": normalized})
    if len(operation_ids) != len(set(operation_ids)):
        raise NumericBaselineStoreError("duplicate operation IDs in data matrix")

    unreferenced = sorted(set(tables) - referenced_tables - {"provenance_index"})
    if unreferenced:
        raise NumericBaselineStoreError(
            f"numeric tables are not connected to any operation: {', '.join(unreferenced)}"
        )

    return {
        "registry": registry,
        "matrix": matrix,
        "tables": tables,
        "operations": operation_rows,
        "registry_sha256": _canonical_sha(registry),
        "matrix_sha256": _canonical_sha(matrix),
    }


def _schema_for(columns: list[tuple[str, pa.DataType]]) -> pa.Schema:
    return pa.schema([pa.field(name, data_type, nullable=False) for name, data_type in columns])


def validate_numeric_parquet(
    path: Path,
    expected_columns: list[tuple[str, pa.DataType]],
    *,
    require_zero_rows: bool = False,
) -> dict[str, Any]:
    if path.suffix != ".parquet":
        raise NumericBaselineStoreError(f"non-Parquet payload rejected: {path.name}")
    schema = pq.read_schema(path)
    expected = _schema_for(expected_columns)
    if schema.names != expected.names:
        raise NumericBaselineStoreError(f"column mismatch: {path.name}")
    for actual_field, expected_field in zip(schema, expected):
        if actual_field.type != expected_field.type:
            raise NumericBaselineStoreError(
                f"type mismatch in {path.name}:{actual_field.name}: "
                f"{actual_field.type} != {expected_field.type}"
            )
        if not (pa.types.is_integer(actual_field.type) or pa.types.is_floating(actual_field.type)):
            raise NumericBaselineStoreError(
                f"non-numeric Parquet column rejected: {path.name}:{actual_field.name}"
            )
    table = pq.read_table(path)
    if require_zero_rows and table.num_rows != 0:
        raise NumericBaselineStoreError(f"bootstrap table must contain zero rows: {path.name}")
    for column in table.columns:
        if column.null_count:
            raise NumericBaselineStoreError(f"null values rejected: {path.name}")
    return {
        "rows": table.num_rows,
        "columns": table.num_columns,
        "bytes": path.stat().st_size,
        "sha256": _file_sha(path),
    }


def build_bootstrap(output_dir: Path) -> dict[str, Any]:
    control = validate_control_plane()
    if output_dir.exists():
        shutil.rmtree(output_dir)
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True)

    files: list[dict[str, Any]] = []
    for table_id in sorted(control["tables"]):
        columns = control["tables"][table_id]
        schema = _schema_for(columns)
        arrays = [pa.array([], type=field.type) for field in schema]
        table = pa.Table.from_arrays(arrays, schema=schema)
        path = data_dir / f"{table_id}.parquet"
        pq.write_table(
            table,
            path,
            compression="zstd",
            use_dictionary=False,
            write_statistics=True,
            version="2.6",
            data_page_version="2.0",
        )
        validation = validate_numeric_parquet(path, columns, require_zero_rows=True)
        files.append(
            {
                "table_id": table_id,
                "remote_path": f"{REMOTE_ROOT}/{table_id}.parquet",
                **validation,
            }
        )

    manifest = {
        "schema_version": "numeric-baseline-bootstrap-receipt-v1",
        "status": "NUMERIC_BASELINE_BOOTSTRAP_VALIDATED",
        "table_count": len(files),
        "operation_count": EXPECTED_OPERATION_COUNT,
        "managed_mode_count": EXPECTED_MANAGED_MODE_COUNT,
        "registry_sha256": control["registry_sha256"],
        "matrix_sha256": control["matrix_sha256"],
        "content_sha256": _canonical_sha(
            [{"table_id": row["table_id"], "sha256": row["sha256"]} for row in files]
        ),
        "files": files,
        "huggingface_payloads_numeric_only": True,
        "huggingface_control_json_uploaded": False,
        "compute_runtime_network_allowed": False,
        "direct_center_connection_allowed": False,
        "selection_and_relay_owner": "gpts-usage-center",
        "model_calls": 0,
    }
    _write_json(output_dir / "validation-receipt.json", manifest)
    return manifest


def _resolve_repo_id(api: HfApi, token: str, override: str | None) -> tuple[str, str]:
    identity = api.whoami(token=token)
    if not isinstance(identity, Mapping) or not identity.get("name"):
        raise NumericBaselineStoreError("Hugging Face identity could not be resolved")
    owner = str(identity["name"])
    requested = str(override or "").strip()
    repo_id = requested or f"{owner}/{DEFAULT_REPO_NAME}"
    parts = repo_id.split("/")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    if len(parts) != 2 or any(not part or any(ch not in allowed for ch in part) for part in parts):
        raise NumericBaselineStoreError("numeric baseline dataset repo must use safe owner/name")
    return repo_id, owner


def sync_private_library(output_dir: Path) -> dict[str, Any]:
    token = os.getenv(HF_TOKEN_ENV, "").strip()
    if not token:
        raise NumericBaselineStoreError("HF_TOKEN is required")
    bootstrap = build_bootstrap(output_dir)
    api = HfApi()
    repo_id, owner = _resolve_repo_id(api, token, os.getenv(HF_REPO_ENV))
    api.create_repo(repo_id=repo_id, repo_type="dataset", private=True, exist_ok=True, token=token)

    info = api.repo_info(repo_id=repo_id, repo_type="dataset", token=token)
    if not bool(getattr(info, "private", False)):
        raise NumericBaselineStoreError("numeric baseline dataset must be private")

    expected_paths = {row["remote_path"] for row in bootstrap["files"]}
    existing = set(api.list_repo_files(repo_id=repo_id, repo_type="dataset", token=token))
    unexpected = sorted(
        path for path in existing
        if path not in expected_paths and not path.startswith(".")
    )
    if unexpected:
        raise NumericBaselineStoreError(
            "numeric-only dataset contains unexpected non-baseline files: "
            + ", ".join(unexpected[:20])
        )

    operations: list[Any] = []
    for path in sorted(existing - expected_paths):
        if path.startswith("."):
            continue
        operations.append(CommitOperationDelete(path_in_repo=path))
    for row in bootstrap["files"]:
        operations.append(
            CommitOperationAdd(
                path_in_repo=row["remote_path"],
                path_or_fileobj=output_dir / "data" / f"{row['table_id']}.parquet",
            )
        )
    commit = api.create_commit(
        repo_id=repo_id,
        repo_type="dataset",
        operations=operations,
        commit_message="Initialize pure numeric compute baseline schemas",
        token=token,
    )

    verified: list[dict[str, Any]] = []
    control = validate_control_plane()
    for row in bootstrap["files"]:
        local = hf_hub_download(
            repo_id=repo_id,
            filename=row["remote_path"],
            repo_type="dataset",
            token=token,
            force_download=True,
        )
        validation = validate_numeric_parquet(
            Path(local), control["tables"][row["table_id"]], require_zero_rows=True
        )
        if validation["sha256"] != row["sha256"]:
            raise NumericBaselineStoreError(
                f"remote numeric payload hash mismatch: {row['table_id']}"
            )
        verified.append({"table_id": row["table_id"], **validation})

    remote_files = set(api.list_repo_files(repo_id=repo_id, repo_type="dataset", token=token))
    visible_payloads = {path for path in remote_files if not path.startswith(".")}
    if visible_payloads != expected_paths:
        raise NumericBaselineStoreError("remote numeric dataset file set mismatch")
    if any(not path.endswith(".parquet") for path in visible_payloads):
        raise NumericBaselineStoreError("non-Parquet content detected in numeric dataset")

    receipt = {
        **bootstrap,
        "status": "NUMERIC_BASELINE_LIBRARY_SYNCHRONIZED",
        "repository": repo_id,
        "repository_owner": owner,
        "private": True,
        "commit_oid": str(getattr(commit, "oid", "") or ""),
        "verified_files": verified,
        "remote_file_count": len(visible_payloads),
        "secret_values_exposed": False,
    }
    _write_json(output_dir / "sync-receipt.json", receipt)
    return receipt


def render_receipt(output_dir: Path) -> str:
    path = output_dir / "sync-receipt.json"
    if not path.exists():
        path = output_dir / "validation-receipt.json"
    if not path.exists():
        return "HF numeric baseline result: `NO_RECEIPT`\n"
    row = _load_json(path)
    lines = [
        f"HF numeric baseline result: `{row.get('status', 'UNKNOWN')}`",
        "",
        f"- Numeric table families: `{row.get('table_count', 0)}`",
        f"- Compute operations covered: `{row.get('operation_count', 0)}`",
        f"- Managed modes covered: `{row.get('managed_mode_count', 0)}`",
        f"- Numeric-only payloads: `{str(bool(row.get('huggingface_payloads_numeric_only'))).lower()}`",
        f"- HF control JSON uploaded: `{str(bool(row.get('huggingface_control_json_uploaded'))).lower()}`",
        f"- Compute network allowed: `{str(bool(row.get('compute_runtime_network_allowed'))).lower()}`",
        f"- Direct center connection allowed: `{str(bool(row.get('direct_center_connection_allowed'))).lower()}`",
        f"- GPTs relay owner: `{row.get('selection_and_relay_owner', '')}`",
        f"- Content SHA256: `{row.get('content_sha256', '')}`",
    ]
    if row.get("repository"):
        lines.append(f"- Private dataset: `{row['repository']}`")
        lines.append(f"- Remote numeric files: `{row.get('remote_file_count', 0)}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("validate", "sync", "render"))
    parser.add_argument("--output-dir", default="hf-numeric-baseline-output")
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    try:
        if args.command == "validate":
            build_bootstrap(output_dir)
        elif args.command == "sync":
            sync_private_library(output_dir)
        else:
            print(render_receipt(output_dir), end="")
        return 0
    except Exception as exc:
        token = os.getenv(HF_TOKEN_ENV, "")
        output_dir.mkdir(parents=True, exist_ok=True)
        _write_json(
            output_dir / "failure-receipt.json",
            {
                "status": "NUMERIC_BASELINE_FAILED",
                "error": _redact(str(exc), token),
                "secret_values_exposed": False,
                "model_calls": 0,
            },
        )
        print(_redact(str(exc), token))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
