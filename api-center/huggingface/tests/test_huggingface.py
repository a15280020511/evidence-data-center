from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("huggingface_task", ROOT / "huggingface_task.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class FakeApi:
    def __init__(self) -> None:
        self.calls = []

    def list_models(self, **kwargs):
        self.calls.append(("list_models", kwargs))
        return iter([{"id": "open/model-a", "private": False}, {"id": "open/model-b", "private": False}])

    def model_info(self, repo_id, **kwargs):
        self.calls.append(("model_info", {"repo_id": repo_id, **kwargs}))
        return {"id": repo_id, "private": False}

    def list_datasets(self, **kwargs):
        self.calls.append(("list_datasets", kwargs))
        return iter([{"id": "open/data", "private": False}])

    def dataset_info(self, repo_id, **kwargs):
        self.calls.append(("dataset_info", {"repo_id": repo_id, **kwargs}))
        return {"id": repo_id, "private": False}

    def list_spaces(self, **kwargs):
        self.calls.append(("list_spaces", kwargs))
        return iter([{"id": "open/space", "private": False}])

    def space_info(self, repo_id, **kwargs):
        self.calls.append(("space_info", {"repo_id": repo_id, **kwargs}))
        return {"id": repo_id, "private": False}

    def list_repo_tree(self, repo_id, **kwargs):
        self.calls.append(("list_repo_tree", {"repo_id": repo_id, **kwargs}))
        return iter([{"path": "README.md", "size": 100}])

    def list_repo_refs(self, repo_id, **kwargs):
        self.calls.append(("list_repo_refs", {"repo_id": repo_id, **kwargs}))
        return {"branches": [{"name": "main"}], "tags": []}

    def get_paths_info(self, repo_id, paths, **kwargs):
        self.calls.append(("get_paths_info", {"repo_id": repo_id, "paths": paths, **kwargs}))
        return [{"path": path, "size": 100} for path in paths]


class HuggingFaceProviderTests(unittest.TestCase):
    def test_catalog_and_schema_alignment(self) -> None:
        catalog = json.loads((ROOT / "provider-catalog.json").read_text(encoding="utf-8"))
        schema = json.loads((ROOT / "ticket.schema.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        operations = {row["operation_id"] for row in provider["operations"]}
        self.assertEqual(provider["provider_id"], "huggingface-hub")
        self.assertEqual(provider["ticket_prefix"], "[intel-huggingface]")
        self.assertEqual(provider["required_secret_environment_variable"], "")
        self.assertEqual(len(operations), 11)
        self.assertEqual(operations, set(schema["properties"]["operation"]["enum"]))
        self.assertTrue(provider["limits"]["public_repositories_only"])
        self.assertFalse(provider["limits"]["authentication_used"])
        self.assertFalse(provider["limits"]["inference_allowed"])
        self.assertFalse(provider["limits"]["training_or_jobs_allowed"])
        self.assertFalse(provider["limits"]["space_invocation_allowed"])
        self.assertFalse(provider["limits"]["file_download_allowed"])
        self.assertFalse(provider["limits"]["write_operations_allowed"])

    def test_model_search_is_bounded_and_anonymous(self) -> None:
        api = FakeApi()
        result, method = module.execute_operation(api, "models-search", {"query": "bert", "limit": 2}, 5)
        self.assertEqual(method, "list_models")
        self.assertEqual(len(result), 2)
        _, kwargs = api.calls[-1]
        self.assertIs(kwargs["token"], False)
        self.assertEqual(kwargs["limit"], 2)

    def test_security_operation_is_anonymous(self) -> None:
        api = FakeApi()
        _, method = module.execute_operation(api, "model-security", {"repo_id": "open/model"}, 5)
        self.assertEqual(method, "model_info_securityStatus")
        _, kwargs = api.calls[-1]
        self.assertTrue(kwargs["securityStatus"])
        self.assertIs(kwargs["token"], False)

    def test_non_public_repository_is_rejected(self) -> None:
        with self.assertRaises(RuntimeError):
            module.ensure_public({"id": "restricted/model", "private": True})

    def test_repo_tree_is_non_recursive(self) -> None:
        api = FakeApi()
        result, method = module.execute_operation(
            api,
            "repo-tree",
            {"repo_id": "open/data", "repo_type": "dataset", "path": "data", "limit": 10},
            5,
        )
        self.assertEqual(method, "list_repo_tree")
        self.assertEqual(len(result), 1)
        _, kwargs = api.calls[-1]
        self.assertFalse(kwargs["recursive"])
        self.assertFalse(kwargs["expand"])
        self.assertIs(kwargs["token"], False)

    def test_unsafe_paths_are_rejected(self) -> None:
        for value in ("../x", "a/../b", "/root", "a//b"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    module.safe_path(value, required=True)

    def test_repo_paths_are_unique(self) -> None:
        api = FakeApi()
        result, method = module.execute_operation(
            api,
            "repo-paths-info",
            {"repo_id": "open/model", "repo_type": "model", "paths": ["README.md", "config.json"]},
            5,
        )
        self.assertEqual(method, "get_paths_info")
        self.assertEqual(len(result), 2)
        with self.assertRaises(ValueError):
            module.execute_operation(
                api,
                "repo-paths-info",
                {"repo_id": "open/model", "repo_type": "model", "paths": ["README.md", "README.md"]},
                5,
            )

    def test_catalog_operation_is_local(self) -> None:
        api = FakeApi()
        result, method = module.execute_operation(api, "catalog-capabilities", {}, 5)
        self.assertEqual(method, "local-catalog")
        self.assertIn("provider", result)
        self.assertEqual(api.calls, [])


if __name__ == "__main__":
    unittest.main()
