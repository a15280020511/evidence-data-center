#!/usr/bin/env python3
"""Daily, bounded discovery of public APIs, remote MCP endpoints and readable sources."""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import re
import socket
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

UA = "evidence-data-center-source-discovery/2"
URL_RE = re.compile(r"https://[^\s\"'<>)}\]]+", re.I)
BLOCKED_HOSTS = {
    "localhost", "metadata.google.internal", "metadata.azure.internal",
    "kubernetes.default", "instance-data",
}
BLOCKED_SUFFIXES = (".local", ".internal", ".localhost", ".svc", ".cluster.local")
MACHINE_TYPES = ("json", "xml", "csv", "rss", "atom", "yaml", "protobuf")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load(path: Path, default: Any) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def save(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def canonical_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]


def safe_https_url(value: Any, *, resolve: bool = False) -> str | None:
    try:
        parsed = urllib.parse.urlsplit(str(value or "").strip().rstrip(".,;:"))
    except ValueError:
        return None
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        return None
    if parsed.username or parsed.password or parsed.port not in (None, 443):
        return None
    host = parsed.hostname.casefold().rstrip(".")
    if host in BLOCKED_HOSTS or host.endswith(BLOCKED_SUFFIXES):
        return None
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None and not literal.is_global:
        return None
    if resolve and literal is None:
        try:
            addresses = {
                str(row[4][0]).split("%", 1)[0]
                for row in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
                if row and len(row) >= 5 and row[4]
            }
            if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
                return None
        except (socket.gaierror, ValueError):
            return None
    return urllib.parse.urlunsplit(("https", host, re.sub(r"/{2,}", "/", parsed.path or "/"), parsed.query, ""))


def request_json(
    url: str,
    method: str = "GET",
    body: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    max_bytes: int = 8_000_000,
) -> Any:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request_headers = {"Accept": "application/json", "User-Agent": UA, **dict(headers or {})}
    if data is not None:
        request_headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    with urllib.request.urlopen(request, timeout=25) as response:
        raw = response.read(max_bytes + 1)
        if len(raw) > max_bytes:
            raise RuntimeError("response exceeds maximum size")
        return json.loads(raw.decode("utf-8"))


def trusted_host(host: str, config: Mapping[str, Any]) -> bool:
    exact = {str(item).casefold() for item in config.get("trusted_exact_domains") or []}
    suffixes = tuple(str(item).casefold() for item in config.get("trusted_domain_suffixes") or [])
    return host.casefold() in exact or host.casefold().endswith(suffixes)


def detect_type(text: str, url: str) -> str:
    blob = f"{text} {url}".casefold()
    rules = (
        ("remote_mcp", ("model context protocol", "remote mcp", "/mcp")),
        ("openapi", ("openapi", "swagger")),
        ("graphql", ("graphql",)),
        ("ckan", ("ckan", "/api/3/action/")),
        ("socrata", ("socrata", "api/views")),
        ("arcgis_rest", ("arcgis", "/rest/services")),
        ("stac", ("stac",)),
        ("sparql", ("sparql",)),
        ("sdmx", ("sdmx",)),
        ("oai_pmh", ("oai-pmh", "verb=identify")),
        ("rss_atom", ("rss", "atom", "/feed")),
        ("bulk_download", ("bulk download", ".csv", ".json", ".zip")),
        ("rest_api", ("rest api", "/api/", "/v1/", "/v2/", "/v3/")),
    )
    for source_type, words in rules:
        if any(word in blob for word in words):
            return source_type
    return "web_read"


def license_state(text: str, config: Mapping[str, Any]) -> str:
    lowered = text.casefold()
    if any(str(term).casefold() in lowered for term in config.get("license_negative_terms") or []):
        return "prohibited"
    if any(str(term).casefold() in lowered for term in config.get("license_positive_terms") or []):
        return "open"
    return "unknown"


def auth_state(text: str, config: Mapping[str, Any]) -> str:
    lowered = text.casefold()
    return "required" if any(str(term).casefold() in lowered for term in config.get("auth_terms") or []) else "unknown"


def new_source(
    url: str,
    title: str,
    description: str,
    engine: str,
    query: str,
    config: Mapping[str, Any],
    *,
    source_type: str | None = None,
    auth: str | None = None,
    license_value: str | None = None,
    catalog_url: str | None = None,
) -> dict[str, Any] | None:
    normalized = safe_https_url(url)
    if not normalized:
        return None
    host = urllib.parse.urlsplit(normalized).hostname or ""
    text = f"{title} {description} {normalized}"
    row = {
        "source_id": canonical_id(normalized),
        "url": normalized,
        "host": host,
        "title": str(title or host)[:300],
        "description": str(description or "")[:1600],
        "source_type": source_type or detect_type(text, normalized),
        "auth": auth or auth_state(text, config),
        "license": license_value or license_state(text, config),
        "trusted_domain": trusted_host(host, config),
        "high_value": any(str(term).casefold() in text.casefold() for term in config.get("high_value_terms") or []),
        "discovery_engine": engine,
        "discovery_query": str(query)[:500],
        "catalog_url": catalog_url,
        "first_seen_at": utc_now(),
        "last_seen_at": utc_now(),
        "probe": {"ok": False, "machine_readable": False, "checked_at": None},
        "status": "candidate",
        "integration_mode": "manual_or_future_validation",
    }
    row["score"] = score(row)
    return row


def score(row: Mapping[str, Any]) -> int:
    value = 10
    value += 24 if row.get("trusted_domain") else 0
    value += 14 if row.get("source_type") not in {"web_read", "openapi_catalog"} else 0
    value += 12 if row.get("auth") == "none" else 2 if row.get("auth") == "required" else 0
    value += 10 if row.get("license") == "open" else -50 if row.get("license") == "prohibited" else 0
    value += 18 if (row.get("probe") or {}).get("ok") else 0
    value += 10 if (row.get("probe") or {}).get("machine_readable") else 0
    value += 8 if row.get("high_value") else 0
    value += 4 if row.get("discovery_engine") == "apis.guru" else 0
    return max(0, min(100, value))


def probe(row: dict[str, Any]) -> None:
    url = safe_https_url(row.get("url"), resolve=True)
    if not url:
        row["probe"] = {"ok": False, "machine_readable": False, "checked_at": utc_now(), "error": "unsafe URL"}
        return
    try:
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json, application/xml, text/csv, application/rss+xml, application/atom+xml, text/html;q=0.7",
                "Range": "bytes=0-65535",
                "User-Agent": UA,
            },
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            if not safe_https_url(response.geturl(), resolve=True):
                raise RuntimeError("unsafe redirect")
            raw = response.read(65537)
            content_type = str(response.headers.get("Content-Type") or "").split(";", 1)[0].casefold()
            machine = any(token in content_type for token in MACHINE_TYPES)
            row["probe"] = {
                "ok": 200 <= int(response.status) < 400,
                "status": int(response.status),
                "content_type": content_type,
                "machine_readable": machine,
                "bytes_sampled": min(len(raw), 65536),
                "checked_at": utc_now(),
            }
            if row.get("auth") == "unknown" and row["probe"]["ok"]:
                row["auth"] = "none"
    except Exception as exc:
        row["probe"] = {
            "ok": False,
            "machine_readable": False,
            "checked_at": utc_now(),
            "error": f"{type(exc).__name__}: {str(exc)[:180]}",
        }


def query_set(config: Mapping[str, Any], cursor: int, limit: int, regions: list[str]) -> tuple[list[str], int]:
    axes = [
        list(config.get("protocol_keywords") or []),
        list(config.get("institution_keywords") or []),
        list(config.get("sector_keywords") or []),
        list(config.get("publication_keywords") or []),
        regions,
    ]
    if not all(axes):
        return [], cursor
    total = 1
    for axis in axes:
        total *= len(axis)
    queries = []
    for offset in range(limit):
        number = (cursor + offset) % total
        values = []
        for axis in axes:
            values.append(axis[number % len(axis)])
            number //= len(axis)
        protocol, institution, sector, publication, region = values
        queries.append(f'"{protocol}" "{sector}" ({institution} OR "{publication}") "{region}"')
    return queries, (cursor + limit) % total


def countries(config: Mapping[str, Any], offline: bool) -> list[str]:
    fallback = list(config.get("regional_language_keywords") or [])
    if offline:
        return fallback
    try:
        data = request_json("https://api.worldbank.org/v2/country?format=json&per_page=400", max_bytes=2_000_000)
        names = {
            str(row["name"])
            for row in data[1]
            if row.get("name") and (row.get("region") or {}).get("id") != "NA"
        }
        return fallback + sorted(names)
    except Exception:
        return fallback


def api_base_urls(spec: Mapping[str, Any]) -> list[str]:
    result: list[str] = []
    for server in spec.get("servers") or []:
        if isinstance(server, Mapping):
            url = safe_https_url(server.get("url"))
            if url and "{" not in url:
                result.append(url.rstrip("/"))
    if not result and spec.get("host"):
        schemes = [str(item).casefold() for item in spec.get("schemes") or ["https"]]
        if "https" in schemes:
            candidate = safe_https_url(f"https://{spec['host']}{spec.get('basePath') or ''}")
            if candidate:
                result.append(candidate.rstrip("/"))
    return list(dict.fromkeys(result))


def required_parameters(path_row: Mapping[str, Any], operation: Mapping[str, Any]) -> bool:
    parameters: list[Any] = []
    parameters.extend(path_row.get("parameters") or [])
    parameters.extend(operation.get("parameters") or [])
    for parameter in parameters:
        if not isinstance(parameter, Mapping):
            continue
        location = str(parameter.get("in") or "")
        if location == "path" or bool(parameter.get("required")):
            return True
    return bool(operation.get("requestBody"))


def openapi_operational_sources(
    spec: Mapping[str, Any],
    spec_url: str,
    title: str,
    description: str,
    config: Mapping[str, Any],
) -> list[dict[str, Any]]:
    security_schemes = (spec.get("components") or {}).get("securitySchemes") or spec.get("securityDefinitions") or {}
    global_security = spec.get("security") or []
    info = spec.get("info") if isinstance(spec.get("info"), Mapping) else {}
    license_info = info.get("license") if isinstance(info.get("license"), Mapping) else {}
    license_text = f"{license_info.get('name') or ''} {license_info.get('url') or ''}"
    license_value = license_state(license_text, config)
    sources: list[dict[str, Any]] = []
    for base in api_base_urls(spec)[:3]:
        for path, path_row in (spec.get("paths") or {}).items():
            if len(sources) >= 3:
                break
            if not isinstance(path_row, Mapping) or "{" in str(path):
                continue
            operation = path_row.get("get")
            if not isinstance(operation, Mapping) or required_parameters(path_row, operation):
                continue
            operation_security = operation.get("security", global_security)
            requires_auth = bool(operation_security) or bool(security_schemes and operation_security is None)
            if requires_auth:
                continue
            url = safe_https_url(base.rstrip("/") + "/" + str(path).lstrip("/"))
            if not url:
                continue
            summary = str(operation.get("summary") or operation.get("operationId") or path)
            row = new_source(
                url,
                f"{title}: {summary}",
                description,
                "apis.guru",
                "safe zero-parameter GET extracted from OpenAPI",
                config,
                source_type="rest_api",
                auth="none",
                license_value=license_value,
                catalog_url=spec_url,
            )
            if row:
                sources.append(row)
    return sources


def apis_guru(config: Mapping[str, Any], cursor: int) -> tuple[list[dict[str, Any]], int, list[str]]:
    index = request_json("https://api.apis.guru/v2/list.json", max_bytes=12_000_000)
    services = sorted(index.items())
    if not services:
        return [], cursor, []
    batch = min(int(config.get("apis_guru_batch_size") or 120), len(services))
    found: list[dict[str, Any]] = []
    errors: list[str] = []
    for offset in range(batch):
        name, service = services[(cursor + offset) % len(services)]
        versions = service.get("versions") or {}
        if not versions:
            continue
        item = versions[sorted(versions)[-1]]
        info = item.get("info") or {}
        title = str(info.get("title") or name)
        description = str(info.get("description") or "")
        spec_url = safe_https_url(item.get("swaggerUrl") or item.get("swaggerYamlUrl"))
        if not spec_url or not spec_url.casefold().endswith(".json"):
            continue
        catalog_row = new_source(
            spec_url,
            title,
            description,
            "apis.guru",
            "rotating OpenAPI catalog",
            config,
            source_type="openapi_catalog",
            auth="metadata_only",
            catalog_url=spec_url,
        )
        if catalog_row:
            catalog_row.update(status="catalog_reference", integration_mode="metadata_only")
            found.append(catalog_row)
        try:
            spec = request_json(spec_url, max_bytes=3_000_000)
            if isinstance(spec, Mapping):
                found.extend(openapi_operational_sources(spec, spec_url, title, description, config))
        except Exception as exc:
            errors.append(f"apis.guru spec {name}: {type(exc).__name__}: {str(exc)[:140]}")
    return found, (cursor + batch) % len(services), errors


def search(engine: str, query: str, token: str) -> list[Mapping[str, Any]]:
    if engine == "github":
        compact = " ".join(re.findall(r"[A-Za-z0-9_-]+", query))[:140]
        params = urllib.parse.urlencode({"q": f"{compact} api data", "sort": "updated", "order": "desc", "per_page": 10})
        data = request_json(
            "https://api.github.com/search/repositories?" + params,
            headers={"Authorization": f"Bearer {token}", "X-GitHub-Api-Version": "2022-11-28"},
        )
    elif engine == "tavily":
        data = request_json(
            "https://api.tavily.com/search",
            "POST",
            {"api_key": token, "query": query, "search_depth": "advanced", "max_results": 8, "include_answer": False, "include_raw_content": False},
        )
    else:
        data = request_json(
            "https://api.exa.ai/search",
            "POST",
            {"query": query, "numResults": 8, "type": "auto", "contents": {"text": {"maxCharacters": 800}}},
            {"x-api-key": token},
        )
    return list(data.get("items") or data.get("results") or [])


def extract_search_results(
    engine: str,
    query: str,
    items: Iterable[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items:
        title = str(item.get("title") or item.get("name") or item.get("full_name") or "")
        text = str(item.get("content") or item.get("text") or item.get("description") or "")
        urls = [str(item[key]) for key in ("url", "html_url", "homepage") if item.get(key)] + URL_RE.findall(text)
        for url in urls[:6]:
            row = new_source(url, title, text, engine, query, config)
            if row:
                rows.append(row)
    return rows


def merge(existing: dict[str, dict[str, Any]], incoming: Iterable[dict[str, Any]]) -> None:
    for row in incoming:
        old = existing.get(row["source_id"])
        if not old:
            existing[row["source_id"]] = row
            continue
        old["last_seen_at"] = row["last_seen_at"]
        old["trusted_domain"] = bool(old.get("trusted_domain") or row.get("trusted_domain"))
        old["high_value"] = bool(old.get("high_value") or row.get("high_value"))
        if old.get("source_type") == "openapi_catalog" or row.get("source_type") == "openapi_catalog":
            old.update(status="catalog_reference", integration_mode="metadata_only", auth="metadata_only", source_type="openapi_catalog")


def decide(row: dict[str, Any], config: Mapping[str, Any]) -> None:
    if row.get("source_type") == "openapi_catalog" or urllib.parse.urlsplit(str(row.get("url") or "")).hostname == "api.apis.guru":
        row.update(status="catalog_reference", integration_mode="metadata_only", auth="metadata_only")
        row["score"] = score(row)
        return
    row["score"] = score(row)
    probe_data = row.get("probe") or {}
    eligible = (
        row["score"] >= int(config.get("auto_integrate_score") or 72)
        and row.get("trusted_domain")
        and row.get("auth") == "none"
        and row.get("license") != "prohibited"
        and probe_data.get("ok")
        and (probe_data.get("machine_readable") or row.get("source_type") == "web_read")
        and row.get("source_type") in set(config.get("allowed_source_types") or [])
    )
    if eligible:
        row.update(
            status="integrated",
            integration_mode="fixed-url-read-only-registry",
            integrated_at=row.get("integrated_at") or utc_now(),
        )
    elif row.get("auth") == "required" and row.get("high_value") and row["score"] >= int(config.get("key_notification_score") or 78):
        row.update(status="key_required_high_value", integration_mode="notification_only")
    else:
        row.update(status="candidate", integration_mode="manual_or_future_validation")


def notify_keyed(rows: list[dict[str, Any]], report_url: str) -> tuple[str, str]:
    if not rows:
        return "none", "no new key-required candidates"
    key = str(os.getenv("SERVERCHAN_SENDKEY") or os.getenv("SERVERCHAN_KEY") or os.getenv("SCKEY") or "").strip()
    failure = "Server酱 SendKey is not configured"
    if key:
        try:
            description = "\n".join(f"- **{row['title']}**（{row['score']}分）\n  {row['url']}" for row in rows[:20])
            if report_url:
                description += f"\n\n完整报告：{report_url}"
            data = urllib.parse.urlencode({"title": f"情报中心发现 {len(rows)} 个高价值需 Key 来源", "desp": description}).encode("utf-8")
            request = urllib.request.Request(
                f"https://sctapi.ftqq.com/{urllib.parse.quote(key, safe='')}.send",
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": UA},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=20) as response:
                result = json.loads(response.read(100_000).decode("utf-8", errors="replace"))
                if result.get("code") == 0:
                    return "serverchan", "Server酱 delivered"
                failure = "Server酱 returned non-zero code"
        except Exception as exc:
            failure = f"Server酱 failed: {type(exc).__name__}"
    token = str(os.getenv("GITHUB_TOKEN") or "")
    repository = str(os.getenv("GITHUB_REPOSITORY") or "")
    if token and "/" in repository:
        try:
            headers = {"Authorization": f"Bearer {token}", "X-GitHub-Api-Version": "2022-11-28"}
            body = failure + "\n\n" + "\n".join(f"- **{row['title']}** | {row['score']}分 | {row['url']}" for row in rows[:30])
            query = urllib.parse.urlencode({"q": f'repo:{repository} is:issue is:open in:title "[source-discovery-key]"', "per_page": 1})
            found = request_json("https://api.github.com/search/issues?" + query, headers=headers)
            items = found.get("items") or []
            if items:
                request_json(f"https://api.github.com/repos/{repository}/issues/{items[0]['number']}/comments", "POST", {"body": body}, headers)
            else:
                request_json(
                    f"https://api.github.com/repos/{repository}/issues",
                    "POST",
                    {"title": f"[source-discovery-key] {datetime.now(timezone.utc).date()} 高价值需 Key 来源", "body": body},
                    headers,
                )
            return "github_issue", failure + "; GitHub issue fallback recorded"
        except Exception as exc:
            return "failed", failure + f"; issue fallback failed: {type(exc).__name__}"
    return "failed", failure


def run(args: argparse.Namespace) -> int:
    config = load(args.config, {})
    registry_doc = load(args.registry, {"sources": []})
    candidates_doc = load(args.candidates, {"candidates": []})
    state = load(args.state, {"query_cursor": 0, "apis_guru_cursor": 0, "runs": 0})
    rows = {
        row["source_id"]: dict(row)
        for row in list(registry_doc.get("sources") or []) + list(candidates_doc.get("candidates") or [])
        if isinstance(row, Mapping) and row.get("source_id")
    }
    for row in rows.values():
        if urllib.parse.urlsplit(str(row.get("url") or "")).hostname == "api.apis.guru":
            row.update(status="catalog_reference", integration_mode="metadata_only", auth="metadata_only", source_type="openapi_catalog")

    queries, next_query_cursor = query_set(
        config,
        int(state.get("query_cursor") or 0),
        args.max_queries or int(config.get("daily_query_limit") or 24),
        countries(config, args.offline),
    )
    found: list[dict[str, Any]] = []
    errors: list[str] = []
    next_api_cursor = int(state.get("apis_guru_cursor") or 0)
    engine_counts = {"github": 0, "tavily": 0, "exa": 0}

    if not args.offline:
        try:
            catalog_rows, next_api_cursor, catalog_errors = apis_guru(config, next_api_cursor)
            found.extend(catalog_rows)
            errors.extend(catalog_errors)
        except Exception as exc:
            errors.append(f"apis.guru: {type(exc).__name__}: {str(exc)[:180]}")

        tokens = {
            "github": str(os.getenv("GITHUB_TOKEN") or ""),
            "tavily": str(os.getenv("TAVILY_API_KEY") or ""),
            "exa": str(os.getenv("EXA_API_KEY") or ""),
        }
        limits = {"github": min(4, len(queries)), "tavily": min(8, len(queries)), "exa": min(8, len(queries))}
        for index, query in enumerate(queries):
            for engine, token in tokens.items():
                selected = (
                    token
                    and engine_counts[engine] < limits[engine]
                    and (engine != "tavily" or index % 3 == 0)
                    and (engine != "exa" or index % 3 == 1)
                    and (engine != "github" or index % 6 == 2)
                )
                if not selected:
                    continue
                engine_counts[engine] += 1
                try:
                    found.extend(extract_search_results(engine, query, search(engine, query, token), config))
                    if engine == "github":
                        time.sleep(1)
                except Exception as exc:
                    errors.append(f"{engine}: {type(exc).__name__}: {str(exc)[:160]}")

    merge(rows, found[: int(config.get("max_new_candidates_per_run") or 500)])
    probed = 0
    if not args.offline:
        probe_limit = int(config.get("max_probe_count_per_run") or 80)
        eligible_for_probe = sorted(
            (
                row for row in rows.values()
                if row.get("source_type") != "openapi_catalog"
                and row.get("license") != "prohibited"
                and not (row.get("source_type") == "remote_mcp" and not row.get("trusted_domain"))
            ),
            key=lambda row: ((row.get("probe") or {}).get("checked_at") is not None, -int(row.get("score") or 0)),
        )
        for row in eligible_for_probe[:probe_limit]:
            probe(row)
            probed += 1

    for row in rows.values():
        decide(row, config)

    registry = sorted((row for row in rows.values() if row.get("status") == "integrated"), key=lambda row: row["source_id"])
    candidates = sorted((row for row in rows.values() if row.get("status") != "integrated"), key=lambda row: (-int(row.get("score") or 0), row["source_id"]))
    new_keyed = [
        row for row in candidates
        if row.get("status") == "key_required_high_value" and not row.get("serverchan_notified_at")
    ]
    channel, notification_reason = notify_keyed(new_keyed, str(os.getenv("DISCOVERY_REPORT_URL") or ""))
    if channel == "serverchan":
        for row in new_keyed:
            row["serverchan_notified_at"] = utc_now()
    elif channel == "github_issue":
        for row in new_keyed:
            row["github_issue_notified_at"] = utc_now()

    finished = utc_now()
    save(args.registry, {"schema_version": "global-source-registry-v2", "updated_at": finished, "source_count": len(registry), "sources": registry})
    save(args.candidates, {"schema_version": "global-source-candidates-v2", "updated_at": finished, "candidate_count": len(candidates), "candidates": candidates})
    state.update(
        schema_version="global-source-discovery-state-v2",
        query_cursor=next_query_cursor,
        apis_guru_cursor=next_api_cursor,
        runs=int(state.get("runs") or 0) + 1,
        last_run_at=finished,
        last_errors=errors[-50:],
        last_engine_counts=engine_counts,
    )
    save(args.state, state)

    catalog_count = sum(1 for row in candidates if row.get("status") == "catalog_reference")
    keyed_count = sum(1 for row in candidates if row.get("status") == "key_required_high_value")
    lines = [
        "# 全球来源自动发现日报",
        "",
        f"- 运行时间：{finished}",
        f"- 轮换查询数：{len(queries)}",
        f"- 本轮原始发现：{len(found)}",
        f"- 本轮安全探测：{probed}",
        f"- 可直接取数的自动接入：{len(registry)}",
        f"- OpenAPI目录参考：{catalog_count}",
        f"- 高价值需 Key：{keyed_count}",
        f"- 本轮通知渠道：{channel}",
        f"- 非阻断错误：{len(errors)}",
        "",
        "自动接入只统计真实数据端点，不再把 APIs.guru 的 OpenAPI 说明文件计为可取数接口。只有固定 HTTPS、只读、无需 Key、可信机构域名、条款未禁止且有界探测通过的真实端点进入执行注册表。",
    ]
    if registry:
        lines += ["", "## 可直接取数的自动接入", ""] + [
            f"- `{row['source_id']}` | {row['source_type']} | {row['score']} | {row['title']} | {row['url']}"
            for row in registry[-25:]
        ]
    if new_keyed:
        lines += ["", "## 本轮新增高价值需 Key", ""] + [
            f"- {row['score']} | {row['title']} | {row['url']}" for row in new_keyed[:25]
        ]
    if errors:
        lines += ["", "## 非阻断错误", ""] + [f"- {item}" for item in errors[:20]]
    args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": "completed",
        "queries": len(queries),
        "discovered": len(found),
        "probed": probed,
        "integrated_operational": len(registry),
        "catalog_references": catalog_count,
        "candidates": len(candidates),
        "keyed": keyed_count,
        "notification": {"channel": channel, "reason": notification_reason},
        "engine_counts": engine_counts,
        "errors": errors,
    }, ensure_ascii=False))
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    for name in ("config", "registry", "candidates", "state", "report"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--max-queries", type=int, default=0)
    parser.add_argument("--offline", action="store_true")
    return run(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
