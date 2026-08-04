from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
CONNECTORS = ROOT / "connectors"
CHINA_BBOX = "53.56,73.50,18.10,134.77"


def write_json(path: Path, payload: object, *, sort_keys: bool = False) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=sort_keys) + "\n",
        encoding="utf-8",
    )


def resilience() -> dict:
    return {
        "circuit_breaker": {
            "interval": 60,
            "log_status_change": True,
            "max_errors": 3,
            "timeout": 30,
        },
        "rate_limit": {"capacity": 1, "every": "1s", "max_rate": 1},
    }


def station_rule() -> dict:
    return {
        "type": "string",
        "max_length": 119,
        "pattern": r"^CH[A-Z0-9]{9}(?:,CH[A-Z0-9]{9}){0,9}$",
    }


def date_rule() -> dict:
    return {
        "type": "string",
        "max_length": 10,
        "pattern": r"^\d{4}-\d{2}-\d{2}$",
    }


def search_connector() -> dict:
    return {
        "id": "noaa-ncei-china-station-search",
        "enabled": True,
        "endpoint": "/data/noaa/ncei/china/stations",
        "method": "GET",
        "output_encoding": "json",
        "timeout": "30s",
        "input_query_strings": [
            "dataset",
            "startDate",
            "endDate",
            "bbox",
            "dataTypes",
            "stations",
            "limit",
            "offset",
        ],
        "parameter_rules": {
            "properties": {
                "dataset": {
                    "type": "string",
                    "enum": [
                        "daily-summaries",
                        "global-summary-of-the-month",
                        "global-summary-of-the-year",
                    ],
                },
                "startDate": date_rule(),
                "endDate": date_rule(),
                "bbox": {"type": "string", "enum": [CHINA_BBOX]},
                "dataTypes": {
                    "type": "string",
                    "max_length": 1000,
                    "pattern": r"^[A-Z0-9,_-]{1,1000}$",
                },
                "stations": station_rule(),
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000},
                "offset": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 1000000,
                },
            },
            "required_any_of": [
                ["dataset"],
                ["startDate"],
                ["endDate"],
                ["bbox"],
            ],
        },
        "response_contract": {
            "any_data_paths": ["results"],
            "success_when_data_present": True,
        },
        "response_quality": {
            "collection_path": "results",
            "hard_limit": 1000,
            "recommended_action": (
                "Use the fixed China bounding box, a narrow date interval, and "
                "pagination to discover CH-prefixed Chinese stations before "
                "retrieving observations."
            ),
        },
        "backend": {
            "host": "https://www.ncei.noaa.gov",
            "url_pattern": "/access/services/search/v1/data",
            "method": "GET",
            "encoding": "json",
            "allow": [
                "results",
                "totalCount",
                "formats",
                "dataTypes",
                "stations",
                "errorMessage",
                "errorCode",
                "errors",
            ],
            "resilience": resilience(),
        },
    }


def data_connector(connector_id: str, endpoint: str, dataset: str) -> dict:
    common_fields = [
        "STATION",
        "DATE",
        "LATITUDE",
        "LONGITUDE",
        "ELEVATION",
        "NAME",
        "REPORT_TYPE",
        "SOURCE",
        "PRCP",
        "PRCP_ATTRIBUTES",
        "SNOW",
        "SNOW_ATTRIBUTES",
        "SNWD",
        "SNWD_ATTRIBUTES",
        "TAVG",
        "TAVG_ATTRIBUTES",
        "TMAX",
        "TMAX_ATTRIBUTES",
        "TMIN",
        "TMIN_ATTRIBUTES",
        "AWND",
        "AWND_ATTRIBUTES",
        "WDF2",
        "WDF5",
        "WSF2",
        "WSF5",
        "EMXT",
        "EMNT",
        "EMXP",
        "HTDD",
        "CLDD",
        "DP01",
        "DP10",
        "DX32",
        "DX70",
        "DX90",
        "DT00",
        "DT32",
        "DYFG",
        "DYTS",
        "errorMessage",
        "errorCode",
        "errors",
    ]
    return {
        "id": connector_id,
        "enabled": True,
        "endpoint": endpoint,
        "method": "GET",
        "output_encoding": "json",
        "timeout": "30s",
        "input_query_strings": [
            "dataset",
            "stations",
            "startDate",
            "endDate",
            "dataTypes",
            "format",
            "units",
            "includeAttributes",
            "includeStationName",
            "includeStationLocation",
        ],
        "parameter_rules": {
            "properties": {
                "dataset": {"type": "string", "enum": [dataset]},
                "stations": station_rule(),
                "startDate": date_rule(),
                "endDate": date_rule(),
                "dataTypes": {
                    "type": "string",
                    "max_length": 1000,
                    "pattern": r"^[A-Z0-9,_-]{1,1000}$",
                },
                "format": {"type": "string", "enum": ["json"]},
                "units": {"type": "string", "enum": ["metric"]},
                "includeAttributes": {"type": "boolean"},
                "includeStationName": {"type": "boolean"},
                "includeStationLocation": {"type": "boolean"},
            },
            "required_any_of": [
                ["dataset"],
                ["stations"],
                ["startDate"],
                ["endDate"],
                ["format"],
                ["units"],
            ],
        },
        "response_contract": {
            "any_data_paths": ["0"],
            "success_when_data_present": True,
        },
        "response_quality": {
            "collection_path": "0",
            "hard_limit": 50000,
            "recommended_action": (
                "Use one to ten CH-prefixed Chinese station IDs and a bounded "
                "date interval; split long periods into smaller tickets."
            ),
        },
        "backend": {
            "host": "https://www.ncei.noaa.gov",
            "url_pattern": "/access/services/data/v1",
            "method": "GET",
            "encoding": "json",
            "allow": common_fields,
            "resilience": resilience(),
        },
    }


def update_metadata() -> None:
    path = ROOT / "catalog-metadata.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    rows = doc["connectors"]
    for connector_id in list(rows):
        if connector_id.startswith("noaa-nws-") or connector_id == "noaa-ncei-data-search":
            del rows[connector_id]

    rows["noaa-ncei-china-station-search"] = {
        "display_name": "NOAA/NCEI 中国历史气象站点检索",
        "description": "在固定中国范围框内发现 NOAA/NCEI 的中国历史气象站点与可用数据文件。",
        "data_category": "china-historical-weather-station-discovery",
        "use_cases": [
            "中国历史气象站点发现",
            "站点编号与时间覆盖核验",
            "日月年数据下载前置检索",
        ],
        "geographic_coverage": "中国陆地区域固定范围框：53.56N,73.50E,18.10N,134.77E",
        "freshness": "随 NCEI 全球历史数据集更新；日数据持续更新，月年汇总按周期更新",
        "cost_class": "free-public-no-key",
        "limitations": [
            "仅发现中国范围内 NCEI 已收录的站点和文件，不代表中国全部国家气象站",
            "必须保留站点、日期、单位、质量标识与来源信息",
            "禁止无界全球检索和整库镜像",
        ],
        "parameter_notes": {
            "dataset": "日、月或年历史数据集",
            "bbox": f"固定中国范围框 {CHINA_BBOX}",
            "startDate": "必填；YYYY-MM-DD",
            "endDate": "必填；YYYY-MM-DD",
            "stations": "可选；CH 开头的中国站点编号，最多 10 个",
            "limit": "可选；最多 1000",
        },
        "example_parameters": {
            "dataset": "daily-summaries",
            "startDate": "2024-01-01",
            "endDate": "2024-01-31",
            "bbox": CHINA_BBOX,
            "limit": 20,
        },
    }

    for connector_id, label, dataset in [
        ("noaa-ncei-china-daily", "中国历史逐日气象观测", "daily-summaries"),
        (
            "noaa-ncei-china-monthly",
            "中国历史月度气象汇总",
            "global-summary-of-the-month",
        ),
        (
            "noaa-ncei-china-yearly",
            "中国历史年度气象汇总",
            "global-summary-of-the-year",
        ),
    ]:
        rows[connector_id] = {
            "display_name": f"NOAA/NCEI {label}",
            "description": f"按 CH 前缀中国站点编号读取 NOAA/NCEI 的{label}，仅输出 JSON 和公制单位。",
            "data_category": "china-historical-weather-climate",
            "use_cases": [
                "中国历史温度分析",
                "中国历史降水分析",
                "气候趋势与商业风险建模",
            ],
            "geographic_coverage": "仅允许 CH 前缀的中国站点编号；单票最多 10 个站点",
            "freshness": "取决于 NCEI 对相应全球数据集的更新周期",
            "cost_class": "free-public-no-key",
            "limitations": [
                "NCEI 是全球历史气象资料汇编，不等同于中国气象局完整原始站网",
                "不同站点、年代和变量的覆盖完整度不同",
                "必须检查缺测值、质量标识、站点迁移和观测制度变化",
                "长时间跨度应拆分查询，禁止批量镜像整个档案",
            ],
            "parameter_notes": {
                "dataset": f"固定为 {dataset}",
                "stations": "必填；CH 开头的中国站点编号，最多 10 个",
                "startDate": "必填；YYYY-MM-DD",
                "endDate": "必填；YYYY-MM-DD",
                "format": "固定 json",
                "units": "固定 metric",
                "dataTypes": "可选；例如 TAVG,TMAX,TMIN,PRCP",
            },
            "example_parameters": {
                "dataset": dataset,
                "stations": "CHM00054511",
                "startDate": "2024-01-01",
                "endDate": "2024-01-07",
                "dataTypes": "TAVG,TMAX,TMIN,PRCP",
                "format": "json",
                "units": "metric",
                "includeStationName": True,
                "includeStationLocation": True,
            },
        }
    write_json(path, doc)


def update_tests() -> None:
    test = '''from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CONNECTORS = ROOT / "connectors"
SCHEMA = json.loads((ROOT / "connector.schema.json").read_text(encoding="utf-8"))


class NoaaChinaHistoricalConnectorTests(unittest.TestCase):
    def load(self, connector_id: str) -> dict:
        return json.loads(
            (CONNECTORS / f"{connector_id}.connector.json").read_text(
                encoding="utf-8"
            )
        )

    def test_only_four_china_historical_noaa_connectors_exist(self) -> None:
        paths = sorted(CONNECTORS.glob("noaa-*.connector.json"))
        self.assertEqual(
            [path.stem.removesuffix(".connector") for path in paths],
            [
                "noaa-ncei-china-daily",
                "noaa-ncei-china-monthly",
                "noaa-ncei-china-station-search",
                "noaa-ncei-china-yearly",
            ],
        )
        self.assertFalse(any("nws" in path.name for path in paths))

    def test_all_connectors_validate_and_use_only_ncei(self) -> None:
        validator = Draft202012Validator(SCHEMA)
        for path in CONNECTORS.glob("noaa-*.connector.json"):
            doc = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(list(validator.iter_errors(doc)), [])
            self.assertEqual(doc["method"], "GET")
            self.assertEqual(doc["backend"]["host"], "https://www.ncei.noaa.gov")
            self.assertNotIn("secret_header", doc)
            self.assertNotIn("secret_query", doc)

    def test_station_search_is_fixed_to_china_bbox(self) -> None:
        doc = self.load("noaa-ncei-china-station-search")
        rules = doc["parameter_rules"]["properties"]
        self.assertEqual(rules["bbox"]["enum"], ["53.56,73.50,18.10,134.77"])
        self.assertEqual(
            rules["dataset"]["enum"],
            [
                "daily-summaries",
                "global-summary-of-the-month",
                "global-summary-of-the-year",
            ],
        )
        self.assertEqual(
            doc["backend"]["url_pattern"],
            "/access/services/search/v1/data",
        )

    def test_data_connectors_require_china_stations_json_and_metric(self) -> None:
        expected = {
            "noaa-ncei-china-daily": "daily-summaries",
            "noaa-ncei-china-monthly": "global-summary-of-the-month",
            "noaa-ncei-china-yearly": "global-summary-of-the-year",
        }
        for connector_id, dataset in expected.items():
            doc = self.load(connector_id)
            rules = doc["parameter_rules"]["properties"]
            self.assertEqual(rules["dataset"]["enum"], [dataset])
            self.assertEqual(rules["format"]["enum"], ["json"])
            self.assertEqual(rules["units"]["enum"], ["metric"])
            self.assertIn("^CH", rules["stations"]["pattern"])
            self.assertEqual(
                doc["backend"]["url_pattern"],
                "/access/services/data/v1",
            )


if __name__ == "__main__":
    unittest.main()
'''
    (ROOT / "tests" / "test_noaa_connectors.py").write_text(test, encoding="utf-8")

    replacements = {
        REPO / ".github" / "workflows" / "api-catalog-validate.yml": [
            ("== 75", "== 72")
        ],
        ROOT / "tests" / "test_api_catalog.py": [
            (
                'self.assertEqual(catalog["connector_count"], 75)',
                'self.assertEqual(catalog["connector_count"], 72)',
            )
        ],
        ROOT / "tests" / "test_capability_maximization.py": [
            (
                'self.assertEqual(manifest["connector_count"], 75)',
                'self.assertEqual(manifest["connector_count"], 72)',
            ),
            (
                'self.assertEqual(manifest["enabled_connector_count"], 75)',
                'self.assertEqual(manifest["enabled_connector_count"], 72)',
            ),
        ],
    }
    for path, pairs in replacements.items():
        text = path.read_text(encoding="utf-8")
        for old, new in pairs:
            if old in text:
                text = text.replace(old, new, 1)
            elif new not in text:
                raise RuntimeError(f"expected count baseline not found: {path}: {old}")
        path.write_text(text, encoding="utf-8")


def update_readme() -> None:
    text = """# NOAA/NCEI China historical-weather integration

This package intentionally excludes U.S.-only NWS forecast, observation, and alert endpoints.

It exposes four read-only China historical-data capabilities:

- discover NCEI records and CH-prefixed stations inside a fixed China bounding box;
- retrieve daily station observations from `daily-summaries`;
- retrieve monthly summaries from `global-summary-of-the-month`;
- retrieve yearly summaries from `global-summary-of-the-year`.

No NOAA key is required. Data retrieval is limited to one to ten CH-prefixed station identifiers, JSON output, metric units, fixed official HTTPS hosts, and bounded ticket execution. NCEI coverage is global-source archival coverage and is not equivalent to the complete China Meteorological Administration station network.

Official references:

- `https://www.ncei.noaa.gov/access/search/documentation/data-service/`
- `https://www.ncei.noaa.gov/access/search/documentation/search-service/`
- `https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily`
"""
    (ROOT / "noaa" / "README.md").write_text(text, encoding="utf-8")


def main() -> None:
    for path in CONNECTORS.glob("noaa-nws-*.connector.json"):
        path.unlink()
    old = CONNECTORS / "noaa-ncei-data-search.connector.json"
    if old.exists():
        old.unlink()

    docs = [
        search_connector(),
        data_connector(
            "noaa-ncei-china-daily",
            "/data/noaa/ncei/china/daily",
            "daily-summaries",
        ),
        data_connector(
            "noaa-ncei-china-monthly",
            "/data/noaa/ncei/china/monthly",
            "global-summary-of-the-month",
        ),
        data_connector(
            "noaa-ncei-china-yearly",
            "/data/noaa/ncei/china/yearly",
            "global-summary-of-the-year",
        ),
    ]
    for doc in docs:
        write_json(
            CONNECTORS / f"{doc['id']}.connector.json",
            doc,
            sort_keys=True,
        )

    update_metadata()
    update_readme()
    update_tests()
    print(json.dumps({"status": "PASS", "noaa_connectors": 4, "scope": "china-history-only"}))


if __name__ == "__main__":
    main()
