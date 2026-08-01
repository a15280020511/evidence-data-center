#!/usr/bin/env python3
"""Remove assertions for fields intentionally omitted from the normalized global catalog."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "api-center/tests/test_api_catalog.py"
text = path.read_text(encoding="utf-8")
for line in (
    '        self.assertEqual(providers["miaoxiang-mcp"]["official_endpoint"], "https://mxapi.eastmoney.com/mxds/mcp")\n',
    '        self.assertEqual(providers["miaoxiang-mcp"]["mcp_protocol_version"], "2025-11-25")\n',
):
    if text.count(line) != 1:
        raise RuntimeError(f"expected one global-catalog assertion: {line!r}")
    text = text.replace(line, "", 1)
path.write_text(text, encoding="utf-8")
Path(__file__).unlink()
