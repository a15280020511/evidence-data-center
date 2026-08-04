from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("knowledge_graph_store", ROOT / "knowledge_graph_store.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class KnowledgeGraphStoreTests(unittest.TestCase):
    def test_node_and_edge_ids_are_deterministic(self) -> None:
        a = MODULE.node(
            "Dataset", "Example", "source", "42", "https://example.org/42",
            "CC0", {"x": 1}, {"doi": ["10.1/x"]}, "2026-08-04T00:00:00Z",
        )
        b = MODULE.node(
            "Dataset", "Example", "source", "42", "https://example.org/42",
            "CC0", {"x": 1}, {"doi": ["10.1/x"]}, "2026-08-05T00:00:00Z",
        )
        self.assertEqual(a["kg_id"], b["kg_id"])
        self.assertEqual(a["content_hash"], b["content_hash"])
        ea = MODULE.edge("REGISTERED_IN", a["kg_id"], "kg:source:source", "source", "https://example.org/42", "2026-08-04T00:00:00Z")
        eb = MODULE.edge("REGISTERED_IN", b["kg_id"], "kg:source:source", "source", "https://example.org/42", "2026-08-05T00:00:00Z")
        self.assertEqual(ea["edge_id"], eb["edge_id"])

    def test_merge_replaces_by_stable_key(self) -> None:
        rows = MODULE.merge(
            [{"kg_id": "a", "name": "old"}, {"kg_id": "b", "name": "b"}],
            [{"kg_id": "a", "name": "new"}],
            "kg_id",
        )
        self.assertEqual(rows, [{"kg_id": "a", "name": "new"}, {"kg_id": "b", "name": "b"}])

    def test_all_backbone_parsers_create_graph_rows(self) -> None:
        at = "2026-08-04T00:00:00Z"
        fixtures = [
            (MODULE.parse_re3data, b"<list><repository><id>r3d1</id><name>Repo One</name><link>https://repo.example/</link></repository></list>",
             {"source_id":"re3data","max_records":10,"license":"CC0","edge_type":"REGISTERED_IN"}),
            (MODULE.parse_ols, json.dumps({"_embedded":{"ontologies":[{"ontologyId":"efo","config":{"title":"EFO"}}]}}).encode(),
             {"source_id":"ols","max_records":10,"license":"CC0","edge_type":"REGISTERED_IN"}),
            (MODULE.parse_obo, json.dumps({"@graph":[{"id":"go","title":"Gene Ontology"}]}).encode(),
             {"source_id":"obo-foundry","max_records":10,"license":"open","edge_type":"REGISTERED_IN"}),
            (MODULE.parse_optimade, json.dumps({"data":[{"id":"mp","attributes":{"name":"Materials Project","base_url":"https://example.org"}}]}).encode(),
             {"source_id":"optimade-providers","max_records":10,"license":"open","edge_type":"REGISTERED_IN"}),
            (MODULE.parse_fairsharing, b"<OAI-PMH xmlns:oai_dc='http://www.openarchives.org/OAI/2.0/oai_dc/' xmlns:dc='http://purl.org/dc/elements/1.1/'><ListRecords><record><header><identifier>oai:fairsharing_record:2521</identifier></header><metadata><oai_dc:dc><dc:title>Example Standard</dc:title><dc:type>standard</dc:type></oai_dc:dc></metadata></record><resumptionToken>next</resumptionToken></ListRecords></OAI-PMH>",
             {"source_id":"fairsharing-oai","max_records":10,"license":"CC BY-SA 4.0","edge_type":"REGISTERED_IN"}),
        ]
        for parser, raw, source in fixtures:
            with self.subTest(parser=parser.__name__):
                nodes, edges, _ = parser(raw, source, at)
                self.assertEqual(len(nodes), 1)
                self.assertEqual(len(edges), 1)
                self.assertEqual(edges[0]["target_kg_id"], MODULE.source_kg(source["source_id"]))

    def test_real_registry_contract_and_bootstrap(self) -> None:
        control = MODULE.validate()
        self.assertEqual(len(control["seeds"]), 249)
        self.assertEqual(len(control["plan"]["active_sources"]), 5)
        with tempfile.TemporaryDirectory() as tmp:
            receipt = MODULE.bootstrap(Path(tmp))
            self.assertEqual(receipt["status"], "GLOBAL_KNOWLEDGE_GRAPH_BOOTSTRAP_VALIDATED")
            self.assertEqual(receipt["registered_source_node_count"], 249)
            self.assertEqual(receipt["active_backbone_source_count"], 5)
            self.assertFalse(receipt["network_used"])
            self.assertFalse(receipt["secret_values_exposed"])
            self.assertEqual(len(list(Path(tmp).glob("*.parquet"))), 3)


if __name__ == "__main__":
    unittest.main()
