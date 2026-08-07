#!/usr/bin/env python3
"""Resilient Cloudflare semantic transform for verified PRC justice pages.

Attempt 1 lets Cloudflare Browser Rendering navigate the already PRIMARY_VERIFIED
public URL. If Browser Rendering rejects navigation with HTTP 422, attempt 2
fetches the same verified public URL once with a bounded ordinary HTTPS GET and
passes that in-memory HTML to Cloudflare /browser-rendering/json. The HTML is
never written to disk. A deliberately simple JSON Schema is used for Cloudflare;
strict repository schema validation is applied only after normalization.
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
from urllib.parse import urlsplit

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
MAX_CLOUDFLARE_RESPONSE_BYTES = 512 * 1024
MAX_HTML_BYTES = 512 * 1024


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
    result: list[dict[str, Any]] = []
    if not path.is_file():
        return result
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        row = json.loads(raw)
        if not isinstance(row, dict):
            raise TransformError(f"JSONL row {number} must be an object")
        result.append(row)
    return result


def _write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(_canonical(row) + "\n" for row in rows), encoding="utf-8")


def _capability_ids() -> list[str]:
    matrix = _load(CAPABILITY_MATRIX_PATH)
    rows = matrix.get("technology_domains") or []
    ids = sorted(str(row.get("capability_id") or "") for row in rows if isinstance(row, Mapping))
    if len(ids) != 19 or any(not item for item in ids):
        raise TransformError("expected exactly 19 registered public capability IDs")
    return ids


def _cloudflare_schema() -> dict[str, Any]:
    # Keep the Cloudflare-side schema intentionally simple. Strict max lengths,
    # nullable unions and all safety fields are enforced locally after extraction.
    return {
        "type": "object",
        "properties": {
            "subject_type": {"type": "string", "enum": ["capability","technology","practice_standard","doctrine","enforcement","institutional_capacity"]},
            "capability_ids": {"type": "array", "items": {"type": "string", "enum": _capability_ids()}},
            "technology_terms": {"type": "array", "items": {"type": "string"}},
            "legal_domains": {"type": "array", "items": {"type": "string"}},
            "procedural_stage": {"type": "string"},
            "lifecycle_stage": {"type": "string", "enum": ["","CONCEPT","RESEARCH_SIGNAL","TRAINING_SIGNAL","STANDARDIZING","STANDARDIZED","INVESTING","DEPLOYING","FIRST_PRACTICE","REPEATED_PRACTICE","CROSS_REGION_OBSERVED","CROSS_INSTITUTION_OBSERVED","MATURE_PUBLIC_PRACTICE","CONTESTED","STALE_REVIEW_REQUIRED"]},
            "trend_direction": {"type": "string", "enum": ["NEW","RISING","STABLE","DECLINING","CONTESTED","INSUFFICIENT_DATA"]},
            "summary": {"type": "string"},
            "practice_standard_summary": {"type": "string"},
            "doctrine_or_enforcement_summary": {"type": "string"},
            "confidence": {"type": "string", "enum": ["LOW","MEDIUM","MEDIUM_HIGH","HIGH"]}
        },
        "required": [
            "subject_type","capability_ids","technology_terms","legal_domains",
            "procedural_stage","lifecycle_stage","trend_direction","summary",
            "practice_standard_summary","doctrine_or_enforcement_summary","confidence"
        ]
    }


def validate_configuration() -> dict[str, Any]:
    final_schema = _load(DERIVED_SCHEMA_PATH)
    Draft202012Validator.check_schema(final_schema)
    Draft202012Validator.check_schema(_cloudflare_schema())
    if final_schema.get("$id") != "prc-justice-derived-intelligence-record-v1":
        raise TransformError("unexpected derived record schema")
    forbidden = {"source_url","url","raw_text","raw_source_text","raw_model_response","quote","full_text"}
    if forbidden & set((final_schema.get("properties") or {}).keys()):
        raise TransformError("derived record schema exposes raw-source fields")
    return {
        "status": "PRC_JUSTICE_CLOUDFLARE_TRANSFORM_V2_VALIDATED",
        "registered_capability_count": len(_capability_ids()),
        "max_pages_per_run": MAX_PAGES,
        "cloudflare_schema_style": "simple-json-schema-plus-local-strict-validation",
        "url_first_then_in_memory_html_fallback": True,
        "raw_html_persisted": False,
        "raw_source_text_persisted": False,
        "raw_source_url_in_hf_export": False,
        "raw_model_response_persisted": False,
        "direct_huggingface_write_allowed": False,
        "model_calls": 0,
        "network_used": False,
    }


def _eligible(row: Mapping[str, Any]) -> bool:
    if row.get("review_status") not in {"PRIMARY_VERIFIED", "CROSS_VERIFIED"}:
        return False
    source = row.get("source") or {}
    safety = row.get("safety") or {}
    url = str(source.get("url") or "")
    parsed = urlsplit(url)
    return bool(
        isinstance(source, Mapping)
        and source.get("primary") is True
        and parsed.scheme == "https"
        and parsed.hostname
        and parsed.hostname == str(source.get("host") or "").casefold()
        and safety.get("public_or_authorized") is True
        and safety.get("contains_secret_operational_detail") is False
        and safety.get("contains_targeting_or_evasion_detail") is False
        and safety.get("contains_personal_targeting") is False
    )


def _secrets() -> tuple[str, str]:
    account = str(os.getenv(ACCOUNT_ENV) or "").strip()
    token = str(os.getenv(TOKEN_ENV) or "").strip()
    if not re.fullmatch(r"[0-9a-fA-F]{32}", account):
        raise TransformError("CLOUDFLARE_ACCOUNT_ID must be a 32-character hexadecimal account ID")
    if not token:
        raise TransformError("CLOUDFLARE_API_TOKEN is not configured")
    return account, token


def _prompt(event: Mapping[str, Any]) -> str:
    return (
        "你是中国大陆司法公开情报结构化分析器。只依据输入的公开页面，把信息翻译成简洁、标准化、可计算的中文情报记录。"
        "不要逐字复制长段正文；不要输出原始URL、个人画像、秘密侦查设备或参数、目标选择、监控盲点、规避侦查或反取证内容。"
        "只识别公开高层能力、技术、标准、采购、培训、科研、案件、司法结果、法律理论或执行尺度。"
        "capability_ids只能从Schema枚举选择；证据不足时返回空数组。"
        "单一课程、采购或单案不得表述成全国普遍部署。没有明确时间比较时trend_direction使用INSUFFICIENT_DATA或STABLE。"
        "procedural_stage、practice_standard_summary、doctrine_or_enforcement_summary无法确认时返回空字符串。"
        "summary必须抽象归纳，不得大段照抄页面。"
        f" 已知元数据：institution_type={event.get('institution_type')}; region={event.get('region')}; signal_type={event.get('signal_type')}."
    )


def _safe_cloudflare_error(response: requests.Response) -> str:
    try:
        value = response.json()
    except ValueError:
        return f"HTTP_{response.status_code}"
    messages: list[str] = []
    if isinstance(value, Mapping):
        for row in value.get("errors") or []:
            if isinstance(row, Mapping):
                code = str(row.get("code") or "")[:40]
                message = re.sub(r"https?://\S+", "<url>", str(row.get("message") or ""))[:240]
                messages.append(f"{code}:{message}")
    return (f"HTTP_{response.status_code}:" + "|".join(messages))[:600]


def _post_cloudflare(payload: Mapping[str, Any]) -> tuple[dict[str, Any] | None, int, str | None]:
    account, token = _secrets()
    response = requests.post(
        f"{API_BASE}/accounts/{account}/browser-rendering/json",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "prc-justice-intelligence-transform-v2/1",
        },
        json=dict(payload),
        timeout=TIMEOUT_SECONDS,
        allow_redirects=False,
    )
    raw = bytes(response.content or b"")
    if len(raw) > MAX_CLOUDFLARE_RESPONSE_BYTES:
        raise TransformError("Cloudflare response exceeds bounded size")
    if response.status_code == 429:
        raise TransformError("CLOUDFLARE_QUOTA_OR_RATE_LIMIT")
    if not response.ok:
        return None, response.status_code, _safe_cloudflare_error(response)
    try:
        envelope = response.json()
    except ValueError as exc:
        raise TransformError("Cloudflare response is not JSON") from exc
    if not isinstance(envelope, Mapping) or envelope.get("success") is not True or not isinstance(envelope.get("result"), Mapping):
        raise TransformError("Cloudflare extraction did not return a valid result")
    result = dict(envelope["result"])
    errors = sorted(Draft202012Validator(_cloudflare_schema()).iter_errors(result), key=lambda item: list(item.path))
    if errors:
        raise TransformError("Cloudflare result failed simple schema: " + "; ".join(item.message for item in errors[:5]))
    return result, response.status_code, None


def _fetch_verified_html(url: str) -> str:
    response = requests.get(
        url,
        headers={"Accept":"text/html,application/xhtml+xml","User-Agent":"prc-justice-primary-fallback/1"},
        timeout=30,
        allow_redirects=False,
        stream=True,
    )
    if not response.ok:
        raise TransformError(f"verified HTML fallback returned HTTP {response.status_code}")
    content_type = str(response.headers.get("content-type") or "").casefold()
    if "html" not in content_type:
        raise TransformError("verified HTML fallback did not return HTML")
    chunks: list[bytes] = []
    size = 0
    for chunk in response.iter_content(chunk_size=65536):
        if not chunk:
            continue
        size += len(chunk)
        if size > MAX_HTML_BYTES:
            raise TransformError("verified HTML fallback exceeds bounded size")
        chunks.append(chunk)
    encoding = response.encoding or "utf-8"
    return b"".join(chunks).decode(encoding, errors="replace")


def _cloudflare_extract(event: Mapping[str, Any]) -> tuple[dict[str, Any], str, int]:
    url = str((event.get("source") or {}).get("url") or "")
    common = {"prompt": _prompt(event), "response_format": {"type":"json_schema","json_schema":_cloudflare_schema()}}
    result, status, error = _post_cloudflare({"url":url, **common})
    if result is not None:
        return result, "cloudflare_url", 1
    # HTTP 422 can represent Browser Rendering navigation/body validation failure.
    # Use a single bounded ordinary GET of the already verified public URL, keep
    # the HTML only in memory, then ask the same Cloudflare AI endpoint to extract.
    if status != 422:
        raise TransformError(error or f"Cloudflare Browser Rendering returned HTTP {status}")
    html = _fetch_verified_html(url)
    result, status2, error2 = _post_cloudflare({"html":html, **common})
    html = ""  # discard reference before returning; never persist it
    if result is None:
        raise TransformError(error2 or f"Cloudflare HTML extraction returned HTTP {status2}")
    return result, "direct_https_to_cloudflare_html", 2


def _bounded_string(value: Any, maximum: int, *, required: bool = False) -> str | None:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if required and not text:
        raise TransformError("required model-derived summary is empty")
    if len(text) > maximum:
        text = text[:maximum].rstrip()
    return text or None


def _evidence_ref(event: Mapping[str, Any]) -> str:
    source = event.get("source") or {}
    return "evref:" + _sha(str(event.get("event_id") or "") + "|" + str(source.get("content_fingerprint") or ""))


def _record(event: Mapping[str, Any], extracted: Mapping[str, Any], as_of: str) -> dict[str, Any]:
    evref = _evidence_ref(event)
    capability_ids = [str(item) for item in extracted.get("capability_ids") or []][:20]
    if any(item not in _capability_ids() for item in capability_ids):
        raise TransformError("Cloudflare returned unregistered capability_id")
    technology_terms = list(dict.fromkeys(_bounded_string(item, 160, required=True) for item in extracted.get("technology_terms") or []))[:30]
    legal_domains = list(dict.fromkeys(_bounded_string(item, 120, required=True) for item in extracted.get("legal_domains") or []))[:20]
    lifecycle = str(extracted.get("lifecycle_stage") or "").strip() or None
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
        "capability_ids": capability_ids,
        "technology_terms": technology_terms,
        "legal_domains": legal_domains,
        "procedural_stage": _bounded_string(extracted.get("procedural_stage"), 160),
        "lifecycle_stage": lifecycle,
        "trend_direction": extracted["trend_direction"],
        "summary": _bounded_string(extracted.get("summary"), 1800, required=True),
        "practice_standard_summary": _bounded_string(extracted.get("practice_standard_summary"), 1800),
        "doctrine_or_enforcement_summary": _bounded_string(extracted.get("doctrine_or_enforcement_summary"), 1800),
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
        raise TransformError("derived record failed strict schema: " + "; ".join(item.message for item in errors[:5]))
    return record


def _link_records(rows: list[dict[str, Any]]) -> None:
    seen_edges: set[tuple[str, str, str]] = set()
    for left_index in range(len(rows)):
        for right_index in range(left_index + 1, len(rows)):
            left, right = rows[left_index], rows[right_index]
            matches = [
                ("SAME_CAPABILITY", bool(set(left.get("capability_ids") or []) & set(right.get("capability_ids") or []))),
                ("SAME_INSTITUTION", bool(left.get("institution_name") and left.get("institution_name") == right.get("institution_name"))),
                ("SAME_REGION", bool(left.get("region") and left.get("region") == right.get("region"))),
                ("SAME_DOMAIN", bool(set(left.get("legal_domains") or []) & set(right.get("legal_domains") or []))),
            ]
            for relation, matched in matches:
                if not matched:
                    continue
                key = (left["record_id"], right["record_id"], relation)
                if key in seen_edges:
                    continue
                seen_edges.add(key)
                if len(left["relationships"]) < 50:
                    left["relationships"].append({"relation":relation,"target_ref":right["record_id"],"strength":"CONTEXTUAL_ASSOCIATION"})
                if len(right["relationships"]) < 50:
                    right["relationships"].append({"relation":relation,"target_ref":left["record_id"],"strength":"CONTEXTUAL_ASSOCIATION"})


def transform(input_path: Path, output_dir: Path, max_pages: int) -> dict[str, Any]:
    validate_configuration()
    if not 1 <= max_pages <= MAX_PAGES:
        raise TransformError(f"max_pages must be 1..{MAX_PAGES}")
    events = [row for row in _read_jsonl(input_path) if _eligible(row)]
    selected: list[dict[str, Any]] = []
    fingerprints: set[str] = set()
    for row in events:
        fingerprint = str((row.get("source") or {}).get("content_fingerprint") or "")
        if not fingerprint or fingerprint in fingerprints:
            continue
        fingerprints.add(fingerprint)
        selected.append(row)
        if len(selected) >= max_pages:
            break

    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    successful_model_calls = 0
    cloudflare_requests = 0
    fallback_count = 0
    quota_exhausted = False
    as_of = datetime.now(timezone.utc).date().isoformat()
    for event in selected:
        try:
            extracted, route, request_count = _cloudflare_extract(event)
            cloudflare_requests += request_count
            successful_model_calls += 1
            fallback_count += int(route != "cloudflare_url")
            records.append(_record(event, extracted, as_of))
        except TransformError as exc:
            if str(exc) == "CLOUDFLARE_QUOTA_OR_RATE_LIMIT":
                quota_exhausted = True
                break
            failures.append({"event_id":str(event.get("event_id") or ""),"error":str(exc)[:600]})

    _link_records(records)
    validator = Draft202012Validator(_load(DERIVED_SCHEMA_PATH))
    for row in records:
        if list(validator.iter_errors(row)):
            raise TransformError("linked record failed strict schema validation")
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
        "cloudflare_requests": cloudflare_requests,
        "model_calls": successful_model_calls,
        "in_memory_html_fallback_count": fallback_count,
        "network_used": bool(selected),
        "raw_html_persisted": False,
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
