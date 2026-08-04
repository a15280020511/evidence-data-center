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
WHO_GHO_CATALOG = HERE / "who-gho/provider-catalog.json"
MEDIASTACK_CATALOG = HERE / "mediastack/provider-catalog.json"
STATISTICS_OF_THE_WORLD_CATALOG = HERE / "statistics-of-the-world/provider-catalog.json"
AISSTREAM_CATALOG = HERE / "aisstream/provider-catalog.json"
INTERNET_ARCHIVE_CATALOG = HERE / "internet-archive/provider-catalog.json"
MARKETSTACK_CATALOG = HERE / "marketstack/provider-catalog.json"
NASA_CATALOG = HERE / "nasa/provider-catalog.json"
METNO_GEOSATELLITE_CATALOG = HERE / "metno-geosatellite/provider-catalog.json"
COPERNICUS_CATALOG = HERE / "copernicus/provider-catalog.json"
EIA_CATALOG = HERE / "eia/provider-catalog.json"
UN_COMTRADE_CATALOG = HERE / "un-comtrade/provider-catalog.json"
OPENSKY_NETWORK_CATALOG = HERE / "opensky-network/provider-catalog.json"
HEXDB_AVIATION_CATALOG = HERE / "hexdb-aviation/provider-catalog.json"
WTO_CATALOG = HERE / "wto/provider-catalog.json"
IMF_CATALOG = HERE / "imf/provider-catalog.json"
WORLDBANK_DOCUMENTS_CATALOG = HERE / "worldbank-documents/provider-catalog.json"
BIS_CATALOG = HERE / "bis/provider-catalog.json"
ADB_CATALOG = HERE / "adb/provider-catalog.json"
KNOWLEDGE_TOOLS_CATALOG = HERE / "knowledge-tools/provider-catalog.json"
PUBLIC_DATA_GEOSPATIAL_CATALOG = HERE / "public-data-geospatial/provider-catalog.json"
CLOUDFLARE_CATALOG = HERE / "cloudflare/provider-catalog.json"
FRED_CATALOG = HERE / "fred/provider-catalog.json"
HUGGINGFACE_CATALOG = HERE / "huggingface/provider-catalog.json"
EVIDENCE_STANDARDIZATION_CATALOG = HERE / "evidence-standardization/provider-catalog.json"
GLOBAL_RESEARCH_INTELLIGENCE_CATALOG = HERE / "global-research-intelligence/provider-catalog.json"
OPENBB_FREE_CATALOG = HERE / "openbb-free/provider-catalog.json"
OPEN_DATA_AGGREGATORS_CATALOG = HERE / "open-data-aggregators/provider-catalog.json"
NIH_PUBLIC_HEALTH_CATALOG = HERE / "nih-public-health/provider-catalog.json"
OPENSTREETMAP_CATALOG = HERE / "openstreetmap/provider-catalog.json"
GNEWS_CATALOG = HERE / "gnews/provider-catalog.json"
GLOBAL_LITERATURE_LIBRARIES_CATALOG = HERE / "global-literature-libraries/provider-catalog.json"
GLOBAL_KNOWLEDGE_ARCHIVES_CATALOG = HERE / "global-knowledge-archives/provider-catalog.json"
GLOBAL_KNOWLEDGE_FABRIC_CATALOG = HERE / "global-knowledge-fabric/provider-catalog.json"
BAIDU_AI_CLOUD_CATALOG = HERE / "baidu-ai-cloud/provider-catalog.json"
OPEN_SOFTWARE_SECURITY_KNOWLEDGE_CATALOG = HERE / "open-software-security-knowledge/provider-catalog.json"
GOOGLE_PUBLIC_INTELLIGENCE_CATALOG = HERE / "google-public-intelligence/provider-catalog.json"
REALITY_OBSERVATION_CATALOG = HERE / "reality-observation/provider-catalog.json"
COPERNICUS_MARINE_CATALOG = HERE / "copernicus-marine/provider-catalog.json"
NOAA_CDO_CATALOG = HERE / "noaa-cdo/provider-catalog.json"
GLOBAL_SENSOR_BACKBONE_CATALOG = HERE / "global-sensor-backbone/provider-catalog.json"

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
    "who-gho-odata": 8,
    "mediastack": 5,
    "statistics-of-the-world": 11,
    "aisstream": 4,
    "internet-archive": 6,
    "marketstack": 11,
    "nasa": 25,
    "metno-geosatellite": 4,
    "copernicus-cdse": 7,
    "eia": 6,
    "un-comtrade": 10,
    "opensky-network": 9,
    "hexdb-aviation": 6,
    "wto": 7,
    "imf": 6,
    "worldbank-documents": 7,
    "bis": 8,
    "adb": 8,
    "wolfram-alpha": 4,
    "llamaparse": 3,
    "public-data-geospatial": 34,
    "cloudflare": 22,
    "fred": 25,
    "huggingface-hub": 11,
    "evidence-standardization": 8,
    "global-research-intelligence": 23,
    "openbb-free": 7,
    "open-data-aggregators": 13,
    "nih-public-health": 6,
    "openstreetmap": 6,
    "gnews": 3,
    "global-literature-libraries": 10,
    "global-knowledge-archives": 9,
    "global-knowledge-fabric": 9,
    "baidu-ai-cloud": 8,
    "open-software-security-knowledge": 11,
    "google-public-intelligence": 9,
    "reality-observation": 27,
    "copernicus-marine": 3,
    "noaa-cdo": 5,
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
    WHO_GHO_CATALOG,
    MEDIASTACK_CATALOG,
    STATISTICS_OF_THE_WORLD_CATALOG,
    AISSTREAM_CATALOG,
    INTERNET_ARCHIVE_CATALOG,
    MARKETSTACK_CATALOG,
    NASA_CATALOG,
    METNO_GEOSATELLITE_CATALOG,
    COPERNICUS_CATALOG,
    EIA_CATALOG,
    UN_COMTRADE_CATALOG,
    OPENSKY_NETWORK_CATALOG,
    HEXDB_AVIATION_CATALOG,
    WTO_CATALOG,
    IMF_CATALOG,
    WORLDBANK_DOCUMENTS_CATALOG,
    BIS_CATALOG,
    ADB_CATALOG,
    KNOWLEDGE_TOOLS_CATALOG,
    PUBLIC_DATA_GEOSPATIAL_CATALOG,
    CLOUDFLARE_CATALOG,
    FRED_CATALOG,
    HUGGINGFACE_CATALOG,
    EVIDENCE_STANDARDIZATION_CATALOG,
    GLOBAL_RESEARCH_INTELLIGENCE_CATALOG,
    OPENBB_FREE_CATALOG,
    OPEN_DATA_AGGREGATORS_CATALOG,
    NIH_PUBLIC_HEALTH_CATALOG,
    OPENSTREETMAP_CATALOG,
    GNEWS_CATALOG,
    GLOBAL_LITERATURE_LIBRARIES_CATALOG,
    GLOBAL_KNOWLEDGE_ARCHIVES_CATALOG,
    GLOBAL_KNOWLEDGE_FABRIC_CATALOG,
    BAIDU_AI_CLOUD_CATALOG,
    OPEN_SOFTWARE_SECURITY_KNOWLEDGE_CATALOG,
    GOOGLE_PUBLIC_INTELLIGENCE_CATALOG,
    REALITY_OBSERVATION_CATALOG,
    NOAA_CDO_CATALOG,
    COPERNICUS_MARINE_CATALOG,
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

    standalone = base.load_json(GLOBAL_SENSOR_BACKBONE_CATALOG)
    rows = standalone.get("providers") if isinstance(standalone, Mapping) else None
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], Mapping):
        raise ValueError("global sensor standalone provider catalog is invalid")
    sensor = rows[0]
    operations = sensor.get("operations")
    if sensor.get("provider_id") != "global-sensor-backbone" or not isinstance(operations, list) or len(operations) != 17:
        raise ValueError("global sensor standalone provider invariant failed")
    if standalone.get("secret_values_exposed") is not False:
        raise ValueError("global sensor standalone provider exposes secret values")
    catalog["standalone_managed_provider_catalogs"] = [
        {
            "provider_id": "global-sensor-backbone",
            "display_name": sensor.get("display_name"),
            "ticket_prefix": sensor.get("ticket_prefix"),
            "operation_count": len(operations),
            "catalog_path": "global-sensor-backbone/provider-catalog.json",
            "secret_values_exposed": False,
            "directly_invokable": True,
        }
    ]

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
        "who-gho/provider-catalog.json",
        "mediastack/provider-catalog.json",
        "statistics-of-the-world/provider-catalog.json",
        "aisstream/provider-catalog.json",
        "internet-archive/provider-catalog.json",
        "marketstack/provider-catalog.json",
        "nasa/provider-catalog.json",
        "metno-geosatellite/provider-catalog.json",
        "copernicus/provider-catalog.json",
        "eia/provider-catalog.json",
        "un-comtrade/provider-catalog.json",
        "opensky-network/provider-catalog.json",
        "hexdb-aviation/provider-catalog.json",
        "wto/provider-catalog.json",
        "imf/provider-catalog.json",
        "worldbank-documents/provider-catalog.json",
        "bis/provider-catalog.json",
        "adb/provider-catalog.json",
        "knowledge-tools/provider-catalog.json",
        "public-data-geospatial/provider-catalog.json",
        "cloudflare/provider-catalog.json",
        "fred/provider-catalog.json",
        "huggingface/provider-catalog.json",
        "evidence-standardization/provider-catalog.json",
        "global-research-intelligence/provider-catalog.json",
        "openbb-free/provider-catalog.json",
        "open-data-aggregators/provider-catalog.json",
        "nih-public-health/provider-catalog.json",
        "openstreetmap/provider-catalog.json",
        "gnews/provider-catalog.json",
        "global-literature-libraries/provider-catalog.json",
        "global-knowledge-archives/provider-catalog.json",
        "global-knowledge-fabric/provider-catalog.json",
        "baidu-ai-cloud/provider-catalog.json",
        "open-software-security-knowledge/provider-catalog.json",
        "google-public-intelligence/provider-catalog.json",
        "reality-observation/provider-catalog.json",
        "noaa-cdo/provider-catalog.json",
        "copernicus-marine/provider-catalog.json",
        "global-sensor-backbone/provider-catalog.json",
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
