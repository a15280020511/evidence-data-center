#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import global_knowledge_registry as registry_mod
import global_knowledge_search as search_mod

HERE = Path(__file__).resolve().parent
REGISTRY = registry_mod.load_registry(HERE / "global-knowledge-sources.json")

FIXTURES = {
    "openlibrary.org": {"docs": [{"key": "/works/OL1W", "title": "Example Book", "author_name": ["Alice Author"], "first_publish_year": 1901, "isbn": ["123"], "public_scan_b": True, "ia": ["examplebook"]}]},
    "googleapis.com": {"items": [{"id": "GB1", "volumeInfo": {"title": "Example Book", "authors": ["Alice Author"], "publishedDate": "1901", "industryIdentifiers": [{"type": "ISBN_13", "identifier": "123"}], "infoLink": "https://books.google.example/item"}, "accessInfo": {"viewability": "ALL_PAGES", "publicDomain": True, "webReaderLink": "https://books.google.example/read"}}]},
    "crossref.org": {"message": {"items": [{"title": ["Example Paper"], "author": [{"given": "Ada", "family": "Scholar"}], "issued": {"date-parts": [[2024, 1, 1]]}, "DOI": "10.1/example", "URL": "https://doi.org/10.1/example", "type": "journal-article", "license": [{"URL": "https://creativecommons.org/licenses/by/4.0/"}]}]}},
    "datacite.org": {"data": [{"id": "10.2/example", "attributes": {"titles": [{"title": "Example Dataset"}], "creators": [{"name": "Data Author"}], "publicationYear": 2025, "doi": "10.2/example", "url": "https://example.org/dataset", "rightsList": [{"rightsIdentifier": "CC-BY-4.0"}], "types": {"resourceTypeGeneral": "Dataset"}}}]},
    "europepmc": {"resultList": {"result": [{"id": "1", "source": "MED", "title": "Example Medicine", "pubYear": "2023", "doi": "10.3/example", "pmid": "1", "pmcid": "PMC1", "isOpenAccess": "Y", "authorList": {"author": [{"fullName": "Med Author"}]}}]}},
    "semanticscholar": {"data": [{"paperId": "S2", "title": "Example AI", "year": 2026, "authors": [{"name": "AI Author"}], "url": "https://www.semanticscholar.org/paper/S2", "externalIds": {"DOI": "10.4/example", "ArXiv": "2601.00001"}, "openAccessPdf": {"url": "https://example.org/paper.pdf", "status": "GREEN"}}]},
    "zenodo": {"hits": {"hits": [{"id": 9, "created": "2025-01-01", "doi": "10.5281/zenodo.9", "metadata": {"title": "Example Record", "creators": [{"name": "Repo Author"}], "publication_date": "2025-01-01", "access_right": "open", "license": "cc-by-4.0"}, "links": {"html": "https://zenodo.org/records/9"}}]}},
    "dblp": {"result": {"hits": {"hit": [{"info": {"title": "Example CS", "authors": {"author": [{"text": "CS Author"}]}, "year": "2022", "key": "conf/x/1", "doi": "10.5/example", "url": "https://dblp.org/rec/conf/x/1", "type": "Conference and Workshop Papers", "venue": "X"}}]}}},
    "loc": {"results": [{"id": "https://www.loc.gov/item/1/", "title": "Example Archive", "date": "1910", "contributor": ["Archive Author"], "number_lccn": ["abc"], "online_format": ["image"], "rights": ["No known restrictions"]}]},
}

ARXIV_XML = b'''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry><id>https://arxiv.org/abs/2601.00001</id><updated>2026-01-01T00:00:00Z</updated><published>2026-01-01T00:00:00Z</published><title>Example Preprint</title><author><name>Preprint Author</name></author></entry>
</feed>'''


def fake_request(url: str, *, timeout: int, max_bytes: int) -> bytes:
    assert timeout > 0 and max_bytes > 0
    if "export.arxiv.org" in url:
        return ARXIV_XML
    if "openlibrary.org" in url:
        value = FIXTURES["openlibrary.org"]
    elif "googleapis.com" in url:
        value = FIXTURES["googleapis.com"]
    elif "crossref.org" in url:
        value = FIXTURES["crossref.org"]
    elif "datacite.org" in url:
        value = FIXTURES["datacite.org"]
    elif "europepmc" in url:
        value = FIXTURES["europepmc"]
    elif "semanticscholar" in url:
        value = FIXTURES["semanticscholar"]
    elif "zenodo.org" in url:
        value = FIXTURES["zenodo"]
    elif "dblp.org" in url:
        value = FIXTURES["dblp"]
    elif "loc.gov" in url:
        value = FIXTURES["loc"]
    else:
        raise AssertionError(url)
    return json.dumps(value).encode("utf-8")


def main() -> int:
    assert registry_mod.validate_registry(REGISTRY) == []
    original = search_mod.request_bytes
    search_mod.request_bytes = fake_request
    try:
        report = search_mod.run_search(REGISTRY, query="example", limit=2)
    finally:
        search_mod.request_bytes = original

    assert report["status"] == "pass", report
    assert report["source_count"] == 10
    assert report["successful_source_count"] == 10, report["sources"]
    assert report["failed_source_count"] == 0
    assert report["result_count"] == 10
    assert report["safety"]["result_files_fetched"] is False
    assert report["safety"]["shadow_sources_live_searched"] is False
    assert {row["source_id"] for row in report["results"]} == search_mod.LIVE_SOURCE_IDS

    crossref = next(row for row in report["results"] if row["source_id"] == "crossref")
    assert crossref["identifiers"]["doi"] == "10.1/example"
    assert crossref["year"] == 2024

    open_library = next(row for row in report["results"] if row["source_id"] == "open-library")
    assert open_library["provider_access"]["public_scan"] is True

    semantic = next(row for row in report["results"] if row["source_id"] == "semantic-scholar")
    assert semantic["provider_access"]["declared_open_access_pdf"].endswith("paper.pdf")

    blocked_shadow = search_mod.run_search(REGISTRY, query="example", source_ids=["annas-archive"])
    assert blocked_shadow["status"] == "blocked"
    assert any("unsupported live source ids" in error for error in blocked_shadow["errors"])

    blocked_unknown = search_mod.run_search(REGISTRY, query="example", source_ids=["unknown-source"])
    assert blocked_unknown["status"] == "blocked"

    print(json.dumps({
        "deterministic_live_source_parsers": "passed",
        "source_count": report["source_count"],
        "result_count": report["result_count"],
        "shadow_live_search_gate": "passed",
        "file_fetch_gate": "passed"
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
