#!/usr/bin/env python3
from __future__ import annotations

import runpy
from pathlib import Path

path = Path("api-center/tests/test_capability_maximization.py")
text = path.read_text(encoding="utf-8")
if '"baidu-ai-cloud": 3' not in text and '"baidu-ai-cloud": 4' not in text:
    marker = '            "serpapi": 4,\n'
    if text.count(marker) != 1:
        raise SystemExit("unable to insert Baidu capability count baseline")
    text = text.replace(marker, marker + '            "baidu-ai-cloud": 3,\n', 1)
    path.write_text(text, encoding="utf-8")

runpy.run_path("tools/tmp_enable_baidu_summary.py", run_name="__main__")
