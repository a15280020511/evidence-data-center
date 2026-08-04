from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("re3data_task", HERE / "re3data_task.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class Re3DataTests(unittest.TestCase):
    def test_catalog_and_schema_match(self) -> None:
        catalog = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
        schema = json.loads((HERE / "ticket.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        provider = catalog["providers"][0]
        operations = {row["operation_id"] for row in provider["operations"]}
        self.assertEqual(operations, set(schema["properties"]["operation"]["enum"]))
        self.assertEqual(provider["limits"]["requests_per_ticket_max"], 1)
        self.assertIs(provider["limits"]["redirects_allowed"], False)
        self.assertEqual(provider["required_secret_environment_variable"], "")

    def test_fixed_index_and_record_paths(self) -> None:
        self.assertEqual(
            MODULE.build_request("re3data-repositories", {}),
            ("https://www.re3data.org/api/v40/repositories", "index"),
        )
        self.assertEqual(
            MODULE.build_request(
                "re3data-repository", {"repository_id": "r3d100013343"}
            ),
            (
                "https://www.re3data.org/api/v40/repository/r3d100013343",
                "record",
            ),
        )

    def test_record_identifier_is_strict(self) -> None:
        for invalid in ("R3D", "r3d/../../x", "r3dabc", "https://example.com"):
            with self.assertRaises(ValueError):
                MODULE.build_request(
                    "re3data-repository", {"repository_id": invalid}
                )

    def test_xml_contracts(self) -> None:
        index = b"<list><repository><id>r3d100013343</id></repository></list>"
        root, count = MODULE.validate_xml("index", index)
        self.assertEqual(root, "list")
        self.assertEqual(count, 1)
        record = b"<r3d:repository xmlns:r3d='x'><r3d:repositoryName>Demo</r3d:repositoryName></r3d:repository>"
        root, count = MODULE.validate_xml("record", record)
        self.assertEqual(root, "repository")
        self.assertEqual(count, 1)
        with self.assertRaises(RuntimeError):
            MODULE.validate_xml("index", b"not xml")

    def test_catalog_is_local(self) -> None:
        self.assertEqual(
            MODULE.build_request("catalog-capabilities", {}),
            (None, "catalog"),
        )


if __name__ == "__main__":
    unittest.main()
