#!/usr/bin/env python3
"""Build the frozen safe YuanDian API snapshot from the reviewed official 2026-07-31 catalog."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUTPUT_PATH = HERE / "readonly-apis.snapshot.json"
OFFICIAL_ORIGIN = "https://open.chineselaw.com"
ROWS = [('law_vector_search',
  'POST',
  '法律法规',
  '法律法规语义检索',
  '按自然语言查询检索法条，支持时效性、效力级别和实施日期过滤。',
  ['query', 'rewrite_flag', 'fatiao_filter', 'return_num']),
 ('rh_ft_detail', 'POST', '法律法规', '法条详情', '按法条ID，或法规名称与条号查询单条法条详情。', ['id', 'fgmc', 'ftnum', 'refer_date']),
 ('rh_fg_detail', 'POST', '法律法规', '法规详情', '按法规ID或法规名称查询法规详情和指定日期版本。', ['id', 'fgmc', 'refer_date']),
 ('rh_ft_search',
  'POST',
  '法律法规',
  '法条关键词检索',
  '按关键词及法规、效力、时效、地域和日期条件检索法条。',
  ['keyword', 'fgmc', 'effect1', 'sxx', 'area', 'publish_start', 'publish_end', 'implement_start', 'implement_end', 'pageNo', 'pageSize']),
 ('rh_fg_search',
  'POST',
  '法律法规',
  '法规关键词检索',
  '按关键词及名称、效力、时效、地域和日期条件检索法规。',
  ['keyword', 'fgmc', 'effect1', 'sxx', 'area', 'publish_start', 'publish_end', 'implement_start', 'implement_end', 'pageNo', 'pageSize']),
 ('case_vector_search',
  'POST',
  '案例文书',
  '案例语义检索',
  '按自然语言查询进行案例语义检索，并支持案件类别、案由、法院、地域和日期过滤。',
  ['query', 'rewrite_flag', 'wenshu_filter', 'return_num']),
 ('rh_case_details', 'GET', '案例文书', '案例详情', '按案例ID或案号查询普通案例或权威案例详情。', ['id', 'ah', 'type']),
 ('rh_qwal_search',
  'POST',
  '案例文书',
  '权威案例关键词检索',
  '检索指导、典型、参考等权威案例。',
  ['ah', 'title', 'ay', 'court', 'area', 'wslx', 'ajlx', 'cp_start', 'cp_end', 'keyword', 'pageNo', 'pageSize']),
 ('rh_ptal_search',
  'POST',
  '案例文书',
  '普通案例关键词检索',
  '检索普通裁判案例，支持案号、企业、案由、法院、地域、日期、全文和援引法条过滤。',
  ['ah',
   'title',
   'company',
   'ay',
   'court',
   'area',
   'wslx',
   'ajlx',
   'cp_start',
   'cp_end',
   'ja_start',
   'ja_end',
   'keyword',
   'analysis_keyword',
   'law_reference',
   'pageNo',
   'pageSize']),
 ('rh_ssgsgg_search',
  'POST',
  '企业信息',
  '上市公司公告关键词检索',
  '按标题、公司、股票简称、交易所、地区、分类、日期和全文关键词检索公告。',
  ['title', 'company_name', 'stock_name', 'exchange', 'area', 'category', 'publish_start', 'publish_end', 'keyword', 'pageNo', 'pageSize']),
 ('rh_enterpriseAnnualReport', 'GET', '企业信息', '企业年报详情', '按企业ID或统一社会信用代码和年份查询企业年报。', ['id', 'tyshxydm', 'year']),
 ('rh_enterpriseAggregationSummary', 'GET', '企业信息', '企业聚合总览', '按企业ID或统一社会信用代码查询多模块统计总览。', ['id', 'tyshxydm']),
 ('rh_enterpriseSearch', 'GET', '企业信息', '企业检索', '按企业名称关键词检索企业候选。', ['name', 'top_k']),
 ('rh_enterpriseBaseInfo', 'GET', '企业信息', '企业基本信息', '查询企业基本信息、股东、成员和分支机构。', ['id', 'tyshxydm']),
 ('rh_enterpriseOutInvest', 'GET', '企业信息', '企业对外投资', '分页查询企业对外投资。', ['id', 'tyshxydm', 'pageNo', 'pageSize']),
 ('rh_enterpriseBrand', 'GET', '企业信息', '企业商标', '分页查询企业商标。', ['id', 'tyshxydm', 'pageNo', 'pageSize']),
 ('rh_enterprisePatent', 'GET', '企业信息', '企业专利', '分页查询企业专利。', ['id', 'tyshxydm', 'pageNo', 'pageSize']),
 ('rh_enterpriseSoftRight', 'GET', '企业信息', '企业软件著作权', '分页查询企业软件著作权。', ['id', 'tyshxydm', 'pageNo', 'pageSize']),
 ('rh_enterpriseWorksRight', 'GET', '企业信息', '企业作品著作权', '分页查询企业作品著作权。', ['id', 'tyshxydm', 'pageNo', 'pageSize']),
 ('rh_enterpriseIcp', 'GET', '企业信息', '企业网站备案', '分页查询企业网站备案。', ['id', 'tyshxydm', 'pageNo', 'pageSize']),
 ('rh_enterpriseChangeInfo', 'GET', '企业信息', '企业变更记录', '分页查询企业变更记录。', ['id', 'tyshxydm', 'pageNo', 'pageSize']),
 ('rh_enterpriseWritAgg', 'GET', '企业信息', '企业涉诉统计', '查询企业涉诉信息多维统计。', ['id', 'tyshxydm']),
 ('rh_enterpriseWritList', 'GET', '企业信息', '企业涉诉文书', '分页查询企业涉诉文书摘要。', ['id', 'tyshxydm', 'pageNo', 'pageSize']),
 ('rh_enterpriseCourtSessionNotice', 'GET', '企业信息', '企业开庭公告', '分页查询企业开庭公告。', ['id', 'tyshxydm', 'pageNo', 'pageSize']),
 ('rh_enterpriseCourtNotice', 'GET', '企业信息', '企业法院公告', '分页查询企业法院公告。', ['id', 'tyshxydm', 'pageNo', 'pageSize']),
 ('rh_enterpriseExecutions', 'GET', '企业信息', '企业失信被执行人', '分页查询企业失信被执行人记录。', ['id', 'tyshxydm', 'pageNo', 'pageSize']),
 ('rh_enterpriseExecutedPerson', 'GET', '企业信息', '企业被执行人', '分页查询企业被执行人记录。', ['id', 'tyshxydm', 'pageNo', 'pageSize']),
 ('rh_enterpriseFrozenEquity', 'GET', '企业信息', '企业股权冻结', '分页查询企业股权冻结。', ['id', 'tyshxydm', 'pageNo', 'pageSize']),
 ('rh_enterprisePunishment', 'GET', '企业信息', '企业行政处罚', '分页查询企业行政处罚。', ['id', 'tyshxydm', 'pageNo', 'pageSize']),
 ('rh_enterprisePledge', 'GET', '企业信息', '企业股权出质', '分页查询企业股权出质。', ['id', 'tyshxydm', 'pageNo', 'pageSize']),
 ('rh_enterpriseGuaranty', 'GET', '企业信息', '企业对外担保', '分页查询企业对外担保。', ['id', 'tyshxydm', 'pageNo', 'pageSize']),
 ('rh_enterpriseAbnormalOperation', 'GET', '企业信息', '企业经营异常', '分页查询企业经营异常记录。', ['id', 'tyshxydm', 'pageNo', 'pageSize']),
 ('rh_enterpriseCorporateTax', 'GET', '企业信息', '企业欠税公告', '分页查询企业欠税公告。', ['id', 'tyshxydm', 'pageNo', 'pageSize']),
 ('rh_enterpriseSeriousIllegal', 'GET', '企业信息', '企业严重违法', '分页查询企业严重违法记录。', ['id', 'tyshxydm', 'pageNo', 'pageSize']),
 ('rh_company_detail', 'GET', '企业信息', '企业聚合详情', '按企业ID或统一社会信用代码查询企业聚合详情。', ['id', 'tyshxydm']),
 ('rh_company_info', 'GET', '企业信息', '企业名称详情检索', '按企业名称、曾用名或股票简称检索候选企业详情。', ['name', 'num']),
 ('hall_detect', 'POST', '幻觉检测', '法律幻觉校验', '校验文本中的法规、法条和案号引用，返回时效性与权威原文核验结果。', ['text'])]


def operation_id(route_key: str) -> str:
    value = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", route_key.replace("_", "-"))
    return "yuandian-" + value.lower()


def build() -> dict:
    apis = []
    for route_key, method, category, name, description, parameters in ROWS:
        apis.append({
            "operation_id": operation_id(route_key),
            "route_key": route_key,
            "http_method": method,
            "category": category,
            "display_name": name,
            "description": description,
            "endpoint": f"{OFFICIAL_ORIGIN}/open/{route_key}",
            "known_parameter_names": parameters,
            "full_contract_discovery": f"{OFFICIAL_ORIGIN}/api-docs/{route_key}.html",
            "read_only": True,
        })
    categories = dict(Counter(row["category"] for row in apis))
    return {
        "schema_version": "yuandian-readonly-api-snapshot-v1",
        "snapshot_date": "2026-07-31",
        "official_origin": OFFICIAL_ORIGIN,
        "official_catalog_url": f"{OFFICIAL_ORIGIN}/api/apis?pageNum=1&pageSize=200&sortBy=latest",
        "official_documentation_url": f"{OFFICIAL_ORIGIN}/docs/",
        "discovery_mode": "official-public-json-catalog-with-repository-fallback",
        "documented_api_count": len(apis),
        "categories": categories,
        "secret_values_exposed": False,
        "apis": apis,
    }


def main() -> int:
    OUTPUT_PATH.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
