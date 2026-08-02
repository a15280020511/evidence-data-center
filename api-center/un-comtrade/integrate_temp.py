#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one match, found {count}: {old!r}")
    file.write_text(text.replace(old, new), encoding="utf-8")


def main() -> None:
    catalog_test = "api-center/tests/test_api_catalog.py"
    replace_once(
        catalog_test,
        '    "eia": 6,\n    "wolfram-alpha": 4,',
        '    "eia": 6,\n    "un-comtrade": 10,\n    "wolfram-alpha": 4,',
    )
    replace_once(
        catalog_test,
        '        self.assertEqual(catalog["managed_provider_count"], 39)',
        '        self.assertEqual(catalog["managed_provider_count"], 40)',
    )
    replace_once(
        catalog_test,
        '        self.assertEqual(catalog["enabled_managed_provider_count"], 39)',
        '        self.assertEqual(catalog["enabled_managed_provider_count"], 40)',
    )
    replace_once(
        catalog_test,
        '        self.assertEqual(catalog["managed_operation_count"], 426)',
        '        self.assertEqual(catalog["managed_operation_count"], 436)',
    )
    replace_once(
        catalog_test,
        '            "eia": "EIA_API_KEY",\n            "wolfram-alpha": "WOLFRAM_ALPHA_APP_ID",',
        '            "eia": "EIA_API_KEY",\n            "un-comtrade": "UN_COMTRADE_API_KEY",\n            "wolfram-alpha": "WOLFRAM_ALPHA_APP_ID",',
    )

    capability_test = "api-center/tests/test_capability_maximization.py"
    replace_once(capability_test, "            426,\n        )", "            436,\n        )")
    replace_once(
        capability_test,
        '            "eia": 6,\n            "wolfram-alpha": 4,',
        '            "eia": 6,\n            "un-comtrade": 10,\n            "wolfram-alpha": 4,',
    )

    workflow = ".github/workflows/api-catalog-validate.yml"
    replace_once(
        workflow,
        "            api-center/eia/requirements.txt\n\n      - name: Install isolated intelligence dependencies",
        "            api-center/eia/requirements.txt\n            api-center/un-comtrade/requirements.txt\n\n      - name: Install isolated intelligence dependencies",
    )
    replace_once(
        workflow,
        "            -r api-center/eia/requirements.txt\n          python -m pip check",
        "            -r api-center/eia/requirements.txt \\\n            -r api-center/un-comtrade/requirements.txt\n          python -m pip check",
    )
    replace_once(
        workflow,
        "          python -m unittest discover -s api-center/eia/tests -p 'test_*.py' -v\n          python -m unittest discover -s api-center/tests -p 'test_*.py' -v",
        "          python -m unittest discover -s api-center/eia/tests -p 'test_*.py' -v\n          python -m unittest discover -s api-center/un-comtrade/tests -p 'test_*.py' -v\n          python -m unittest discover -s api-center/tests -p 'test_*.py' -v",
    )
    replace_once(
        workflow,
        "          assert catalog['managed_provider_count'] == len(providers) == 39",
        "          assert catalog['managed_provider_count'] == len(providers) == 40",
    )
    replace_once(
        workflow,
        "          assert catalog['enabled_managed_provider_count'] == 39",
        "          assert catalog['enabled_managed_provider_count'] == 40",
    )
    replace_once(workflow, "          ) == 426", "          ) == 436")
    eia_block = """          eia = providers['eia']
          assert eia['ticket_prefix'] == '[intel-eia]'
          assert eia['required_secret_environment_variable_name'] == 'EIA_API_KEY'
          assert len(eia['operations']) == 6
          assert eia['limits']['requests_per_ticket_max'] == 1
          assert eia['limits']['rows_per_response_max'] == 5000
          assert eia['limits']['fixed_api_host'] == 'api.eia.gov'
          assert eia['limits']['automatic_pagination_allowed'] is False
          assert eia['limits']['bulk_download_allowed'] is False
          assert eia['limits']['path_traversal_allowed'] is False
          assert eia['limits']['background_crawling_allowed'] is False
          assert eia['limits']['write_operations_allowed'] is False

"""
    comtrade_block = """          un_comtrade = providers['un-comtrade']
          assert un_comtrade['ticket_prefix'] == '[intel-un-comtrade]'
          assert un_comtrade['required_secret_environment_variable_name'] == 'UN_COMTRADE_API_KEY'
          assert len(un_comtrade['operations']) == 10
          assert un_comtrade['limits']['requests_per_ticket_max'] == 1
          assert un_comtrade['limits']['preview_records_max'] == 500
          assert un_comtrade['limits']['records_per_request_max'] == 5000
          assert un_comtrade['limits']['free_api_calls_per_day'] == 500
          assert un_comtrade['limits']['fixed_api_host'] == 'comtradeapi.un.org'
          assert un_comtrade['limits']['automatic_pagination_allowed'] is False
          assert un_comtrade['limits']['bulk_api_allowed'] is False
          assert un_comtrade['limits']['async_api_allowed'] is False
          assert un_comtrade['limits']['write_operations_allowed'] is False

"""
    replace_once(workflow, eia_block, eia_block + comtrade_block)
    replace_once(workflow, "              'managed_providers': 39,", "              'managed_providers': 40,")
    replace_once(workflow, "              'managed_operations': 426,", "              'managed_operations': 436,")
    replace_once(
        workflow,
        "              'eia_operations': 6,\n              'removed_providers':",
        "              'eia_operations': 6,\n              'un_comtrade_operations': 10,\n              'removed_providers':",
    )

    task = Path("api-center/un-comtrade/un_comtrade_task.py")
    text = task.read_text(encoding="utf-8")
    old = '    _append_boolean(query, parameters, "count_only", "countOnly")\n    _append_boolean(query, parameters, "include_descriptions", "includeDesc")'
    new = '    if not trade_balance:\n        _append_boolean(query, parameters, "count_only", "countOnly")\n    _append_boolean(query, parameters, "include_descriptions", "includeDesc")'
    if text.count(old) != 1:
        raise SystemExit("unable to patch trade-balance countOnly behavior")
    task.write_text(text.replace(old, new), encoding="utf-8")

    provider_path = Path("api-center/un-comtrade/provider-catalog.json")
    provider_catalog = json.loads(provider_path.read_text(encoding="utf-8"))
    operation = next(
        row
        for row in provider_catalog["providers"][0]["operations"]
        if row["operation_id"] == "trade-balance"
    )
    operation["parameters"] = [
        name for name in operation["parameters"] if name != "count_only"
    ]
    operation["parameter_schema"]["properties"].pop("count_only", None)
    provider_path.write_text(
        json.dumps(provider_catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
