from pathlib import Path

path = Path("api-center/build_catalog_market_search.py")
text = path.read_text(encoding="utf-8")
old = '    "baidu-ai-cloud": 4,\n'
new = '    "baidu-ai-cloud": 8,\n'
if text.count(old) != 1:
    raise SystemExit(f"expected one Baidu invariant, found {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
