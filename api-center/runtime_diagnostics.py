#!/usr/bin/env python3
"""Build redacted, structured diagnostics for API-center validation runs."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SAFE_ENV_KEYS = (
    "GITHUB_REPOSITORY",
    "GITHUB_RUN_ID",
    "GITHUB_RUN_ATTEMPT",
    "GITHUB_SHA",
    "GITHUB_WORKFLOW",
    "GITHUB_JOB",
)
EXPECTED_FILES = (
    "api-center/connector-manifest.json",
    "api-center/krakend.validation.json",
    "api-center-unit-tests.log",
    "api-center-base-image-requested.txt",
    "api-center-base-image-resolved.txt",
    "api-center-health.json",
    "api-center-container-inspect.json",
    "api-center-runtime.log",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inventory(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relative in EXPECTED_FILES:
        path = root / relative
        if path.is_file():
            rows.append(
                {
                    "path": relative,
                    "size_bytes": path.stat().st_size,
                    "sha256": _sha256(path),
                    "modified_at": datetime.fromtimestamp(
                        path.stat().st_mtime, timezone.utc
                    ).isoformat(),
                }
            )
    return rows


def _parse_json(path: Path, parse_errors: list[dict[str, str]]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        parse_errors.append(
            {
                "path": str(path),
                "type": type(exc).__name__,
                "message": str(exc),
            }
        )
        return None


def _root_cause(
    *,
    outcomes: dict[str, str],
    health: str,
    missing: list[str],
    parse_errors: list[dict[str, str]],
) -> dict[str, Any]:
    ordered = (
        ("registry", "API_REGISTRY_VALIDATION_FAILED"),
        ("base_image", "API_BASE_IMAGE_RESOLUTION_FAILED"),
        ("config", "API_GATEWAY_CONFIG_INVALID"),
        ("image", "API_IMAGE_BUILD_FAILED"),
        ("runtime", "API_RUNTIME_HEALTH_FAILED"),
    )
    for stage, code in ordered:
        if outcomes.get(stage) != "success":
            return {
                "code": code,
                "stage": stage,
                "message": f"{stage} step outcome is {outcomes.get(stage) or 'unknown'}",
            }
    if health != "healthy":
        return {
            "code": "API_RUNTIME_NOT_HEALTHY",
            "stage": "runtime",
            "message": f"container health is {health or 'unknown'}",
        }
    if parse_errors:
        return {
            "code": "API_DIAGNOSTIC_JSON_INVALID",
            "stage": "diagnostics",
            "message": parse_errors[0]["message"],
        }
    if missing:
        return {
            "code": "API_DIAGNOSTIC_EVIDENCE_MISSING",
            "stage": "evidence",
            "message": f"missing required evidence: {', '.join(missing)}",
        }
    return {"code": "NONE", "stage": "complete", "message": ""}


def build(
    root: Path,
    *,
    registry_outcome: str,
    base_image_outcome: str,
    config_outcome: str,
    image_outcome: str,
    runtime_outcome: str,
    health: str,
    container_id: str,
) -> dict[str, Any]:
    root = root.resolve()
    parse_errors: list[dict[str, str]] = []
    manifest = _parse_json(root / "api-center/connector-manifest.json", parse_errors)
    health_payload = _parse_json(root / "api-center-health.json", parse_errors)
    inspect_payload = _parse_json(
        root / "api-center-container-inspect.json", parse_errors
    )

    outcomes = {
        "registry": registry_outcome,
        "base_image": base_image_outcome,
        "config": config_outcome,
        "image": image_outcome,
        "runtime": runtime_outcome,
    }
    missing = [relative for relative in EXPECTED_FILES if not (root / relative).is_file()]
    primary = _root_cause(
        outcomes=outcomes,
        health=health,
        missing=missing,
        parse_errors=parse_errors,
    )
    status = "PASS" if primary["code"] == "NONE" else "FAIL"

    requested_image = ""
    requested_path = root / "api-center-base-image-requested.txt"
    if requested_path.is_file():
        requested_image = requested_path.read_text(
            encoding="utf-8", errors="replace"
        ).strip()

    result = {
        "schema_version": "api-center-diagnostics-v2",
        "created_at": _utc_now(),
        "status": status,
        "primary_failure": primary,
        "run_identity": {
            key.lower(): os.getenv(key) for key in SAFE_ENV_KEYS
        },
        "stage_status": {
            stage: ("PASS" if outcome == "success" else "FAIL")
            for stage, outcome in outcomes.items()
        },
        "runtime": {
            "container_id": container_id or None,
            "health": health or "unknown",
            "requested_image": requested_image or None,
            "health_payload_present": health_payload is not None,
            "container_inspect_present": inspect_payload is not None,
        },
        "connector_summary": {
            "manifest_present": isinstance(manifest, dict),
            "connector_count": (
                manifest.get("connector_count")
                if isinstance(manifest, dict)
                else None
            ),
            "enabled_connector_count": (
                manifest.get("enabled_connector_count")
                if isinstance(manifest, dict)
                else None
            ),
        },
        "missing_evidence": missing,
        "parse_errors": parse_errors,
        "remediation_hints": _remediation(primary["code"]),
        "artifact_inventory": _inventory(root),
        "security": {
            "secret_values_included": False,
            "environment_allowlist": [key.lower() for key in SAFE_ENV_KEYS],
            "connector_secret_values_embedded": False,
        },
    }
    (root / "api-center-diagnostics.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    audit = {
        "version": 5,
        "created_at": result["created_at"],
        "status": status,
        "primary_failure": primary,
        "stage_status": result["stage_status"],
        "health": result["runtime"]["health"],
        "files": result["artifact_inventory"],
        "missing_evidence": missing,
        "parse_error_count": len(parse_errors),
        "secret_values_included": False,
    }
    (root / "api-center-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _write_output("status", status)
    _write_output("error_code", primary["code"])
    return result


def _remediation(code: str) -> list[str]:
    mapping = {
        "API_REGISTRY_VALIDATION_FAILED": [
            "Inspect api-center-unit-tests.log and connector schema errors."
        ],
        "API_BASE_IMAGE_RESOLUTION_FAILED": [
            "Check the pinned Dockerfile image tag and digest resolution."
        ],
        "API_GATEWAY_CONFIG_INVALID": [
            "Inspect generated gateway configuration and offline validation output."
        ],
        "API_IMAGE_BUILD_FAILED": [
            "Inspect Docker build output and the pinned base image."
        ],
        "API_RUNTIME_HEALTH_FAILED": [
            "Inspect api-center-runtime.log and api-center-container-inspect.json."
        ],
        "API_RUNTIME_NOT_HEALTHY": [
            "Inspect container health checks, runtime log, ports, and generated configuration."
        ],
        "API_DIAGNOSTIC_EVIDENCE_MISSING": [
            "Inspect the first failed step and ensure failure-path capture runs before cleanup."
        ],
    }
    return mapping.get(
        code,
        ["Use the primary failure stage, runtime log, container inspect, and file hashes."],
    )


def _write_output(name: str, value: str) -> None:
    target = os.getenv("GITHUB_OUTPUT")
    if not target:
        return
    with open(target, "a", encoding="utf-8") as handle:
        handle.write(f"{name}={str(value).replace(chr(10), ' ')}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--registry-outcome", default="unknown")
    parser.add_argument("--base-image-outcome", default="unknown")
    parser.add_argument("--config-outcome", default="unknown")
    parser.add_argument("--image-outcome", default="unknown")
    parser.add_argument("--runtime-outcome", default="unknown")
    parser.add_argument("--health", default="unknown")
    parser.add_argument("--container-id", default="")
    args = parser.parse_args()
    result = build(
        Path(args.root),
        registry_outcome=args.registry_outcome,
        base_image_outcome=args.base_image_outcome,
        config_outcome=args.config_outcome,
        image_outcome=args.image_outcome,
        runtime_outcome=args.runtime_outcome,
        health=args.health,
        container_id=args.container_id,
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "primary_failure": result["primary_failure"],
                "missing_evidence_count": len(result["missing_evidence"]),
                "parse_error_count": len(result["parse_errors"]),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
