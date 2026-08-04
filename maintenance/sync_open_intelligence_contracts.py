#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / "api-center/tests/test_api_catalog.py"
text = path.read_text(encoding="utf-8")
needle = '    "noaa-cdo": 5,\n}'
replacement = '    "noaa-cdo": 5,\n    "open-intelligence-toolkit": 22,\n}'
if replacement not in text:
    if needle not in text:
        raise SystemExit("expected operation-count insertion point not found")
    text = text.replace(needle, replacement, 1)
path.write_text(text, encoding="utf-8")
print("synchronized open-intelligence-toolkit operation count")
