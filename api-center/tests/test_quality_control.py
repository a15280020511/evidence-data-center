import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from quality_control import classify_health, compare_sources, snapshot_metadata


class QualityControlTests(unittest.TestCase):
    def test_health(self):
        self.assertEqual(classify_health("x", 0.99, 0.99, 1)["status"], "PRODUCTION")

    def test_conflict(self):
        result = compare_sources(
            "population",
            [
                {"source_id": "a", "original_publisher": "p", "value": 100, "is_primary": True, "quality_score": 1},
                {"source_id": "b", "original_publisher": "p", "value": 101, "quality_score": 0.8},
            ],
        )
        self.assertFalse(result["merge_allowed"])

    def test_snapshot(self):
        result = snapshot_metadata(
            b"{}",
            "https://x",
            observed_at="2026-01-01T00:00:00Z",
            data_vintage="2025",
            unit="count",
            geography="CN",
            time_scope="2025",
            license="open",
        )
        self.assertEqual(len(result["response_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
