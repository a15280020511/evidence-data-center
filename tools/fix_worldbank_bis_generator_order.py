#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).with_name("add_worldbank_docs_bis.py")
text = path.read_text(encoding="utf-8")
old = "replace_once(catalog_test, '    \"imf\": 6,\\n    \"adb\": 8,', '    \"imf\": 6,\\n    \"worldbank-documents\": 7,\\n    \"bis\": 8,\\n    \"adb\": 8,')"
new = "replace_once(catalog_test, '    \"imf\": 6,\\n    \"wolfram-alpha\": 4,', '    \"imf\": 6,\\n    \"worldbank-documents\": 7,\\n    \"bis\": 8,\\n    \"wolfram-alpha\": 4,')"
if old not in text:
    raise RuntimeError("expected catalog ordering pattern not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
