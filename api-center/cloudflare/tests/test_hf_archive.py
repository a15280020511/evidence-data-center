from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("cloudflare_hf_archive", ROOT / "hf_archive.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_result(root: Path, *, private_policy: bool = True) -> None:
    ticket = {
        "task_id": "archive-test-20260803",
        "provider": "cloudflare",
        "operation": "radar-global-search",
        "parameters": {"query": "energy", "limit": 5},
        "data_policy": {
            "classification": "public" if private_policy else "restricted",
            "contains_personal_data": False,
        },
        "acceptance": {"timeout_seconds": 30, "max_response_bytes": 1000000},
    }
    ticket_status = {
        "accepted": True,
        "task_id": ticket["task_id"],
        "provider": "cloudflare",
        "operation": ticket["operation"],
        "secret_values_exposed": False,
    }
    snapshot = {"provider": "cloudflare", "operation": ticket["operation"], "data": {"result": [1, 2, 3]}}
    diagnostics = {
        "status": "INTEL_CLOUDFLARE_COMPLETED",
        "task_id": ticket["task_id"],
        "operation": ticket["operation"],
        "completed_at": "2026-08-03T01:02:03+00:00",
        "metadata": {"response_sha256": "a" * 64},
        "secret_values_exposed": False,
    }
    for name, value in {
        "ticket.json": ticket,
        "ticket-status.json": ticket_status,
        "snapshot.json": snapshot,
        "diagnostics.json": diagnostics,
    }.items():
        write_json(root / name, value)
    files = []
    for name in sorted(["ticket.json", "ticket-status.json", "snapshot.json", "diagnostics.json"]):
        raw = (root / name).read_bytes()
        files.append({"name": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    write_json(
        root / "manifest.json",
        {
            "status": "INTEL_CLOUDFLARE_COMPLETED",
            "task_id": ticket["task_id"],
            "provider": "cloudflare",
            "operation": ticket["operation"],
            "files": files,
            "secret_values_exposed": False,
        },
    )


class FakeApi:
    def __init__(self, *, private: bool = True) -> None:
        self.private = private
        self.calls: list[tuple[str, dict[str, object]]] = []
        self.uploaded_names: list[str] = []
        self.uploaded_record: dict[str, object] | None = None

    def whoami(self, **kwargs):
        self.calls.append(("whoami", kwargs))
        return {"name": "James147258", "type": "user"}

    def create_repo(self, **kwargs):
        self.calls.append(("create_repo", kwargs))
        return SimpleNamespace(repo_id=kwargs["repo_id"])

    def dataset_info(self, repo_id, **kwargs):
        self.calls.append(("dataset_info", {"repo_id": repo_id, **kwargs}))
        return SimpleNamespace(id=repo_id, private=self.private)

    def upload_folder(self, **kwargs):
        self.calls.append(("upload_folder", kwargs))
        folder = Path(str(kwargs["folder_path"]))
        self.uploaded_names = sorted(path.name for path in folder.iterdir() if path.is_file())
        self.uploaded_record = json.loads((folder / "archive-record.json").read_text(encoding="utf-8"))
        return SimpleNamespace(oid="commit-oid-test")


class HuggingFaceArchiveTests(unittest.TestCase):
    def test_installed_sdk_has_required_upload_folder_signature(self) -> None:
        parameters = inspect.signature(HfApi.upload_folder).parameters
        for name in ("repo_id", "folder_path", "path_in_repo", "repo_type", "token", "commit_message"):
            self.assertIn(name, parameters)

    def test_completed_public_result_is_archived_to_private_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_result(root)
            api = FakeApi()
            receipt = module.archive_result(
                root,
                token="hf_test_secret",
                repo_override=None,
                github_repository="a15280020511/evidence-data-center",
                issue_number="999",
                run_id="12345",
                run_attempt="1",
                source_sha="abc123",
                api=api,
            )
            self.assertEqual(receipt["status"], "HF_CLOUDFLARE_ARCHIVE_COMPLETED")
            self.assertEqual(receipt["repo_id"], "James147258/cloudflare-intelligence-archive")
            self.assertTrue(receipt["private"])
            self.assertIn("year=2026/month=08/day=03", receipt["path"])
            self.assertIn("archive-record.json", api.uploaded_names)
            self.assertIn("manifest.json", api.uploaded_names)
            self.assertEqual(api.uploaded_record["source"]["run_id"], "12345")
            self.assertFalse(api.uploaded_record["secret_values_exposed"])
            create_call = next(kwargs for name, kwargs in api.calls if name == "create_repo")
            self.assertTrue(create_call["private"])
            self.assertEqual(create_call["repo_type"], "dataset")
            self.assertEqual(create_call["token"], "hf_test_secret")
            upload_call = next(kwargs for name, kwargs in api.calls if name == "upload_folder")
            self.assertEqual(upload_call["token"], "hf_test_secret")

    def test_custom_repo_override_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_result(root)
            receipt = module.archive_result(
                root,
                token="hf_test_secret",
                repo_override="James147258/custom-cloudflare-archive",
                github_repository="repo/name",
                issue_number="1",
                run_id="2",
                run_attempt="1",
                source_sha="sha",
                api=FakeApi(),
            )
            self.assertEqual(receipt["repo_id"], "James147258/custom-cloudflare-archive")

    def test_public_repository_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_result(root)
            with self.assertRaises(module.ArchiveError):
                module.archive_result(
                    root,
                    token="hf_test_secret",
                    repo_override=None,
                    github_repository="repo/name",
                    issue_number="1",
                    run_id="2",
                    run_attempt="1",
                    source_sha="sha",
                    api=FakeApi(private=False),
                )

    def test_restricted_or_personal_results_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_result(root, private_policy=False)
            with self.assertRaises(module.ArchiveError):
                module.validate_local_result(root)

    def test_tampered_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_result(root)
            (root / "snapshot.json").write_text("tampered", encoding="utf-8")
            with self.assertRaises(module.ArchiveError):
                module.validate_local_result(root)

    def test_failed_collection_is_not_archived(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_result(root)
            diagnostics = json.loads((root / "diagnostics.json").read_text(encoding="utf-8"))
            diagnostics["status"] = "INTEL_CLOUDFLARE_FAILED"
            write_json(root / "diagnostics.json", diagnostics)
            with self.assertRaises(module.ArchiveError):
                module.validate_local_result(root)

    def test_token_is_redacted_from_failure_text(self) -> None:
        rendered = module.redact("upstream rejected hf_secret_value", "hf_secret_value")
        self.assertNotIn("hf_secret_value", rendered)
        self.assertIn("[REDACTED]", rendered)


if __name__ == "__main__":
    unittest.main()
