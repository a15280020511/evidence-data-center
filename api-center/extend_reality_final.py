#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_reality_catalog() -> None:
    path = ROOT / "reality-observation/provider-catalog.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    provider = data["providers"][0]
    limits = provider["limits"]
    secrets = limits["optional_secret_environment_variables"]
    if "MAPILLARY_ACCESS_TOKEN" not in secrets:
        secrets.append("MAPILLARY_ACCESS_TOKEN")
    hosts = limits["fixed_api_hosts"]
    if "graph.mapillary.com" not in hosts:
        hosts.append("graph.mapillary.com")
    operations = provider["operations"]
    ids = {row["operation_id"] for row in operations}
    if "mapillary-image-search" not in ids:
        operations.insert(8, {
            "operation_id": "mapillary-image-search",
            "description": "按小范围边界框检索Mapillary公开街景图像元数据和1024像素缩略图地址。",
            "parameters": ["bbox", "limit"],
            "parameter_schema": {
                "type": "object", "additionalProperties": False,
                "properties": {
                    "bbox": {"type": "array", "minItems": 4, "maxItems": 4, "items": {"type": "number", "minimum": -180, "maximum": 180}},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 25}
                },
                "required": ["bbox"]
            },
            "result_contract": {"provider": "reality-observation", "official_origin": "https://graph.mapillary.com", "http_method": "GET", "read_only": True, "credential_mode": "MAPILLARY_ACCESS_TOKEN", "content_scope": "public-image-metadata-and-thumbnail-urls"}
        })
    if "melbourne-transport-activity-latest" not in ids:
        target = next(i for i, row in enumerate(operations) if row["operation_id"] == "melbourne-pedestrian-latest")
        operations.insert(target, {
            "operation_id": "melbourne-transport-activity-latest",
            "description": "读取墨尔本AIRS五分钟分类交通活动量，区分行人、自行车、电动滑板车、汽车、公交和货车等。",
            "parameters": ["limit", "offset"],
            "parameter_schema": {
                "type": "object", "additionalProperties": False,
                "properties": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 100},
                    "offset": {"type": "integer", "minimum": 0, "maximum": 10000, "default": 0}
                }
            },
            "result_contract": {"provider": "reality-observation", "official_origin": "https://data.melbourne.vic.gov.au", "http_method": "GET", "read_only": True, "credential_mode": "none", "aggregation": "count,countin,countout by class and countline"}
        })
    write_json(path, data)


def patch_reality_schema() -> None:
    path = ROOT / "reality-observation/ticket.schema.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    enum = data["properties"]["operation"]["enum"]
    for value in ("mapillary-image-search", "melbourne-transport-activity-latest"):
        if value not in enum:
            enum.append(value)
    write_json(path, data)


def patch_reality_runtime() -> None:
    path = ROOT / "reality-observation/reality_observation_task.py"
    text = path.read_text(encoding="utf-8")
    mapillary_block = '''\n    if operation == "mapillary-image-search":\n        token = _secret("MAPILLARY_ACCESS_TOKEN", env)\n        bbox_values = _bbox(parameters)\n        if (bbox_values[2] - bbox_values[0]) > 0.2 or (bbox_values[3] - bbox_values[1]) > 0.2:\n            raise ValueError("Mapillary bbox span exceeds 0.2 degrees")\n        return {\n            "method": "GET",\n            "url": "https://graph.mapillary.com/images",\n            "safe_path": "/images",\n            "params": {\n                "bbox": ",".join(f"{value:g}" for value in bbox_values),\n                "fields": "id,captured_at,computed_geometry,computed_compass_angle,thumb_1024_url,is_pano,sequence",\n                "limit": str(\n                    bounded_int(\n                        parameters.get("limit"),\n                        default=25,\n                        minimum=1,\n                        maximum=100,\n                        name="limit",\n                    )\n                ),\n            },\n            "headers": {**base_headers, "Authorization": f"OAuth {token}"},\n            "response_kind": "json",\n            "credential_name": "MAPILLARY_ACCESS_TOKEN",\n        }\n'''
    marker = '    if operation == "kartaview-nearby-photos":\n'
    if 'if operation == "mapillary-image-search":' not in text:
        if marker not in text:
            raise SystemExit("Mapillary insertion marker missing")
        text = text.replace(marker, mapillary_block + "\n" + marker, 1)

    transport_block = '''\n    if operation == "melbourne-transport-activity-latest":\n        return {\n            "method": "GET",\n            "url": (\n                "https://data.melbourne.vic.gov.au/api/explore/v2.1/catalog/datasets/"\n                "transport-activity-counts/records"\n            ),\n            "safe_path": "/api/explore/v2.1/catalog/datasets/transport-activity-counts/records",\n            "params": {\n                "limit": str(\n                    bounded_int(\n                        parameters.get("limit"),\n                        default=100,\n                        minimum=1,\n                        maximum=100,\n                        name="limit",\n                    )\n                ),\n                "offset": str(\n                    bounded_int(\n                        parameters.get("offset"),\n                        default=0,\n                        minimum=0,\n                        maximum=10000,\n                        name="offset",\n                    )\n                ),\n                "order_by": "from desc",\n            },\n            "headers": base_headers,\n            "response_kind": "json",\n        }\n'''
    marker = '    if operation in {"melbourne-pedestrian-latest", "melbourne-pedestrian-history"}:\n'
    if 'if operation == "melbourne-transport-activity-latest":' not in text:
        if marker not in text:
            raise SystemExit("Transport insertion marker missing")
        text = text.replace(marker, transport_block + "\n" + marker, 1)

    summarize = '''\n\ndef _summarize_transport_activity(data: Any) -> Mapping[str, Any]:\n    if not isinstance(data, Mapping):\n        return {"data": data}\n    results = data.get("results")\n    if not isinstance(results, list):\n        return {"data": data}\n    by_class: dict[str, int] = {}\n    total = 0\n    countlines: set[int] = set()\n    latest = None\n    for row in results:\n        if not isinstance(row, Mapping):\n            continue\n        road_class = str(row.get("class") or "unknown")\n        try:\n            value = int(row.get("count") or 0)\n        except (TypeError, ValueError):\n            value = 0\n        total += value\n        by_class[road_class] = by_class.get(road_class, 0) + value\n        try:\n            countlines.add(int(row.get("countlineid")))\n        except (TypeError, ValueError):\n            pass\n        timestamp = row.get("from")\n        if isinstance(timestamp, str) and (latest is None or timestamp > latest):\n            latest = timestamp\n    return {\n        "record_count": len(results),\n        "countline_count": len(countlines),\n        "total_activity_count": total,\n        "activity_by_class": by_class,\n        "latest_interval_start": latest,\n        "records": results,\n        "total_count": data.get("total_count"),\n    }\n'''
    marker = '\ndef _snapshot_from_response(operation: str, kind: str, raw: bytes, response: requests.Response) -> Any:\n'
    if 'def _summarize_transport_activity' not in text:
        if marker not in text:
            raise SystemExit("Summarizer insertion marker missing")
        text = text.replace(marker, summarize + marker, 1)
    old = '        if operation == "melbourne-pedestrian-latest":\n            return _summarize_melbourne(data)\n'
    new = old + '        if operation == "melbourne-transport-activity-latest":\n            return _summarize_transport_activity(data)\n'
    if 'operation == "melbourne-transport-activity-latest"' not in text.split('def _snapshot_from_response', 1)[1]:
        if old not in text:
            raise SystemExit("Snapshot branch marker missing")
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def patch_reality_tests() -> None:
    path = ROOT / "reality-observation/tests/test_reality_observation_task.py"
    text = path.read_text(encoding="utf-8")
    text = text.replace('self.assertEqual(len(provider["operations"]), 25)', 'self.assertEqual(len(provider["operations"]), 27)')
    old = '{"FIRMS_MAP_KEY", "FINGRID_API_KEY", "ENTSOE_API_TOKEN"},'
    new = '{"FIRMS_MAP_KEY", "FINGRID_API_KEY", "ENTSOE_API_TOKEN", "MAPILLARY_ACCESS_TOKEN"},'
    text = text.replace(old, new)
    tests = '''\n    def test_mapillary_metadata_request_is_bounded(self) -> None:\n        spec = module.build_request(\n            "mapillary-image-search",\n            {"bbox": [119.25, 26.04, 119.30, 26.09], "limit": 10},\n            environ={"MAPILLARY_ACCESS_TOKEN": "secret-mapillary"},\n        )\n        self.assertEqual(spec["url"], "https://graph.mapillary.com/images")\n        self.assertEqual(spec["params"]["limit"], "10")\n        self.assertNotIn("secret-mapillary", spec["safe_path"])\n        self.assertIn("OAuth", spec["headers"]["Authorization"])\n\n    def test_transport_activity_endpoint_and_summary(self) -> None:\n        spec = module.build_request(\n            "melbourne-transport-activity-latest", {"limit": 20}, environ={}\n        )\n        self.assertIn("transport-activity-counts", spec["url"])\n        self.assertEqual(spec["params"]["order_by"], "from desc")\n        summary = module._summarize_transport_activity(\n            {\n                "results": [\n                    {"countlineid": 1, "from": "2026-08-01T00:00:00Z", "class": "Pedestrian", "count": 5},\n                    {"countlineid": 1, "from": "2026-08-01T00:05:00Z", "class": "Car", "count": 3},\n                ]\n            }\n        )\n        self.assertEqual(summary["total_activity_count"], 8)\n        self.assertEqual(summary["activity_by_class"]["Pedestrian"], 5)\n'''
    marker = '\n\nif __name__ == "__main__":\n'
    if 'test_mapillary_metadata_request_is_bounded' not in text:
        text = text.replace(marker, tests + marker, 1)
    path.write_text(text, encoding="utf-8")


def patch_reality_workflow_readme() -> None:
    path = ROOT.parent / ".github/workflows/reality-observation-api-ticket.yml"
    text = path.read_text(encoding="utf-8")
    marker = '      ENTSOE_API_TOKEN: ${{ secrets.ENTSOE_API_TOKEN }}\n'
    if 'MAPILLARY_ACCESS_TOKEN:' not in text:
        text = text.replace(marker, marker + '      MAPILLARY_ACCESS_TOKEN: ${{ secrets.MAPILLARY_ACCESS_TOKEN }}\n', 1)
    path.write_text(text, encoding="utf-8")
    readme = ROOT / "reality-observation/README.md"
    content = readme.read_text(encoding="utf-8")
    if '- `MAPILLARY_ACCESS_TOKEN`' not in content:
        content = content.rstrip() + '\n- `MAPILLARY_ACCESS_TOKEN`\n'
    readme.write_text(content, encoding="utf-8")


def patch_catalog_builder() -> None:
    path = ROOT / "build_catalog_market_search.py"
    text = path.read_text(encoding="utf-8")
    const_marker = 'REALITY_OBSERVATION_CATALOG = HERE / "reality-observation/provider-catalog.json"\n'
    if 'COPERNICUS_MARINE_CATALOG' not in text:
        text = text.replace(const_marker, const_marker + 'COPERNICUS_MARINE_CATALOG = HERE / "copernicus-marine/provider-catalog.json"\n', 1)
    text = text.replace('    "reality-observation": 25,', '    "reality-observation": 27,')
    if '    "copernicus-marine": 3,' not in text:
        text = text.replace('    "reality-observation": 27,', '    "reality-observation": 27,\n    "copernicus-marine": 3,', 1)
    tuple_marker = '    REALITY_OBSERVATION_CATALOG,\n)'
    if '    COPERNICUS_MARINE_CATALOG,\n)' not in text:
        text = text.replace(tuple_marker, '    REALITY_OBSERVATION_CATALOG,\n    COPERNICUS_MARINE_CATALOG,\n)', 1)
    reading_marker = '        "reality-observation/provider-catalog.json",\n'
    if '"copernicus-marine/provider-catalog.json"' not in text:
        text = text.replace(reading_marker, reading_marker + '        "copernicus-marine/provider-catalog.json",\n', 1)
    path.write_text(text, encoding="utf-8")


def patch_catalog_tests_and_ci() -> None:
    path = ROOT / "tests/test_api_catalog.py"
    text = path.read_text(encoding="utf-8")
    text = text.replace('    "reality-observation": 25,', '    "reality-observation": 27,')
    if '    "copernicus-marine": 3,' not in text:
        text = text.replace('    "reality-observation": 27,', '    "reality-observation": 27,\n    "copernicus-marine": 3,', 1)
    path.write_text(text, encoding="utf-8")

    ci = ROOT.parent / ".github/workflows/api-catalog-validate.yml"
    content = ci.read_text(encoding="utf-8")
    content = content.replace("              'reality-observation': 25,", "              'reality-observation': 27,\n              'copernicus-marine': 3,")
    content = content.replace("              'FIRMS_MAP_KEY', 'FINGRID_API_KEY', 'ENTSOE_API_TOKEN'", "              'FIRMS_MAP_KEY', 'FINGRID_API_KEY', 'ENTSOE_API_TOKEN', 'MAPILLARY_ACCESS_TOKEN'")
    ci.write_text(content, encoding="utf-8")


def main() -> None:
    patch_reality_catalog()
    patch_reality_schema()
    patch_reality_runtime()
    patch_reality_tests()
    patch_reality_workflow_readme()
    patch_catalog_builder()
    patch_catalog_tests_and_ci()


if __name__ == "__main__":
    main()
