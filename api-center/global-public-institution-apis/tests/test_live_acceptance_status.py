from __future__ import annotations

import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]


class PublicInstitutionLiveAcceptanceTests(unittest.TestCase):
    def test_live_and_pending_statuses_are_explicit(self) -> None:
        matrix = json.loads((HERE / "source-access-matrix.json").read_text(encoding="utf-8"))
        rows = {row["source_id"]: row for row in matrix["sources"]}
        live = {sid for sid, row in rows.items() if row["implementation_status"] == "production-live"}
        pending = {sid for sid, row in rows.items() if row["implementation_status"] == "implemented-pending-free-secret"}
        self.assertEqual(live, {"singapore-data-gov", "australia-abs-data-api", "california-cnra-ckan", "asu-dataverse"})
        self.assertEqual(pending, {"indonesia-bps", "japan-estat", "materials-project", "india-data-gov", "brazil-dados-gov"})
        self.assertEqual(matrix["production_live_count"], len(live))
        self.assertEqual(matrix["pending_free_credential_count"], len(pending))
        for sid in live:
            self.assertEqual(rows[sid]["live_acceptance"]["status"], "PASS")
            self.assertIs(rows[sid]["live_acceptance"]["secret_values_exposed"], False)
        for sid in pending:
            acceptance = rows[sid]["live_acceptance"]
            self.assertEqual(acceptance["status"], "BLOCKED_MISSING_SECRET")
            self.assertIs(acceptance["upstream_called"], False)
            self.assertIs(acceptance["secret_values_exposed"], False)


if __name__ == "__main__":
    unittest.main()
