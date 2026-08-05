from __future__ import annotations

import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]


class GlobalPublicSpecializedLiveStatusTests(unittest.TestCase):
    def test_live_and_blocked_statuses_are_explicit(self) -> None:
        matrix = json.loads(
            (HERE / "source-access-matrix.json").read_text(encoding="utf-8")
        )
        rows = {row["source_id"]: row for row in matrix["sources"]}
        self.assertEqual(matrix["active_source_count"], 2)
        self.assertEqual(matrix["production_live_count"], 1)
        self.assertEqual(matrix["pending_free_credential_count"], 1)
        self.assertEqual(matrix["pending_live_acceptance_count"], 0)

        poland = rows["poland-isztar4"]
        self.assertEqual(poland["implementation_status"], "production-live")
        self.assertEqual(poland["live_acceptance"]["status"], "PASS")
        self.assertEqual(poland["live_acceptance"]["issue"], 1112)
        self.assertIs(poland["live_acceptance"]["upstream_called"], True)
        self.assertIs(poland["live_acceptance"]["secret_values_exposed"], False)

        korea = rows["korea-data-go-kr-krx-listed"]
        self.assertEqual(
            korea["implementation_status"],
            "implemented-pending-free-secret",
        )
        self.assertEqual(
            korea["live_acceptance"]["status"],
            "BLOCKED_MISSING_SECRET",
        )
        self.assertEqual(korea["live_acceptance"]["issue"], 1113)
        self.assertEqual(
            korea["live_acceptance"]["required_secret"],
            "KOREA_DATA_GO_KR_SERVICE_KEY",
        )
        self.assertIs(korea["live_acceptance"]["upstream_called"], False)
        self.assertIs(korea["live_acceptance"]["secret_values_exposed"], False)


if __name__ == "__main__":
    unittest.main()
