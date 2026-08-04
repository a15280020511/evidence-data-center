#!/usr/bin/env python3
"""Temporary compatibility fix for the latest managed-provider catalog tail."""
from pathlib import Path

path = Path(__file__).resolve().parent / "build_catalog_market_search.py"
text = path.read_text(encoding="utf-8")

if "    COPERNICUS_MARINE_CATALOG,\n)" not in text:
    marker = "    NOAA_CDO_CATALOG,\n)"
    if marker not in text:
        raise SystemExit("latest managed-provider tuple tail marker not found")
    text = text.replace(
        marker,
        "    NOAA_CDO_CATALOG,\n    COPERNICUS_MARINE_CATALOG,\n)",
        1,
    )

if '        "copernicus-marine/provider-catalog.json",\n' not in text:
    marker = '        "noaa-cdo/provider-catalog.json",\n'
    if marker not in text:
        raise SystemExit("latest reading-order tail marker not found")
    text = text.replace(
        marker,
        marker + '        "copernicus-marine/provider-catalog.json",\n',
        1,
    )

path.write_text(text, encoding="utf-8")
