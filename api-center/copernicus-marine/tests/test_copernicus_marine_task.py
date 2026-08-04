from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "copernicus_marine_task", HERE / "copernicus_marine_task.py"
)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class FakeCatalogue:
    def model_dump(self, **_: object) -> dict[str, object]:
        return {
            "products": [
                {
                    "product_id": "P1",
                    "title": "Ocean product",
                    "description": "test",
                    "datasets": [
                        {"dataset_id": "D1", "dataset_name": "Dataset one"},
                        {"dataset_id": "D2", "dataset_name": "Dataset two"},
                    ],
                }
            ]
        }


class CopernicusMarineProviderTests(unittest.TestCase):
    def test_catalog_contract(self) -> None:
        catalog = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "copernicus-marine")
        self.assertEqual(len(provider["operations"]), 3)
        self.assertFalse(provider["limits"]["whole_dataset_get_allowed"])
        self.assertFalse(provider["limits"]["write_operations_allowed"])

    def test_describe_compacts_catalogue(self) -> None:
        fake = types.SimpleNamespace(describe=lambda **_: FakeCatalogue())
        with patch.dict(sys.modules, {"copernicusmarine": fake}):
            result = module._describe(
                {"contains": ["temperature"], "max_products": 1, "max_datasets_per_product": 1}
            )
        self.assertEqual(result["products_returned"], 1)
        self.assertEqual(result["products"][0]["datasets_returned"], 1)
        self.assertEqual(result["products"][0]["datasets_available"], 2)

    def test_bbox_and_time_are_bounded(self) -> None:
        with self.assertRaises(ValueError):
            module._bbox([-10, -10, 10, 10])
        with tempfile.TemporaryDirectory() as tmp:
            fake = types.SimpleNamespace(subset=lambda **_: None)
            with patch.dict(sys.modules, {"copernicusmarine": fake}), patch.dict(
                os.environ,
                {
                    "COPERNICUSMARINE_SERVICE_USERNAME": "user",
                    "COPERNICUSMARINE_SERVICE_PASSWORD": "password",
                },
                clear=True,
            ):
                with self.assertRaises(ValueError):
                    module._subset(
                        {
                            "dataset_id": "cmems_test_dataset",
                            "variables": ["thetao"],
                            "bbox": [119, 25, 120, 26],
                            "start_datetime": "2026-08-01T00:00:00Z",
                            "end_datetime": "2026-08-20T00:00:00Z",
                        },
                        Path(tmp),
                        1_000_000,
                        os.environ,
                    )

    def test_subset_uses_backend_credentials_and_writes_one_csv(self) -> None:
        captured: dict[str, object] = {}

        def fake_subset(**kwargs: object) -> dict[str, object]:
            captured.update(kwargs)
            target = Path(str(kwargs["output_directory"])) / str(kwargs["output_filename"])
            target.write_text("time,thetao\n2026-08-01T00:00:00Z,25.0\n", encoding="utf-8")
            return {"status": "ok"}

        fake = types.SimpleNamespace(subset=fake_subset)
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            sys.modules, {"copernicusmarine": fake}
        ):
            result, raw = module._subset(
                {
                    "dataset_id": "cmems_test_dataset",
                    "variables": ["thetao"],
                    "bbox": [119, 25, 120, 26],
                    "start_datetime": "2026-08-01T00:00:00Z",
                    "end_datetime": "2026-08-02T00:00:00Z",
                },
                Path(tmp),
                1_000_000,
                {
                    "COPERNICUSMARINE_SERVICE_USERNAME": "backend-user",
                    "COPERNICUSMARINE_SERVICE_PASSWORD": "backend-password",
                },
            )
        self.assertEqual(captured["username"], "backend-user")
        self.assertEqual(captured["password"], "backend-password")
        self.assertEqual(captured["file_format"], "csv")
        self.assertGreater(len(raw), 0)
        self.assertEqual(result["output_file"], "copernicus-marine-subset.csv")

    def test_subset_requires_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RuntimeError):
                module._subset(
                    {
                        "dataset_id": "cmems_test_dataset",
                        "variables": ["thetao"],
                        "bbox": [119, 25, 120, 26],
                        "start_datetime": "2026-08-01T00:00:00Z",
                        "end_datetime": "2026-08-02T00:00:00Z",
                    },
                    Path(tmp),
                    1_000_000,
                    {},
                )


if __name__ == "__main__":
    unittest.main()
