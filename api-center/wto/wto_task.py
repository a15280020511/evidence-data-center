#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "international-statistics"))
from provider_task import main
if __name__ == "__main__":
    raise SystemExit(main("wto"))
