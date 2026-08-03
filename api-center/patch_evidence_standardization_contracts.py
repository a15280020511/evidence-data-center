#!/usr/bin/env python3
"""One-shot synchronization of aggregate test contracts for evidence standardization."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_exact(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        if new in text:
            return
        raise RuntimeError(f"expected contract text not found in {path}: {old!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def main() -> int:
    api_catalog = ROOT / "api-center/tests/test_api_catalog.py"
    replace_exact(api_catalog, '    "huggingface-hub": 11,\n}', '    "huggingface-hub": 11,\n    "evidence-standardization": 8,\n}')
    replace_exact(api_catalog, 'catalog["managed_provider_count"], 51', 'catalog["managed_provider_count"], 52')
    replace_exact(api_catalog, 'catalog["enabled_managed_provider_count"], 51', 'catalog["enabled_managed_provider_count"], 52')
    replace_exact(api_catalog, 'catalog["managed_operation_count"], 580', 'catalog["managed_operation_count"], 588')

    capability = ROOT / "api-center/tests/test_capability_maximization.py"
    replace_exact(capability, '            580,\n', '            588,\n')
    replace_exact(capability, '            "huggingface-hub": 11,\n        }', '            "huggingface-hub": 11,\n            "evidence-standardization": 8,\n        }')
    print("evidence standardization aggregate contracts synchronized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
