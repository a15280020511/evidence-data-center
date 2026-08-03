from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("nih_public_health_task", ROOT / "nih_public_health_task.py")
assert SPEC and SPEC.loader
task = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(task)


class FakeJsonResponse:
    ok = True
    status_code = 200
    headers = {"Content-Type": "application/json"}
    content = b'{"esearchresult":{"count":"1","idlist":["12345"]}}'

    def json(self):
        return json.loads(self.content)


class FakeXmlResponse:
    ok = True
    status_code = 200
    headers = {"Content-Type": "application/xml"}
    content = b"<PubmedArticleSet><PubmedArticle/></PubmedArticleSet>"

    def json(self):
        raise ValueError("not json")


class NihPublicHealthTests(unittest.TestCase):
    def ticket(self, operation="catalog-capabilities", parameters=None):
        return {
            "task_id": "nih-health-test-001",
            "provider": "nih-public-health",
            "operation": operation,
            "objective": "test bounded health provider",
            "parameters": parameters or {},
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "acceptance": {"timeout_seconds": 30, "max_response_bytes": 1000000},
        }

    def test_catalog_and_schema(self):
        catalog = json.loads((ROOT / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "nih-public-health")
        self.assertEqual(provider["ticket_prefix"], "[intel-nih-health]")
        self.assertEqual(len(provider["operations"]), 6)
        self.assertEqual(provider["limits"]["requests_per_ticket_max"], 1)
        self.assertFalse(provider["limits"]["arbitrary_urls_allowed"])
        self.assertFalse(provider["limits"]["write_operations_allowed"])
        task.validate_ticket(self.ticket(), schema_path=task.SCHEMA_PATH, catalog_path=task.CATALOG_PATH)

    def test_request_builders_are_fixed(self):
        url, params, kind = task.build_request("pubmed-search", {"query": "hypertension", "retmax": 5})
        self.assertEqual(url, "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi")
        self.assertEqual(params["db"], "pubmed")
        self.assertEqual(params["retmax"], 5)
        self.assertEqual(kind, "json")
        url, params, kind = task.build_request("openfda-query", {"dataset": "drug-event", "search": "patient.drug.medicinalproduct:aspirin"})
        self.assertEqual(url, "https://api.fda.gov/drug/event.json")
        self.assertEqual(kind, "json")
        with self.assertRaises(ValueError):
            task.build_request("openfda-query", {"dataset": "https://evil.test"})
        with self.assertRaises(ValueError):
            task.build_request("pubmed-fetch", {"pmids": ["1"] * 51})

    def test_local_catalog_needs_no_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            ticket = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket.write_text(json.dumps(self.ticket()), encoding="utf-8")
            self.assertEqual(task.execute(ticket, out), 0)
            diagnostics = json.loads((out / "diagnostics.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostics["status"], "INTEL_NIH_PUBLIC_HEALTH_COMPLETED")
            self.assertFalse(diagnostics["metadata"]["upstream_called"])

    def test_pubmed_search_is_one_get(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(task.requests, "get", return_value=FakeJsonResponse()) as get:
            ticket = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket.write_text(json.dumps(self.ticket("pubmed-search", {"query": "hypertension", "retmax": 1})), encoding="utf-8")
            self.assertEqual(task.execute(ticket, out), 0)
            self.assertEqual(get.call_count, 1)
            self.assertFalse(get.call_args.kwargs["allow_redirects"])
            diagnostics = json.loads((out / "diagnostics.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostics["status"], "INTEL_NIH_PUBLIC_HEALTH_COMPLETED")
            self.assertEqual(diagnostics["metadata"]["row_count"], 1)

    def test_pubmed_fetch_preserves_xml(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(task.requests, "get", return_value=FakeXmlResponse()) as get:
            ticket = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket.write_text(json.dumps(self.ticket("pubmed-fetch", {"pmids": ["12345"]})), encoding="utf-8")
            self.assertEqual(task.execute(ticket, out), 0)
            self.assertEqual(get.call_count, 1)
            self.assertTrue((out / "response.xml").is_file())


if __name__ == "__main__":
    unittest.main()
