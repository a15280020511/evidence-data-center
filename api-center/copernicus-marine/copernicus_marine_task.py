#!/usr/bin/env python3
"""Bounded Copernicus Marine Toolbox provider."""
from __future__ import annotations

import importlib
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, MutableMapping

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
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,199}$")
VARIABLE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")


def _parse_datetime(value: Any, name: str) -> datetime:
    text = str(value or "").strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO-8601 date-time") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _bbox(value: Any) -> list[float]:
    if not isinstance(value, list) or len(value) != 4:
        raise ValueError("bbox must contain [west,south,east,north]")
    try:
        west, south, east, north = [float(item) for item in value]
    except (TypeError, ValueError) as exc:
        raise ValueError("bbox values must be numeric") from exc
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError("bbox is invalid")
    if east - west > 2 or north - south > 2:
        raise ValueError("bbox span exceeds 2 degrees")
    return [west, south, east, north]


def _secret(name: str, environ: Mapping[str, str]) -> str:
    value = str(environ.get(name) or "").strip()
    if not value:
        raise RuntimeError(f"required backend credential is missing: {name}")
    return value


def _model_dump(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", exclude_none=True)
    if hasattr(value, "dict"):
        return value.dict(exclude_none=True)
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, list):
        return [_model_dump(item) for item in value]
    return value


def _compact_catalog(data: Any, max_products: int, max_datasets: int) -> Mapping[str, Any]:
    raw = _model_dump(data)
    if not isinstance(raw, Mapping):
        return {"catalog": raw}
    products = raw.get("products")
    compact_products: list[dict[str, Any]] = []
    if isinstance(products, list):
        for product in products[:max_products]:
            if not isinstance(product, Mapping):
                continue
            row: dict[str, Any] = {}
            for key in (
                "product_id",
                "title",
                "description",
                "thumbnail_url",
                "sources",
                "keywords",
            ):
                if key in product:
                    row[key] = product[key]
            datasets = product.get("datasets")
            if isinstance(datasets, list):
                compact_datasets = []
                for dataset in datasets[:max_datasets]:
                    if not isinstance(dataset, Mapping):
                        continue
                    compact_datasets.append(
                        {
                            key: dataset[key]
                            for key in (
                                "dataset_id",
                                "dataset_name",
                                "name",
                                "version",
                                "part",
                                "services",
                            )
                            if key in dataset
                        }
                    )
                row["datasets"] = compact_datasets
                row["datasets_returned"] = len(compact_datasets)
                row["datasets_available"] = len(datasets)
            compact_products.append(row)
    return {
        "products_returned": len(compact_products),
        "products_available": len(products) if isinstance(products, list) else None,
        "products": compact_products,
    }


def _describe(parameters: Mapping[str, Any]) -> Mapping[str, Any]:
    module = importlib.import_module("copernicusmarine")
    kwargs: dict[str, Any] = {}
    contains = parameters.get("contains")
    if contains is not None:
        if not isinstance(contains, list) or not 1 <= len(contains) <= 5:
            raise ValueError("contains must have 1 to 5 terms")
        terms = []
        for value in contains:
            text = str(value)
            if not 1 <= len(text) <= 80 or any(ord(ch) < 32 for ch in text):
                raise ValueError("contains term is invalid")
            terms.append(text)
        kwargs["contains"] = terms
    for field in ("product_id", "dataset_id"):
        if parameters.get(field):
            value = str(parameters[field])
            if not IDENTIFIER_RE.fullmatch(value):
                raise ValueError(f"{field} is invalid")
            kwargs[field] = value
    catalogue = module.describe(**kwargs)
    return _compact_catalog(
        catalogue,
        bounded_int(
            parameters.get("max_products"),
            default=10,
            minimum=1,
            maximum=20,
            name="max_products",
        ),
        bounded_int(
            parameters.get("max_datasets_per_product"),
            default=10,
            minimum=1,
            maximum=20,
            name="max_datasets_per_product",
        ),
    )


def _subset(
    parameters: Mapping[str, Any],
    output_dir: Path,
    max_bytes: int,
    environ: Mapping[str, str],
) -> tuple[Mapping[str, Any], bytes]:
    dataset_id = str(parameters.get("dataset_id") or "")
    if not IDENTIFIER_RE.fullmatch(dataset_id):
        raise ValueError("dataset_id is invalid")
    variables = parameters.get("variables")
    if not isinstance(variables, list) or not 1 <= len(variables) <= 5:
        raise ValueError("variables must contain 1 to 5 values")
    normalized_variables = [str(value) for value in variables]
    if len(set(normalized_variables)) != len(normalized_variables):
        raise ValueError("variables must be unique")
    if any(not VARIABLE_RE.fullmatch(value) for value in normalized_variables):
        raise ValueError("variable is invalid")
    west, south, east, north = _bbox(parameters.get("bbox"))
    start = _parse_datetime(parameters.get("start_datetime"), "start_datetime")
    end = _parse_datetime(parameters.get("end_datetime"), "end_datetime")
    if end <= start:
        raise ValueError("end_datetime must be after start_datetime")
    if (end - start).total_seconds() > 7 * 86400:
        raise ValueError("time span exceeds 7 days")
    minimum_depth = parameters.get("minimum_depth")
    maximum_depth = parameters.get("maximum_depth")
    if (minimum_depth is None) != (maximum_depth is None):
        raise ValueError("minimum_depth and maximum_depth must be supplied together")
    kwargs: dict[str, Any] = {
        "dataset_id": dataset_id,
        "variables": normalized_variables,
        "minimum_longitude": west,
        "maximum_longitude": east,
        "minimum_latitude": south,
        "maximum_latitude": north,
        "start_datetime": start.isoformat().replace("+00:00", "Z"),
        "end_datetime": end.isoformat().replace("+00:00", "Z"),
        "username": _secret("COPERNICUSMARINE_SERVICE_USERNAME", environ),
        "password": _secret("COPERNICUSMARINE_SERVICE_PASSWORD", environ),
        "output_directory": str(output_dir),
        "output_filename": "copernicus-marine-subset.csv",
        "file_format": "csv",
        "overwrite": True,
        "disable_progress_bar": True,
    }
    if minimum_depth is not None:
        low = float(minimum_depth)
        high = float(maximum_depth)
        if high < low or high - low > 500:
            raise ValueError("depth range is invalid or exceeds 500 meters")
        kwargs["minimum_depth"] = low
        kwargs["maximum_depth"] = high
    module = importlib.import_module("copernicusmarine")
    response = module.subset(**kwargs)
    target = output_dir / "copernicus-marine-subset.csv"
    if not target.exists():
        candidates = list(output_dir.glob("*.csv"))
        if len(candidates) != 1:
            raise RuntimeError("Toolbox did not produce exactly one CSV file")
        candidates[0].replace(target)
    raw = target.read_bytes()
    if len(raw) > max_bytes or len(raw) > 20_000_000:
        target.unlink(missing_ok=True)
        raise RuntimeError("subset output exceeds the configured size limit")
    return (
        {
            "dataset_id": dataset_id,
            "variables": normalized_variables,
            "bbox": [west, south, east, north],
            "start_datetime": kwargs["start_datetime"],
            "end_datetime": kwargs["end_datetime"],
            "response": _model_dump(response),
            "output_file": target.name,
            "output_bytes": len(raw),
            "output_sha256": bytes_sha(raw),
        },
        raw,
    )


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    max_bytes = bounded_int(
        acceptance.get("max_response_bytes"),
        default=10_000_000,
        minimum=1024,
        maximum=20_000_000,
        name="max_response_bytes",
    )
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_COPERNICUS_MARINE_FAILED"
    failure = None
    snapshot: Any = None
    metadata: MutableMapping[str, Any] = {
        "upstream_called": False,
        "secret_values_exposed": False,
        "write_operations_allowed": False,
        "whole_dataset_get_allowed": False,
        "model_calls": 0,
    }
    try:
        if operation == "catalog-capabilities":
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        elif operation == "describe":
            snapshot = {
                "provider": "copernicus-marine",
                "operation": operation,
                "data": _describe(parameters),
            }
            metadata.update(
                {
                    "upstream_called": True,
                    "credential_mode": "none",
                    "request_path": "copernicusmarine.describe",
                }
            )
        elif operation == "subset-csv":
            subset, raw = _subset(parameters, output_dir, max_bytes, os.environ)
            snapshot = {
                "provider": "copernicus-marine",
                "operation": operation,
                "data": subset,
            }
            metadata.update(
                {
                    "upstream_called": True,
                    "credential_mode": "backend-secret",
                    "credential_names": [
                        "COPERNICUSMARINE_SERVICE_USERNAME",
                        "COPERNICUSMARINE_SERVICE_PASSWORD",
                    ],
                    "request_path": "copernicusmarine.subset",
                    "response_bytes": len(raw),
                    "response_sha256": bytes_sha(raw),
                }
            )
        else:
            raise ValueError(f"unsupported operation: {operation}")
        encoded = json.dumps(snapshot, ensure_ascii=False, default=str).encode("utf-8")
        if len(encoded) > max_bytes:
            raise RuntimeError("snapshot exceeds acceptance.max_response_bytes")
        status = "INTEL_COPERNICUS_MARINE_COMPLETED"
    except Exception as exc:
        failure = {"type": type(exc).__name__, "message": str(exc)[:2000]}
        for path in output_dir.glob("*.csv"):
            if path.name != "snapshot.json":
                path.unlink(missing_ok=True)
    return finish_execution(
        ticket=ticket,
        output_dir=output_dir,
        status=status,
        snapshot=snapshot,
        metadata=metadata,
        failure=failure,
        started_at=started_at,
        started_perf=started_perf,
        schema_prefix="copernicus-marine",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-copernicus-marine]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="copernicus-marine-ticket-status-v1",
            display_name="Copernicus Marine",
        )
    )
