from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "google_cloud_task_tests", ROOT / "google_cloud_task.py"
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class GoogleCloudTaskTests(unittest.TestCase):
    def ticket(self, provider: str = "bigquery", operation: str = "catalog-projects") -> dict:
        return {
            "task_id": "gcp-test-0001",
            "provider": provider,
            "operation": operation,
            "objective": "validate managed public-data access",
            "parameters": {},
            "data_policy": {
                "classification": "public",
                "contains_personal_data": False,
            },
            "acceptance": {
                "timeout_seconds": 30,
                "max_response_bytes": 500000,
            },
        }

    def test_catalog_exposes_all_declared_operations(self) -> None:
        catalog = module.load_json(ROOT / "provider-catalog.json")
        providers = {row["provider_id"]: row for row in catalog["providers"]}
        self.assertEqual(
            set(catalog["required_secret_environment_variables"]),
            {"GOOGLE_CLOUD_SERVICE_ACCOUNT_JSON"},
        )
        self.assertEqual(
            providers["bigquery"]["required_secret_environment_variable"],
            "GOOGLE_CLOUD_SERVICE_ACCOUNT_JSON",
        )
        self.assertEqual(
            providers["earth-engine"]["required_secret_environment_variable"],
            "GOOGLE_CLOUD_SERVICE_ACCOUNT_JSON",
        )
        self.assertEqual(
            {row["operation_id"] for row in providers["bigquery"]["operations"]},
            {
                "catalog-projects",
                "catalog-datasets",
                "catalog-tables",
                "catalog-table",
                "catalog-routines",
                "catalog-models",
                "query-readonly",
            },
        )
        self.assertEqual(
            {row["operation_id"] for row in providers["earth-engine"]["operations"]},
            {
                "catalog-capabilities",
                "catalog-dataset-root",
                "catalog-dataset-search",
                "catalog-dataset",
                "catalog-algorithms",
                "compute-value-readonly",
            },
        )
        self.assertFalse(catalog["secret_values_exposed"])

    def test_each_google_service_has_one_canonical_credential(self) -> None:
        self.assertEqual(
            module._credential_secret_name("bigquery", "catalog-projects"),
            "BIGQUERY_SERVICE_ACCOUNT_JSON",
        )
        self.assertEqual(
            module._credential_secret_name("earth-engine", "catalog-algorithms"),
            "EARTH_ENGINE_SERVICE_ACCOUNT_JSON",
        )
        self.assertEqual(
            module._credential_secret_name("earth-engine", "compute-value-readonly"),
            "EARTH_ENGINE_SERVICE_ACCOUNT_JSON",
        )
        self.assertIsNone(
            module._credential_secret_name("earth-engine", "catalog-dataset-search")
        )
        self.assertNotEqual(
            module._credential_secret_name("bigquery", "catalog-projects"),
            module._credential_secret_name("earth-engine", "catalog-algorithms"),
        )

    def test_ticket_validation_rejects_unknown_operation_or_parameter(self) -> None:
        ticket = self.ticket()
        module.validate_ticket(ticket)
        ticket["operation"] = "delete-everything"
        with self.assertRaisesRegex(ValueError, "unsupported provider operation"):
            module.validate_ticket(ticket)
        ticket = self.ticket()
        ticket["parameters"] = {"sql": "SELECT 1"}
        with self.assertRaisesRegex(ValueError, "non-allowlisted parameters"):
            module.validate_ticket(ticket)


    def test_bigquery_sql_allows_only_fully_qualified_readonly_queries(self) -> None:
        sql, projects = module._validate_readonly_sql(
            "SELECT name FROM `bigquery-public-data.usa_names.usa_1910_current` LIMIT 5"
        )
        self.assertTrue(sql.startswith("SELECT"))
        self.assertEqual(projects, {"bigquery-public-data"})
        patent_sql, patent_projects = module._validate_readonly_sql(
            "SELECT publication_number FROM `patents-public-data.patents.publications` LIMIT 1"
        )
        self.assertTrue(patent_sql.startswith("SELECT"))
        self.assertEqual(patent_projects, {"patents-public-data"})
        with self.assertRaisesRegex(ValueError, "only a single SELECT or WITH"):
            module._validate_readonly_sql("DELETE FROM `bigquery-public-data.x.y` WHERE TRUE")
        with self.assertRaisesRegex(ValueError, "fully qualified"):
            module._validate_readonly_sql("SELECT * FROM dataset.table")
        with self.assertRaisesRegex(ValueError, "non-allowlisted projects"):
            module._validate_readonly_sql("SELECT * FROM `private-project.dataset.table`")
        cte_sql, cte_projects = module._validate_readonly_sql(
            "WITH recent AS (SELECT name FROM `bigquery-public-data.usa_names.usa_1910_current`) SELECT * FROM recent"
        )
        self.assertTrue(cte_sql.startswith("WITH"))
        self.assertEqual(cte_projects, {"bigquery-public-data"})
        unnest_sql, unnest_projects = module._validate_readonly_sql(
            "SELECT item FROM UNNEST([1, 2, 3]) AS item"
        )
        self.assertTrue(unnest_sql.startswith("SELECT"))
        self.assertEqual(unnest_projects, set())
        with self.assertRaisesRegex(ValueError, "multiple SQL statements"):
            module._validate_readonly_sql("SELECT 1; SELECT 2")
        with self.assertRaisesRegex(ValueError, "forbidden"):
            module._validate_readonly_sql(
                "SELECT * FROM EXTERNAL_QUERY('connection', 'SELECT 1')"
            )

    def test_bigquery_query_dry_runs_before_execution_and_decodes_rows(self) -> None:
        responses = [
            (
                {"totalBytesProcessed": "12345"},
                {"http_status": 200},
            ),
            (
                {
                    "jobComplete": True,
                    "totalRows": "1",
                    "totalBytesProcessed": "12345",
                    "totalBytesBilled": "0",
                    "cacheHit": True,
                    "schema": {
                        "fields": [
                            {"name": "count", "type": "INTEGER"},
                            {"name": "label", "type": "STRING"},
                        ]
                    },
                    "rows": [{"f": [{"v": "7"}, {"v": "ok"}]}],
                },
                {"http_status": 200},
            ),
        ]
        with mock.patch.object(module, "_http_json", side_effect=responses) as mocked:
            result, metadata = module._bigquery_query(
                {
                    "sql": "SELECT 7 AS count, 'ok' AS label FROM `bigquery-public-data.samples.shakespeare` LIMIT 1",
                    "maximum_bytes_billed": 1000000,
                    "max_rows": 10,
                },
                "token",
                "billing-project",
                30,
            )
        self.assertEqual(mocked.call_count, 2)
        self.assertEqual(result["rows"], [{"count": 7, "label": "ok"}])
        self.assertEqual(result["estimated_bytes_processed"], 12345)
        self.assertTrue(result["cache_hit"])
        self.assertEqual(metadata["dry_run_http_status"], 200)

    def test_bigquery_query_stops_when_dry_run_exceeds_budget(self) -> None:
        with mock.patch.object(
            module,
            "_http_json",
            return_value=({"totalBytesProcessed": "2000000"}, {"http_status": 200}),
        ) as mocked:
            with self.assertRaisesRegex(RuntimeError, "above maximum_bytes_billed"):
                module._bigquery_query(
                    {
                        "sql": "SELECT * FROM `bigquery-public-data.samples.shakespeare`",
                        "maximum_bytes_billed": 1000000,
                    },
                    "token",
                    "billing-project",
                    30,
                )
        self.assertEqual(mocked.call_count, 1)

    def test_earth_engine_expression_blocks_writes_private_assets_and_urls(self) -> None:
        safe = json.dumps(
            {
                "functionInvocationValue": {
                    "functionName": "Image.reduceRegion",
                    "arguments": {
                        "image": {
                            "functionInvocationValue": {
                                "functionName": "Image.load",
                                "arguments": {
                                    "id": {"constantValue": "WorldPop/GP/100m/pop"}
                                },
                            }
                        }
                    },
                }
            }
        )
        _, audit = module._validate_ee_expression(safe)
        self.assertIn("Image.reduceRegion", audit["algorithms"])
        for function_name in ("Export.image.toDrive", "Asset.createAsset"):
            raw = json.dumps(
                {"functionInvocationValue": {"functionName": function_name, "arguments": {}}}
            )
            with self.assertRaisesRegex(ValueError, "forbidden algorithms"):
                module._validate_ee_expression(raw)
        with self.assertRaisesRegex(ValueError, "private user"):
            module._validate_ee_expression(json.dumps({"constantValue": "users/demo/private"}))
        with self.assertRaisesRegex(ValueError, "external URLs"):
            module._validate_ee_expression(json.dumps({"constantValue": "https://example.com/a"}))
        with self.assertRaisesRegex(ValueError, "non-public project"):
            module._validate_ee_expression(
                json.dumps({"constantValue": "projects/private/assets/secret"})
            )

    def test_earth_engine_public_capability_catalog_needs_no_credentials(self) -> None:
        data, metadata = module._earth_engine(
            "catalog-capabilities", {}, None, None, 30
        )
        self.assertEqual(data["provider_id"], "earth-engine")
        self.assertEqual(metadata["catalog_source"], "repository-policy")

    def test_execute_reports_blocked_when_credentials_are_missing(self) -> None:
        ticket = self.ticket()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            output_dir = root / "out"
            ticket_path.write_text(json.dumps(ticket), encoding="utf-8")
            with mock.patch.dict(os.environ, {}, clear=True):
                rc = module.execute(ticket_path, output_dir)
            self.assertEqual(rc, 1)
            snapshot = json.loads(
                (output_dir / "gcp-snapshot.json").read_text(encoding="utf-8")
            )
            self.assertEqual(snapshot["status"], "API_GCP_BLOCKED")
            diagnostics = json.loads(
                (output_dir / "gcp-diagnostics.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                diagnostics["credential_secret_name"],
                "BIGQUERY_SERVICE_ACCOUNT_JSON",
            )
            self.assertEqual(
                snapshot["failure"]["code"], "GOOGLE_CLOUD_CREDENTIALS_MISSING"
            )
            self.assertFalse(snapshot["security"]["secret_values_included"])

    def test_earth_engine_authenticated_operation_requires_its_own_secret(self) -> None:
        ticket = self.ticket("earth-engine", "catalog-algorithms")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            output_dir = root / "out"
            ticket_path.write_text(json.dumps(ticket), encoding="utf-8")
            with mock.patch.dict(os.environ, {}, clear=True):
                rc = module.execute(ticket_path, output_dir)
            self.assertEqual(rc, 1)
            snapshot = json.loads(
                (output_dir / "gcp-snapshot.json").read_text(encoding="utf-8")
            )
            diagnostics = json.loads(
                (output_dir / "gcp-diagnostics.json").read_text(encoding="utf-8")
            )
            self.assertEqual(snapshot["status"], "API_GCP_BLOCKED")
            self.assertEqual(
                diagnostics["credential_secret_name"],
                "EARTH_ENGINE_SERVICE_ACCOUNT_JSON",
            )

    def test_stac_paths_are_strictly_allowlisted(self) -> None:
        self.assertEqual(
            module._validate_stac_path("catalog/WorldPop/WorldPop_GP_100m_pop.json"),
            "catalog/WorldPop/WorldPop_GP_100m_pop.json",
        )
        for value in (
            "../secret.json",
            "catalog/../../secret.json",
            "https://example.com/catalog.json",
            "catalog/item.txt",
        ):
            with self.assertRaises(ValueError):
                module._validate_stac_path(value)


if __name__ == "__main__":
    unittest.main()
