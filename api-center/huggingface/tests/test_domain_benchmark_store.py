from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

MODULE_PATH = Path(__file__).resolve().parents[1] / "domain_benchmark_store.py"
SPEC = importlib.util.spec_from_file_location("domain_benchmark_store", MODULE_PATH)
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
        return SimpleNamespace(oid="commit-oid-123")

    def list_repo_files(self, **kwargs):
        return sorted(self.remote_files)


class DomainBenchmarkStoreTests(unittest.TestCase):
    def test_requirements_are_complete(self) -> None:
        document = MODULE.load_json(MODULE.REQUIREMENTS_PATH)
        result = MODULE.validate_requirements(document)
        self.assertEqual(set(result["domains"]), MODULE.EXPECTED_DOMAINS)
        self.assertEqual(set(result["asset_libraries"]), MODULE.EXPECTED_ASSET_LIBRARIES)
        self.assertEqual(len(result["requirements_sha256"]), 64)

    def test_bundle_is_deterministic_and_complete(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            one = MODULE.build_bundle(Path(first))
            two = MODULE.build_bundle(Path(second))
            self.assertEqual(one["bundle_sha256"], two["bundle_sha256"])
            self.assertEqual(one["file_count"], 19)
            first_paths = {row["path"] for row in one["files"]}
            self.assertIn("requirements.json", first_paths)
            self.assertIn("manifest.schema.json", first_paths)
            self.assertIn("library-index.json", first_paths)
            for domain in MODULE.EXPECTED_DOMAINS:
                self.assertIn(f"domains/{domain}/requirements.json", first_paths)
            for library in MODULE.EXPECTED_ASSET_LIBRARIES:
                self.assertIn(f"asset-libraries/{library}/README.json", first_paths)

    def test_sync_uses_existing_private_dataset(self) -> None:
        fake = FakeApi()
        with tempfile.TemporaryDirectory() as output:
            receipt = MODULE.sync_library(
                token="secret-token",
                repo_override="James147258/cloudflare-intelligence-archive",
                fallback_repo=None,
                output_dir=Path(output),
                api=fake,
            )
            self.assertEqual(receipt["status"], "HF_DOMAIN_BENCHMARK_LIBRARY_CONNECTED")
            self.assertEqual(receipt["repo_id"], "James147258/cloudflare-intelligence-archive")
            self.assertTrue(receipt["private"])
            self.assertFalse(receipt["compute_runtime_network_used"])
            self.assertFalse(receipt["direct_center_connection"])
            self.assertFalse(receipt["secret_values_exposed"])
            self.assertEqual(receipt["model_calls"], 0)
            self.assertEqual(receipt["commit_oid"], "commit-oid-123")
            self.assertEqual(len(fake.uploaded), 1)
            saved = json.loads(
                (Path(output) / "hf-domain-benchmark-library-receipt.json").read_text(encoding="utf-8")
            )
            self.assertEqual(saved["bundle_sha256"], receipt["bundle_sha256"])

    def test_public_dataset_is_rejected(self) -> None:
        fake = FakeApi(private=False)
        with tempfile.TemporaryDirectory() as output:
            with self.assertRaisesRegex(MODULE.DomainBenchmarkStoreError, "must be private"):
                MODULE.sync_library(
                    token="secret-token",
                    repo_override="James147258/cloudflare-intelligence-archive",
                    fallback_repo=None,
                    output_dir=Path(output),
                    api=fake,
                )

    def test_missing_token_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as output:
            with self.assertRaisesRegex(MODULE.DomainBenchmarkStoreError, "HF_TOKEN"):
                MODULE.sync_library(
                    token="",
                    repo_override=None,
                    fallback_repo=None,
                    output_dir=Path(output),
                    api=FakeApi(),
                )

    def test_default_repo_uses_authenticated_account(self) -> None:
        repo_id, account = MODULE.resolve_repo_id(FakeApi(), "secret-token", None, None)
        self.assertEqual(account, "James147258")
        self.assertEqual(repo_id, "James147258/cloudflare-intelligence-archive")

    def test_unsafe_repo_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(MODULE.DomainBenchmarkStoreError, "unsafe"):
            MODULE.resolve_repo_id(FakeApi(), "secret-token", "James147258/bad repo", None)


if __name__ == "__main__":
    unittest.main()
