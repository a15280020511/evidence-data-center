from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("justice_handoff_builder", HERE / "encrypt_prc_justice_hf_handoff.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * ((4 - len(value) % 4) % 4))


def public_descriptor(private_key: x25519.X25519PrivateKey) -> dict:
    public = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return {
        "schema_version": MODULE.PUBLIC_KEY_SCHEMA,
        "algorithm": "X25519-HKDF-SHA256-CHACHA20POLY1305",
        "key_id": hashlib.sha256(public).hexdigest()[:24],
        "public_key_b64url": b64(public),
        "purpose": "test recipient",
        "plaintext_allowed": False,
        "raw_source_allowed": False,
    }


def synthetic_export() -> dict:
    return {
        "schema_version": "governance-prc-justice-derived-export-v1",
        "producer_repository": MODULE.EXPECTED_PRODUCER,
        "producer_commit": "a" * 40,
        "source_run_id": "31191782538",
        "as_of_date": "2026-08-07",
        "record_count": 2,
        "records": [
            {"record_id": "jintel:" + "1" * 40, "summary": "第一条模型归一化司法情报"},
            {"record_id": "jintel:" + "2" * 40, "summary": "第二条模型归一化司法情报"},
        ],
        "raw_source_text_included": False,
        "raw_source_url_included": False,
        "raw_model_response_included": False,
        "personal_data_included": False,
        "secret_operational_details_included": False,
        "evasion_or_anti_forensics_included": False,
        "evidence_reference_resolution_owner": MODULE.EXPECTED_PRODUCER,
        "storage_gateway_owner": "a15280020511/decision-system-governance",
        "direct_huggingface_write": False,
    }


class EncryptedHandoffBuilderTests(unittest.TestCase):
    def test_public_key_validation_rejects_tampered_key_id(self) -> None:
        private = x25519.X25519PrivateKey.generate()
        descriptor = public_descriptor(private)
        descriptor["key_id"] = "0" * 24
        with self.assertRaises(MODULE.HandoffError):
            MODULE.validate_public_key(descriptor)

    def test_unsafe_export_is_rejected(self) -> None:
        value = synthetic_export()
        value["raw_source_url_included"] = True
        with self.assertRaises(MODULE.HandoffError):
            MODULE._validate_export(value)

    def test_encrypted_build_round_trip_contains_no_plaintext(self) -> None:
        private = x25519.X25519PrivateKey.generate()
        descriptor = public_descriptor(private)
        export = synthetic_export()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            export_path = root / "export.json"
            key_path = root / "key.json"
            output = root / "out"
            export_path.write_text(json.dumps(export, ensure_ascii=False), encoding="utf-8")
            key_path.write_text(json.dumps(descriptor), encoding="utf-8")
            manifest = MODULE.build(export_path, key_path, output)
            self.assertEqual(manifest["record_count"], 2)
            self.assertFalse(manifest["plaintext_issue_transport"])
            envelopes = sorted(output.glob("handoff-*.json"))
            self.assertEqual(len(envelopes), manifest["chunk_count"])
            envelope_text = envelopes[0].read_text(encoding="utf-8")
            self.assertNotIn("第一条模型归一化司法情报", envelope_text)
            envelope = json.loads(envelope_text)

            ephemeral_public = unb64(envelope["ephemeral_public_key_b64url"])
            recipient_public = private.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
            shared = private.exchange(x25519.X25519PublicKey.from_public_bytes(ephemeral_public))
            salt = hashlib.sha256(ephemeral_public + recipient_public).digest()
            key = HKDF(algorithm=hashes.SHA256(), length=32, salt=salt, info=MODULE.KDF_CONTEXT).derive(shared)
            plaintext = ChaCha20Poly1305(key).decrypt(
                unb64(envelope["nonce_b64url"]),
                unb64(envelope["ciphertext_b64url"]),
                MODULE._canonical(envelope["aad"]),
            )
            restored = json.loads(plaintext)
            self.assertEqual(restored["record_count"], 2)
            self.assertEqual(restored["records"][0]["summary"], "第一条模型归一化司法情报")
            self.assertEqual(hashlib.sha256(plaintext).hexdigest(), envelope["plaintext_sha256"])

    def test_builder_validate_reports_no_privilege_expansion(self) -> None:
        result = MODULE.validate()
        self.assertFalse(result["github_cross_repo_actions_permission_required"])
        self.assertFalse(result["github_cross_repo_contents_permission_required"])
        self.assertFalse(result["hf_token_required_in_evidence_center"])
        self.assertFalse(result["plaintext_issue_transport"])
        self.assertEqual(result["model_calls"], 0)
        self.assertFalse(result["network_used"])


if __name__ == "__main__":
    unittest.main()
