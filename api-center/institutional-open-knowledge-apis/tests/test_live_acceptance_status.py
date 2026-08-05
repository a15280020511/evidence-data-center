from __future__ import annotations

import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]


class InstitutionalKnowledgeLiveAcceptanceTests(unittest.TestCase):
    def test_live_and_blocked_statuses_are_explicit(self) -> None:
        matrix = json.loads((HERE / "source-access-matrix.json").read_text(encoding="utf-8"))
        rows = {row["source_id"]: row for row in matrix["sources"]}
        live = {sid for sid, row in rows.items() if row["implementation_status"] == "production-live"}
        blocked = {sid for sid, row in rows.items() if row["implementation_status"] == "implemented-external-timeout"}
        self.assertEqual(live, {"nasa-osdr-biodata", "japan-statistics-dashboard"})
        self.assertEqual(blocked, {"fraser-oai"})
        self.assertEqual(matrix["production_live_count"], len(live))
        for sid in live:
            self.assertEqual(rows[sid]["live_acceptance"]["status"], "PASS")
            self.assertIs(rows[sid]["live_acceptance"]["secret_values_exposed"], False)
        fraser = rows["fraser-oai"]["live_acceptance"]
        self.assertEqual(fraser["status"], "FAILED")
        self.assertIn("timeout", fraser["failure"].lower())
        self.assertIs(fraser["secret_values_exposed"], False)


if __name__ == "__main__":
    unittest.main()
