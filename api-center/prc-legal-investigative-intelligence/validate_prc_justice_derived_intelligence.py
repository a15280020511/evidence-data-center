#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
SCHEMA = HERE / "prc-justice-derived-intelligence-record.schema.json"
MESH = HERE / "prc-justice-intelligence-mesh.json"
TRANSFORM = HERE / "transform_prc_justice_with_cloudflare_v2.py"
ENCRYPT = HERE / "encrypt_prc_justice_hf_handoff.py"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate() -> dict[str, Any]:
    schema = load(SCHEMA)
    Draft202012Validator.check_schema(schema)
    props = set((schema.get("properties") or {}).keys())
    forbidden_fields = {"source_url","raw_text","raw_source_text","raw_model_response","full_text","quote"}
    if props & forbidden_fields:
        raise RuntimeError("derived record schema exposes raw-source fields")
    safety = ((schema.get("properties") or {}).get("safety") or {}).get("properties") or {}
    for key in ("raw_source_text_stored","raw_source_url_stored","raw_model_response_stored","personal_targeting","secret_operational_detail","evasion_or_anti_forensics"):
        if (safety.get(key) or {}).get("const") is not False:
            raise RuntimeError(f"unsafe derived-record safety field: {key}")

    mesh = load(MESH)
    if mesh.get("schema_version") != "prc-justice-intelligence-mesh-v1":
        raise RuntimeError("mesh schema mismatch")
    if len(mesh.get("core_dimensions") or []) != 6:
        raise RuntimeError("exactly six core analysis dimensions are required")
    sections = set(((mesh.get("derived_storage") or {}).get("sections") or []))
    required_sections = {"signals","capabilities","technology_lifecycle","practice_standards","doctrine","procurement_and_deployment","institutions_regions","judicial_outcomes","trend_snapshots","model_findings","compute_indices","report_snapshots"}
    if sections != required_sections:
        raise RuntimeError("derived HF section set is incomplete")
    forbidden = set(((mesh.get("derived_storage") or {}).get("forbidden") or []))
    for item in ("raw_web_page_text","raw_pdf_text","raw_source_url","raw_model_response","personal_targeting_data","secret_operational_details","evasion_or_anti_forensics_content"):
        if item not in forbidden:
            raise RuntimeError(f"missing HF storage prohibition: {item}")
    strategy = mesh.get("collection_strategy") or {}
    if int(strategy.get("max_cloudflare_ai_pages_per_cycle") or 0) != 6:
        raise RuntimeError("Cloudflare AI cycle bound must remain six pages")
    data_flow = mesh.get("data_flow") or []
    for stage in (
        "cloudflare_schema_constrained_transform",
        "encrypt_export_for_governance_with_current_public_key",
        "post_ciphertext_only_to_evidence_handoff_issue",
        "governance_poll_decrypt_validate_and_write_private_hf_dataset",
    ):
        if stage not in data_flow:
            raise RuntimeError(f"required derived-intelligence data-flow stage missing: {stage}")
    transport = mesh.get("cross_repository_transport") or {}
    expected_transport = {
        "mode": "encrypted_issue_mailbox",
        "algorithm": "X25519-HKDF-SHA256-CHACHA20POLY1305",
        "cross_repo_actions_permission_required": False,
        "cross_repo_contents_permission_required": False,
        "plaintext_issue_transport": False,
        "hf_token_in_evidence_center": False,
        "raw_source_in_transport": False,
        "raw_model_response_in_transport": False,
    }
    for key, expected in expected_transport.items():
        if transport.get(key) != expected:
            raise RuntimeError(f"encrypted transport contract mismatch: {key}")

    transform_text = TRANSFORM.read_text(encoding="utf-8")
    transform_markers = (
        'f"{API_BASE}/accounts/{account}/browser-rendering/json"',
        '"raw_source_text_persisted": False',
        '"raw_source_url_in_hf_export": False',
        '"raw_model_response_persisted": False',
        '"raw_html_persisted": False',
        '"direct_huggingface_write": False',
        '"storage_gateway_owner": "a15280020511/decision-system-governance"',
        'MAX_PAGES = 6',
        'if response.status_code == 429',
        'if status != 422',
        '_fetch_verified_html(url)',
        '"simple-json-schema-plus-local-strict-validation"',
    )
    missing = [item for item in transform_markers if item not in transform_text]
    if missing:
        raise RuntimeError("transform v2 safety/resilience markers missing: " + ", ".join(missing))

    encrypt_text = ENCRYPT.read_text(encoding="utf-8")
    encrypt_markers = (
        'ENVELOPE_SCHEMA = "governance-prc-justice-encrypted-handoff-v1"',
        'KDF_CONTEXT = b"prc-justice-hf-encrypted-issue-v1"',
        'ChaCha20Poly1305(key).encrypt',
        'x25519.X25519PrivateKey.generate()',
        'MAX_PLAINTEXT_BYTES = 36 * 1024',
        '"plaintext_issue_transport":False',
        '"raw_source_text_in_transport":False',
        '"github_cross_repo_actions_permission_required":False',
        '"hf_token_required_in_evidence_center":False',
    )
    missing = [item for item in encrypt_markers if item not in encrypt_text]
    if missing:
        raise RuntimeError("encrypted handoff builder markers missing: " + ", ".join(missing))
    return {
        "status": "PRC_JUSTICE_DERIVED_INTELLIGENCE_ENCRYPTED_TRANSPORT_VALIDATED",
        "core_dimension_count": 6,
        "hf_section_count": len(sections),
        "cloudflare_ai_pages_per_cycle": 6,
        "cloudflare_url_first": True,
        "bounded_in_memory_html_fallback_on_422": True,
        "encrypted_issue_transport": True,
        "cross_repo_actions_permission_required": False,
        "cross_repo_contents_permission_required": False,
        "hf_token_in_evidence_center": False,
        "raw_html_persisted": False,
        "raw_source_in_hf": False,
        "raw_model_response_in_hf": False,
        "direct_hf_write": False,
        "storage_gateway": "a15280020511/decision-system-governance",
        "model_calls": 0,
        "network_used": False,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, sort_keys=True))
