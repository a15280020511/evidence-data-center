#!/usr/bin/env python3
from pathlib import Path

path = Path('api-center/tests/test_capability_maximization.py')
text = path.read_text(encoding='utf-8')
old_count = '            471,\n'
new_count = '            479,\n'
if old_count not in text:
    raise SystemExit('stale operation count not found')
text = text.replace(old_count, new_count, 1)
old_provider = '            "faostat": 7,\n'
new_provider = '            "faostat": 7,\n            "adb": 8,\n'
if old_provider not in text:
    raise SystemExit('FAOSTAT provider row not found')
text = text.replace(old_provider, new_provider, 1)
path.write_text(text, encoding='utf-8')
print('ADB capability test updated to 479 operations')
