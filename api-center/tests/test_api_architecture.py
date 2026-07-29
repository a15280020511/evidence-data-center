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
            REPO / "THREE_CENTERS.md",
            REPO / "GPTS_USAGE_ORCHESTRATION.md",
            REPO / "gpts-orchestration-policy.json",
            REPO / "OBSERVABILITY.md",
        ]
        self.assertEqual([str(path) for path in required if not path.is_file()], [])

    def test_workflow_is_generic_and_has_no_connector_specific_secret(self) -> None:
        workflow = (REPO / ".github/workflows/api-ticket.yml").read_text(encoding="utf-8")
        self.assertIn("API_CENTER_SECRETS_JSON", workflow)
        self.assertIn("API_GATEWAY_AUTH_TOKEN", workflow)
        self.assertNotIn("AMAP_API_KEY", workflow)
        self.assertNotIn("curl --get 'https://", workflow)

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
            (REPO / "gpts-orchestration-policy.json").read_text(encoding="utf-8")
        )
        self.assertEqual(catalog["selection_owner"], "gpts-usage-center")
        self.assertEqual(catalog["maintenance_owner"], "web-gpt-github-plugin")
        self.assertFalse(catalog["direct_center_to_center_calls_allowed"])
        self.assertEqual(orchestration["sole_cross_center_relay"], "custom-gpts")
        self.assertFalse(orchestration["direct_center_to_center_calls_allowed"])


if __name__ == "__main__":
    unittest.main()
