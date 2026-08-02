from __future__ import annotations
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
