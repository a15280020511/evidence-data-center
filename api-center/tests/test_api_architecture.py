from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
API = REPO / "api-center"


class ApiArchitectureTests(unittest.TestCase):
    def test_formal_api_entry_and_contracts_exist(self) -> None:
        required = [
            API / "api-ticket.schema.json",
            API / "api_ticket.py",
            API / "api_task.py",
            API / "api-catalog.json",
            API / "api-catalog.md",
            API / "catalog-metadata.json",
            API / "build_catalog.py",
            REPO / ".github/workflows/api-ticket.yml",
            REPO / ".github/workflows/api-catalog-validate.yml",
            REPO / "README.md",
            REPO / "OPERATIONS_RUNBOOK.md",
            REPO / "SECURITY.md",
            REPO / "governance-compatibility.json",
            REPO / "OBSERVABILITY.md",
        ]
        self.assertEqual([str(path) for path in required if not path.is_file()], [])

    def test_workflow_injects_each_api_secret_independently(self) -> None:
        workflow = (REPO / ".github/workflows/api-ticket.yml").read_text(encoding="utf-8")
        manifest = json.loads((API / "connector-manifest.json").read_text(encoding="utf-8"))
        self.assertIn("API_GATEWAY_AUTH_TOKEN", workflow)
        for secret_name in manifest["required_secret_environment_variables"]:
            self.assertIn(f"{secret_name}: ${{{{ secrets.{secret_name} }}}}", workflow)
        self.assertNotIn("API_CENTER" + "_SECRETS_JSON", workflow)
        self.assertNotIn("curl --get 'https://", workflow)

    def test_aggregated_or_alias_secret_names_are_forbidden(self) -> None:
        forbidden = (
            "API_CENTER" + "_SECRETS_JSON",
            "YD" + "_API_KEY",
            "GOOGLE_CLOUD" + "_SERVICE_ACCOUNT_JSON",
        )
        roots = [API, REPO / ".github/workflows"]
        matches = []
        for root in roots:
            for path in root.rglob("*"):
                if not path.is_file() or path.suffix in {".pyc", ".zip", ".gz"}:
                    continue
                try:
                    content = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                for name in forbidden:
                    if name in content:
                        matches.append(f"{path.relative_to(REPO)}:{name}")
        self.assertEqual(matches, [])

    def test_all_enabled_get_connectors_have_response_contract(self) -> None:
        manifest = json.loads((API / "connector-manifest.json").read_text(encoding="utf-8"))
        for row in manifest["connectors"]:
            if not row["enabled"] or row["method"] != "GET":
                continue
            connector = json.loads((API / row["file"]).read_text(encoding="utf-8"))
            contract = connector.get("response_contract")
            self.assertIsInstance(contract, dict, row["id"])
            status_contract = bool(
                contract.get("status_path") and contract.get("success_values")
            )
            data_contract = bool(
                contract.get("success_when_data_present") is True
                and contract.get("any_data_paths")
            )
            self.assertTrue(status_contract or data_contract, row["id"])

    def test_api_ticket_rejects_personal_data_by_schema(self) -> None:
        schema = json.loads((API / "api-ticket.schema.json").read_text(encoding="utf-8"))
        policy = schema["properties"]["data_policy"]["properties"]
        self.assertEqual(policy["classification"]["const"], "public")
        self.assertIs(policy["contains_personal_data"]["const"], False)

    def test_catalog_and_orchestration_lock_roles(self) -> None:
        catalog = json.loads((API / "api-catalog.json").read_text(encoding="utf-8"))
        orchestration = json.loads(
            (REPO / "governance-compatibility.json").read_text(encoding="utf-8")
        )
        self.assertEqual(catalog["selection_owner"], "gpts-usage-center")
        self.assertEqual(catalog["maintenance_owner"], "web-gpt-github-plugin")
        self.assertFalse(catalog["direct_center_to_center_calls_allowed"])
        self.assertEqual(orchestration["sole_cross_center_relay"], "custom-gpts")
        self.assertFalse(orchestration["direct_center_to_center_calls_allowed"])


if __name__ == "__main__":
    unittest.main()
