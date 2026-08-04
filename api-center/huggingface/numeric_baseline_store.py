#!/usr/bin/env python3
"""Validate and synchronize the pure-numeric Hugging Face compute baseline library."""
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
from huggingface_hub import CommitOperationAdd, HfApi, hf_hub_download

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
    "int8": pa.int8(), "int16": pa.int16(), "int32": pa.int32(), "int64": pa.int64(),
    "uint8": pa.uint8(), "uint16": pa.uint16(), "uint32": pa.uint32(), "uint64": pa.uint64(),
    "float32": pa.float32(), "float64": pa.float64(),
}


class NumericBaselineStoreError(RuntimeError):
    pass


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _sha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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
    if registry.get("private_dataset_required") is not True or registry.get("remote_root") != REMOTE_ROOT:
        raise NumericBaselineStoreError("private numeric storage contract mismatch")

    expected_encoding = {
        "format": "parquet", "compression": "zstd", "dictionary": False,
        "nulls": False, "categories": "integer_codes", "time": "int64",
        "control_metadata": "github-only",
    }
    encoding = registry.get("encoding")
    if not isinstance(encoding, Mapping) or any(encoding.get(k) != v for k, v in expected_encoding.items()):
        raise NumericBaselineStoreError("numeric encoding contract mismatch")
    if set(registry.get("allowed_types") or []) != set(TYPE_MAP):
        raise NumericBaselineStoreError("allowed numeric types mismatch")

    table_rows = registry.get("tables")
    if not isinstance(table_rows, list) or len(table_rows) != EXPECTED_TABLE_COUNT:
        raise NumericBaselineStoreError("numeric table registry must contain exactly 31 tables")
    tables: dict[str, list[tuple[str, pa.DataType]]] = {}
    for row in table_rows:
        if not isinstance(row, Mapping):
            raise NumericBaselineStoreError("numeric table row must be an object")
        table_id = str(row.get("id") or "")
        columns = row.get("columns")
        if not table_id or table_id in tables or not isinstance(columns, list) or not columns:
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
    blob_sha = str(catalog.get("git_blob_sha") or "")
    if len(blob_sha) != 40 or any(ch not in "0123456789abcdef" for ch in blob_sha):
        raise NumericBaselineStoreError("compute catalog Git blob SHA missing")

    expected_policy = {
        "numeric_payload_only": True, "text_columns_allowed": False,
        "object_columns_allowed": False, "null_values_allowed": False,
        "primary_format": "parquet-zstd", "control_metadata_storage": "github-only",
        "huggingface_control_json_allowed": False,
    }
    policy = matrix.get("payload_policy")
    if not isinstance(policy, Mapping) or any(policy.get(k) != v for k, v in expected_policy.items()):
        raise NumericBaselineStoreError("numeric payload policy mismatch")

    operation_rows = matrix.get("operations")
    if not isinstance(operation_rows, list) or len(operation_rows) != EXPECTED_OPERATION_COUNT:
        raise NumericBaselineStoreError("operation data matrix must cover exactly 29 operations")
    ids: list[str] = []
    referenced: set[str] = set()
    normalized_rows: list[dict[str, Any]] = []
    for row in operation_rows:
        if not isinstance(row, Mapping):
            raise NumericBaselineStoreError("operation data row must be an object")
        operation_id = str(row.get("operation_id") or "")
        required = [str(item) for item in row.get("required_tables") or []]
        if not operation_id or not required or len(required) != len(set(required)):
            raise NumericBaselineStoreError(f"invalid operation data row: {operation_id!r}")
        unknown = sorted(set(required) - set(tables))
        if unknown:
            raise NumericBaselineStoreError(
                f"operation {operation_id} references unknown tables: {', '.join(unknown)}"
            )
        ids.append(operation_id)
        referenced.update(required)
        normalized_rows.append({"operation_id": operation_id, "required_tables": required})
    if len(ids) != len(set(ids)):
        raise NumericBaselineStoreError("duplicate operation IDs in data matrix")
    unreferenced = sorted(set(tables) - referenced - {"provenance_index"})
    if unreferenced:
        raise NumericBaselineStoreError(
            f"numeric tables are not connected to any operation: {', '.join(unreferenced)}"
        )
    return {
        "registry": registry, "matrix": matrix, "tables": tables, "operations": normalized_rows,
        "registry_sha256": _sha(registry), "matrix_sha256": _sha(matrix),
    }


def _schema(columns: list[tuple[str, pa.DataType]]) -> pa.Schema:
    return pa.schema([pa.field(name, dtype, nullable=False) for name, dtype in columns])


def validate_numeric_parquet(
    path: Path,
    expected_columns: list[tuple[str, pa.DataType]],
    *,
    require_zero_rows: bool = False,
) -> dict[str, Any]:
    if path.suffix != ".parquet":
        raise NumericBaselineStoreError(f"non-Parquet payload rejected: {path.name}")
    actual = pq.read_schema(path)
    expected = _schema(expected_columns)
    if actual.names != expected.names:
        raise NumericBaselineStoreError(f"column mismatch: {path.name}")
    for got, wanted in zip(actual, expected):
        if got.type != wanted.type:
            raise NumericBaselineStoreError(f"type mismatch in {path.name}:{got.name}")
        if not (pa.types.is_integer(got.type) or pa.types.is_floating(got.type)):
            raise NumericBaselineStoreError(f"non-numeric Parquet column rejected: {path.name}:{got.name}")
    table = pq.read_table(path)
    if require_zero_rows and table.num_rows != 0:
        raise NumericBaselineStoreError(f"bootstrap table must contain zero rows: {path.name}")
    if any(column.null_count for column in table.columns):
        raise NumericBaselineStoreError(f"null values rejected: {path.name}")
    return {
        "rows": table.num_rows, "columns": table.num_columns,
        "bytes": path.stat().st_size, "sha256": _file_sha(path),
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
        schema = _schema(columns)
        table = pa.Table.from_arrays([pa.array([], type=f.type) for f in schema], schema=schema)
        path = data_dir / f"{table_id}.parquet"
        pq.write_table(
            table, path, compression="zstd", use_dictionary=False,
            write_statistics=True, version="2.6", data_page_version="2.0",
        )
        files.append({
            "table_id": table_id,
            "remote_path": f"{REMOTE_ROOT}/{table_id}.parquet",
            **validate_numeric_parquet(path, columns, require_zero_rows=True),
        })
    receipt = {
        "schema_version": "numeric-baseline-bootstrap-receipt-v1",
        "status": "NUMERIC_BASELINE_BOOTSTRAP_VALIDATED",
        "table_count": len(files), "operation_count": EXPECTED_OPERATION_COUNT,
        "managed_mode_count": EXPECTED_MANAGED_MODE_COUNT,
        "registry_sha256": control["registry_sha256"], "matrix_sha256": control["matrix_sha256"],
        "content_sha256": _sha([{"table_id": r["table_id"], "sha256": r["sha256"]} for r in files]),
        "files": files, "huggingface_payloads_numeric_only": True,
        "huggingface_control_json_uploaded": False, "compute_runtime_network_allowed": False,
        "direct_center_connection_allowed": False,
        "selection_and_relay_owner": "gpts-usage-center", "model_calls": 0,
    }
    _write_json(output_dir / "validation-receipt.json", receipt)
    return receipt


def plan_template_initialization(
    existing_files: set[str],
    bootstrap_files: list[Mapping[str, Any]],
) -> dict[str, Any]:
    expected = {str(row["remote_path"]): str(row["table_id"]) for row in bootstrap_files}
    visible = {path for path in existing_files if not path.startswith(".")}
    unexpected = sorted(visible - set(expected))
    if unexpected:
        raise NumericBaselineStoreError(
            "numeric-only dataset contains unexpected files: " + ", ".join(unexpected[:20])
        )
    missing = sorted(set(expected) - visible)
    return {
        "expected_paths": set(expected),
        "missing_paths": missing,
        "preserved_paths": sorted(visible),
        "path_to_table": expected,
    }


def _resolve_repo_id(api: HfApi, token: str) -> tuple[str, str]:
    identity = api.whoami(token=token)
    if not isinstance(identity, Mapping) or not identity.get("name"):
        raise NumericBaselineStoreError("Hugging Face identity could not be resolved")
    owner = str(identity["name"])
    repo_id = os.getenv(HF_REPO_ENV, "").strip() or f"{owner}/{DEFAULT_REPO_NAME}"
    parts = repo_id.split("/")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    if len(parts) != 2 or any(not p or any(ch not in allowed for ch in p) for p in parts):
        raise NumericBaselineStoreError("numeric baseline dataset repo must use safe owner/name")
    return repo_id, owner


def sync_private_library(output_dir: Path) -> dict[str, Any]:
    token = os.getenv(HF_TOKEN_ENV, "").strip()
    if not token:
        raise NumericBaselineStoreError("HF_TOKEN is required")
    bootstrap = build_bootstrap(output_dir)
    api = HfApi()
    repo_id, owner = _resolve_repo_id(api, token)
    api.create_repo(repo_id=repo_id, repo_type="dataset", private=True, exist_ok=True, token=token)
    info = api.repo_info(repo_id=repo_id, repo_type="dataset", token=token)
    if not bool(getattr(info, "private", False)):
        raise NumericBaselineStoreError("numeric baseline dataset must be private")

    existing = set(api.list_repo_files(repo_id=repo_id, repo_type="dataset", token=token))
    plan = plan_template_initialization(existing, bootstrap["files"])
    rows_by_path = {str(row["remote_path"]): row for row in bootstrap["files"]}
    operations = [
        CommitOperationAdd(
            path_in_repo=remote_path,
            path_or_fileobj=output_dir / "data" / f"{rows_by_path[remote_path]['table_id']}.parquet",
        )
        for remote_path in plan["missing_paths"]
    ]
    commit_oid = ""
    if operations:
        commit = api.create_commit(
            repo_id=repo_id, repo_type="dataset", operations=operations,
            commit_message="Initialize missing pure numeric compute baseline schemas", token=token,
        )
        commit_oid = str(getattr(commit, "oid", "") or "")

    control = validate_control_plane()
    verified: list[dict[str, Any]] = []
    initialized = set(plan["missing_paths"])
    for row in bootstrap["files"]:
        local = hf_hub_download(
            repo_id=repo_id, filename=row["remote_path"], repo_type="dataset",
            token=token, force_download=True,
        )
        checked = validate_numeric_parquet(
            Path(local), control["tables"][row["table_id"]], require_zero_rows=False
        )
        if row["remote_path"] in initialized and checked["sha256"] != row["sha256"]:
            raise NumericBaselineStoreError(f"initialized numeric template hash mismatch: {row['table_id']}")
        verified.append({"table_id": row["table_id"], **checked})

    visible = {
        path for path in api.list_repo_files(repo_id=repo_id, repo_type="dataset", token=token)
        if not path.startswith(".")
    }
    if visible != plan["expected_paths"] or any(not path.endswith(".parquet") for path in visible):
        raise NumericBaselineStoreError("remote numeric dataset file set mismatch")
    remote_content_sha = _sha([
        {"table_id": row["table_id"], "sha256": row["sha256"], "rows": row["rows"]}
        for row in sorted(verified, key=lambda item: item["table_id"])
    ])
    receipt = {
        **bootstrap,
        "status": "NUMERIC_BASELINE_LIBRARY_SYNCHRONIZED",
        "repository": repo_id,
        "repository_owner": owner,
        "private": True,
        "commit_oid": commit_oid,
        "verified_files": verified,
        "remote_file_count": len(visible),
        "remote_row_count": sum(int(row["rows"]) for row in verified),
        "initialized_file_count": len(plan["missing_paths"]),
        "preserved_file_count": len(plan["preserved_paths"]),
        "data_preserved_on_sync": True,
        "content_sha256": remote_content_sha,
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
        f"HF numeric baseline result: `{row.get('status', 'UNKNOWN')}`", "",
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
        lines += [
            f"- Private dataset: `{row['repository']}`",
            f"- Remote numeric files: `{row.get('remote_file_count', 0)}`",
            f"- Remote numeric rows: `{row.get('remote_row_count', 0)}`",
            f"- Newly initialized files: `{row.get('initialized_file_count', 0)}`",
            f"- Preserved existing files: `{row.get('preserved_file_count', 0)}`",
            f"- Existing data preserved on sync: `{str(bool(row.get('data_preserved_on_sync'))).lower()}`",
        ]
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
        message = str(exc).replace(token, "[REDACTED]") if token else str(exc)
        output_dir.mkdir(parents=True, exist_ok=True)
        _write_json(output_dir / "failure-receipt.json", {
            "status": "NUMERIC_BASELINE_FAILED",
            "error": message.replace("\n", " ")[:1600],
            "secret_values_exposed": False,
            "model_calls": 0,
        })
        print(message.replace("\n", " ")[:1600])
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
