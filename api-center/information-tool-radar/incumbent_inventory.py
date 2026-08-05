#!/usr/bin/env python3
"""Build a deterministic inventory of tools already present in the intelligence center.

The inventory is derived from repository contracts, never from memory. It covers:
- enabled ordinary connector operations and their service families;
- managed provider/tool directories with executable or catalog contracts;
- canonical aliases, local fingerprint inputs and public locators.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse

URL_RE = re.compile(r"https://[^\s\]\[()<>\"']+", re.I)
EXCLUDED_DIRECTORIES = {
    "__pycache__", "connectors", "discovery", "information-tool-radar",
    "schemas", "tests", "testdata", "fixtures", "runtime", "scripts",
}
MARKER_NAMES = {
    "provider-catalog.json", "provider_catalog.json", "capabilities.json",
    "CAPABILITIES.json", "operations.json", "manifest.json",
}
FIELD_ALIASES = {
    "provider_id", "provider", "service_id", "service", "name", "title",
    "display_name", "package", "package_name",
}
REJECTED_LOCATOR_HOSTS = {
    "json-schema.org", "decision-system.example", "example.invalid",
    "localhost", "127.0.0.1",
}
OWN_REPOSITORY_PREFIX = "https://github.com/a15280020511/evidence-data-center"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").casefold()).strip("-")


def compact_alias(value: str) -> str:
    return re.sub(r"[^a-z0-9\u0080-\uffff]+", "", str(value or "").casefold())


def strings_from_json(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from strings_from_json(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings_from_json(item)


def canonical_locator(value: str) -> str | None:
    locator = str(value or "").strip().rstrip("`.,;:)]}")
    if not locator.startswith("https://"):
        return None
    parsed = urlparse(locator)
    host = (parsed.hostname or "").casefold().removeprefix("www.")
    if not host or host in REJECTED_LOCATOR_HOSTS or host.endswith(".invalid") or host.endswith(".example"):
        return None
    if locator.startswith(OWN_REPOSITORY_PREFIX):
        return None
    return locator[:2000]


def family_id(connector_id: str, backend_host: str) -> str:
    value = connector_id.casefold()
    prefixes = (
        "alpha-vantage", "open-meteo", "world-bank", "baidu-map",
        "newsapi", "dbnomics", "wikidata", "openstreetmap", "amap",
    )
    for prefix in prefixes:
        if value == prefix or value.startswith(prefix + "-"):
            return prefix
    host = (urlparse(backend_host).hostname or "").casefold().removeprefix("www.")
    parts = [part for part in host.split(".") if part]
    if host.endswith("open-meteo.com"):
        return "open-meteo"
    if host.endswith("worldbank.org"):
        return "world-bank"
    if host.endswith("amap.com"):
        return "amap"
    if host.endswith("baidu.com"):
        return "baidu-map"
    if host.endswith("newsapi.org"):
        return "newsapi"
    if host.endswith("db.nomics.world") or host.endswith("dbnomics.world"):
        return "dbnomics"
    if host.endswith("wikidata.org"):
        return "wikidata"
    if host.endswith("openstreetmap.org"):
        return "openstreetmap"
    if len(parts) >= 2:
        return normalized(parts[-2])
    return normalized(value.split("-", 1)[0]) or "unknown-service"


def heading_alias(readme: Path) -> str | None:
    if not readme.exists():
        return None
    try:
        for line in readme.read_text(encoding="utf-8", errors="replace").splitlines()[:40]:
            if line.startswith("# "):
                value = line[2:].strip()
                return value[:160] if value else None
    except OSError:
        return None
    return None


def top_level_aliases(data: Any) -> set[str]:
    output: set[str] = set()
    if not isinstance(data, Mapping):
        return output
    for key, value in data.items():
        if str(key).casefold() in FIELD_ALIASES and isinstance(value, str) and 1 < len(value) <= 160:
            output.add(value)
    provider = data.get("provider")
    if isinstance(provider, Mapping):
        for key, value in provider.items():
            if str(key).casefold() in FIELD_ALIASES and isinstance(value, str) and 1 < len(value) <= 160:
                output.add(value)
    return output


def extract_metadata(directory: Path, repo_root: Path) -> tuple[set[str], set[str], list[str]]:
    aliases: set[str] = {directory.name, directory.name.replace("-", " ")}
    locators: set[str] = set()
    fingerprint_paths: list[str] = []
    files = [path for path in directory.rglob("*") if path.is_file()]
    for path in files:
        relative = path.relative_to(repo_root).as_posix()
        name = path.name
        if name in MARKER_NAMES or name.endswith("_task.py") or name.endswith("_provider.py"):
            fingerprint_paths.append(relative)
        if path.suffix.casefold() == ".json" and path.stat().st_size <= 2_000_000:
            try:
                data = load_json(path)
            except (OSError, ValueError, json.JSONDecodeError):
                continue
            aliases.update(top_level_aliases(data))
            for value in strings_from_json(data):
                locator = canonical_locator(value) if isinstance(value, str) else None
                if locator:
                    locators.add(locator)
        elif name.casefold() == "readme.md" and path.stat().st_size <= 1_000_000:
            alias = heading_alias(path)
            if alias:
                aliases.add(alias)
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for match in URL_RE.findall(text):
                locator = canonical_locator(match)
                if locator:
                    locators.add(locator)
    return aliases, locators, sorted(set(fingerprint_paths))


def managed_directories(api_center: Path) -> list[Path]:
    output: list[Path] = []
    for child in sorted(api_center.iterdir(), key=lambda path: path.name.casefold()):
        if not child.is_dir() or child.name in EXCLUDED_DIRECTORIES or child.name.startswith("."):
            continue
        files = [path for path in child.rglob("*") if path.is_file()]
        if any(
            path.name in MARKER_NAMES or path.name.endswith("_task.py") or path.name.endswith("_provider.py")
            for path in files
        ):
            output.append(child)
    return output


def merge_entry(entries: dict[str, dict[str, Any]], entry: Mapping[str, Any]) -> None:
    identifier = str(entry["tool_id"])
    existing = entries.get(identifier)
    if existing is None:
        entries[identifier] = dict(entry)
        return
    for key in ("aliases", "locators", "fingerprint_paths", "source_kinds", "operation_ids"):
        existing[key] = sorted(set(existing.get(key) or []) | set(entry.get(key) or []))


def fingerprint(repo_root: Path, paths: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for value in sorted(set(paths)):
        path = repo_root / value
        digest.update(value.encode("utf-8"))
        digest.update(b"\0")
        if path.is_file():
            digest.update(path.read_bytes())
        elif path.is_dir():
            for child in sorted(item for item in path.rglob("*") if item.is_file()):
                digest.update(child.relative_to(repo_root).as_posix().encode("utf-8"))
                digest.update(b"\0")
                digest.update(child.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def build_inventory(repo_root: Path) -> dict[str, Any]:
    api_center = repo_root / "api-center"
    manifest_path = api_center / "connector-manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(manifest_path)
    manifest = load_json(manifest_path)
    connectors = manifest.get("connectors") if isinstance(manifest, Mapping) else []
    connectors = [item for item in connectors or [] if isinstance(item, Mapping) and item.get("enabled", True)]

    entries: dict[str, dict[str, Any]] = {}
    operations_by_family: dict[str, list[str]] = {}
    hosts_by_family: dict[str, set[str]] = {}
    files_by_family: dict[str, set[str]] = {}
    for connector in connectors:
        connector_id = str(connector.get("id") or "")
        backend_host = str(connector.get("backend_host") or "")
        family = family_id(connector_id, backend_host)
        operations_by_family.setdefault(family, []).append(connector_id)
        locator = canonical_locator(backend_host)
        if locator:
            hosts_by_family.setdefault(family, set()).add(locator)
        file_name = str(connector.get("file") or "")
        if file_name:
            files_by_family.setdefault(family, set()).add(f"api-center/{file_name}")

    for family, operation_ids in sorted(operations_by_family.items()):
        merge_entry(entries, {
            "tool_id": family,
            "aliases": sorted({family, family.replace("-", " ")}),
            "locators": sorted(hosts_by_family.get(family, set())),
            "fingerprint_paths": sorted(files_by_family.get(family, set()) | {"api-center/connector-manifest.json"}),
            "source_kinds": ["ordinary_connector_family"],
            "operation_ids": sorted(operation_ids),
            "enabled": True,
        })

    directories = managed_directories(api_center)
    for directory in directories:
        aliases, locators, fingerprint_paths = extract_metadata(directory, repo_root)
        identifier = normalized(directory.name)
        merge_entry(entries, {
            "tool_id": identifier,
            "aliases": sorted(alias for alias in aliases if compact_alias(alias)),
            "locators": sorted(locators),
            "fingerprint_paths": fingerprint_paths or [directory.relative_to(repo_root).as_posix()],
            "source_kinds": ["managed_tool_directory"],
            "operation_ids": [],
            "enabled": True,
        })

    tools = sorted(entries.values(), key=lambda item: str(item["tool_id"]))
    for item in tools:
        item["fingerprintable"] = bool(item.get("fingerprint_paths"))
        item["fingerprint_sha256"] = fingerprint(repo_root, item.get("fingerprint_paths") or [])
        item["externally_locatable"] = bool(item.get("locators"))

    return {
        "schema_version": "incumbent-tool-inventory-v2",
        "connector_operations": len(connectors),
        "ordinary_service_families": len(operations_by_family),
        "managed_tool_directories": len(directories),
        "tool_count": len(tools),
        "tools": tools,
    }
