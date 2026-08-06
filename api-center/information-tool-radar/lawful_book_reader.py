#!/usr/bin/env python3
"""Download and read lawfully accessible books under a strict rights policy.

Remote retrieval is limited to approved public-domain/open-license source hosts.
User-provided local files are accepted only with an explicit rights attestation.
The reader supports EPUB, HTML/XHTML, and plain text using Python's standard library.
It extracts table-of-contents entries, headings, chapter excerpts, and bounded body
text. It does not access Anna's Archive detail or download links.
"""
from __future__ import annotations

import argparse
import html
import io
import json
import mimetypes
import posixpath
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Any, Mapping
from xml.etree import ElementTree as ET

USER_AGENT = (
    "evidence-data-center-lawful-book-reader/1.0 "
    "(+https://github.com/a15280020511/evidence-data-center)"
)
RIGHTS_BASES = {"public-domain", "open-license", "user-provided"}
REMOTE_RIGHTS_BASES = {"public-domain", "open-license"}
SUPPORTED_FORMATS = {"epub", "html", "xhtml", "txt"}
REDIRECT_CODES = {301, 302, 303, 307, 308}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Mapping[str, str],
        newurl: str,
    ) -> None:
        return None


def build_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        NoRedirect(),
    )


def normalize_host(value: str) -> str:
    host = value.strip().casefold().rstrip(".")
    if not host or "/" in host or ":" in host or "@" in host:
        raise ValueError(f"invalid source host: {value}")
    return host


def validate_source_registry(registry: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if registry.get("schema_version") != "lawful-book-source-registry-v1":
        errors.append("unsupported schema_version")
    policy = registry.get("policy")
    if not isinstance(policy, Mapping):
        errors.append("policy missing")
        policy = {}
    required = {
        "https_required": True,
        "unknown_domains_allowed": False,
        "cross_domain_redirects_allowed": False,
        "anna_archive_downloads_allowed": False,
        "rights_attestation_required": True,
    }
    for key, expected in required.items():
        if policy.get(key) is not expected:
            errors.append(f"policy {key} must be {expected!r}")

    sources = registry.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("sources missing")
        return errors
    seen: set[str] = set()
    for item in sources:
        if not isinstance(item, Mapping):
            errors.append("invalid source entry")
            continue
        try:
            host = normalize_host(str(item.get("host") or ""))
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if host in seen:
            errors.append(f"duplicate source host: {host}")
        seen.add(host)
        if item.get("enabled") is not True:
            errors.append(f"source disabled in active registry: {host}")
        rights = set(str(value) for value in item.get("rights_bases") or [])
        if not rights or not rights.issubset(REMOTE_RIGHTS_BASES):
            errors.append(f"invalid rights bases for {host}")
        formats = set(str(value).casefold() for value in item.get("formats") or [])
        if not formats or not formats.issubset(SUPPORTED_FORMATS):
            errors.append(f"invalid formats for {host}")
        if "anna" in host or "annas-archive" in host:
            errors.append("Anna's Archive may not be a lawful download source")
    return errors


def source_for_url(registry: Mapping[str, Any], url: str) -> Mapping[str, Any]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("remote URL must use HTTPS")
    if parsed.username or parsed.password or parsed.port:
        raise ValueError("URL credentials and explicit ports are forbidden")
    host = parsed.hostname.casefold().rstrip(".")
    for item in registry.get("sources") or []:
        if not isinstance(item, Mapping) or item.get("enabled") is not True:
            continue
        configured = normalize_host(str(item.get("host") or ""))
        allow_subdomains = item.get("allow_subdomains") is True
        if host == configured or (allow_subdomains and host.endswith("." + configured)):
            return item
    raise ValueError(f"source domain is not approved: {host}")


def infer_format(name: str, content_type: str = "") -> str:
    path = urllib.parse.urlparse(name).path if "://" in name else name
    suffix = Path(path).suffix.casefold().lstrip(".")
    if suffix in {"htm", "html"}:
        return "html"
    if suffix == "xhtml":
        return "xhtml"
    if suffix in {"txt", "text"}:
        return "txt"
    if suffix == "epub":
        return "epub"
    lowered = content_type.casefold().split(";", 1)[0].strip()
    return {
        "application/epub+zip": "epub",
        "text/plain": "txt",
        "text/html": "html",
        "application/xhtml+xml": "xhtml",
    }.get(lowered, "")


def download_book(
    registry: Mapping[str, Any],
    url: str,
    rights_basis: str,
    timeout: int,
    max_bytes: int,
) -> tuple[bytes, str, str, Mapping[str, Any]]:
    source = source_for_url(registry, url)
    allowed_rights = set(str(value) for value in source.get("rights_bases") or [])
    if rights_basis not in allowed_rights:
        raise ValueError(f"rights basis {rights_basis} is not approved for this source")
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/epub+zip,text/plain,text/html,application/xhtml+xml",
            "Accept-Encoding": "identity",
            "User-Agent": USER_AGENT,
        },
        method="GET",
    )
    try:
        with build_opener().open(request, timeout=timeout) as response:
            payload = response.read(max_bytes + 1)
            if len(payload) > max_bytes:
                raise RuntimeError(f"book exceeds {max_bytes} bytes")
            content_type = response.headers.get("Content-Type", "")
            final_url = response.geturl()
    except urllib.error.HTTPError as exc:
        if int(exc.code) in REDIRECT_CODES:
            location = exc.headers.get("Location") if exc.headers else None
            target = urllib.parse.urljoin(url, location or "")
            raise RuntimeError(f"redirect blocked; review final URL separately: {target}")
        raise
    if final_url != url:
        raise RuntimeError("unexpected redirect was followed")
    fmt = infer_format(url, content_type)
    if not fmt:
        raise ValueError(f"unsupported or ambiguous content type: {content_type}")
    allowed_formats = set(str(value).casefold() for value in source.get("formats") or [])
    if fmt not in allowed_formats:
        raise ValueError(f"format {fmt} is not approved for this source")
    return payload, fmt, content_type, source


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip = 0
        self._heading_level: int | None = None
        self._heading_parts: list[str] = []
        self._parts: list[str] = []
        self.headings: list[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        folded = tag.casefold()
        if folded in {"script", "style", "noscript", "svg"}:
            self._skip += 1
            return
        if self._skip:
            return
        if folded in {"p", "div", "section", "article", "li", "br", "hr"}:
            self._parts.append("\n")
        if len(folded) == 2 and folded[0] == "h" and folded[1].isdigit():
            self._heading_level = int(folded[1])
            self._heading_parts = []
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        folded = tag.casefold()
        if folded in {"script", "style", "noscript", "svg"}:
            if self._skip:
                self._skip -= 1
            return
        if self._skip:
            return
        if len(folded) == 2 and folded[0] == "h" and folded[1].isdigit():
            title = " ".join(" ".join(self._heading_parts).split()).strip()
            if title:
                self.headings.append({"level": self._heading_level, "title": title[:300]})
            self._heading_level = None
            self._heading_parts = []
            self._parts.append("\n")
        elif folded in {"p", "div", "section", "article", "li"}:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        text = html.unescape(data)
        self._parts.append(text)
        if self._heading_level is not None:
            self._heading_parts.append(text)

    def text(self) -> str:
        value = "".join(self._parts).replace("\r", "\n")
        lines = [" ".join(line.split()) for line in value.splitlines()]
        return "\n".join(line for line in lines if line).strip()


def decode_text(payload: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "utf-16", "gb18030", "latin-1"):
        try:
            return payload.decode(encoding)
        except UnicodeDecodeError:
            continue
    return payload.decode("utf-8", errors="replace")


def parse_html(payload: bytes, max_chars: int) -> dict[str, Any]:
    parser = VisibleTextParser()
    parser.feed(decode_text(payload))
    observed = parser.text()
    text = observed[:max_chars]
    return {
        "metadata": {},
        "toc": parser.headings[:500],
        "chapters": [],
        "content_text": text,
        "content_chars_extracted": len(text),
        "content_truncated": len(observed) > max_chars,
    }


def parse_txt(payload: bytes, max_chars: int) -> dict[str, Any]:
    raw = decode_text(payload)
    normalized = "\n".join(line.rstrip() for line in raw.replace("\r\n", "\n").split("\n")).strip()
    text = normalized[:max_chars]
    toc: list[dict[str, Any]] = []
    for line in normalized.splitlines():
        stripped = line.strip()
        if re.match(r"^(chapter|book|part|section)\s+[\divxlcdm]+", stripped, re.I):
            toc.append({"level": 1, "title": stripped[:300]})
        elif re.match(r"^第[一二三四五六七八九十百千万0-9]+[章节篇部卷]", stripped):
            toc.append({"level": 1, "title": stripped[:300]})
        if len(toc) >= 500:
            break
    return {
        "metadata": {},
        "toc": toc,
        "chapters": [],
        "content_text": text,
        "content_chars_extracted": len(text),
        "content_truncated": len(normalized) > max_chars,
    }


def safe_zip_members(archive: zipfile.ZipFile) -> dict[str, zipfile.ZipInfo]:
    infos = archive.infolist()
    if len(infos) > 2000:
        raise ValueError("EPUB contains too many files")
    total = 0
    output: dict[str, zipfile.ZipInfo] = {}
    for info in infos:
        path = PurePosixPath(info.filename)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("EPUB contains an unsafe path")
        total += int(info.file_size)
        if total > 100_000_000:
            raise ValueError("EPUB uncompressed size exceeds limit")
        if info.compress_size and info.file_size / max(info.compress_size, 1) > 1000:
            raise ValueError("EPUB compression ratio is unsafe")
        output[info.filename] = info
    return output


def local_name(base_file: str, href: str) -> str:
    path = posixpath.normpath(posixpath.join(posixpath.dirname(base_file), href.split("#", 1)[0]))
    if path.startswith("../") or path == "..":
        raise ValueError("EPUB manifest path escapes archive")
    return path


def xml_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return " ".join(" ".join(element.itertext()).split()).strip()


def epub_toc_from_nav(archive: zipfile.ZipFile, nav_path: str) -> list[dict[str, Any]]:
    root = ET.fromstring(archive.read(nav_path))
    toc: list[dict[str, Any]] = []
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1].casefold() == "a":
            title = xml_text(element)
            if title:
                toc.append({"level": 1, "title": title[:300]})
                if len(toc) >= 500:
                    break
    return toc


def epub_toc_from_ncx(archive: zipfile.ZipFile, ncx_path: str) -> list[dict[str, Any]]:
    root = ET.fromstring(archive.read(ncx_path))
    toc: list[dict[str, Any]] = []
    for navpoint in root.iter():
        if navpoint.tag.rsplit("}", 1)[-1] != "navPoint":
            continue
        label = next(
            (child for child in navpoint.iter() if child.tag.rsplit("}", 1)[-1] == "text"),
            None,
        )
        title = xml_text(label)
        if title:
            toc.append({"level": 1, "title": title[:300]})
            if len(toc) >= 500:
                break
    return toc


def parse_epub(payload: bytes, max_chars: int) -> dict[str, Any]:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = safe_zip_members(archive)
        container_name = "META-INF/container.xml"
        if container_name not in members:
            raise ValueError("EPUB container.xml missing")
        container = ET.fromstring(archive.read(container_name))
        rootfile = next(
            (
                element.attrib.get("full-path")
                for element in container.iter()
                if element.tag.rsplit("}", 1)[-1] == "rootfile"
                and element.attrib.get("full-path")
            ),
            None,
        )
        if not rootfile or rootfile not in members:
            raise ValueError("EPUB package document missing")
        package = ET.fromstring(archive.read(rootfile))

        metadata: dict[str, str] = {}
        for element in package.iter():
            local = element.tag.rsplit("}", 1)[-1]
            if local in {"title", "creator", "language", "publisher", "date"}:
                value = xml_text(element)
                if value and local not in metadata:
                    metadata[local] = value[:500]

        manifest: dict[str, dict[str, str]] = {}
        for element in package.iter():
            if element.tag.rsplit("}", 1)[-1] != "item":
                continue
            item_id = element.attrib.get("id")
            href = element.attrib.get("href")
            if item_id and href:
                manifest[item_id] = {
                    "href": href,
                    "media_type": element.attrib.get("media-type", ""),
                    "properties": element.attrib.get("properties", ""),
                }

        spine_ids: list[str] = []
        spine_toc = ""
        for element in package.iter():
            local = element.tag.rsplit("}", 1)[-1]
            if local == "spine":
                spine_toc = element.attrib.get("toc", "")
            elif local == "itemref" and element.attrib.get("idref"):
                spine_ids.append(element.attrib["idref"])

        toc: list[dict[str, Any]] = []
        nav_item = next((item for item in manifest.values() if "nav" in item["properties"].split()), None)
        if nav_item:
            nav_path = local_name(rootfile, nav_item["href"])
            if nav_path in members:
                try:
                    toc = epub_toc_from_nav(archive, nav_path)
                except ET.ParseError:
                    toc = []
        if not toc:
            ncx_item = manifest.get(spine_toc) if spine_toc else None
            if ncx_item is None:
                ncx_item = next(
                    (item for item in manifest.values() if item["media_type"] == "application/x-dtbncx+xml"),
                    None,
                )
            if ncx_item:
                ncx_path = local_name(rootfile, ncx_item["href"])
                if ncx_path in members:
                    try:
                        toc = epub_toc_from_ncx(archive, ncx_path)
                    except ET.ParseError:
                        toc = []

        chapters: list[dict[str, Any]] = []
        full_parts: list[str] = []
        remaining = max_chars
        fallback_toc: list[dict[str, Any]] = []
        total_text_observed = 0
        for item_id in spine_ids[:500]:
            item = manifest.get(item_id)
            if not item or item["media_type"] not in {"application/xhtml+xml", "text/html"}:
                continue
            name = local_name(rootfile, item["href"])
            if name not in members:
                continue
            parser = VisibleTextParser()
            parser.feed(decode_text(archive.read(name)))
            chapter_text = parser.text()
            if not chapter_text:
                continue
            total_text_observed += len(chapter_text)
            fallback_toc.extend(parser.headings)
            chapters.append({
                "path": name,
                "headings": parser.headings[:20],
                "text_excerpt": chapter_text[:2000],
            })
            if remaining > 0:
                part = chapter_text[:remaining]
                full_parts.append(part)
                remaining -= len(part)
            if remaining <= 0 and len(chapters) >= 100:
                break

        content_text = "\n\n".join(full_parts)[:max_chars]
        if not toc:
            toc = fallback_toc[:500]
        return {
            "metadata": metadata,
            "toc": toc,
            "chapters": chapters[:100],
            "content_text": content_text,
            "content_chars_extracted": len(content_text),
            "content_truncated": total_text_observed > len(content_text),
        }


def parse_book(payload: bytes, fmt: str, max_chars: int) -> dict[str, Any]:
    if fmt == "epub":
        return parse_epub(payload, max_chars)
    if fmt in {"html", "xhtml"}:
        return parse_html(payload, max_chars)
    if fmt == "txt":
        return parse_txt(payload, max_chars)
    raise ValueError(f"unsupported format: {fmt}")


def run_reader(
    registry: Mapping[str, Any],
    *,
    rights_basis: str,
    rights_note: str,
    url: str | None = None,
    file_path: Path | None = None,
    timeout: int = 25,
    max_bytes: int = 25_000_000,
    max_chars: int = 150_000,
    retained_file: Path | None = None,
) -> dict[str, Any]:
    policy_errors = validate_source_registry(registry)
    if rights_basis not in RIGHTS_BASES:
        policy_errors.append("invalid rights basis")
    if len(rights_note.strip()) < 8:
        policy_errors.append("rights attestation note is required")
    if bool(url) == bool(file_path):
        policy_errors.append("provide exactly one of URL or local file")
    if url and rights_basis not in REMOTE_RIGHTS_BASES:
        policy_errors.append("remote retrieval requires public-domain or open-license basis")
    if file_path and rights_basis != "user-provided":
        policy_errors.append("local files require user-provided rights basis")
    if url:
        try:
            source_for_url(registry, url)
        except ValueError as exc:
            policy_errors.append(str(exc))
    if policy_errors:
        return {
            "schema_version": "lawful-book-reader-report-v1",
            "generated_at": utc_now(),
            "status": "blocked",
            "policy_errors": policy_errors,
            "rights_basis": rights_basis,
            "rights_note": rights_note[:500],
        }

    source_record: Mapping[str, Any] | None = None
    content_type = ""
    if url:
        payload, fmt, content_type, source_record = download_book(
            registry, url, rights_basis, timeout, max_bytes
        )
        source = url
    else:
        assert file_path is not None
        payload = file_path.read_bytes()
        if len(payload) > max_bytes:
            raise ValueError(f"book exceeds {max_bytes} bytes")
        fmt = infer_format(str(file_path), mimetypes.guess_type(str(file_path))[0] or "")
        if not fmt:
            raise ValueError("unsupported local file format")
        source = str(file_path)

    parsed = parse_book(payload, fmt, max_chars)
    retained = False
    retained_path: str | None = None
    if retained_file is not None:
        retained_file.parent.mkdir(parents=True, exist_ok=True)
        retained_file.write_bytes(payload)
        retained = True
        retained_path = str(retained_file)

    return {
        "schema_version": "lawful-book-reader-report-v1",
        "generated_at": utc_now(),
        "status": "pass",
        "rights_basis": rights_basis,
        "rights_note": rights_note[:500],
        "source": source,
        "source_host": (
            urllib.parse.urlparse(url).hostname.casefold()
            if url and urllib.parse.urlparse(url).hostname
            else None
        ),
        "source_policy": dict(source_record) if source_record else {"type": "user-provided"},
        "format": fmt,
        "content_type": content_type,
        "downloaded_bytes": len(payload),
        "file_retained": retained,
        "retained_path": retained_path,
        "metadata": parsed["metadata"],
        "toc": parsed["toc"],
        "chapters": parsed["chapters"],
        "content_text": parsed["content_text"],
        "content_chars_extracted": parsed["content_chars_extracted"],
        "content_truncated": parsed["content_truncated"],
        "safety": {
            "approved_source_required_for_remote": True,
            "rights_attestation_required": True,
            "cross_domain_redirects_followed": False,
            "anna_archive_downloads_allowed": False,
            "access_controls_bypassed": False,
            "supported_formats": sorted(SUPPORTED_FORMATS),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url")
    source.add_argument("--file", type=Path)
    parser.add_argument("--rights-basis", required=True, choices=sorted(RIGHTS_BASES))
    parser.add_argument("--rights-note", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--retain-file", type=Path)
    parser.add_argument("--timeout", type=int, default=25)
    parser.add_argument("--max-bytes", type=int, default=25_000_000)
    parser.add_argument("--max-chars", type=int, default=150_000)
    parser.add_argument("--enforce", action="store_true")
    args = parser.parse_args()

    try:
        report = run_reader(
            load_json(args.registry),
            rights_basis=args.rights_basis,
            rights_note=args.rights_note,
            url=args.url,
            file_path=args.file,
            timeout=min(max(args.timeout, 5), 60),
            max_bytes=min(max(args.max_bytes, 100_000), 50_000_000),
            max_chars=min(max(args.max_chars, 1_000), 500_000),
            retained_file=args.retain_file,
        )
    except Exception as exc:
        report = {
            "schema_version": "lawful-book-reader-report-v1",
            "generated_at": utc_now(),
            "status": "fail",
            "rights_basis": args.rights_basis,
            "rights_note": args.rights_note[:500],
            "error": f"{type(exc).__name__}: {str(exc)[:500]}",
        }
    save_json(args.output, report)
    print(json.dumps({
        "status": report.get("status"),
        "format": report.get("format"),
        "downloaded_bytes": report.get("downloaded_bytes", 0),
        "toc_entries": len(report.get("toc") or []),
        "content_chars_extracted": report.get("content_chars_extracted", 0),
        "file_retained": report.get("file_retained", False),
    }, ensure_ascii=False))
    if args.enforce and report.get("status") != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
