from pathlib import Path

for filename in (
    "api-center/build_catalog_market_search.py",
    "api-center/tests/test_api_catalog.py",
    "api-center/tests/test_capability_maximization.py",
):
    path = Path(filename)
    text = path.read_text(encoding="utf-8")
    old = '    "baidu-ai-cloud": 4,\n'
    new = '    "baidu-ai-cloud": 8,\n'
    if text.count(old) != 1:
        raise SystemExit(f"{filename}: expected one Baidu invariant, found {text.count(old)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
