#!/usr/bin/env python3
from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

import requests

FUZHOU = {"lat": 26.0745, "lon": 119.2965}
YEARS = list(range(1981, 2026))
MONTHS = set(range(8, 13))
SERVICE = "https://services2.arcgis.com/FiaPA4ga0iQKduv3/ArcGIS/rest/services/IBTrACS_ALL_list_v04r00_lines_1/FeatureServer/0/query"


def query_radius(session: requests.Session, radius_km: int) -> tuple[list[dict], int]:
    params = {
        "where": "year >= 1981 AND year <= 2025 AND month >= 8 AND month <= 12 AND BASIN = 'WP'",
        "geometry": json.dumps({"x": FUZHOU["lon"], "y": FUZHOU["lat"], "spatialReference": {"wkid": 4326}}),
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "distance": str(radius_km),
        "units": "esriSRUnit_Kilometer",
        "outFields": "SID,NAME,year,month,USA_WIND",
        "returnGeometry": "false",
        "resultRecordCount": "1000",
        "f": "json",
    }
    response = session.get(SERVICE, params=params, timeout=60, allow_redirects=False)
    response.raise_for_status()
    payload = response.json()
    if "error" in payload:
        raise RuntimeError(payload["error"])
    features = payload.get("features") or []
    if payload.get("exceededTransferLimit"):
        raise RuntimeError(f"query exceeded ArcGIS transfer limit at {radius_km} km")
    storms: dict[str, dict] = {}
    for feature in features:
        a = feature.get("attributes") or {}
        sid = str(a.get("SID") or "").strip()
        year = int(a.get("year") or 0)
        month = int(a.get("month") or 0)
        if not sid or year not in YEARS or month not in MONTHS:
            continue
        row = storms.setdefault(
            sid,
            {"sid": sid, "name": a.get("NAME"), "year": year, "months": set(), "max_wind_kt": None},
        )
        row["months"].add(month)
        wind = a.get("USA_WIND")
        if isinstance(wind, (int, float)) and wind >= 0:
            row["max_wind_kt"] = max(row["max_wind_kt"] or 0, float(wind))
    for row in storms.values():
        row["months"] = sorted(row["months"])
    return list(storms.values()), len(features)


def parse_oni(session: requests.Session) -> tuple[list[int], list[int]]:
    response = session.get(
        "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt",
        timeout=45,
        allow_redirects=False,
    )
    response.raise_for_status()
    by_year: dict[int, dict[str, float]] = defaultdict(dict)
    for line in response.text.splitlines():
        parts = line.split()
        if len(parts) < 4 or parts[0] == "SEAS":
            continue
        try:
            year = int(parts[1])
            anomaly = float(parts[-1])
        except ValueError:
            continue
        by_year[year][parts[0]] = anomaly
    analog, moderate_strong = [], []
    for year in YEARS:
        values = [by_year.get(year, {}).get(s) for s in ("ASO", "SON", "OND")]
        values = [v for v in values if v is not None]
        if values and max(values) >= 0.5:
            analog.append(year)
        if values and max(values) >= 1.0:
            moderate_strong.append(year)
    return analog, moderate_strong


def beta_interval(successes: int, trials: int, seed: int) -> dict:
    rng = random.Random(seed + successes * 1000 + trials)
    samples = sorted(rng.betavariate(successes + 1, trials - successes + 1) for _ in range(200000))
    return {
        "posterior_mean": round((successes + 1) / (trials + 2), 4),
        "credible_80": [round(samples[int(0.10 * len(samples))], 4), round(samples[int(0.90 * len(samples))], 4)],
        "credible_90": [round(samples[int(0.05 * len(samples))], 4), round(samples[int(0.95 * len(samples))], 4)],
    }


def main() -> int:
    session = requests.Session()
    session.headers.update({"User-Agent": "evidence-data-center-noaa-typhoon-model/1"})
    analog_years, moderate_strong_years = parse_oni(session)
    output = {
        "schema_version": "noaa-fuzhou-typhoon-model-v1",
        "location": FUZHOU,
        "historical_period": "1981-2025",
        "forecast_window": "2026-08-01/2026-12-31",
        "source": {
            "tracks": "NOAA IBTrACS v04r00 ArcGIS feature layer updated 2026-03-03",
            "enso": "NOAA CPC ONI",
        },
        "enso_analog_years": analog_years,
        "moderate_or_strong_enso_analog_years": moderate_strong_years,
        "radii": {},
    }
    for radius in (100, 200, 300):
        storms, feature_count = query_radius(session, radius)
        by_year: dict[int, list[dict]] = defaultdict(list)
        for storm in storms:
            by_year[storm["year"]].append(storm)
        hit_years = sorted(by_year)
        typhoon_years = sorted(
            year for year, rows in by_year.items() if any((row["max_wind_kt"] or 0) >= 64 for row in rows)
        )
        analog_hits = sorted(set(hit_years).intersection(analog_years))
        moderate_strong_hits = sorted(set(hit_years).intersection(moderate_strong_years))
        monthly_storms: dict[int, set[str]] = defaultdict(set)
        for storm in storms:
            for month in storm["months"]:
                monthly_storms[month].add(storm["sid"])
        output["radii"][str(radius)] = {
            "arcgis_feature_count": feature_count,
            "unique_storm_count": len(storms),
            "hit_year_count": len(hit_years),
            "hit_years": hit_years,
            "annual_hit_rate": round(len(hit_years) / len(YEARS), 4),
            "annual_hit_posterior": beta_interval(len(hit_years), len(YEARS), radius),
            "typhoon_intensity_hit_year_count": len(typhoon_years),
            "typhoon_intensity_hit_rate": round(len(typhoon_years) / len(YEARS), 4),
            "el_nino_analog_trials": len(analog_years),
            "el_nino_analog_hit_count": len(analog_hits),
            "el_nino_analog_hit_rate": round(len(analog_hits) / len(analog_years), 4),
            "el_nino_analog_posterior": beta_interval(len(analog_hits), len(analog_years), radius + 10),
            "moderate_strong_el_nino_trials": len(moderate_strong_years),
            "moderate_strong_el_nino_hit_count": len(moderate_strong_hits),
            "moderate_strong_el_nino_hit_rate": round(len(moderate_strong_hits) / len(moderate_strong_years), 4),
            "moderate_strong_el_nino_posterior": beta_interval(
                len(moderate_strong_hits), len(moderate_strong_years), radius + 20
            ),
            "monthly_unique_storm_counts": {str(month): len(monthly_storms[month]) for month in sorted(monthly_storms)},
            "storms": sorted(storms, key=lambda row: (row["year"], row["sid"])),
        }
    path = Path("noaa-fuzhou-typhoon-model.json")
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print("MODEL_RESULT_BEGIN")
    print(json.dumps(output, ensure_ascii=False))
    print("MODEL_RESULT_END")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
