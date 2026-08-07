from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


api_ticket = load_module("api_ticket_prc_bridge", ROOT / "api_ticket.py")
api_task = load_module("api_task_prc_bridge", ROOT / "api_task.py")


class PRCOpenGenericBridgeTests(unittest.TestCase):
    def packet(self, connector_id: str = "prc-sinofacts-company-search") -> dict:
        return {
            "task_id": "api-prc-open-0001",
            "objective": "collect public non-personal company intelligence",
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "requests": [
                {
                    "request_id": "prc-1",
                    "connector_id": connector_id,
                    "parameters": (
                        {"query": "01.AI", "max_results": 3}
                        if connector_id == "prc-sinofacts-company-search"
                        else {"query": "示例公司", "language": "zh"}
                    ),
                }
            ],
            "acceptance": {"require_all": True, "minimum_successful_requests": 1},
        }

    def test_generic_ticket_plans_local_prc_connector(self) -> None:
        packet = self.packet()
        self.assertEqual(list(api_ticket.VALIDATOR.iter_errors(packet)), [])
        plan = api_ticket._validate_and_plan(packet, ROOT)
        row = plan["requests"][0]
        self.assertEqual(row["execution_mode"], "local-prc-open")
        self.assertEqual(row["method"], "LOCAL")
        self.assertEqual(plan["required_secret_environment_variables"], [])

    def test_generic_ticket_rejects_unknown_local_parameter(self) -> None:
        packet = self.packet("prc-china-check-company-search")
        packet["requests"][0]["parameters"]["cookie"] = "forbidden"
        with self.assertRaisesRegex(ValueError, "PRC local parameter contract"):
            api_ticket._validate_and_plan(packet, ROOT)

    def test_local_and_gateway_requests_cannot_mix(self) -> None:
        packet = self.packet()
        packet["requests"].append(
            {
                "request_id": "wb-1",
                "connector_id": "worldbank-indicator",
                "parameters": {"indicator_code": "NY.GDP.MKTP.CD", "format": "json"},
            }
        )
        packet["acceptance"] = {"require_all": True, "minimum_successful_requests": 2}
        with self.assertRaisesRegex(ValueError, "must be isolated"):
            api_ticket._validate_and_plan(packet, ROOT)

    def test_resolve_mode_selects_zero_secret_local_execution(self) -> None:
        plan = api_ticket._validate_and_plan(self.packet(), ROOT)
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(
            os.environ,
            {"API_GATEWAY_BASE_URL": "", "API_GATEWAY_AUTH_TOKEN": ""},
            clear=False,
        ):
            result = api_task.resolve_mode(plan, Path(tmp))
        self.assertEqual(result["mode"], "local-prc-open")
        self.assertEqual(result["required_secret_count"], 0)
        self.assertEqual(result["secret_source"], "none")

    def test_execute_local_mode_publishes_normal_api_completed_snapshot(self) -> None:
        plan = api_ticket._validate_and_plan(self.packet(), ROOT)
        fake_bridge = SimpleNamespace(
            execute_request=lambda *args, **kwargs: {
                "success": True,
                "state": "success",
                "message": "",
                "data_present": True,
                "response": {"matches": [{"name_zh": "示例"}]},
                "upstream_metadata": {"http_status": 200},
                "source_side_hard_stop": False,
                "error_type": None,
                "provider": "sinofacts",
                "operation": "company-search",
            }
        )
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            api_task, "_load_prc_local_bridge", return_value=fake_bridge
        ), mock.patch.dict(
            os.environ,
            {"API_GATEWAY_MODE": "local-prc-open", "API_GATEWAY_BASE_URL": ""},
            clear=False,
        ):
            root = Path(tmp)
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
            rc = api_task.execute(plan_path, root / "out")
            snapshot = json.loads(
                (root / "out/api-snapshot.json").read_text(encoding="utf-8")
            )
        self.assertEqual(rc, 0)
        self.assertEqual(snapshot["status"], "API_COMPLETED")
        self.assertEqual(snapshot["gateway_mode"], "local-prc-open")
        self.assertEqual(snapshot["successful_request_count"], 1)

    def test_source_denial_stays_failed_without_retry_or_fallback(self) -> None:
        plan = api_ticket._validate_and_plan(
            self.packet("prc-china-check-company-search"), ROOT
        )
        fake_bridge = SimpleNamespace(
            execute_request=lambda *args, **kwargs: {
                "success": False,
                "state": "rate_limited",
                "message": "HTTP 429",
                "data_present": False,
                "response": None,
                "upstream_metadata": {},
                "source_side_hard_stop": True,
                "error_type": "RATE_LIMITED",
                "provider": "china-check",
                "operation": "company-search",
            }
        )
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            api_task, "_load_prc_local_bridge", return_value=fake_bridge
        ), mock.patch.dict(
            os.environ,
            {"API_GATEWAY_MODE": "local-prc-open", "API_GATEWAY_BASE_URL": ""},
            clear=False,
        ):
            root = Path(tmp)
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
            rc = api_task.execute(plan_path, root / "out")
            snapshot = json.loads(
                (root / "out/api-snapshot.json").read_text(encoding="utf-8")
            )
            audit = json.loads((root / "out/api-audit.json").read_text(encoding="utf-8"))
        self.assertEqual(rc, 2)
        self.assertEqual(snapshot["status"], "API_FAILED")
        self.assertEqual(snapshot["requests"][0]["attempt_count"], 1)
        self.assertEqual(audit["source_side_hard_stop_count"], 1)


if __name__ == "__main__":
    unittest.main()
