#!/usr/bin/env python3
"""Bounded read-only AlphaFeed execution for API-center tickets."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any, Mapping

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from managed_provider_runtime import (  # noqa: E402
    bounded_int,
    finish_execution,
    json_safe,
    load_json,
    provider_row,
    run_cli,
    utc_now,
    validate_ticket,
)

SCHEMA_PATH = HERE / "ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"
API_KEY_ENV = "ALPHAFEED_API_KEY"


def api_key() -> str:
    value = str(os.getenv(API_KEY_ENV) or "").strip()
    if not value:
        raise RuntimeError(f"missing repository Secret {API_KEY_ENV}")
    if not 8 <= len(value) <= 512:
        raise RuntimeError(f"invalid repository Secret {API_KEY_ENV}")
    if any(ord(char) < 0x21 or ord(char) > 0x7E for char in value):
        raise RuntimeError(f"invalid repository Secret {API_KEY_ENV}: visible ASCII required")
    return value


def execute_sdk(operation: str, parameters: Mapping[str, Any]) -> Any:
    from alphafeed import AlphaFeed

    client = AlphaFeed(api_key=api_key())
    if operation == "quotes":
        symbols = parameters.get("symbols")
        universe = parameters.get("universe")
        if bool(symbols) == bool(universe):
            raise ValueError("quotes requires exactly one of symbols or universe")
        kwargs: dict[str, Any] = {"to_dataframe": False}
        if symbols:
            kwargs["symbols"] = list(symbols)
        else:
            kwargs["universes"] = str(universe)
        return client.quotes.get(**kwargs)
    if operation == "klines":
        kwargs = {
            "period": str(parameters.get("period") or "1d"),
            "count": bounded_int(
                parameters.get("count"), default=100, minimum=1, maximum=1000, name="count"
            ),
            "adjust": str(parameters.get("adjust") or "forward"),
            "to_dataframe": False,
        }
        return client.klines.get(str(parameters["symbol"]), **kwargs)
    if operation == "klines-batch":
        kwargs = {
            "period": str(parameters.get("period") or "1d"),
            "count": bounded_int(
                parameters.get("count"), default=100, minimum=1, maximum=500, name="count"
            ),
            "adjust": str(parameters.get("adjust") or "forward"),
            "to_dataframe": False,
            "show_progress": False,
        }
        return client.klines.batch(list(parameters["symbols"]), **kwargs)
    if operation == "intraday":
        return client.klines.intraday(
            str(parameters["symbol"]),
            period=str(parameters.get("period") or "1m"),
            to_dataframe=False,
        )
    if operation == "intraday-batch":
        return client.klines.intraday_batch(
            list(parameters["symbols"]),
            period=str(parameters.get("period") or "1m"),
            to_dataframe=False,
        )
    if operation == "depth":
        return client.depth.get(str(parameters["symbol"]))
    if operation == "instrument":
        return client.instruments.get(str(parameters["symbol"]))
    if operation == "instruments-batch":
        return client.instruments.batch(list(parameters["symbols"]))
    if operation == "adjustment-factors":
        return client.klines.ex_factors(
            list(parameters["symbols"]), to_dataframe=False
        )
    raise ValueError(f"unsupported AlphaFeed operation: {operation}")


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    bounded_int(
        acceptance.get("timeout_seconds"),
        default=45, minimum=5, maximum=90, name="timeout_seconds"
    )
    max_bytes = bounded_int(
        acceptance.get("max_response_bytes"),
        default=10_000_000, minimum=1024, maximum=20_000_000,
        name="max_response_bytes"
    )
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "API_ALPHAFEED_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "api_origin": "api.alphafeed.org",
        "credential_mode": "api-key-backend-only",
        "secret_values_exposed": False,
        "sdk_version": "0.1.4",
    }

    try:
        if operation == "catalog-capabilities":
            snapshot = {"provider": provider_row(CATALOG_PATH)}
            metadata["credential_mode"] = "none"
        else:
            result = json_safe(execute_sdk(operation, parameters))
            encoded = __import__("json").dumps(
                result, ensure_ascii=False, allow_nan=False
            ).encode("utf-8")
            if len(encoded) > max_bytes:
                raise RuntimeError(
                    f"response exceeds acceptance.max_response_bytes={max_bytes}"
                )
            snapshot = {
                "provider": "alphafeed",
                "operation": operation,
                "data": result,
            }
            metadata.update(
                {
                    "upstream_called": True,
                    "response_bytes": len(encoded),
                }
            )
        status = "API_ALPHAFEED_COMPLETED"
    except Exception as exc:
        message = str(exc)
        secret = str(os.getenv(API_KEY_ENV) or "")
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
        schema_prefix="alphafeed",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[api-alphafeed]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="alphafeed-ticket-status-v1",
            display_name="AlphaFeed",
        )
    )
