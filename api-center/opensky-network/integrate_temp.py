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
    catalog_test = "api-center/tests/test_api_catalog.py"
    replace_once(
        catalog_test,
        '    "un-comtrade": 10,\n    "wolfram-alpha": 4,',
        '    "un-comtrade": 10,\n    "opensky-network": 9,\n    "wolfram-alpha": 4,',
    )
    replace_once(
        catalog_test,
        '        self.assertEqual(catalog["managed_provider_count"], 40)',
        '        self.assertEqual(catalog["managed_provider_count"], 41)',
    )
    replace_once(
        catalog_test,
        '        self.assertEqual(catalog["enabled_managed_provider_count"], 40)',
        '        self.assertEqual(catalog["enabled_managed_provider_count"], 41)',
    )
    replace_once(
        catalog_test,
        '        self.assertEqual(catalog["managed_operation_count"], 436)',
        '        self.assertEqual(catalog["managed_operation_count"], 445)',
    )
    replace_once(
        catalog_test,
        '            "un-comtrade": "UN_COMTRADE_API_KEY",\n            "wolfram-alpha": "WOLFRAM_ALPHA_APP_ID",',
        '            "un-comtrade": "UN_COMTRADE_API_KEY",\n            "opensky-network": "OPEN_SKY_CLIENT_SECRET",\n            "wolfram-alpha": "WOLFRAM_ALPHA_APP_ID",',
    )

    capability_test = "api-center/tests/test_capability_maximization.py"
    replace_once(capability_test, "            436,\n        )", "            445,\n        )")
    replace_once(
        capability_test,
        '            "un-comtrade": 10,\n            "wolfram-alpha": 4,',
        '            "un-comtrade": 10,\n            "opensky-network": 9,\n            "wolfram-alpha": 4,',
    )


if __name__ == "__main__":
    main()
