#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one match, found {count}: {old!r}")
    file.write_text(text.replace(old, new), encoding="utf-8")


def main() -> None:
    path = "api-center/build_catalog_market_search.py"
    replace_once(
        path,
        'UN_COMTRADE_CATALOG = HERE / "un-comtrade/provider-catalog.json"\nKNOWLEDGE_TOOLS_CATALOG',
        'UN_COMTRADE_CATALOG = HERE / "un-comtrade/provider-catalog.json"\nOPENSKY_NETWORK_CATALOG = HERE / "opensky-network/provider-catalog.json"\nKNOWLEDGE_TOOLS_CATALOG',
    )
    replace_once(
        path,
        '    "un-comtrade": 10,\n    "wolfram-alpha": 4,',
        '    "un-comtrade": 10,\n    "opensky-network": 9,\n    "wolfram-alpha": 4,',
    )
    replace_once(
        path,
        '    UN_COMTRADE_CATALOG,\n    KNOWLEDGE_TOOLS_CATALOG,',
        '    UN_COMTRADE_CATALOG,\n    OPENSKY_NETWORK_CATALOG,\n    KNOWLEDGE_TOOLS_CATALOG,',
    )
    replace_once(
        path,
        '        "un-comtrade/provider-catalog.json",\n        "knowledge-tools/provider-catalog.json",',
        '        "un-comtrade/provider-catalog.json",\n        "opensky-network/provider-catalog.json",\n        "knowledge-tools/provider-catalog.json",',
    )


if __name__ == "__main__":
    main()
