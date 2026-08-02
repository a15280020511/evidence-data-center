from pathlib import Path

path = Path(__file__).resolve().parents[1] / "api-center/tests/test_capability_maximization.py"
text = path.read_text(encoding="utf-8")
old_count = '            522,\n'
new_count = '            544,\n'
old_provider = '            "public-data-geospatial": 35,\n        }'
new_provider = '            "public-data-geospatial": 35,\n            "cloudflare": 22,\n        }'
if text.count(old_count) != 1:
    raise SystemExit("expected exactly one old managed-operation count")
if text.count(old_provider) != 1:
    raise SystemExit("expected exactly one provider-count anchor")
path.write_text(text.replace(old_count, new_count, 1).replace(old_provider, new_provider, 1), encoding="utf-8")
