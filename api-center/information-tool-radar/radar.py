#!/usr/bin/env python3
"""Bounded, read-only Information & Tool Radar.

The runner uses only the Python standard library. It discovers metadata from
independent public indexes and registries, normalizes candidates, measures
coverage and writes auditable artifacts. It never installs or executes any
discovered project.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import urlparse

USER_AGENT = (
    "evidence-data-center-information-tool-radar/1 "
    "(+https://github.com/a15280020511/evidence-data-center)"
)
RETRYABLE_HTTP = {429, 500, 502, 503, 504}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def bounded_text(value: Any, maximum: int = 300) -> str:
    return " ".join(str(value or "").split()).strip()[:maximum]


def request_bytes(
    url: str,
    *,
    timeout: int,
    max_bytes: int,
    method: str = "GET",
    body: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    attempts: int = 3,
) -> bytes:
    request_headers = {
        "Accept": "application/json, application/xml, text/xml, application/rss+xml, text/plain",
        "Accept-Encoding": "identity",
        "User-Agent": USER_AGENT,
    }
    request_headers.update(dict(headers or {}))
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    last_error: BaseException | None = None
    for attempt in range(max(1, attempts)):
        request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = response.read(max_bytes + 1)
                if len(payload) > max_bytes:
                    raise RuntimeError(f"response exceeded {max_bytes} bytes")
                return payload
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in RETRYABLE_HTTP or attempt + 1 >= attempts:
                raise
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            try:
                delay = min(float(retry_after), 5.0) if retry_after else float(2 ** attempt)
            except ValueError:
                delay = float(2 ** attempt)
            time.sleep(delay)
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt + 1 >= attempts:
                raise
            time.sleep(float(2 ** attempt))
    raise RuntimeError(f"request failed: {last_error}")


def request_json(url: str, **kwargs: Any) -> Any:
    return json.loads(request_bytes(url, **kwargs).decode("utf-8"))


def query_url(base: str, params: Mapping[str, Any]) -> str:
    return base + ("&" if "?" in base else "?") + urllib.parse.urlencode(params, doseq=True)


def candidate_id(adapter: str, category: str, title: str, locator: str) -> str:
    raw = "\0".join((adapter, category, title.casefold(), locator)).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def make_candidate(
    adapter: str,
    category: str,
    title: str,
    locator: str,
    evidence: Mapping[str, Any],
    *,
    language: str | None = None,
    country: str | None = None,
    status: str = "candidate",
) -> dict[str, Any]:
    normalized_title = bounded_text(title) or bounded_text(locator)
    normalized_locator = bounded_text(locator, 2000)
    return {
        "candidate_id": candidate_id(adapter, category, normalized_title, normalized_locator),
        "adapter": adapter,
        "category": category,
        "title": normalized_title,
        "locator": normalized_locator,
        "language": language,
        "country": country,
        "discovered_at": utc_now(),
        "evidence": dict(evidence),
        "status": status,
    }


@dataclass
class AdapterResult:
    name: str
    category: str
    success: bool = False
    candidates: list[dict[str, Any]] = field(default_factory=list)
    probes: int = 0
    successful_probes: int = 0
    errors: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def add_error(self, exc: BaseException | str) -> None:
        text = str(exc)
        if isinstance(exc, BaseException):
            text = f"{type(exc).__name__}: {exc}"
        self.errors.append(text[:300])


def common_crawl(config: Mapping[str, Any], runtime: Mapping[str, int]) -> AdapterResult:
    result = AdapterResult("common_crawl", str(config["category"]))
    result.probes += 1
    catalog = request_json(str(config["index_catalog"]), timeout=runtime["timeout"], max_bytes=runtime["max_bytes"])
    if not isinstance(catalog, list) or not catalog:
        raise RuntimeError("Common Crawl index catalog was empty")
    result.successful_probes += 1
    latest = catalog[0]
    index_id = str(latest.get("id") or "")
    index_url = str(latest.get("cdx-api") or f"https://index.commoncrawl.org/{index_id}-index")
    result.details["index_id"] = index_id
    for domain in list(config.get("probe_domains") or []):
        result.probes += 1
        try:
            url = query_url(index_url, {"url": domain, "output": "json", "matchType": "domain", "filter": "status:200", "limit": runtime["max_records"]})
            payload = request_bytes(url, timeout=runtime["timeout"], max_bytes=runtime["max_bytes"])
            rows = [json.loads(line) for line in payload.decode("utf-8", errors="replace").splitlines() if line.strip()]
            result.successful_probes += 1
            for row in rows[: runtime["max_records"]]:
                original = str(row.get("url") or row.get("urlkey") or domain)
                result.candidates.append(make_candidate(result.name, result.category, f"Common Crawl capture: {domain}", original, {"index": index_id, "timestamp": row.get("timestamp"), "status": row.get("status")}, status="reference"))
        except Exception as exc:
            result.add_error(f"{domain}: {type(exc).__name__}: {exc}")
    result.success = result.successful_probes > 0
    return result


def parse_cdx(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, list):
        raise RuntimeError("CDX endpoint did not return a JSON list")
    if not data:
        return []
    header = data[0] if isinstance(data[0], list) else []
    rows = data[1:] if header else data
    output: list[dict[str, Any]] = []
    for row in rows:
        if isinstance(row, list) and header:
            output.append(dict(zip(header, row)))
        elif isinstance(row, Mapping):
            output.append(dict(row))
    return output


def wayback(config: Mapping[str, Any], runtime: Mapping[str, int]) -> AdapterResult:
    result = AdapterResult("wayback", str(config["category"]))
    endpoints = [str(config.get("endpoint") or "")]
    fallback = str(config.get("fallback_endpoint") or "")
    if fallback:
        endpoints.append(fallback)
    backend_success: dict[str, int] = {endpoint: 0 for endpoint in endpoints if endpoint}
    for domain in list(config.get("probe_domains") or []):
        result.probes += 1
        for endpoint in endpoints:
            if not endpoint:
                continue
            try:
                params: dict[str, Any] = {"url": domain, "output": "json", "limit": runtime["max_records"]}
                if "web.archive.org" in endpoint:
                    params.update({"fl": "timestamp,original,statuscode,digest", "filter": "statuscode:200", "collapse": "digest"})
                data = request_json(query_url(endpoint, params), timeout=runtime["timeout"], max_bytes=runtime["max_bytes"], attempts=2)
                rows = parse_cdx(data)
                backend_success[endpoint] = backend_success.get(endpoint, 0) + 1
                result.successful_probes += 1
                for item in rows[: runtime["max_records"]]:
                    original = str(item.get("original") or item.get("url") or domain)
                    timestamp = str(item.get("timestamp") or "")
                    if "arquivo.pt" in endpoint:
                        replay = f"https://arquivo.pt/wayback/{timestamp}/{original}" if timestamp else original
                        backend_name = "arquivo.pt"
                    else:
                        replay = f"https://web.archive.org/web/{timestamp}/{original}" if timestamp else original
                        backend_name = "internet-archive"
                    result.candidates.append(make_candidate(result.name, result.category, f"Archived snapshot: {domain}", replay, {**item, "archive_backend": backend_name}, status="reference"))
                break
            except Exception as exc:
                result.add_error(f"{domain} via {endpoint}: {type(exc).__name__}: {exc}")
    result.details["backend_success"] = backend_success
    result.success = result.successful_probes > 0
    return result


def gdelt(config: Mapping[str, Any], runtime: Mapping[str, int]) -> AdapterResult:
    result = AdapterResult("gdelt", str(config["category"]))
    for query in list(config.get("queries") or []):
        result.probes += 1
        try:
            url = query_url(str(config["endpoint"]), {"query": query, "mode": "artlist", "maxrecords": runtime["max_records"], "format": "json", "sort": "HybridRel"})
            data = request_json(url, timeout=runtime["timeout"], max_bytes=runtime["max_bytes"], attempts=2)
            articles = data.get("articles") if isinstance(data, Mapping) else []
            if not isinstance(articles, list):
                raise RuntimeError("GDELT articles missing")
            result.successful_probes += 1
            for item in articles[: runtime["max_records"]]:
                if isinstance(item, Mapping) and item.get("url"):
                    result.candidates.append(make_candidate(result.name, result.category, str(item.get("title") or query), str(item["url"]), {"query": query, "domain": item.get("domain"), "seendate": item.get("seendate")}, language=str(item.get("language") or "") or None, country=str(item.get("sourcecountry") or "") or None, status="reference"))
        except Exception as exc:
            result.add_error(f"{query}: {type(exc).__name__}: {exc}")
    result.success = result.successful_probes > 0
    return result


def wikimedia(config: Mapping[str, Any], runtime: Mapping[str, int]) -> AdapterResult:
    result = AdapterResult("wikimedia", str(config["category"]))
    languages = list(config.get("languages") or [])
    successful_languages: list[str] = []
    delay = max(0.0, min(float(config.get("request_delay_seconds") or 0.0), 2.0))
    maxlag = min(max(int(config.get("maxlag") or 5), 1), 10)
    for index, language in enumerate(languages):
        if index and delay:
            time.sleep(delay)
        result.probes += 1
        try:
            endpoint = f"https://{language}.wikipedia.org/w/api.php"
            url = query_url(endpoint, {"action": "query", "list": "recentchanges", "rcnamespace": 0, "rclimit": runtime["max_records"], "rcprop": "title|timestamp|ids", "format": "json", "formatversion": 2, "maxlag": maxlag})
            data = request_json(url, timeout=runtime["timeout"], max_bytes=runtime["max_bytes"], attempts=3)
            changes = data.get("query", {}).get("recentchanges", []) if isinstance(data, Mapping) else []
            if not isinstance(changes, list):
                raise RuntimeError("Wikimedia recentchanges missing")
            result.successful_probes += 1
            successful_languages.append(str(language))
            for item in changes[: runtime["max_records"]]:
                if not isinstance(item, Mapping):
                    continue
                pageid = item.get("pageid")
                title = str(item.get("title") or "")
                locator = f"https://{language}.wikipedia.org/?curid={pageid}" if pageid else f"https://{language}.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                result.candidates.append(make_candidate(result.name, result.category, title, locator, {"timestamp": item.get("timestamp"), "revid": item.get("revid")}, language=str(language), status="change_signal"))
        except Exception as exc:
            result.add_error(f"{language}: {type(exc).__name__}: {exc}")
    result.details["languages_configured"] = languages
    result.details["languages_succeeded"] = successful_languages
    result.success = result.successful_probes > 0
    return result


def datacite_rows(data: Any) -> list[Mapping[str, Any]]:
    rows = data.get("data") if isinstance(data, Mapping) else []
    if not isinstance(rows, list):
        raise RuntimeError("DataCite data missing")
    return [row for row in rows if isinstance(row, Mapping)]


def add_datacite_candidates(result: AdapterResult, rows: Iterable[Mapping[str, Any]], query: str, maximum: int) -> None:
    for row in list(rows)[:maximum]:
        attributes = row.get("attributes") if isinstance(row.get("attributes"), Mapping) else {}
        titles = attributes.get("titles") if isinstance(attributes.get("titles"), list) else []
        title = str(titles[0].get("title") or "") if titles and isinstance(titles[0], Mapping) else ""
        doi = str(attributes.get("doi") or row.get("id") or "")
        locator = str(attributes.get("url") or (f"https://doi.org/{doi}" if doi else ""))
        if locator:
            result.candidates.append(make_candidate(result.name, result.category, title or doi or query, locator, {"query": query, "doi": doi, "types": attributes.get("types")}, status="reference"))


def datacite(config: Mapping[str, Any], runtime: Mapping[str, int]) -> AdapterResult:
    result = AdapterResult("datacite", str(config["category"]))
    endpoint = str(config["endpoint"])
    for query in list(config.get("queries") or []):
        result.probes += 1
        words = [word for word in str(query).split() if word]
        expression = "titles.title:(" + " +".join(words) + ")" if words else str(query)
        try:
            url = query_url(endpoint, {"query": expression, "page[size]": runtime["max_records"], "sort": "relevance"})
            rows = datacite_rows(request_json(url, timeout=runtime["timeout"], max_bytes=runtime["max_bytes"], attempts=3))
            result.successful_probes += 1
            add_datacite_candidates(result, rows, str(query), runtime["max_records"])
        except Exception as exc:
            result.add_error(f"{query}: {type(exc).__name__}: {exc}")
    if not result.candidates:
        result.probes += 1
        fallback_params = dict(config.get("fallback_parameters") or {})
        fallback_params["page[size]"] = runtime["max_records"]
        try:
            rows = datacite_rows(request_json(query_url(endpoint, fallback_params), timeout=runtime["timeout"], max_bytes=runtime["max_bytes"], attempts=3))
            result.successful_probes += 1
            result.details["fallback_used"] = True
            add_datacite_candidates(result, rows, "recent datasets fallback", runtime["max_records"])
        except Exception as exc:
            result.add_error(f"fallback: {type(exc).__name__}: {exc}")
    result.success = result.successful_probes > 0
    return result


def pypi(config: Mapping[str, Any], runtime: Mapping[str, int]) -> AdapterResult:
    result = AdapterResult("pypi", str(config["category"]))
    result.probes = 1
    root = ET.fromstring(request_bytes(str(config["rss"]), timeout=runtime["timeout"], max_bytes=runtime["max_bytes"]))
    for item in root.findall(".//item")[: runtime["max_records"]]:
        title = bounded_text(item.findtext("title") or "")
        link = bounded_text(item.findtext("link") or "", 2000)
        if title and link:
            result.candidates.append(make_candidate(result.name, result.category, title, link, {"published": bounded_text(item.findtext("pubDate") or "")}, status="change_signal"))
    result.successful_probes = 1
    result.success = True
    return result


def osv(config: Mapping[str, Any], runtime: Mapping[str, int]) -> AdapterResult:
    result = AdapterResult("osv", str(config["category"]))
    packages = [item for item in list(config.get("packages") or []) if isinstance(item, Mapping)]
    result.probes = len(packages)
    data = request_json(str(config["endpoint"]), method="POST", body={"queries": [{"package": dict(item)} for item in packages]}, timeout=runtime["timeout"], max_bytes=runtime["max_bytes"])
    rows = data.get("results") if isinstance(data, Mapping) else []
    if not isinstance(rows, list):
        raise RuntimeError("OSV batch results missing")
    result.successful_probes = min(len(rows), len(packages))
    for package, row in zip(packages, rows):
        vulnerabilities = row.get("vulns") if isinstance(row, Mapping) and isinstance(row.get("vulns"), list) else []
        for vuln in vulnerabilities[: runtime["max_records"]]:
            if isinstance(vuln, Mapping):
                vuln_id = str(vuln.get("id") or "unknown")
                result.candidates.append(make_candidate(result.name, result.category, f"{package.get('ecosystem')}:{package.get('name')} {vuln_id}", f"https://osv.dev/vulnerability/{urllib.parse.quote(vuln_id)}", {"package": dict(package), "aliases": vuln.get("aliases"), "modified": vuln.get("modified")}, status="change_signal"))
    result.success = result.successful_probes > 0
    return result


def github(config: Mapping[str, Any], runtime: Mapping[str, int]) -> AdapterResult:
    result = AdapterResult("github", str(config["category"]))
    token = os.getenv("GITHUB_TOKEN", "").strip()
    headers = {"X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    for query in list(config.get("queries") or []):
        result.probes += 1
        try:
            url = query_url(str(config["endpoint"]), {"q": query, "sort": "updated", "order": "desc", "per_page": runtime["max_records"]})
            data = request_json(url, timeout=runtime["timeout"], max_bytes=runtime["max_bytes"], headers=headers)
            rows = data.get("items") if isinstance(data, Mapping) else []
            if not isinstance(rows, list):
                raise RuntimeError("GitHub items missing")
            result.successful_probes += 1
            for row in rows[: runtime["max_records"]]:
                if isinstance(row, Mapping) and row.get("html_url"):
                    result.candidates.append(make_candidate(result.name, result.category, str(row.get("full_name") or row.get("name") or query), str(row["html_url"]), {"query": query, "description": bounded_text(row.get("description") or "", 500), "archived": bool(row.get("archived", False)), "updated_at": row.get("updated_at"), "language": row.get("language"), "stars": row.get("stargazers_count")}, status="candidate"))
        except Exception as exc:
            result.add_error(f"{query}: {type(exc).__name__}: {exc}")
    result.success = result.successful_probes > 0
    return result


ADAPTERS: dict[str, Callable[[Mapping[str, Any], Mapping[str, int]], AdapterResult]] = {"common_crawl": common_crawl, "wayback": wayback, "gdelt": gdelt, "wikimedia": wikimedia, "datacite": datacite, "pypi": pypi, "osv": osv, "github": github}


def deduplicate(candidates: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for item in candidates:
        output.setdefault(str(item["candidate_id"]), item)
    return sorted(output.values(), key=lambda item: (str(item["category"]), str(item["adapter"]), str(item["title"]).casefold()))


def domain_count(candidates: Iterable[Mapping[str, Any]]) -> int:
    domains = {urlparse(str(item.get("locator") or "")).hostname.casefold() for item in candidates if urlparse(str(item.get("locator") or "")).hostname}
    return len(domains)


def build_report(config: Mapping[str, Any], results: list[AdapterResult]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    candidates = deduplicate(item for result in results for item in result.candidates)
    enabled_categories = {str(adapter.get("category")) for adapter in config.get("adapters", {}).values() if isinstance(adapter, Mapping) and bool(adapter.get("enabled", False))}
    successful = [result for result in results if result.success]
    hit_categories = {result.category for result in results if result.success and result.candidates}
    configured_languages: list[str] = []
    succeeded_languages: list[str] = []
    for result in results:
        if result.name == "wikimedia":
            configured_languages = list(result.details.get("languages_configured") or [])
            succeeded_languages = list(result.details.get("languages_succeeded") or [])
    success_rate = len(successful) / len(results) if results else 0.0
    category_coverage = len(hit_categories) / len(enabled_categories) if enabled_categories else 0.0
    language_coverage = len(succeeded_languages) / len(configured_languages) if configured_languages else 0.0
    minimum_success = float(config.get("minimum_success_rate") or 0.0)
    minimum_coverage = float(config.get("minimum_category_coverage") or 0.0)
    report = {"schema_version": "information-tool-radar-report-v1", "generated_at": utc_now(), "status": "pass" if success_rate >= minimum_success and category_coverage >= minimum_coverage else "fail", "scope": "bounded representative coverage test, not a claim of complete global coverage", "metrics": {"adapters_enabled": len(results), "adapters_succeeded": len(successful), "adapter_success_rate": round(success_rate, 4), "categories_configured": len(enabled_categories), "categories_with_candidates": len(hit_categories), "category_coverage": round(category_coverage, 4), "languages_configured": len(configured_languages), "languages_succeeded": len(succeeded_languages), "language_endpoint_coverage": round(language_coverage, 4), "unique_candidates": len(candidates), "unique_domains": domain_count(candidates), "total_probes": sum(result.probes for result in results), "successful_probes": sum(result.successful_probes for result in results)}, "thresholds": {"minimum_success_rate": minimum_success, "minimum_category_coverage": minimum_coverage}, "covered_categories": sorted(hit_categories), "blind_spots": sorted(enabled_categories - hit_categories), "adapters": {result.name: {"category": result.category, "success": result.success, "records": len(result.candidates), "probes": result.probes, "successful_probes": result.successful_probes, "errors": result.errors, "details": result.details} for result in results}, "safety": {"read_only": True, "installs_or_executes_discovered_code": False, "billing_activation": False, "production_promotion": False}}
    return report, candidates


def markdown_report(report: Mapping[str, Any]) -> str:
    metrics = report.get("metrics") if isinstance(report.get("metrics"), Mapping) else {}
    lines = ["# 信息工具雷达覆盖测试", "", f"- 状态：**{str(report.get('status')).upper()}**", f"- 适配器成功率：{float(metrics.get('adapter_success_rate') or 0):.1%}", f"- 八类覆盖率：{float(metrics.get('category_coverage') or 0):.1%}", f"- 多语言端点覆盖率：{float(metrics.get('language_endpoint_coverage') or 0):.1%}", f"- 唯一候选：{metrics.get('unique_candidates', 0)}", f"- 唯一域名：{metrics.get('unique_domains', 0)}", f"- 探测成功：{metrics.get('successful_probes', 0)}/{metrics.get('total_probes', 0)}", "", "> 本报告是有界代表性测试，不代表全球互联网绝对完整或无盲区。", "", "## 适配器", "", "| 适配器 | 类别 | 成功 | 记录 | 探测 | 错误 |", "|---|---|---:|---:|---:|---:|"]
    adapters = report.get("adapters") if isinstance(report.get("adapters"), Mapping) else {}
    for name, row in adapters.items():
        if isinstance(row, Mapping):
            lines.append(f"| {name} | {row.get('category')} | {'是' if row.get('success') else '否'} | {row.get('records', 0)} | {row.get('successful_probes', 0)}/{row.get('probes', 0)} | {len(row.get('errors') or [])} |")
    lines.extend(["", "## 未覆盖类别", ""])
    blind = list(report.get("blind_spots") or [])
    lines.append("无" if not blind else "、".join(blind))
    return "\n".join(lines) + "\n"


def run(config: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    runtime = {"timeout": min(max(int(config.get("timeout_seconds") or 20), 5), 60), "max_bytes": min(max(int(config.get("max_response_bytes") or 1_500_000), 10_000), 5_000_000), "max_records": min(max(int(config.get("max_records_per_probe") or 10), 1), 25)}
    results: list[AdapterResult] = []
    adapters = config.get("adapters") if isinstance(config.get("adapters"), Mapping) else {}
    for name, adapter_config in adapters.items():
        if not isinstance(adapter_config, Mapping) or not bool(adapter_config.get("enabled", False)):
            continue
        function = ADAPTERS.get(str(name))
        if function is None:
            result = AdapterResult(str(name), str(adapter_config.get("category") or "unknown")); result.add_error("adapter implementation missing"); results.append(result); continue
        try:
            results.append(function(adapter_config, runtime))
        except Exception as exc:
            result = AdapterResult(str(name), str(adapter_config.get("category") or "unknown")); result.add_error(exc); results.append(result)
    return build_report(config, results)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--config", type=Path, required=True); parser.add_argument("--output-dir", type=Path, required=True); parser.add_argument("--enforce-thresholds", action="store_true"); args = parser.parse_args(argv)
    config = load_json(args.config); report, candidates = run(config); args.output_dir.mkdir(parents=True, exist_ok=True)
    save_json(args.output_dir / "coverage-report.json", report); (args.output_dir / "coverage-report.md").write_text(markdown_report(report), encoding="utf-8")
    with (args.output_dir / "candidates.jsonl").open("w", encoding="utf-8") as handle:
        for item in candidates: handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
    save_json(args.output_dir / "manifest.json", {"schema_version": "information-tool-radar-artifact-manifest-v1", "generated_at": utc_now(), "files": ["coverage-report.json", "coverage-report.md", "candidates.jsonl"], "candidate_count": len(candidates), "status": report["status"]})
    print(json.dumps({"status": report["status"], **report["metrics"]}, ensure_ascii=False)); return 1 if args.enforce_thresholds and report["status"] != "pass" else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
