#!/usr/bin/env python3
"""Hardened runtime entry for the Cloudflare China numeric compiler.

This module applies the validated response-schema and Arrow-row builders to the
base implementation, verifies the supplemental China domain control file, and
renders explicit failure receipts. All production workflows and tests use this
entry point.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Mapping

import pyarrow as pa

HERE = Path(__file__).resolve().parent
BASE_PATH = HERE / "cloudflare_numeric_compiler.py"
DOMAIN_PATH = HERE.parents[1] / "huggingface" / "numeric-baseline-library" / "china-finance-business-domain-requirements.json"
SPEC = importlib.util.spec_from_file_location("cloudflare_numeric_compiler_base", BASE_PATH)
assert SPEC and SPEC.loader
BASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BASE)


def response_schema(profile: Mapping[str, Any]) -> dict[str, Any]:
    kind = str(profile["kind"])
    maximum = int(profile["max_records"])
    properties: dict[str, Any] = {
        "publication_date": {
            "type": "string",
            "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
        }
    }
    if kind == "metric":
        properties.update(
            {
                "entity_key": {"type": "string", "minLength": 2, "maxLength": 200},
                "geography_id": {"type": "integer", "minimum": 0, "maximum": 999999},
                "records": {
                    "type": "array",
                    "maxItems": maximum,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "metric_code",
                            "period_start",
                            "period_end",
                            "value",
                            "lower_bound",
                            "upper_bound",
                            "unit_code",
                            "confidence",
                        ],
                        "properties": {
                            "metric_code": {"type": "string", "enum": list(profile["allowed_codes"])},
                            "period_start": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                            "period_end": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                            "value": {"type": "number"},
                            "lower_bound": {"type": "number"},
                            "upper_bound": {"type": "number"},
                            "unit_code": {"type": "string", "enum": list(profile["allowed_units"])},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        },
                    },
                },
            }
        )
        required = ["publication_date", "entity_key", "geography_id", "records"]
    elif kind == "event":
        properties.update(
            {
                "entity_key": {"type": "string", "minLength": 2, "maxLength": 200},
                "geography_id": {"type": "integer", "minimum": 0, "maximum": 999999},
                "events": {
                    "type": "array",
                    "maxItems": maximum,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "event_code",
                            "start_date",
                            "end_date",
                            "magnitude",
                            "direction_code",
                            "probability",
                            "status_code",
                            "confidence",
                        ],
                        "properties": {
                            "event_code": {"type": "string", "enum": list(profile["allowed_codes"])},
                            "start_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                            "end_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                            "magnitude": {"type": "number"},
                            "direction_code": {"type": "integer", "enum": [-1, 0, 1]},
                            "probability": {"type": "number", "minimum": 0, "maximum": 1},
                            "status_code": {"type": "integer", "minimum": 0, "maximum": 65535},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        },
                    },
                },
            }
        )
        required = ["publication_date", "entity_key", "geography_id", "events"]
    elif kind == "link":
        properties["links"] = {
            "type": "array",
            "maxItems": maximum,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "source_entity_key",
                    "target_entity_key",
                    "relation_code",
                    "weight",
                    "start_date",
                    "end_date",
                    "confidence",
                ],
                "properties": {
                    "source_entity_key": {"type": "string", "minLength": 2, "maxLength": 200},
                    "target_entity_key": {"type": "string", "minLength": 2, "maxLength": 200},
                    "relation_code": {"type": "string", "enum": list(profile["allowed_codes"])},
                    "weight": {"type": "number"},
                    "start_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                    "end_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                },
            },
        }
        required = ["publication_date", "links"]
    else:
        raise BASE.NumericCompilerError(f"unsupported profile kind: {kind}")
    return {
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": properties,
    }


def table_from_rows(table_id: str, rows: list[dict[str, Any]]) -> pa.Table:
    columns = BASE._columns_for_table(table_id)
    schema = pa.schema([pa.field(name, dtype, nullable=False) for name, dtype in columns])
    arrays = [
        pa.array([row[field.name] for row in rows], type=field.type)
        for field in schema
    ]
    return pa.Table.from_arrays(arrays, schema=schema)


def validate_domains() -> dict[str, Any]:
    payload = json.loads(DOMAIN_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "china-finance-business-domain-requirements-v1":
        raise BASE.NumericCompilerError("unsupported China finance/business domain requirements")
    if payload.get("status") != "production-control" or payload.get("domain_count") != 12:
        raise BASE.NumericCompilerError("China finance/business domain requirements are incomplete")
    policy = payload.get("storage_policy") or {}
    expected = {
        "huggingface_payload_numeric_only": True,
        "natural_language_payload_allowed": False,
        "control_metadata_location": "github",
        "selection_and_relay_owner": "gpts-usage-center",
        "compute_runtime_network_allowed": False,
        "direct_center_connection_allowed": False,
        "automatic_trading_allowed": False,
        "personalized_investment_advice_allowed": False,
    }
    if any(policy.get(key) != value for key, value in expected.items()):
        raise BASE.NumericCompilerError("China finance/business storage policy mismatch")
    domains = payload.get("domains")
    if not isinstance(domains, list) or len(domains) != 12:
        raise BASE.NumericCompilerError("exactly 12 China finance/business domains are required")
    ids = [str(row.get("id") or "") for row in domains if isinstance(row, Mapping)]
    if len(ids) != 12 or len(set(ids)) != 12 or any(not value.startswith("cn-") for value in ids):
        raise BASE.NumericCompilerError("China finance/business domain IDs are invalid")
    if any(not row.get("variable_groups") or not row.get("default_tables") for row in domains):
        raise BASE.NumericCompilerError("China finance/business domain mappings are incomplete")
    return {"domain_count": 12, "domain_ids": ids}


def validate_configuration() -> dict[str, Any]:
    receipt = dict(BASE.validate_configuration())
    domains = validate_domains()
    receipt.update(domains)
    return receipt


def render(output_dir: Path) -> str:
    failure_path = output_dir / "failure-receipt.json"
    execution_path = output_dir / "execution-receipt.json"
    if failure_path.exists() and not execution_path.exists():
        receipt = json.loads(failure_path.read_text(encoding="utf-8"))
        return (
            f"Cloudflare numeric compiler result: `{receipt['status']}`\n\n"
            f"- Error type: `{receipt['error_type']}`\n"
            f"- Raw page text persisted: `{str(receipt['raw_page_text_persisted']).lower()}`\n"
            f"- Raw AI response persisted: `{str(receipt['raw_ai_response_persisted']).lower()}`\n"
            f"- Secret values exposed: `{str(receipt['secret_values_exposed']).lower()}`\n"
        )
    return BASE.render(output_dir)


BASE.response_schema = response_schema
BASE._table_from_rows = table_from_rows
BASE.validate_configuration = validate_configuration
BASE.render = render


def __getattr__(name: str) -> Any:
    return getattr(BASE, name)


def main() -> int:
    return BASE.main()


if __name__ == "__main__":
    raise SystemExit(main())
