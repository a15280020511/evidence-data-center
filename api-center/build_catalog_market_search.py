#!/usr/bin/env python3
"""Compatibility wrapper that extends the API catalog with managed providers."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any, Mapping

HERE = Path(__file__).resolve().parent
BASE_SPEC = importlib.util.spec_from_file_location("base_build_catalog", HERE / "build_catalog.py")
if BASE_SPEC is None or BASE_SPEC.loader is None:
    raise RuntimeError("unable to load base API catalog generator")
base = importlib.util.module_from_spec(BASE_SPEC)
BASE_SPEC.loader.exec_module(base)

MARKET_SEARCH_CATALOG = HERE / "market-search/provider-catalog.json"
TUSHARE_CATALOG = HERE / "tushare/provider-catalog.json"
BAOSTOCK_CATALOG = HERE / "baostock/provider-catalog.json"
EODHD_CATALOG = HERE / "eodhd/provider-catalog.json"
DATA_COMMONS_CATALOG = HERE / "data-commons/provider-catalog.json"
QWEATHER_CATALOG = HERE / "qweather/provider-catalog.json"
XWEATHER_CATALOG = HERE / "xweather/provider-catalog.json"
MIAOXIANG_MCP_CATALOG = HERE / "miaoxiang-mcp/provider-catalog.json"
EAST_ASIA_ECON_CATALOG = HERE / "east-asia-econ/provider-catalog.json"
ALPHA_VANTAGE_CATALOG = HERE / "alpha-vantage/provider-catalog.json"
OVERTURE_MAPS_CATALOG = HERE / "overture-maps/provider-catalog.json"
OECD_CATALOG = HERE / "oecd/provider-catalog.json"
ALPHAFEED_CATALOG = HERE / "alphafeed/provider-catalog.json"
GAPUP_MCP_CATALOG = HERE / "gapup-mcp/provider-catalog.json"
KNOWLEDGE_TOOLS_CATALOG = HERE / "knowledge-tools/provider-catalog.json"
EXPECTED_EXTENDED_PROVIDERS = {
    "tickflow": 5,
    "serpapi": 4,
    "tushare": 20,
    "baostock": 20,
    "eodhd": 25,
    "data-commons": 5,
    "qweather": 18,
    "xweather": 10,
    "miaoxiang-mcp": 13,
    "east-asia-econ": 6,
    "alpha-vantage": 66,
    "overture-maps": 7,
    "oecd": 6,
    "alphafeed": 10,
    "gapup-mcp": 209,
    "wolfram-alpha": 4,
    "llamaparse": 3,
}
base.MANAGED_PROVIDER_CATALOG_PATHS = (
    *base.MANAGED_PROVIDER_CATALOG_PATHS,
    MARKET_SEARCH_CATALOG,
    TUSHARE_CATALOG,
    BAOSTOCK_CATALOG,
    EODHD_CATALOG,
    DATA_COMMONS_CATALOG,
    QWEATHER_CATALOG,
    XWEATHER_CATALOG,
    MIAOXIANG_MCP_CATALOG,
    EAST_ASIA_ECON_CATALOG,
    ALPHA_VANTAGE_CATALOG,
    OVERTURE_MAPS_CATALOG,
    OECD_CATALOG,
    ALPHAFEED_CATALOG,
    GAPUP_MCP_CATALOG,
    KNOWLEDGE_TOOLS_CATALOG,
)

load_json = base.load_json
canonical_sha = base.canonical_sha


def build(manifest_path: Path, metadata_path: Path, connector_root: Path) -> dict[str, Any]:
    catalog = base.build(manifest_path, metadata_path, connector_root)
    providers = {row["provider_id"]: row for row in catalog["managed_providers"]}
    for provider_id, expected_operations in EXPECTED_EXTENDED_PROVIDERS.items():
        provider = providers.get(provider_id)
        if provider is None or provider["operation_count"] != expected_operations:
            raise ValueError(
                f"extended provider invariant failed: {provider_id}/{expected_operations}"
            )
        if provider["secret_value_exposed"] is not False:
            raise ValueError(f"extended provider exposes secret values: {provider_id}")

    reading_order = list(catalog.get("detail_reading_order") or [])
    for item in (
        "market-search/provider-catalog.json",
        "tushare/provider-catalog.json",
        "baostock/provider-catalog.json",
        "eodhd/provider-catalog.json",
        "data-commons/provider-catalog.json",
        "qweather/provider-catalog.json",
        "xweather/provider-catalog.json",
        "miaoxiang-mcp/provider-catalog.json",
        "east-asia-econ/provider-catalog.json",
        "alpha-vantage/provider-catalog.json",
        "overture-maps/provider-catalog.json",
        "oecd/provider-catalog.json",
        "alphafeed/provider-catalog.json",
        "gapup-mcp/provider-catalog.json",
        "knowledge-tools/provider-catalog.json",
    ):
        if item not in reading_order:
            insert_at = (
                reading_order.index("catalog-metadata.json")
                if "catalog-metadata.json" in reading_order
                else len(reading_order)
            )
            reading_order.insert(insert_at, item)
    catalog["detail_reading_order"] = reading_order
    catalog.pop("catalog_sha256", None)
    catalog["catalog_sha256"] = base.canonical_sha(catalog)
    return catalog


def render_markdown(catalog: Mapping[str, Any]) -> str:
    return base.render_markdown(catalog)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(HERE / "connector-manifest.json"))
    parser.add_argument("--metadata", default=str(HERE / "catalog-metadata.json"))
    parser.add_argument("--json-output", default=str(HERE / "api-catalog.json"))
    parser.add_argument("--markdown-output", default=str(HERE / "api-catalog.md"))
    args = parser.parse_args()
    catalog = build(Path(args.manifest), Path(args.metadata), HERE / "connectors")
    Path(args.json_output).write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    Path(args.markdown_output).write_text(render_markdown(catalog), encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "connector_count": catalog["connector_count"],
        "managed_provider_count": catalog["managed_provider_count"],
        "managed_operation_count": catalog["managed_operation_count"],
        "catalog_sha256": catalog["catalog_sha256"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
