#!/usr/bin/env python3
"""Initialize and verify the private Hugging Face external reality library.

This adapter belongs to the Evidence & Data Center. It may access Hugging Face
only inside its managed GitHub workflow. The Compute Center remains network-denied
and receives only GPTs-mediated immutable snapshots, manifests, and hashes.
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
LIBRARY_SOURCE = HERE / "external-reality-library"
REGISTRY_PATH = LIBRARY_SOURCE / "registry.json"
RECORD_SCHEMA_PATH = LIBRARY_SOURCE / "record.schema.json"
HF_ORIGIN = "https://huggingface.co"
HF_TOKEN_ENV = "HF_TOKEN"
HF_REPO_ENV = "HF_EXTERNAL_REALITY_DATASET_REPO"
HF_BENCHMARK_REPO_ENV = "HF_DOMAIN_BENCHMARK_DATASET_REPO"
HF_FALLBACK_REPO_ENV = "HF_CLOUDFLARE_DATASET_REPO"
DEFAULT_REPO_NAME = "cloudflare-intelligence-archive"
REMOTE_ROOT = "external-reality/v1/control"

EXPECTED_DOMAINS = {
    "macroeconomy-fiscal-monetary",
    "enterprise-commerce-industry",
    "finance-capital-markets",
    "law-policy-regulation",
    "population-labor-income",
    "geospatial-land-urban",
    "transport-logistics-ports",
    "energy-power-resources",
    "international-trade-supply-chain",
    "agriculture-food-commodities",
    "environment-climate-weather",
    "public-health-healthcare",
    "science-technology-patents",
    "education-human-capital",
    "public-safety-emergency",
    "media-news-public-opinion",
    "infrastructure-telecom-internet",
    "government-public-services",
}
EXPECTED_COLLECTION_LAYERS = {
    "sources",
    "raw-snapshots",
    "normalized-records",
    "time-series",
    "entity-master",
    "variable-dictionaries",
    "crosswalks",
    "derived-indicators",
    "rule-snapshots",
    "event-timelines",
    "quality-reports",
    "licenses-provenance",
    "manifests",
}


class ExternalRealityStoreError(RuntimeError):
    """Raised when the external reality library cannot be validated or synchronized."""


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


def validate_registry(document: Mapping[str, Any]) -> dict[str, Any]:
    if document.get("schema_version") != "external-reality-library-registry-v1":
        raise ExternalRealityStoreError("unsupported external reality registry schema")
    if document.get("status") != "structure-complete-data-pending":
        raise ExternalRealityStoreError("external reality registry status must remain data-pending")

    storage = document.get("storage_contract")
    if not isinstance(storage, Mapping):
        raise ExternalRealityStoreError("storage contract is required")
    expected_storage = {
        "provider": "huggingface",
        "repo_type": "dataset",
        "private_required": True,
        "remote_root": REMOTE_ROOT,
        "authoritative_storage_owner": "evidence-data-center",
        "selection_and_transfer_owner": "gpts-usage-center",
        "compute_runtime_network_allowed": False,
        "direct_center_to_center_connection_allowed": False,
        "raw_secrets_allowed": False,
        "personal_data_default_allowed": False,
        "append_only_versions": True,
        "immutable_hash_required": True,
    }
    for key, expected in expected_storage.items():
        if storage.get(key) != expected:
            raise ExternalRealityStoreError(f"invalid storage contract: {key}")

    domains = document.get("domains")
    layers = document.get("collection_layers")
    fields = document.get("record_requirements")
    if not isinstance(domains, list) or not isinstance(layers, list) or not isinstance(fields, list):
        raise ExternalRealityStoreError("external reality registry is incomplete")

    domain_ids = [str(row.get("id") or "") for row in domains if isinstance(row, Mapping)]
    layer_ids = [str(row.get("id") or "") for row in layers if isinstance(row, Mapping)]
    if len(domain_ids) != len(domains) or set(domain_ids) != EXPECTED_DOMAINS or len(set(domain_ids)) != len(domain_ids):
        raise ExternalRealityStoreError("external reality domain registry is incomplete or duplicated")
    if len(layer_ids) != len(layers) or set(layer_ids) != EXPECTED_COLLECTION_LAYERS or len(set(layer_ids)) != len(layer_ids):
        raise ExternalRealityStoreError("external reality collection layers are incomplete or duplicated")
    if len(fields) < 18 or len(set(str(item) for item in fields)) != len(fields):
        raise ExternalRealityStoreError("external reality record requirements are incomplete or duplicated")

    for row in domains:
        for key in ("id", "priority", "purpose", "required_collections", "geographic_scope", "preferred_granularity"):
            if key not in row:
                raise ExternalRealityStoreError(f"domain row missing {key}: {row.get('id')}")
        if row.get("priority") not in {"P1", "P2", "P3"}:
            raise ExternalRealityStoreError(f"invalid domain priority: {row.get('id')}")
        for key in ("required_collections", "geographic_scope", "preferred_granularity"):
            value = row.get(key)
            if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item for item in value):
                raise ExternalRealityStoreError(f"invalid {key}: {row.get('id')}")

    for row in layers:
        if not isinstance(row, Mapping) or not row.get("id") or not row.get("purpose"):
            raise ExternalRealityStoreError("invalid collection layer row")

    return {
        "domains": domains,
        "collection_layers": layers,
        "record_requirements": fields,
        "registry_sha256": canonical_sha(document),
    }


def validate_record_schema(document: Mapping[str, Any]) -> str:
    if document.get("$id") != "external-reality-record-v1":
        raise ExternalRealityStoreError("external reality record schema ID mismatch")
    required = set(document.get("required") or [])
    if not set(load_json(REGISTRY_PATH)["record_requirements"]).issubset(required):
        raise ExternalRealityStoreError("record schema does not require every registry field")
    properties = document.get("properties")
    if not isinstance(properties, Mapping):
        raise ExternalRealityStoreError("record schema properties are missing")
    if properties.get("contains_personal_data", {}).get("const") is not False:
        raise ExternalRealityStoreError("record schema must reject personal data")
    return canonical_sha(document)


def build_bundle(output_dir: Path) -> dict[str, Any]:
    registry = load_json(REGISTRY_PATH)
    validation = validate_registry(registry)
    schema = load_json(RECORD_SCHEMA_PATH)
    schema_sha = validate_record_schema(schema)

    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REGISTRY_PATH, output_dir / "registry.json")
    shutil.copy2(RECORD_SCHEMA_PATH, output_dir / "record.schema.json")

    template = {
        "schema_version": "external-reality-collection-template-v1",
        "record_schema": f"{REMOTE_ROOT}/record.schema.json",
        "status": "data-pending",
        "required_fields": validation["record_requirements"],
        "storage_owner": "evidence-data-center",
        "selection_and_transfer_owner": "gpts-usage-center",
        "append_only_versions": True,
        "immutable_hash_required": True,
        "compute_runtime_network_allowed": False,
        "direct_center_connection_allowed": False,
        "raw_secrets_allowed": False,
        "contains_personal_data": False,
    }
    write_json(output_dir / "collection-template.json", template)

    domain_rows = []
    for domain in validation["domains"]:
        domain_id = str(domain["id"])
        layer_rows = []
        for layer in validation["collection_layers"]:
            layer_id = str(layer["id"])
            relative = Path("domains") / domain_id / layer_id / "README.json"
            write_json(
                output_dir / relative,
                {
                    "schema_version": "external-reality-collection-directory-v1",
                    "domain": domain_id,
                    "collection_layer": layer_id,
                    "status": "data-pending",
                    "purpose": layer["purpose"],
                    "record_schema": f"{REMOTE_ROOT}/record.schema.json",
                    "collection_template": f"{REMOTE_ROOT}/collection-template.json",
                    "append_only_versions": True,
                    "immutable_hash_required": True,
                    "compute_runtime_network_allowed": False,
                    "direct_center_connection_allowed": False,
                    "raw_secrets_allowed": False,
                    "contains_personal_data_default": False,
                },
            )
            layer_rows.append(
                {"collection_layer": layer_id, "status": "data-pending", "path": relative.as_posix()}
            )

        requirements_path = Path("domains") / domain_id / "requirements.json"
        write_json(
            output_dir / requirements_path,
            {
                "schema_version": "external-reality-domain-requirements-v1",
                "domain": domain_id,
                "priority": domain["priority"],
                "status": "data-pending",
                "purpose": domain["purpose"],
                "required_collections": domain["required_collections"],
                "geographic_scope": domain["geographic_scope"],
                "preferred_granularity": domain["preferred_granularity"],
                "collection_layers": layer_rows,
                "record_schema": f"{REMOTE_ROOT}/record.schema.json",
                "runtime_contract": {
                    "storage_owner": "evidence-data-center",
                    "selection_and_transfer_owner": "gpts-usage-center",
                    "compute_runtime_network_allowed": False,
                    "direct_center_connection_allowed": False,
                },
            },
        )
        domain_rows.append(
            {
                "domain": domain_id,
                "priority": domain["priority"],
                "status": "data-pending",
                "requirements_path": requirements_path.as_posix(),
                "collection_layer_count": len(layer_rows),
            }
        )

    index = {
        "schema_version": "external-reality-library-index-v1",
        "status": "initialized-data-pending",
        "provider": "huggingface",
        "repo_type": "dataset",
        "private_required": True,
        "remote_root": REMOTE_ROOT,
        "registry_sha256": validation["registry_sha256"],
        "record_schema_sha256": schema_sha,
        "domain_count": len(EXPECTED_DOMAINS),
        "collection_layer_count": len(EXPECTED_COLLECTION_LAYERS),
        "domains": domain_rows,
        "storage_owner": "evidence-data-center",
        "selection_and_transfer_owner": "gpts-usage-center",
        "compute_runtime_network_allowed": False,
        "direct_center_connection_allowed": False,
        "secret_values_exposed": False,
        "model_calls": 0,
    }
    write_json(output_dir / "external-reality-index.json", index)

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
        "schema_version": "external-reality-control-bundle-v1",
        "generated_from": "evidence-data-center",
        "remote_root": REMOTE_ROOT,
        "files": files,
        "file_count": len(files),
        "bundle_sha256": canonical_sha(files),
        "domain_count": len(EXPECTED_DOMAINS),
        "collection_layer_count": len(EXPECTED_COLLECTION_LAYERS),
        "directories_per_domain": len(EXPECTED_COLLECTION_LAYERS),
        "secret_values_exposed": False,
        "model_calls": 0,
    }
    write_json(output_dir / "bundle-manifest.json", bundle)
    return bundle


def resolve_repo_id(
    api: Any,
    token: str,
    override: str | None,
    benchmark_repo: str | None,
    fallback_repo: str | None,
) -> tuple[str, str]:
    identity = api.whoami(token=token)
    if not isinstance(identity, Mapping) or not identity.get("name"):
        raise ExternalRealityStoreError("Hugging Face whoami did not return an account name")
    account = str(identity["name"])
    requested = str(override or benchmark_repo or fallback_repo or "").strip()
    repo_id = requested or f"{account}/{DEFAULT_REPO_NAME}"
    parts = repo_id.split("/")
    if len(parts) != 2 or any(not part or len(part) > 96 for part in parts):
        raise ExternalRealityStoreError("external reality dataset repo must use owner/name")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    if any(any(character not in allowed for character in part) for part in parts):
        raise ExternalRealityStoreError("external reality dataset repo contains unsafe characters")
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
    benchmark_repo: str | None,
    fallback_repo: str | None,
    output_dir: Path,
    api: Any | None = None,
) -> dict[str, Any]:
    if not token:
        raise ExternalRealityStoreError(f"{HF_TOKEN_ENV} is not configured")
    client = api or HfApi(
        endpoint=HF_ORIGIN,
        token=False,
        library_name="intelligence-center-external-reality-store",
        library_version="1",
    )
    repo_id, account = resolve_repo_id(client, token, repo_override, benchmark_repo, fallback_repo)
    client.create_repo(repo_id=repo_id, repo_type="dataset", private=True, exist_ok=True, token=token)
    info = client.dataset_info(repo_id, token=token, timeout=30)
    if getattr(info, "private", None) is not True:
        raise ExternalRealityStoreError("external reality dataset repository must be private")

    with tempfile.TemporaryDirectory(prefix="external-reality-library-") as temp:
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
                commit_message="initialize governed external reality database v1",
            )
            commit_oid = str(getattr(upload, "oid", "") or "")

        expected = {f"{REMOTE_ROOT}/{row['path']}" for row in local_bundle["files"]}
        expected.add(f"{REMOTE_ROOT}/bundle-manifest.json")
        remote_files = set(client.list_repo_files(repo_id=repo_id, repo_type="dataset", token=token))
        missing = sorted(expected - remote_files)
        if missing:
            raise ExternalRealityStoreError(f"remote external reality control files missing: {missing[:10]}")

        remote_after = _remote_manifest(repo_id, token) if api is None else local_bundle
        if not remote_after or remote_after.get("bundle_sha256") != local_bundle["bundle_sha256"]:
            raise ExternalRealityStoreError("remote external reality bundle hash mismatch")

    receipt = {
        "schema_version": "hf-external-reality-library-receipt-v1",
        "status": "HF_EXTERNAL_REALITY_LIBRARY_CONNECTED",
        "account": account,
        "repo_id": repo_id,
        "repo_type": "dataset",
        "private": True,
        "remote_root": REMOTE_ROOT,
        "bundle_sha256": remote_after["bundle_sha256"],
        "file_count": remote_after["file_count"] + 1,
        "domain_count": len(EXPECTED_DOMAINS),
        "collection_layer_count": len(EXPECTED_COLLECTION_LAYERS),
        "directories_per_domain": len(EXPECTED_COLLECTION_LAYERS),
        "commit_oid": commit_oid,
        "unchanged": unchanged,
        "domains": sorted(EXPECTED_DOMAINS),
        "collection_layers": sorted(EXPECTED_COLLECTION_LAYERS),
        "compute_runtime_network_used": False,
        "evidence_center_network_used": True,
        "direct_center_connection": False,
        "secret_values_exposed": False,
        "model_calls": 0,
        "connected_at": date.today().isoformat(),
    }
    write_json(output_dir / "hf-external-reality-library-receipt.json", receipt)
    return receipt


def render_receipt(output_dir: Path) -> int:
    path = output_dir / "hf-external-reality-library-receipt.json"
    if not path.exists():
        print("Hugging Face external reality library: `FAILED`")
        return 1
    receipt = load_json(path)
    print(f"Hugging Face external reality library: `{receipt.get('status', 'UNKNOWN')}`")
    print(f"\n- Dataset: `{receipt.get('repo_id', '')}`")
    print(f"- Root: `{receipt.get('remote_root', '')}`")
    print(f"- Control files: `{receipt.get('file_count', 0)}`")
    print(f"- Reality domains: `{receipt.get('domain_count', 0)}`")
    print(f"- Collection layers per domain: `{receipt.get('directories_per_domain', 0)}`")
    print(f"- Bundle SHA256: `{receipt.get('bundle_sha256', '')}`")
    print("- Private repository: `true`")
    print("- Compute runtime network used: `false`")
    print("- Direct center connection: `false`")
    print("- Secret values exposed: `false`")
    return 0 if receipt.get("status") == "HF_EXTERNAL_REALITY_LIBRARY_CONNECTED" else 1


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
            benchmark_repo=os.getenv(HF_BENCHMARK_REPO_ENV),
            fallback_repo=os.getenv(HF_FALLBACK_REPO_ENV),
            output_dir=output_dir,
        )
        return 0
    except Exception as exc:
        write_json(
            output_dir / "hf-external-reality-library-receipt.json",
            {
                "schema_version": "hf-external-reality-library-receipt-v1",
                "status": "HF_EXTERNAL_REALITY_LIBRARY_FAILED",
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
