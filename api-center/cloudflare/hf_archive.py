#!/usr/bin/env python3
"""Persist completed Cloudflare collection artifacts to a private Hugging Face dataset repo."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from huggingface_hub import HfApi

HF_ORIGIN = "https://huggingface.co"
HF_TOKEN_ENV = "HF_TOKEN"
HF_REPO_ENV = "HF_CLOUDFLARE_DATASET_REPO"
DEFAULT_REPO_NAME = "cloudflare-intelligence-archive"
MAX_ARCHIVE_BYTES = 25_000_000
SAFE_COMPONENT_RE = re.compile(r"[^A-Za-z0-9._=-]+")


class ArchiveError(RuntimeError):
    """Raised when a collection result cannot be archived safely."""


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_component(value: Any, *, maximum: int = 120) -> str:
    rendered = SAFE_COMPONENT_RE.sub("-", str(value or "").strip()).strip("-.")
    if not rendered:
        rendered = "unknown"
    return rendered[:maximum]


def redact(message: str, token: str) -> str:
    value = str(message)
    if token:
        value = value.replace(token, "[REDACTED]")
    return value.replace("\n", " ")[:1200]


def validate_local_result(output_dir: Path) -> dict[str, Any]:
    required = {
        "ticket.json",
        "ticket-status.json",
        "diagnostics.json",
        "manifest.json",
    }
    missing = sorted(name for name in required if not (output_dir / name).is_file())
    if missing:
        raise ArchiveError(f"missing Cloudflare result files: {missing}")

    ticket = load_json(output_dir / "ticket.json")
    ticket_status = load_json(output_dir / "ticket-status.json")
    diagnostics = load_json(output_dir / "diagnostics.json")
    manifest = load_json(output_dir / "manifest.json")
    documents = [ticket_status, diagnostics, manifest]

    if diagnostics.get("status") != "INTEL_CLOUDFLARE_COMPLETED":
        raise ArchiveError("only completed Cloudflare results may be archived")
    if manifest.get("status") != diagnostics.get("status"):
        raise ArchiveError("manifest and diagnostics status mismatch")
    if ticket.get("provider") != "cloudflare" or manifest.get("provider") != "cloudflare":
        raise ArchiveError("archive input is not a Cloudflare result")
    if ticket.get("task_id") != diagnostics.get("task_id") or ticket.get("task_id") != manifest.get("task_id"):
        raise ArchiveError("task identity mismatch")
    if ticket.get("operation") != diagnostics.get("operation") or ticket.get("operation") != manifest.get("operation"):
        raise ArchiveError("operation identity mismatch")
    if any(document.get("secret_values_exposed") is not False for document in documents):
        raise ArchiveError("secret exposure marker is not false")

    policy = ticket.get("data_policy") if isinstance(ticket.get("data_policy"), Mapping) else {}
    if policy.get("classification") != "public" or policy.get("contains_personal_data") is not False:
        raise ArchiveError("only public, non-personal Cloudflare collection results may be archived")

    listed = manifest.get("files")
    if not isinstance(listed, list) or not listed:
        raise ArchiveError("manifest files are missing")
    manifest_names: set[str] = set()
    total_bytes = 0
    verified_files: list[dict[str, Any]] = []
    for row in listed:
        if not isinstance(row, Mapping):
            raise ArchiveError("manifest file row is invalid")
        name = str(row.get("name") or "")
        if not name or Path(name).name != name or name == "hf-archive-receipt.json":
            raise ArchiveError("manifest contains an unsafe file name")
        path = output_dir / name
        if not path.is_file():
            raise ArchiveError(f"manifest file is missing: {name}")
        size = path.stat().st_size
        digest = sha256_file(path)
        if int(row.get("bytes", -1)) != size or str(row.get("sha256") or "") != digest:
            raise ArchiveError(f"manifest integrity mismatch: {name}")
        manifest_names.add(name)
        total_bytes += size
        verified_files.append({"name": name, "bytes": size, "sha256": digest})

    allowed_names = manifest_names | {"manifest.json"}
    unexpected = sorted(
        path.name
        for path in output_dir.iterdir()
        if path.is_file() and path.name not in allowed_names
    )
    if unexpected:
        raise ArchiveError(f"unexpected Cloudflare result files: {unexpected}")
    total_bytes += (output_dir / "manifest.json").stat().st_size
    if total_bytes > MAX_ARCHIVE_BYTES:
        raise ArchiveError(f"archive exceeds {MAX_ARCHIVE_BYTES} bytes")

    completed_at = str(diagnostics.get("completed_at") or "")
    try:
        completed = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ArchiveError("diagnostics.completed_at is invalid") from exc
    if completed.tzinfo is None:
        completed = completed.replace(tzinfo=timezone.utc)
    completed = completed.astimezone(timezone.utc)

    metadata = diagnostics.get("metadata") if isinstance(diagnostics.get("metadata"), Mapping) else {}
    return {
        "ticket": ticket,
        "diagnostics": diagnostics,
        "manifest": manifest,
        "files": verified_files,
        "total_bytes": total_bytes,
        "completed": completed,
        "content_sha256": str(metadata.get("response_sha256") or manifest.get("files", [{}])[-1].get("sha256") or ""),
    }


def resolve_repo_id(api: HfApi, token: str, override: str | None) -> tuple[str, str]:
    info = api.whoami(token=token)
    if not isinstance(info, Mapping) or not info.get("name"):
        raise ArchiveError("Hugging Face whoami did not return an account name")
    account = str(info["name"])
    requested = str(override or "").strip()
    repo_id = requested or f"{account}/{DEFAULT_REPO_NAME}"
    if not re.fullmatch(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}/[A-Za-z0-9][A-Za-z0-9._-]{0,95}$", repo_id):
        raise ArchiveError("HF_CLOUDFLARE_DATASET_REPO must be owner/name")
    return repo_id, account


def archive_result(
    output_dir: Path,
    *,
    token: str,
    repo_override: str | None,
    github_repository: str,
    issue_number: str,
    run_id: str,
    run_attempt: str,
    source_sha: str,
    api: HfApi | None = None,
) -> dict[str, Any]:
    if not token:
        raise ArchiveError(f"{HF_TOKEN_ENV} is not configured")
    validated = validate_local_result(output_dir)
    client = api or HfApi(endpoint=HF_ORIGIN, token=False, library_name="intelligence-center-cloudflare-archive", library_version="1")
    repo_id, account = resolve_repo_id(client, token, repo_override)

    client.create_repo(
        repo_id=repo_id,
        repo_type="dataset",
        private=True,
        exist_ok=True,
        token=token,
    )
    repo_info = client.dataset_info(repo_id, token=token, timeout=30)
    if getattr(repo_info, "private", None) is not True:
        raise ArchiveError("Hugging Face archive repository must be private")

    ticket = validated["ticket"]
    diagnostics = validated["diagnostics"]
    completed: datetime = validated["completed"]
    path_in_repo = "/".join(
        [
            "cloudflare",
            f"year={completed:%Y}",
            f"month={completed:%m}",
            f"day={completed:%d}",
            f"operation={safe_component(ticket['operation'], maximum=80)}",
            f"task={safe_component(ticket['task_id'], maximum=100)}",
            f"run={safe_component(run_id, maximum=40)}-{safe_component(run_attempt, maximum=12)}",
        ]
    )

    with tempfile.TemporaryDirectory(prefix="cloudflare-hf-archive-") as temp_dir:
        staging = Path(temp_dir)
        for row in validated["files"]:
            shutil.copy2(output_dir / row["name"], staging / row["name"])
        shutil.copy2(output_dir / "manifest.json", staging / "manifest.json")
        record = {
            "schema_version": "cloudflare-hf-archive-record-v1",
            "provider": "cloudflare",
            "operation": ticket["operation"],
            "task_id": ticket["task_id"],
            "collection_status": diagnostics["status"],
            "collected_at": diagnostics.get("completed_at"),
            "content_sha256": validated["content_sha256"],
            "total_bytes": validated["total_bytes"],
            "files": validated["files"],
            "source": {
                "github_repository": github_repository,
                "issue_number": issue_number,
                "run_id": run_id,
                "run_attempt": run_attempt,
                "source_sha": source_sha,
            },
            "archive": {
                "repo_id": repo_id,
                "repo_type": "dataset",
                "private": True,
                "path": path_in_repo,
                "storage_mode": "append-only-versioned-artifacts",
            },
            "data_policy": ticket.get("data_policy"),
            "secret_values_exposed": False,
            "model_calls": 0,
        }
        write_json(staging / "archive-record.json", record)
        upload = client.upload_folder(
            repo_id=repo_id,
            repo_type="dataset",
            folder_path=str(staging),
            path_in_repo=path_in_repo,
            token=token,
            commit_message=f"archive cloudflare {ticket['operation']} {ticket['task_id']}",
        )

    receipt = {
        "schema_version": "cloudflare-hf-archive-receipt-v1",
        "status": "HF_CLOUDFLARE_ARCHIVE_COMPLETED",
        "repo_id": repo_id,
        "account": account,
        "repo_type": "dataset",
        "private": True,
        "path": path_in_repo,
        "task_id": ticket["task_id"],
        "operation": ticket["operation"],
        "content_sha256": validated["content_sha256"],
        "total_bytes": validated["total_bytes"],
        "file_count": len(validated["files"]) + 2,
        "commit_oid": str(getattr(upload, "oid", "") or ""),
        "secret_values_exposed": False,
        "model_calls": 0,
    }
    write_json(output_dir / "hf-archive-receipt.json", receipt)
    return receipt


def render_receipt(output_dir: Path) -> int:
    path = output_dir / "hf-archive-receipt.json"
    if not path.exists():
        print("Cloudflare archive result: `HF_CLOUDFLARE_ARCHIVE_FAILED`")
        print("\n- Failure: `archive receipt was not generated`")
        print("- Secret values exposed: `false`")
        return 1
    receipt = load_json(path)
    print(f"Cloudflare archive result: `{receipt.get('status', 'UNKNOWN')}`")
    print(f"\n- Dataset: `{receipt.get('repo_id', '')}`")
    print(f"- Path: `{receipt.get('path', '')}`")
    print(f"- Files: `{receipt.get('file_count', 0)}`")
    print(f"- Bytes: `{receipt.get('total_bytes', 0)}`")
    print("- Private repository: `true`")
    print("- Secret values exposed: `false`")
    return 0 if receipt.get("status") == "HF_CLOUDFLARE_ARCHIVE_COMPLETED" else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    archive_parser = subparsers.add_parser("archive")
    archive_parser.add_argument("--output-dir", required=True)
    render_parser = subparsers.add_parser("render")
    render_parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    if args.command == "render":
        return render_receipt(output_dir)

    token = str(os.getenv(HF_TOKEN_ENV) or "").strip()
    try:
        archive_result(
            output_dir,
            token=token,
            repo_override=os.getenv(HF_REPO_ENV),
            github_repository=str(os.getenv("GITHUB_REPOSITORY") or ""),
            issue_number=str(os.getenv("ISSUE_NUMBER") or ""),
            run_id=str(os.getenv("GITHUB_RUN_ID") or ""),
            run_attempt=str(os.getenv("GITHUB_RUN_ATTEMPT") or "1"),
            source_sha=str(os.getenv("GITHUB_SHA") or ""),
        )
        return 0
    except Exception as exc:
        failure = {
            "schema_version": "cloudflare-hf-archive-receipt-v1",
            "status": "HF_CLOUDFLARE_ARCHIVE_FAILED",
            "failure": {
                "type": type(exc).__name__,
                "message": redact(str(exc), token),
            },
            "secret_values_exposed": False,
            "model_calls": 0,
        }
        write_json(output_dir / "hf-archive-receipt.json", failure)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
