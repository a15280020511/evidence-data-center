from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"missing patch anchor in {path}: {old!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")

provider_dir = ROOT / "api-center/public-data-geospatial"
provider_dir.mkdir(parents=True, exist_ok=True)
parts = ROOT / ".migration/public-data-geospatial"
(provider_dir / "provider-catalog.json").write_text(
    "".join(p.read_text(encoding="utf-8") for p in sorted(parts.glob("provider.part*"))),
    encoding="utf-8",
)
(provider_dir / "public_data_geospatial_task.py").write_text(
    "".join(p.read_text(encoding="utf-8") for p in sorted(parts.glob("task.part*"))),
    encoding="utf-8",
)

build = "api-center/build_catalog_market_search.py"
replace_once(build,
    'KNOWLEDGE_TOOLS_CATALOG = HERE / "knowledge-tools/provider-catalog.json"\n',
    'KNOWLEDGE_TOOLS_CATALOG = HERE / "knowledge-tools/provider-catalog.json"\nPUBLIC_DATA_GEOSPATIAL_CATALOG = HERE / "public-data-geospatial/provider-catalog.json"\n')
replace_once(build,
    '    "llamaparse": 3,\n}',
    '    "llamaparse": 3,\n    "public-data-geospatial": 39,\n}')
replace_once(build,
    '    KNOWLEDGE_TOOLS_CATALOG,\n)',
    '    KNOWLEDGE_TOOLS_CATALOG,\n    PUBLIC_DATA_GEOSPATIAL_CATALOG,\n)')
replace_once(build,
    '        "knowledge-tools/provider-catalog.json",\n    ):',
    '        "knowledge-tools/provider-catalog.json",\n        "public-data-geospatial/provider-catalog.json",\n    ):')

test = "api-center/tests/test_api_catalog.py"
replace_once(test,
    '    "llamaparse": 3,\n}',
    '    "llamaparse": 3,\n    "public-data-geospatial": 39,\n}')
replace_once(test, 'catalog["managed_provider_count"], 47', 'catalog["managed_provider_count"], 48')
replace_once(test, 'catalog["enabled_managed_provider_count"], 47', 'catalog["enabled_managed_provider_count"], 48')
replace_once(test, 'catalog["managed_operation_count"], 487', 'catalog["managed_operation_count"], 526')

cap = "api-center/tests/test_capability_maximization.py"
replace_once(cap, '            487,\n        )', '            526,\n        )')
replace_once(cap,
    '            "llamaparse": 3,\n        }',
    '            "llamaparse": 3,\n            "public-data-geospatial": 39,\n        }')

provider_path = ROOT / "api-center/market-search/provider-catalog.json"
catalog = json.loads(provider_path.read_text(encoding="utf-8"))
changed = 0
for provider in catalog.get("providers", []):
    if provider.get("provider_id") != "serpapi":
        continue
    for operation in provider.get("operations", []):
        prop = operation.get("parameter_schema", {}).get("properties", {}).get("hl")
        if isinstance(prop, dict):
            prop["type"] = "string"
            prop["minLength"] = 2
            prop["maxLength"] = 5
            prop["pattern"] = "^[a-z]{2}(?:-[a-z]{2})?$"
            changed += 1
if not changed:
    raise SystemExit("SerpAPI hl schema was not found")
provider_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
