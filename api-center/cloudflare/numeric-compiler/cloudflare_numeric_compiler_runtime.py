#!/usr/bin/env python3
"""Hardened runtime entry for the Cloudflare China numeric compiler.

This module applies the validated response-schema and Arrow-row builders to the
base implementation, verifies the supplemental China domain control file, and
forces all numeric batches through the governance baseline gateway. Direct
private Hugging Face commits are rejected even if the legacy CLI flag is used.
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
ROLE_PATH = HERE.parents[1] / "huggingface" / "numeric-baseline-library" / "library-role.json"
SPEC = importlib.util.spec_from_file_location("cloudflare_numeric_compiler_base", BASE_PATH)
assert SPEC and SPEC.loader
BASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BASE)
ORIGINAL_VALIDATE_CONFIGURATION = BASE.validate_configuration
ORIGINAL_RENDER = BASE.render
ORIGINAL_EXECUTE = BASE.execute


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
    role = json.loads(ROLE_PATH.read_text(encoding="utf-8"))
    if role.get("schema_version") != "compute-center-baseline-library-role-v2":
        raise BASE.NumericCompilerError("baseline role contract is outdated")
    if role.get("storage_gateway_owner") != "a15280020511/decision-system-governance":
        raise BASE.NumericCompilerError("governance must own baseline storage")
    if role.get("intelligence_center_direct_dataset_write_allowed") is not False:
        raise BASE.NumericCompilerError("evidence center direct Dataset writes must be forbidden")
    return {
        "domain_count": 12,
        "domain_ids": ids,
        "storage_gateway_owner": role["storage_gateway_owner"],
        "direct_huggingface_write_allowed": False,
    }


def validate_configuration() -> dict[str, Any]:
    receipt = dict(ORIGINAL_VALIDATE_CONFIGURATION())
    receipt.update(validate_domains())
    receipt["governance_artifact_required"] = True
    receipt["direct_huggingface_write_allowed"] = False
    return receipt


def execute(
    ticket_path: Path,
    output_dir: Path,
    *,
    commit_to_hf: bool = False,
) -> dict[str, Any]:
    if commit_to_hf:
        raise BASE.NumericCompilerError(
            "direct Hugging Face commit is forbidden; export a governance baseline Artifact"
        )
    receipt = dict(ORIGINAL_EXECUTE(ticket_path, output_dir, commit_to_hf=False))
    receipt["storage"] = {
        "committed_to_hf": False,
        "governance_artifact_required": True,
        "storage_gateway_owner": "a15280020511/decision-system-governance",
    }
    receipt["gpts_relay_owner"] = "a15280020511/decision-system-governance"
    BASE._write_json(output_dir / "execution-receipt.json", receipt)
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
    text = ORIGINAL_RENDER(output_dir)
    if execution_path.exists():
        text += (
            "- Direct Hugging Face write allowed: `false`\n"
            "- Governance Artifact required: `true`\n"
            "- Storage gateway: `a15280020511/decision-system-governance`\n"
        )
    return text


BASE.response_schema = response_schema
BASE._table_from_rows = table_from_rows
BASE.validate_configuration = validate_configuration
BASE.execute = execute
BASE.render = render


def __getattr__(name: str) -> Any:
    return getattr(BASE, name)


def main() -> int:
    return BASE.main()


if __name__ == "__main__":
    raise SystemExit(main())
