#!/usr/bin/env python3
"""Scheduled, bounded, evidence-driven self-iteration for public PRC justice practice.

This module only absorbs high-level capability observations from primary public
or explicitly authorized sources. It does not collect secret operational
surveillance details, targeting playbooks, evasion techniques, credentials,
private endpoints, or non-public training materials.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import html
import ipaddress
import json
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable, Mapping

UA = "evidence-data-center-prc-justice-self-iteration/1"
BLOCKED_HOSTS = {
    "localhost",
    "metadata.google.internal",
    "metadata.azure.internal",
    "kubernetes.default",
    "instance-data",
}
DATE_RE = re.compile(r"(?<!\d)(20\d{2})[-年/.](0?[1-9]|1[0-2])[-月/.](0?[1-9]|[12]\d|3[01])日?")
SPACE_RE = re.compile(r"\s+")


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip_depth and data.strip():
            self.parts.append(data.strip())

    def text(self) -> str:
        return SPACE_RE.sub(" ", " ".join(self.parts)).strip()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_date(dt: datetime | None = None) -> str:
    return (dt or utc_now()).date().isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def save_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n")


def normalized_text(value: Any) -> str:
    return SPACE_RE.sub(" ", str(value or "")).strip()


def host_allowed(host: str, allowed_hosts: set[str]) -> bool:
    host = host.casefold().rstrip(".")
    return any(host == item or host.endswith("." + item) for item in allowed_hosts)


def safe_https_url(value: str, allowed_hosts: set[str], resolve: bool = False) -> str | None:
    try:
        parsed = urllib.parse.urlsplit(str(value or "").strip())
    except ValueError:
        return None
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        return None
    if parsed.username or parsed.password or parsed.port not in (None, 443):
        return None
    host = parsed.hostname.casefold().rstrip(".")
    if host in BLOCKED_HOSTS or host.endswith((".local", ".internal", ".localhost", ".svc", ".cluster.local")):
        return None
    if not host_allowed(host, allowed_hosts):
        return None
    if resolve:
        try:
            rows = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
            ips = {str(row[4][0]).split("%", 1)[0] for row in rows}
            if not ips or any(not ipaddress.ip_address(ip).is_global for ip in ips):
                return None
        except (socket.gaierror, ValueError):
            return None
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    return urllib.parse.urlunsplit(("https", host, path, parsed.query, ""))


def request_json(
    url: str,
    *,
    method: str = "GET",
    body: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    timeout: int = 20,
    max_bytes: int = 4_000_000,
) -> dict[str, Any]:
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    merged = {"Accept": "application/json", "User-Agent": UA, **dict(headers or {})}
    if data is not None:
        merged["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=merged, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(max_bytes + 1)
        if len(raw) > max_bytes:
            raise RuntimeError("response_too_large")
        return json.loads(raw.decode("utf-8", errors="strict"))


def decode_page(raw: bytes, content_type: str) -> str:
    match = re.search(r"charset=([A-Za-z0-9._-]+)", content_type or "", re.I)
    candidates = [match.group(1)] if match else []
    candidates += ["utf-8", "gb18030"]
    for encoding in candidates:
        try:
            return raw.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode("utf-8", errors="replace")


def fetch_primary_page(url: str, policy: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    allowed = {str(x).casefold() for x in policy["primary_outcome_hosts"]}
    safe = safe_https_url(url, allowed, resolve=True)
    if not safe:
        raise ValueError("unsafe_or_non_primary_url")
    timeout = int(policy["limits"]["request_timeout_seconds"])
    max_bytes = int(policy["limits"]["max_page_bytes"])
    opener = urllib.request.build_opener(NoRedirect)
    request = urllib.request.Request(
        safe,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.5",
            "User-Agent": UA,
            "Range": f"bytes=0-{max_bytes - 1}",
        },
        method="GET",
    )
    try:
        with opener.open(request, timeout=timeout) as response:
            raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                raise RuntimeError("primary_page_too_large")
            content_type = str(response.headers.get("Content-Type") or "")
            if "pdf" in content_type.casefold():
                raise RuntimeError("pdf_candidate_requires_separate_review")
            text = decode_page(raw, content_type)
            extractor = TextExtractor()
            extractor.feed(text)
            page_text = html.unescape(extractor.text())
            return page_text, {
                "status": int(getattr(response, "status", 200)),
                "content_type": content_type.split(";", 1)[0],
                "bytes_sampled": len(raw),
                "final_url": safe,
            }
    except urllib.error.HTTPError as exc:
        if 300 <= exc.code < 400:
            location = str(exc.headers.get("Location") or "")
            raise RuntimeError(f"redirect_not_followed:{exc.code}:{location[:160]}")
        raise RuntimeError(f"http_error:{exc.code}") from exc


def search_tavily(query: str, token: str, limit: int, timeout: int) -> list[dict[str, Any]]:
    payload = {
        "api_key": token,
        "query": query,
        "search_depth": "advanced",
        "max_results": limit,
        "include_answer": False,
        "include_raw_content": False,
    }
    data = request_json("https://api.tavily.com/search", method="POST", body=payload, timeout=timeout)
    rows = []
    for item in data.get("results") or []:
        if not isinstance(item, Mapping):
            continue
        rows.append(
            {
                "url": str(item.get("url") or ""),
                "title": normalized_text(item.get("title")),
                "snippet": normalized_text(item.get("content")),
                "published_date": normalized_text(item.get("published_date") or item.get("publishedDate")),
                "engine": "tavily",
                "query": query,
            }
        )
    return rows


def search_exa(query: str, token: str, limit: int, timeout: int, start_date: str) -> list[dict[str, Any]]:
    payload = {
        "query": query,
        "numResults": limit,
        "type": "auto",
        "startPublishedDate": start_date,
        "contents": {"text": {"maxCharacters": 1200}},
    }
    data = request_json(
        "https://api.exa.ai/search",
        method="POST",
        body=payload,
        headers={"x-api-key": token},
        timeout=timeout,
    )
    rows = []
    for item in data.get("results") or []:
        if not isinstance(item, Mapping):
            continue
        rows.append(
            {
                "url": str(item.get("url") or ""),
                "title": normalized_text(item.get("title")),
                "snippet": normalized_text(item.get("text") or item.get("summary")),
                "published_date": normalized_text(item.get("publishedDate") or item.get("published_date")),
                "engine": "exa",
                "query": query,
            }
        )
    return rows


def parse_date(value: str, page_text: str) -> str | None:
    candidates = [value, page_text[:6000]]
    for candidate in candidates:
        if not candidate:
            continue
        iso = re.search(r"(?<!\d)(20\d{2})-(\d{2})-(\d{2})(?!\d)", candidate)
        if iso:
            try:
                return datetime(int(iso.group(1)), int(iso.group(2)), int(iso.group(3))).date().isoformat()
            except ValueError:
                pass
        match = DATE_RE.search(candidate)
        if match:
            try:
                return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3))).date().isoformat()
            except ValueError:
                pass
    return None


def any_signal(text: str, signals: Iterable[str]) -> bool:
    return any(str(signal) in text for signal in signals)


def matching_ids(text: str, pattern_map: Mapping[str, Any]) -> list[str]:
    out = []
    for key, patterns in pattern_map.items():
        if any(str(pattern) in text for pattern in (patterns or [])):
            out.append(str(key))
    return out


def classify_first(text: str, pattern_map: Mapping[str, Any], default: str) -> str:
    for key, patterns in pattern_map.items():
        if any(str(pattern) in text for pattern in (patterns or [])):
            return str(key)
    return default


def institution_for_host(host: str) -> str:
    host = host.casefold()
    mapping = {
        "spp.gov.cn": "人民检察院公开来源",
        "court.gov.cn": "人民法院公开来源",
        "rmfyalk.court.gov.cn": "人民法院案例库",
        "mps.gov.cn": "公安机关公开来源",
        "ccdi.gov.cn": "纪检监察公开来源",
        "moj.gov.cn": "司法行政公开来源",
        "customs.gov.cn": "海关缉私公开来源",
        "nia.gov.cn": "移民管理公开来源",
        "ccg.gov.cn": "海警公开来源",
    }
    for suffix, name in mapping.items():
        if host == suffix or host.endswith("." + suffix):
            return name
    return "官方公开来源"


def safe_case_type(text: str) -> str:
    pairs = [
        ("network_or_telecom_crime", ("网络犯罪", "电信网络诈骗", "涉网案件")),
        ("property_or_economic_crime", ("盗窃", "诈骗", "经济犯罪")),
        ("duty_crime_or_supervision", ("职务犯罪", "审查调查", "监察调查")),
        ("drug_or_toxicology_case", ("毒品", "毒物")),
        ("public_interest_or_environment", ("公益诉讼", "生态环境", "自然资源")),
        ("injury_or_forensic_medical_case", ("伤情", "法医", "医学影像")),
    ]
    for value, signals in pairs:
        if any(signal in text for signal in signals):
            return value
    return "public_case_practice"


def build_observation(
    candidate: Mapping[str, Any],
    page_text: str,
    policy: Mapping[str, Any],
    existing: list[Mapping[str, Any]],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    url = str(candidate["url"])
    parsed = urllib.parse.urlsplit(url)
    host = str(parsed.hostname or "").casefold()
    title = normalized_text(candidate.get("title")) or host
    record: dict[str, Any] = {
        "url": url,
        "title": title[:300],
        "host": host,
        "engine": candidate.get("engine"),
        "query": candidate.get("query"),
        "status": "REVIEW_ONLY",
        "reason": None,
        "matched_capability_ids": [],
    }
    if any_signal(page_text, policy["sensitive_operational_signals"]):
        record["reason"] = "sensitive_operational_signal"
        return None, record
    if any_signal(page_text, policy["conflict_or_review_signals"]):
        record["reason"] = "conflict_or_admissibility_review_signal"
        return None, record
    if not any_signal(page_text, policy["case_signals"]):
        record["reason"] = "no_case_practice_signal"
        return None, record
    capabilities = matching_ids(page_text, policy["capability_patterns"])
    max_caps = int(policy["limits"]["max_capability_ids_per_observation"])
    if not capabilities:
        record["reason"] = "no_known_safe_capability_match"
        return None, record
    if len(capabilities) > max_caps:
        record["reason"] = "too_many_capability_matches"
        return None, record
    pub_date = parse_date(str(candidate.get("published_date") or ""), page_text)
    if not pub_date:
        record["reason"] = "publication_date_unverified"
        return None, record

    evidence_tokens = matching_ids(page_text, policy["evidence_token_patterns"])
    stage = classify_first(page_text, policy["procedural_stage_patterns"], "public_case_practice")
    outcome_key = classify_first(page_text, policy["outcome_patterns"], "public_result_not_further_classified")
    review_types = []
    for cap in capabilities:
        if cap in {
            "electronic-data-forensics",
            "network-log-and-connection-evidence",
            "forensic-medicine-and-dna",
            "toxicology-chemistry-microtrace",
            "geospatial-remote-sensing-and-mapping",
            "video-image-investigation",
            "audio-voice-evidence",
            "fingerprint-trace-document-forensics",
            "technical-evidence-specialist-review",
        }:
            review_types.append(cap)

    assistance = []
    if "provider-and-institutional-assistance" in capabilities:
        assistance.append("lawfully_public_provider_or_institutional_record_assistance")
    cooperation = []
    if "interagency-evidence-cooperation" in capabilities:
        cooperation.append("publicly_described_interagency_evidence_or_technical_cooperation")

    fingerprint_material = f"{url}|{pub_date}|{title}"
    fingerprint = hashlib.sha256(fingerprint_material.encode("utf-8")).hexdigest()[:24]
    observation_id = f"auto-{pub_date.replace('-', '')}-{fingerprint[:12]}"

    corroborates: list[str] = []
    current_caps = set(capabilities)
    for row in existing:
        old_caps = {str(x) for x in row.get("capability_ids") or []}
        if current_caps & old_caps:
            oid = str(row.get("observation_id") or "")
            if oid and oid not in corroborates:
                corroborates.append(oid)
        if len(corroborates) >= 5:
            break

    observation = {
        "observation_id": observation_id,
        "case_source": title[:500],
        "primary_source_url": url,
        "publication_date": pub_date,
        "case_type": safe_case_type(page_text),
        "jurisdiction_or_institution": institution_for_host(host),
        "procedural_stage": stage,
        "publicly_described_clue_origin": "一手官方公开材料描述案件或监督实践；自动吸收层不保留目标选择、秘密数据源或行动部署细节。",
        "public_evidence_chain": evidence_tokens or ["publicly_described_evidence_or_technical_review"],
        "digital_or_forensic_review_type": review_types,
        "lawful_provider_or_institutional_assistance_if_public": assistance,
        "interagency_cooperation_if_public": cooperation,
        "procedure_or_admissibility_issue": "仅记录公开材料中出现的高层证据类别、程序阶段和技术性审查类型；不保存秘密实施方法。",
        "outcome": outcome_key,
        "capability_ids": capabilities,
        "verification_status": str(policy["verification_and_iteration"]["new_primary_case_observation_level"]),
        "corroborates_observation_ids": corroborates,
        "conflicts_with_observation_ids": [],
        "source_fingerprint": fingerprint,
        "reviewed_at": iso_date(),
    }
    record["status"] = "AUTO_ABSORB_ELIGIBLE"
    record["reason"] = "primary_official_case_with_known_safe_capability"
    record["matched_capability_ids"] = capabilities
    record["observation_id"] = observation_id
    return observation, record


def recompute_rollup(ledger: dict[str, Any], policy: Mapping[str, Any]) -> None:
    existing_rollup = {
        str(row.get("capability_id")): dict(row)
        for row in ledger.get("capability_rollup") or []
        if isinstance(row, Mapping) and row.get("capability_id")
    }
    by_cap: dict[str, list[str]] = {}
    for obs in ledger.get("observations") or []:
        if not isinstance(obs, Mapping):
            continue
        oid = str(obs.get("observation_id") or "")
        for cap in obs.get("capability_ids") or []:
            if oid:
                by_cap.setdefault(str(cap), []).append(oid)

    rows: list[dict[str, Any]] = []
    min_cor = int(policy["verification_and_iteration"]["corroborated_minimum_independent_observations"])
    for cap in sorted(by_cap):
        ids = list(dict.fromkeys(by_cap[cap]))
        prior = existing_rollup.get(cap, {})
        prior_level = str(prior.get("verification_level") or "")
        if prior_level in {"CONTESTED", "STALE_REVIEW_REQUIRED", "STRONGLY_CORROBORATED"}:
            level = prior_level
        elif len(ids) >= min_cor:
            level = "CORROBORATED_PRACTICE"
        else:
            level = "PRIMARY_OBSERVED"
        note = str(prior.get("note") or "")
        if not note:
            note = f"由版本化公开案件观察账本汇总；当前支持观察 {len(ids)} 条。自动流程最高只提升至 CORROBORATED_PRACTICE。"
        rows.append(
            {
                "capability_id": cap,
                "verification_level": level,
                "supporting_observation_ids": ids,
                "note": note,
            }
        )
    ledger["capability_rollup"] = rows


def validate_contract(policy: Mapping[str, Any], matrix: Mapping[str, Any], ledger: Mapping[str, Any]) -> dict[str, Any]:
    assert policy["schema_version"] == "prc-justice-self-iteration-policy-v1"
    safety = policy["safety_boundary"]
    required_false = [
        "automatic_login",
        "captcha_solving",
        "waf_bypass",
        "hidden_api_reverse_engineering",
        "proxy_or_identity_rotation",
        "secret_internal_system_collection",
        "covert_surveillance_implementation_details",
        "target_selection_or_tracking_playbook",
        "investigation_evasion",
        "anti_forensics",
        "evidence_destruction",
        "operational_tactical_playbook",
        "personal_targeting",
    ]
    for key in required_false:
        assert safety[key] is False, key
    assert safety["public_or_authorized_sources_only"] is True
    assert safety["primary_source_required_for_automatic_absorption"] is True
    assert policy["automation_gate"]["never_admin_bypass_branch_protection"] is True

    capabilities = {
        str(row["capability_id"])
        for row in matrix.get("technology_domains") or []
        if isinstance(row, Mapping) and row.get("capability_id")
    }
    assert len(capabilities) >= 19
    assert set(policy["capability_patterns"]).issubset(capabilities)
    assert "network-crime-investigation" in capabilities
    assert "electronic-data-forensics" in capabilities
    assert "network-log-and-connection-evidence" in capabilities

    primary_hosts = {str(x) for x in policy["primary_outcome_hosts"]}
    assert len(primary_hosts) >= 8
    assert all("." in host and "://" not in host for host in primary_hosts)
    assert int(policy["limits"]["minimum_seconds_between_prc_primary_fetches"]) >= 10
    assert int(policy["limits"]["max_new_observations_per_run"]) <= 10
    assert policy["limits"]["automatic_retry"] is False

    observations = [row for row in ledger.get("observations") or [] if isinstance(row, Mapping)]
    ids = [str(row.get("observation_id")) for row in observations]
    assert len(ids) == len(set(ids))
    urls = [str(row.get("primary_source_url") or "") for row in observations if row.get("primary_source_url")]
    assert len(urls) == len(set(urls))
    assert ledger["safety_boundary"]["history_deletion_on_conflict"] is False

    synthetic = (
        "最高人民检察院发布典型案例。检察机关开展技术性证据审查，"
        "复核原始电子数据、应用日志和网络连接记录，并结合平台数据和交易记录进行证据审查。"
    )
    matched = matching_ids(synthetic, policy["capability_patterns"])
    assert "electronic-data-forensics" in matched
    assert "network-log-and-connection-evidence" in matched
    assert "technical-evidence-specialist-review" in matched

    return {
        "status": "PASS",
        "reviewable": True,
        "verifiable": True,
        "absorbable": True,
        "iterable": True,
        "primary_host_count": len(primary_hosts),
        "capability_pattern_count": len(policy["capability_patterns"]),
        "existing_observation_count": len(observations),
        "automatic_retry": False,
        "secret_operational_details": False,
    }


def run_live(args: argparse.Namespace, policy: dict[str, Any], matrix: dict[str, Any], ledger: dict[str, Any]) -> int:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    profile = args.profile
    if profile == "auto":
        profile = "weekly" if utc_now().weekday() == 6 else "daily"

    timeout = int(policy["limits"]["request_timeout_seconds"])
    result_limit = int(policy["limits"]["search_results_per_query"])
    query_limit = int(
        policy["limits"]["search_queries_per_engine_weekly"]
        if profile == "weekly"
        else policy["limits"]["search_queries_per_engine_daily"]
    )
    queries = list(policy["daily_queries"])
    if profile == "weekly":
        queries += list(policy["weekly_extra_queries"])
    queries = queries[:query_limit]

    tokens = {
        "tavily": str(os.getenv("TAVILY_API_KEY") or "").strip(),
        "exa": str(os.getenv("EXA_API_KEY") or "").strip(),
    }
    active_engines = [name for name, token in tokens.items() if token]
    report: dict[str, Any] = {
        "schema_version": "prc-justice-self-iteration-report-v1",
        "run_at": utc_now().replace(microsecond=0).isoformat(),
        "profile": profile,
        "status": "RUNNING",
        "active_search_engines": active_engines,
        "queries": queries,
        "search_errors": [],
        "candidate_count": 0,
        "primary_pages_fetched": 0,
        "new_observation_count": 0,
        "review_candidate_count": 0,
        "ledger_changed": False,
        "auto_merge_eligible": False,
        "safety_boundary_triggered": False,
    }
    if not active_engines:
        report["status"] = "FAIL_NO_DISCOVERY_KEY"
        save_json(output_dir / "self-iteration-report.json", report)
        return 3

    start_date = (utc_now() - timedelta(days=int(policy["cadence"]["maximum_age_days_for_search"]))).isoformat()
    found: list[dict[str, Any]] = []
    for query in queries:
        if tokens["tavily"]:
            try:
                found.extend(search_tavily(query, tokens["tavily"], result_limit, timeout))
            except Exception as exc:
                report["search_errors"].append(f"tavily:{type(exc).__name__}:{str(exc)[:180]}")
        if tokens["exa"]:
            try:
                found.extend(search_exa(query, tokens["exa"], result_limit, timeout, start_date))
            except Exception as exc:
                report["search_errors"].append(f"exa:{type(exc).__name__}:{str(exc)[:180]}")

    all_allowed = {
        str(x).casefold()
        for x in list(policy["primary_outcome_hosts"]) + list(policy["source_view_hosts"])
    }
    dedup: dict[str, dict[str, Any]] = {}
    for row in found:
        safe = safe_https_url(str(row.get("url") or ""), all_allowed, resolve=False)
        if not safe:
            continue
        row = dict(row)
        row["url"] = safe
        if safe not in dedup:
            dedup[safe] = row
        else:
            old = dedup[safe]
            if len(str(row.get("snippet") or "")) > len(str(old.get("snippet") or "")):
                dedup[safe] = row

    max_candidates = int(policy["limits"]["max_unique_candidate_urls"])
    candidates = list(dedup.values())[:max_candidates]
    report["candidate_count"] = len(candidates)

    existing_rows = [dict(row) for row in ledger.get("observations") or [] if isinstance(row, Mapping)]
    existing_urls = {str(row.get("primary_source_url") or "") for row in existing_rows}
    existing_fingerprints = {str(row.get("source_fingerprint") or "") for row in existing_rows}
    existing_ids = {str(row.get("observation_id") or "") for row in existing_rows}

    primary_hosts = {str(x).casefold() for x in policy["primary_outcome_hosts"]}
    max_fetch = int(policy["limits"]["max_primary_pages_fetched"])
    sleep_seconds = int(policy["limits"]["minimum_seconds_between_prc_primary_fetches"])
    new_obs: list[dict[str, Any]] = []
    candidate_records: list[dict[str, Any]] = []
    last_fetch = 0.0

    for candidate in candidates:
        if len(new_obs) >= int(policy["limits"]["max_new_observations_per_run"]):
            break
        url = str(candidate["url"])
        host = str(urllib.parse.urlsplit(url).hostname or "").casefold()
        if not host_allowed(host, primary_hosts):
            candidate_records.append(
                {
                    "url": url,
                    "title": candidate.get("title"),
                    "host": host,
                    "status": "SOURCE_VIEW_ONLY",
                    "reason": "not_primary_outcome_host",
                    "engine": candidate.get("engine"),
                }
            )
            continue
        if url in existing_urls:
            candidate_records.append(
                {
                    "url": url,
                    "title": candidate.get("title"),
                    "host": host,
                    "status": "ALREADY_ABSORBED",
                    "reason": "primary_url_seen",
                    "engine": candidate.get("engine"),
                }
            )
            continue
        if report["primary_pages_fetched"] >= max_fetch:
            break

        since = time.monotonic() - last_fetch
        if last_fetch and since < sleep_seconds:
            time.sleep(sleep_seconds - since)
        try:
            page_text, fetch_meta = fetch_primary_page(url, policy)
        except Exception as exc:
            candidate_records.append(
                {
                    "url": url,
                    "title": candidate.get("title"),
                    "host": host,
                    "status": "FETCH_FAILED_REVIEW_ONLY",
                    "reason": f"{type(exc).__name__}:{str(exc)[:180]}",
                    "engine": candidate.get("engine"),
                }
            )
            last_fetch = time.monotonic()
            report["primary_pages_fetched"] += 1
            continue
        last_fetch = time.monotonic()
        report["primary_pages_fetched"] += 1
        observation, record = build_observation(candidate, page_text, policy, existing_rows + new_obs)
        record["fetch"] = fetch_meta
        candidate_records.append(record)
        if observation is None:
            if record.get("reason") in {"sensitive_operational_signal", "conflict_or_admissibility_review_signal"}:
                report["safety_boundary_triggered"] = True
            continue
        if observation["observation_id"] in existing_ids:
            continue
        if observation["source_fingerprint"] in existing_fingerprints:
            continue
        new_obs.append(observation)
        existing_ids.add(observation["observation_id"])
        existing_fingerprints.add(observation["source_fingerprint"])

    report["review_candidate_count"] = sum(
        1
        for row in candidate_records
        if str(row.get("status")) not in {"AUTO_ABSORB_ELIGIBLE", "ALREADY_ABSORBED", "SOURCE_VIEW_ONLY"}
    )

    if new_obs:
        original_observations = copy.deepcopy(existing_rows)
        ledger["observations"] = existing_rows + new_obs
        assert ledger["observations"][: len(original_observations)] == original_observations
        recompute_rollup(ledger, policy)
        ledger["reviewed_at"] = iso_date()
        if args.write_ledger:
            save_json(Path(args.ledger), ledger)
        report["ledger_changed"] = True

    report["new_observation_count"] = len(new_obs)
    report["new_observation_ids"] = [row["observation_id"] for row in new_obs]
    report["auto_merge_eligible"] = bool(
        new_obs
        and not report["safety_boundary_triggered"]
        and all(row["verification_status"] == "PRIMARY_OBSERVED" for row in new_obs)
    )
    report["status"] = "PASS"

    save_json(output_dir / "self-iteration-report.json", report)
    save_jsonl(output_dir / "candidate-observations.jsonl", candidate_records)
    save_json(output_dir / "new-observations.json", {"observations": new_obs})
    return 0


def parse_args() -> argparse.Namespace:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("validate", "live"), default="validate")
    parser.add_argument("--profile", choices=("auto", "daily", "weekly"), default="auto")
    parser.add_argument("--policy", type=Path, default=here / "prc-justice-self-iteration-policy.json")
    parser.add_argument("--matrix", type=Path, default=here / "investigative-technology-intelligence-matrix.json")
    parser.add_argument("--ledger", type=Path, default=here / "case-derived-investigative-capability-ledger.json")
    parser.add_argument("--output-dir", default="prc-justice-self-iteration-artifact")
    parser.add_argument("--write-ledger", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    policy = load_json(args.policy)
    matrix = load_json(args.matrix)
    ledger = load_json(args.ledger)
    validation = validate_contract(policy, matrix, ledger)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    save_json(output_dir / "contract-validation.json", validation)
    if args.mode == "validate":
        print(json.dumps(validation, ensure_ascii=False))
        return 0
    result = run_live(args, policy, matrix, ledger)
    report_path = output_dir / "self-iteration-report.json"
    if report_path.exists():
        print(report_path.read_text(encoding="utf-8").strip())
    return result


if __name__ == "__main__":
    raise SystemExit(main())
