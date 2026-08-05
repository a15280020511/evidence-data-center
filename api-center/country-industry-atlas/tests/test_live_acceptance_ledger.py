from __future__ import annotations

import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]


class CountryAtlasLiveAcceptanceLedgerTests(unittest.TestCase):
    def test_registry_is_promoted_only_as_discovery(self) -> None:
        ledger = json.loads((HERE / "live-acceptance-ledger.json").read_text(encoding="utf-8"))
        rows = ledger["production_discovery_sources"]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["source_id"], "dataportals-public-registry")
        self.assertEqual(row["operation"], "portal-registry-search")
        self.assertEqual(row["live_acceptance_issue"], 1036)
        self.assertEqual(row["live_acceptance_run"], 30975076611)
        self.assertEqual(row["live_acceptance_artifact"], 8917945192)
        self.assertEqual(row["live_acceptance_status"], "INTEL_COUNTRY_INDUSTRY_ATLAS_COMPLETED")
        self.assertEqual(row["live_acceptance_duration_ms"], 312)
        self.assertEqual(row["production_status"], "production-live-discovery")
        self.assertIs(row["secret_values_exposed"], False)
        self.assertEqual(ledger["concrete_country_apis_promoted_by_this_ledger"], [])

    def test_governance_does_not_promote_registry_entries(self) -> None:
        ledger = json.loads((HERE / "live-acceptance-ledger.json").read_text(encoding="utf-8"))
        governance = ledger["governance"]
        self.assertIs(governance["registry_discovery_source_can_be_production"], True)
        self.assertIs(governance["registry_entries_are_production_sources"], False)
        self.assertIs(governance["automatic_portal_activation_allowed"], False)
        self.assertIs(governance["automatic_api_endpoint_following_allowed"], False)
        self.assertIs(governance["independent_live_acceptance_required"], True)


if __name__ == "__main__":
    unittest.main()
