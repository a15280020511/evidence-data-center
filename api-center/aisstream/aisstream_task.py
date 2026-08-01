#!/usr/bin/env python3
"""Bounded read-only AISstream execution for Intelligence Center tickets."""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Mapping

import websockets

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
STREAM_URL = "wss://stream.aisstream.io/v0/stream"
MMSI_RE = re.compile(r"^[0-9]{9}$")
MESSAGE_TYPES = {
    "PositionReport",
    "UnknownMessage",
    "AddressedSafetyMessage",
    "AddressedBinaryMessage",
    "AidsToNavigationReport",
    "AssignedModeCommand",
    "BaseStationReport",
    "BinaryAcknowledge",
    "BinaryBroadcastMessage",
    "ChannelManagement",
    "CoordinatedUTCInquiry",
    "DataLinkManagementMessage",
    "DataLinkManagementMessageData",
    "ExtendedClassBPositionReport",
    "GroupAssignmentCommand",
    "GnssBroadcastBinaryMessage",
    "Interrogation",
    "LongRangeAisBroadcastMessage",
    "MultiSlotBinaryMessage",
    "SafetyBroadcastMessage",
    "ShipStaticData",
    "SingleSlotBinaryMessage",
    "StandardClassBPositionReport",
    "StandardSearchAndRescueAircraftReport",
    "StaticDataReport",
}


def _number(value: Any, *, name: str, minimum: float, maximum: float) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a number")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a number") from exc
    if not minimum <= parsed <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return parsed


def normalize_boxes(parameters: Mapping[str, Any]) -> list[list[list[float]]]:
    raw = parameters.get("bounding_boxes")
    if not isinstance(raw, list) or not raw:
        raise ValueError("bounding_boxes must be a non-empty array")
    if len(raw) > 4:
        raise ValueError("at most 4 bounding boxes are allowed")
    boxes: list[list[list[float]]] = []
    total_area = 0.0
    for box_index, box in enumerate(raw):
        if not isinstance(box, list) or len(box) != 2:
            raise ValueError(f"bounding_boxes[{box_index}] must contain two corners")
        corners: list[list[float]] = []
        for corner_index, corner in enumerate(box):
            if not isinstance(corner, list) or len(corner) != 2:
                raise ValueError(
                    f"bounding_boxes[{box_index}][{corner_index}] must be [latitude, longitude]"
                )
            lat = _number(
                corner[0],
                name=f"bounding_boxes[{box_index}][{corner_index}][0]",
                minimum=-90.0,
                maximum=90.0,
            )
            lon = _number(
                corner[1],
                name=f"bounding_boxes[{box_index}][{corner_index}][1]",
                minimum=-180.0,
                maximum=180.0,
            )
            corners.append([lat, lon])
        lat_span = abs(corners[0][0] - corners[1][0])
        lon_span = abs(corners[0][1] - corners[1][1])
        if lat_span == 0 or lon_span == 0:
            raise ValueError("bounding boxes must have non-zero area")
        area = lat_span * lon_span
        if area > 400.0:
            raise ValueError("each bounding box must not exceed 400 square degrees")
        total_area += area
        boxes.append(corners)
    if total_area > 800.0:
        raise ValueError("combined bounding-box area must not exceed 800 square degrees")
    return boxes


def normalize_mmsi(parameters: Mapping[str, Any]) -> list[str]:
    raw = parameters.get("mmsi") or []
    if not isinstance(raw, list):
        raise ValueError("mmsi must be an array")
    if len(raw) > 20:
        raise ValueError("at most 20 MMSI values are allowed")
    values = [str(value) for value in raw]
    if len(values) != len(set(values)):
        raise ValueError("mmsi values must be unique")
    if any(not MMSI_RE.fullmatch(value) for value in values):
        raise ValueError("each MMSI must contain exactly 9 digits")
    return values


def normalize_message_types(parameters: Mapping[str, Any]) -> list[str]:
    raw = parameters.get("message_types") or []
    if not isinstance(raw, list):
        raise ValueError("message_types must be an array")
    if len(raw) > 8:
        raise ValueError("at most 8 message types are allowed")
    values = [str(value) for value in raw]
    if len(values) != len(set(values)):
        raise ValueError("message_types must be unique")
    unknown = sorted(set(values) - MESSAGE_TYPES)
    if unknown:
        raise ValueError(f"unsupported message types: {', '.join(unknown)}")
    return values


def build_subscription(operation: str, parameters: Mapping[str, Any], api_key: str) -> dict[str, Any]:
    if operation == "catalog-capabilities":
        return {}
    boxes = normalize_boxes(parameters)
    mmsi = normalize_mmsi(parameters)
    message_types = normalize_message_types(parameters)
    if operation == "collect-vessel-positions":
        message_types = [
            "PositionReport",
            "StandardClassBPositionReport",
            "ExtendedClassBPositionReport",
        ]
    elif operation == "collect-vessel-static":
        message_types = ["ShipStaticData", "StaticDataReport"]
    elif operation != "collect-messages":
        raise ValueError(f"unsupported operation: {operation}")
    subscription: dict[str, Any] = {
        "APIKey": api_key,
        "BoundingBoxes": boxes,
    }
    if mmsi:
        subscription["FiltersShipMMSI"] = mmsi
    if message_types:
        subscription["FilterMessageTypes"] = message_types
    return subscription


async def collect_stream(
    *,
    subscription: Mapping[str, Any],
    duration_seconds: int,
    max_messages: int,
    max_response_bytes: int,
) -> tuple[list[Mapping[str, Any]], int]:
    messages: list[Mapping[str, Any]] = []
    raw_bytes = 0
    loop = asyncio.get_running_loop()
    deadline = loop.time() + duration_seconds
    async with websockets.connect(
        STREAM_URL,
        open_timeout=10,
        close_timeout=5,
        ping_interval=10,
        ping_timeout=10,
        max_size=2_000_000,
        max_queue=64,
    ) as websocket:
        await websocket.send(json.dumps(subscription, separators=(",", ":")))
        while len(messages) < max_messages:
            remaining = deadline - loop.time()
            if remaining <= 0:
                break
            try:
                raw = await asyncio.wait_for(websocket.recv(), timeout=min(remaining, 5.0))
            except asyncio.TimeoutError:
                continue
            if not isinstance(raw, str):
                raise RuntimeError("AISstream returned a non-text websocket frame")
            encoded = raw.encode("utf-8")
            raw_bytes += len(encoded)
            if raw_bytes > max_response_bytes:
                raise RuntimeError(
                    f"stream exceeds acceptance.max_response_bytes={max_response_bytes}"
                )
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise RuntimeError("AISstream returned invalid JSON") from exc
            if not isinstance(parsed, Mapping):
                raise RuntimeError("AISstream message is not an object")
            messages.append(parsed)
    return messages, raw_bytes


def summarize(messages: list[Mapping[str, Any]]) -> dict[str, Any]:
    message_types: dict[str, int] = {}
    vessels: dict[str, dict[str, Any]] = {}
    for row in messages:
        message_type = str(row.get("MessageType") or "Unknown")
        message_types[message_type] = message_types.get(message_type, 0) + 1
        metadata = row.get("MetaData") or row.get("Metadata") or {}
        if not isinstance(metadata, Mapping):
            continue
        mmsi = str(metadata.get("MMSI") or metadata.get("UserID") or "").strip()
        if not mmsi:
            continue
        vessels[mmsi] = {
            "mmsi": mmsi,
            "ship_name": metadata.get("ShipName"),
            "latitude": metadata.get("latitude", metadata.get("Latitude")),
            "longitude": metadata.get("longitude", metadata.get("Longitude")),
            "time_utc": metadata.get("time_utc", metadata.get("Time_utc")),
        }
    return {
        "message_count": len(messages),
        "message_type_counts": dict(sorted(message_types.items())),
        "unique_vessel_count": len(vessels),
        "latest_vessels": list(vessels.values())[:100],
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
        default=30,
        minimum=5,
        maximum=45,
        name="timeout_seconds",
    )
    duration = bounded_int(
        parameters.get("duration_seconds"),
        default=10,
        minimum=1,
        maximum=30,
        name="duration_seconds",
    )
    max_messages = bounded_int(
        parameters.get("max_messages"),
        default=50,
        minimum=1,
        maximum=200,
        name="max_messages",
    )
    max_bytes = bounded_int(
        acceptance.get("max_response_bytes"),
        default=5_000_000,
        minimum=1024,
        maximum=20_000_000,
        name="max_response_bytes",
    )
    if duration + 10 > timeout:
        raise ValueError("timeout_seconds must be at least duration_seconds + 10")
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_AISSTREAM_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "api_origin": "stream.aisstream.io",
        "transport": "wss",
        "credential_mode": "backend_secret",
        "secret_environment_variable": "AISSTREAM_API_KEY",
        "secret_values_exposed": False,
        "stream_bounded": True,
        "background_streaming": False,
    }
    try:
        if operation == "catalog-capabilities":
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        else:
            api_key = os.environ.get("AISSTREAM_API_KEY", "").strip()
            if not api_key:
                raise RuntimeError("AISSTREAM_API_KEY is not configured")
            subscription = build_subscription(operation, parameters, api_key)
            messages, raw_bytes = asyncio.run(
                collect_stream(
                    subscription=subscription,
                    duration_seconds=duration,
                    max_messages=max_messages,
                    max_response_bytes=max_bytes,
                )
            )
            safe_subscription = {
                key: value for key, value in subscription.items() if key != "APIKey"
            }
            payload = {
                "provider": "aisstream",
                "operation": operation,
                "subscription": safe_subscription,
                "duration_seconds": duration,
                "max_messages": max_messages,
                "summary": summarize(messages),
                "messages": messages,
            }
            encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            if len(encoded) > max_bytes:
                raise RuntimeError("serialized result exceeds max_response_bytes")
            (output_dir / "response.json").write_bytes(encoded)
            snapshot = payload
            metadata.update(
                {
                    "upstream_called": True,
                    "message_count": len(messages),
                    "response_bytes": len(encoded),
                    "wire_bytes": raw_bytes,
                    "response_sha256": bytes_sha(encoded),
                    "duration_seconds": duration,
                    "max_messages": max_messages,
                    "bounding_box_count": len(safe_subscription["BoundingBoxes"]),
                    "mmsi_filter_count": len(safe_subscription.get("FiltersShipMMSI", [])),
                    "message_type_filter_count": len(
                        safe_subscription.get("FilterMessageTypes", [])
                    ),
                }
            )
        status = "INTEL_AISSTREAM_COMPLETED"
    except Exception as exc:
        message = str(exc)
        secret = os.environ.get("AISSTREAM_API_KEY", "").strip()
        if secret:
            message = message.replace(secret, "[REDACTED]")
        failure = {"type": type(exc).__name__, "message": message[:2000]}
    return finish_execution(
        ticket=ticket,
        output_dir=output_dir,
        status=status,
        snapshot=snapshot,
        metadata=metadata,
        failure=failure,
        started_at=started_at,
        started_perf=started_perf,
        schema_prefix="aisstream",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-aisstream]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="aisstream-ticket-status-v1",
            display_name="AISstream",
        )
    )
