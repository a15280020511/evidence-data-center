#!/usr/bin/env python3
"""Validate China policy/intelligence domains, source priority and AI routing controls."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

HERE = Path(__file__).resolve().parent
LIBRARY = HERE.parents[1] / "huggingface" / "numeric-baseline-library"
DOMAIN_PATH = LIBRARY / "china-policy-intelligence-domain-requirements.json"
SOURCE_PATH = LIBRARY / "china-public-source-priority-registry.json"
ROUTING_PATH = HERE / "cloudflare-ai-routing-policy.json"


class PolicyControlError(RuntimeError):
    pass


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_domains() -> list[str]:
    payload = load(DOMAIN_PATH)
    if payload.get("schema_version") != "china-policy-intelligence-domain-requirements-v1":
        raise PolicyControlError("unsupported China policy/intelligence domain registry")
    if payload.get("status") != "production-control" or payload.get("domain_count") != 24:
        raise PolicyControlError("China policy/intelligence domain registry is incomplete")
    policy = payload.get("storage_policy") or {}
    expected = {
        "huggingface_payload_numeric_only": True,
        "natural_language_payload_allowed": False,
        "control_metadata_location": "github",
        "selection_and_relay_owner": "gpts-usage-center",
        "compute_runtime_network_allowed": False,
        "direct_center_connection_allowed": False,
        "public_sources_only": True,
        "personal_data_allowed": False,
        "restricted_nonpublic_data_allowed": False,
        "automatic_policy_judgment_allowed": False,
    }
    if any(policy.get(key) != value for key, value in expected.items()):
        raise PolicyControlError("China policy/intelligence storage policy mismatch")
    domains = payload.get("domains")
    if not isinstance(domains, list) or len(domains) != 24:
        raise PolicyControlError("exactly 24 China policy/intelligence domains are required")
    ids: list[str] = []
    for row in domains:
        if not isinstance(row, Mapping):
            raise PolicyControlError("domain row must be an object")
        domain_id = str(row.get("id") or "")
        groups = row.get("variable_groups")
        tables = row.get("default_tables")
        if not domain_id.startswith("cn-") or domain_id in ids:
            raise PolicyControlError(f"invalid or duplicate domain ID: {domain_id!r}")
        if not isinstance(groups, list) or len(groups) < 8 or len(groups) != len(set(groups)):
            raise PolicyControlError(f"domain variable groups are incomplete: {domain_id}")
        if not isinstance(tables, list) or "observations" not in tables or "benchmark_outcomes" not in tables:
            raise PolicyControlError(f"domain table mapping is incomplete: {domain_id}")
        ids.append(domain_id)
    return ids


def validate_sources() -> list[int]:
    payload = load(SOURCE_PATH)
    if payload.get("schema_version") != "china-public-source-priority-registry-v1":
        raise PolicyControlError("unsupported China public source registry")
    if payload.get("status") != "production-control":
        raise PolicyControlError("China public source registry is not production-control")
    if payload.get("storage_location") != "github-only" or payload.get("huggingface_upload_allowed") is not False:
        raise PolicyControlError("source controls must remain GitHub-only")
    rows = payload.get("source_classes")
    if not isinstance(rows, list) or len(rows) != 24:
        raise PolicyControlError("exactly 24 China source classes are required")
    ids: list[int] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise PolicyControlError("source class row must be an object")
        source_id = int(row.get("source_class_id") or 0)
        weight = float(row.get("default_quality_weight") or 0)
        if source_id < 1000 or source_id in ids:
            raise PolicyControlError(f"invalid or duplicate source class ID: {source_id}")
        if row.get("authority_tier") not in {"A", "B", "C", "D"} or not 0 < weight <= 1:
            raise PolicyControlError(f"invalid source authority controls: {source_id}")
        if row.get("raw_content_persistence_allowed") is not False:
            raise PolicyControlError(f"raw source persistence must remain forbidden: {source_id}")
        if row.get("numeric_baseline_ingestion_allowed") is not True:
            raise PolicyControlError(f"numeric ingestion must remain explicit: {source_id}")
        ids.append(source_id)
    quality = payload.get("quality_rules") or {}
    if quality.get("tier_c_requires_independent_confirmation") is not True:
        raise PolicyControlError("tier C sources must require independent confirmation")
    if quality.get("tier_d_only_for_attention_or_diffusion_aggregates") is not True:
        raise PolicyControlError("tier D sources must remain aggregate-only")
    if quality.get("personal_data_allowed") is not False or quality.get("restricted_nonpublic_data_allowed") is not False:
        raise PolicyControlError("personal or restricted non-public data is forbidden")
    return ids


def validate_routing() -> dict[str, Any]:
    payload = load(ROUTING_PATH)
    if payload.get("schema_version") != "cloudflare-ai-numeric-routing-policy-v1":
        raise PolicyControlError("unsupported Cloudflare AI routing policy")
    if payload.get("status") != "production-control" or payload.get("default_strategy") != "deterministic_first":
        raise PolicyControlError("Cloudflare AI routing must remain deterministic-first")
    tiers = payload.get("tiers")
    if not isinstance(tiers, list) or [row.get("tier_id") for row in tiers] != [0, 1, 2, 3]:
        raise PolicyControlError("AI routing tiers are incomplete")
    external = payload.get("external_model_policy") or {}
    if external.get("enabled_by_default") is not False:
        raise PolicyControlError("external AI model must remain disabled by default")
    if external.get("automatic_paid_fallback_allowed") is not False:
        raise PolicyControlError("automatic paid fallback is forbidden")
    if external.get("automatic_provider_switch_allowed") is not False:
        raise PolicyControlError("automatic provider switching is forbidden")
    if external.get("raw_page_persistence_allowed") is not False or external.get("raw_model_response_persistence_allowed") is not False:
        raise PolicyControlError("raw content persistence is forbidden")
    gate = payload.get("ingestion_gate") or {}
    expected_gate = {
        "model_output_is_intermediate_only": True,
        "github_deterministic_validation_required": True,
        "cross_source_validation_required_for_subjective_scores": True,
        "numeric_parquet_only": True,
        "huggingface_control_metadata_uploaded": False,
        "direct_center_connection_allowed": False,
    }
    if any(gate.get(key) != value for key, value in expected_gate.items()):
        raise PolicyControlError("numeric ingestion gate mismatch")
    return payload


def validate() -> dict[str, Any]:
    domains = validate_domains()
    sources = validate_sources()
    routing = validate_routing()
    return {
        "status": "CHINA_POLICY_INTELLIGENCE_CONTROLS_VALIDATED",
        "policy_domain_count": len(domains),
        "source_class_count": len(sources),
        "default_strategy": routing["default_strategy"],
        "external_model_enabled_by_default": routing["external_model_policy"]["enabled_by_default"],
        "automatic_paid_fallback_allowed": routing["external_model_policy"]["automatic_paid_fallback_allowed"],
        "numeric_hf_payload_only": routing["ingestion_gate"]["numeric_parquet_only"],
        "raw_content_persisted": False,
        "direct_center_connection_allowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    receipt = validate()
    (output_dir / "policy-control-validation-receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
