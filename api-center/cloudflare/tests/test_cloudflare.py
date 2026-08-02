from __future__ import annotations

import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))
SPEC = importlib.util.spec_from_file_location("cloudflare_task", ROOT / "cloudflare_task.py")
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class CloudflareProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["CLOUDFLARE_API_TOKEN"] = "test-token-not-real"
        os.environ["CLOUDFLARE_ACCOUNT_ID"] = "0123456789abcdef0123456789abcdef"

    def test_catalog_has_22_read_only_operations(self) -> None:
        catalog = json.loads((ROOT / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "cloudflare")
        self.assertEqual(len(provider["operations"]), 22)
        self.assertFalse(provider["limits"]["write_operations_allowed"])
        self.assertFalse(provider["limits"]["urlscanner_submission_allowed"])
        self.assertTrue(all(row["result_contract"]["read_only"] for row in provider["operations"]))

    def test_browser_rendering_uses_fixed_cloudflare_host(self) -> None:
        records = [(2, 1, 6, "", ("93.184.216.34", 443))]
        with patch.object(mod.socket, "getaddrinfo", return_value=records):
            spec = mod.build("browser-markdown", {"url": "https://example.com/page?q=1"})
        self.assertEqual(spec.method, "POST")
        self.assertEqual(spec.url, "https://api.cloudflare.com/client/v4/accounts/0123456789abcdef0123456789abcdef/browser-rendering/markdown")
        self.assertEqual(spec.json_body, {"url": "https://example.com/page?q=1"})
        self.assertNotIn("test-token-not-real", spec.url)

    def test_radar_summary_dimension_is_allowlisted(self) -> None:
        spec = mod.build("radar-http-summary", {"dimension": "DEVICE_TYPE", "date_range": "7d", "location": "CN"})
        self.assertEqual(spec.url, "https://api.cloudflare.com/client/v4/radar/http/summary/DEVICE_TYPE")
        self.assertIn(("location", "CN"), spec.params)
        with self.assertRaises(ValueError):
            mod.build("radar-http-summary", {"dimension": "ARBITRARY_PATH"})

    def test_urlscanner_is_read_only_and_uuid_bounded(self) -> None:
        scan = "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e"
        spec = mod.build("urlscanner-result", {"scan_id": scan})
        self.assertEqual(spec.method, "GET")
        self.assertTrue(spec.url.endswith(f"/urlscanner/v2/result/{scan}"))
        with self.assertRaises(ValueError):
            mod.build("urlscanner-result", {"scan_id": "../../scan"})

    def test_private_ip_target_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            mod.validate_public_https_url("https://127.0.0.1/")


if __name__ == "__main__":
    unittest.main()
