#!/usr/bin/env python3
"""Initialize and verify the private Hugging Face domain benchmark material library.

This adapter belongs to the Intelligence Center. It may use the network only inside
its managed GitHub workflow. The Compute Center remains network-denied and consumes
only GPTs-mediated immutable snapshots, manifests, and hashes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from datetime import date
from pathlib import Path
from typing import Any, Mapping

from huggingface_hub import HfApi, hf_hub_download

HERE = Path(__file__).resolve().parent
LIBRARY_SOURCE = HERE / "domain-benchmark-library"
REQUIREMENTS_PATH = LIBRARY_SOURCE / "requirements.json"
SCHEMA_PATH = LIBRARY_SOURCE / "manifest.schema.json"
MATERIAL_DIRECTORY_PATH = LIBRARY_SOURCE / "material-directory-registry.json"
HF_ORIGIN = "https://huggingface.co"
HF_TOKEN_ENV = "HF_TOKEN"
HF_REPO_ENV = "HF_DOMAIN_BENCHMARK_DATASET_REPO"
HF_FALLBACK_REPO_ENV = "HF_CLOUDFLARE_DATASET_REPO"
DEFAULT_REPO_NAME = "cloudflare-intelligence-archive"
REMOTE_ROOT = "domain-benchmarks/v1/control"
EXPECTED_DOMAINS = {
    "commercial-footfall",
    "finance-investment",
    "public-policy",
    "social-behavior",
    "information-diffusion",
    "crisis-warning",
    "resource-optimization",
    "china-real-world",
}
EXPECTED_ASSET_LIBRARIES = {
    "sample-library",
    "factor-library",
    "domain-rule-snapshot-library",
    "baseline-library",
    "metric-threshold-library",
    "outcome-feedback-library",
    "ontology-crosswalk-library",
    "regime-event-library",
    "source-catalog-library",
    "data-dictionary-library",
    "license-provenance-library",
    "benchmark-manifest-library",
}
EXPECTED_MATERIAL_DIRECTORIES = {
    "sources",
    "snapshots",
    "variable-dictionaries",
    "factors",
    "rule-snapshots",
    "baselines",
    "metric-thresholds",
    "regime-events",
    "crosswalks",
    "outcome-feedback",
    "licenses-provenance",
    "manifests",
}


class DomainBenchmarkStoreError(RuntimeError):
    """Raised when the benchmark material library cannot be validated or synchronized."""


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def redact(message: str, token: str) -> str:
    text = str(message)
    if token:
        text = text.replace(token, "[REDACTED]")
    return text.replace("\n", " ")[:1600]


def _validate_material_directory_registry(document: Mapping[str, Any]) -> dict[str, Any]:
    if document.get("schema_version") != "domain-benchmark-material-directory-registry-v1":
        raise DomainBenchmarkStoreError("unsupported material directory registry schema")
    additional = document.get("additional_asset_libraries")
    directories = document.get("domain_material_directories")
    policies = document.get("policies")
    if not isinstance(additional, list) or not isinstance(directories, list) or not isinstance(policies, Mapping):
        raise DomainBenchmarkStoreError("material directory registry is incomplete")
    additional_ids = {str(row.get("id") or "") for row in additional if isinstance(row, Mapping)}
    directory_ids = {str(row.get("id") or "") for row in directories if isinstance(row, Mapping)}
    if additional_ids != {
        "source-catalog-library",
        "data-dictionary-library",
        "license-provenance-library",
        "benchmark-manifest-library",
    }:
        raise DomainBenchmarkStoreError("additional asset library registry is incomplete")
    if directory_ids != EXPECTED_MATERIAL_DIRECTORIES:
        raise DomainBenchmarkStoreError("domain material directory registry is incomplete")
    required_policies = {
        "private_dataset_required": True,
        "append_only_versions": True,
        "immutable_hash_required": True,
        "raw_secrets_allowed": False,
        "compute_runtime_network_allowed": False,
        "direct_center_connection_allowed": False,
    }
    for key, expected in required_policies.items():
        if policies.get(key) != expected:
            raise DomainBenchmarkStoreError(f"invalid material directory policy: {key}")
    return {
        "additional_asset_libraries": additional,
        "domain_material_directories": directories,
        "material_directory_sha256": canonical_sha(document),
    }


def validate_requirements(document: Mapping[str, Any]) -> dict[str, Any]:
    if document.get("schema_version") != "domain-benchmark-library-requirements-v1":
        raise DomainBenchmarkStoreError("unsupported requirements schema")
    storage = document.get("storage_contract")
    if not isinstance(storage, Mapping):
        raise DomainBenchmarkStoreError("storage_contract is required")
    required_storage = {
        "provider": "huggingface",
        "repo_type": "dataset",
        "private_required": True,
        "compute_runtime_network_allowed": False,
        "direct_center_to_center_connection_allowed": False,
        "raw_secrets_in_records_allowed": False,
    }
    for key, expected in required_storage.items():
        if storage.get(key) != expected:
            raise DomainBenchmarkStoreError(f"invalid storage contract: {key}")

    domains = document.get("domains")
    if not isinstance(domains, list):
        raise DomainBenchmarkStoreError("domains must be a list")
    domain_ids = [str(row.get("id") or "") for row in domains if isinstance(row, Mapping)]
    if len(domain_ids) != len(domains) or set(domain_ids) != EXPECTED_DOMAINS or len(set(domain_ids)) != len(domain_ids):
        raise DomainBenchmarkStoreError("domain registry is incomplete or duplicated")
    for row in domains:
        for field in ("required_datasets", "required_baselines", "required_metrics"):
            values = row.get(field)
            if not isinstance(values, list) or not values or any(not isinstance(item, str) or not item for item in values):
                raise DomainBenchmarkStoreError(f"invalid {field} for domain {row.get('id')}")

    base_libraries = document.get("required_asset_libraries")
    if not isinstance(base_libraries, list):
        raise DomainBenchmarkStoreError("required_asset_libraries must be a list")
    base_ids = [str(row.get("id") or "") for row in base_libraries if isinstance(row, Mapping)]
    material = _validate_material_directory_registry(load_json(MATERIAL_DIRECTORY_PATH))
    combined = list(base_libraries) + list(material["additional_asset_libraries"])
    combined_ids = [str(row.get("id") or "") for row in combined if isinstance(row, Mapping)]
    if len(combined_ids) != len(combined) or set(combined_ids) != EXPECTED_ASSET_LIBRARIES or len(set(combined_ids)) != len(combined_ids):
        raise DomainBenchmarkStoreError("combined asset library registry is incomplete or duplicated")

    evidence = document.get("required_evidence_per_benchmark")
    fields = document.get("required_record_fields")
    if not isinstance(evidence, list) or len(evidence) < 8:
        raise DomainBenchmarkStoreError("benchmark evidence requirements are incomplete")
    if not isinstance(fields, list) or len(fields) < 12:
        raise DomainBenchmarkStoreError("benchmark record requirements are incomplete")

    return {
        "schema_version": document["schema_version"],
        "domains": sorted(domain_ids),
        "asset_libraries": sorted(combined_ids),
        "asset_library_rows": combined,
        "material_directories": material["domain_material_directories"],
        "requirements_sha256": canonical_sha(document),
        "material_directory_sha256": material["material_directory_sha256"],
    }


def build_bundle(output_dir: Path) -> dict[str, Any]:
    requirements = load_json(REQUIREMENTS_PATH)
    validation = validate_requirements(requirements)
    schema = load_json(SCHEMA_PATH)
    if schema.get("$id") != "domain-benchmark-manifest-v1":
        raise DomainBenchmarkStoreError("manifest schema ID mismatch")

    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REQUIREMENTS_PATH, output_dir / "requirements.json")
    shutil.copy2(SCHEMA_PATH, output_dir / "manifest.schema.json")
    shutil.copy2(MATERIAL_DIRECTORY_PATH, output_dir / "material-directory-registry.json")

    domain_rows = []
    for domain in requirements["domains"]:
        domain_id = domain["id"]
        material_rows = []
        for material in validation["material_directories"]:
            directory_id = material["id"]
            relative = Path("domains") / domain_id / directory_id / "README.json"
            write_json(
                output_dir / relative,
                {
                    "schema_version": "domain-benchmark-material-directory-v1",
                    "domain": domain_id,
                    "directory_id": directory_id,
                    "status": "data-pending",
                    "purpose": material["purpose"],
                    "storage_owner": "evidence-data-center",
                    "selection_owner": "gpts-usage-center",
                    "compute_runtime_network_allowed": False,
                    "direct_center_connection": False,
                    "immutable_snapshot_hash_required": True,
                    "raw_secrets_allowed": False,
                },
            )
            material_rows.append({"directory_id": directory_id, "status": "data-pending", "path": relative.as_posix()})

        domain_record = {
            "schema_version": "domain-benchmark-domain-requirements-v2",
            "domain": domain_id,
            "priority": domain["priority"],
            "status": "data-pending",
            "required_datasets": domain["required_datasets"],
            "required_baselines": domain["required_baselines"],
            "required_metrics": domain["required_metrics"],
            "required_evidence": requirements["required_evidence_per_benchmark"],
            "material_directories": material_rows,
            "manifest_schema": f"{REMOTE_ROOT}/manifest.schema.json",
            "runtime_contract": {
                "storage_owner": "evidence-data-center",
                "selection_owner": "gpts-usage-center",
                "compute_network_used": False,
                "direct_center_connection": False,
            },
        }
        relative = Path("domains") / domain_id / "requirements.json"
        write_json(output_dir / relative, domain_record)
        domain_rows.append(
            {
                "domain": domain_id,
                "priority": domain["priority"],
                "status": "data-pending",
                "requirements_path": relative.as_posix(),
                "material_directory_count": len(material_rows),
            }
        )

    asset_rows = []
    for library in validation["asset_library_rows"]:
        library_id = library["id"]
        relative = Path("asset-libraries") / library_id / "README.json"
        write_json(
            output_dir / relative,
            {
                "schema_version": "domain-benchmark-asset-library-v2",
                "library_id": library_id,
                "status": "data-pending",
                "purpose": library["purpose"],
                "append_only_versions": True,
                "immutable_snapshot_hash_required": True,
                "runtime_network_allowed": False,
                "raw_secrets_allowed": False,
            },
        )
        asset_rows.append({"library_id": library_id, "status": "data-pending", "path": relative.as_posix()})

    library_index = {
        "schema_version": "domain-benchmark-library-index-v2",
        "status": "initialized-data-pending",
        "provider": "huggingface",
        "repo_type": "dataset",
        "private_required": True,
        "remote_root": REMOTE_ROOT,
        "requirements_sha256": validation["requirements_sha256"],
        "material_directory_sha256": validation["material_directory_sha256"],
        "manifest_schema_sha256": sha256_file(output_dir / "manifest.schema.json"),
        "domains": domain_rows,
        "asset_libraries": asset_rows,
        "domain_material_directory_count": len(EXPECTED_MATERIAL_DIRECTORIES),
        "promotion_rule": "No domain benchmark may become production or decision-grade without frozen real data, baselines, sample-out evidence, adversarial checks and applicable shadow feedback.",
        "compute_runtime_network_allowed": False,
        "direct_center_connection": False,
        "model_calls": 0,
    }
    write_json(output_dir / "library-index.json", library_index)

    files = []
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name != "bundle-manifest.json":
            files.append(
                {
                    "path": path.relative_to(output_dir).as_posix(),
                    "sha256": sha256_file(path),
                    "bytes": path.stat().st_size,
                }
            )
    bundle = {
        "schema_version": "domain-benchmark-control-bundle-v2",
        "generated_from": "evidence-data-center",
        "remote_root": REMOTE_ROOT,
        "files": files,
        "file_count": len(files),
        "bundle_sha256": canonical_sha(files),
        "domain_count": len(EXPECTED_DOMAINS),
        "asset_library_count": len(EXPECTED_ASSET_LIBRARIES),
        "material_directories_per_domain": len(EXPECTED_MATERIAL_DIRECTORIES),
        "secret_values_exposed": False,
        "model_calls": 0,
    }
    write_json(output_dir / "bundle-manifest.json", bundle)
    return bundle


def resolve_repo_id(api: Any, token: str, override: str | None, fallback: str | None) -> tuple[str, str]:
    identity = api.whoami(token=token)
    if not isinstance(identity, Mapping) or not identity.get("name"):
        raise DomainBenchmarkStoreError("Hugging Face whoami did not return an account name")
    account = str(identity["name"])
    requested = str(override or fallback or "").strip()
    repo_id = requested or f"{account}/{DEFAULT_REPO_NAME}"
    parts = repo_id.split("/")
    if len(parts) != 2 or any(not part or len(part) > 96 for part in parts):
        raise DomainBenchmarkStoreError("domain benchmark dataset repo must use owner/name")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    if any(any(character not in allowed for character in part) for part in parts):
        raise DomainBenchmarkStoreError("domain benchmark dataset repo contains unsafe characters")
    return repo_id, account


def _remote_manifest(repo_id: str, token: str) -> dict[str, Any] | None:
    try:
        path = hf_hub_download(
            repo_id=repo_id,
            filename=f"{REMOTE_ROOT}/bundle-manifest.json",
            repo_type="dataset",
            token=token,
        )
    except Exception:
        return None
    value = load_json(Path(path))
    return value if isinstance(value, dict) else None


def sync_library(
    *,
    token: str,
    repo_override: str | None,
    fallback_repo: str | None,
    output_dir: Path,
    api: Any | None = None,
) -> dict[str, Any]:
    if not token:
        raise DomainBenchmarkStoreError(f"{HF_TOKEN_ENV} is not configured")
    client = api or HfApi(
        endpoint=HF_ORIGIN,
        token=False,
        library_name="intelligence-center-domain-benchmark-store",
        library_version="2",
    )
    repo_id, account = resolve_repo_id(client, token, repo_override, fallback_repo)
    client.create_repo(repo_id=repo_id, repo_type="dataset", private=True, exist_ok=True, token=token)
    info = client.dataset_info(repo_id, token=token, timeout=30)
    if getattr(info, "private", None) is not True:
        raise DomainBenchmarkStoreError("domain benchmark dataset repository must be private")

    with tempfile.TemporaryDirectory(prefix="domain-benchmark-library-") as temp:
        staging = Path(temp)
        local_bundle = build_bundle(staging)
        remote_before = _remote_manifest(repo_id, token) if api is None else None
        unchanged = bool(remote_before and remote_before.get("bundle_sha256") == local_bundle["bundle_sha256"])
        commit_oid = "unchanged"
        if not unchanged:
            upload = client.upload_folder(
                repo_id=repo_id,
                repo_type="dataset",
                folder_path=str(staging),
                path_in_repo=REMOTE_ROOT,
                token=token,
                commit_message="expand domain benchmark material directories v2",
            )
            commit_oid = str(getattr(upload, "oid", "") or "")

        expected = {f"{REMOTE_ROOT}/{row['path']}" for row in local_bundle["files"]}
        expected.add(f"{REMOTE_ROOT}/bundle-manifest.json")
        remote_files = set(client.list_repo_files(repo_id=repo_id, repo_type="dataset", token=token))
        missing = sorted(expected - remote_files)
        if missing:
            raise DomainBenchmarkStoreError(f"remote benchmark control files missing: {missing[:10]}")

        remote_after = _remote_manifest(repo_id, token) if api is None else local_bundle
        if not remote_after or remote_after.get("bundle_sha256") != local_bundle["bundle_sha256"]:
            raise DomainBenchmarkStoreError("remote benchmark bundle hash mismatch")

    receipt = {
        "schema_version": "hf-domain-benchmark-library-receipt-v2",
        "status": "HF_DOMAIN_BENCHMARK_LIBRARY_CONNECTED",
        "account": account,
        "repo_id": repo_id,
        "repo_type": "dataset",
        "private": True,
        "remote_root": REMOTE_ROOT,
        "bundle_sha256": remote_after["bundle_sha256"],
        "file_count": remote_after["file_count"] + 1,
        "domain_count": len(EXPECTED_DOMAINS),
        "asset_library_count": len(EXPECTED_ASSET_LIBRARIES),
        "material_directories_per_domain": len(EXPECTED_MATERIAL_DIRECTORIES),
        "commit_oid": commit_oid,
        "unchanged": unchanged,
        "domains": sorted(EXPECTED_DOMAINS),
        "asset_libraries": sorted(EXPECTED_ASSET_LIBRARIES),
        "compute_runtime_network_used": False,
        "evidence_center_network_used": True,
        "direct_center_connection": False,
        "secret_values_exposed": False,
        "model_calls": 0,
        "connected_at": date.today().isoformat(),
    }
    write_json(output_dir / "hf-domain-benchmark-library-receipt.json", receipt)
    return receipt


def render_receipt(output_dir: Path) -> int:
    path = output_dir / "hf-domain-benchmark-library-receipt.json"
    if not path.exists():
        print("Hugging Face domain benchmark library: `FAILED`")
        return 1
    receipt = load_json(path)
    print(f"Hugging Face domain benchmark library: `{receipt.get('status', 'UNKNOWN')}`")
    print(f"\n- Dataset: `{receipt.get('repo_id', '')}`")
    print(f"- Root: `{receipt.get('remote_root', '')}`")
    print(f"- Control files: `{receipt.get('file_count', 0)}`")
    print(f"- Domains: `{receipt.get('domain_count', 0)}`")
    print(f"- Asset libraries: `{receipt.get('asset_library_count', 0)}`")
    print(f"- Material directories per domain: `{receipt.get('material_directories_per_domain', 0)}`")
    print(f"- Bundle SHA256: `{receipt.get('bundle_sha256', '')}`")
    print("- Private repository: `true`")
    print("- Compute runtime network used: `false`")
    print("- Direct center connection: `false`")
    print("- Secret values exposed: `false`")
    return 0 if receipt.get("status") == "HF_DOMAIN_BENCHMARK_LIBRARY_CONNECTED" else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--output-dir", required=True)
    sync_parser = subparsers.add_parser("sync")
    sync_parser.add_argument("--output-dir", required=True)
    render_parser = subparsers.add_parser("render")
    render_parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    output_dir = Path(args.output_dir)

    if args.command == "render":
        return render_receipt(output_dir)
    if args.command == "validate":
        bundle = build_bundle(output_dir)
        print(json.dumps(bundle, ensure_ascii=False, sort_keys=True))
        return 0

    token = str(os.getenv(HF_TOKEN_ENV) or "").strip()
    try:
        sync_library(
            token=token,
            repo_override=os.getenv(HF_REPO_ENV),
            fallback_repo=os.getenv(HF_FALLBACK_REPO_ENV),
            output_dir=output_dir,
        )
        return 0
    except Exception as exc:
        write_json(
            output_dir / "hf-domain-benchmark-library-receipt.json",
            {
                "schema_version": "hf-domain-benchmark-library-receipt-v2",
                "status": "HF_DOMAIN_BENCHMARK_LIBRARY_FAILED",
                "failure": {"type": type(exc).__name__, "message": redact(str(exc), token)},
                "compute_runtime_network_used": False,
                "direct_center_connection": False,
                "secret_values_exposed": False,
                "model_calls": 0,
            },
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
