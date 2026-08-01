#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "api-center/xweather/provider-catalog.json"
TEST = ROOT / "api-center/xweather/tests/test_xweather_task.py"
LIVE = ROOT / ".github/scripts/live_smoke_xweather_alphafeed.py"

catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
provider = catalog["providers"][0]
operation = next(row for row in provider["operations"] if row["operation_id"] == "observations-summary")
operation["parameters"] = ["location", "from", "to", "plimit", "fields"]
properties = operation["parameter_schema"]["properties"]
properties.pop("limit", None)
properties["plimit"] = {"type": "integer", "minimum": 1, "maximum": 30}
CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

test_text = TEST.read_text(encoding="utf-8")
marker = "    def test_schema_rejects_path_escape(self):\n"
addition = '''    def test_history_summary_uses_plimit_for_daily_periods(self):
        url, query, _ = task.build_request(
            "observations-summary",
            {
                "location": "fuzhou,fujian,china",
                "from": "2026-07-25",
                "to": "2026-07-31",
                "plimit": 7,
            },
        )
        self.assertEqual(
            url,
            "https://data.api.xweather.com/observations/summary/fuzhou,fujian,china",
        )
        self.assertEqual(
            query,
            {"from": "2026-07-25", "to": "2026-07-31", "plimit": "7"},
        )

'''
if addition not in test_text:
    if marker not in test_text:
        raise SystemExit("test insertion marker not found")
    test_text = test_text.replace(marker, addition + marker, 1)
TEST.write_text(test_text, encoding="utf-8")

live_text = LIVE.read_text(encoding="utf-8")
live_text = live_text.replace(
    '"from": "2026-07-25", "to": "2026-07-31", "limit": 7',
    '"from": "2026-07-25", "to": "2026-07-31", "plimit": 7',
)
live_text = live_text.replace(
    '"from": "2011-08-02", "to": "2011-08-02", "limit": 1',
    '"from": "2011-08-02", "to": "2011-08-02", "plimit": 1',
)
live_text = live_text.replace(
    '"from": "2011-08-01", "to": "2011-08-01", "limit": 1',
    '"from": "2011-08-01", "to": "2011-08-01", "plimit": 1',
)
LIVE.write_text(live_text, encoding="utf-8")

print(json.dumps({
    "status": "PASS",
    "provider": "xweather",
    "operation": "observations-summary",
    "period_limit_parameter": "plimit",
}, ensure_ascii=False))
