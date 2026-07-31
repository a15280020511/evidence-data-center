from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "mainland_runner_preflight",
    ROOT / "mainland_runner_preflight.py",
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class FakeResponse:
    def __init__(self, raw: bytes) -> None:
        self.raw = raw

    def read(self, size: int) -> bytes:
        return self.raw[:size]

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class MainlandRunnerPreflightTests(unittest.TestCase):
    def test_extracts_ipv4_from_chinese_reflector_text(self) -> None:
        self.assertEqual(
            module.extract_ipv4("当前 IP：1.2.3.4 来自于：中国".encode("utf-8")),
            "1.2.3.4",
        )

    def test_rejects_github_hosted_runner(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "self-hosted"):
            module.verify(
                "1.2.3.4",
                "github-hosted",
                "Linux",
                "X64",
                opener=lambda *_args, **_kwargs: FakeResponse(b"1.2.3.4"),
            )

    def test_rejects_mismatched_egress(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "does not match"):
            module.verify(
                "1.2.3.4",
                "self-hosted",
                "Linux",
                "X64",
                opener=lambda *_args, **_kwargs: FakeResponse(b"8.8.8.8"),
            )

    def test_verifies_and_stores_only_hash(self) -> None:
        result = module.verify(
            "1.2.3.4",
            "self-hosted",
            "Linux",
            "X64",
            opener=lambda *_args, **_kwargs: FakeResponse(b"1.2.3.4\n"),
        )
        self.assertTrue(result["verified"])
        self.assertEqual(len(result["public_ipv4_sha256"]), 64)
        self.assertFalse(result["raw_public_ipv4_stored"])
        self.assertNotIn("1.2.3.4", str(result))


if __name__ == "__main__":
    unittest.main()
