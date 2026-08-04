#!/usr/bin/env python3
"""Build immutable, GPTs-approved compute material packages in the Intelligence Center.

This module may read the private Hugging Face Dataset only inside the managed
Evidence Center workflow. It never dispatches the Compute Center and never
changes Compute Center state. The output is a self-contained GitHub Actions
Artifact that GPTs must retrieve and relay as complete bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from huggingface_hub import HfApi, hf_hub_download
from jsonschema import Draft202012Validator, FormatChecker

HERE = Path(__file__).resolve().parent
SOURCE_SCHEMA_PATH = HERE / "compute-material-packaging" / "source-record.schema.json"
HF_TOKEN_ENV = "HF_TOKEN"
HF_REPO_ENV = "HF_DOMAIN_BENCHMARK_DATASET_REPO"
HF_FALLBACK_REPO_ENV = "HF_CLOUDFLARE_DATASET_REPO"
DEFAULT_REPO_NAME = "cloudflare-intelligence-archive"
ALLOWED_SOURCE_ROOTS = {"external-reality/v1", "domain-benchmarks/v1"}
ALLOWED_MATERIAL_TYPES = {
    "sample_snapshot",
    "factor_definition_snapshot",
    "domain_rule_snapshot",
    "baseline_evidence_snapshot",
    "metric_threshold_snapshot",
    "ontology_crosswalk_snapshot",
    "regime_event_snapshot",
    "outcome_feedback_snapshot",
    "benchmark_manifest",
}
ALLOWED_MEDIA_TYPES = {
    "application/json": {".json"},
    "application/x-ndjson": {".jsonl", ".ndjson"},
    "text/csv": {".csv"},
    "application/vnd.apache.parquet": {".parquet"},
    "application/vnd.apache.arrow.file": {".arrow", ".feather"},
    "application/geo+json": {".geojson", ".json"},
    "application/geopackage+sqlite3": {".gpkg"},
}
FORBIDDEN_SUFFIXES = {
    ".py", ".pyc", ".pyo", ".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd",
    ".js", ".mjs", ".cjs", ".exe", ".dll", ".so", ".dylib", ".jar", ".war",
    ".whl", ".zip", ".tar", ".tgz", ".gz", ".bz2", ".xz", ".7z",
}
MAX_FILE_BYTES = 2_000_000_000
MAX_TOTAL_BYTES = 10_000_000_000


class ComputeMaterialPackagerError(RuntimeError):
    """Raised when source records or package contents are not decision-safe."""


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


def _safe_relative(value: str, label: str) -> PurePosixPath:
    path = PurePosixPath(str(value))
    if not value or path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise ComputeMaterialPackagerError(f"unsafe {label}: {value!r}")
    if any(part in {"", ".git"} for part in path.parts):
        raise ComputeMaterialPackagerError(f"unsafe {label}: {value!r}")
    return path


def _parse_date(value: Any, label: str, *, nullable: bool = False) -> date | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str):
        raise ComputeMaterialPackagerError(f"{label} must be an ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ComputeMaterialPackagerError(f"invalid {label}: {value}") from exc


def _parse_datetime(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        raise ComputeMaterialPackagerError(f"{label} must be an ISO datetime")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ComputeMaterialPackagerError(f"invalid {label}: {value}") from exc
    if parsed.tzinfo is None:
        raise ComputeMaterialPackagerError(f"{label} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _validator() -> Draft202012Validator:
    schema = _load_json(SOURCE_SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _validate_source_record(
    record: Mapping[str, Any],
    *,
    record_path: str,
    expected_material_type: str,
    as_of: date,
) -> None:
    errors = sorted(_validator().iter_errors(record), key=lambda item: list(item.absolute_path))
    if errors:
        first = errors[0]
        where = ".".join(str(item) for item in first.absolute_path) or "$"
        raise ComputeMaterialPackagerError(f"{record_path}: {where}: {first.message}")
    if record.get("material_type") != expected_material_type:
        raise ComputeMaterialPackagerError(
            f"{record_path}: material_type does not match package selection"
        )
    if "compute-analysis" not in record["license"]["use_scope"]:
        raise ComputeMaterialPackagerError(f"{record_path}: license excludes compute-analysis")
    valid_from = _parse_date(record.get("valid_from"), "valid_from", nullable=True)
    valid_to = _parse_date(record.get("valid_to"), "valid_to", nullable=True)
    if valid_from and valid_to and valid_to < valid_from:
        raise ComputeMaterialPackagerError(f"{record_path}: valid_to precedes valid_from")
    if valid_to and valid_to < as_of:
        raise ComputeMaterialPackagerError(f"{record_path}: source material is expired")
    review_due = _parse_date(record.get("review_due_at"), "review_due_at")
    if review_due < as_of:
        raise ComputeMaterialPackagerError(f"{record_path}: source review is overdue")
    root = str(record.get("source_root") or "")
    if root not in ALLOWED_SOURCE_ROOTS:
        raise ComputeMaterialPackagerError(f"{record_path}: unsupported source_root")
    for row in record["files"]:
        source_path = _safe_relative(str(row["path"]), "source file path")
        if not str(source_path).startswith(root + "/"):
            raise ComputeMaterialPackagerError(
                f"{record_path}: source file is outside declared source_root"
            )
        suffix = source_path.suffix.lower()
        if suffix in FORBIDDEN_SUFFIXES:
            raise ComputeMaterialPackagerError(f"{record_path}: executable/archive file forbidden")
        media_type = str(row["media_type"])
        if suffix not in ALLOWED_MEDIA_TYPES[media_type]:
            raise ComputeMaterialPackagerError(
                f"{record_path}: media type does not match file extension"
            )
        if int(row["bytes"]) > MAX_FILE_BYTES:
            raise ComputeMaterialPackagerError(f"{record_path}: source file exceeds size limit")


def _validate_selection(selection: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "package_id", "task_id", "material_type", "version", "created_at",
        "record_paths", "valid_from", "valid_to", "geographic_scope",
        "time_range", "decision_use", "gpts_validation",
    }
    missing = sorted(required - set(selection))
    if missing:
        raise ComputeMaterialPackagerError(f"selection fields missing: {', '.join(missing)}")
    package_id = str(selection["package_id"])
    task_id = str(selection["task_id"])
    for label, value in (("package_id", package_id), ("task_id", task_id)):
        if len(value) < 8 or len(value) > 128 or not all(
            ch.isalnum() or ch in "._:-" for ch in value
        ):
            raise ComputeMaterialPackagerError(f"invalid {label}")
    material_type = str(selection["material_type"])
    if material_type not in ALLOWED_MATERIAL_TYPES:
        raise ComputeMaterialPackagerError("unsupported material_type")
    created_at = _parse_datetime(selection["created_at"], "created_at")
    valid_from = _parse_date(selection["valid_from"], "valid_from", nullable=True)
    valid_to = _parse_date(selection["valid_to"], "valid_to", nullable=True)
    if valid_from and valid_to and valid_to < valid_from:
        raise ComputeMaterialPackagerError("selection valid_to precedes valid_from")
    records = selection["record_paths"]
    if not isinstance(records, list) or not records or len(records) > 200:
        raise ComputeMaterialPackagerError("record_paths must contain 1..200 entries")
    normalized_records = [str(_safe_relative(str(value), "record path")) for value in records]
    if len(set(normalized_records)) != len(normalized_records):
        raise ComputeMaterialPackagerError("duplicate record_paths")
    scope = selection["geographic_scope"]
    if not isinstance(scope, list) or not scope or any(not str(item) for item in scope):
        raise ComputeMaterialPackagerError("geographic_scope must be a non-empty array")
    time_range = selection["time_range"]
    if not isinstance(time_range, Mapping) or set(time_range) != {"start", "end"}:
        raise ComputeMaterialPackagerError("time_range must contain start and end")
    approval = selection["gpts_validation"]
    if not isinstance(approval, Mapping):
        raise ComputeMaterialPackagerError("gpts_validation must be an object")
    required_approval = {
        "status", "validator", "validated_at", "task_id", "selection_sha256"
    }
    if set(approval) != required_approval:
        raise ComputeMaterialPackagerError("gpts_validation fields are incomplete or excessive")
    if approval.get("status") != "PASS" or approval.get("validator") != "gpts-usage-center":
        raise ComputeMaterialPackagerError("GPTs approval is required")
    if approval.get("task_id") != task_id:
        raise ComputeMaterialPackagerError("GPTs approval task_id mismatch")
    _parse_datetime(approval.get("validated_at"), "gpts_validation.validated_at")
    selection_without_approval = dict(selection)
    selection_without_approval.pop("gpts_validation")
    expected_selection_sha = _canonical_sha(selection_without_approval)
    if approval.get("selection_sha256") != expected_selection_sha:
        raise ComputeMaterialPackagerError("GPTs selection SHA256 mismatch")
    return {
        "package_id": package_id,
        "task_id": task_id,
        "material_type": material_type,
        "version": str(selection["version"]),
        "created_at": created_at.isoformat().replace("+00:00", "Z"),
        "record_paths": normalized_records,
        "valid_from": selection["valid_from"],
        "valid_to": selection["valid_to"],
        "geographic_scope": [str(item) for item in scope],
        "time_range": {"start": time_range["start"], "end": time_range["end"]},
        "decision_use": str(selection["decision_use"]),
        "gpts_validation": dict(approval),
        "selection_sha256": expected_selection_sha,
    }


def _copy_and_verify_file(
    *,
    source_root: Path,
    destination_root: Path,
    record_id: str,
    row: Mapping[str, Any],
) -> dict[str, Any]:
    source_relative = _safe_relative(str(row["path"]), "source file path")
    source = source_root / Path(*source_relative.parts)
    if not source.is_file() or source.is_symlink():
        raise ComputeMaterialPackagerError(f"source file missing or unsafe: {source_relative}")
    size = source.stat().st_size
    digest = _file_sha(source)
    if size != int(row["bytes"]) or digest != row["sha256"]:
        raise ComputeMaterialPackagerError(f"source file integrity mismatch: {source_relative}")
    payload_name = f"{digest[:16]}-{source.name}"
    payload_relative = PurePosixPath("payload") / record_id / payload_name
    destination = destination_root / Path(*payload_relative.parts)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    return {
        "path": str(payload_relative),
        "sha256": digest,
        "bytes": size,
        "media_type": row["media_type"],
        "source_path": str(source_relative),
        "source_record_id": record_id,
    }


def build_package(
    *,
    selection: Mapping[str, Any],
    source_root: Path,
    output_dir: Path,
    source_repository_reference: str,
) -> dict[str, Any]:
    normalized = _validate_selection(selection)
    as_of = _parse_date(normalized["gpts_validation"]["validated_at"][:10], "validated_at")
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    source_records: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []
    total_bytes = 0
    for record_path in normalized["record_paths"]:
        path = source_root / Path(*PurePosixPath(record_path).parts)
        if not path.is_file() or path.is_symlink():
            raise ComputeMaterialPackagerError(f"source record missing or unsafe: {record_path}")
        raw = path.read_bytes()
        record = json.loads(raw.decode("utf-8"))
        if not isinstance(record, Mapping):
            raise ComputeMaterialPackagerError(f"source record must be an object: {record_path}")
        _validate_source_record(
            record,
            record_path=record_path,
            expected_material_type=normalized["material_type"],
            as_of=as_of,
        )
        record_id = str(record["record_id"])
        source_records.append({
            "record_id": record_id,
            "version": record["version"],
            "record_path": record_path,
            "record_sha256": hashlib.sha256(raw).hexdigest(),
            "source_root": record["source_root"],
            "review_due_at": record["review_due_at"],
        })
        for row in record["files"]:
            copied = _copy_and_verify_file(
                source_root=source_root,
                destination_root=output_dir,
                record_id=record_id,
                row=row,
            )
            total_bytes += int(copied["bytes"])
            if total_bytes > MAX_TOTAL_BYTES:
                raise ComputeMaterialPackagerError("package exceeds total size limit")
            files.append(copied)
    files.sort(key=lambda row: row["path"])
    source_records.sort(key=lambda row: row["record_id"])
    if len({row["path"] for row in files}) != len(files):
        raise ComputeMaterialPackagerError("duplicate package payload path")
    manifest = {
        "schema_version": "compute-material-package-manifest-v1",
        "package_id": normalized["package_id"],
        "task_id": normalized["task_id"],
        "material_type": normalized["material_type"],
        "version": normalized["version"],
        "created_at": normalized["created_at"],
        "source_center": "intelligence-center",
        "source_repository_reference": source_repository_reference,
        "decision_use": normalized["decision_use"],
        "source_records": source_records,
        "files": [
            {key: row[key] for key in (
                "path", "sha256", "bytes", "media_type", "source_path", "source_record_id"
            )}
            for row in files
        ],
        "total_bytes": total_bytes,
        "contains_personal_data": False,
        "runtime_code_included": False,
        "selection_sha256": normalized["selection_sha256"],
    }
    _write_json(output_dir / "manifest.json", manifest)
    manifest_sha = _file_sha(output_dir / "manifest.json")
    envelope_files = [
        {key: row[key] for key in ("path", "sha256", "bytes", "media_type")}
        for row in files
    ]
    envelope = {
        "schema_version": "compute-external-domain-material-envelope-v2",
        "transfer_id": normalized["package_id"],
        "task_id": normalized["task_id"],
        "material_type": normalized["material_type"],
        "source_center": "intelligence-center",
        "source_repository_reference": source_repository_reference,
        "version": normalized["version"],
        "created_at": normalized["created_at"],
        "valid_from": normalized["valid_from"],
        "valid_to": normalized["valid_to"],
        "files": envelope_files,
        "manifest_path": "manifest.json",
        "manifest_sha256": manifest_sha,
        "license": {
            "name": "mixed-source-reviewed",
            "reviewed": True,
            "use_scope": ["compute-analysis"],
            "source_record_ids": [row["record_id"] for row in source_records],
        },
        "geographic_scope": normalized["geographic_scope"],
        "time_range": normalized["time_range"],
        "contains_personal_data": False,
        "gpts_validation": {
            **normalized["gpts_validation"],
            "approved_manifest_sha256": manifest_sha,
        },
    }
    _write_json(output_dir / "envelope.json", envelope)
    package_fingerprint = _canonical_sha({
        "manifest_sha256": manifest_sha,
        "envelope_sha256": _file_sha(output_dir / "envelope.json"),
        "files": envelope_files,
    })
    receipt = {
        "schema_version": "compute-material-package-receipt-v1",
        "status": "COMPUTE_MATERIAL_PACKAGE_BUILT",
        "package_id": normalized["package_id"],
        "task_id": normalized["task_id"],
        "material_type": normalized["material_type"],
        "source_record_count": len(source_records),
        "file_count": len(files),
        "total_bytes": total_bytes,
        "manifest_sha256": manifest_sha,
        "envelope_sha256": _file_sha(output_dir / "envelope.json"),
        "package_sha256": package_fingerprint,
        "gpts_validation": "PASS",
        "compute_runtime_network_used": False,
        "direct_center_connection": False,
        "model_calls": 0,
    }
    _write_json(output_dir / "receipt.json", receipt)
    return receipt


def _resolve_repo_id(api: Any, token: str, override: str | None, fallback: str | None) -> str:
    identity = api.whoami(token=token)
    account = str(identity.get("name") or "") if isinstance(identity, Mapping) else ""
    if not account:
        raise ComputeMaterialPackagerError("Hugging Face identity is unavailable")
    repo_id = str(override or fallback or f"{account}/{DEFAULT_REPO_NAME}").strip()
    parts = repo_id.split("/")
    if len(parts) != 2 or any(not part for part in parts):
        raise ComputeMaterialPackagerError("Hugging Face repo must use owner/name")
    return repo_id


def build_from_hf(
    *,
    selection: Mapping[str, Any],
    token: str,
    repo_override: str | None,
    fallback_repo: str | None,
    output_dir: Path,
    api: Any | None = None,
) -> dict[str, Any]:
    if not token:
        raise ComputeMaterialPackagerError("HF_TOKEN is not configured")
    normalized = _validate_selection(selection)
    client = api or HfApi(token=False, library_name="compute-material-packager", library_version="1")
    repo_id = _resolve_repo_id(client, token, repo_override, fallback_repo)
    with tempfile.TemporaryDirectory(prefix="compute-material-source-") as temporary:
        source_root = Path(temporary)
        for record_path in normalized["record_paths"]:
            local_record = Path(hf_hub_download(
                repo_id=repo_id,
                repo_type="dataset",
                filename=record_path,
                token=token,
            ))
            record = _load_json(local_record)
            destination = source_root / Path(*PurePosixPath(record_path).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(local_record, destination)
            if not isinstance(record, Mapping):
                raise ComputeMaterialPackagerError(f"invalid source record: {record_path}")
            for row in record.get("files", []):
                source_path = str(row.get("path") or "")
                remote = Path(hf_hub_download(
                    repo_id=repo_id,
                    repo_type="dataset",
                    filename=source_path,
                    token=token,
                ))
                target = source_root / Path(*_safe_relative(source_path, "source file path").parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(remote, target)
        return build_package(
            selection=selection,
            source_root=source_root,
            output_dir=output_dir,
            source_repository_reference=f"hf-dataset:{repo_id}",
        )


def _selection_from_event(path: Path) -> Mapping[str, Any]:
    event = _load_json(path)
    issue = event.get("issue") if isinstance(event, Mapping) else None
    body = issue.get("body") if isinstance(issue, Mapping) else None
    if not isinstance(body, str):
        raise ComputeMaterialPackagerError("GitHub issue body is unavailable")
    value = json.loads(body)
    if not isinstance(value, Mapping):
        raise ComputeMaterialPackagerError("GitHub issue body must be a JSON object")
    return value


def render_receipt(output_dir: Path) -> int:
    path = output_dir / "receipt.json"
    if not path.exists():
        print("Compute material package: `FAILED`")
        return 1
    receipt = _load_json(path)
    print(f"Compute material package: `{receipt.get('status', 'UNKNOWN')}`")
    print(f"\n- Package ID: `{receipt.get('package_id', '')}`")
    print(f"- Task ID: `{receipt.get('task_id', '')}`")
    print(f"- Material type: `{receipt.get('material_type', '')}`")
    print(f"- Source records: `{receipt.get('source_record_count', 0)}`")
    print(f"- Payload files: `{receipt.get('file_count', 0)}`")
    print(f"- Total bytes: `{receipt.get('total_bytes', 0)}`")
    print(f"- Manifest SHA256: `{receipt.get('manifest_sha256', '')}`")
    print(f"- Package SHA256: `{receipt.get('package_sha256', '')}`")
    print("- GPTs validation: `PASS`")
    print("- Direct center connection: `false`")
    print("- Compute runtime network used: `false`")
    return 0 if receipt.get("status") == "COMPUTE_MATERIAL_PACKAGE_BUILT" else 1


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command", required=True)
    local = sub.add_parser("build-local")
    local.add_argument("--selection", required=True)
    local.add_argument("--source-root", required=True)
    local.add_argument("--output-dir", required=True)
    local.add_argument("--source-reference", default="local-test-fixture")
    remote = sub.add_parser("build-hf")
    remote.add_argument("--event-path", required=True)
    remote.add_argument("--output-dir", required=True)
    render = sub.add_parser("render")
    render.add_argument("--output-dir", required=True)
    return root


def main() -> int:
    args = parser().parse_args()
    output_dir = Path(args.output_dir)
    if args.command == "render":
        return render_receipt(output_dir)
    try:
        if args.command == "build-local":
            selection = _load_json(Path(args.selection))
            build_package(
                selection=selection,
                source_root=Path(args.source_root),
                output_dir=output_dir,
                source_repository_reference=args.source_reference,
            )
        else:
            selection = _selection_from_event(Path(args.event_path))
            build_from_hf(
                selection=selection,
                token=str(os.getenv(HF_TOKEN_ENV) or "").strip(),
                repo_override=os.getenv(HF_REPO_ENV),
                fallback_repo=os.getenv(HF_FALLBACK_REPO_ENV),
                output_dir=output_dir,
            )
        return 0
    except Exception as exc:
        output_dir.mkdir(parents=True, exist_ok=True)
        token = str(os.getenv(HF_TOKEN_ENV) or "")
        _write_json(output_dir / "receipt.json", {
            "schema_version": "compute-material-package-receipt-v1",
            "status": "COMPUTE_MATERIAL_PACKAGE_FAILED",
            "failure": {"type": type(exc).__name__, "message": _redact(str(exc), token)},
            "compute_runtime_network_used": False,
            "direct_center_connection": False,
            "model_calls": 0,
        })
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
