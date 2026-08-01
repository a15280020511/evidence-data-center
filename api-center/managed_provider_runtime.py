#!/usr/bin/env python3
"""Shared deterministic runtime for bounded managed API-center providers."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from jsonschema import Draft202012Validator


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def canonical_sha(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def bytes_sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def write_output(name: str, value: Any) -> None:
    target = os.getenv("GITHUB_OUTPUT")
    if not target:
        return
    text = str(value).replace("\n", " ").replace("\r", " ")
    with open(target, "a", encoding="utf-8") as handle:
        handle.write(f"{name}={text}\n")


def provider_row(catalog_path: Path) -> Mapping[str, Any]:
    catalog = load_json(catalog_path)
    providers = catalog.get("providers") if isinstance(catalog, Mapping) else None
    if not isinstance(providers, list) or len(providers) != 1:
        raise ValueError("provider catalog must contain exactly one provider")
    provider = providers[0]
    if not isinstance(provider, Mapping):
        raise ValueError("provider catalog row must be an object")
    return provider


def operation_map(catalog_path: Path) -> dict[str, Mapping[str, Any]]:
    provider = provider_row(catalog_path)
    operations = provider.get("operations")
    if not isinstance(operations, list):
        raise ValueError("provider operations must be a list")
    return {
        str(row["operation_id"]): row
        for row in operations
        if isinstance(row, Mapping) and "operation_id" in row
    }


def validate_ticket(
    ticket: Mapping[str, Any],
    *,
    schema_path: Path,
    catalog_path: Path,
) -> None:
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(ticket), key=lambda item: list(item.absolute_path)
    )
    if errors:
        rendered = "; ".join(
            f"{'.'.join(str(x) for x in item.absolute_path) or '$'}: {item.message}"
            for item in errors[:20]
        )
        raise ValueError(rendered)

    operation = str(ticket["operation"])
    row = operation_map(catalog_path).get(operation)
    if row is None:
        raise ValueError(f"unsupported operation: {operation}")
    parameters = ticket.get("parameters")
    if not isinstance(parameters, Mapping):
        raise ValueError("parameters must be an object")
    allowed = {str(name) for name in row.get("parameters", [])}
    unexpected = sorted(set(parameters) - allowed)
    if unexpected:
        raise ValueError(f"non-allowlisted parameters: {unexpected}")
    operation_schema = row.get("parameter_schema")
    if isinstance(operation_schema, Mapping):
        operation_errors = sorted(
            Draft202012Validator(operation_schema).iter_errors(parameters),
            key=lambda item: list(item.absolute_path),
        )
        if operation_errors:
            rendered = "; ".join(
                f"parameters.{'.'.join(str(x) for x in item.absolute_path)}: {item.message}"
                for item in operation_errors[:20]
            )
            raise ValueError(rendered)


def prepare(
    event_path: Path,
    output_dir: Path,
    *,
    ticket_prefix: str,
    schema_path: Path,
    catalog_path: Path,
    status_schema: str,
) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    event = load_json(event_path)
    issue = event.get("issue") if isinstance(event.get("issue"), Mapping) else {}
    title = str(issue.get("title") or "")
    body = str(issue.get("body") or "")
    accepted = False
    reason = ""
    ticket: Mapping[str, Any] | None = None
    try:
        if not title.startswith(ticket_prefix):
            raise ValueError(f"issue title must start with {ticket_prefix}")
        parsed = json.loads(body)
        if not isinstance(parsed, Mapping):
            raise ValueError("ticket body must be a JSON object")
        validate_ticket(parsed, schema_path=schema_path, catalog_path=catalog_path)
        ticket = parsed
        accepted = True
        write_json(output_dir / "ticket.json", ticket)
    except (json.JSONDecodeError, ValueError) as exc:
        reason = str(exc)

    status = {
        "schema_version": status_schema,
        "accepted": accepted,
        "reason": reason,
        "task_id": str((ticket or {}).get("task_id") or ""),
        "provider": str((ticket or {}).get("provider") or ""),
        "operation": str((ticket or {}).get("operation") or ""),
        "ticket_sha256": canonical_sha(ticket) if ticket else None,
        "secret_values_exposed": False,
        "model_calls": 0,
    }
    write_json(output_dir / "ticket-status.json", status)
    write_output("accepted", "true" if accepted else "false")
    write_output("reason", reason)
    return 0 if accepted else 1


def bounded_int(
    value: Any,
    *,
    default: int,
    minimum: int,
    maximum: int,
    name: str,
) -> int:
    if value in (None, ""):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if not minimum <= parsed <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return parsed


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]
    if hasattr(value, "to_dict"):
        try:
            return json_safe(value.to_dict(orient="records"))
        except TypeError:
            return json_safe(value.to_dict())
    if hasattr(value, "item"):
        try:
            return json_safe(value.item())
        except Exception:
            pass
    if hasattr(value, "tolist"):
        try:
            return json_safe(value.tolist())
        except Exception:
            pass
    return str(value)


def finish_execution(
    *,
    ticket: Mapping[str, Any],
    output_dir: Path,
    status: str,
    snapshot: Mapping[str, Any] | None,
    metadata: Mapping[str, Any],
    failure: Mapping[str, Any] | None,
    started_at: str,
    started_perf: float,
    schema_prefix: str,
) -> int:
    if snapshot is not None:
        write_json(output_dir / "snapshot.json", json_safe(snapshot))
    duration_ms = round((time.perf_counter() - started_perf) * 1000)
    diagnostics = {
        "schema_version": f"{schema_prefix}-diagnostics-v1",
        "status": status,
        "task_id": ticket["task_id"],
        "operation": ticket["operation"],
        "started_at": started_at,
        "completed_at": utc_now(),
        "duration_ms": duration_ms,
        "metadata": json_safe(metadata),
        "failure": json_safe(failure),
        "secret_values_exposed": False,
        "model_calls": 0,
    }
    write_json(output_dir / "diagnostics.json", diagnostics)

    files = []
    for path_item in sorted(output_dir.iterdir()):
        if path_item.is_file() and path_item.name != "manifest.json":
            raw = path_item.read_bytes()
            files.append(
                {"name": path_item.name, "bytes": len(raw), "sha256": bytes_sha(raw)}
            )
    manifest = {
        "schema_version": f"{schema_prefix}-manifest-v1",
        "status": status,
        "task_id": ticket["task_id"],
        "provider": ticket["provider"],
        "operation": ticket["operation"],
        "files": files,
        "secret_values_exposed": False,
        "model_calls": 0,
    }
    write_json(output_dir / "manifest.json", manifest)
    write_output("status", status)
    return 0 if status.endswith("_COMPLETED") else 1


def render(
    output_dir: Path,
    phase: str,
    artifact_url: str,
    *,
    display_name: str,
) -> int:
    ticket_status = (
        load_json(output_dir / "ticket-status.json")
        if (output_dir / "ticket-status.json").exists()
        else {}
    )
    if phase == "accepted":
        print(
            f"{display_name} API ticket accepted: "
            f"`{ticket_status.get('task_id', '')}` / "
            f"`{ticket_status.get('operation', '')}`. "
            "Secret values remain backend-only."
        )
        return 0
    if phase == "rejected":
        print(
            f"{display_name} API ticket rejected: "
            f"{ticket_status.get('reason') or 'invalid ticket'}"
        )
        return 0

    diagnostics = (
        load_json(output_dir / "diagnostics.json")
        if (output_dir / "diagnostics.json").exists()
        else {}
    )
    manifest = (
        load_json(output_dir / "manifest.json")
        if (output_dir / "manifest.json").exists()
        else {}
    )
    print(f"{display_name} API result: `{diagnostics.get('status', 'UNKNOWN')}`")
    print(f"\n- Operation: `{diagnostics.get('operation', '')}`")
    print(f"- Duration: `{diagnostics.get('duration_ms', 0)} ms`")
    print(f"- Files: `{len(manifest.get('files') or [])}`")
    failure = diagnostics.get("failure")
    if failure:
        print(f"- Failure: `{failure.get('type', 'Error')}: {failure.get('message', '')}`")
    if artifact_url:
        print(f"- Artifact: {artifact_url}")
    print("- Secret values exposed: `false`")
    return 0


def run_cli(
    *,
    execute: Callable[[Path, Path], int],
    ticket_prefix: str,
    schema_path: Path,
    catalog_path: Path,
    status_schema: str,
    display_name: str,
) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--event-path", required=True)
    prepare_parser.add_argument("--output-dir", required=True)

    execute_parser = sub.add_parser("execute")
    execute_parser.add_argument("--ticket", required=True)
    execute_parser.add_argument("--output-dir", required=True)

    render_parser = sub.add_parser("render")
    render_parser.add_argument("--output-dir", required=True)
    render_parser.add_argument(
        "--phase", choices=("accepted", "rejected", "completed"), required=True
    )
    render_parser.add_argument("--artifact-url", default="")

    args = parser.parse_args()
    if args.command == "prepare":
        return prepare(
            Path(args.event_path),
            Path(args.output_dir),
            ticket_prefix=ticket_prefix,
            schema_path=schema_path,
            catalog_path=catalog_path,
            status_schema=status_schema,
        )
    if args.command == "execute":
        return execute(Path(args.ticket), Path(args.output_dir))
    return render(
        Path(args.output_dir),
        args.phase,
        args.artifact_url,
        display_name=display_name,
    )
