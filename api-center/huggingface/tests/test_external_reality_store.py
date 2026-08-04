from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

MODULE_PATH = Path(__file__).resolve().parents[1] / "external_reality_store.py"
SPEC = importlib.util.spec_from_file_location("external_reality_store", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class FakeApi:
    def __init__(self, *, private: bool = True) -> None:
        self.private = private
        self.remote_files: set[str] = set()
        self.created: list[dict] = []
        self.uploaded: list[dict] = []

    def whoami(self, *, token: str):
        assert token == "secret-token"
        return {"name": "James147258"}

    def create_repo(self, **kwargs):
        self.created.append(kwargs)
        return SimpleNamespace()

    def dataset_info(self, repo_id: str, *, token: str, timeout: int):
        assert repo_id == "James147258/cloudflare-intelligence-archive"
        assert token == "secret-token"
        assert timeout == 30
        return SimpleNamespace(private=self.private)

    def upload_folder(self, **kwargs):
        folder = Path(kwargs["folder_path"])
        root = kwargs["path_in_repo"]
        for path in folder.rglob("*"):
            if path.is_file():
                self.remote_files.add(f"{root}/{path.relative_to(folder).as_posix()}")
        self.uploaded.append(kwargs)
        return SimpleNamespace(oid="external-reality-commit-001")

    def list_repo_files(self, **kwargs):
        return sorted(self.remote_files)


class ExternalRealityStoreTests(unittest.TestCase):
    def test_registry_is_complete(self) -> None:
        registry = MODULE.load_json(MODULE.REGISTRY_PATH)
        result = MODULE.validate_registry(registry)
        self.assertEqual({row["id"] for row in result["domains"]}, MODULE.EXPECTED_DOMAINS)
        self.assertEqual(
            {row["id"] for row in result["collection_layers"]},
            MODULE.EXPECTED_COLLECTION_LAYERS,
        )
        self.assertEqual(len(result["registry_sha256"]), 64)

    def test_bundle_is_deterministic_and_complete(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            one = MODULE.build_bundle(Path(first))
            two = MODULE.build_bundle(Path(second))
            self.assertEqual(one["bundle_sha256"], two["bundle_sha256"])
            self.assertEqual(one["file_count"], 256)
            self.assertEqual(one["domain_count"], 18)
            self.assertEqual(one["collection_layer_count"], 13)
            self.assertEqual(one["directories_per_domain"], 13)
            paths = {row["path"] for row in one["files"]}
            self.assertIn("registry.json", paths)
            self.assertIn("record.schema.json", paths)
            self.assertIn("collection-template.json", paths)
            self.assertIn("external-reality-index.json", paths)
            for domain in MODULE.EXPECTED_DOMAINS:
                self.assertIn(f"domains/{domain}/requirements.json", paths)
                for layer in MODULE.EXPECTED_COLLECTION_LAYERS:
                    self.assertIn(f"domains/{domain}/{layer}/README.json", paths)

    def test_sync_uses_existing_private_dataset(self) -> None:
        fake = FakeApi()
        with tempfile.TemporaryDirectory() as output:
            receipt = MODULE.sync_library(
                token="secret-token",
                repo_override="James147258/cloudflare-intelligence-archive",
                benchmark_repo=None,
                fallback_repo=None,
                output_dir=Path(output),
                api=fake,
            )
            self.assertEqual(receipt["status"], "HF_EXTERNAL_REALITY_LIBRARY_CONNECTED")
            self.assertEqual(receipt["repo_id"], "James147258/cloudflare-intelligence-archive")
            self.assertTrue(receipt["private"])
            self.assertEqual(receipt["file_count"], 257)
            self.assertEqual(receipt["domain_count"], 18)
            self.assertEqual(receipt["collection_layer_count"], 13)
            self.assertFalse(receipt["compute_runtime_network_used"])
            self.assertFalse(receipt["direct_center_connection"])
            self.assertFalse(receipt["secret_values_exposed"])
            self.assertEqual(receipt["model_calls"], 0)
            self.assertEqual(receipt["commit_oid"], "external-reality-commit-001")
            self.assertEqual(len(fake.uploaded), 1)
            saved = json.loads(
                (Path(output) / "hf-external-reality-library-receipt.json").read_text(encoding="utf-8")
            )
            self.assertEqual(saved["bundle_sha256"], receipt["bundle_sha256"])

    def test_public_dataset_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as output:
            with self.assertRaisesRegex(MODULE.ExternalRealityStoreError, "must be private"):
                MODULE.sync_library(
                    token="secret-token",
                    repo_override="James147258/cloudflare-intelligence-archive",
                    benchmark_repo=None,
                    fallback_repo=None,
                    output_dir=Path(output),
                    api=FakeApi(private=False),
                )

    def test_missing_token_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as output:
            with self.assertRaisesRegex(MODULE.ExternalRealityStoreError, "HF_TOKEN"):
                MODULE.sync_library(
                    token="",
                    repo_override=None,
                    benchmark_repo=None,
                    fallback_repo=None,
                    output_dir=Path(output),
                    api=FakeApi(),
                )

    def test_repo_fallback_order_and_safety(self) -> None:
        repo_id, account = MODULE.resolve_repo_id(
            FakeApi(),
            "secret-token",
            None,
            "James147258/cloudflare-intelligence-archive",
            "James147258/fallback",
        )
        self.assertEqual(account, "James147258")
        self.assertEqual(repo_id, "James147258/cloudflare-intelligence-archive")
        with self.assertRaisesRegex(MODULE.ExternalRealityStoreError, "unsafe"):
            MODULE.resolve_repo_id(FakeApi(), "secret-token", "James147258/bad repo", None, None)


if __name__ == "__main__":
    unittest.main()
