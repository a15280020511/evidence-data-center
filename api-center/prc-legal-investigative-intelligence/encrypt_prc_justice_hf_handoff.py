#!/usr/bin/env python3
"""Encrypt sanitized PRC justice derived-intelligence exports for Governance.

Only a Governance-published X25519 public key is required. The output is a set of
bounded ciphertext JSON envelopes suitable for posting to Evidence Center Issues.
No GitHub cross-repository Actions/Contents permission and no Hugging Face token is
needed in Evidence Center.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Mapping

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

PUBLIC_KEY_SCHEMA = "governance-prc-justice-transport-public-key-v1"
ENVELOPE_SCHEMA = "governance-prc-justice-encrypted-handoff-v1"
KDF_CONTEXT = b"prc-justice-hf-encrypted-issue-v1"
EXPECTED_PRODUCER = "a15280020511/evidence-data-center"
MAX_PLAINTEXT_BYTES = 36 * 1024
MAX_ISSUE_BODY_BYTES = 63 * 1024
MAX_RECORDS = 2000


class HandoffError(RuntimeError):
    pass


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _unb64(value: Any, name: str, expected: int) -> bytes:
    text = str(value or "").strip()
    try:
        raw = base64.urlsafe_b64decode(text + "=" * ((4 - len(text) % 4) % 4))
    except Exception as exc:
        raise HandoffError(f"{name} is not valid base64url") from exc
    if len(raw) != expected:
        raise HandoffError(f"{name} must decode to {expected} bytes")
    return raw


def validate_public_key(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise HandoffError("Governance transport public key must be an object")
    required = {
        "schema_version","algorithm","key_id","public_key_b64url","purpose",
        "plaintext_allowed","raw_source_allowed"
    }
    if set(value) != required or value.get("schema_version") != PUBLIC_KEY_SCHEMA:
        raise HandoffError("Governance transport public key schema mismatch")
    if value.get("algorithm") != "X25519-HKDF-SHA256-CHACHA20POLY1305":
        raise HandoffError("unexpected transport algorithm")
    public = _unb64(value.get("public_key_b64url"), "public key", 32)
    expected_id = hashlib.sha256(public).hexdigest()[:24]
    if value.get("key_id") != expected_id:
        raise HandoffError("public key_id does not match key bytes")
    if value.get("plaintext_allowed") is not False or value.get("raw_source_allowed") is not False:
        raise HandoffError("unsafe Governance transport key policy")
    return dict(value)


def _validate_export(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping) or value.get("schema_version") != "governance-prc-justice-derived-export-v1":
        raise HandoffError("unsupported derived export schema")
    if value.get("producer_repository") != EXPECTED_PRODUCER:
        raise HandoffError("unexpected derived export producer")
    records = value.get("records")
    if not isinstance(records, list) or not 1 <= len(records) <= MAX_RECORDS:
        raise HandoffError("derived export must contain 1..2000 records")
    if int(value.get("record_count") or 0) != len(records):
        raise HandoffError("derived export record_count mismatch")
    for flag in (
        "raw_source_text_included","raw_source_url_included","raw_model_response_included",
        "personal_data_included","secret_operational_details_included","evasion_or_anti_forensics_included",
        "direct_huggingface_write",
    ):
        if value.get(flag) is not False:
            raise HandoffError(f"unsafe derived export flag: {flag}")
    if value.get("storage_gateway_owner") != "a15280020511/decision-system-governance":
        raise HandoffError("derived export storage owner mismatch")
    if not re.fullmatch(r"[0-9a-f]{40}", str(value.get("producer_commit") or "")):
        raise HandoffError("producer_commit must be a 40-character SHA")
    if not str(value.get("source_run_id") or "").isdigit():
        raise HandoffError("source_run_id must be numeric")
    return dict(value)


def _chunk_export(export: Mapping[str, Any]) -> list[dict[str, Any]]:
    base = {key: value for key, value in export.items() if key not in {"records","record_count"}}
    chunks: list[dict[str, Any]] = []
    current: list[Any] = []
    for record in export["records"]:
        candidate = {**base, "record_count": len(current) + 1, "records": [*current, record]}
        if len(_canonical(candidate)) <= MAX_PLAINTEXT_BYTES:
            current.append(record)
            continue
        if not current:
            raise HandoffError("one derived record is too large for encrypted Issue transport")
        chunks.append({**base, "record_count": len(current), "records": current})
        current = [record]
        single = {**base, "record_count": 1, "records": current}
        if len(_canonical(single)) > MAX_PLAINTEXT_BYTES:
            raise HandoffError("one derived record is too large for encrypted Issue transport")
    if current:
        chunks.append({**base, "record_count": len(current), "records": current})
    if not 1 <= len(chunks) <= 50:
        raise HandoffError("encrypted Issue chunk count outside allowed range")
    return chunks


def _encrypt_chunk(chunk: Mapping[str, Any], descriptor: Mapping[str, Any], index: int, total: int) -> dict[str, Any]:
    recipient_bytes = _unb64(descriptor["public_key_b64url"], "public key", 32)
    recipient = x25519.X25519PublicKey.from_public_bytes(recipient_bytes)
    ephemeral_private = x25519.X25519PrivateKey.generate()
    ephemeral_public = ephemeral_private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    shared = ephemeral_private.exchange(recipient)
    salt = hashlib.sha256(ephemeral_public + recipient_bytes).digest()
    key = HKDF(algorithm=hashes.SHA256(), length=32, salt=salt, info=KDF_CONTEXT).derive(shared)
    plaintext = _canonical(chunk)
    export_sha = hashlib.sha256(plaintext).hexdigest()
    aad = {
        "source_repository": EXPECTED_PRODUCER,
        "source_run_id": int(str(chunk["source_run_id"])),
        "source_commit": str(chunk["producer_commit"]),
        "chunk_index": index,
        "chunk_count": total,
        "record_count": int(chunk["record_count"]),
        "export_sha256": export_sha,
        "raw_source_text_included": False,
        "raw_source_url_included": False,
        "raw_model_response_included": False,
    }
    nonce = os.urandom(12)
    ciphertext = ChaCha20Poly1305(key).encrypt(nonce, plaintext, _canonical(aad))
    envelope = {
        "schema_version": ENVELOPE_SCHEMA,
        "key_id": descriptor["key_id"],
        "ephemeral_public_key_b64url": _b64(ephemeral_public),
        "nonce_b64url": _b64(nonce),
        "ciphertext_b64url": _b64(ciphertext),
        "aad": aad,
        "plaintext_sha256": export_sha,
        "plaintext_bytes": len(plaintext),
    }
    if len(_canonical(envelope)) > MAX_ISSUE_BODY_BYTES:
        raise HandoffError("encrypted handoff envelope exceeds GitHub Issue body budget")
    return envelope


def build(export_path: Path, public_key_path: Path, output_dir: Path) -> dict[str, Any]:
    export = _validate_export(_load(export_path))
    descriptor = validate_public_key(_load(public_key_path))
    chunks = _chunk_export(export)
    output_dir.mkdir(parents=True, exist_ok=True)
    envelopes = [_encrypt_chunk(chunk, descriptor, index + 1, len(chunks)) for index, chunk in enumerate(chunks)]
    for index, envelope in enumerate(envelopes, 1):
        (output_dir / f"handoff-{index:03d}.json").write_bytes(_canonical(envelope))
    manifest = {
        "schema_version":"prc-justice-encrypted-handoff-manifest-v1",
        "key_id":descriptor["key_id"],
        "source_run_id":int(str(export["source_run_id"])),
        "source_commit":export["producer_commit"],
        "record_count":export["record_count"],
        "chunk_count":len(envelopes),
        "plaintext_issue_transport":False,
        "raw_source_text_in_transport":False,
        "raw_source_url_in_transport":False,
        "raw_model_response_in_transport":False,
        "github_cross_repo_actions_permission_required":False,
        "github_cross_repo_contents_permission_required":False,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def validate() -> dict[str, Any]:
    return {
        "status":"PRC_JUSTICE_ENCRYPTED_HANDOFF_BUILDER_VALIDATED",
        "algorithm":"X25519-HKDF-SHA256-CHACHA20POLY1305",
        "max_plaintext_bytes_per_issue":MAX_PLAINTEXT_BYTES,
        "plaintext_issue_transport":False,
        "raw_source_text_in_transport":False,
        "raw_source_url_in_transport":False,
        "raw_model_response_in_transport":False,
        "github_cross_repo_actions_permission_required":False,
        "github_cross_repo_contents_permission_required":False,
        "hf_token_required_in_evidence_center":False,
        "network_used":False,
        "model_calls":0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["validate","build"])
    parser.add_argument("--export")
    parser.add_argument("--public-key")
    parser.add_argument("--output-dir", default="prc-justice-encrypted-handoffs")
    args = parser.parse_args()
    try:
        if args.command == "validate":
            result = validate()
        else:
            if not args.export or not args.public_key:
                raise HandoffError("--export and --public-key are required for build")
            result = build(Path(args.export), Path(args.public_key), Path(args.output_dir))
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}"[:1000], file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
