#!/usr/bin/env python3
"""Production CLI and quality filter for the unified public-book search engine."""
from __future__ import annotations

import re
import urllib.parse
from typing import Any, Sequence
from xml.etree import ElementTree as ET

import public_book_search as engine


def gutenberg_ebook_id(entry_id: str, links: Sequence[ET.Element]) -> str | None:
    candidates = [entry_id]
    candidates.extend(str(link.attrib.get("href") or "") for link in links)
    for candidate in candidates:
        parsed = urllib.parse.urlparse(candidate)
        path = parsed.path or candidate
        match = re.search(r"(?:^|/)ebooks/(\d+)(?:\.opds)?(?:/|$)", path)
        if match:
            return match.group(1)
        match = re.fullmatch(
            r"(?:urn:)?(?:gutenberg:)?ebook:(\d+)", candidate.strip(), re.I
        )
        if match:
            return match.group(1)
    return None


def parse_gutenberg_opds(payload: bytes, limit: int) -> list[dict[str, Any]]:
    root = ET.fromstring(payload)
    output: list[dict[str, Any]] = []
    seen_ebook_ids: set[str] = set()
    for entry in root.findall("atom:entry", engine.ATOM_NS):
        title = " ".join(
            entry.findtext(
                "atom:title", default="", namespaces=engine.ATOM_NS
            ).split()
        )
        if not title:
            continue
        links = list(entry.findall("atom:link", engine.ATOM_NS))
        entry_id = entry.findtext(
            "atom:id", default="", namespaces=engine.ATOM_NS
        ).strip()
        ebook_id = gutenberg_ebook_id(entry_id, links)
        if not ebook_id or ebook_id in seen_ebook_ids:
            continue
        seen_ebook_ids.add(ebook_id)

        authors = [
            " ".join(
                node.findtext(
                    "atom:name", default="", namespaces=engine.ATOM_NS
                ).split()
            )
            for node in entry.findall("atom:author", engine.ATOM_NS)
        ]
        authors = [value for value in authors if value]
        readable_locations: list[dict[str, str]] = []
        available_formats: list[str] = []
        seen_locations: set[tuple[str, str]] = set()
        for link in links:
            href = str(link.attrib.get("href") or "")
            rel = str(link.attrib.get("rel") or "")
            mime = str(link.attrib.get("type") or "").split(";", 1)[0].casefold()
            safe = engine._safe_https_url(href, "gutenberg.org")
            if not safe:
                continue
            fmt = engine.BOOK_FILE_MIME_TO_FORMAT.get(mime)
            if not fmt or "acquisition" not in rel:
                continue
            if urllib.parse.urlparse(safe).path.casefold().endswith(".opds"):
                continue
            key = (fmt, safe)
            if key in seen_locations:
                continue
            seen_locations.add(key)
            available_formats.append(fmt)
            readable_locations.append(
                {
                    "format": fmt,
                    "url": safe,
                    "declared_by": "official-opds",
                }
            )

        summary = engine._clean_text(
            entry.findtext(
                "atom:summary", default="", namespaces=engine.ATOM_NS
            )
        )
        output.append(
            {
                "provider_record_id": ebook_id,
                "title": title[:500],
                "authors": authors[:20],
                "catalog_url": f"https://www.gutenberg.org/ebooks/{ebook_id}",
                "readable_locations": readable_locations[:10],
                "available_formats": sorted(set(available_formats)),
                "summary": summary[:1000],
                "rights_basis": "public-domain-us",
            }
        )
        if len(output) >= limit:
            break
    return output


def install_quality_filter() -> None:
    engine.parse_gutenberg_opds = parse_gutenberg_opds


def main() -> int:
    install_quality_filter()
    return engine.main()


if __name__ == "__main__":
    raise SystemExit(main())
