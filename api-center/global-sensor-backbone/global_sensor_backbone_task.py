#!/usr/bin/env python3
"""Bounded global real-world sensor backbone for the Intelligence Center."""
from __future__ import annotations

import json
import os
import ssl
import sys
import time
from pathlib import Path
from typing import Any, Mapping

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

WIS2_BROKERS = {
    "noaa": "wis2broker.globaldata.nws.noaa.gov",
    "meteofrance": "globalbroker.meteo.fr",
    "cma": "gb.wis.cma.cn",
    "inmet": "globalbroker.inmet.gov.br",
}

FIXED = {
    "glofas-collection": "https://ewds.climate.copernicus.eu/api/catalogue/v1/collections/cems-glofas-forecast",
    "ripe-atlas-probes": "https://atlas.ripe.net/api/v2/probes/",
    "ripe-atlas-measurements": "https://atlas.ripe.net/api/v2/measurements/",
    "ooni-measurements": "https://api.ooni.io/api/v1/measurements",
    "ooni-aggregation": "https://api.ooni.io/api/v1/aggregation",
    "eumetsat-collections": "https://api.eumetsat.int/data/browse/collections",
    "portwatch-collections": "https://portwatch.imf.org/api/search/v1/collections",
    "aemo-nemweb-index": "https://visualisations.aemo.com.au/aemo/nemweb/",
    "ecmwf-open-data-index": "https://data.ecmwf.int/forecasts/",
    "entsog-operational-data": "https://transparency.entsog.eu/api/v1/operationalData",
    "gie-storage": "https://agsi.gie.eu/api",
    "kpx-current-supply": "https://apis.data.go.kr/B552115/sukub5mMaxDatetime2/getSukub5mMaxDatetime2",
    "kpx-generation-mix": "https://openapi.kpx.or.kr/openapi/sumperfuel5m/getSumperfuel5m",
    "gfw-events": "https://gateway.api.globalfishingwatch.org/v3/events",
}

GFW_DATASETS = {
    "encounters": "public-global-encounters-events:latest",
    "loitering": "public-global-loitering-events:latest",
    "fishing": "public-global-fishing-events:latest",
    "port-visits": "public-global-port-visits-events:latest",
    "ais-gaps": "public-global-gaps-events:latest",
}


def _query(parameters: Mapping[str, Any], allowed: set[str]) -> dict[str, Any]:
    unexpected = sorted(set(parameters) - allowed)
    if unexpected:
        raise ValueError(f"unsupported parameters: {unexpected}")
    result: dict[str, Any] = {}
    for key, value in parameters.items():
        if value in (None, "", []):
            continue
        if isinstance(value, bool):
            result[key] = "true" if value else "false"
        elif isinstance(value, list):
            result[key] = ",".join(str(item) for item in value)
        else:
            result[key] = value
    return result


def build_request(
    operation: str,
    parameters: Mapping[str, Any],
) -> tuple[str | None, dict[str, Any], dict[str, str]]:
    headers = {
        "Accept": "application/json",
        "User-Agent": "gpts-global-sensor-backbone/1",
    }
    if operation in {"catalog-capabilities", "source-status"}:
        if parameters:
            raise ValueError(f"{operation} accepts no parameters")
        return None, {}, headers
    if operation == "wis2-notifications":
        return "mqtt", {}, headers
    if operation == "ripe-atlas-results":
        measurement_id = int(parameters["measurement_id"])
        if not 1 <= measurement_id <= 2_147_483_647:
            raise ValueError("measurement_id out of range")
        query = _query(parameters, {"measurement_id", "start", "stop", "probe_ids"})
        query.pop("measurement_id", None)
        return (
            f"https://atlas.ripe.net/api/v2/measurements/{measurement_id}/results/",
            query,
            headers,
        )
    if operation == "nasa-power-point":
        temporal = str(parameters.get("temporal") or "daily")
        if temporal not in {"hourly", "daily", "monthly", "climatology"}:
            raise ValueError("temporal must be hourly, daily, monthly or climatology")
        query = _query(
            parameters,
            {
                "temporal", "parameters", "latitude", "longitude", "start", "end",
                "community", "format",
            },
        )
        query.pop("temporal", None)
        query.setdefault("community", "RE")
        query.setdefault("format", "JSON")
        return (
            f"https://power.larc.nasa.gov/api/temporal/{temporal}/point",
            query,
            headers,
        )
    if operation == "portwatch-items":
        collection_id = str(parameters["collection_id"])
        if not collection_id or "/" in collection_id or ".." in collection_id:
            raise ValueError("invalid collection_id")
        query = _query(
            parameters, {"collection_id", "limit", "bbox", "datetime", "q"}
        )
        query.pop("collection_id", None)
        return (
            f"https://portwatch.imf.org/api/search/v1/collections/{collection_id}/items",
            query,
            headers,
        )
    if operation == "open-prices":
        resource = str(parameters.get("resource") or "prices")
        paths = {
            "prices": "prices",
            "stats": "prices/stats",
            "products": "products",
            "locations": "locations",
        }
        if resource not in paths:
            raise ValueError("unsupported Open Prices resource")
        query = _query(
            parameters,
            {
                "resource", "page", "size", "product_code", "location_osm_id",
                "date__gte", "date__lte",
            },
        )
        query.pop("resource", None)
        return (
            f"https://prices.openfoodfacts.org/api/v1/{paths[resource]}",
            query,
            headers,
        )
    if operation == "gfw-events":
        token = str(os.getenv("GLOBAL_FISHING_WATCH_API_TOKEN") or "").strip()
        if not token:
            raise RuntimeError("GLOBAL_FISHING_WATCH_API_TOKEN is not configured")
        event_type = str(parameters.get("event_type") or "port-visits")
        if event_type not in GFW_DATASETS:
            raise ValueError("unsupported event_type")
        query = _query(
            parameters,
            {
                "event_type", "start_date", "end_date", "limit", "offset",
                "vessels", "bounding_box",
            },
        )
        query.pop("event_type", None)
        query["datasets"] = GFW_DATASETS[event_type]
        headers["Authorization"] = f"Bearer {token}"
        return FIXED[operation], query, headers
    if operation == "gie-storage":
        token = str(os.getenv("GIE_API_KEY") or "").strip()
        if not token:
            raise RuntimeError("GIE_API_KEY is not configured")
        query = _query(
            parameters,
            {"country", "company", "facility", "from", "till", "page", "size"},
        )
        headers["x-key"] = token
        return FIXED[operation], query, headers
    if operation in {"kpx-current-supply", "kpx-generation-mix"}:
        token = str(os.getenv("KOREA_DATA_GO_KR_SERVICE_KEY") or "").strip()
        if not token:
            raise RuntimeError("KOREA_DATA_GO_KR_SERVICE_KEY is not configured")
        query = _query(parameters, {"dataType", "pageNo", "numOfRows"})
        query["serviceKey"] = token
        query.setdefault("dataType", "json")
        return FIXED[operation], query, headers
    if operation == "entsog-operational-data":
        return (
            FIXED[operation],
            _query(
                parameters,
                {
                    "from", "to", "indicator", "directionKey", "pointKey",
                    "operatorKey", "limit", "offset",
                },
            ),
            headers,
        )
    if operation == "ripe-atlas-probes":
        return (
            FIXED[operation],
            _query(
                parameters,
                {"country_code", "asn_v4", "asn_v6", "status", "is_public", "limit", "offset"},
            ),
            headers,
        )
    if operation == "ripe-atlas-measurements":
        return (
            FIXED[operation],
            _query(parameters, {"type", "status", "is_public", "target_ip", "limit", "offset"}),
            headers,
        )
    if operation == "ooni-measurements":
        return (
            FIXED[operation],
            _query(
                parameters,
                {"probe_cc", "test_name", "since", "until", "domain", "input", "anomaly", "confirmed", "limit", "offset"},
            ),
            headers,
        )
    if operation == "ooni-aggregation":
        return (
            FIXED[operation],
            _query(parameters, {"probe_cc", "test_name", "since", "until", "axis_x", "axis_y"}),
            headers,
        )
    if operation == "eumetsat-collections":
        return FIXED[operation], _query(parameters, {"format", "limit", "offset"}), headers
    if operation in {
        "glofas-collection",
        "portwatch-collections",
        "aemo-nemweb-index",
        "ecmwf-open-data-index",
    }:
        if parameters:
            raise ValueError(f"{operation} accepts no parameters")
        return FIXED[operation], {}, headers
    raise ValueError(f"unsupported operation: {operation}")


def _wis2(parameters: Mapping[str, Any], timeout: int) -> dict[str, Any]:
    try:
        import paho.mqtt.client as mqtt
    except ImportError as exc:
        raise RuntimeError("paho-mqtt is required for WIS2 notifications") from exc
    broker_id = str(parameters.get("broker") or "noaa")
    host = WIS2_BROKERS.get(broker_id)
    if not host:
        raise ValueError("unsupported WIS2 broker")
    topic = str(parameters.get("topic") or "origin/a/wis2/#")
    if not topic.startswith(("origin/a/wis2/", "cache/a/wis2/")):
        raise ValueError("WIS2 topic must stay inside origin/cache wis2 namespace")
    max_messages = bounded_int(
        parameters.get("max_messages"),
        default=10,
        minimum=1,
        maximum=25,
        name="max_messages",
    )
    messages: list[dict[str, Any]] = []
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set("everyone", "everyone")
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED)

    def on_connect(
        mqtt_client: Any,
        userdata: Any,
        flags: Any,
        reason_code: Any,
        properties: Any,
    ) -> None:
        if int(reason_code) != 0:
            raise RuntimeError(f"WIS2 MQTT connection failed: {reason_code}")
        mqtt_client.subscribe(topic, qos=0)

    def on_message(mqtt_client: Any, userdata: Any, msg: Any) -> None:
        raw = bytes(msg.payload or b"")
        try:
            payload: Any = json.loads(raw.decode("utf-8"))
        except Exception:
            payload = {"raw_text": raw[:5000].decode("utf-8", errors="replace")}
        messages.append({"topic": msg.topic, "payload": payload})
        if len(messages) >= max_messages:
            mqtt_client.disconnect()

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(host, 8883, keepalive=max(30, timeout))
    client.loop_start()
    deadline = time.monotonic() + min(timeout, 30)
    while time.monotonic() < deadline and len(messages) < max_messages:
        time.sleep(0.1)
    client.disconnect()
    client.loop_stop()
    return {
        "provider": "wmo-wis2",
        "broker": broker_id,
        "topic": topic,
        "message_count": len(messages),
        "messages": messages,
    }


def _safe_failure(exc: Exception) -> str:
    text = str(exc)
    for name in (
        "GLOBAL_FISHING_WATCH_API_TOKEN",
        "GIE_API_KEY",
        "KOREA_DATA_GO_KR_SERVICE_KEY",
    ):
        secret = str(os.getenv(name) or "")
        if secret:
            text = text.replace(secret, "[REDACTED]")
    return text[:2000]


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(
        acceptance.get("timeout_seconds"),
        default=30,
        minimum=5,
        maximum=120,
        name="timeout_seconds",
    )
    max_bytes = bounded_int(
        acceptance.get("max_response_bytes"),
        default=5_000_000,
        minimum=1024,
        maximum=20_000_000,
        name="max_response_bytes",
    )
    started_at, started_perf = utc_now(), time.perf_counter()
    status = "INTEL_GLOBAL_SENSOR_FAILED"
    failure: Mapping[str, Any] | None = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "requests_per_ticket_max": 1,
        "automatic_retry": False,
        "automatic_pagination": False,
        "redirects_allowed": False,
        "secret_values_exposed": False,
        "operation": operation,
    }
    try:
        url, query, headers = build_request(operation, parameters)
        if operation == "catalog-capabilities":
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        elif operation == "source-status":
            snapshot = {
                "provider": "global-sensor-backbone",
                "active_operations": sorted(
                    [
                        "wis2-notifications",
                        *FIXED.keys(),
                        "ripe-atlas-results",
                        "nasa-power-point",
                        "portwatch-items",
                        "open-prices",
                    ]
                ),
                "mapped_existing": [
                    "cloudflare-radar-outages",
                    "copernicus-cdse",
                    "copernicus-marine",
                    "opensky-network",
                    "openaq",
                    "usgs-earthquakes",
                ],
                "deferred_until_stable_public_api": [
                    "mobilitydatabase-feed-catalog"
                ],
                "licence_constraints": {
                    "gfw-events": "non-commercial-only",
                    "cloudflare-radar": "CC-BY-NC",
                },
            }
        elif url == "mqtt":
            snapshot = _wis2(parameters, timeout)
            metadata.update(
                {
                    "upstream_called": True,
                    "protocol": "MQTTS",
                    "api_host": WIS2_BROKERS[
                        str(parameters.get("broker") or "noaa")
                    ],
                }
            )
        else:
            response = requests.get(
                url,
                params=query,
                headers=headers,
                timeout=timeout,
                allow_redirects=False,
            )
            raw = bytes(response.content or b"")
            metadata.update(
                {
                    "upstream_called": True,
                    "request_url": url,
                    "query_parameter_names": sorted(query),
                    "http_status": int(response.status_code),
                    "content_type": str(response.headers.get("Content-Type") or ""),
                    "response_bytes": len(raw),
                }
            )
            if len(raw) > max_bytes:
                raise RuntimeError(
                    f"response exceeds acceptance.max_response_bytes={max_bytes}"
                )
            if not response.ok:
                excerpt = raw[:1000].decode("utf-8", errors="replace")
                raise RuntimeError(
                    f"upstream HTTP {response.status_code}: {excerpt}"
                )
            content_type = str(response.headers.get("Content-Type") or "").lower()
            if "json" in content_type or raw.lstrip().startswith((b"{", b"[")):
                data: Any = response.json()
            else:
                data = {"text": raw.decode("utf-8", errors="replace")}
            (output_dir / "response.bin").write_bytes(raw)
            snapshot = {
                "provider": "global-sensor-backbone",
                "operation": operation,
                "data": data,
            }
            metadata["response_sha256"] = bytes_sha(raw)
        status = "INTEL_GLOBAL_SENSOR_COMPLETED"
    except Exception as exc:
        failure = {"type": type(exc).__name__, "message": _safe_failure(exc)}
    return finish_execution(
        ticket=ticket,
        output_dir=output_dir,
        status=status,
        snapshot=snapshot,
        metadata=metadata,
        failure=failure,
        started_at=started_at,
        started_perf=started_perf,
        schema_prefix="global-sensor-backbone",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-global-sensor]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="global-sensor-backbone-ticket-status-v1",
            display_name="Global Sensor Backbone",
        )
    )
