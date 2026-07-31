#!/usr/bin/env python3
"""Validate one Google credential bundle and emit safe blocked artifacts when unavailable."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

BUNDLE_ENV = "GOOGLE_CREDENTIALS_JSON"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_sha(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def parse_bundle(raw: str) -> tuple[dict[str, Any], str]:
    text = raw.strip()
    if not text:
        raise RuntimeError(f"missing repository Secret {BUNDLE_ENV}")
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{BUNDLE_ENV} is not valid JSON") from exc
    if not isinstance(value, Mapping):
        raise RuntimeError(f"{BUNDLE_ENV} must contain a JSON object")
    service_account = value.get("service_account")
    api_key = str(value.get("data_commons_api_key") or "").strip()
    if not isinstance(service_account, Mapping):
        raise RuntimeError(f"{BUNDLE_ENV}.service_account must be a JSON object")
    required = {
        "type",
        "project_id",
        "private_key_id",
        "private_key",
        "client_email",
        "token_uri",
    }
    missing = sorted(required - set(service_account))
    if missing:
        raise RuntimeError(
            f"{BUNDLE_ENV}.service_account is missing fields: {missing}"
        )
    if str(service_account.get("type") or "") != "service_account":
        raise RuntimeError(
            f"{BUNDLE_ENV}.service_account.type must be service_account"
        )
    if not api_key:
        raise RuntimeError(f"{BUNDLE_ENV}.data_commons_api_key is required")
    return dict(service_account), api_key


def append_multiline(path: Path, name: str, value: str) -> None:
    delimiter = f"GOOGLE_BUNDLE_{name}_EOF"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{name}<<{delimiter}\n{value}\n{delimiter}\n")


def export_runtime(raw: str, github_env: Path) -> None:
    service_account, data_commons_api_key = parse_bundle(raw)
    encoded = json.dumps(
        service_account,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    append_multiline(github_env, "BIGQUERY_SERVICE_ACCOUNT_JSON", encoded)
    append_multiline(github_env, "EARTH_ENGINE_SERVICE_ACCOUNT_JSON", encoded)
    append_multiline(
        github_env,
        "GOOGLE_DATA_COMMONS_API_KEY",
        data_commons_api_key,
    )


def bundle_failure_message(raw: str) -> str:
    try:
        parse_bundle(raw)
    except RuntimeError as exc:
        return str(exc)
    return f"failed to expand repository Secret {BUNDLE_ENV}"


def _gcp_blocked_snapshot(ticket: Mapping[str, Any], message: str) -> tuple[dict[str, Any], dict[str, Any], str, list[str]]:
    failure = {
        "code": "GOOGLE_CREDENTIALS_BUNDLE_INVALID",
        "message": message,
        "retryable": False,
    }
    snapshot: dict[str, Any] = {
        "schema_version": "google-cloud-api-snapshot-v1",
        "status": "API_GCP_BLOCKED",
        "created_at": utc_now(),
        "started_at": utc_now(),
        "elapsed_seconds": 0.0,
        "task_id": str(ticket["task_id"]),
        "provider": str(ticket["provider"]),
        "operation": str(ticket["operation"]),
        "objective": str(ticket.get("objective") or ""),
        "ticket_sha256": canonical_sha(ticket),
        "parameters": dict(ticket.get("parameters") or {}),
        "data_policy": dict(ticket["data_policy"]),
        "data": None,
        "upstream_metadata": {},
        "failure": failure,
        "security": {
            "secret_values_included": False,
            "authorization_header_recorded": False,
            "public_non_personal_data_only": True,
            "bigquery_write_allowed": False,
            "earth_engine_export_or_asset_write_allowed": False,
        },
        "model_calls": 0,
    }
    snapshot["snapshot_sha256"] = canonical_sha(snapshot)
    diagnostics = {
        "schema_version": "google-cloud-api-diagnostics-v1",
        "status": snapshot["status"],
        "provider": snapshot["provider"],
        "operation": snapshot["operation"],
        "failure": failure,
        "credential_secret_name": BUNDLE_ENV,
        "credential_secret_value_exposed": False,
    }
    summary = "\n".join(
        [
            "# API_GCP_BLOCKED",
            "",
            f"- Task ID: `{snapshot['task_id']}`",
            f"- Provider: `{snapshot['provider']}`",
            f"- Operation: `{snapshot['operation']}`",
            f"- Snapshot SHA256: `{snapshot['snapshot_sha256']}`",
            "- Model calls: `0`",
            f"- Error code: `{failure['code']}`",
            f"- Message: {message}",
            "",
        ]
    )
    files = [
        "ticket.json",
        "ticket-status.json",
        "gcp-snapshot.json",
        "gcp-diagnostics.json",
        "gcp-summary.md",
    ]
    return snapshot, diagnostics, summary, files


def _data_commons_blocked_snapshot(ticket: Mapping[str, Any], message: str) -> tuple[dict[str, Any], dict[str, Any], str, list[str]]:
    failure = {
        "code": "GOOGLE_CREDENTIALS_BUNDLE_INVALID",
        "message": message,
        "retryable": False,
    }
    snapshot: dict[str, Any] = {
        "schema_version": "data-commons-api-snapshot-v1",
        "status": "API_DATA_COMMONS_BLOCKED",
        "created_at": utc_now(),
        "started_at": utc_now(),
        "elapsed_seconds": 0.0,
        "task_id": str(ticket["task_id"]),
        "provider": "data-commons",
        "operation": str(ticket["operation"]),
        "objective": str(ticket.get("objective") or ""),
        "ticket_sha256": canonical_sha(ticket),
        "parameters": dict(ticket.get("parameters") or {}),
        "data_policy": dict(ticket["data_policy"]),
        "data": None,
        "upstream_metadata": {},
        "failure": failure,
        "security": {
            "secret_values_included": False,
            "api_key_recorded": False,
            "authorization_header_recorded": False,
            "public_non_personal_data_only": True,
            "arbitrary_url_allowed": False,
            "sparql_allowed": False,
            "write_operations_allowed": False,
        },
        "model_calls": 0,
    }
    snapshot["snapshot_sha256"] = canonical_sha(snapshot)
    diagnostics = {
        "schema_version": "data-commons-api-diagnostics-v1",
        "status": snapshot["status"],
        "provider": "data-commons",
        "operation": snapshot["operation"],
        "failure": failure,
        "credential_secret_name": BUNDLE_ENV,
        "credential_secret_value_exposed": False,
    }
    summary = "\n".join(
        [
            "# API_DATA_COMMONS_BLOCKED",
            "",
            f"- Task ID: `{snapshot['task_id']}`",
            "- Provider: `data-commons`",
            f"- Operation: `{snapshot['operation']}`",
            f"- Snapshot SHA256: `{snapshot['snapshot_sha256']}`",
            "- Model calls: `0`",
            f"- Error code: `{failure['code']}`",
            f"- Message: {message}",
            "",
        ]
    )
    files = [
        "ticket.json",
        "ticket-status.json",
        "data-commons-snapshot.json",
        "data-commons-diagnostics.json",
        "data-commons-summary.md",
    ]
    return snapshot, diagnostics, summary, files


def generate_blocked_artifact(
    *,
    ticket_path: Path,
    output_dir: Path,
    target: str,
    raw_bundle: str,
) -> None:
    ticket = json.loads(ticket_path.read_text(encoding="utf-8"))
    if not isinstance(ticket, Mapping):
        raise ValueError("ticket must contain a JSON object")
    output_dir.mkdir(parents=True, exist_ok=True)
    message = bundle_failure_message(raw_bundle)
    if target == "gcp":
        snapshot, diagnostics, summary, files = _gcp_blocked_snapshot(
            ticket,
            message,
        )
        write_json(output_dir / "gcp-snapshot.json", snapshot)
        write_json(output_dir / "gcp-diagnostics.json", diagnostics)
        (output_dir / "gcp-summary.md").write_text(summary, encoding="utf-8")
        manifest_schema = "google-cloud-artifact-manifest-v1"
    elif target == "data-commons":
        snapshot, diagnostics, summary, files = _data_commons_blocked_snapshot(
            ticket,
            message,
        )
        write_json(output_dir / "data-commons-snapshot.json", snapshot)
        write_json(output_dir / "data-commons-diagnostics.json", diagnostics)
        (output_dir / "data-commons-summary.md").write_text(
            summary,
            encoding="utf-8",
        )
        manifest_schema = "data-commons-artifact-manifest-v1"
    else:
        raise ValueError(f"unsupported blocked artifact target: {target}")
    write_json(
        output_dir / "artifact-manifest.json",
        {
            "schema_version": manifest_schema,
            "files": files,
            "snapshot_sha256": snapshot["snapshot_sha256"],
            "secret_values_included": False,
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--blocked-target",
        choices=["gcp", "data-commons"],
    )
    parser.add_argument("--ticket")
    parser.add_argument("--output-dir")
    args = parser.parse_args()
    raw = str(os.getenv(BUNDLE_ENV) or "")
    if args.blocked_target:
        if not args.ticket or not args.output_dir:
            parser.error(
                "--ticket and --output-dir are required with --blocked-target"
            )
        generate_blocked_artifact(
            ticket_path=Path(args.ticket),
            output_dir=Path(args.output_dir),
            target=args.blocked_target,
            raw_bundle=raw,
        )
        return 0
    github_env = str(os.getenv("GITHUB_ENV") or "").strip()
    if not github_env:
        raise RuntimeError("GITHUB_ENV is required")
    export_runtime(raw, Path(github_env))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
