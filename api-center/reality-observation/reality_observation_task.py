#!/usr/bin/env python3
"""Bounded read-only reality observation provider for the Intelligence Center."""
from __future__ import annotations

import csv
import io
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Mapping, MutableMapping

import requests

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from managed_provider_runtime import (  # noqa: E402
    bounded_int,
    bytes_sha,
    finish_execution,
    load_json,
    provider_row,
    run_cli,
    utc_now,
    validate_ticket,
)

SCHEMA_PATH = HERE / "ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"
USER_AGENT = "intelligence-center-reality-observation/1"

ALLOWED_PLANETARY_COLLECTIONS = {
    "naip",
    "sentinel-2-l2a",
    "landsat-c2-l2",
    "3dep-seamless",
    "io-lulc-9-class",
}
ALLOWED_EARTH_SEARCH_COLLECTIONS = {
    "sentinel-2-l2a",
    "landsat-c2-l2",
    "cop-dem-glo-30",
}
FIRMS_SOURCES = {"VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT", "MODIS_NRT"}
CELESTRAK_GROUPS = {
    "active",
    "stations",
    "weather",
    "resource",
    "science",
    "geo",
    "gnss",
    "starlink",
    "oneweb",
    "planet",
}
COOPS_PRODUCTS = {
    "water_level",
    "air_temperature",
    "water_temperature",
    "wind",
    "currents",
    "predictions",
}
ICAO_RE = re.compile(r"^[A-Z0-9]{4}(?:,[A-Z0-9]{4}){0,19}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATE8_RE = re.compile(r"^\d{8}$")
DT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T")
PERIOD_RE = re.compile(r"^\d{12}$")
STATION_RE = re.compile(r"^[A-Z0-9]{4,10}$")
ENTSOE_CODE_RE = re.compile(r"^[A-Z][0-9]{2}$")
EIC_RE = re.compile(r"^[0-9A-Z-]{16}$")


def _bounded_float(
    value: Any, *, minimum: float, maximum: float, name: str
) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if number < minimum or number > maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return number


def _bbox(parameters: Mapping[str, Any]) -> list[float]:
    value = parameters.get("bbox")
    if not isinstance(value, list) or len(value) != 4:
        raise ValueError("bbox must contain [west,south,east,north]")
    west = _bounded_float(value[0], minimum=-180, maximum=180, name="west")
    south = _bounded_float(value[1], minimum=-90, maximum=90, name="south")
    east = _bounded_float(value[2], minimum=-180, maximum=180, name="east")
    north = _bounded_float(value[3], minimum=-90, maximum=90, name="north")
    if west >= east or south >= north:
        raise ValueError("bbox ordering is invalid")
    if (east - west) > 30 or (north - south) > 30:
        raise ValueError("bbox span exceeds 30 degrees")
    return [west, south, east, north]


def _date(value: Any, name: str) -> str:
    text = str(value or "")
    if not DATE_RE.fullmatch(text):
        raise ValueError(f"{name} must be YYYY-MM-DD")
    return text


def _date8(value: Any, name: str) -> str:
    text = str(value or "")
    if not DATE8_RE.fullmatch(text):
        raise ValueError(f"{name} must be YYYYMMDD")
    return text


def _datetime(value: Any, name: str) -> str:
    text = str(value or "")
    if not DT_RE.match(text) or len(text) > 40:
        raise ValueError(f"{name} must be an ISO date-time")
    return text


def _secret(name: str, environ: Mapping[str, str]) -> str:
    value = str(environ.get(name) or "").strip()
    if not value:
        raise RuntimeError(f"required backend credential is missing: {name}")
    return value


def _collections(
    value: Any, allowed: set[str], *, name: str = "collections"
) -> list[str]:
    if not isinstance(value, list) or not 1 <= len(value) <= 5:
        raise ValueError(f"{name} must contain 1 to 5 values")
    normalized = [str(item) for item in value]
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{name} must be unique")
    if any(item not in allowed for item in normalized):
        raise ValueError(f"{name} contains a non-allowlisted collection")
    return normalized


def build_request(
    operation: str,
    parameters: Mapping[str, Any],
    *,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    env = environ or os.environ
    base_headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
    if operation == "catalog-capabilities":
        return {"method": "LOCAL", "url": None, "safe_path": "local", "headers": {}}

    if operation in {"planetary-stac-search", "earth-search-stac-search"}:
        planetary = operation == "planetary-stac-search"
        collections = _collections(
            parameters.get("collections"),
            ALLOWED_PLANETARY_COLLECTIONS if planetary else ALLOWED_EARTH_SEARCH_COLLECTIONS,
        )
        body: dict[str, Any] = {
            "collections": collections,
            "bbox": _bbox(parameters),
            "limit": bounded_int(
                parameters.get("limit"),
                default=20,
                minimum=1,
                maximum=100,
                name="limit",
            ),
        }
        if parameters.get("datetime"):
            body["datetime"] = str(parameters["datetime"])[:80]
        origin = (
            "https://planetarycomputer.microsoft.com/api/stac/v1"
            if planetary
            else "https://earth-search.aws.element84.com/v1"
        )
        return {
            "method": "POST",
            "url": origin + "/search",
            "safe_path": "/search",
            "headers": base_headers,
            "json": body,
            "response_kind": "json",
        }

    if operation == "nasa-firms-area":
        key = _secret("FIRMS_MAP_KEY", env)
        source = str(parameters.get("source") or "")
        if source not in FIRMS_SOURCES:
            raise ValueError("source is not allowlisted")
        bbox = ",".join(f"{value:g}" for value in _bbox(parameters))
        days = bounded_int(
            parameters.get("day_range"),
            default=1,
            minimum=1,
            maximum=5,
            name="day_range",
        )
        date = parameters.get("date")
        suffix = f"/{_date(date, 'date')}" if date else ""
        path = f"/api/area/csv/{key}/{source}/{bbox}/{days}{suffix}"
        safe = f"/api/area/csv/[REDACTED]/{source}/[BBOX]/{days}" + (
            "/[DATE]" if date else ""
        )
        return {
            "method": "GET",
            "url": "https://firms.modaps.eosdis.nasa.gov" + path,
            "safe_path": safe,
            "headers": {"Accept": "text/csv", "User-Agent": USER_AGENT},
            "response_kind": "csv",
            "credential_name": "FIRMS_MAP_KEY",
        }

    if operation == "nasa-eonet-events":
        query: dict[str, str] = {
            "status": str(parameters.get("status") or "open"),
            "days": str(
                bounded_int(
                    parameters.get("days"),
                    default=30,
                    minimum=1,
                    maximum=365,
                    name="days",
                )
            ),
            "limit": str(
                bounded_int(
                    parameters.get("limit"),
                    default=50,
                    minimum=1,
                    maximum=200,
                    name="limit",
                )
            ),
        }
        if query["status"] not in {"open", "closed", "all"}:
            raise ValueError("status is invalid")
        if parameters.get("category"):
            category = str(parameters["category"])
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", category):
                raise ValueError("category is invalid")
            query["category"] = category
        if parameters.get("bbox") is not None:
            query["bbox"] = ",".join(f"{value:g}" for value in _bbox(parameters))
        return {
            "method": "GET",
            "url": "https://eonet.gsfc.nasa.gov/api/v3/events",
            "safe_path": "/api/v3/events",
            "params": query,
            "headers": base_headers,
            "response_kind": "json",
        }

    if operation == "celestrak-gp":
        query = {"FORMAT": "json"}
        if parameters.get("catalog_number") is not None:
            query["CATNR"] = str(
                bounded_int(
                    parameters.get("catalog_number"),
                    default=0,
                    minimum=1,
                    maximum=999999,
                    name="catalog_number",
                )
            )
        else:
            group = str(parameters.get("group") or "active")
            if group not in CELESTRAK_GROUPS:
                raise ValueError("group is not allowlisted")
            query["GROUP"] = group
        return {
            "method": "GET",
            "url": "https://celestrak.org/NORAD/elements/gp.php",
            "safe_path": "/NORAD/elements/gp.php",
            "params": query,
            "headers": base_headers,
            "response_kind": "json",
        }

    if operation == "openaerialmap-search":
        return {
            "method": "GET",
            "url": "https://api.openaerialmap.org/meta",
            "safe_path": "/meta",
            "params": {
                "bbox": ",".join(f"{value:g}" for value in _bbox(parameters)),
                "limit": str(
                    bounded_int(
                        parameters.get("limit"),
                        default=20,
                        minimum=1,
                        maximum=100,
                        name="limit",
                    )
                ),
            },
            "headers": base_headers,
            "response_kind": "json",
        }


    if operation == "mapillary-image-search":
        token = _secret("MAPILLARY_ACCESS_TOKEN", env)
        bbox_values = _bbox(parameters)
        if (bbox_values[2] - bbox_values[0]) > 0.2 or (bbox_values[3] - bbox_values[1]) > 0.2:
            raise ValueError("Mapillary bbox span exceeds 0.2 degrees")
        return {
            "method": "GET",
            "url": "https://graph.mapillary.com/images",
            "safe_path": "/images",
            "params": {
                "bbox": ",".join(f"{value:g}" for value in bbox_values),
                "fields": "id,captured_at,computed_geometry,computed_compass_angle,thumb_1024_url,is_pano,sequence",
                "limit": str(
                    bounded_int(
                        parameters.get("limit"),
                        default=25,
                        minimum=1,
                        maximum=100,
                        name="limit",
                    )
                ),
            },
            "headers": {**base_headers, "Authorization": f"OAuth {token}"},
            "response_kind": "json",
            "credential_name": "MAPILLARY_ACCESS_TOKEN",
        }

    if operation == "kartaview-nearby-photos":
        lat = _bounded_float(
            parameters.get("latitude"), minimum=-90, maximum=90, name="latitude"
        )
        lng = _bounded_float(
            parameters.get("longitude"), minimum=-180, maximum=180, name="longitude"
        )
        radius = bounded_int(
            parameters.get("radius_m"),
            default=250,
            minimum=10,
            maximum=2000,
            name="radius_m",
        )
        zoom = bounded_int(
            parameters.get("zoom_level"),
            default=18,
            minimum=12,
            maximum=20,
            name="zoom_level",
        )
        return {
            "method": "GET",
            "url": "https://api.openstreetcam.org/2.0/photo/",
            "safe_path": "/2.0/photo/",
            "params": {
                "lat": f"{lat:.7f}",
                "lng": f"{lng:.7f}",
                "radius": str(radius),
                "zoomLevel": str(zoom),
                "join": "sequence",
                "orderBy": "id",
                "orderDirection": "desc",
            },
            "headers": base_headers,
            "response_kind": "json",
        }

    if operation == "ioos-erddap-search":
        search_for = str(parameters.get("search_for") or "")
        if not 1 <= len(search_for) <= 200 or any(ord(ch) < 32 for ch in search_for):
            raise ValueError("search_for is invalid")
        return {
            "method": "GET",
            "url": "https://erddap.ioos.us/erddap/search/index.json",
            "safe_path": "/erddap/search/index.json",
            "params": {
                "page": str(
                    bounded_int(
                        parameters.get("page"),
                        default=1,
                        minimum=1,
                        maximum=100,
                        name="page",
                    )
                ),
                "itemsPerPage": str(
                    bounded_int(
                        parameters.get("items_per_page"),
                        default=25,
                        minimum=1,
                        maximum=100,
                        name="items_per_page",
                    )
                ),
                "searchFor": search_for,
            },
            "headers": base_headers,
            "response_kind": "json",
        }

    if operation in {"aviationweather-metar", "aviationweather-taf"}:
        ids = str(parameters.get("ids") or "").upper()
        if not ICAO_RE.fullmatch(ids):
            raise ValueError("ids must contain 1 to 20 four-character ICAO identifiers")
        query = {"ids": ids, "format": "json"}
        if operation == "aviationweather-metar":
            query["hours"] = str(
                bounded_int(
                    parameters.get("hours"),
                    default=2,
                    minimum=1,
                    maximum=24,
                    name="hours",
                )
            )
        product = "metar" if operation.endswith("metar") else "taf"
        return {
            "method": "GET",
            "url": f"https://aviationweather.gov/api/data/{product}",
            "safe_path": f"/api/data/{product}",
            "params": query,
            "headers": base_headers,
            "response_kind": "json",
        }

    if operation == "earthscope-stations":
        west, south, east, north = _bbox(parameters)
        query = {
            "format": "geojson",
            "level": "station",
            "minlongitude": f"{west:g}",
            "minlatitude": f"{south:g}",
            "maxlongitude": f"{east:g}",
            "maxlatitude": f"{north:g}",
            "includeavailability": "false",
            "nodata": "404",
        }
        if parameters.get("start_time"):
            query["starttime"] = _date(parameters["start_time"], "start_time")
        if parameters.get("end_time"):
            query["endtime"] = _date(parameters["end_time"], "end_time")
        return {
            "method": "GET",
            "url": "https://service.earthscope.org/fdsnws/station/1/query",
            "safe_path": "/fdsnws/station/1/query",
            "params": query,
            "headers": base_headers,
            "response_kind": "json",
        }

    if operation == "noaa-swpc-kp":
        return {
            "method": "GET",
            "url": "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json",
            "safe_path": "/products/noaa-planetary-k-index.json",
            "headers": base_headers,
            "response_kind": "json",
        }

    if operation == "noaa-swpc-solar-wind":
        product = str(parameters.get("product") or "plasma-7-day")
        if product not in {"plasma-7-day", "mag-7-day"}:
            raise ValueError("product is invalid")
        return {
            "method": "GET",
            "url": f"https://services.swpc.noaa.gov/products/solar-wind/{product}.json",
            "safe_path": f"/products/solar-wind/{product}.json",
            "headers": base_headers,
            "response_kind": "json",
        }

    if operation == "safecast-measurements":
        query: dict[str, str] = {
            "page": str(
                bounded_int(
                    parameters.get("page"),
                    default=1,
                    minimum=1,
                    maximum=1000,
                    name="page",
                )
            ),
            "per_page": str(
                bounded_int(
                    parameters.get("per_page"),
                    default=50,
                    minimum=1,
                    maximum=100,
                    name="per_page",
                )
            ),
        }
        has_lat = parameters.get("latitude") is not None
        has_lng = parameters.get("longitude") is not None
        if has_lat != has_lng:
            raise ValueError("latitude and longitude must be supplied together")
        if has_lat:
            query["latitude"] = str(
                _bounded_float(
                    parameters["latitude"], minimum=-90, maximum=90, name="latitude"
                )
            )
            query["longitude"] = str(
                _bounded_float(
                    parameters["longitude"],
                    minimum=-180,
                    maximum=180,
                    name="longitude",
                )
            )
            query["distance"] = str(
                _bounded_float(
                    parameters.get("distance_km", 10),
                    minimum=0.1,
                    maximum=100,
                    name="distance_km",
                )
            )
        return {
            "method": "GET",
            "url": "https://api.safecast.org/measurements.json",
            "safe_path": "/measurements.json",
            "params": query,
            "headers": base_headers,
            "response_kind": "json",
        }

    if operation == "opensensemap-boxes":
        return {
            "method": "GET",
            "url": "https://api.opensensemap.org/boxes",
            "safe_path": "/boxes",
            "params": {
                "bbox": ",".join(f"{value:g}" for value in _bbox(parameters)),
                "minimal": "true" if parameters.get("minimal", True) else "false",
            },
            "headers": base_headers,
            "response_kind": "json",
        }

    if operation == "noaa-ndbc-latest":
        station = str(parameters.get("station") or "").upper()
        if not STATION_RE.fullmatch(station):
            raise ValueError("station is invalid")
        return {
            "method": "GET",
            "url": f"https://www.ndbc.noaa.gov/data/realtime2/{station}.txt",
            "safe_path": "/data/realtime2/[STATION].txt",
            "headers": {"Accept": "text/plain", "User-Agent": USER_AGENT},
            "response_kind": "text",
        }

    if operation == "noaa-coops-data":
        station = str(parameters.get("station") or "").upper()
        if not STATION_RE.fullmatch(station):
            raise ValueError("station is invalid")
        product = str(parameters.get("product") or "")
        if product not in COOPS_PRODUCTS:
            raise ValueError("product is invalid")
        query = {
            "product": product,
            "application": "intelligence-center",
            "begin_date": _date8(parameters.get("begin_date"), "begin_date"),
            "end_date": _date8(parameters.get("end_date"), "end_date"),
            "station": station,
            "time_zone": "gmt",
            "units": "metric",
            "format": "json",
        }
        if product in {"water_level", "predictions"}:
            query["datum"] = "MSL"
        if parameters.get("interval"):
            query["interval"] = str(parameters["interval"])
        return {
            "method": "GET",
            "url": "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter",
            "safe_path": "/api/prod/datagetter",
            "params": query,
            "headers": base_headers,
            "response_kind": "json",
        }


    if operation == "melbourne-transport-activity-latest":
        return {
            "method": "GET",
            "url": (
                "https://data.melbourne.vic.gov.au/api/explore/v2.1/catalog/datasets/"
                "transport-activity-counts/records"
            ),
            "safe_path": "/api/explore/v2.1/catalog/datasets/transport-activity-counts/records",
            "params": {
                "limit": str(
                    bounded_int(
                        parameters.get("limit"),
                        default=100,
                        minimum=1,
                        maximum=100,
                        name="limit",
                    )
                ),
                "offset": str(
                    bounded_int(
                        parameters.get("offset"),
                        default=0,
                        minimum=0,
                        maximum=10000,
                        name="offset",
                    )
                ),
                "order_by": "from desc",
            },
            "headers": base_headers,
            "response_kind": "json",
        }

    if operation in {"melbourne-pedestrian-latest", "melbourne-pedestrian-history"}:
        latest = operation.endswith("latest")
        dataset = (
            "pedestrian-counting-system-past-hour-counts-per-minute"
            if latest
            else "pedestrian-counting-system-monthly-counts-per-hour"
        )
        query: dict[str, str] = {
            "limit": str(
                bounded_int(
                    parameters.get("limit"),
                    default=100,
                    minimum=1,
                    maximum=100,
                    name="limit",
                )
            ),
            "order_by": "sensing_datetime desc" if latest else "sensing_date desc",
        }
        clauses = []
        if parameters.get("location_id") is not None:
            location_id = bounded_int(
                parameters.get("location_id"),
                default=0,
                minimum=1,
                maximum=1000,
                name="location_id",
            )
            clauses.append(f"location_id={location_id}")
        if not latest:
            clauses.append(
                f"sensing_date >= date'{_date(parameters.get('date_from'), 'date_from')}'"
            )
            clauses.append(
                f"sensing_date <= date'{_date(parameters.get('date_to'), 'date_to')}'"
            )
        if clauses:
            query["where"] = " and ".join(clauses)
        return {
            "method": "GET",
            "url": (
                "https://data.melbourne.vic.gov.au/api/explore/v2.1/catalog/datasets/"
                f"{dataset}/records"
            ),
            "safe_path": f"/api/explore/v2.1/catalog/datasets/{dataset}/records",
            "params": query,
            "headers": base_headers,
            "response_kind": "json",
        }

    if operation == "neso-generation-mix":
        if parameters.get("from_time") and parameters.get("to_time"):
            start = _datetime(parameters["from_time"], "from_time")
            end = _datetime(parameters["to_time"], "to_time")
            path = f"/generation/{start}/{end}"
        elif parameters.get("from_time") or parameters.get("to_time"):
            raise ValueError("from_time and to_time must be supplied together")
        else:
            path = "/generation"
        return {
            "method": "GET",
            "url": "https://api.carbonintensity.org.uk" + path,
            "safe_path": "/generation/[BOUNDED]" if path != "/generation" else path,
            "headers": base_headers,
            "response_kind": "json",
        }

    if operation == "elexon-generation-summary":
        return {
            "method": "GET",
            "url": "https://data.elexon.co.uk/bmrs/api/v1/generation/outturn/summary",
            "safe_path": "/bmrs/api/v1/generation/outturn/summary",
            "params": {
                "startTime": _datetime(parameters.get("start_time"), "start_time"),
                "endTime": _datetime(parameters.get("end_time"), "end_time"),
                "includeNegativeGeneration": "false",
                "format": "json",
            },
            "headers": base_headers,
            "response_kind": "json",
        }

    if operation == "elexon-demand-summary":
        resolution = str(parameters.get("resolution") or "hourly")
        if resolution not in {"minute", "hourly", "daily", "weekly"}:
            raise ValueError("resolution is invalid")
        return {
            "method": "GET",
            "url": "https://data.elexon.co.uk/bmrs/api/v1/demand/outturn/summary",
            "safe_path": "/bmrs/api/v1/demand/outturn/summary",
            "params": {
                "from": _datetime(parameters.get("from_time"), "from_time"),
                "to": _datetime(parameters.get("to_time"), "to_time"),
                "resolution": resolution,
                "format": "json",
            },
            "headers": base_headers,
            "response_kind": "json",
        }

    if operation == "fingrid-dataset":
        api_key = _secret("FINGRID_API_KEY", env)
        dataset_id = bounded_int(
            parameters.get("dataset_id"),
            default=0,
            minimum=1,
            maximum=10000,
            name="dataset_id",
        )
        query: dict[str, str] = {
            "pageSize": str(
                bounded_int(
                    parameters.get("page_size"),
                    default=100,
                    minimum=1,
                    maximum=1000,
                    name="page_size",
                )
            )
        }
        if parameters.get("start_time"):
            query["startTime"] = _datetime(parameters["start_time"], "start_time")
        if parameters.get("end_time"):
            query["endTime"] = _datetime(parameters["end_time"], "end_time")
        return {
            "method": "GET",
            "url": f"https://data.fingrid.fi/api/datasets/{dataset_id}/data",
            "safe_path": "/api/datasets/[DATASET]/data",
            "params": query,
            "headers": {
                **base_headers,
                "x-api-key": api_key,
            },
            "response_kind": "json",
            "credential_name": "FINGRID_API_KEY",
        }

    if operation == "entsoe-document":
        token = _secret("ENTSOE_API_TOKEN", env)
        document_type = str(parameters.get("document_type") or "")
        if not ENTSOE_CODE_RE.fullmatch(document_type):
            raise ValueError("document_type is invalid")
        query = {
            "securityToken": token,
            "documentType": document_type,
            "periodStart": str(parameters.get("period_start") or ""),
            "periodEnd": str(parameters.get("period_end") or ""),
        }
        if not PERIOD_RE.fullmatch(query["periodStart"]) or not PERIOD_RE.fullmatch(
            query["periodEnd"]
        ):
            raise ValueError("period_start and period_end must be YYYYMMDDHHMM")
        for field, upstream in (
            ("in_domain", "in_Domain"),
            ("out_domain", "out_Domain"),
        ):
            if parameters.get(field):
                value = str(parameters[field])
                if not EIC_RE.fullmatch(value):
                    raise ValueError(f"{field} is invalid")
                query[upstream] = value
        if parameters.get("process_type"):
            value = str(parameters["process_type"])
            if not ENTSOE_CODE_RE.fullmatch(value):
                raise ValueError("process_type is invalid")
            query["processType"] = value
        return {
            "method": "GET",
            "url": "https://web-api.tp.entsoe.eu/api",
            "safe_path": "/api?securityToken=[REDACTED]",
            "params": query,
            "headers": {"Accept": "application/xml", "User-Agent": USER_AGENT},
            "response_kind": "xml",
            "credential_name": "ENTSOE_API_TOKEN",
        }

    raise ValueError(f"unsupported operation: {operation}")


def _summarize_melbourne(data: Any) -> Mapping[str, Any]:
    if not isinstance(data, Mapping):
        return {"data": data}
    results = data.get("results")
    if not isinstance(results, list):
        return {"data": data}
    total = 0
    sensors: set[int] = set()
    latest = None
    for row in results:
        if not isinstance(row, Mapping):
            continue
        value = row.get("total_of_directions")
        try:
            total += int(value or 0)
        except (TypeError, ValueError):
            pass
        try:
            sensors.add(int(row.get("location_id")))
        except (TypeError, ValueError):
            pass
        timestamp = row.get("sensing_datetime")
        if isinstance(timestamp, str) and (latest is None or timestamp > latest):
            latest = timestamp
    return {
        "record_count": len(results),
        "sensor_count": len(sensors),
        "sum_total_of_directions": total,
        "latest_sensing_datetime": latest,
        "records": results,
        "total_count": data.get("total_count"),
    }



def _summarize_transport_activity(data: Any) -> Mapping[str, Any]:
    if not isinstance(data, Mapping):
        return {"data": data}
    results = data.get("results")
    if not isinstance(results, list):
        return {"data": data}
    by_class: dict[str, int] = {}
    total = 0
    countlines: set[int] = set()
    latest = None
    for row in results:
        if not isinstance(row, Mapping):
            continue
        road_class = str(row.get("class") or "unknown")
        try:
            value = int(row.get("count") or 0)
        except (TypeError, ValueError):
            value = 0
        total += value
        by_class[road_class] = by_class.get(road_class, 0) + value
        try:
            countlines.add(int(row.get("countlineid")))
        except (TypeError, ValueError):
            pass
        timestamp = row.get("from")
        if isinstance(timestamp, str) and (latest is None or timestamp > latest):
            latest = timestamp
    return {
        "record_count": len(results),
        "countline_count": len(countlines),
        "total_activity_count": total,
        "activity_by_class": by_class,
        "latest_interval_start": latest,
        "records": results,
        "total_count": data.get("total_count"),
    }

def _snapshot_from_response(operation: str, kind: str, raw: bytes, response: requests.Response) -> Any:
    if kind == "json":
        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError("upstream returned invalid JSON") from exc
        if operation == "melbourne-pedestrian-latest":
            return _summarize_melbourne(data)
        if operation == "melbourne-transport-activity-latest":
            return _summarize_transport_activity(data)
        return data
    text = raw.decode("utf-8", errors="replace")
    if kind == "csv":
        reader = csv.DictReader(io.StringIO(text))
        rows = []
        for index, row in enumerate(reader):
            if index >= 500:
                break
            rows.append(dict(row))
        return {
            "columns": reader.fieldnames or [],
            "row_count_returned": len(rows),
            "rows": rows,
        }
    return {
        "content_type": response.headers.get("Content-Type", ""),
        "text": text[:2_000_000],
        "truncated": len(text) > 2_000_000,
    }


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(
        acceptance.get("timeout_seconds"),
        default=60,
        minimum=5,
        maximum=120,
        name="timeout_seconds",
    )
    max_bytes = bounded_int(
        acceptance.get("max_response_bytes"),
        default=10_000_000,
        minimum=1024,
        maximum=20_000_000,
        name="max_response_bytes",
    )
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_REALITY_OBSERVATION_FAILED"
    failure = None
    snapshot: Any = None
    metadata: MutableMapping[str, Any] = {
        "upstream_called": False,
        "credential_mode": "none",
        "secret_values_exposed": False,
        "write_operations_allowed": False,
        "device_control_allowed": False,
        "individual_tracking_allowed": False,
        "model_calls": 0,
    }
    try:
        spec = build_request(operation, parameters)
        if spec["method"] == "LOCAL":
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        else:
            response = requests.request(
                spec["method"],
                spec["url"],
                params=spec.get("params"),
                json=spec.get("json"),
                headers=spec.get("headers"),
                timeout=timeout,
                allow_redirects=False,
            )
            raw = response.content
            if len(raw) > max_bytes:
                raise RuntimeError(
                    f"response exceeds acceptance.max_response_bytes={max_bytes}"
                )
            if not response.ok:
                sample = raw[:1000].decode("utf-8", errors="replace")
                raise RuntimeError(
                    f"upstream HTTP {response.status_code}: {sample}"
                )
            kind = str(spec.get("response_kind") or "json")
            snapshot = {
                "provider": "reality-observation",
                "operation": operation,
                "data": _snapshot_from_response(operation, kind, raw, response),
            }
            suffix = {
                "json": "json",
                "csv": "csv",
                "xml": "xml",
                "text": "txt",
            }.get(kind, "bin")
            (output_dir / f"response.{suffix}").write_bytes(raw)
            metadata.update(
                {
                    "upstream_called": True,
                    "http_status": response.status_code,
                    "content_type": response.headers.get("Content-Type", ""),
                    "request_origin": re.match(r"^https://[^/]+", str(spec["url"])).group(0),
                    "request_path": spec.get("safe_path"),
                    "response_bytes": len(raw),
                    "response_sha256": bytes_sha(raw),
                    "credential_mode": (
                        "backend-secret"
                        if spec.get("credential_name")
                        else "none"
                    ),
                    "credential_name": spec.get("credential_name"),
                }
            )
        status = "INTEL_REALITY_OBSERVATION_COMPLETED"
    except Exception as exc:
        failure = {"type": type(exc).__name__, "message": str(exc)[:2000]}
    return finish_execution(
        ticket=ticket,
        output_dir=output_dir,
        status=status,
        snapshot=snapshot,
        metadata=metadata,
        failure=failure,
        started_at=started_at,
        started_perf=started_perf,
        schema_prefix="reality-observation",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-reality-observation]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="reality-observation-ticket-status-v1",
            display_name="Reality Observation",
        )
    )
