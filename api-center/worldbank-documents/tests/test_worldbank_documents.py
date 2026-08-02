from __future__ import annotations
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("worldbank_documents_task", ROOT / "worldbank_documents_task.py")
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class WorldBankDocumentsCountTests(unittest.TestCase):
    def test_facets_container_is_not_counted_as_document(self):
        payload = {"documents": {"D1": {"id": "1"}, "D2": {"id": "2"}, "facets": {}}}
        self.assertEqual(mod.count_rows(payload), 2)

    def test_document_list_count(self):
        self.assertEqual(mod.count_rows({"documents": [{"id": "1"}]}), 1)


if __name__ == "__main__":
    unittest.main()
