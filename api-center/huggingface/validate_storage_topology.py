#!/usr/bin/env python3
"""Fail closed if private Hugging Face storage returns to the evidence center."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROLE = ROOT / "api-center/huggingface/numeric-baseline-library/library-role.json"

PRIVATE_STORAGE_WORKFLOWS = (
    ".github/workflows/hf-numeric-baseline-library.yml",
    ".github/workflows/hf-domain-benchmark-library.yml",
    ".github/workflows/hf-external-reality-library.yml",
    ".github/workflows/compute-material-packager.yml",
    ".github/workflows/cloudflare-cn-numeric-compiler.yml",
    ".github/workflows/cloudflare-cn-daily-harvest.yml",
    ".github/workflows/cloudflare-api-ticket.yml",
)
FORBIDDEN_OPERATIONAL_PATTERNS = (
    "HF_TOKEN: ${{ secrets.HF_TOKEN }}",
    "HF_NUMERIC_BASELINE_DATASET_REPO: ${{",
    "HF_DOMAIN_BENCHMARK_DATASET_REPO: ${{",
    "HF_EXTERNAL_REALITY_DATASET_REPO: ${{",
    "HF_CLOUDFLARE_DATASET_REPO: ${{",
    "python api-center/cloudflare/hf_archive.py",
    " --commit-to-hf",
    " build-hf ",
)


def _operational_workflow_text(text: str) -> str:
    """Ignore self-check lines that quote forbidden markers as test data."""
    kept = []
    for line in text.splitlines():
        stripped = line.strip()
        if "grep -q" in stripped or "grep -Eq" in stripped:
            continue
        if stripped.startswith("echo ") and "forbidden" in stripped.lower():
            continue
        kept.append(line)
    return "\n".join(kept)


def validate() -> dict[str, object]:
    role = json.loads(ROLE.read_text(encoding="utf-8"))
    expected = {
        "schema_version": "compute-center-baseline-library-role-v2",
        "beneficiary_center": "a15280020511/compute-simulation-center",
        "data_producer": "a15280020511/evidence-data-center",
        "storage_gateway_owner": "a15280020511/decision-system-governance",
        "external_controller": "gpts-via-decision-system-governance-only",
        "intelligence_center_private_dataset_credentials_allowed": False,
        "intelligence_center_direct_dataset_read_allowed": False,
        "intelligence_center_direct_dataset_write_allowed": False,
        "compute_center_direct_dataset_access_allowed": False,
        "expert_center_dataset_access_allowed": False,
        "knowledge_base_storage_allowed": False,
        "knowledge_graph_storage_allowed": False,
    }
    mismatches = [key for key, value in expected.items() if role.get(key) != value]
    if mismatches:
        raise RuntimeError("baseline role mismatch: " + ", ".join(mismatches))

    checked: list[str] = []
    violations: list[str] = []
    for raw in PRIVATE_STORAGE_WORKFLOWS:
        path = ROOT / raw
        if not path.is_file():
            raise RuntimeError(f"required workflow missing: {raw}")
        text = _operational_workflow_text(path.read_text(encoding="utf-8"))
        checked.append(raw)
        for pattern in FORBIDDEN_OPERATIONAL_PATTERNS:
            if pattern in text:
                violations.append(f"{raw}:{pattern}")
    if violations:
        raise RuntimeError("forbidden private storage path: " + "; ".join(violations))

    public_hf = (ROOT / ".github/workflows/huggingface-api-ticket.yml").read_text(encoding="utf-8")
    if 'HF_TOKEN: ""' not in public_hf or 'HUGGING_FACE_HUB_TOKEN: ""' not in public_hf:
        raise RuntimeError("public Hugging Face provider must explicitly disable authentication")

    if (ROOT / "api-center/cloudflare/hf_archive.py").exists():
        raise RuntimeError("private Cloudflare Hugging Face archive adapter must remain deleted")
    if (ROOT / "api-center/cloudflare/tests/test_hf_archive.py").exists():
        raise RuntimeError("obsolete private archive tests must remain deleted")

    runtime = (
        ROOT
        / "api-center/cloudflare/numeric-compiler/cloudflare_numeric_compiler_runtime.py"
    ).read_text(encoding="utf-8")
    required_runtime_markers = (
        "direct Hugging Face commit is forbidden",
        "BASE.execute = execute",
        '"governance_artifact_required": True',
        '"a15280020511/decision-system-governance"',
    )
    missing = [marker for marker in required_runtime_markers if marker not in runtime]
    if missing:
        raise RuntimeError("runtime fail-closed markers missing: " + ", ".join(missing))

    export = (ROOT / "api-center/huggingface/build_governance_baseline_export.py").read_text(
        encoding="utf-8"
    )
    for marker in (
        'SCHEMA_VERSION = "governance-baseline-export-v1"',
        'PRODUCER_REPOSITORY = "a15280020511/evidence-data-center"',
        '"direct_huggingface_write": False',
    ):
        if marker not in export:
            raise RuntimeError(f"governance export marker missing: {marker}")

    return {
        "status": "EVIDENCE_STORAGE_TOPOLOGY_VALIDATED",
        "checked_workflow_count": len(checked),
        "public_huggingface_provider_retained": True,
        "public_huggingface_authentication_used": False,
        "private_huggingface_storage_in_evidence_center": False,
        "storage_gateway_owner": "a15280020511/decision-system-governance",
        "compute_direct_huggingface_access": False,
        "secret_values_exposed": False,
        "model_calls": 0,
    }


def main() -> int:
    receipt = validate()
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
