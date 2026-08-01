#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
task = ROOT / "api-center" / "browserless" / "browserless_task.py"
tests = ROOT / "api-center" / "browserless" / "tests" / "test_browserless_task.py"

text = task.read_text(encoding="utf-8")
old = '''        if operation == "catalog-capabilities":
            snapshot = {"provider": provider_catalog()}
            metadata["credential_mode"] = "none"
'''
new = '''        if operation == "catalog-capabilities":
            snapshot = {"provider": provider_catalog()}
            metadata["credential_mode"] = "none"
            status = "API_BROWSERLESS_COMPLETED"
'''
if old not in text:
    if new not in text:
        raise SystemExit("catalog operation marker not found")
else:
    task.write_text(text.replace(old, new, 1), encoding="utf-8")

text = tests.read_text(encoding="utf-8")
marker = '''    def test_missing_secret_fails_without_exposing_value(self) -> None:
'''
addition = '''    def test_catalog_execution_succeeds_without_secret(self) -> None:
        value = ticket("catalog-capabilities", {})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            ticket_path.write_text(json.dumps(value), encoding="utf-8")
            with mock.patch.dict("os.environ", {}, clear=True):
                self.assertEqual(module.execute(ticket_path, root), 0)
            diagnostics = json.loads((root / "diagnostics.json").read_text(encoding="utf-8"))
            manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostics["status"], "API_BROWSERLESS_COMPLETED")
            self.assertEqual(manifest["status"], "API_BROWSERLESS_COMPLETED")
            self.assertFalse(diagnostics["metadata"]["upstream_called"])
            self.assertEqual(diagnostics["metadata"]["credential_mode"], "none")
            self.assertIsNone(diagnostics["failure"])

'''
if addition not in text:
    if marker not in text:
        raise SystemExit("test insertion marker not found")
    tests.write_text(text.replace(marker, addition + marker, 1), encoding="utf-8")

print("Browserless catalog status fix materialized")
