#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "api-center"
PKG = API / "open-intelligence-toolkit"
REMOVED = {"sec-submissions", "sec-company-facts"}

catalog_path = PKG / "provider-catalog.json"
catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
provider = catalog["providers"][0]
provider["operations"] = [row for row in provider["operations"] if row["operation_id"] not in REMOVED]
provider["description"] = provider["description"].replace("公司、", "")
assert len(provider["operations"]) == 20
catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

schema_path = PKG / "ticket.schema.json"
schema = json.loads(schema_path.read_text(encoding="utf-8"))
schema["properties"]["operation"]["enum"] = [x for x in schema["properties"]["operation"]["enum"] if x not in REMOVED]
assert len(schema["properties"]["operation"]["enum"]) == 20
schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

matrix_path = PKG / "source-access-matrix.json"
matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
matrix["enabled_no_key_sources"] = [x for x in matrix["enabled_no_key_sources"] if x != "sec-edgar"]
conditional = [row for row in matrix["conditional_not_directly_invokable"] if row.get("id") != "sec-edgar"]
conditional.append({
    "id": "sec-edgar",
    "reason": "official data.sec.gov returned HTTP 403 from the GitHub Actions production egress even with fair-access identification headers; do not expose as a production operation"
})
matrix["conditional_not_directly_invokable"] = conditional
matrix["licence_and_use_notes"].pop("sec-edgar", None)
matrix_path.write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

runtime_path = PKG / "open_intelligence_toolkit_task.py"
runtime = runtime_path.read_text(encoding="utf-8")
start_marker = '\n elif op in {"sec-submissions","sec-company-facts"}:'
end_marker = '\n elif op=="bls-series":'
start = runtime.find(start_marker)
end = runtime.find(end_marker, start + 1)
if start < 0 or end < 0:
    raise SystemExit("SEC runtime branch markers were not found")
runtime = runtime[:start] + runtime[end:]
if "sec-submissions" in runtime or "sec-company-facts" in runtime:
    raise SystemExit("SEC runtime branches were not removed cleanly")
runtime_path.write_text(runtime, encoding="utf-8")

validator_path = PKG / "validate_open_intelligence_toolkit.py"
validator = validator_path.read_text(encoding="utf-8")
for fragment in [
    ',"sec-submissions":{"cik":"0000320193"}',
    ',"sec-company-facts":{"cik":"0000320193"}',
]:
    validator = validator.replace(fragment, "")
if "sec-submissions" in validator or "sec-company-facts" in validator:
    raise SystemExit("SEC validator samples were not removed cleanly")
validator_path.write_text(validator, encoding="utf-8")

test_path = PKG / "tests/test_open_intelligence_toolkit.py"
test = test_path.read_text(encoding="utf-8").replace("self.assertEqual(len(p[\"operations\"]),22)", "self.assertEqual(len(p[\"operations\"]),20)")
test_path.write_text(test, encoding="utf-8")

readme_path = PKG / "README.md"
readme = readme_path.read_text(encoding="utf-8").replace("22项免Key", "20项免Key")
if "SEC EDGAR已验证" not in readme:
    readme += "\nSEC EDGAR已验证为GitHub Actions生产出口HTTP 403，因此仅登记为条件能力，不作为可调用生产操作。\n"
readme_path.write_text(readme, encoding="utf-8")

build_path = API / "build_catalog_market_search.py"
build = build_path.read_text(encoding="utf-8").replace('"open-intelligence-toolkit": 22', '"open-intelligence-toolkit": 20')
build_path.write_text(build, encoding="utf-8")

api_test_path = API / "tests/test_api_catalog.py"
api_test = api_test_path.read_text(encoding="utf-8")
if '"open-intelligence-toolkit": 22' in api_test:
    api_test = api_test.replace('"open-intelligence-toolkit": 22', '"open-intelligence-toolkit": 20')
elif '"open-intelligence-toolkit": 20' not in api_test:
    api_test = api_test.replace('    "noaa-cdo": 5,\n}', '    "noaa-cdo": 5,\n    "open-intelligence-toolkit": 20,\n}')
api_test_path.write_text(api_test, encoding="utf-8")

subprocess.run(["python", "api-center/build_config.py"], cwd=ROOT, check=True)
subprocess.run(["python", "api-center/build_catalog_market_search.py"], cwd=ROOT, check=True)
aggregate = json.loads((API / "api-catalog.json").read_text(encoding="utf-8"))
assert aggregate["managed_provider_count"] == 68
assert aggregate["managed_operation_count"] == 756
print(json.dumps({"status": "PASS", "toolkit_operations": 20, "managed_operations": 756, "sec_production": False}))
