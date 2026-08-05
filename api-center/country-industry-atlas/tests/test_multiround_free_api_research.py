from __future__ import annotations

import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]


class MultiroundFreeApiResearchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = json.loads(
            (HERE / "multiround-free-api-research-20260805.json").read_text(encoding="utf-8")
        )

    def test_all_four_search_providers_ran_across_five_rounds(self) -> None:
        run = self.data["search_execution"]
        self.assertEqual(run["rounds"], 5)
        self.assertEqual(run["actual_upstream_searches"], 20)
        self.assertEqual(
            set(run["providers_each_round"]),
            {"tavily", "exa", "google-via-serpapi", "baidu-ai-search"},
        )
        self.assertEqual(len(run["issues"]), 20)
        self.assertEqual(run["model_calls"], 0)
        self.assertIs(run["secret_values_exposed"], False)

    def test_candidates_are_not_automatically_promoted(self) -> None:
        governance = self.data["governance"]
        self.assertIs(governance["search_result_is_production_source"], False)
        self.assertIs(governance["automatic_connector_creation_allowed"], False)
        self.assertIs(governance["independent_live_acceptance_required"], True)
        self.assertIs(governance["duplicate_connector_creation_allowed"], False)

    def test_high_value_incremental_candidates_are_recorded(self) -> None:
        direct = {row["source_id"] for row in self.data["new_direct_or_no_key_candidates"]}
        keyed = {row["source_id"] for row in self.data["new_free_key_or_application_candidates"]}
        self.assertTrue(
            {
                "brazil-dados-gov-br-api",
                "singapore-data-gov-sg",
                "issuelab-oai-pmh",
                "poland-isztar4-json",
                "us-federal-register-api",
            }.issubset(direct)
        )
        self.assertTrue(
            {
                "us-datagov-v4",
                "australia-abs-indicator-api",
                "indonesia-bps-web-api",
                "japan-estat-api",
                "materials-project-api",
            }.issubset(keyed)
        )

    def test_authorised_or_non_api_sources_are_not_misclassified(self) -> None:
        excluded = {
            row["source_id"] for row in self.data["official_data_but_not_public_general_api"]
        }
        self.assertEqual(
            excluded,
            {"brazil-inpi-trademark-register", "uk-hmrc-customs-declarations"},
        )
        self.assertIs(
            self.data["governance"]["authorised_business_data_must_not_be_classified_as_public"],
            True,
        )


if __name__ == "__main__":
    unittest.main()
