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
        pending_secret = {
            sid for sid, row in rows.items()
            if row["implementation_status"] == "implemented-pending-free-secret"
        }
        pending_live = {
            sid for sid, row in rows.items()
            if row["implementation_status"] == "implemented-pending-live-acceptance"
        }

        self.assertEqual(
            live,
            {"singapore-data-gov", "australia-abs-data-api", "california-cnra-ckan", "asu-dataverse"},
        )
        self.assertEqual(
            pending_secret,
            {"indonesia-bps", "japan-estat", "materials-project", "india-data-gov", "brazil-dados-gov", "korea-data-go-kr-krx-listed"},
        )
        self.assertEqual(
            pending_live,
            {"uk-api-catalogue", "poland-isztar4", "ukraine-nipo"},
        )
        self.assertEqual(matrix["active_source_count"], len(rows))
        self.assertEqual(matrix["production_live_count"], len(live))
        self.assertEqual(matrix["pending_free_credential_count"], len(pending_secret))
        self.assertEqual(matrix["pending_live_acceptance_count"], len(pending_live))

        for sid in live:
            self.assertEqual(rows[sid]["live_acceptance"]["status"], "PASS")
            self.assertIs(rows[sid]["live_acceptance"]["secret_values_exposed"], False)

        existing_blocked = pending_secret - {"korea-data-go-kr-krx-listed"}
        for sid in existing_blocked:
            acceptance = rows[sid]["live_acceptance"]
            self.assertEqual(acceptance["status"], "BLOCKED_MISSING_SECRET")
            self.assertIs(acceptance["upstream_called"], False)
            self.assertIs(acceptance["secret_values_exposed"], False)

        korea = rows["korea-data-go-kr-krx-listed"]["live_acceptance"]
        self.assertEqual(korea["status"], "NOT_RUN")
        self.assertIs(korea["upstream_called"], False)
        self.assertIs(korea["secret_values_exposed"], False)

        for sid in pending_live:
            acceptance = rows[sid]["live_acceptance"]
            self.assertEqual(acceptance["status"], "NOT_RUN")
            self.assertIs(acceptance["upstream_called"], False)
            self.assertIs(acceptance["secret_values_exposed"], False)

    def test_policy_exclusions_remain_excluded(self) -> None:
        matrix = json.loads((HERE / "source-access-matrix.json").read_text(encoding="utf-8"))
        excluded = {row["source_id"] for row in matrix["not_enabled"]}
        self.assertEqual(
            excluded,
            {"issuelab-oai", "federal-register", "uk-hmrc-customs-declarations", "brazil-inpi-general-trademark-api"},
        )


if __name__ == "__main__":
    unittest.main()
