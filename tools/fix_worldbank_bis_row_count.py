#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"expected exactly one match in {path}, got {text.count(old)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


wb = ROOT / "api-center/worldbank-documents/worldbank_documents_task.py"
replace_once(
    wb,
    '''def count_rows(payload: Any) -> int:
    if isinstance(payload, Mapping):
        docs = payload.get("documents")
        if isinstance(docs, list): return len(docs)
        if isinstance(docs, Mapping): return len(docs)
        for key in ("total","count"):
            if isinstance(payload.get(key),int): return int(payload[key])
        return 1
    if isinstance(payload,list): return len(payload)
    return 0
''',
    '''def count_rows(payload: Any) -> int:
    if isinstance(payload, Mapping):
        docs = payload.get("documents")
        if isinstance(docs, list):
            return len(docs)
        if isinstance(docs, Mapping):
            return sum(
                1
                for key, value in docs.items()
                if key != "facets" and isinstance(value, Mapping)
            )
        for key in ("total", "count"):
            if isinstance(payload.get(key), int):
                return int(payload[key])
        return 1
    if isinstance(payload, list):
        return len(payload)
    return 0
''',
)

bis = ROOT / "api-center/bis/bis_task.py"
replace_once(
    bis,
    '''def row_count(payload:Any)->int:
    if isinstance(payload,list): return len(payload)
    if isinstance(payload,Mapping):
        for key in ("data","dataSets","series","structures"):
            value=payload.get(key)
            if isinstance(value,list): return len(value)
            if isinstance(value,Mapping): return len(value)
        return 1
    return 0
''',
    '''def row_count(payload:Any)->int:
    if isinstance(payload,list):
        return len(payload)
    if isinstance(payload,Mapping):
        data=payload.get("data")
        if isinstance(data,Mapping):
            for key in ("dataflows","dataStructures","codelists","conceptSchemes"):
                value=data.get(key)
                if isinstance(value,list):
                    return len(value)
                if isinstance(value,Mapping):
                    return len(value)
        for key in ("dataSets","series","structures"):
            value=payload.get(key)
            if isinstance(value,list):
                return len(value)
            if isinstance(value,Mapping):
                return len(value)
        return 1
    return 0
''',
)

wb_test = ROOT / "api-center/worldbank-documents/tests/test_worldbank_documents.py"
wb_test.parent.mkdir(parents=True, exist_ok=True)
wb_test.write_text('''from __future__ import annotations
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
''', encoding="utf-8")

bis_test = ROOT / "api-center/bis/tests/test_bis.py"
bis_test.parent.mkdir(parents=True, exist_ok=True)
bis_test.write_text('''from __future__ import annotations
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("bis_task", ROOT / "bis_task.py")
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class BisCountTests(unittest.TestCase):
    def test_sdmx_dataflow_count(self):
        payload = {"data": {"dataflows": [{"id": "A"}, {"id": "B"}]}}
        self.assertEqual(mod.row_count(payload), 2)

    def test_sdmx_dataset_count(self):
        payload = {"dataSets": [{"series": {"0": {}}}]}
        self.assertEqual(mod.row_count(payload), 1)


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8")

print("World Bank Documents and BIS row-count semantics corrected")
