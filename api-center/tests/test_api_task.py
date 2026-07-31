from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("api_task", ROOT / "api_task.py")
assert SPEC and SPEC.loader
api_task = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(api_task)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        body = json.dumps(
            {
                "status": "1",
                "info": "OK",
                "infocode": "10000",
                "items": [{"value": 1}],
            }
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # noqa: A002
        return


class ApiTaskTests(unittest.TestCase):
    def plan(self) -> dict:
        return {
            "schema_version": "api-request-plan-v1",
            "task_id": "api-task-0001",
            "objective": "test",
            "ticket_sha256": "ticket-sha",
            "data_policy": {
                "classification": "public",
                "contains_personal_data": False,
            },
            "acceptance": {
                "require_all": True,
                "minimum_successful_requests": 1,
                "timeout_seconds": 5,
                "max_attempts": 1,
                "max_response_bytes_per_request": 100000,
            },
            "required_secret_environment_variables": ["DEMO_API_KEY"],
            "requests": [
                {
                    "request_id": "request-1",
                    "connector_id": "demo-api",
                    "endpoint": "/data/demo",
                    "method": "GET",
                    "parameters": {"q": "public"},
                    "allow_empty": False,
                    "response_contract": {
                        "status_path": "status",
                        "success_values": ["1"],
                        "error_code_path": "infocode",
                        "message_path": "info",
                        "any_data_paths": ["items"],
                    },
                    "connector_sha256": "connector-sha",
                }
            ],
        }

    def test_contract_supports_root_arrays_and_numeric_paths(self) -> None:
        payload = [{"page": 1}, [{"id": "CHN"}]]
        result = api_task.evaluate_response_contract(
            payload,
            {"success_when_data_present": True, "any_data_paths": ["1"]},
            allow_empty=False,
        )
        self.assertTrue(result["success"])
        self.assertTrue(result["data_present"])
        missing = api_task.evaluate_response_contract(
            [{"page": 1}, []],
            {"success_when_data_present": True, "any_data_paths": ["1"]},
            allow_empty=False,
        )
        self.assertFalse(missing["success"])

    def test_contract_detects_success_and_empty(self) -> None:
        contract = self.plan()["requests"][0]["response_contract"]
        ok = api_task.evaluate_response_contract(
            {"status": "1", "items": [1]}, contract, allow_empty=False
        )
        self.assertTrue(ok["success"])
        empty = api_task.evaluate_response_contract(
            {"status": "1", "items": []}, contract, allow_empty=False
        )
        self.assertFalse(empty["success"])
        self.assertEqual(empty["state"], "empty")

    def test_resolve_mode_writes_only_required_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch.dict(
                os.environ,
                {
                    "API_GATEWAY_BASE_URL": "",
                    "API_CENTER_SECRETS_JSON": json.dumps(
                        {"DEMO_API_KEY": "test-value", "UNUSED_KEY": "ignore-me"}
                    ),
                },
                clear=False,
            ):
                result = api_task.resolve_mode(self.plan(), root)
            self.assertEqual(result["mode"], "ephemeral")
            env_text = Path(result["env_file"]).read_text(encoding="utf-8")
            self.assertIn("DEMO_API_KEY=test-value", env_text)
            self.assertNotIn("UNUSED_KEY", env_text)
            public = (root / "gateway-mode.json").read_text(encoding="utf-8")
            self.assertNotIn("test-value", public)

    def test_malformed_optional_bundle_does_not_block_keyless_plan(self) -> None:
        plan = self.plan()
        plan["required_secret_environment_variables"] = []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch.dict(
                os.environ,
                {
                    "API_GATEWAY_BASE_URL": "",
                    "API_GATEWAY_AUTH_TOKEN": "",
                    "API_CENTER_SECRETS_JSON": "not-valid-json trailing",
                },
                clear=False,
            ):
                result = api_task.resolve_mode(plan, root)
            self.assertEqual(result["mode"], "ephemeral")
            self.assertEqual(result["secret_bundle_status"], "invalid_ignored")
            self.assertEqual(Path(result["env_file"]).read_text(encoding="utf-8"), "")

    def test_dedicated_secret_overrides_malformed_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch.dict(
                os.environ,
                {
                    "API_GATEWAY_BASE_URL": "",
                    "API_GATEWAY_AUTH_TOKEN": "",
                    "API_CENTER_SECRETS_JSON": "not-valid-json trailing",
                    "DEMO_API_KEY": "direct-test-value",
                },
                clear=False,
            ):
                result = api_task.resolve_mode(self.plan(), root)
            self.assertEqual(result["mode"], "ephemeral")
            self.assertEqual(result["secret_bundle_status"], "invalid_ignored")
            env_text = Path(result["env_file"]).read_text(encoding="utf-8")
            self.assertEqual(env_text, "DEMO_API_KEY=direct-test-value\n")
            public = (root / "gateway-mode.json").read_text(encoding="utf-8")
            self.assertNotIn("direct-test-value", public)

    def test_malformed_bundle_with_missing_required_secret_is_structured_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch.dict(
                os.environ,
                {
                    "API_GATEWAY_BASE_URL": "",
                    "API_GATEWAY_AUTH_TOKEN": "",
                    "API_CENTER_SECRETS_JSON": "not-valid-json trailing",
                    "DEMO_API_KEY": "",
                },
                clear=False,
            ):
                result = api_task.resolve_mode(self.plan(), root)
            self.assertEqual(result["mode"], "blocked")
            self.assertEqual(result["secret_bundle_status"], "invalid_ignored")
            self.assertEqual(result["missing_secret_environment_variables"], ["DEMO_API_KEY"])

    def test_execute_and_finalize(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                plan_path = root / "request-plan.json"
                plan_path.write_text(json.dumps(self.plan()), encoding="utf-8")
                with mock.patch.dict(
                    os.environ,
                    {
                        "API_GATEWAY_MODE": "ephemeral",
                        "API_GATEWAY_BASE_URL": f"http://127.0.0.1:{server.server_port}",
                        "API_GATEWAY_AUTH_TOKEN": "test-auth-value",
                        "GITHUB_RUN_ID": "123",
                    },
                    clear=False,
                ):
                    rc = api_task.execute(plan_path, root)
                self.assertEqual(rc, 0)
                snapshot = json.loads((root / "api-snapshot.json").read_text(encoding="utf-8"))
                self.assertEqual(snapshot["status"], "API_COMPLETED")
                self.assertEqual(snapshot["successful_request_count"], 1)
                serialized = json.dumps(snapshot)
                self.assertNotIn("test-auth-value", serialized)
                (root / "api-console.log").write_text("ok\n", encoding="utf-8")
                (root / "api-center-runtime.env").write_text(
                    "DEMO_API_KEY=test-value\n", encoding="utf-8"
                )
                api_task.finalize(root)
                diagnostics = json.loads((root / "api-diagnostics.json").read_text(encoding="utf-8"))
                self.assertEqual(diagnostics["stage_status"]["write_manifest"], "PASS")
                manifest = json.loads((root / "artifact-manifest.json").read_text(encoding="utf-8"))
                paths = {row["path"] for row in manifest["files"]}
                self.assertIn("api-snapshot.json", paths)
                self.assertIn("api-diagnostics.json", paths)
                self.assertIn("api-console.log", paths)
                self.assertNotIn("api-center-runtime.env", paths)
                self.assertNotIn("test-value", json.dumps(manifest))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_blocked_mode_is_structured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path = root / "request-plan.json"
            plan_path.write_text(json.dumps(self.plan()), encoding="utf-8")
            with mock.patch.dict(
                os.environ,
                {
                    "API_GATEWAY_MODE": "blocked",
                    "API_GATEWAY_BASE_URL": "",
                    "API_GATEWAY_BLOCK_REASON": "missing required Secret values",
                },
                clear=False,
            ):
                rc = api_task.execute(plan_path, root)
            self.assertEqual(rc, 3)
            snapshot = json.loads((root / "api-snapshot.json").read_text(encoding="utf-8"))
            self.assertEqual(snapshot["status"], "API_BLOCKED")


if __name__ == "__main__":
    unittest.main()
