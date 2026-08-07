#!/usr/bin/env python3
"""Transform PRIMARY_VERIFIED public justice signals into sanitized derived intelligence.

Cloudflare Browser Rendering /json performs a bounded schema-constrained semantic
extraction directly from the verified public source URL. Raw page text and the raw
model response are never persisted. Output contains only normalized derived fields
plus opaque evidence references that can be resolved inside Evidence Center.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import requests
from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
DERIVED_SCHEMA_PATH = HERE / "prc-justice-derived-intelligence-record.schema.json"
CAPABILITY_MATRIX_PATH = HERE / "investigative-technology-intelligence-matrix.json"
API_BASE = "https://api.cloudflare.com/client/v4"
TOKEN_ENV = "CLOUDFLARE_API_TOKEN"
ACCOUNT_ENV = "CLOUDFLARE_ACCOUNT_ID"
MAX_PAGES = 6
TIMEOUT_SECONDS = 90
MAX_RESPONSE_BYTES = 512 * 1024


class TransformError(RuntimeError):
    pass


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        return rows
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise TransformError(f"JSONL row {line_number} must be an object")
        rows.append(value)
    return rows


def _write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(_canonical(row) + "\n" for row in rows), encoding="utf-8")


def _capability_ids() -> list[str]:
    matrix = _load(CAPABILITY_MATRIX_PATH)
    rows = matrix.get("technology_domains") or []
    ids = sorted(str(row.get("capability_id") or "") for row in rows if isinstance(row, Mapping))
    if len(ids) != 19 or any(not item for item in ids):
        raise TransformError("expected exactly 19 registered public high-level capability IDs")
    return ids


def _extraction_schema() -> dict[str, Any]:
    capabilities = _capability_ids()
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "subject_type", "capability_ids", "technology_terms", "legal_domains",
            "procedural_stage", "lifecycle_stage", "trend_direction", "summary",
            "practice_standard_summary", "doctrine_or_enforcement_summary", "confidence"
        ],
        "properties": {
            "subject_type": {"enum": ["capability","technology","practice_standard","doctrine","enforcement","institutional_capacity"]},
            "capability_ids": {"type":"array","maxItems":10,"uniqueItems":True,"items":{"enum":capabilities}},
            "technology_terms": {"type":"array","maxItems":20,"uniqueItems":True,"items":{"type":"string","minLength":1,"maxLength":120}},
            "legal_domains": {"type":"array","maxItems":12,"uniqueItems":True,"items":{"type":"string","minLength":1,"maxLength":100}},
            "procedural_stage": {"type":["string","null"],"maxLength":120},
            "lifecycle_stage": {"type":["string","null"],"enum":[None,"CONCEPT","RESEARCH_SIGNAL","TRAINING_SIGNAL","STANDARDIZING","STANDARDIZED","INVESTING","DEPLOYING","FIRST_PRACTICE","REPEATED_PRACTICE","CROSS_REGION_OBSERVED","CROSS_INSTITUTION_OBSERVED","MATURE_PUBLIC_PRACTICE","CONTESTED","STALE_REVIEW_REQUIRED"]},
            "trend_direction": {"enum":["NEW","RISING","STABLE","DECLINING","CONTESTED","INSUFFICIENT_DATA"]},
            "summary": {"type":"string","minLength":1,"maxLength":1600},
            "practice_standard_summary": {"type":["string","null"],"maxLength":1600},
            "doctrine_or_enforcement_summary": {"type":["string","null"],"maxLength":1600},
            "confidence": {"enum":["LOW","MEDIUM","MEDIUM_HIGH","HIGH"]}
        }
    }


def validate_configuration() -> dict[str, Any]:
    schema = _load(DERIVED_SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator.check_schema(_extraction_schema())
    if schema.get("$id") != "prc-justice-derived-intelligence-record-v1":
        raise TransformError("unexpected derived intelligence schema")
    forbidden = {"source_url", "raw_text", "raw_source_text", "raw_model_response", "quote", "full_text"}
    observed = set((schema.get("properties") or {}).keys())
    if forbidden & observed:
        raise TransformError("derived HF record schema contains forbidden raw-source fields")
    return {
        "status": "PRC_JUSTICE_CLOUDFLARE_TRANSFORM_VALIDATED",
        "registered_capability_count": len(_capability_ids()),
        "max_pages_per_run": MAX_PAGES,
        "raw_source_text_persisted": False,
        "raw_source_url_in_hf_export": False,
        "raw_model_response_persisted": False,
        "personal_targeting_allowed": False,
        "secret_operational_detail_allowed": False,
        "evasion_or_anti_forensics_allowed": False,
        "direct_huggingface_write_allowed": False,
        "storage_gateway": "a15280020511/decision-system-governance",
        "network_used": False,
        "model_calls": 0,
    }


def _eligible(row: Mapping[str, Any]) -> bool:
    if row.get("review_status") not in {"PRIMARY_VERIFIED", "CROSS_VERIFIED"}:
        return False
    source = row.get("source") or {}
    safety = row.get("safety") or {}
    return bool(
        isinstance(source, Mapping)
        and source.get("primary") is True
        and str(source.get("url") or "").startswith("https://")
        and safety.get("public_or_authorized") is True
        and safety.get("contains_secret_operational_detail") is False
        and safety.get("contains_targeting_or_evasion_detail") is False
        and safety.get("contains_personal_targeting") is False
    )


def _cloudflare_extract(url: str, event: Mapping[str, Any]) -> dict[str, Any]:
    account = str(os.getenv(ACCOUNT_ENV) or "").strip()
    token = str(os.getenv(TOKEN_ENV) or "").strip()
    if not re.fullmatch(r"[0-9a-fA-F]{32}", account):
        raise TransformError("CLOUDFLARE_ACCOUNT_ID must be a 32-character hexadecimal account ID")
    if not token:
        raise TransformError("CLOUDFLARE_API_TOKEN is not configured")
    prompt = (
        "你是中国大陆司法公开情报结构化分析器。只依据当前公开页面，把内容翻译成简洁、标准化、可计算的中文情报记录。"
        "不得逐字复制长段正文，不得输出原始URL，不得输出个人画像、秘密侦查设备/参数、目标选择、监控盲点、规避侦查或反取证内容。"
        "只识别公开高层能力类别、技术/标准/采购/培训/科研/案件/司法结果、法律理论或执行尺度。"
        "capability_ids只能从Schema枚举中选择；证据不足时留空。单一课程、采购或单案不得表述成全国普遍部署。"
        "trend_direction只有在页面本身提供比较或变化信息时才可用NEW/RISING/DECLINING，否则用STABLE或INSUFFICIENT_DATA。"
        "summary必须是抽象归纳，不是原文摘录。"
        f" 已知元数据：institution_type={event.get('institution_type')}; region={event.get('region')}; signal_type={event.get('signal_type')}."
    )
    body = {
        "url": url,
        "prompt": prompt,
        "response_format": {"type":"json_schema","json_schema":_extraction_schema()},
    }
    response = requests.post(
        f"{API_BASE}/accounts/{account}/browser-rendering/json",
        headers={"Authorization":f"Bearer {token}","Content-Type":"application/json","Accept":"application/json","User-Agent":"prc-justice-intelligence-transform/1"},
        json=body,
        timeout=TIMEOUT_SECONDS,
        allow_redirects=False,
    )
    raw = bytes(response.content or b"")
    if len(raw) > MAX_RESPONSE_BYTES:
        raise TransformError("Cloudflare response exceeds bounded size")
    if response.status_code == 429:
        raise TransformError("CLOUDFLARE_QUOTA_OR_RATE_LIMIT")
    if not response.ok:
        raise TransformError(f"Cloudflare Browser Rendering returned HTTP {response.status_code}")
    try:
        envelope = response.json()
    except ValueError as exc:
        raise TransformError("Cloudflare response is not JSON") from exc
    if not isinstance(envelope, Mapping) or envelope.get("success") is not True or not isinstance(envelope.get("result"), Mapping):
        raise TransformError("Cloudflare extraction did not return a valid result")
    result = dict(envelope["result"])
    errors = sorted(Draft202012Validator(_extraction_schema()).iter_errors(result), key=lambda item: list(item.path))
    if errors:
        raise TransformError("Cloudflare result failed fixed schema: " + "; ".join(item.message for item in errors[:5]))
    return result


def _evidence_ref(event: Mapping[str, Any]) -> str:
    source = event.get("source") or {}
    fingerprint = str(source.get("content_fingerprint") or "")
    event_id = str(event.get("event_id") or "")
    return "evref:" + _sha(event_id + "|" + fingerprint)


def _record(event: Mapping[str, Any], extracted: Mapping[str, Any], as_of: str) -> dict[str, Any]:
    evref = _evidence_ref(event)
    record = {
        "record_id": "jintel:" + _sha(evref + "|" + _canonical(extracted))[:40],
        "as_of_date": as_of,
        "event_date": event.get("event_date"),
        "institution_type": event.get("institution_type"),
        "institution_name": event.get("institution_name"),
        "region": event.get("region"),
        "industry_or_case_domain": event.get("case_type") or ((event.get("legal_domains") or [None])[0]),
        "signal_type": event.get("signal_type"),
        "subject_type": extracted["subject_type"],
        "capability_ids": list(extracted["capability_ids"]),
        "technology_terms": list(extracted["technology_terms"]),
        "legal_domains": list(extracted["legal_domains"]),
        "procedural_stage": extracted["procedural_stage"],
        "lifecycle_stage": extracted["lifecycle_stage"],
        "trend_direction": extracted["trend_direction"],
        "summary": extracted["summary"],
        "practice_standard_summary": extracted["practice_standard_summary"],
        "doctrine_or_enforcement_summary": extracted["doctrine_or_enforcement_summary"],
        "relationships": [],
        "confidence": extracted["confidence"],
        "evidence_ref_ids": [evref],
        "model_transform": {"provider":"cloudflare","method":"browser-rendering-json","schema_version":"prc-justice-derived-intelligence-record-v1"},
        "safety": {
            "public_or_authorized": True,
            "raw_source_text_stored": False,
            "raw_source_url_stored": False,
            "raw_model_response_stored": False,
            "personal_targeting": False,
            "secret_operational_detail": False,
            "evasion_or_anti_forensics": False,
        },
    }
    errors = sorted(Draft202012Validator(_load(DERIVED_SCHEMA_PATH)).iter_errors(record), key=lambda item: list(item.path))
    if errors:
        raise TransformError("derived record failed schema: " + "; ".join(item.message for item in errors[:5]))
    return record


def _link_records(rows: list[dict[str, Any]]) -> None:
    for index, left in enumerate(rows):
        relations: list[dict[str, str]] = []
        for right in rows[index + 1:]:
            checks = [
                ("SAME_CAPABILITY", bool(set(left.get("capability_ids") or []) & set(right.get("capability_ids") or []))),
                ("SAME_INSTITUTION", bool(left.get("institution_name") and left.get("institution_name") == right.get("institution_name"))),
                ("SAME_REGION", bool(left.get("region") and left.get("region") == right.get("region"))),
                ("SAME_DOMAIN", bool(set(left.get("legal_domains") or []) & set(right.get("legal_domains") or []))),
            ]
            for relation, matched in checks:
                if matched:
                    relations.append({"relation":relation,"target_ref":right["record_id"],"strength":"CONTEXTUAL_ASSOCIATION"})
                    right.setdefault("relationships", []).append({"relation":relation,"target_ref":left["record_id"],"strength":"CONTEXTUAL_ASSOCIATION"})
        left["relationships"] = relations[:50]


def transform(input_path: Path, output_dir: Path, max_pages: int) -> dict[str, Any]:
    validate_configuration()
    if not 1 <= max_pages <= MAX_PAGES:
        raise TransformError(f"max_pages must be 1..{MAX_PAGES}")
    events = [row for row in _read_jsonl(input_path) if _eligible(row)]
    seen: set[str] = set()
    selected: list[dict[str, Any]] = []
    for row in events:
        fingerprint = str((row.get("source") or {}).get("content_fingerprint") or "")
        if not fingerprint or fingerprint in seen:
            continue
        seen.add(fingerprint)
        selected.append(row)
        if len(selected) >= max_pages:
            break

    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    model_calls = 0
    quota_exhausted = False
    as_of = datetime.now(timezone.utc).date().isoformat()
    for event in selected:
        url = str((event.get("source") or {}).get("url") or "")
        try:
            result = _cloudflare_extract(url, event)
            model_calls += 1
            records.append(_record(event, result, as_of))
        except TransformError as exc:
            if str(exc) == "CLOUDFLARE_QUOTA_OR_RATE_LIMIT":
                quota_exhausted = True
                break
            failures.append({"event_id":str(event.get("event_id") or ""),"error":str(exc)[:300]})
    _link_records(records)
    validator = Draft202012Validator(_load(DERIVED_SCHEMA_PATH))
    for row in records:
        errors = list(validator.iter_errors(row))
        if errors:
            raise TransformError("linked record failed schema validation")

    _write_jsonl(output_dir / "derived-intelligence.jsonl", records)
    export = {
        "schema_version": "governance-prc-justice-derived-export-v1",
        "producer_repository": "a15280020511/evidence-data-center",
        "producer_commit": str(os.getenv("GITHUB_SHA") or "local"),
        "source_run_id": str(os.getenv("GITHUB_RUN_ID") or "local"),
        "as_of_date": as_of,
        "record_count": len(records),
        "records": records,
        "raw_source_text_included": False,
        "raw_source_url_included": False,
        "raw_model_response_included": False,
        "personal_data_included": False,
        "secret_operational_details_included": False,
        "evasion_or_anti_forensics_included": False,
        "evidence_reference_resolution_owner": "a15280020511/evidence-data-center",
        "storage_gateway_owner": "a15280020511/decision-system-governance",
        "direct_huggingface_write": False,
    }
    _dump(output_dir / "governance-hf-justice-export.json", export)
    receipt = {
        "status": "PRC_JUSTICE_DERIVED_INTELLIGENCE_READY",
        "eligible_event_count": len(events),
        "selected_page_count": len(selected),
        "record_count": len(records),
        "failure_count": len(failures),
        "failures": failures,
        "quota_exhausted": quota_exhausted,
        "network_used": bool(selected),
        "model_calls": model_calls,
        "raw_source_text_persisted": False,
        "raw_source_url_in_hf_export": False,
        "raw_model_response_persisted": False,
        "direct_huggingface_write": False,
    }
    _dump(output_dir / "transform-receipt.json", receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-pages", type=int, default=MAX_PAGES)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        if args.validate_only:
            result = validate_configuration()
        else:
            if not args.input:
                raise TransformError("--input is required unless --validate-only is used")
            result = transform(Path(args.input), Path(args.output_dir), args.max_pages)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
