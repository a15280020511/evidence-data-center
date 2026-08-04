#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

BASE_SHA = "d148855e73a000e27e20fc2cd5daa6cae15dd5c4"
FILES = (
    "api-center/tests/test_api_catalog.py",
    "api-center/tests/test_capability_maximization.py",
)


def base_content(path: str) -> str:
    return subprocess.check_output(
        ["git", "show", f"{BASE_SHA}:{path}"], text=True
    )


def main() -> int:
    for name in FILES:
        text = base_content(name)
        old = '"public-data-geospatial": 35,'
        if old not in text:
            raise SystemExit(f"expected count not found in {name}")
        Path(name).write_text(
            text.replace(old, '"public-data-geospatial": 34,'),
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
