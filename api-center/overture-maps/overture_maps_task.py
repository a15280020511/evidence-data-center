#!/usr/bin/env python3
"""Bounded read-only Overture Maps execution for API-center tickets."""
from __future__ import annotations

import json
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Mapping

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from managed_provider_runtime import (  # noqa: E402
    bounded_int,
    finish_execution,
    load_json,
    provider_row,
    run_cli,
    utc_now,
    validate_ticket,
)

SCHEMA_PATH = HERE / "ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"
FEATURE_TYPES = (
    "address", "bathymetry", "building", "building_part", "division",
    "division_area", "division_boundary", "place", "segment", "connector",
    "infrastructure", "land", "land_cover", "land_use", "water",
)


def validated_bbox(value: Any) -> tuple[float, float, float, float]:
    if not isinstance(value, list) or len(value) != 4:
        raise ValueError("bbox must contain [xmin, ymin, xmax, ymax]")
    try:
        xmin, ymin, xmax, ymax = (float(item) for item in value)
    except (TypeError, ValueError) as exc:
        raise ValueError("bbox values must be numeric") from exc
    if not (-180 <= xmin < xmax <= 180):
        raise ValueError("bbox longitude order/range is invalid")
    if not (-90 <= ymin < ymax <= 90):
        raise ValueError("bbox latitude order/range is invalid")
    area = (xmax - xmin) * (ymax - ymin)
    if area > 4.0:
        raise ValueError("bbox exceeds 4.0 square degrees")
    return xmin, ymin, xmax, ymax


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(
        acceptance.get("timeout_seconds"),
        default=60, minimum=5, maximum=120, name="timeout_seconds"
    )
    max_bytes = bounded_int(
        acceptance.get("max_response_bytes"),
        default=10_000_000, minimum=1024, maximum=20_000_000,
        name="max_response_bytes"
    )
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "API_OVERTURE_MAPS_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "official_origins": [
            "stac.overturemaps.org",
            "anonymous Overture Maps S3 us-west-2",
        ],
        "credential_mode": "none",
        "secret_values_exposed": False,
    }

    try:
        if operation == "catalog-capabilities":
            snapshot = {"provider": provider_row(CATALOG_PATH)}
            status = "API_OVERTURE_MAPS_COMPLETED"
        elif operation == "list-feature-types":
            snapshot = {"provider": "overture-maps", "feature_types": list(FEATURE_TYPES)}
            status = "API_OVERTURE_MAPS_COMPLETED"
        else:
            from overturemaps.core import (
                count_rows,
                get_available_releases,
                get_latest_release,
                query_gers_registry,
                record_batch_reader,
            )

            metadata["upstream_called"] = True
            if operation == "list-releases":
                releases, latest = get_available_releases()
                snapshot = {
                    "provider": "overture-maps",
                    "available_releases": list(releases),
                    "latest_release": latest,
                }
            elif operation == "latest-release":
                snapshot = {
                    "provider": "overture-maps",
                    "latest_release": get_latest_release(),
                }
            elif operation in {"count-features", "query-features"}:
                feature_type = str(parameters["feature_type"])
                if feature_type not in FEATURE_TYPES:
                    raise ValueError("feature_type is not allowlisted")
                bbox = validated_bbox(parameters["bbox"])
                release = parameters.get("release")
                if operation == "count-features":
                    count = count_rows(
                        feature_type,
                        bbox=bbox,
                        release=release,
                        connect_timeout=min(timeout, 30),
                        request_timeout=timeout,
                        stac=True,
                    )
                    snapshot = {
                        "provider": "overture-maps",
                        "feature_type": feature_type,
                        "bbox": list(bbox),
                        "release": release or "latest",
                        "feature_count": int(count),
                    }
                else:
                    from overturemaps.writers import GeoJSONWriter

                    limit = bounded_int(
                        parameters.get("limit"),
                        default=100, minimum=1, maximum=1000, name="limit"
                    )
                    reader = record_batch_reader(
                        feature_type,
                        bbox=bbox,
                        release=release,
                        connect_timeout=min(timeout, 30),
                        request_timeout=timeout,
                        stac=True,
                    )
                    if reader is None:
                        raise RuntimeError("Overture query returned no reader")
                    geojson_path = output_dir / "features.geojson"
                    written = 0
                    with GeoJSONWriter(str(geojson_path)) as writer:
                        while written < limit:
                            try:
                                batch = reader.read_next_batch()
                            except StopIteration:
                                break
                            if batch.num_rows <= 0:
                                continue
                            remaining = limit - written
                            if batch.num_rows > remaining:
                                batch = batch.slice(0, remaining)
                            writer.write_batch(batch)
                            written += batch.num_rows
                    size = geojson_path.stat().st_size
                    if size > max_bytes:
                        geojson_path.unlink(missing_ok=True)
                        raise RuntimeError(
                            f"GeoJSON exceeds acceptance.max_response_bytes={max_bytes}"
                        )
                    snapshot = {
                        "provider": "overture-maps",
                        "feature_type": feature_type,
                        "bbox": list(bbox),
                        "release": release or "latest",
                        "features_written": written,
                        "artifact_file": "features.geojson",
                        "artifact_bytes": size,
                    }
            elif operation == "lookup-gers":
                gers_id = str(parameters["gers_id"])
                parsed = str(uuid.UUID(gers_id))
                result = query_gers_registry(parsed)
                if result is None:
                    raise RuntimeError("GERS ID was not found")
                filepath, bbox_obj = result
                bbox = list(bbox_obj.as_tuple()) if bbox_obj is not None else None
                snapshot = {
                    "provider": "overture-maps",
                    "gers_id": parsed,
                    "registry_filepath": filepath,
                    "bbox": bbox,
                }
            else:
                raise ValueError(f"unsupported operation: {operation}")
            status = "API_OVERTURE_MAPS_COMPLETED"
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
        schema_prefix="overture-maps",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[api-overture]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="overture-maps-ticket-status-v1",
            display_name="Overture Maps",
        )
    )
