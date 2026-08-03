#!/usr/bin/env python3
"""Zero-network validation harness for the governed OpenBB free provider."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

import openbb_free_task as task

SAMPLES = {
    "catalog-capabilities": {},
    "provider-access-matrix": {},
    "package-manifest": {},
    "ecb-currency-reference-rates": {},
    "federal-reserve-federal-funds-rate": {
        "start_date": "2026-01-01",
        "end_date": "2026-01-31",
    },
    "federal-reserve-sofr": {
        "start_date": "2026-01-01",
        "end_date": "2026-01-31",
    },
    "fama-french-factors": {
        "region": "america",
        "factor": "3_factors",
        "frequency": "monthly",
        "start_date": "2020-01-01",
        "end_date": "2021-12-31",
    },
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--operation", required=True, choices=sorted(SAMPLES))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    os.environ["OPENBB_FREE_FIXTURE_MODE"] = "1"
    operation = args.operation
    ticket = {
        "task_id": f"openbb-fixture-{operation}",
        "provider": "openbb-free",
        "operation": operation,
        "parameters": SAMPLES[operation],
        "data_policy": {
            "classification": "public",
            "contains_personal_data": False,
        },
        "acceptance": {
            "timeout_seconds": 60,
            "max_response_bytes": 10000000,
        },
    }

    with tempfile.TemporaryDirectory(prefix="openbb-free-") as temp:
        root = Path(temp)
        ticket_path = root / "ticket.json"
        result_dir = root / "result"
        ticket_path.write_text(json.dumps(ticket), encoding="utf-8")
        return_code = task.execute(ticket_path, result_dir)
        diagnostics = json.loads(
            (result_dir / "diagnostics.json").read_text(encoding="utf-8")
        )
        manifest = json.loads(
            (result_dir / "manifest.json").read_text(encoding="utf-8")
        )
        package_manifest = task.package_manifest()

    expected_status = "INTEL_OPENBB_FREE_COMPLETED"
    status = diagnostics.get("status")
    passed = (
        return_code == 0
        and status == expected_status
        and diagnostics.get("model_calls") == 0
        and diagnostics.get("secret_values_exposed") is False
        and package_manifest.get("all_pins_satisfied") is True
    )
    result = {
        "status": "PASS" if passed else "FAIL",
        "operation": operation,
        "provider_status": status,
        "network_used": False,
        "fixture_mode": True,
        "model_calls": 0,
        "secret_used": False,
        "secret_values_exposed": False,
        "package_manifest": package_manifest,
        "artifact_file_count": len(manifest.get("files") or []),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
