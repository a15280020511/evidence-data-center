#!/usr/bin/env python3
"""Governed modular OpenBB runtime for free, no-key data sources."""
from __future__ import annotations

import asyncio
import json
import math
import os
import sys
import time
from datetime import date, datetime
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any, Mapping

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
ACCESS_MATRIX_PATH = HERE / "provider-access-matrix.json"

PACKAGE_PINS = {
    "openbb-core": "1.6.13",
    "openbb-ecb": "1.6.1",
    "openbb-federal-reserve": "1.6.2",
    "openbb-famafrench": "1.2.1",
}

REMOTE_OPERATIONS = {
    "ecb-currency-reference-rates": {
        "provider": "openbb-ecb",
        "model": "CurrencyReferenceRates",
        "host": "www.ecb.europa.eu",
        "max_days": None,
    },
    "federal-reserve-federal-funds-rate": {
        "provider": "openbb-federal-reserve",
        "model": "FederalFundsRate",
        "host": "markets.newyorkfed.org",
        "max_days": 3660,
    },
    "federal-reserve-sofr": {
        "provider": "openbb-federal-reserve",
        "model": "SOFR",
        "host": "markets.newyorkfed.org",
        "max_days": 3660,
    },
    "fama-french-factors": {
        "provider": "openbb-famafrench",
        "model": "FamaFrenchFactors",
        "host": "mba.tuck.dartmouth.edu",
        "max_days": 7305,
    },
}


def get_fetcher(operation: str):
    """Resolve one allowlisted OpenBB fetcher without dynamic module input."""
    if operation == "ecb-currency-reference-rates":
        from openbb_ecb.models.currency_reference_rates import (
            ECBCurrencyReferenceRatesFetcher,
        )

        return ECBCurrencyReferenceRatesFetcher
    if operation == "federal-reserve-federal-funds-rate":
        from openbb_federal_reserve.models.federal_funds_rate import (
            FederalReserveFederalFundsRateFetcher,
        )

        return FederalReserveFederalFundsRateFetcher
    if operation == "federal-reserve-sofr":
        from openbb_federal_reserve.models.sofr import FederalReserveSOFRFetcher

        return FederalReserveSOFRFetcher
    if operation == "fama-french-factors":
        from openbb_famafrench.models.factors import FamaFrenchFactorsFetcher

        return FamaFrenchFactorsFetcher
    raise ValueError(f"unsupported OpenBB operation: {operation}")


def parse_iso_date(value: Any, name: str) -> date:
    """Parse a strict ISO date."""
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(f"{name} must be YYYY-MM-DD") from exc


def validate_range(parameters: Mapping[str, Any], maximum_days: int | None) -> None:
    """Bound date ranges before OpenBB receives them."""
    if maximum_days is None:
        return
    start = parse_iso_date(parameters.get("start_date"), "start_date")
    end = parse_iso_date(parameters.get("end_date"), "end_date")
    if end < start:
        raise ValueError("end_date must be on or after start_date")
    if (end - start).days > maximum_days:
        raise ValueError(f"date range exceeds {maximum_days} days")


def sanitize(value: Any) -> Any:
    """Convert OpenBB/Pydantic outputs into deterministic JSON-safe values."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if hasattr(value, "model_dump"):
        return sanitize(value.model_dump(mode="json"))
    if hasattr(value, "result") and hasattr(value, "metadata"):
        return {
            "result": sanitize(value.result),
            "metadata": sanitize(value.metadata),
        }
    if isinstance(value, Mapping):
        return {str(key): sanitize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [sanitize(item) for item in value]
    if hasattr(value, "to_dict"):
        try:
            return sanitize(value.to_dict(orient="records"))
        except TypeError:
            return sanitize(value.to_dict())
    return str(value)


def package_manifest() -> dict[str, Any]:
    """Return installed package versions without contacting a package index."""
    rows = []
    for package, pinned in PACKAGE_PINS.items():
        try:
            installed = importlib_metadata.version(package)
            status = "installed"
        except importlib_metadata.PackageNotFoundError:
            installed = None
            status = "missing"
        rows.append(
            {
                "package": package,
                "pinned_version": pinned,
                "installed_version": installed,
                "status": status,
                "license_family": "AGPL-3.0",
            }
        )
    return {
        "schema_version": "openbb-free-package-manifest-v1",
        "openbb_monolith_installed": False,
        "openbb_all_extra_installed": False,
        "package_count": len(rows),
        "packages": rows,
        "all_pins_satisfied": all(
            row["installed_version"] == row["pinned_version"] for row in rows
        ),
        "enabled_remote_operations": sorted(REMOTE_OPERATIONS),
    }


def row_count(payload: Any) -> int:
    """Estimate the number of returned records."""
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, Mapping):
        if isinstance(payload.get("result"), list):
            return len(payload["result"])
        return 1
    return 1


async def fetch_openbb(operation: str, parameters: Mapping[str, Any], timeout: int) -> Any:
    """Execute one allowlisted OpenBB fetcher."""
    fetcher = get_fetcher(operation)
    params = dict(parameters)
    metadata = REMOTE_OPERATIONS[operation]
    validate_range(params, metadata["max_days"])
    # Pydantic validation occurs before any network call.
    fetcher.transform_query(params=params)
    if os.getenv("OPENBB_FREE_FIXTURE_MODE") == "1":
        query = fetcher.transform_query(params=params)
        return {
            "fixture": True,
            "provider": metadata["provider"],
            "model": metadata["model"],
            "validated_query": sanitize(query),
            "records": [{"status": "fixture", "operation": operation}],
        }
    return await asyncio.wait_for(fetcher.fetch_data(params=params, credentials={}), timeout)


def execute(ticket_path: Path, output_dir: Path) -> int:
    """Execute one bounded OpenBB operation and persist an auditable receipt."""
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
        default=10000000,
        minimum=1024,
        maximum=10000000,
        name="max_response_bytes",
    )
    started_at, started_perf = utc_now(), time.perf_counter()
    status = "INTEL_OPENBB_FREE_FAILED"
    failure: Mapping[str, Any] | None = None
    snapshot: Mapping[str, Any] | None = None
    fixture_mode = os.getenv("OPENBB_FREE_FIXTURE_MODE") == "1"
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "network_used": False,
        "fixture_mode": fixture_mode,
        "requests_per_ticket_max": 1,
        "automatic_pagination": False,
        "wrapper_retry": False,
        "secret_used": False,
        "secret_values_exposed": False,
        "model_calls": 0,
        "openbb_monolith_installed": False,
        "paid_provider_calls_allowed": False,
        "trading_or_order_execution_allowed": False,
    }
    try:
        if operation == "catalog-capabilities":
            if parameters:
                raise ValueError("catalog-capabilities accepts no parameters")
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        elif operation == "provider-access-matrix":
            if parameters:
                raise ValueError("provider-access-matrix accepts no parameters")
            snapshot = load_json(ACCESS_MATRIX_PATH)
        elif operation == "package-manifest":
            if parameters:
                raise ValueError("package-manifest accepts no parameters")
            snapshot = package_manifest()
            if not snapshot["all_pins_satisfied"]:
                raise RuntimeError("one or more pinned OpenBB packages are missing or mismatched")
        else:
            operation_meta = REMOTE_OPERATIONS.get(operation)
            if operation_meta is None:
                raise ValueError(f"unsupported operation: {operation}")
            result = asyncio.run(fetch_openbb(operation, parameters, timeout))
            payload = sanitize(result)
            count = row_count(payload)
            if count > 10000:
                raise RuntimeError("OpenBB result exceeds rows_per_response_max=10000")
            stored = (
                json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
            ).encode("utf-8")
            if len(stored) > max_bytes:
                raise RuntimeError("OpenBB result exceeds acceptance.max_response_bytes")
            (output_dir / "response.json").write_bytes(stored)
            snapshot = {
                "provider": "openbb-free",
                "operation": operation,
                "openbb_provider": operation_meta["provider"],
                "openbb_model": operation_meta["model"],
                "row_count": count,
                "data": payload,
            }
            metadata.update(
                {
                    "upstream_called": not fixture_mode,
                    "network_used": not fixture_mode,
                    "api_host": operation_meta["host"],
                    "openbb_provider": operation_meta["provider"],
                    "openbb_model": operation_meta["model"],
                    "response_bytes": len(stored),
                    "response_sha256": bytes_sha(stored),
                    "row_count": count,
                    "package_manifest": package_manifest(),
                }
            )
        status = "INTEL_OPENBB_FREE_COMPLETED"
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
        schema_prefix="openbb-free",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-openbb-free]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="openbb-free-ticket-status-v1",
            display_name="OpenBB Free",
        )
    )
