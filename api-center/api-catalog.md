# API 中心能力目录

- 开放模式：`maximum-safe-readonly`
- 普通连接器：`69/69` 已启用
- 托管提供方：`7/7` 已启用
- 托管操作总数：`93`
- 已公开参数总数：`647`
- 目录 SHA-256：`4e9008f4867803b88795c1abec945367d51f7e53ac305e910b9bd344fdd38cd7`
- 选择者：`GPTs 使用中心`
- 维修者：`普通网页 GPT + GitHub 插件`
- Secret/Authorization 值：`不暴露`
- 写入、交易、任意URL、任意代码、跨中心直连：`不开放`

本目录直接嵌入普通连接器的请求、响应、字段、韧性和安全契约，以及托管提供方每个操作的完整参数Schema。

## 托管提供方

| 提供方 | ID | 状态 | 票据前缀 | 操作数量 | 动态只读发现 |
|---|---|---|---|---|---|
| Google BigQuery | `bigquery` | 启用 | `[api-gcp]` | `7` | 否 |
| Google Earth Engine | `earth-engine` | 启用 | `[api-gcp]` | `6` | 否 |
| Google Data Commons | `data-commons` | 启用 | `[api-dc]` | `5` | 否 |
| AKShare 中国金融公开数据 | `akshare` | 启用 | `[api-akshare]` | `17` | 否 |
| Ashare 轻量 A 股行情 | `ashare` | 启用 | `[api-ashare]` | `1` | 否 |
| Wind AIFin Market 金融数据与能力 | `aifin-market` | 启用 | `[api-aifin]` | `17` | 否 |
| 元典法律智能开放平台 | `yuandian-law` | 启用 | `[api-yuandian]` | `40` | 否 |

## 普通连接器

| 能力 | ID | 状态 | 分类 | 端点 | 参数数 |
|---|---|---|---|---|---|
| 高德坐标转换 | `amap-coordinate-convert` | 启用 | `geospatial` | `GET /data/amap/coordinate/convert` | `2` |
| 高德骑行路线规划 | `amap-direction-bicycling` | 启用 | `routing` | `GET /data/amap/direction/bicycling` | `3` |
| 高德驾车路线规划 | `amap-direction-driving` | 启用 | `routing` | `GET /data/amap/direction/driving` | `10` |
| 高德公交综合路径规划 | `amap-direction-transit` | 启用 | `routing` | `GET /data/amap/direction/transit` | `9` |
| 高德步行路线规划 | `amap-direction-walking` | 启用 | `routing` | `GET /data/amap/direction/walking` | `5` |
| 高德多点距离测量 | `amap-distance` | 启用 | `distance` | `GET /data/amap/distance` | `3` |
| 高德行政区域查询 | `amap-district` | 启用 | `administrative` | `GET /data/amap/district` | `5` |
| 高德地址转坐标 | `amap-geocode` | 启用 | `geocoding` | `GET /data/amap/geocode` | `3` |
| 高德输入提示 | `amap-inputtips` | 启用 | `poi` | `GET /data/amap/inputtips` | `6` |
| 高德IP定位 | `amap-ip-location` | 启用 | `geolocation` | `GET /data/amap/ip/location` | `1` |
| 高德周边POI搜索 | `amap-place-around` | 启用 | `poi` | `GET /data/amap/place/around` | `9` |
| 高德POI详情 | `amap-place-detail` | 启用 | `poi` | `GET /data/amap/place/detail` | `2` |
| 高德多边形POI搜索 | `amap-place-polygon` | 启用 | `poi` | `GET /data/amap/place/polygon` | `6` |
| 高德 POI 关键词搜索 | `amap-place-text` | 启用 | `poi` | `GET /data/amap/place/text` | `7` |
| 高德坐标转地址 | `amap-regeocode` | 启用 | `geocoding` | `GET /data/amap/regeocode` | `6` |
| 高德圆形范围路况 | `amap-traffic-circle` | 启用 | `traffic` | `GET /data/amap/traffic/circle` | `4` |
| 高德矩形范围路况 | `amap-traffic-rectangle` | 启用 | `traffic` | `GET /data/amap/traffic/rectangle` | `3` |
| 高德指定道路路况 | `amap-traffic-road` | 启用 | `traffic` | `GET /data/amap/traffic/road` | `4` |
| 高德城市天气 | `amap-weather` | 启用 | `weather` | `GET /data/amap/weather` | `2` |
| 百度坐标转换 | `baidu-coordinate-convert` | 启用 | `geospatial` | `GET /data/baidu/coordinate/convert` | `3` |
| 百度地图驾车路线规划 | `baidu-direction-driving` | 启用 | `china-routing` | `GET /data/baidu/direction/driving` | `6` |
| 百度riding路线规划 | `baidu-direction-riding` | 启用 | `routing` | `GET /data/baidu/direction/riding` | `4` |
| 百度transit路线规划 | `baidu-direction-transit` | 启用 | `routing` | `GET /data/baidu/direction/transit` | `6` |
| 百度walking路线规划 | `baidu-direction-walking` | 启用 | `routing` | `GET /data/baidu/direction/walking` | `4` |
| 百度地图地址转坐标 | `baidu-geocode` | 启用 | `china-geocoding` | `GET /data/baidu/geocode` | `4` |
| 百度IP定位 | `baidu-ip-location` | 启用 | `geolocation` | `GET /data/baidu/ip/location` | `2` |
| 百度地点详情 | `baidu-place-detail` | 启用 | `poi` | `GET /data/baidu/place/detail` | `3` |
| 百度地图POI搜索 | `baidu-place-search` | 启用 | `china-poi` | `GET /data/baidu/place/search` | `12` |
| 百度地点联想 | `baidu-place-suggestion` | 启用 | `poi` | `GET /data/baidu/place/suggestion` | `5` |
| 百度逆地理编码 | `baidu-regeocode` | 启用 | `geocoding` | `GET /data/baidu/regeocode` | `11` |
| 百度driving批量算路 | `baidu-routematrix-driving` | 启用 | `routing` | `GET /data/baidu/routematrix/driving` | `5` |
| 百度riding批量算路 | `baidu-routematrix-riding` | 启用 | `routing` | `GET /data/baidu/routematrix/riding` | `5` |
| 百度walking批量算路 | `baidu-routematrix-walking` | 启用 | `routing` | `GET /data/baidu/routematrix/walking` | `5` |
| 百度天气查询 | `baidu-weather` | 启用 | `weather` | `GET /data/baidu/weather` | `4` |
| ChinaData.live 中国统计数据集 | `chinadata-live-dataset` | 启用 | `china-statistics` | `GET /data/chinadata/dataset/{dataset_id}` | `1` |
| DBnomics数据集目录 | `dbnomics-dataset` | 启用 | `macroeconomics` | `GET /data/dbnomics/dataset/{provider_code}/{dataset_code}` | `7` |
| DBnomics全球经济序列搜索 | `dbnomics-search` | 启用 | `macroeconomics` | `GET /data/dbnomics/search` | `4` |
| DBnomics 经济时间序列 | `dbnomics-series` | 启用 | `economic-time-series` | `GET /data/dbnomics/series/{provider_code}/{dataset_code}/{series_code}` | `9` |
| NewsAPI 全网新闻检索 | `newsapi-everything` | 启用 | `news-search` | `GET /data/newsapi/everything` | `11` |
| NewsAPI 新闻来源目录 | `newsapi-sources` | 启用 | `news-source-catalog` | `GET /data/newsapi/sources` | `3` |
| NewsAPI 头条新闻 | `newsapi-top-headlines` | 启用 | `news-headlines` | `GET /data/newsapi/top-headlines` | `6` |
| Open-Meteo空气质量 | `openmeteo-air-quality` | 启用 | `environment` | `GET /data/openmeteo/air-quality` | `11` |
| Open-Meteo历史天气 | `openmeteo-archive` | 启用 | `historical-weather` | `GET /data/openmeteo/archive` | `13` |
| Open-Meteo气候变化情景 | `openmeteo-climate` | 启用 | `climate` | `GET /data/openmeteo/climate` | `10` |
| Open-Meteo海拔查询 | `openmeteo-elevation` | 启用 | `terrain` | `GET /data/openmeteo/elevation` | `2` |
| Open-Meteo集合预报 | `openmeteo-ensemble` | 启用 | `weather` | `GET /data/openmeteo/ensemble` | `11` |
| Open-Meteo洪水与河流流量 | `openmeteo-flood` | 启用 | `hydrology` | `GET /data/openmeteo/flood` | `9` |
| Open‑Meteo 全球天气预报 | `openmeteo-forecast` | 启用 | `global-weather` | `GET /data/openmeteo/forecast` | `12` |
| Open-Meteo全球地理编码 | `openmeteo-geocoding` | 启用 | `geocoding` | `GET /data/openmeteo/geocoding` | `5` |
| Open-Meteo历史预报存档 | `openmeteo-historical-forecast` | 启用 | `historical-weather` | `GET /data/openmeteo/historical-forecast` | `13` |
| Open-Meteo海洋预报 | `openmeteo-marine` | 启用 | `marine` | `GET /data/openmeteo/marine` | `13` |
| Open-Meteo季节预报 | `openmeteo-seasonal` | 启用 | `climate` | `GET /data/openmeteo/seasonal` | `10` |
| OpenStreetMap 周边商业与公共设施 | `osm-commercial-around` | 启用 | `commercial-spatial-poi` | `GET /data/osm/commercial/around/{latitude}/{longitude}/{radius}` | `3` |
| OpenStreetMap逆地理编码 | `osm-nominatim-reverse` | 启用 | `geocoding` | `GET /data/osm/nominatim/reverse` | `8` |
| OpenStreetMap Nominatim 地点搜索 | `osm-nominatim-search` | 启用 | `open-geocoding` | `GET /data/osm/nominatim/search` | `8` |
| 天地图地名与POI搜索 | `tianditu-place-search` | 启用 | `china-place-search` | `GET /data/tianditu/place/search` | `2` |
| Wikidata实体声明 | `wikidata-claims` | 启用 | `knowledge-graph` | `GET /data/wikidata/entity/claims` | `5` |
| Wikidata实体原始JSON | `wikidata-entity-data` | 启用 | `knowledge-graph` | `GET /data/wikidata/entity/{entity_id}` | `1` |
| Wikidata实体详情 | `wikidata-entity-get` | 启用 | `knowledge-graph` | `GET /data/wikidata/entity/get` | `11` |
| Wikidata 公开实体搜索 | `wikidata-entity-search` | 启用 | `knowledge-graph` | `GET /data/wikidata/entity/search` | `8` |
| 世界银行国家与经济体目录 | `worldbank-countries` | 启用 | `international-development` | `GET /data/worldbank/countries` | `3` |
| 世界银行单一经济体元数据 | `worldbank-country` | 启用 | `international-development` | `GET /data/worldbank/country/{country_code}` | `2` |
| 世界银行收入组目录 | `worldbank-income-levels` | 启用 | `international-development` | `GET /data/worldbank/income-levels` | `3` |
| 世界银行发展指标时间序列 | `worldbank-indicator-jsonstat` | 启用 | `global-development-indicators` | `GET /data/worldbank/indicator/{country_code}/{indicator_code}` | `14` |
| 世界银行单一指标元数据 | `worldbank-indicator` | 启用 | `international-development` | `GET /data/worldbank/indicator-metadata/{indicator_code}` | `2` |
| 世界银行指标目录 | `worldbank-indicators` | 启用 | `international-development` | `GET /data/worldbank/indicators` | `4` |
| 世界银行贷款类型目录 | `worldbank-lending-types` | 启用 | `international-development` | `GET /data/worldbank/lending-types` | `3` |
| 世界银行数据源目录 | `worldbank-sources` | 启用 | `international-development` | `GET /data/worldbank/sources` | `3` |
| 世界银行主题目录 | `worldbank-topics` | 启用 | `international-development` | `GET /data/worldbank/topics` | `3` |

## 不可取消的安全边界

1. 只读公开数据能力最大化开放；
2. Secret与Authorization只显示环境变量名称，绝不显示值；
3. 动态工具/函数必须先从固定上游或固定安装包发现，再通过只读、签名和Schema校验；
4. 禁止任意URL、请求头、文件路径、脚本、代码、写入、交易和下单；
5. 三中心继续隔离，只能由GPTs传递任务与结果。

## Google BigQuery (`bigquery`)

- 状态：`启用`
- 说明：动态列出获准公共项目中的数据集、表、字段、模型和例程，并执行经过费用预检的只读GoogleSQL查询。
- 目录策略：GPTs可读取全部获准项目的目录元数据；默认公共项目为bigquery-public-data、gdelt-bq和patents-public-data。
- 执行策略：只允许单条SELECT或WITH查询；禁止DDL、DML、脚本、导出、外部查询、远程函数和私有项目访问。
- 票据前缀：`[api-gcp]`
- Secret环境变量名：`GOOGLE_CLOUD_SERVICE_ACCOUNT_JSON`（仅名称）
- 提供方SHA-256：`2817ce97b80e6e2095ac6f52a9177ce77dd8161de543dfc0784b016531b3b625`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-projects` | 列出当前允许访问的BigQuery公共项目和计费项目标识。 | `无` |

`catalog-projects` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `catalog-datasets` | 列出指定获准项目中的全部可见数据集。 | `project_id, max_results, page_token` |

`catalog-datasets` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "project_id": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "max_results": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "page_token": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `catalog-tables` | 列出指定数据集中的表、视图、外部表和物化视图。 | `project_id, dataset_id, max_results, page_token` |

`catalog-tables` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "project_id": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "dataset_id": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "max_results": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "page_token": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `catalog-table` | 读取指定表的完整安全元数据和字段结构，不读取表中数据。 | `project_id, dataset_id, table_id` |

`catalog-table` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "project_id": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "dataset_id": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "table_id": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `catalog-routines` | 列出指定数据集中的用户定义函数和存储过程目录。 | `project_id, dataset_id, max_results, page_token` |

`catalog-routines` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "project_id": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "dataset_id": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "max_results": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "page_token": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `catalog-models` | 列出指定数据集中的BigQuery ML模型目录。 | `project_id, dataset_id, max_results, page_token` |

`catalog-models` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "project_id": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "dataset_id": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "max_results": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "page_token": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `query-readonly` | 先dry-run估算扫描量，再执行只读GoogleSQL并返回有限行数和费用证据。 | `sql, location, maximum_bytes_billed, max_rows, timeout_ms, query_parameters_json` |

`query-readonly` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "sql": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "location": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "maximum_bytes_billed": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "max_rows": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "timeout_ms": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "query_parameters_json": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

限制：

```json
{
  "default_maximum_bytes_billed": 1000000000,
  "hard_maximum_bytes_billed": 10000000000,
  "default_max_rows": 1000,
  "hard_max_rows": 5000,
  "query_timeout_ms": 30000
}
```

## Google Earth Engine (`earth-engine`)

- 状态：`启用`
- 说明：开放官方STAC数据目录和全部算法目录，并执行受控的只读value:compute表达式。中国专题目录覆盖人口、夜间灯光、城市扩张、土地利用和长期气候。
- 目录策略：GPTs可搜索和读取官方Earth Engine STAC目录，并按名称或说明筛选全部可用算法；优先使用china-topic-packs.json中的已核验全球数据集。
- 执行策略：只允许返回JSON值的只读计算；禁止导出、写资产、删除、复制、重命名、上传、外部URL和视频或缩略图任务。
- 票据前缀：`[api-gcp]`
- Secret环境变量名：`GOOGLE_CLOUD_SERVICE_ACCOUNT_JSON`（仅名称）
- 提供方SHA-256：`f08a995b8368618b4bf3bd78cfb66185fc480d758b1271a978671e94caf16904`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取Earth Engine目录、算法和只读计算的完整使用规则。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `catalog-dataset-root` | 读取官方Earth Engine STAC总目录入口。 | `无` |

`catalog-dataset-root` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `catalog-dataset-search` | 在官方STAC对象名称中搜索数据集，并返回可继续读取的对象路径。 | `search, max_results, page_token` |

`catalog-dataset-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "search": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "max_results": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "page_token": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `catalog-dataset` | 按官方STAC对象路径读取一个数据集或子目录的完整元数据。 | `object_path` |

`catalog-dataset` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "object_path": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `catalog-algorithms` | 从Earth Engine API读取全部算法的名称、说明、返回类型和参数，并支持搜索和分页。 | `search, offset, max_results` |

`catalog-algorithms` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "search": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "offset": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "max_results": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `compute-value-readonly` | 执行经过结构和算法安全校验的Earth Engine序列表达式，只返回JSON值。 | `expression_json, workload_tag` |

`compute-value-readonly` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "expression_json": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "workload_tag": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

限制：

```json
{
  "max_expression_characters": 20000,
  "max_expression_nodes": 500,
  "max_expression_depth": 30,
  "max_algorithm_results": 200,
  "max_dataset_results": 100
}
```

## Google Data Commons (`data-commons`)

- 状态：`启用`
- 说明：通过Data Commons REST V2只读查询全球公共统计知识图谱，重点支持中国国家、省级、城市及可用更细行政层级的人口、经济、就业、教育、医疗和环境指标。
- 目录策略：GPTs先读取data-commons/provider-catalog.json和china-starter-pack.json，再解析地点或统计指标DCID；中国细粒度覆盖取决于原始来源，不得假设所有城市或县均有数据。
- 执行策略：仅允许固定的resolve、node和observation端点；只提交公开实体、指标和关系表达式；禁止SPARQL、自然语言接口、任意URL和个人数据。
- 票据前缀：`[api-dc]`
- Secret环境变量名：`GOOGLE_DATA_COMMONS_API_KEY`（仅名称）
- 提供方SHA-256：`54da4c493916be4a170264ed85762d702ea4af6008f012346327498cb1a7ade0`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取Data Commons受控能力、限制和中国起步目录，不调用上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `resolve-place` | 按一个或多个公开地点名称解析Data Commons地点DCID。 | `nodes_json, property` |

`resolve-place` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "nodes_json": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "property": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `resolve-indicator` | 按指标描述解析统计变量或主题DCID。 | `nodes_json` |

`resolve-indicator` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "nodes_json": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `node-properties` | 按固定关系表达式读取节点属性、相邻实体或行政层级关系。 | `nodes_json, property` |

`node-properties` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "nodes_json": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "property": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `observations` | 读取指定实体和统计变量的最新、指定日期或完整时间序列观测，并保留facet来源。 | `entity_dcids_json, variable_dcids_json, date, select_json, facet_ids_json, domains_json` |

`observations` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "entity_dcids_json": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "variable_dcids_json": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "date": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "select_json": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "facet_ids_json": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "domains_json": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

限制：

```json
{
  "max_nodes": 20,
  "max_variables": 20,
  "max_select_fields": 5,
  "max_relation_expression_characters": 300,
  "max_response_bytes": 1000000,
  "timeout_seconds": 60
}
```

## AKShare 中国金融公开数据 (`akshare`)

- 状态：`启用`
- 说明：通过固定、只读、限量的AKShare函数读取A股、ETF、资金流、财务报表、板块与中国宏观经济公共数据。
- 目录策略：GPTs可读取完整固定操作目录并选择高价值只读能力；不得提交任意AKShare函数名、URL、Python代码或动态导入目标。
- 执行策略：每张票据只执行一个固定白名单函数；严格校验证券代码、市场、周期、日期、报表类型、指标枚举、行数和超时；不连接券商、不下单。
- 票据前缀：`[api-akshare]`
- Secret环境变量名：`无`（仅名称）
- 提供方SHA-256：`51c98e310e75aa22eb2cf474ed39a82cef707470af3d0d88a487271cb7ddc4d1`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取AKShare适配器完整安全能力和限制，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `stock-a-share-spot` | 读取A股实时行情总表，可按证券代码过滤。 | `symbols, max_rows` |

`stock-a-share-spot` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbols": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "max_rows": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `stock-a-share-history` | 读取单只A股日、周、月历史行情与复权数据。 | `symbol, period, start_date, end_date, adjust, max_rows, timeout_seconds` |

`stock-a-share-history` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "period": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "start_date": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "end_date": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "adjust": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "max_rows": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "timeout_seconds": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `stock-company-info` | 读取单只A股公开公司基础资料。 | `symbol, timeout_seconds` |

`stock-company-info` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "timeout_seconds": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `stock-financial-indicators` | 读取单只A股财务分析指标。 | `symbol, indicator, max_rows` |

`stock-financial-indicators` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "indicator": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "max_rows": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `stock-financial-report` | 读取单只A股资产负债表、利润表或现金流量表历史数据。 | `symbol, market, statement_type, max_rows` |

`stock-financial-report` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "market": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "statement_type": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "max_rows": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `stock-fund-flow` | 读取单只A股近百个交易日资金流向。 | `symbol, market, max_rows` |

`stock-fund-flow` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "market": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "max_rows": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `stock-fund-flow-ranking` | 读取A股今日、3日、5日或10日资金流排名。 | `indicator, max_rows` |

`stock-fund-flow-ranking` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "indicator": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "max_rows": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `stock-industry-boards` | 读取A股行业板块实时行情目录。 | `max_rows` |

`stock-industry-boards` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "max_rows": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `stock-industry-constituents` | 读取指定行业板块成份股。 | `board_name, max_rows` |

`stock-industry-constituents` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "board_name": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "max_rows": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `fund-etf-spot` | 读取沪深ETF实时行情总表。 | `symbols, max_rows` |

`fund-etf-spot` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbols": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "max_rows": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `fund-etf-history` | 读取单只ETF日、周、月历史行情与复权数据。 | `symbol, period, start_date, end_date, adjust, max_rows` |

`fund-etf-history` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "period": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "start_date": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "end_date": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "adjust": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "max_rows": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `macro-china-gdp` | 读取中国国内生产总值时间序列。 | `max_rows` |

`macro-china-gdp` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "max_rows": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `macro-china-cpi` | 读取中国居民消费价格指数时间序列。 | `max_rows` |

`macro-china-cpi` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "max_rows": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `macro-china-ppi` | 读取中国工业品出厂价格指数时间序列。 | `max_rows` |

`macro-china-ppi` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "max_rows": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `macro-china-pmi` | 读取中国采购经理人指数时间序列。 | `max_rows` |

`macro-china-pmi` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "max_rows": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `macro-china-lpr` | 读取中国贷款市场报价利率时间序列。 | `max_rows` |

`macro-china-lpr` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "max_rows": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

限制：

```json
{
  "max_rows_default": 500,
  "max_rows_hard": 5000,
  "timeout_seconds_default": 20,
  "timeout_seconds_hard": 60,
  "arbitrary_functions_allowed": false,
  "arbitrary_urls_allowed": false,
  "brokerage_execution_allowed": false,
  "fixed_akshare_functions": 16,
  "max_response_bytes": 5000000
}
```

## Ashare 轻量 A 股行情 (`ashare`)

- 状态：`启用`
- 说明：兼容 Ashare get_price 语义，通过固定腾讯与新浪公开行情端点读取A股、指数和基金日周月线及分钟线。
- 目录策略：GPTs只能选择固定 ashare-get-price 操作；不能提交任意URL、函数、请求头、脚本或Python代码。
- 执行策略：每张票据只读取一个证券代码；腾讯为主源，新浪为备用；限制周期、行数、超时和响应大小；不下单、不连接券商。
- 票据前缀：`[api-ashare]`
- Secret环境变量名：`无`（仅名称）
- 提供方SHA-256：`f763ed3c3a2aa7e979a6de86ffa20527b6f93b9d9e8613d21df21e0a4cffe481`

| 操作 | 说明 | 参数 |
|---|---|---|
| `ashare-get-price` | 按证券代码、周期、数量和结束日期读取规范化OHLCV行情。 | `symbol, frequency, count, end_date, source, timeout_seconds` |

`ashare-get-price` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "frequency": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "count": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "end_date": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "source": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "timeout_seconds": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

限制：

```json
{
  "count_default": 120,
  "count_hard": 1000,
  "timeout_seconds_default": 15,
  "timeout_seconds_hard": 30,
  "sources": [
    "auto",
    "tencent",
    "sina"
  ],
  "frequencies": [
    "1d",
    "1w",
    "1M",
    "1m",
    "5m",
    "15m",
    "30m",
    "60m"
  ],
  "arbitrary_functions_allowed": false,
  "arbitrary_urls_allowed": false,
  "brokerage_execution_allowed": false
}
```

## Wind AIFin Market 金融数据与能力 (`aifin-market`)

- 状态：`启用`
- 说明：通过万得官方MCP固定端点，开放当前目录发现的全部15个只读工具，覆盖证券行情、技术面、基本面、股东、事件、公告新闻、宏观经济和综合金融计算。
- 目录策略：GPTs可读取四个固定Wind MCP服务的实时工具目录，并选择本目录登记的全部只读工具；不得提交任意MCP端点、server_type、tool_name、脚本或密钥。
- 执行策略：每张票据只执行一个固定只读操作；先初始化MCP，再调用固定映射工具；限制输入、日期、条数和响应大小；不下单、不写入、不执行任意代码。
- 票据前缀：`[api-aifin]`
- Secret环境变量名：`WIND_API_KEY`（仅名称）
- 提供方SHA-256：`b630c7bf2699e4ff10856cc68063f54bbb5d64e14de27273f38dded0aa6ff819`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地AIFin Market完整安全能力、固定端点和限制，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `catalog-tools` | 列出指定受支持Wind MCP服务当前公开工具目录及输入Schema。 | `server_type` |

`catalog-tools` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "server_type": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `stock-price-indicators` | 读取一个或多个证券的最新价格、估值、盘口、资金流和技术快照指标。 | `windcode, indexes` |

`stock-price-indicators` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "windcode": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "indexes": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `risk-metrics` | 读取股票Beta、Alpha、波动率、夏普比率、最大回撤、VaR及财务安全比率。 | `question` |

`risk-metrics` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "question": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `stock-events` | 读取IPO、增发、配股、并购重组、分红、解禁、监管、诉讼和股权激励等公司事件。 | `question` |

`stock-events` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "question": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `stock-kline` | 读取股票分钟、日、周、月、季、半年或年K线，并支持复权和日期范围。 | `windcode, begin_date, end_date, count, period, aftype, issusp, afdate` |

`stock-kline` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "windcode": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "begin_date": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "end_date": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "count": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "period": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "aftype": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "issusp": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "afdate": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `stock-basicinfo` | 读取公司名称、注册地址、主营业务、行业分类、概念、上市与摘牌等基本档案。 | `question` |

`stock-basicinfo` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "question": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `stock-equity-holders` | 读取股本结构、前十大股东、机构持仓、实际控制人和限售解禁。 | `question` |

`stock-equity-holders` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "question": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `stock-fundamentals` | 读取财务报表、盈利能力、成长、现金流、杠杆、估值和银行业专项指标。 | `question` |

`stock-fundamentals` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "question": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `stock-quote` | 读取单只A股、港股或美股标的的分钟行情或指定时间范围行情。 | `windcode, begin, end` |

`stock-quote` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "windcode": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "begin": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "end": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `stock-technicals` | 读取历史行情、技术指标、融资融券、龙虎榜、涨跌停和阶段高低点。 | `question` |

`stock-technicals` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "question": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `stock-search` | 按市值、行业、价格、涨跌、技术或基本面条件筛选A股。 | `question` |

`stock-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "question": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `company-announcements` | 检索上市公司、债券发行人和金融工具发行人的官方公告与监管文件。 | `query, top_k` |

`company-announcements` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "top_k": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `financial-news` | 按对象、主题和时间范围检索第三方财经新闻。 | `query, top_k` |

`financial-news` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "top_k": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `economic-data` | 通过自然语言或EDB代码搜索并提取宏观、行业经济指标时间序列。 | `executionMode, question, observation, beginDate, endDate` |

`economic-data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "executionMode": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "question": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "observation": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "beginDate": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "endDate": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `economic-data-direct` | 使用结构化条件直接搜索和提取宏观指标，支持频率、量级、币种和搜索模式。 | `metricIdsStr, beginDate, endDate, freq, magnitude, currency, searchType, ifUnion` |

`economic-data-direct` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "metricIdsStr": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "beginDate": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "endDate": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "freq": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "magnitude": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "currency": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "searchType": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    },
    "ifUnion": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

| `analytics-query` | 执行单个只读金融数据聚合、比较、排名、加权平均或复合指标计算问题。 | `question` |

`analytics-query` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "question": {
      "type": [
        "string",
        "integer",
        "number",
        "boolean"
      ]
    }
  }
}
```

限制：

```json
{
  "max_operations_per_ticket": 1,
  "max_response_bytes": 1000000,
  "timeout_seconds": 60,
  "max_document_results": 20,
  "max_kline_count": 5000,
  "max_parameter_characters": 20000,
  "fixed_server_types": [
    "stock_data",
    "financial_docs",
    "economic_data",
    "analytics_data"
  ],
  "upstream_tools_exposed": 15,
  "arbitrary_server_types_allowed": false,
  "arbitrary_tool_names_allowed": false,
  "arbitrary_urls_allowed": false,
  "trading_or_order_execution_allowed": false,
  "write_operations_allowed": false
}
```

## 元典法律智能开放平台 (`yuandian-law`)

- 状态：`启用`
- 说明：通过元典官方开放平台读取中国法律法规、案例文书、企业公开信息和法律幻觉校验数据；冻结37项只读API，并通过官方实时目录自动发现后续安全只读能力。
- 目录策略：GPTs可读取冻结API快照和官方实时JSON目录；固定操作直接映射冻结routeKey，通用调用只允许官方目录当前登记的GET/POST接口。
- 执行策略：每张票据只执行一个只读调用；固定https://open.chineselaw.com主机，使用后端X-API-Key；限制参数深度、条数、超时和响应大小；过滤密钥和直接个人标识字段。
- 票据前缀：`[api-yuandian]`
- Secret环境变量名：`YUANDIAN_API_KEY`（仅名称）
- 提供方SHA-256：`209bcddd432ce325bb04568aa8404881ec8e42ec6995648166a0a3182ceea80e`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取元典适配器的本地完整安全目录、37项冻结只读API和限制，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `catalog-live` | 从元典官方公开JSON目录读取当前API、方法、分类、价格及请求/响应参数元数据；不需要业务API密钥。 | `category_id, page_size` |

`catalog-live` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "category_id": {
      "type": "integer",
      "enum": [
        6,
        7,
        9,
        10
      ]
    },
    "page_size": {
      "type": "integer",
      "minimum": 1,
      "maximum": 200
    }
  }
}
```

| `invoke-readonly-api` | 按元典官方实时目录选择任一GET/POST只读API并调用；固定官方主机，不接受任意URL、请求头或代码。 | `route_key, arguments, timeout_seconds, max_response_bytes` |

`invoke-readonly-api` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "route_key": {
      "type": "string",
      "pattern": "^[A-Za-z][A-Za-z0-9_]{2,95}$"
    },
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  },
  "required": [
    "route_key"
  ]
}
```

| `yuandian-law-vector-search` | 法律法规语义检索：按自然语言查询检索法条，支持时效性、效力级别和实施日期过滤。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-law-vector-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-ft-detail` | 法条详情：按法条ID，或法规名称与条号查询单条法条详情。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-ft-detail` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-fg-detail` | 法规详情：按法规ID或法规名称查询法规详情和指定日期版本。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-fg-detail` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-ft-search` | 法条关键词检索：按关键词及法规、效力、时效、地域和日期条件检索法条。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-ft-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-fg-search` | 法规关键词检索：按关键词及名称、效力、时效、地域和日期条件检索法规。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-fg-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-case-vector-search` | 案例语义检索：按自然语言查询进行案例语义检索，并支持案件类别、案由、法院、地域和日期过滤。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-case-vector-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-case-details` | 案例详情：按案例ID或案号查询普通案例或权威案例详情。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-case-details` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-qwal-search` | 权威案例关键词检索：检索指导、典型、参考等权威案例。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-qwal-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-ptal-search` | 普通案例关键词检索：检索普通裁判案例，支持案号、企业、案由、法院、地域、日期、全文和援引法条过滤。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-ptal-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-ssgsgg-search` | 上市公司公告关键词检索：按标题、公司、股票简称、交易所、地区、分类、日期和全文关键词检索公告。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-ssgsgg-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-enterprise-annual-report` | 企业年报详情：按企业ID或统一社会信用代码和年份查询企业年报。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-enterprise-annual-report` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-enterprise-aggregation-summary` | 企业聚合总览：按企业ID或统一社会信用代码查询多模块统计总览。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-enterprise-aggregation-summary` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-enterprise-search` | 企业检索：按企业名称关键词检索企业候选。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-enterprise-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-enterprise-base-info` | 企业基本信息：查询企业基本信息、股东、成员和分支机构。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-enterprise-base-info` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-enterprise-out-invest` | 企业对外投资：分页查询企业对外投资。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-enterprise-out-invest` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-enterprise-brand` | 企业商标：分页查询企业商标。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-enterprise-brand` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-enterprise-patent` | 企业专利：分页查询企业专利。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-enterprise-patent` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-enterprise-soft-right` | 企业软件著作权：分页查询企业软件著作权。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-enterprise-soft-right` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-enterprise-works-right` | 企业作品著作权：分页查询企业作品著作权。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-enterprise-works-right` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-enterprise-icp` | 企业网站备案：分页查询企业网站备案。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-enterprise-icp` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-enterprise-change-info` | 企业变更记录：分页查询企业变更记录。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-enterprise-change-info` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-enterprise-writ-agg` | 企业涉诉统计：查询企业涉诉信息多维统计。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-enterprise-writ-agg` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-enterprise-writ-list` | 企业涉诉文书：分页查询企业涉诉文书摘要。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-enterprise-writ-list` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-enterprise-court-session-notice` | 企业开庭公告：分页查询企业开庭公告。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-enterprise-court-session-notice` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-enterprise-court-notice` | 企业法院公告：分页查询企业法院公告。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-enterprise-court-notice` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-enterprise-executions` | 企业失信被执行人：分页查询企业失信被执行人记录。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-enterprise-executions` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-enterprise-executed-person` | 企业被执行人：分页查询企业被执行人记录。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-enterprise-executed-person` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-enterprise-frozen-equity` | 企业股权冻结：分页查询企业股权冻结。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-enterprise-frozen-equity` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-enterprise-punishment` | 企业行政处罚：分页查询企业行政处罚。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-enterprise-punishment` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-enterprise-pledge` | 企业股权出质：分页查询企业股权出质。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-enterprise-pledge` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-enterprise-guaranty` | 企业对外担保：分页查询企业对外担保。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-enterprise-guaranty` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-enterprise-abnormal-operation` | 企业经营异常：分页查询企业经营异常记录。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-enterprise-abnormal-operation` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-enterprise-corporate-tax` | 企业欠税公告：分页查询企业欠税公告。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-enterprise-corporate-tax` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-enterprise-serious-illegal` | 企业严重违法：分页查询企业严重违法记录。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-enterprise-serious-illegal` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-company-detail` | 企业聚合详情：按企业ID或统一社会信用代码查询企业聚合详情。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-company-detail` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-rh-company-info` | 企业名称详情检索：按企业名称、曾用名或股票简称检索候选企业详情。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-rh-company-info` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

| `yuandian-hall-detect` | 法律幻觉校验：校验文本中的法规、法条和案号引用，返回时效性与权威原文核验结果。 | `arguments, timeout_seconds, max_response_bytes` |

`yuandian-hall-detect` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "arguments": {
      "type": "object",
      "maxProperties": 60,
      "additionalProperties": true
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 5,
      "maximum": 120
    },
    "max_response_bytes": {
      "type": "integer",
      "minimum": 1024,
      "maximum": 5000000
    }
  }
}
```

最近一次受控只读工具快照：

```json
{
  "schema_version": "yuandian-readonly-api-snapshot-v1",
  "snapshot_date": "2026-07-31",
  "official_origin": "https://open.chineselaw.com",
  "official_catalog_url": "https://open.chineselaw.com/api/apis?pageNum=1&pageSize=200&sortBy=latest",
  "official_documentation_url": "https://open.chineselaw.com/docs/",
  "discovery_mode": "official-public-json-catalog-with-repository-fallback",
  "documented_api_count": 37,
  "categories": {
    "法律法规": 5,
    "案例文书": 4,
    "企业信息": 27,
    "幻觉检测": 1
  },
  "secret_values_exposed": false,
  "apis": [
    {
      "operation_id": "yuandian-law-vector-search",
      "route_key": "law_vector_search",
      "http_method": "POST",
      "category": "法律法规",
      "display_name": "法律法规语义检索",
      "description": "按自然语言查询检索法条，支持时效性、效力级别和实施日期过滤。",
      "endpoint": "https://open.chineselaw.com/open/law_vector_search",
      "known_parameter_names": [
        "query",
        "rewrite_flag",
        "fatiao_filter",
        "return_num"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/law_vector_search.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-ft-detail",
      "route_key": "rh_ft_detail",
      "http_method": "POST",
      "category": "法律法规",
      "display_name": "法条详情",
      "description": "按法条ID，或法规名称与条号查询单条法条详情。",
      "endpoint": "https://open.chineselaw.com/open/rh_ft_detail",
      "known_parameter_names": [
        "id",
        "fgmc",
        "ftnum",
        "refer_date"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_ft_detail.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-fg-detail",
      "route_key": "rh_fg_detail",
      "http_method": "POST",
      "category": "法律法规",
      "display_name": "法规详情",
      "description": "按法规ID或法规名称查询法规详情和指定日期版本。",
      "endpoint": "https://open.chineselaw.com/open/rh_fg_detail",
      "known_parameter_names": [
        "id",
        "fgmc",
        "refer_date"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_fg_detail.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-ft-search",
      "route_key": "rh_ft_search",
      "http_method": "POST",
      "category": "法律法规",
      "display_name": "法条关键词检索",
      "description": "按关键词及法规、效力、时效、地域和日期条件检索法条。",
      "endpoint": "https://open.chineselaw.com/open/rh_ft_search",
      "known_parameter_names": [
        "keyword",
        "fgmc",
        "effect1",
        "sxx",
        "area",
        "publish_start",
        "publish_end",
        "implement_start",
        "implement_end",
        "pageNo",
        "pageSize"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_ft_search.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-fg-search",
      "route_key": "rh_fg_search",
      "http_method": "POST",
      "category": "法律法规",
      "display_name": "法规关键词检索",
      "description": "按关键词及名称、效力、时效、地域和日期条件检索法规。",
      "endpoint": "https://open.chineselaw.com/open/rh_fg_search",
      "known_parameter_names": [
        "keyword",
        "fgmc",
        "effect1",
        "sxx",
        "area",
        "publish_start",
        "publish_end",
        "implement_start",
        "implement_end",
        "pageNo",
        "pageSize"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_fg_search.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-case-vector-search",
      "route_key": "case_vector_search",
      "http_method": "POST",
      "category": "案例文书",
      "display_name": "案例语义检索",
      "description": "按自然语言查询进行案例语义检索，并支持案件类别、案由、法院、地域和日期过滤。",
      "endpoint": "https://open.chineselaw.com/open/case_vector_search",
      "known_parameter_names": [
        "query",
        "rewrite_flag",
        "wenshu_filter",
        "return_num"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/case_vector_search.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-case-details",
      "route_key": "rh_case_details",
      "http_method": "GET",
      "category": "案例文书",
      "display_name": "案例详情",
      "description": "按案例ID或案号查询普通案例或权威案例详情。",
      "endpoint": "https://open.chineselaw.com/open/rh_case_details",
      "known_parameter_names": [
        "id",
        "ah",
        "type"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_case_details.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-qwal-search",
      "route_key": "rh_qwal_search",
      "http_method": "POST",
      "category": "案例文书",
      "display_name": "权威案例关键词检索",
      "description": "检索指导、典型、参考等权威案例。",
      "endpoint": "https://open.chineselaw.com/open/rh_qwal_search",
      "known_parameter_names": [
        "ah",
        "title",
        "ay",
        "court",
        "area",
        "wslx",
        "ajlx",
        "cp_start",
        "cp_end",
        "keyword",
        "pageNo",
        "pageSize"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_qwal_search.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-ptal-search",
      "route_key": "rh_ptal_search",
      "http_method": "POST",
      "category": "案例文书",
      "display_name": "普通案例关键词检索",
      "description": "检索普通裁判案例，支持案号、企业、案由、法院、地域、日期、全文和援引法条过滤。",
      "endpoint": "https://open.chineselaw.com/open/rh_ptal_search",
      "known_parameter_names": [
        "ah",
        "title",
        "company",
        "ay",
        "court",
        "area",
        "wslx",
        "ajlx",
        "cp_start",
        "cp_end",
        "ja_start",
        "ja_end",
        "keyword",
        "analysis_keyword",
        "law_reference",
        "pageNo",
        "pageSize"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_ptal_search.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-ssgsgg-search",
      "route_key": "rh_ssgsgg_search",
      "http_method": "POST",
      "category": "企业信息",
      "display_name": "上市公司公告关键词检索",
      "description": "按标题、公司、股票简称、交易所、地区、分类、日期和全文关键词检索公告。",
      "endpoint": "https://open.chineselaw.com/open/rh_ssgsgg_search",
      "known_parameter_names": [
        "title",
        "company_name",
        "stock_name",
        "exchange",
        "area",
        "category",
        "publish_start",
        "publish_end",
        "keyword",
        "pageNo",
        "pageSize"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_ssgsgg_search.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-enterprise-annual-report",
      "route_key": "rh_enterpriseAnnualReport",
      "http_method": "GET",
      "category": "企业信息",
      "display_name": "企业年报详情",
      "description": "按企业ID或统一社会信用代码和年份查询企业年报。",
      "endpoint": "https://open.chineselaw.com/open/rh_enterpriseAnnualReport",
      "known_parameter_names": [
        "id",
        "tyshxydm",
        "year"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_enterpriseAnnualReport.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-enterprise-aggregation-summary",
      "route_key": "rh_enterpriseAggregationSummary",
      "http_method": "GET",
      "category": "企业信息",
      "display_name": "企业聚合总览",
      "description": "按企业ID或统一社会信用代码查询多模块统计总览。",
      "endpoint": "https://open.chineselaw.com/open/rh_enterpriseAggregationSummary",
      "known_parameter_names": [
        "id",
        "tyshxydm"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_enterpriseAggregationSummary.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-enterprise-search",
      "route_key": "rh_enterpriseSearch",
      "http_method": "GET",
      "category": "企业信息",
      "display_name": "企业检索",
      "description": "按企业名称关键词检索企业候选。",
      "endpoint": "https://open.chineselaw.com/open/rh_enterpriseSearch",
      "known_parameter_names": [
        "name",
        "top_k"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_enterpriseSearch.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-enterprise-base-info",
      "route_key": "rh_enterpriseBaseInfo",
      "http_method": "GET",
      "category": "企业信息",
      "display_name": "企业基本信息",
      "description": "查询企业基本信息、股东、成员和分支机构。",
      "endpoint": "https://open.chineselaw.com/open/rh_enterpriseBaseInfo",
      "known_parameter_names": [
        "id",
        "tyshxydm"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_enterpriseBaseInfo.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-enterprise-out-invest",
      "route_key": "rh_enterpriseOutInvest",
      "http_method": "GET",
      "category": "企业信息",
      "display_name": "企业对外投资",
      "description": "分页查询企业对外投资。",
      "endpoint": "https://open.chineselaw.com/open/rh_enterpriseOutInvest",
      "known_parameter_names": [
        "id",
        "tyshxydm",
        "pageNo",
        "pageSize"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_enterpriseOutInvest.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-enterprise-brand",
      "route_key": "rh_enterpriseBrand",
      "http_method": "GET",
      "category": "企业信息",
      "display_name": "企业商标",
      "description": "分页查询企业商标。",
      "endpoint": "https://open.chineselaw.com/open/rh_enterpriseBrand",
      "known_parameter_names": [
        "id",
        "tyshxydm",
        "pageNo",
        "pageSize"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_enterpriseBrand.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-enterprise-patent",
      "route_key": "rh_enterprisePatent",
      "http_method": "GET",
      "category": "企业信息",
      "display_name": "企业专利",
      "description": "分页查询企业专利。",
      "endpoint": "https://open.chineselaw.com/open/rh_enterprisePatent",
      "known_parameter_names": [
        "id",
        "tyshxydm",
        "pageNo",
        "pageSize"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_enterprisePatent.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-enterprise-soft-right",
      "route_key": "rh_enterpriseSoftRight",
      "http_method": "GET",
      "category": "企业信息",
      "display_name": "企业软件著作权",
      "description": "分页查询企业软件著作权。",
      "endpoint": "https://open.chineselaw.com/open/rh_enterpriseSoftRight",
      "known_parameter_names": [
        "id",
        "tyshxydm",
        "pageNo",
        "pageSize"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_enterpriseSoftRight.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-enterprise-works-right",
      "route_key": "rh_enterpriseWorksRight",
      "http_method": "GET",
      "category": "企业信息",
      "display_name": "企业作品著作权",
      "description": "分页查询企业作品著作权。",
      "endpoint": "https://open.chineselaw.com/open/rh_enterpriseWorksRight",
      "known_parameter_names": [
        "id",
        "tyshxydm",
        "pageNo",
        "pageSize"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_enterpriseWorksRight.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-enterprise-icp",
      "route_key": "rh_enterpriseIcp",
      "http_method": "GET",
      "category": "企业信息",
      "display_name": "企业网站备案",
      "description": "分页查询企业网站备案。",
      "endpoint": "https://open.chineselaw.com/open/rh_enterpriseIcp",
      "known_parameter_names": [
        "id",
        "tyshxydm",
        "pageNo",
        "pageSize"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_enterpriseIcp.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-enterprise-change-info",
      "route_key": "rh_enterpriseChangeInfo",
      "http_method": "GET",
      "category": "企业信息",
      "display_name": "企业变更记录",
      "description": "分页查询企业变更记录。",
      "endpoint": "https://open.chineselaw.com/open/rh_enterpriseChangeInfo",
      "known_parameter_names": [
        "id",
        "tyshxydm",
        "pageNo",
        "pageSize"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_enterpriseChangeInfo.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-enterprise-writ-agg",
      "route_key": "rh_enterpriseWritAgg",
      "http_method": "GET",
      "category": "企业信息",
      "display_name": "企业涉诉统计",
      "description": "查询企业涉诉信息多维统计。",
      "endpoint": "https://open.chineselaw.com/open/rh_enterpriseWritAgg",
      "known_parameter_names": [
        "id",
        "tyshxydm"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_enterpriseWritAgg.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-enterprise-writ-list",
      "route_key": "rh_enterpriseWritList",
      "http_method": "GET",
      "category": "企业信息",
      "display_name": "企业涉诉文书",
      "description": "分页查询企业涉诉文书摘要。",
      "endpoint": "https://open.chineselaw.com/open/rh_enterpriseWritList",
      "known_parameter_names": [
        "id",
        "tyshxydm",
        "pageNo",
        "pageSize"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_enterpriseWritList.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-enterprise-court-session-notice",
      "route_key": "rh_enterpriseCourtSessionNotice",
      "http_method": "GET",
      "category": "企业信息",
      "display_name": "企业开庭公告",
      "description": "分页查询企业开庭公告。",
      "endpoint": "https://open.chineselaw.com/open/rh_enterpriseCourtSessionNotice",
      "known_parameter_names": [
        "id",
        "tyshxydm",
        "pageNo",
        "pageSize"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_enterpriseCourtSessionNotice.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-enterprise-court-notice",
      "route_key": "rh_enterpriseCourtNotice",
      "http_method": "GET",
      "category": "企业信息",
      "display_name": "企业法院公告",
      "description": "分页查询企业法院公告。",
      "endpoint": "https://open.chineselaw.com/open/rh_enterpriseCourtNotice",
      "known_parameter_names": [
        "id",
        "tyshxydm",
        "pageNo",
        "pageSize"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_enterpriseCourtNotice.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-enterprise-executions",
      "route_key": "rh_enterpriseExecutions",
      "http_method": "GET",
      "category": "企业信息",
      "display_name": "企业失信被执行人",
      "description": "分页查询企业失信被执行人记录。",
      "endpoint": "https://open.chineselaw.com/open/rh_enterpriseExecutions",
      "known_parameter_names": [
        "id",
        "tyshxydm",
        "pageNo",
        "pageSize"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_enterpriseExecutions.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-enterprise-executed-person",
      "route_key": "rh_enterpriseExecutedPerson",
      "http_method": "GET",
      "category": "企业信息",
      "display_name": "企业被执行人",
      "description": "分页查询企业被执行人记录。",
      "endpoint": "https://open.chineselaw.com/open/rh_enterpriseExecutedPerson",
      "known_parameter_names": [
        "id",
        "tyshxydm",
        "pageNo",
        "pageSize"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_enterpriseExecutedPerson.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-enterprise-frozen-equity",
      "route_key": "rh_enterpriseFrozenEquity",
      "http_method": "GET",
      "category": "企业信息",
      "display_name": "企业股权冻结",
      "description": "分页查询企业股权冻结。",
      "endpoint": "https://open.chineselaw.com/open/rh_enterpriseFrozenEquity",
      "known_parameter_names": [
        "id",
        "tyshxydm",
        "pageNo",
        "pageSize"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_enterpriseFrozenEquity.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-enterprise-punishment",
      "route_key": "rh_enterprisePunishment",
      "http_method": "GET",
      "category": "企业信息",
      "display_name": "企业行政处罚",
      "description": "分页查询企业行政处罚。",
      "endpoint": "https://open.chineselaw.com/open/rh_enterprisePunishment",
      "known_parameter_names": [
        "id",
        "tyshxydm",
        "pageNo",
        "pageSize"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_enterprisePunishment.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-enterprise-pledge",
      "route_key": "rh_enterprisePledge",
      "http_method": "GET",
      "category": "企业信息",
      "display_name": "企业股权出质",
      "description": "分页查询企业股权出质。",
      "endpoint": "https://open.chineselaw.com/open/rh_enterprisePledge",
      "known_parameter_names": [
        "id",
        "tyshxydm",
        "pageNo",
        "pageSize"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_enterprisePledge.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-enterprise-guaranty",
      "route_key": "rh_enterpriseGuaranty",
      "http_method": "GET",
      "category": "企业信息",
      "display_name": "企业对外担保",
      "description": "分页查询企业对外担保。",
      "endpoint": "https://open.chineselaw.com/open/rh_enterpriseGuaranty",
      "known_parameter_names": [
        "id",
        "tyshxydm",
        "pageNo",
        "pageSize"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_enterpriseGuaranty.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-enterprise-abnormal-operation",
      "route_key": "rh_enterpriseAbnormalOperation",
      "http_method": "GET",
      "category": "企业信息",
      "display_name": "企业经营异常",
      "description": "分页查询企业经营异常记录。",
      "endpoint": "https://open.chineselaw.com/open/rh_enterpriseAbnormalOperation",
      "known_parameter_names": [
        "id",
        "tyshxydm",
        "pageNo",
        "pageSize"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_enterpriseAbnormalOperation.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-enterprise-corporate-tax",
      "route_key": "rh_enterpriseCorporateTax",
      "http_method": "GET",
      "category": "企业信息",
      "display_name": "企业欠税公告",
      "description": "分页查询企业欠税公告。",
      "endpoint": "https://open.chineselaw.com/open/rh_enterpriseCorporateTax",
      "known_parameter_names": [
        "id",
        "tyshxydm",
        "pageNo",
        "pageSize"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_enterpriseCorporateTax.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-enterprise-serious-illegal",
      "route_key": "rh_enterpriseSeriousIllegal",
      "http_method": "GET",
      "category": "企业信息",
      "display_name": "企业严重违法",
      "description": "分页查询企业严重违法记录。",
      "endpoint": "https://open.chineselaw.com/open/rh_enterpriseSeriousIllegal",
      "known_parameter_names": [
        "id",
        "tyshxydm",
        "pageNo",
        "pageSize"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_enterpriseSeriousIllegal.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-company-detail",
      "route_key": "rh_company_detail",
      "http_method": "GET",
      "category": "企业信息",
      "display_name": "企业聚合详情",
      "description": "按企业ID或统一社会信用代码查询企业聚合详情。",
      "endpoint": "https://open.chineselaw.com/open/rh_company_detail",
      "known_parameter_names": [
        "id",
        "tyshxydm"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_company_detail.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-rh-company-info",
      "route_key": "rh_company_info",
      "http_method": "GET",
      "category": "企业信息",
      "display_name": "企业名称详情检索",
      "description": "按企业名称、曾用名或股票简称检索候选企业详情。",
      "endpoint": "https://open.chineselaw.com/open/rh_company_info",
      "known_parameter_names": [
        "name",
        "num"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/rh_company_info.html",
      "read_only": true
    },
    {
      "operation_id": "yuandian-hall-detect",
      "route_key": "hall_detect",
      "http_method": "POST",
      "category": "幻觉检测",
      "display_name": "法律幻觉校验",
      "description": "校验文本中的法规、法条和案号引用，返回时效性与权威原文核验结果。",
      "endpoint": "https://open.chineselaw.com/open/hall_detect",
      "known_parameter_names": [
        "text"
      ],
      "full_contract_discovery": "https://open.chineselaw.com/api-docs/hall_detect.html",
      "read_only": true
    }
  ]
}
```

限制：

```json
{
  "max_operations_per_ticket": 1,
  "max_response_bytes_default": 1000000,
  "max_response_bytes_hard": 5000000,
  "timeout_seconds_default": 60,
  "timeout_seconds_hard": 120,
  "max_argument_properties": 60,
  "max_argument_depth": 6,
  "max_array_items": 200,
  "fixed_origin": "https://open.chineselaw.com",
  "snapshot_api_count": 37,
  "live_catalog_page_size_hard": 200,
  "arbitrary_urls_allowed": false,
  "arbitrary_headers_allowed": false,
  "arbitrary_code_allowed": false,
  "write_operations_allowed": false,
  "secret_values_exposed": false,
  "direct_personal_identifiers_redacted": true,
  "billing_unit": "POINT",
  "documented_cost_range_points_per_call": [
    1,
    50
  ]
}
```

## 高德坐标转换 (`amap-coordinate-convert`)

- 状态：`启用`
- 说明：将GPS、百度、图吧等坐标批量转换为高德坐标。
- 适用：将GPS、百度、图吧等坐标批量转换为高德坐标。
- 地域：中国大陆
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/amap-coordinate-convert.connector.json`
- Secret环境变量名：`AMAP_API_KEY`（仅名称）
- 连接器SHA-256：`c804d41b4ffa22a20603615e967fe81ffa8dc33918d47bde680473b6b6c80b90`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "locations",
    "coordsys"
  ],
  "parameter_rules": {
    "properties": {
      "locations": {
        "type": "string",
        "min_length": 3,
        "max_length": 4096
      },
      "coordsys": {
        "type": "string",
        "enum": [
          "gps",
          "mapbar",
          "baidu",
          "autonavi"
        ]
      }
    },
    "required_any_of": [
      [
        "locations"
      ]
    ]
  },
  "parameter_notes": {
    "locations": "高德官方参数；按接口文档填写",
    "coordsys": "高德官方参数；按接口文档填写"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    "1"
  ],
  "error_code_path": "infocode",
  "message_path": "info",
  "any_data_paths": [
    "locations"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://restapi.amap.com",
  "url_pattern": "/v3/assistant/coordinate/convert",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "info",
    "infocode",
    "count",
    "locations"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 受高德账户配额、权限和上游数据覆盖限制

## 高德骑行路线规划 (`amap-direction-bicycling`)

- 状态：`启用`
- 说明：取得自行车路线、距离、预计时间和步骤。
- 适用：取得自行车路线、距离、预计时间和步骤。
- 地域：中国大陆
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/amap-direction-bicycling.connector.json`
- Secret环境变量名：`AMAP_API_KEY`（仅名称）
- 连接器SHA-256：`65d22ecf78396de2e9d7159d572c9744144a32717a6d47db93e044c0337fd088`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "origin",
    "destination",
    "show_fields"
  ],
  "parameter_rules": {
    "properties": {
      "origin": {
        "type": "string",
        "min_length": 3,
        "max_length": 200
      },
      "destination": {
        "type": "string",
        "min_length": 3,
        "max_length": 200
      }
    },
    "required_any_of": [
      [
        "origin"
      ],
      [
        "destination"
      ]
    ]
  },
  "parameter_notes": {
    "origin": "高德官方参数；按接口文档填写",
    "destination": "高德官方参数；按接口文档填写",
    "show_fields": "高德官方参数；按接口文档填写"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    "1"
  ],
  "error_code_path": "infocode",
  "message_path": "info",
  "any_data_paths": [
    "route"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://restapi.amap.com",
  "url_pattern": "/v5/direction/bicycling",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "info",
    "infocode",
    "count",
    "route"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 受高德账户配额、权限和上游数据覆盖限制

## 高德驾车路线规划 (`amap-direction-driving`)

- 状态：`启用`
- 说明：根据起点、终点及可选途经点取得驾车路线、距离、预计时间和路线步骤。
- 适用：路线比较；通勤与配送测算；候选区域之间的行驶成本估算
- 地域：中国大陆
- 新鲜度：请求时实时返回；交通时效以供应商响应为准
- 成本等级：`provider-quota`
- 详情文件：`connectors/amap-direction-driving.connector.json`
- Secret环境变量名：`AMAP_API_KEY`（仅名称）
- 连接器SHA-256：`17ea913d9880ac5b6125d1d76fb3a6da5c95128d30098997075a675e9b0421ed`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "origin",
    "destination",
    "waypoints",
    "strategy",
    "avoidpolygons",
    "avoidroad",
    "plate",
    "cartype",
    "ferry",
    "show_fields"
  ],
  "parameter_rules": {},
  "parameter_notes": {
    "origin": "必填；经度,纬度",
    "destination": "必填；经度,纬度",
    "waypoints": "可选；途经点",
    "strategy": "可选；路线策略",
    "show_fields": "可选；扩展返回字段"
  },
  "example_parameters": {
    "origin": "119.2965,26.0745",
    "destination": "119.3062,26.0637"
  },
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    "1"
  ],
  "error_code_path": "infocode",
  "message_path": "info",
  "any_data_paths": [
    "route"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://restapi.amap.com",
  "url_pattern": "/v5/direction/driving",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "info",
    "infocode",
    "count",
    "route"
  ],
  "resilience": {},
  "rate_limit_enabled": false,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 不代表网约车平台实时订单热度
- 交通时间可能受实时拥堵和供应商策略影响

## 高德公交综合路径规划 (`amap-direction-transit`)

- 状态：`启用`
- 说明：取得公交、地铁等公共交通换乘方案。
- 适用：取得公交、地铁等公共交通换乘方案。
- 地域：中国大陆
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/amap-direction-transit.connector.json`
- Secret环境变量名：`AMAP_API_KEY`（仅名称）
- 连接器SHA-256：`036a5db52eac86fc157897c4647ce55536a36e73713da83ca1fa914eb0243599`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "origin",
    "destination",
    "city1",
    "city2",
    "strategy",
    "nightflag",
    "date",
    "time",
    "show_fields"
  ],
  "parameter_rules": {
    "properties": {
      "origin": {
        "type": "string",
        "min_length": 3,
        "max_length": 200
      },
      "destination": {
        "type": "string",
        "min_length": 3,
        "max_length": 200
      },
      "strategy": {
        "type": "integer",
        "minimum": 0,
        "maximum": 8
      }
    },
    "required_any_of": [
      [
        "origin"
      ],
      [
        "destination"
      ],
      [
        "city1"
      ]
    ]
  },
  "parameter_notes": {
    "origin": "高德官方参数；按接口文档填写",
    "destination": "高德官方参数；按接口文档填写",
    "city1": "高德官方参数；按接口文档填写",
    "city2": "高德官方参数；按接口文档填写",
    "strategy": "高德官方参数；按接口文档填写",
    "nightflag": "高德官方参数；按接口文档填写",
    "date": "高德官方参数；按接口文档填写",
    "time": "高德官方参数；按接口文档填写",
    "show_fields": "高德官方参数；按接口文档填写"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    "1"
  ],
  "error_code_path": "infocode",
  "message_path": "info",
  "any_data_paths": [
    "route"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://restapi.amap.com",
  "url_pattern": "/v5/direction/transit/integrated",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "info",
    "infocode",
    "count",
    "route"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 受高德账户配额、权限和上游数据覆盖限制

## 高德步行路线规划 (`amap-direction-walking`)

- 状态：`启用`
- 说明：取得两点之间的步行路线、距离、预计时间和路线步骤。
- 适用：短距离可达性；最后一公里分析；步行接驳测算
- 地域：中国大陆
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/amap-direction-walking.connector.json`
- Secret环境变量名：`AMAP_API_KEY`（仅名称）
- 连接器SHA-256：`57fbda206123099aa2c731e60d04582001ce0f79aa32c9cc7d8dc63ae952e7d4`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "origin",
    "destination",
    "origin_id",
    "destination_id",
    "show_fields"
  ],
  "parameter_rules": {},
  "parameter_notes": {
    "origin": "必填；经度,纬度",
    "destination": "必填；经度,纬度",
    "show_fields": "可选；扩展返回字段"
  },
  "example_parameters": {
    "origin": "119.2965,26.0745",
    "destination": "119.3000,26.0700"
  },
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    "1"
  ],
  "error_code_path": "infocode",
  "message_path": "info",
  "any_data_paths": [
    "route"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://restapi.amap.com",
  "url_pattern": "/v5/direction/walking",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "info",
    "infocode",
    "count",
    "route"
  ],
  "resilience": {},
  "rate_limit_enabled": false,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 不包含实时人流量
- 道路施工或临时封闭可能存在延迟

## 高德多点距离测量 (`amap-distance`)

- 状态：`启用`
- 说明：计算一个或多个起点到目标点的距离和预计时间。
- 适用：候选地点排序；多起点成本比较；配送与接驳半径测算
- 地域：中国大陆
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/amap-distance.connector.json`
- Secret环境变量名：`AMAP_API_KEY`（仅名称）
- 连接器SHA-256：`f5b496e25bfe652cda2008f73ea1344d9f6b2c01772107be70aeb63710b77aae`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "origins",
    "destination",
    "type"
  ],
  "parameter_rules": {},
  "parameter_notes": {
    "origins": "必填；一个或多个起点坐标",
    "destination": "必填；目标坐标",
    "type": "可选；距离计算类型"
  },
  "example_parameters": {
    "origins": "119.2965,26.0745|119.3100,26.0800",
    "destination": "119.3062,26.0637",
    "type": "1"
  },
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    "1"
  ],
  "error_code_path": "infocode",
  "message_path": "info",
  "any_data_paths": [
    "results"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://restapi.amap.com",
  "url_pattern": "/v3/distance",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "info",
    "infocode",
    "results"
  ],
  "resilience": {},
  "rate_limit_enabled": false,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 仅提供距离和时间，不提供订单需求概率

## 高德行政区域查询 (`amap-district`)

- 状态：`启用`
- 说明：按名称或行政编码读取省、市、区县、街道层级及边界。
- 适用：按名称或行政编码读取省、市、区县、街道层级及边界。
- 地域：中国大陆
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/amap-district.connector.json`
- Secret环境变量名：`AMAP_API_KEY`（仅名称）
- 连接器SHA-256：`c4f384fb2e512607c2d4d05b5992a13a645fd585e67ddce113de6f56eb485c05`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "keywords",
    "subdistrict",
    "showbiz",
    "extensions",
    "filter"
  ],
  "parameter_rules": {
    "properties": {
      "keywords": {
        "type": "string",
        "min_length": 1,
        "max_length": 200
      },
      "subdistrict": {
        "type": "integer",
        "minimum": 0,
        "maximum": 3
      }
    },
    "required_any_of": [
      [
        "keywords"
      ]
    ]
  },
  "parameter_notes": {
    "keywords": "高德官方参数；按接口文档填写",
    "subdistrict": "高德官方参数；按接口文档填写",
    "showbiz": "高德官方参数；按接口文档填写",
    "extensions": "高德官方参数；按接口文档填写",
    "filter": "高德官方参数；按接口文档填写"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    "1"
  ],
  "error_code_path": "infocode",
  "message_path": "info",
  "any_data_paths": [
    "districts"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://restapi.amap.com",
  "url_pattern": "/v3/config/district",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "info",
    "infocode",
    "count",
    "districts"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 受高德账户配额、权限和上游数据覆盖限制

## 高德地址转坐标 (`amap-geocode`)

- 状态：`启用`
- 说明：把公开地址转换为经纬度坐标和标准化地址信息。
- 适用：地点定位；路线任务准备；公开地址标准化
- 地域：中国大陆
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/amap-geocode.connector.json`
- Secret环境变量名：`AMAP_API_KEY`（仅名称）
- 连接器SHA-256：`76cd76a735a9bff1bcbef92cd18881600c9d67f22cef8c856851e6da2a3565b5`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "address",
    "city",
    "batch"
  ],
  "parameter_rules": {},
  "parameter_notes": {
    "address": "必填；公开地址",
    "city": "建议填写；城市或行政区",
    "batch": "可选；是否批量"
  },
  "example_parameters": {
    "address": "福州宝龙城市广场",
    "city": "福州"
  },
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    "1"
  ],
  "error_code_path": "infocode",
  "message_path": "info",
  "any_data_paths": [
    "geocodes"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://restapi.amap.com",
  "url_pattern": "/v3/geocode/geo",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "info",
    "infocode",
    "count",
    "geocodes"
  ],
  "resilience": {},
  "rate_limit_enabled": false,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 模糊地址可能返回多个候选
- 不得提交私人住宅精确地址或个人轨迹

## 高德输入提示 (`amap-inputtips`)

- 状态：`启用`
- 说明：根据关键词、城市和位置返回POI、公交站或线路建议词。
- 适用：根据关键词、城市和位置返回POI、公交站或线路建议词。
- 地域：中国大陆
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/amap-inputtips.connector.json`
- Secret环境变量名：`AMAP_API_KEY`（仅名称）
- 连接器SHA-256：`5d5b7a7c40245a5cba82197ee03e6cd0a090b6b4eb91be9c43ac426b6d1a3fdb`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "keywords",
    "type",
    "location",
    "city",
    "citylimit",
    "datatype"
  ],
  "parameter_rules": {
    "properties": {
      "keywords": {
        "type": "string",
        "min_length": 1,
        "max_length": 200
      },
      "location": {
        "type": "string",
        "min_length": 3,
        "max_length": 200
      }
    },
    "required_any_of": [
      [
        "keywords"
      ]
    ]
  },
  "parameter_notes": {
    "keywords": "高德官方参数；按接口文档填写",
    "type": "高德官方参数；按接口文档填写",
    "location": "高德官方参数；按接口文档填写",
    "city": "高德官方参数；按接口文档填写",
    "citylimit": "高德官方参数；按接口文档填写",
    "datatype": "高德官方参数；按接口文档填写"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    "1"
  ],
  "error_code_path": "infocode",
  "message_path": "info",
  "any_data_paths": [
    "tips"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://restapi.amap.com",
  "url_pattern": "/v3/assistant/inputtips",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "info",
    "infocode",
    "count",
    "tips"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 受高德账户配额、权限和上游数据覆盖限制

## 高德IP定位 (`amap-ip-location`)

- 状态：`启用`
- 说明：将中国大陆IP地址解析到省市和矩形范围。
- 适用：将中国大陆IP地址解析到省市和矩形范围。
- 地域：中国大陆
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/amap-ip-location.connector.json`
- Secret环境变量名：`AMAP_API_KEY`（仅名称）
- 连接器SHA-256：`a379a011ed2d66575501aeaa90b8dc81f7e656437a7b00e8453cae6589911734`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "ip"
  ],
  "parameter_rules": {
    "properties": {
      "ip": {
        "type": "string",
        "min_length": 3,
        "max_length": 64
      }
    }
  },
  "parameter_notes": {
    "ip": "高德官方参数；按接口文档填写"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    "1"
  ],
  "error_code_path": "infocode",
  "message_path": "info",
  "any_data_paths": [
    "province",
    "city",
    "adcode",
    "rectangle"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://restapi.amap.com",
  "url_pattern": "/v3/ip",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "info",
    "infocode",
    "count",
    "province",
    "city",
    "adcode",
    "rectangle"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 精度通常为城市级，不得用于个人精确定位

## 高德周边POI搜索 (`amap-place-around`)

- 状态：`启用`
- 说明：按中心点和半径搜索餐饮、商业、交通、公共服务等POI。
- 适用：按中心点和半径搜索餐饮、商业、交通、公共服务等POI。
- 地域：中国大陆
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/amap-place-around.connector.json`
- Secret环境变量名：`AMAP_API_KEY`（仅名称）
- 连接器SHA-256：`d3fe97778f8666a635cfd0ffd6bc45db6ab81c290cfd2ca7154d09979234e37c`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "keywords",
    "types",
    "location",
    "radius",
    "sortrule",
    "region",
    "show_fields",
    "page_size",
    "page_num"
  ],
  "parameter_rules": {
    "properties": {
      "location": {
        "type": "string",
        "min_length": 3,
        "max_length": 200
      },
      "radius": {
        "type": "integer",
        "minimum": 1,
        "maximum": 50000
      },
      "page_size": {
        "type": "integer",
        "minimum": 1,
        "maximum": 25
      },
      "page_num": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100
      }
    },
    "required_any_of": [
      [
        "location"
      ]
    ]
  },
  "parameter_notes": {
    "keywords": "高德官方参数；按接口文档填写",
    "types": "高德官方参数；按接口文档填写",
    "location": "高德官方参数；按接口文档填写",
    "radius": "高德官方参数；按接口文档填写",
    "sortrule": "高德官方参数；按接口文档填写",
    "region": "高德官方参数；按接口文档填写",
    "show_fields": "高德官方参数；按接口文档填写",
    "page_size": "高德官方参数；按接口文档填写",
    "page_num": "高德官方参数；按接口文档填写"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    "1"
  ],
  "error_code_path": "infocode",
  "message_path": "info",
  "any_data_paths": [
    "pois"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://restapi.amap.com",
  "url_pattern": "/v5/place/around",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "info",
    "infocode",
    "count",
    "pois"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 受高德账户配额、权限和上游数据覆盖限制

## 高德POI详情 (`amap-place-detail`)

- 状态：`启用`
- 说明：按高德POI ID读取地址、坐标、分类和扩展详情。
- 适用：按高德POI ID读取地址、坐标、分类和扩展详情。
- 地域：中国大陆
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/amap-place-detail.connector.json`
- Secret环境变量名：`AMAP_API_KEY`（仅名称）
- 连接器SHA-256：`31cb2b93818d7bade358890e0c2d3f718114ce5e4ea030e3479f715800abfbc1`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "id",
    "show_fields"
  ],
  "parameter_rules": {
    "properties": {
      "id": {
        "type": "string",
        "min_length": 1,
        "max_length": 200
      }
    },
    "required_any_of": [
      [
        "id"
      ]
    ]
  },
  "parameter_notes": {
    "id": "高德官方参数；按接口文档填写",
    "show_fields": "高德官方参数；按接口文档填写"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    "1"
  ],
  "error_code_path": "infocode",
  "message_path": "info",
  "any_data_paths": [
    "pois"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://restapi.amap.com",
  "url_pattern": "/v5/place/detail",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "info",
    "infocode",
    "count",
    "pois"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 受高德账户配额、权限和上游数据覆盖限制

## 高德多边形POI搜索 (`amap-place-polygon`)

- 状态：`启用`
- 说明：在指定多边形范围内搜索POI。
- 适用：在指定多边形范围内搜索POI。
- 地域：中国大陆
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/amap-place-polygon.connector.json`
- Secret环境变量名：`AMAP_API_KEY`（仅名称）
- 连接器SHA-256：`983b274da05900c920a2552a7fb09afc9622136e3c3c518264387e185741a489`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "polygon",
    "keywords",
    "types",
    "show_fields",
    "page_size",
    "page_num"
  ],
  "parameter_rules": {
    "properties": {
      "polygon": {
        "type": "string",
        "min_length": 10,
        "max_length": 4096
      },
      "page_size": {
        "type": "integer",
        "minimum": 1,
        "maximum": 25
      },
      "page_num": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100
      }
    },
    "required_any_of": [
      [
        "polygon"
      ]
    ]
  },
  "parameter_notes": {
    "polygon": "高德官方参数；按接口文档填写",
    "keywords": "高德官方参数；按接口文档填写",
    "types": "高德官方参数；按接口文档填写",
    "show_fields": "高德官方参数；按接口文档填写",
    "page_size": "高德官方参数；按接口文档填写",
    "page_num": "高德官方参数；按接口文档填写"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    "1"
  ],
  "error_code_path": "infocode",
  "message_path": "info",
  "any_data_paths": [
    "pois"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://restapi.amap.com",
  "url_pattern": "/v5/place/polygon",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "info",
    "infocode",
    "count",
    "pois"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 受高德账户配额、权限和上游数据覆盖限制

## 高德 POI 关键词搜索 (`amap-place-text`)

- 状态：`启用`
- 说明：按关键词、类型和区域搜索公开兴趣点及其坐标、地址和类别。
- 适用：候选地点发现；商圈与设施清单；公开地点核验
- 地域：中国大陆
- 新鲜度：请求时返回；POI 更新频率由供应商决定
- 成本等级：`provider-quota`
- 详情文件：`connectors/amap-place-text.connector.json`
- Secret环境变量名：`AMAP_API_KEY`（仅名称）
- 连接器SHA-256：`1e0a6151c5c88814877ba69d70dc34ccfe1d7c36c8ccebe218ed634bc2e1a9ce`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "keywords",
    "types",
    "region",
    "city_limit",
    "show_fields",
    "page_size",
    "page_num"
  ],
  "parameter_rules": {},
  "parameter_notes": {
    "keywords": "必填或与types至少填写一项",
    "types": "可选；POI类别",
    "region": "建议填写；城市或行政区",
    "page_size": "可选；单页数量",
    "page_num": "可选；页码"
  },
  "example_parameters": {
    "keywords": "商场",
    "region": "福州",
    "page_size": 20,
    "page_num": 1
  },
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    "1"
  ],
  "error_code_path": "infocode",
  "message_path": "info",
  "any_data_paths": [
    "pois"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://restapi.amap.com",
  "url_pattern": "/v5/place/text",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "info",
    "infocode",
    "count",
    "pois"
  ],
  "resilience": {},
  "rate_limit_enabled": false,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- POI数量不等于实时客流或订单量
- 分页结果受供应商上限影响

## 高德坐标转地址 (`amap-regeocode`)

- 状态：`启用`
- 说明：把公开经纬度转换为标准地址、道路和附近公开兴趣点信息。
- 适用：坐标说明；区域归属核验；公开地点上下文补充
- 地域：中国大陆
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/amap-regeocode.connector.json`
- Secret环境变量名：`AMAP_API_KEY`（仅名称）
- 连接器SHA-256：`bac6fa7f5da6be5b711bd6e14a94b61b3d6f138b70efe9b4797dfbd5bbeb2800`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "location",
    "poitype",
    "radius",
    "extensions",
    "roadlevel",
    "homeorcorp"
  ],
  "parameter_rules": {},
  "parameter_notes": {
    "location": "必填；经度,纬度",
    "radius": "可选；搜索半径",
    "extensions": "可选；基础或完整结果"
  },
  "example_parameters": {
    "location": "119.2965,26.0745",
    "extensions": "all"
  },
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    "1"
  ],
  "error_code_path": "infocode",
  "message_path": "info",
  "any_data_paths": [
    "regeocode"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://restapi.amap.com",
  "url_pattern": "/v3/geocode/regeo",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "info",
    "infocode",
    "regeocode"
  ],
  "resilience": {},
  "rate_limit_enabled": false,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 不得用于处理私人实时轨迹
- 附近POI并不代表实时需求

## 高德圆形范围路况 (`amap-traffic-circle`)

- 状态：`启用`
- 说明：按中心点和半径读取实时道路拥堵状态。
- 适用：按中心点和半径读取实时道路拥堵状态。
- 地域：中国大陆
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/amap-traffic-circle.connector.json`
- Secret环境变量名：`AMAP_API_KEY`（仅名称）
- 连接器SHA-256：`58e7b6a0a8f40ae91e44152231f9813038e222f91ef883772f082d34cf9d61d2`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "location",
    "radius",
    "level",
    "extensions"
  ],
  "parameter_rules": {
    "properties": {
      "location": {
        "type": "string",
        "min_length": 3,
        "max_length": 200
      }
    },
    "required_any_of": [
      [
        "location"
      ]
    ]
  },
  "parameter_notes": {
    "location": "高德官方参数；按接口文档填写",
    "radius": "高德官方参数；按接口文档填写",
    "level": "高德官方参数；按接口文档填写",
    "extensions": "高德官方参数；按接口文档填写"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    "1"
  ],
  "error_code_path": "infocode",
  "message_path": "info",
  "any_data_paths": [
    "trafficinfo"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://restapi.amap.com",
  "url_pattern": "/v3/traffic/status/circle",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "info",
    "infocode",
    "count",
    "trafficinfo"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 受高德账户配额、权限和上游数据覆盖限制

## 高德矩形范围路况 (`amap-traffic-rectangle`)

- 状态：`启用`
- 说明：按矩形范围读取实时道路拥堵状态。
- 适用：按矩形范围读取实时道路拥堵状态。
- 地域：中国大陆
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/amap-traffic-rectangle.connector.json`
- Secret环境变量名：`AMAP_API_KEY`（仅名称）
- 连接器SHA-256：`f8297b190beb4338f53e0cc7f7a7615020c451e3c90762545685b1fe3686f44b`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "rectangle",
    "level",
    "extensions"
  ],
  "parameter_rules": {
    "properties": {
      "rectangle": {
        "type": "string",
        "min_length": 3,
        "max_length": 200
      }
    },
    "required_any_of": [
      [
        "rectangle"
      ]
    ]
  },
  "parameter_notes": {
    "rectangle": "高德官方参数；按接口文档填写",
    "level": "高德官方参数；按接口文档填写",
    "extensions": "高德官方参数；按接口文档填写"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    "1"
  ],
  "error_code_path": "infocode",
  "message_path": "info",
  "any_data_paths": [
    "trafficinfo"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://restapi.amap.com",
  "url_pattern": "/v3/traffic/status/rectangle",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "info",
    "infocode",
    "count",
    "trafficinfo"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 受高德账户配额、权限和上游数据覆盖限制

## 高德指定道路路况 (`amap-traffic-road`)

- 状态：`启用`
- 说明：按道路名称和行政编码读取实时道路拥堵状态。
- 适用：按道路名称和行政编码读取实时道路拥堵状态。
- 地域：中国大陆
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/amap-traffic-road.connector.json`
- Secret环境变量名：`AMAP_API_KEY`（仅名称）
- 连接器SHA-256：`972cecfd7e238704e8320ef98f14198211ac325a43c716b9c86e94b6dd276712`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "name",
    "adcode",
    "level",
    "extensions"
  ],
  "parameter_rules": {
    "properties": {
      "name": {
        "type": "string",
        "min_length": 1,
        "max_length": 200
      },
      "adcode": {
        "type": "string",
        "min_length": 1,
        "max_length": 200
      }
    },
    "required_any_of": [
      [
        "name"
      ],
      [
        "adcode"
      ]
    ]
  },
  "parameter_notes": {
    "name": "高德官方参数；按接口文档填写",
    "adcode": "高德官方参数；按接口文档填写",
    "level": "高德官方参数；按接口文档填写",
    "extensions": "高德官方参数；按接口文档填写"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    "1"
  ],
  "error_code_path": "infocode",
  "message_path": "info",
  "any_data_paths": [
    "trafficinfo"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://restapi.amap.com",
  "url_pattern": "/v3/traffic/status/road",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "info",
    "infocode",
    "count",
    "trafficinfo"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 受高德账户配额、权限和上游数据覆盖限制

## 高德城市天气 (`amap-weather`)

- 状态：`启用`
- 说明：取得指定城市的实时天气或预报信息。
- 适用：需求情景调整；出行风险分析；配送和网约车天气修正
- 地域：中国大陆
- 新鲜度：实时或预报；以响应时间为准
- 成本等级：`provider-quota`
- 详情文件：`connectors/amap-weather.connector.json`
- Secret环境变量名：`AMAP_API_KEY`（仅名称）
- 连接器SHA-256：`d86b2afd7067da126fe4d377222fef5824975f0333ae09bf75a4f819b29ff608`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "city",
    "extensions"
  ],
  "parameter_rules": {},
  "parameter_notes": {
    "city": "必填；行政区代码或城市标识",
    "extensions": "可选；base为实时，all为预报"
  },
  "example_parameters": {
    "city": "350100",
    "extensions": "base"
  },
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    "1"
  ],
  "error_code_path": "infocode",
  "message_path": "info",
  "any_data_paths": [
    "lives",
    "forecasts"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://restapi.amap.com",
  "url_pattern": "/v3/weather/weatherInfo",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "info",
    "infocode",
    "count",
    "lives",
    "forecasts"
  ],
  "resilience": {},
  "rate_limit_enabled": false,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 天气预报存在不确定性
- 不能替代平台订单或交通实时数据

## 百度坐标转换 (`baidu-coordinate-convert`)

- 状态：`启用`
- 说明：在WGS84、GCJ02、百度经纬度和墨卡托坐标之间转换。
- 适用：在WGS84、GCJ02、百度经纬度和墨卡托坐标之间转换。
- 地域：中国大陆；部分位置服务支持全球
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/baidu-coordinate-convert.connector.json`
- Secret环境变量名：`BAIDU_MAP_API_KEY`（仅名称）
- 连接器SHA-256：`577518d1537fc78f58d21dda564ed46e3fbfef0be64b57d8e89dacc6d76f05ea`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "coords",
    "from",
    "to"
  ],
  "parameter_rules": {
    "properties": {
      "coords": {
        "type": "string",
        "min_length": 3,
        "max_length": 4096
      },
      "from": {
        "type": "integer",
        "minimum": 1,
        "maximum": 6
      },
      "to": {
        "type": "integer",
        "minimum": 3,
        "maximum": 6
      }
    },
    "required_any_of": [
      [
        "coords"
      ],
      [
        "from"
      ],
      [
        "to"
      ]
    ]
  },
  "parameter_notes": {
    "coords": "百度地图官方参数；按接口文档填写",
    "from": "百度地图官方参数；按接口文档填写",
    "to": "百度地图官方参数；按接口文档填写"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    0
  ],
  "message_path": "message",
  "any_data_paths": [
    "result"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.map.baidu.com",
  "url_pattern": "/geoconv/v1/",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "message",
    "result"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 受百度地图账户权限、配额和数据覆盖限制

## 百度地图驾车路线规划 (`baidu-direction-driving`)

- 状态：`启用`
- 说明：根据起终点及可选途经点读取驾车路线、距离、耗时和步骤。
- 适用：路线比较；配送与通勤成本估算；候选区域之间的可达性建模
- 地域：中国；以百度地图道路覆盖为准
- 新鲜度：请求时读取；交通时效以百度响应为准
- 成本等级：`provider-key-quota`
- 详情文件：`connectors/baidu-direction-driving.connector.json`
- Secret环境变量名：`BAIDU_MAP_API_KEY`（仅名称）
- 连接器SHA-256：`e0e09d46fa8a7dc9468a0718d872fd77f642bf444042f0e2d0c38433e8f5b615`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "origin",
    "destination",
    "waypoints",
    "tactics",
    "coord_type",
    "ret_coordtype"
  ],
  "parameter_rules": {
    "properties": {
      "origin": {
        "type": "string",
        "min_length": 3,
        "max_length": 200
      },
      "destination": {
        "type": "string",
        "min_length": 3,
        "max_length": 200
      },
      "waypoints": {
        "type": "string",
        "max_length": 1000
      },
      "tactics": {
        "type": "integer",
        "minimum": 0,
        "maximum": 12
      },
      "coord_type": {
        "type": "string",
        "enum": [
          "bd09ll",
          "gcj02",
          "wgs84"
        ]
      },
      "ret_coordtype": {
        "type": "string",
        "enum": [
          "bd09ll",
          "gcj02"
        ]
      }
    },
    "required_any_of": [
      [
        "origin"
      ],
      [
        "destination"
      ]
    ]
  },
  "parameter_notes": {
    "origin": "必填；坐标或名称",
    "destination": "必填；坐标或名称",
    "waypoints": "可选途经点",
    "tactics": "路线策略",
    "coord_type": "输入坐标类型",
    "ret_coordtype": "返回坐标类型"
  },
  "example_parameters": {
    "origin": "26.0745,119.2965",
    "destination": "26.0637,119.3062",
    "coord_type": "gcj02",
    "ret_coordtype": "gcj02"
  },
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    0
  ],
  "message_path": "message",
  "any_data_paths": [
    "result.routes"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.map.baidu.com",
  "url_pattern": "/directionlite/v1/driving",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "message",
    "result"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 路线耗时不代表网约车订单热度
- 需要BAIDU_MAP_API_KEY
- 实时交通能力和配额取决于百度账户及接口返回
- 坐标顺序和坐标系必须在调用前核验

## 百度riding路线规划 (`baidu-direction-riding`)

- 状态：`启用`
- 说明：取得riding方式的路线、距离、时间和步骤。
- 适用：取得riding方式的路线、距离、时间和步骤。
- 地域：中国大陆；部分位置服务支持全球
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/baidu-direction-riding.connector.json`
- Secret环境变量名：`BAIDU_MAP_API_KEY`（仅名称）
- 连接器SHA-256：`1b1985db481183be1f0cdb845b15db5ea67969ffa776657087c2b4b36a417687`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "origin",
    "destination",
    "coord_type",
    "ret_coordtype"
  ],
  "parameter_rules": {
    "properties": {
      "origin": {
        "type": "string",
        "min_length": 3,
        "max_length": 200
      },
      "destination": {
        "type": "string",
        "min_length": 3,
        "max_length": 200
      }
    },
    "required_any_of": [
      [
        "origin"
      ],
      [
        "destination"
      ]
    ]
  },
  "parameter_notes": {
    "origin": "百度地图官方参数；按接口文档填写",
    "destination": "百度地图官方参数；按接口文档填写",
    "coord_type": "百度地图官方参数；按接口文档填写",
    "ret_coordtype": "百度地图官方参数；按接口文档填写"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    0
  ],
  "message_path": "message",
  "any_data_paths": [
    "result"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.map.baidu.com",
  "url_pattern": "/directionlite/v1/riding",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "message",
    "result"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 受百度地图账户权限、配额和数据覆盖限制

## 百度transit路线规划 (`baidu-direction-transit`)

- 状态：`启用`
- 说明：取得transit方式的路线、距离、时间和步骤。
- 适用：取得transit方式的路线、距离、时间和步骤。
- 地域：中国大陆；部分位置服务支持全球
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/baidu-direction-transit.connector.json`
- Secret环境变量名：`BAIDU_MAP_API_KEY`（仅名称）
- 连接器SHA-256：`d78497dbb8f68de71c0e3ae375c8bdd12232040b509cd92e4661fcecd4adc1bb`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "origin",
    "destination",
    "coord_type",
    "ret_coordtype",
    "region",
    "tactics"
  ],
  "parameter_rules": {
    "properties": {
      "origin": {
        "type": "string",
        "min_length": 3,
        "max_length": 200
      },
      "destination": {
        "type": "string",
        "min_length": 3,
        "max_length": 200
      }
    },
    "required_any_of": [
      [
        "origin"
      ],
      [
        "destination"
      ]
    ]
  },
  "parameter_notes": {
    "origin": "百度地图官方参数；按接口文档填写",
    "destination": "百度地图官方参数；按接口文档填写",
    "coord_type": "百度地图官方参数；按接口文档填写",
    "ret_coordtype": "百度地图官方参数；按接口文档填写",
    "region": "百度地图官方参数；按接口文档填写",
    "tactics": "百度地图官方参数；按接口文档填写"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    0
  ],
  "message_path": "message",
  "any_data_paths": [
    "result"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.map.baidu.com",
  "url_pattern": "/directionlite/v1/transit",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "message",
    "result"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 受百度地图账户权限、配额和数据覆盖限制

## 百度walking路线规划 (`baidu-direction-walking`)

- 状态：`启用`
- 说明：取得walking方式的路线、距离、时间和步骤。
- 适用：取得walking方式的路线、距离、时间和步骤。
- 地域：中国大陆；部分位置服务支持全球
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/baidu-direction-walking.connector.json`
- Secret环境变量名：`BAIDU_MAP_API_KEY`（仅名称）
- 连接器SHA-256：`2c0f941816935cc38fa6aeb730e7cbbbde3a0ce00f059c651f64c25919d5a097`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "origin",
    "destination",
    "coord_type",
    "ret_coordtype"
  ],
  "parameter_rules": {
    "properties": {
      "origin": {
        "type": "string",
        "min_length": 3,
        "max_length": 200
      },
      "destination": {
        "type": "string",
        "min_length": 3,
        "max_length": 200
      }
    },
    "required_any_of": [
      [
        "origin"
      ],
      [
        "destination"
      ]
    ]
  },
  "parameter_notes": {
    "origin": "百度地图官方参数；按接口文档填写",
    "destination": "百度地图官方参数；按接口文档填写",
    "coord_type": "百度地图官方参数；按接口文档填写",
    "ret_coordtype": "百度地图官方参数；按接口文档填写"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    0
  ],
  "message_path": "message",
  "any_data_paths": [
    "result"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.map.baidu.com",
  "url_pattern": "/directionlite/v1/walking",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "message",
    "result"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 受百度地图账户权限、配额和数据覆盖限制

## 百度地图地址转坐标 (`baidu-geocode`)

- 状态：`启用`
- 说明：使用百度地图地理编码服务把公开地址转换为坐标和可信度等结果。
- 适用：公开地点定位；路线任务准备；地址与坐标交叉核验
- 地域：中国；以百度地图覆盖为准
- 新鲜度：请求时读取百度地图当前数据
- 成本等级：`provider-key-quota`
- 详情文件：`connectors/baidu-geocode.connector.json`
- Secret环境变量名：`BAIDU_MAP_API_KEY`（仅名称）
- 连接器SHA-256：`cbffb7b788ab5e19aed770f4e9a7e2cc4b15a58e98a58b21684abe52468da440`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "address",
    "city",
    "output",
    "ret_coordtype"
  ],
  "parameter_rules": {
    "properties": {
      "address": {
        "type": "string",
        "min_length": 1,
        "max_length": 200
      },
      "city": {
        "type": "string",
        "min_length": 1,
        "max_length": 100
      },
      "output": {
        "type": "string",
        "enum": [
          "json"
        ]
      },
      "ret_coordtype": {
        "type": "string",
        "enum": [
          "gcj02ll",
          "bd09ll"
        ]
      }
    },
    "required_any_of": [
      [
        "address"
      ]
    ]
  },
  "parameter_notes": {
    "address": "必填；公开地址",
    "city": "建议填写；城市名称",
    "output": "固定建议json",
    "ret_coordtype": "gcj02ll或bd09ll"
  },
  "example_parameters": {
    "address": "福州宝龙城市广场",
    "city": "福州",
    "output": "json",
    "ret_coordtype": "gcj02ll"
  },
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    0
  ],
  "message_path": "message",
  "any_data_paths": [
    "result"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.map.baidu.com",
  "url_pattern": "/geocoding/v3/",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "result",
    "message"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 需要BAIDU_MAP_API_KEY
- 百度坐标体系与WGS84不同，建模前必须统一坐标
- 不得提交私人住宅精确地址、个人实时位置或轨迹
- 配额和许可由百度地图开放平台账户决定

## 百度IP定位 (`baidu-ip-location`)

- 状态：`启用`
- 说明：将IP地址解析为城市、坐标和地址信息。
- 适用：将IP地址解析为城市、坐标和地址信息。
- 地域：中国大陆；部分位置服务支持全球
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/baidu-ip-location.connector.json`
- Secret环境变量名：`BAIDU_MAP_API_KEY`（仅名称）
- 连接器SHA-256：`56c81a573bc2c78a27138c9398ff820f2128ac2421e381c0ab2c5980918b114a`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "ip",
    "coor"
  ],
  "parameter_rules": {
    "properties": {
      "ip": {
        "type": "string",
        "min_length": 3,
        "max_length": 64
      }
    }
  },
  "parameter_notes": {
    "ip": "百度地图官方参数；按接口文档填写",
    "coor": "百度地图官方参数；按接口文档填写"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    0
  ],
  "message_path": "message",
  "any_data_paths": [
    "content"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.map.baidu.com",
  "url_pattern": "/location/ip",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "message",
    "content"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 精度通常为城市级，不得用于个人精确定位

## 百度地点详情 (`baidu-place-detail`)

- 状态：`启用`
- 说明：按POI UID读取名称、地址、坐标、分类和详情。
- 适用：按POI UID读取名称、地址、坐标、分类和详情。
- 地域：中国大陆；部分位置服务支持全球
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/baidu-place-detail.connector.json`
- Secret环境变量名：`BAIDU_MAP_API_KEY`（仅名称）
- 连接器SHA-256：`1caf6f3d15ba42fa6e8cb084211d291a2402ffefb180f0cba23b0ab34528094e`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "uid",
    "scope",
    "output"
  ],
  "parameter_rules": {
    "properties": {
      "uid": {
        "type": "string",
        "min_length": 1,
        "max_length": 200
      }
    },
    "required_any_of": [
      [
        "uid"
      ]
    ]
  },
  "parameter_notes": {
    "uid": "百度地图官方参数；按接口文档填写",
    "scope": "百度地图官方参数；按接口文档填写",
    "output": "百度地图官方参数；按接口文档填写"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    0
  ],
  "message_path": "message",
  "any_data_paths": [
    "result"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.map.baidu.com",
  "url_pattern": "/place/v2/detail",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "message",
    "result"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 受百度地图账户权限、配额和数据覆盖限制

## 百度地图POI搜索 (`baidu-place-search`)

- 状态：`启用`
- 说明：按关键词和区域、边界或中心点搜索公开兴趣点。
- 适用：商圈与设施清单；竞争和业态代理变量；公开地点交叉核验
- 地域：中国；以百度地图覆盖为准
- 新鲜度：请求时读取百度地图当前POI数据
- 成本等级：`provider-key-quota`
- 详情文件：`connectors/baidu-place-search.connector.json`
- Secret环境变量名：`BAIDU_MAP_API_KEY`（仅名称）
- 连接器SHA-256：`9404cfb3553a63c2492f7ede41e5efe80b30c8f82ad616768b44678d95067c98`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "query",
    "region",
    "bounds",
    "location",
    "radius",
    "scope",
    "tag",
    "page_size",
    "page_num",
    "output",
    "coord_type",
    "ret_coordtype"
  ],
  "parameter_rules": {
    "properties": {
      "query": {
        "type": "string",
        "min_length": 1,
        "max_length": 200
      },
      "region": {
        "type": "string",
        "min_length": 1,
        "max_length": 100
      },
      "bounds": {
        "type": "string",
        "min_length": 3,
        "max_length": 200
      },
      "location": {
        "type": "string",
        "min_length": 3,
        "max_length": 100
      },
      "radius": {
        "type": "integer",
        "minimum": 1,
        "maximum": 50000
      },
      "scope": {
        "type": "integer",
        "enum": [
          1,
          2
        ]
      },
      "page_size": {
        "type": "integer",
        "minimum": 1,
        "maximum": 20
      },
      "page_num": {
        "type": "integer",
        "minimum": 0,
        "maximum": 100
      },
      "output": {
        "type": "string",
        "enum": [
          "json"
        ]
      },
      "coord_type": {
        "type": "integer",
        "minimum": 1,
        "maximum": 6
      },
      "ret_coordtype": {
        "type": "string",
        "enum": [
          "gcj02ll",
          "bd09ll"
        ]
      }
    },
    "required_any_of": [
      [
        "query"
      ],
      [
        "region",
        "bounds",
        "location"
      ]
    ]
  },
  "parameter_notes": {
    "query": "必填；关键词",
    "region": "区域搜索时填写城市或行政区",
    "bounds": "矩形边界搜索",
    "location": "圆形搜索中心纬度,经度",
    "radius": "圆形搜索半径，米",
    "scope": "1基础结果，2详细结果",
    "tag": "可选分类",
    "page_size": "1至20",
    "page_num": "从0开始",
    "output": "固定建议json",
    "coord_type": "输入坐标类型",
    "ret_coordtype": "返回坐标类型"
  },
  "example_parameters": {
    "query": "商场",
    "region": "福州",
    "scope": 2,
    "page_size": 20,
    "page_num": 0,
    "output": "json",
    "ret_coordtype": "gcj02ll"
  },
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    0
  ],
  "message_path": "message",
  "any_data_paths": [
    "results"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.map.baidu.com",
  "url_pattern": "/place/v2/search",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "message",
    "total",
    "results"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- POI数量不等于实时客流、销售额或完整商户名录
- 需要BAIDU_MAP_API_KEY
- 页数和配额受上游限制
- 坐标体系必须在计算中心显式标注

## 百度地点联想 (`baidu-place-suggestion`)

- 状态：`启用`
- 说明：按关键词和区域返回地点输入联想。
- 适用：按关键词和区域返回地点输入联想。
- 地域：中国大陆；部分位置服务支持全球
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/baidu-place-suggestion.connector.json`
- Secret环境变量名：`BAIDU_MAP_API_KEY`（仅名称）
- 连接器SHA-256：`a712c049a8756d335f4e4f5c8bbfe811bf57aa9c72c063c6ffc269a39a4464c0`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "query",
    "region",
    "city_limit",
    "output",
    "ret_coordtype"
  ],
  "parameter_rules": {
    "properties": {
      "query": {
        "type": "string",
        "min_length": 1,
        "max_length": 200
      },
      "region": {
        "type": "string",
        "min_length": 1,
        "max_length": 200
      }
    },
    "required_any_of": [
      [
        "query"
      ],
      [
        "region"
      ]
    ]
  },
  "parameter_notes": {
    "query": "百度地图官方参数；按接口文档填写",
    "region": "百度地图官方参数；按接口文档填写",
    "city_limit": "百度地图官方参数；按接口文档填写",
    "output": "百度地图官方参数；按接口文档填写",
    "ret_coordtype": "百度地图官方参数；按接口文档填写"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    0
  ],
  "message_path": "message",
  "any_data_paths": [
    "result"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.map.baidu.com",
  "url_pattern": "/place/v2/suggestion",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "message",
    "result"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 受百度地图账户权限、配额和数据覆盖限制

## 百度逆地理编码 (`baidu-regeocode`)

- 状态：`启用`
- 说明：将坐标解析为结构化地址、行政区和周边POI。
- 适用：将坐标解析为结构化地址、行政区和周边POI。
- 地域：中国大陆；部分位置服务支持全球
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/baidu-regeocode.connector.json`
- Secret环境变量名：`BAIDU_MAP_API_KEY`（仅名称）
- 连接器SHA-256：`d39439105520bdd8f5e4ade3301897340059c4834a9841f6ce2c4d3719c72129`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "location",
    "coordtype",
    "ret_coordtype",
    "pois",
    "poi_types",
    "radius",
    "extensions_poi",
    "extensions_road",
    "extensions_town",
    "language",
    "language_auto"
  ],
  "parameter_rules": {
    "properties": {
      "location": {
        "type": "string",
        "min_length": 3,
        "max_length": 200
      },
      "radius": {
        "type": "integer",
        "minimum": 0,
        "maximum": 1000
      }
    },
    "required_any_of": [
      [
        "location"
      ]
    ]
  },
  "parameter_notes": {
    "location": "百度地图官方参数；按接口文档填写",
    "coordtype": "百度地图官方参数；按接口文档填写",
    "ret_coordtype": "百度地图官方参数；按接口文档填写",
    "pois": "百度地图官方参数；按接口文档填写",
    "poi_types": "百度地图官方参数；按接口文档填写",
    "radius": "百度地图官方参数；按接口文档填写",
    "extensions_poi": "百度地图官方参数；按接口文档填写",
    "extensions_road": "百度地图官方参数；按接口文档填写",
    "extensions_town": "百度地图官方参数；按接口文档填写",
    "language": "百度地图官方参数；按接口文档填写",
    "language_auto": "百度地图官方参数；按接口文档填写"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    0
  ],
  "message_path": "message",
  "any_data_paths": [
    "result"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.map.baidu.com",
  "url_pattern": "/reverse_geocoding/v3/",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "message",
    "result"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 受百度地图账户权限、配额和数据覆盖限制

## 百度driving批量算路 (`baidu-routematrix-driving`)

- 状态：`启用`
- 说明：批量计算多个起点和终点的driving距离与耗时。
- 适用：批量计算多个起点和终点的driving距离与耗时。
- 地域：中国大陆；部分位置服务支持全球
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/baidu-routematrix-driving.connector.json`
- Secret环境变量名：`BAIDU_MAP_API_KEY`（仅名称）
- 连接器SHA-256：`c220104bb7ea9bc12e3a10ea5125734e85d40f62912bedfa4d83ebe543f7a1d8`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "origins",
    "destinations",
    "tactics",
    "coord_type",
    "ret_coordtype"
  ],
  "parameter_rules": {
    "properties": {
      "origins": {
        "type": "string",
        "min_length": 3,
        "max_length": 200
      },
      "destinations": {
        "type": "string",
        "min_length": 3,
        "max_length": 200
      }
    },
    "required_any_of": [
      [
        "origins"
      ],
      [
        "destinations"
      ]
    ]
  },
  "parameter_notes": {
    "origins": "百度地图官方参数；按接口文档填写",
    "destinations": "百度地图官方参数；按接口文档填写",
    "tactics": "百度地图官方参数；按接口文档填写",
    "coord_type": "百度地图官方参数；按接口文档填写",
    "ret_coordtype": "百度地图官方参数；按接口文档填写"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    0
  ],
  "message_path": "message",
  "any_data_paths": [
    "result"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.map.baidu.com",
  "url_pattern": "/routematrix/v2/driving",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "message",
    "result"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 受百度地图账户权限、配额和数据覆盖限制

## 百度riding批量算路 (`baidu-routematrix-riding`)

- 状态：`启用`
- 说明：批量计算多个起点和终点的riding距离与耗时。
- 适用：批量计算多个起点和终点的riding距离与耗时。
- 地域：中国大陆；部分位置服务支持全球
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/baidu-routematrix-riding.connector.json`
- Secret环境变量名：`BAIDU_MAP_API_KEY`（仅名称）
- 连接器SHA-256：`f3d702ce223bbcf2ade70b095c5144865340da2c0df8024af5c2670b2604eb37`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "origins",
    "destinations",
    "tactics",
    "coord_type",
    "ret_coordtype"
  ],
  "parameter_rules": {
    "properties": {
      "origins": {
        "type": "string",
        "min_length": 3,
        "max_length": 200
      },
      "destinations": {
        "type": "string",
        "min_length": 3,
        "max_length": 200
      }
    },
    "required_any_of": [
      [
        "origins"
      ],
      [
        "destinations"
      ]
    ]
  },
  "parameter_notes": {
    "origins": "百度地图官方参数；按接口文档填写",
    "destinations": "百度地图官方参数；按接口文档填写",
    "tactics": "百度地图官方参数；按接口文档填写",
    "coord_type": "百度地图官方参数；按接口文档填写",
    "ret_coordtype": "百度地图官方参数；按接口文档填写"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    0
  ],
  "message_path": "message",
  "any_data_paths": [
    "result"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.map.baidu.com",
  "url_pattern": "/routematrix/v2/riding",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "message",
    "result"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 受百度地图账户权限、配额和数据覆盖限制

## 百度walking批量算路 (`baidu-routematrix-walking`)

- 状态：`启用`
- 说明：批量计算多个起点和终点的walking距离与耗时。
- 适用：批量计算多个起点和终点的walking距离与耗时。
- 地域：中国大陆；部分位置服务支持全球
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/baidu-routematrix-walking.connector.json`
- Secret环境变量名：`BAIDU_MAP_API_KEY`（仅名称）
- 连接器SHA-256：`4b21114de27b0d31fca94730cf17dfa033db91f5f2f23bf33d4e75a8e4e7b1c2`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "origins",
    "destinations",
    "tactics",
    "coord_type",
    "ret_coordtype"
  ],
  "parameter_rules": {
    "properties": {
      "origins": {
        "type": "string",
        "min_length": 3,
        "max_length": 200
      },
      "destinations": {
        "type": "string",
        "min_length": 3,
        "max_length": 200
      }
    },
    "required_any_of": [
      [
        "origins"
      ],
      [
        "destinations"
      ]
    ]
  },
  "parameter_notes": {
    "origins": "百度地图官方参数；按接口文档填写",
    "destinations": "百度地图官方参数；按接口文档填写",
    "tactics": "百度地图官方参数；按接口文档填写",
    "coord_type": "百度地图官方参数；按接口文档填写",
    "ret_coordtype": "百度地图官方参数；按接口文档填写"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    0
  ],
  "message_path": "message",
  "any_data_paths": [
    "result"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.map.baidu.com",
  "url_pattern": "/routematrix/v2/walking",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "message",
    "result"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 受百度地图账户权限、配额和数据覆盖限制

## 百度天气查询 (`baidu-weather`)

- 状态：`启用`
- 说明：按行政区或坐标读取实况、预报、生活指数和预警。
- 适用：按行政区或坐标读取实况、预报、生活指数和预警。
- 地域：中国大陆；部分位置服务支持全球
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/baidu-weather.connector.json`
- Secret环境变量名：`BAIDU_MAP_API_KEY`（仅名称）
- 连接器SHA-256：`c555501c81de0366d1507ecab19b880318f422667559454e3445ae276c4c626a`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "district_id",
    "location",
    "data_type",
    "coordtype"
  ],
  "parameter_rules": {
    "properties": {
      "district_id": {
        "type": "string",
        "min_length": 1,
        "max_length": 200
      },
      "location": {
        "type": "string",
        "min_length": 3,
        "max_length": 200
      }
    },
    "required_any_of": [
      [
        "district_id",
        "location"
      ]
    ]
  },
  "parameter_notes": {
    "district_id": "百度地图官方参数；按接口文档填写",
    "location": "百度地图官方参数；按接口文档填写",
    "data_type": "百度地图官方参数；按接口文档填写",
    "coordtype": "百度地图官方参数；按接口文档填写"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    0
  ],
  "message_path": "message",
  "any_data_paths": [
    "result"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.map.baidu.com",
  "url_pattern": "/weather/v1/",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "message",
    "result"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 受百度地图账户权限、配额和数据覆盖限制

## ChinaData.live 中国统计数据集 (`chinadata-live-dataset`)

- 状态：`启用`
- 说明：按稳定数据集 slug 获取 ChinaData.live 整理的中国宏观、人口、产业、能源和贸易等公开时间序列。
- 适用：中国宏观指标取数；人口与产业趋势；与官方或国际来源交叉核验
- 地域：中国；具体地域和口径以数据集元数据为准
- 新鲜度：随 ChinaData.live 对上游官方或国际来源的更新而更新
- 成本等级：`free-public-fair-use`
- 详情文件：`connectors/chinadata-live-dataset.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`02ed5a5fff883cda4683ec734bbadd888c7952fdb7c1efa16cfcb756296e6ed5`

请求契约：

```json
{
  "path_parameter_names": [
    "dataset_id"
  ],
  "path_parameters": {
    "dataset_id": {
      "pattern": "^[a-z0-9][a-z0-9-]{0,63}$",
      "max_length": 64
    }
  },
  "query_parameter_names": [],
  "parameter_rules": {},
  "parameter_notes": {
    "dataset_id": "必填；ChinaData.live 数据集 slug，只允许小写字母、数字和连字符，例如 china-gdp"
  },
  "example_parameters": {
    "dataset_id": "china-gdp"
  },
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "success",
  "success_values": [
    true
  ],
  "message_path": "message",
  "any_data_paths": [
    "data.data"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://chinadata.live",
  "url_pattern": "/api/v2/data/{dataset_id}",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "success",
    "data",
    "error",
    "message"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 1,
      "every": "1s",
      "capacity": 1
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- ChinaData.live 是独立数据门户，不是中国政府机构
- 必须保留响应中的 source、unit、frequency 和原始来源说明
- 公开 API 用于研究、评估和轻量调用，受公平使用和源数据许可约束
- 关键政策或投资结论应回到国家统计局、海关或原始国际机构复核

## DBnomics数据集目录 (`dbnomics-dataset`)

- 状态：`启用`
- 说明：读取指定提供方数据集的维度、系列目录和元数据。
- 适用：读取指定提供方数据集的维度、系列目录和元数据。
- 地域：全球
- 新鲜度：随原始统计机构更新
- 成本等级：`free-public`
- 详情文件：`connectors/dbnomics-dataset.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`32872f1c71f0223ce4480473e65b81f7e95cf2a0515f7b849ac7197276a4b525`

请求契约：

```json
{
  "path_parameter_names": [
    "dataset_code",
    "provider_code"
  ],
  "path_parameters": {
    "provider_code": {
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$",
      "max_length": 32
    },
    "dataset_code": {
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$",
      "max_length": 128
    }
  },
  "query_parameter_names": [
    "observations",
    "facets",
    "metadata",
    "limit",
    "offset"
  ],
  "parameter_rules": {},
  "parameter_notes": {
    "observations": "DBnomics API参数",
    "facets": "DBnomics API参数",
    "metadata": "DBnomics API参数",
    "limit": "DBnomics API参数",
    "offset": "DBnomics API参数"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "success_when_data_present": true,
  "any_data_paths": [
    "datasets.docs",
    "series.docs"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.db.nomics.world",
  "url_pattern": "/v22/series/{provider_code}/{dataset_code}",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "_meta",
    "datasets",
    "providers",
    "series",
    "errors"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 1,
      "every": "1s",
      "capacity": 1
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 保留原提供方代码和缺失值；数据频率与修订规则依来源而异

## DBnomics全球经济序列搜索 (`dbnomics-search`)

- 状态：`启用`
- 说明：在全球统计机构的标准化经济时间序列中按关键词检索。
- 适用：在全球统计机构的标准化经济时间序列中按关键词检索。
- 地域：全球
- 新鲜度：随原始统计机构更新
- 成本等级：`free-public`
- 详情文件：`connectors/dbnomics-search.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`9cfdd2a3247b25dbcb1ee953c6fb5ff9da2ffba42b0b76582586d862eef78c44`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "q",
    "limit",
    "offset",
    "facets"
  ],
  "parameter_rules": {
    "properties": {
      "q": {
        "type": "string",
        "min_length": 1,
        "max_length": 200
      }
    },
    "required_any_of": [
      [
        "q"
      ]
    ]
  },
  "parameter_notes": {
    "q": "DBnomics API参数",
    "limit": "DBnomics API参数",
    "offset": "DBnomics API参数",
    "facets": "DBnomics API参数"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "success_when_data_present": true,
  "any_data_paths": [
    "series.docs"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.db.nomics.world",
  "url_pattern": "/v22/series",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "_meta",
    "datasets",
    "providers",
    "series",
    "errors"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 1,
      "every": "1s",
      "capacity": 1
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 保留原提供方代码和缺失值；数据频率与修订规则依来源而异

## DBnomics 经济时间序列 (`dbnomics-series`)

- 状态：`启用`
- 说明：通过 DBnomics v22 统一接口读取指定提供方、数据集和序列的元数据及观测值。
- 适用：中国国家统计局序列；国际宏观指标交叉验证；可复现历史时间序列分析
- 地域：全球；可通过 NBS 等提供方读取中国数据
- 新鲜度：DBnomics 抓取器通常在上游发布后自动更新，并保留历史修订
- 成本等级：`free-public`
- 详情文件：`connectors/dbnomics-series.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`6f1cde18cc298975abe3c2683b777d373b16aa71e39981e449b87ceaffefee3f`

请求契约：

```json
{
  "path_parameter_names": [
    "dataset_code",
    "provider_code",
    "series_code"
  ],
  "path_parameters": {
    "provider_code": {
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$",
      "max_length": 32
    },
    "dataset_code": {
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$",
      "max_length": 128
    },
    "series_code": {
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$",
      "max_length": 256
    }
  },
  "query_parameter_names": [
    "observations",
    "facets",
    "metadata",
    "align_periods",
    "limit",
    "offset"
  ],
  "parameter_rules": {},
  "parameter_notes": {
    "provider_code": "必填；DBnomics 提供方代码，例如 NBS、WB、IMF",
    "dataset_code": "必填；提供方的数据集代码，例如 A_A0201",
    "series_code": "必填；精确单序列代码，例如 A020106",
    "observations": "建议填1或true以返回观测值",
    "facets": "可选；是否返回分面元数据",
    "metadata": "可选；是否返回详细元数据",
    "align_periods": "可选；多序列时对齐期间，本连接器主要用于精确单序列",
    "limit": "可选；返回上限",
    "offset": "可选；分页偏移"
  },
  "example_parameters": {
    "provider_code": "NBS",
    "dataset_code": "A_A0201",
    "series_code": "A020106",
    "observations": 1
  },
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "series.num_found",
  "success_values": [
    1
  ],
  "any_data_paths": [
    "series.docs"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.db.nomics.world",
  "url_pattern": "/v22/series/{provider_code}/{dataset_code}/{series_code}",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "_meta",
    "datasets",
    "providers",
    "series",
    "errors"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 1,
      "every": "1s",
      "capacity": 1
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- DBnomics 是聚合平台，数值、代码和许可沿用原始提供方
- 连接器限制为精确单序列，series.num_found 必须等于1
- 不用于整库批量下载；应做聚焦查询并保留 provider/dataset/series 代码
- 关键数据应同时检查原始统计机构的发布日期、单位和修订说明

## NewsAPI 全网新闻检索 (`newsapi-everything`)

- 状态：`启用`
- 说明：调用NewsAPI Everything端点，按关键词、时间、语言、来源或域名检索公开新闻文章元数据。
- 适用：专题新闻检索；企业与事件舆情线索；按时间和来源构建新闻证据集
- 地域：全球；覆盖范围取决于NewsAPI收录的新闻源
- 新鲜度：取决于订阅套餐；Developer免费套餐文章延迟24小时且最多检索近1个月
- 成本等级：`provider-key-plan-limited`
- 详情文件：`connectors/newsapi-everything.connector.json`
- Secret环境变量名：`NEWSAPI_API_KEY`（仅名称）
- 连接器SHA-256：`d53a3b43ed4f4c58731c5121d08714a07b3639318d3142551d4aef72d287af19`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "q",
    "searchIn",
    "sources",
    "domains",
    "excludeDomains",
    "from",
    "to",
    "language",
    "sortBy",
    "pageSize",
    "page"
  ],
  "parameter_rules": {
    "properties": {
      "q": {
        "type": "string",
        "min_length": 1,
        "max_length": 500
      },
      "searchIn": {
        "type": "string",
        "pattern": "^(?:title|description|content)(?:,(?:title|description|content))*$"
      },
      "language": {
        "type": "string",
        "enum": [
          "ar",
          "de",
          "en",
          "es",
          "fr",
          "he",
          "it",
          "nl",
          "no",
          "pt",
          "ru",
          "sv",
          "ud",
          "zh"
        ]
      },
      "sortBy": {
        "type": "string",
        "enum": [
          "relevancy",
          "popularity",
          "publishedAt"
        ]
      },
      "pageSize": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100
      },
      "page": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100
      }
    },
    "required_any_of": [
      [
        "q",
        "sources",
        "domains"
      ]
    ]
  },
  "parameter_notes": {
    "q": "建议必填；关键词或布尔表达式，官方上限500字符",
    "searchIn": "可选；title、description、content，可逗号分隔",
    "sources": "可选；最多20个来源ID，不能与domains同时假设等价",
    "domains": "可选；限定来源域名",
    "excludeDomains": "可选；排除域名",
    "from": "可选；ISO 8601起始时间，受套餐历史范围限制",
    "to": "可选；ISO 8601结束时间",
    "language": "可选；两位语言代码，例如zh、en",
    "sortBy": "可选；relevancy、popularity或publishedAt",
    "pageSize": "可选；1至100",
    "page": "可选；页码"
  },
  "example_parameters": {
    "q": "\"福州\" AND 商业",
    "language": "zh",
    "sortBy": "publishedAt",
    "pageSize": 20,
    "page": 1
  },
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    "ok"
  ],
  "error_code_path": "code",
  "message_path": "message",
  "any_data_paths": [
    "articles"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://newsapi.org",
  "url_pattern": "/v2/everything",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "totalResults",
    "articles",
    "code",
    "message"
  ],
  "resilience": {
    "circuit_breaker": {
      "interval": 60,
      "timeout": 30,
      "max_errors": 3,
      "log_status_change": true
    },
    "rate_limit": {
      "max_rate": 1,
      "every": "1s",
      "capacity": 1
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 只返回文章元数据、摘要和最多约200字符的content片段，不提供完整文章正文
- Developer免费套餐仅限开发测试，不能用于正式生产或内部生产环境
- Developer免费套餐每天100次请求、文章延迟24小时、最多检索近1个月
- 来源覆盖、去重、发布时间和摘要可能不完整；重要事实必须打开原文并进行多源核验
- 不得绕过出版商付费墙、版权或NewsAPI订阅条款

## NewsAPI 新闻来源目录 (`newsapi-sources`)

- 状态：`启用`
- 说明：调用NewsAPI Sources端点，列出Top Headlines支持的新闻来源及其类别、语言和国家信息。
- 适用：发现可用新闻来源ID；按国家语言筛选媒体；为头条查询准备来源白名单
- 地域：全球；仅包含NewsAPI Top Headlines支持的来源子集
- 新鲜度：来源目录变化较慢，建议每日或每周缓存一次
- 成本等级：`provider-key-plan-limited`
- 详情文件：`connectors/newsapi-sources.connector.json`
- Secret环境变量名：`NEWSAPI_API_KEY`（仅名称）
- 连接器SHA-256：`adacca590d8e6d1790d3b1a29ad292f247c7bda3cd7d381a5a4cdbe7f6e6bd61`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "category",
    "language",
    "country"
  ],
  "parameter_rules": {
    "properties": {
      "country": {
        "type": "string",
        "pattern": "^[a-z]{2}$"
      },
      "category": {
        "type": "string",
        "enum": [
          "business",
          "entertainment",
          "general",
          "health",
          "science",
          "sports",
          "technology"
        ]
      },
      "language": {
        "type": "string",
        "enum": [
          "ar",
          "de",
          "en",
          "es",
          "fr",
          "he",
          "it",
          "nl",
          "no",
          "pt",
          "ru",
          "sv",
          "ud",
          "zh"
        ]
      }
    }
  },
  "parameter_notes": {
    "category": "可选；新闻类别",
    "language": "可选；两位语言代码，例如zh、en",
    "country": "可选；两位国家代码，例如cn、us"
  },
  "example_parameters": {
    "language": "zh",
    "country": "cn"
  },
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    "ok"
  ],
  "error_code_path": "code",
  "message_path": "message",
  "any_data_paths": [
    "sources"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://newsapi.org",
  "url_pattern": "/v2/top-headlines/sources",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "sources",
    "code",
    "message"
  ],
  "resilience": {
    "circuit_breaker": {
      "interval": 60,
      "timeout": 30,
      "max_errors": 3,
      "log_status_change": true
    },
    "rate_limit": {
      "max_rate": 1,
      "every": "1s",
      "capacity": 1
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- Sources只列出Top Headlines可用来源，不等于Everything端点的全部收录来源
- 该端点也计入请求配额，官方建议缓存并降低调用频率
- 媒体归属国家、语言和类别由NewsAPI维护，必要时应访问来源官网核验

## NewsAPI 头条新闻 (`newsapi-top-headlines`)

- 状态：`启用`
- 说明：调用NewsAPI Top Headlines端点，按国家、类别、来源或关键词读取头条新闻元数据。
- 适用：国家与行业头条监测；突发事件线索；指定来源最新标题采集
- 地域：NewsAPI支持的国家、类别和来源；具体列表以官方Sources目录为准
- 新鲜度：取决于订阅套餐；免费Developer套餐存在24小时延迟
- 成本等级：`provider-key-plan-limited`
- 详情文件：`connectors/newsapi-top-headlines.connector.json`
- Secret环境变量名：`NEWSAPI_API_KEY`（仅名称）
- 连接器SHA-256：`03a4fce728dbf80a6c7b87e774e72f350d5cf5562a52de366ced920ba5a05e35`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "q",
    "sources",
    "country",
    "category",
    "pageSize",
    "page"
  ],
  "parameter_rules": {
    "properties": {
      "q": {
        "type": "string",
        "min_length": 1,
        "max_length": 500
      },
      "country": {
        "type": "string",
        "pattern": "^[a-z]{2}$"
      },
      "category": {
        "type": "string",
        "enum": [
          "business",
          "entertainment",
          "general",
          "health",
          "science",
          "sports",
          "technology"
        ]
      },
      "pageSize": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100
      },
      "page": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100
      }
    },
    "required_any_of": [
      [
        "q",
        "sources",
        "country",
        "category"
      ]
    ],
    "mutually_exclusive": [
      [
        "sources",
        "country"
      ],
      [
        "sources",
        "category"
      ]
    ]
  },
  "parameter_notes": {
    "q": "可选；关键词或短语",
    "sources": "可选；来源ID列表；不能与country或category组合",
    "country": "可选；两位国家代码；不能与sources组合",
    "category": "可选；business、entertainment、general、health、science、sports、technology",
    "pageSize": "可选；1至100",
    "page": "可选；页码"
  },
  "example_parameters": {
    "country": "cn",
    "category": "business",
    "pageSize": 20,
    "page": 1
  },
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status",
  "success_values": [
    "ok"
  ],
  "error_code_path": "code",
  "message_path": "message",
  "any_data_paths": [
    "articles"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://newsapi.org",
  "url_pattern": "/v2/top-headlines",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "status",
    "totalResults",
    "articles",
    "code",
    "message"
  ],
  "resilience": {
    "circuit_breaker": {
      "interval": 60,
      "timeout": 30,
      "max_errors": 3,
      "log_status_change": true
    },
    "rate_limit": {
      "max_rate": 1,
      "every": "1s",
      "capacity": 1
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- sources不能与country或category混用，错误组合会由上游拒绝
- 免费Developer套餐并不适合真正的实时生产监控
- 只提供新闻元数据和摘要片段，不提供完整正文
- 头条排序、来源覆盖和国家分类由NewsAPI决定，不能视为完整媒体样本

## Open-Meteo空气质量 (`openmeteo-air-quality`)

- 状态：`启用`
- 说明：读取PM2.5、PM10、臭氧、二氧化氮、花粉和空气质量指数。
- 适用：读取PM2.5、PM10、臭氧、二氧化氮、花粉和空气质量指数。
- 地域：全球；具体覆盖依赖模型
- 新鲜度：请求时返回；更新频率依模型而定
- 成本等级：`free-public-or-provider-policy`
- 详情文件：`connectors/openmeteo-air-quality.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`d29ddac3494b8a8ece7a1410dc269ebb6c24050b3a651bb4e16f9a958e05cbb9`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "latitude",
    "longitude",
    "current",
    "hourly",
    "timezone",
    "forecast_days",
    "past_days",
    "start_date",
    "end_date",
    "domains",
    "timeformat"
  ],
  "parameter_rules": {
    "properties": {
      "latitude": {
        "type": "number",
        "minimum": -90,
        "maximum": 90
      },
      "longitude": {
        "type": "number",
        "minimum": -180,
        "maximum": 180
      },
      "start_date": {
        "type": "string",
        "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
        "max_length": 10
      },
      "end_date": {
        "type": "string",
        "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
        "max_length": 10
      },
      "current": {
        "type": "string",
        "min_length": 1,
        "max_length": 2000
      },
      "hourly": {
        "type": "string",
        "min_length": 1,
        "max_length": 2000
      },
      "domains": {
        "type": "string",
        "min_length": 1,
        "max_length": 2000
      },
      "forecast_days": {
        "type": "integer",
        "minimum": 1,
        "maximum": 365
      },
      "past_days": {
        "type": "integer",
        "minimum": 0,
        "maximum": 365
      }
    },
    "required_any_of": [
      [
        "latitude"
      ],
      [
        "longitude"
      ]
    ]
  },
  "parameter_notes": {
    "latitude": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "longitude": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "current": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "hourly": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "timezone": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "forecast_days": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "past_days": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "start_date": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "end_date": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "domains": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "timeformat": "Open-Meteo官方参数；变量列表可用逗号分隔"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "success_when_data_present": true,
  "any_data_paths": [
    "current",
    "hourly"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://air-quality-api.open-meteo.com",
  "url_pattern": "/v1/air-quality",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "latitude",
    "longitude",
    "generationtime_ms",
    "utc_offset_seconds",
    "timezone",
    "timezone_abbreviation",
    "elevation",
    "current_units",
    "current",
    "hourly_units",
    "hourly",
    "daily_units",
    "daily",
    "results",
    "reason",
    "error"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 不同模型的空间分辨率、时间范围和更新频率不同

## Open-Meteo历史天气 (`openmeteo-archive`)

- 状态：`启用`
- 说明：读取1940年以来可用的历史天气和再分析时间序列。
- 适用：读取1940年以来可用的历史天气和再分析时间序列。
- 地域：全球；具体覆盖依赖模型
- 新鲜度：请求时返回；更新频率依模型而定
- 成本等级：`free-public-or-provider-policy`
- 详情文件：`connectors/openmeteo-archive.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`d72b1e2f9f56096f78430a154415ff4ff751c434c29fc1abb65754ec3fa65338`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "latitude",
    "longitude",
    "hourly",
    "daily",
    "timezone",
    "start_date",
    "end_date",
    "past_days",
    "forecast_days",
    "timeformat",
    "temperature_unit",
    "wind_speed_unit",
    "precipitation_unit"
  ],
  "parameter_rules": {
    "properties": {
      "latitude": {
        "type": "number",
        "minimum": -90,
        "maximum": 90
      },
      "longitude": {
        "type": "number",
        "minimum": -180,
        "maximum": 180
      },
      "start_date": {
        "type": "string",
        "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
        "max_length": 10
      },
      "end_date": {
        "type": "string",
        "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
        "max_length": 10
      },
      "hourly": {
        "type": "string",
        "min_length": 1,
        "max_length": 2000
      },
      "daily": {
        "type": "string",
        "min_length": 1,
        "max_length": 2000
      },
      "forecast_days": {
        "type": "integer",
        "minimum": 1,
        "maximum": 365
      },
      "past_days": {
        "type": "integer",
        "minimum": 0,
        "maximum": 365
      }
    },
    "required_any_of": [
      [
        "latitude"
      ],
      [
        "longitude"
      ]
    ]
  },
  "parameter_notes": {
    "latitude": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "longitude": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "hourly": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "daily": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "timezone": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "start_date": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "end_date": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "past_days": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "forecast_days": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "timeformat": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "temperature_unit": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "wind_speed_unit": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "precipitation_unit": "Open-Meteo官方参数；变量列表可用逗号分隔"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "success_when_data_present": true,
  "any_data_paths": [
    "hourly",
    "daily"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://archive-api.open-meteo.com",
  "url_pattern": "/v1/archive",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "latitude",
    "longitude",
    "generationtime_ms",
    "utc_offset_seconds",
    "timezone",
    "timezone_abbreviation",
    "elevation",
    "current_units",
    "current",
    "hourly_units",
    "hourly",
    "daily_units",
    "daily",
    "results",
    "reason",
    "error"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 不同模型的空间分辨率、时间范围和更新频率不同

## Open-Meteo气候变化情景 (`openmeteo-climate`)

- 状态：`启用`
- 说明：读取CMIP气候模型的历史和未来情景变量。
- 适用：读取CMIP气候模型的历史和未来情景变量。
- 地域：全球；具体覆盖依赖模型
- 新鲜度：请求时返回；更新频率依模型而定
- 成本等级：`free-public-or-provider-policy`
- 详情文件：`connectors/openmeteo-climate.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`36a5ed8114beb9c9c92a5784f7efc09679d107b12ffe90fd844268977bd4bca0`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "latitude",
    "longitude",
    "start_date",
    "end_date",
    "models",
    "daily",
    "temperature_unit",
    "wind_speed_unit",
    "precipitation_unit",
    "timeformat"
  ],
  "parameter_rules": {
    "properties": {
      "latitude": {
        "type": "number",
        "minimum": -90,
        "maximum": 90
      },
      "longitude": {
        "type": "number",
        "minimum": -180,
        "maximum": 180
      },
      "start_date": {
        "type": "string",
        "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
        "max_length": 10
      },
      "end_date": {
        "type": "string",
        "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
        "max_length": 10
      },
      "daily": {
        "type": "string",
        "min_length": 1,
        "max_length": 2000
      },
      "models": {
        "type": "string",
        "min_length": 1,
        "max_length": 2000
      }
    },
    "required_any_of": [
      [
        "latitude"
      ],
      [
        "longitude"
      ],
      [
        "start_date"
      ],
      [
        "end_date"
      ],
      [
        "daily"
      ]
    ]
  },
  "parameter_notes": {
    "latitude": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "longitude": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "start_date": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "end_date": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "models": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "daily": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "temperature_unit": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "wind_speed_unit": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "precipitation_unit": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "timeformat": "Open-Meteo官方参数；变量列表可用逗号分隔"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "success_when_data_present": true,
  "any_data_paths": [
    "daily"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://climate-api.open-meteo.com",
  "url_pattern": "/v1/climate",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "latitude",
    "longitude",
    "generationtime_ms",
    "utc_offset_seconds",
    "timezone",
    "timezone_abbreviation",
    "elevation",
    "current_units",
    "current",
    "hourly_units",
    "hourly",
    "daily_units",
    "daily",
    "results",
    "reason",
    "error"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 不同模型的空间分辨率、时间范围和更新频率不同

## Open-Meteo海拔查询 (`openmeteo-elevation`)

- 状态：`启用`
- 说明：按一个或多个坐标读取地形海拔。
- 适用：按一个或多个坐标读取地形海拔。
- 地域：全球；具体覆盖依赖模型
- 新鲜度：请求时返回；更新频率依模型而定
- 成本等级：`free-public-or-provider-policy`
- 详情文件：`connectors/openmeteo-elevation.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`589c292b1317da6586276716cc515de4a751ed57dc51479eea59c2aabe8e6934`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "latitude",
    "longitude"
  ],
  "parameter_rules": {
    "properties": {
      "latitude": {
        "type": "number",
        "minimum": -90,
        "maximum": 90
      },
      "longitude": {
        "type": "number",
        "minimum": -180,
        "maximum": 180
      }
    },
    "required_any_of": [
      [
        "latitude"
      ],
      [
        "longitude"
      ]
    ]
  },
  "parameter_notes": {
    "latitude": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "longitude": "Open-Meteo官方参数；变量列表可用逗号分隔"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "success_when_data_present": true,
  "any_data_paths": [
    "elevation"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.open-meteo.com",
  "url_pattern": "/v1/elevation",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "latitude",
    "longitude",
    "generationtime_ms",
    "utc_offset_seconds",
    "timezone",
    "timezone_abbreviation",
    "elevation",
    "current_units",
    "current",
    "hourly_units",
    "hourly",
    "daily_units",
    "daily",
    "results",
    "reason",
    "error"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 不同模型的空间分辨率、时间范围和更新频率不同

## Open-Meteo集合预报 (`openmeteo-ensemble`)

- 状态：`启用`
- 说明：读取多个集合预报成员和不确定性范围。
- 适用：读取多个集合预报成员和不确定性范围。
- 地域：全球；具体覆盖依赖模型
- 新鲜度：请求时返回；更新频率依模型而定
- 成本等级：`free-public-or-provider-policy`
- 详情文件：`connectors/openmeteo-ensemble.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`e61fdd23534a265908dcddbae2abd7a28e91f78d555e2c20c4b0d24abe1460d5`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "latitude",
    "longitude",
    "hourly",
    "models",
    "forecast_days",
    "past_days",
    "timezone",
    "timeformat",
    "temperature_unit",
    "wind_speed_unit",
    "precipitation_unit"
  ],
  "parameter_rules": {
    "properties": {
      "latitude": {
        "type": "number",
        "minimum": -90,
        "maximum": 90
      },
      "longitude": {
        "type": "number",
        "minimum": -180,
        "maximum": 180
      },
      "hourly": {
        "type": "string",
        "min_length": 1,
        "max_length": 2000
      },
      "models": {
        "type": "string",
        "min_length": 1,
        "max_length": 2000
      },
      "forecast_days": {
        "type": "integer",
        "minimum": 1,
        "maximum": 365
      },
      "past_days": {
        "type": "integer",
        "minimum": 0,
        "maximum": 365
      }
    },
    "required_any_of": [
      [
        "latitude"
      ],
      [
        "longitude"
      ],
      [
        "hourly"
      ]
    ]
  },
  "parameter_notes": {
    "latitude": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "longitude": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "hourly": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "models": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "forecast_days": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "past_days": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "timezone": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "timeformat": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "temperature_unit": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "wind_speed_unit": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "precipitation_unit": "Open-Meteo官方参数；变量列表可用逗号分隔"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "success_when_data_present": true,
  "any_data_paths": [
    "hourly"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://ensemble-api.open-meteo.com",
  "url_pattern": "/v1/ensemble",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "latitude",
    "longitude",
    "generationtime_ms",
    "utc_offset_seconds",
    "timezone",
    "timezone_abbreviation",
    "elevation",
    "current_units",
    "current",
    "hourly_units",
    "hourly",
    "daily_units",
    "daily",
    "results",
    "reason",
    "error"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 不同模型的空间分辨率、时间范围和更新频率不同

## Open-Meteo洪水与河流流量 (`openmeteo-flood`)

- 状态：`启用`
- 说明：读取历史和预测河流流量、分位数及集合成员。
- 适用：读取历史和预测河流流量、分位数及集合成员。
- 地域：全球；具体覆盖依赖模型
- 新鲜度：请求时返回；更新频率依模型而定
- 成本等级：`free-public-or-provider-policy`
- 详情文件：`connectors/openmeteo-flood.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`9679531be7aeb9793f86a59f91e01d254b58971532373ab7730b0f347edc43c1`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "latitude",
    "longitude",
    "daily",
    "forecast_days",
    "past_days",
    "start_date",
    "end_date",
    "ensemble",
    "timeformat"
  ],
  "parameter_rules": {
    "properties": {
      "latitude": {
        "type": "number",
        "minimum": -90,
        "maximum": 90
      },
      "longitude": {
        "type": "number",
        "minimum": -180,
        "maximum": 180
      },
      "start_date": {
        "type": "string",
        "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
        "max_length": 10
      },
      "end_date": {
        "type": "string",
        "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
        "max_length": 10
      },
      "daily": {
        "type": "string",
        "min_length": 1,
        "max_length": 2000
      },
      "forecast_days": {
        "type": "integer",
        "minimum": 1,
        "maximum": 365
      },
      "past_days": {
        "type": "integer",
        "minimum": 0,
        "maximum": 365
      }
    },
    "required_any_of": [
      [
        "latitude"
      ],
      [
        "longitude"
      ],
      [
        "daily"
      ]
    ]
  },
  "parameter_notes": {
    "latitude": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "longitude": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "daily": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "forecast_days": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "past_days": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "start_date": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "end_date": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "ensemble": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "timeformat": "Open-Meteo官方参数；变量列表可用逗号分隔"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "success_when_data_present": true,
  "any_data_paths": [
    "daily"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://flood-api.open-meteo.com",
  "url_pattern": "/v1/flood",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "latitude",
    "longitude",
    "generationtime_ms",
    "utc_offset_seconds",
    "timezone",
    "timezone_abbreviation",
    "elevation",
    "current_units",
    "current",
    "hourly_units",
    "hourly",
    "daily_units",
    "daily",
    "results",
    "reason",
    "error"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 5公里分辨率可能无法精确匹配小河流

## Open‑Meteo 全球天气预报 (`openmeteo-forecast`)

- 状态：`启用`
- 说明：按经纬度读取当前天气、小时预报或逐日预报，适合全球天气情景与出行风险修正。
- 适用：全球天气查询；商业与出行情景修正；配送和网约车天气风险建模
- 地域：全球经纬度
- 新鲜度：请求时读取Open‑Meteo当前模型结果；更新频率取决于具体预报模型
- 成本等级：`free-public-fair-use`
- 详情文件：`connectors/openmeteo-forecast.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`8c3aa26aa02277ad0707b34f42d66b341fd39503feb28d108d1b83ac8ffb5fb0`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "latitude",
    "longitude",
    "current",
    "hourly",
    "daily",
    "timezone",
    "forecast_days",
    "past_days",
    "temperature_unit",
    "wind_speed_unit",
    "precipitation_unit",
    "timeformat"
  ],
  "parameter_rules": {
    "properties": {
      "latitude": {
        "type": "number",
        "minimum": -90,
        "maximum": 90
      },
      "longitude": {
        "type": "number",
        "minimum": -180,
        "maximum": 180
      },
      "forecast_days": {
        "type": "integer",
        "minimum": 1,
        "maximum": 16
      },
      "past_days": {
        "type": "integer",
        "minimum": 0,
        "maximum": 92
      },
      "timezone": {
        "type": "string",
        "min_length": 1,
        "max_length": 100
      },
      "temperature_unit": {
        "type": "string",
        "enum": [
          "celsius",
          "fahrenheit"
        ]
      },
      "wind_speed_unit": {
        "type": "string",
        "enum": [
          "kmh",
          "ms",
          "mph",
          "kn"
        ]
      },
      "precipitation_unit": {
        "type": "string",
        "enum": [
          "mm",
          "inch"
        ]
      },
      "timeformat": {
        "type": "string",
        "enum": [
          "iso8601",
          "unixtime"
        ]
      },
      "current": {
        "type": "string",
        "min_length": 1,
        "max_length": 2000
      },
      "hourly": {
        "type": "string",
        "min_length": 1,
        "max_length": 2000
      },
      "daily": {
        "type": "string",
        "min_length": 1,
        "max_length": 2000
      }
    },
    "required_any_of": [
      [
        "latitude"
      ],
      [
        "longitude"
      ],
      [
        "current",
        "hourly",
        "daily"
      ]
    ]
  },
  "parameter_notes": {
    "latitude": "必填；WGS84纬度",
    "longitude": "必填；WGS84经度",
    "current": "current变量列表，例如temperature_2m,precipitation,weather_code",
    "hourly": "小时变量列表",
    "daily": "逐日变量列表",
    "timezone": "建议填写auto或IANA时区",
    "forecast_days": "1至16",
    "past_days": "0至92",
    "temperature_unit": "celsius或fahrenheit",
    "wind_speed_unit": "kmh、ms、mph或kn",
    "precipitation_unit": "mm或inch",
    "timeformat": "iso8601或unixtime"
  },
  "example_parameters": {
    "latitude": 26.0745,
    "longitude": 119.2965,
    "current": "temperature_2m,precipitation,weather_code,wind_speed_10m",
    "hourly": "temperature_2m,precipitation_probability",
    "forecast_days": 3,
    "timezone": "Asia/Shanghai"
  },
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "success_when_data_present": true,
  "any_data_paths": [
    "current",
    "hourly",
    "daily"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.open-meteo.com",
  "url_pattern": "/v1/forecast",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "latitude",
    "longitude",
    "generationtime_ms",
    "utc_offset_seconds",
    "timezone",
    "timezone_abbreviation",
    "elevation",
    "current_units",
    "current",
    "hourly_units",
    "hourly",
    "daily_units",
    "daily",
    "reason",
    "error"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 10,
      "every": "1s",
      "capacity": 10
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 天气预报具有模型不确定性，不等于现场观测
- 免费公共服务受公平使用和上游可用性限制
- 经纬度必须为WGS84；不得提交个人实时轨迹

## Open-Meteo全球地理编码 (`openmeteo-geocoding`)

- 状态：`启用`
- 说明：按地名或邮编搜索全球地点及行政区、坐标和时区。
- 适用：按地名或邮编搜索全球地点及行政区、坐标和时区。
- 地域：全球；具体覆盖依赖模型
- 新鲜度：请求时返回；更新频率依模型而定
- 成本等级：`free-public-or-provider-policy`
- 详情文件：`connectors/openmeteo-geocoding.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`f8afe12847e0c232352a02ccdea616981dd5a7ee84d0b88dc8d50143678b1e9e`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "name",
    "count",
    "language",
    "countryCode",
    "format"
  ],
  "parameter_rules": {
    "properties": {
      "name": {
        "type": "string",
        "min_length": 1,
        "max_length": 200
      },
      "count": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100
      }
    },
    "required_any_of": [
      [
        "name"
      ]
    ]
  },
  "parameter_notes": {
    "name": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "count": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "language": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "countryCode": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "format": "Open-Meteo官方参数；变量列表可用逗号分隔"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "success_when_data_present": true,
  "any_data_paths": [
    "results"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://geocoding-api.open-meteo.com",
  "url_pattern": "/v1/search",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "latitude",
    "longitude",
    "generationtime_ms",
    "utc_offset_seconds",
    "timezone",
    "timezone_abbreviation",
    "elevation",
    "current_units",
    "current",
    "hourly_units",
    "hourly",
    "daily_units",
    "daily",
    "results",
    "reason",
    "error"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 不同模型的空间分辨率、时间范围和更新频率不同

## Open-Meteo历史预报存档 (`openmeteo-historical-forecast`)

- 状态：`启用`
- 说明：读取过去发布的天气预报，用于回测预测误差。
- 适用：读取过去发布的天气预报，用于回测预测误差。
- 地域：全球；具体覆盖依赖模型
- 新鲜度：请求时返回；更新频率依模型而定
- 成本等级：`free-public-or-provider-policy`
- 详情文件：`connectors/openmeteo-historical-forecast.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`f11fbf3149c82e55d9c6937696f7611e3555bc9651468c4ddb5906439b5cd1dc`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "latitude",
    "longitude",
    "hourly",
    "daily",
    "timezone",
    "start_date",
    "end_date",
    "past_days",
    "forecast_days",
    "timeformat",
    "temperature_unit",
    "wind_speed_unit",
    "precipitation_unit"
  ],
  "parameter_rules": {
    "properties": {
      "latitude": {
        "type": "number",
        "minimum": -90,
        "maximum": 90
      },
      "longitude": {
        "type": "number",
        "minimum": -180,
        "maximum": 180
      },
      "start_date": {
        "type": "string",
        "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
        "max_length": 10
      },
      "end_date": {
        "type": "string",
        "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
        "max_length": 10
      },
      "hourly": {
        "type": "string",
        "min_length": 1,
        "max_length": 2000
      },
      "daily": {
        "type": "string",
        "min_length": 1,
        "max_length": 2000
      },
      "forecast_days": {
        "type": "integer",
        "minimum": 1,
        "maximum": 365
      },
      "past_days": {
        "type": "integer",
        "minimum": 0,
        "maximum": 365
      }
    },
    "required_any_of": [
      [
        "latitude"
      ],
      [
        "longitude"
      ]
    ]
  },
  "parameter_notes": {
    "latitude": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "longitude": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "hourly": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "daily": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "timezone": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "start_date": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "end_date": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "past_days": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "forecast_days": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "timeformat": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "temperature_unit": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "wind_speed_unit": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "precipitation_unit": "Open-Meteo官方参数；变量列表可用逗号分隔"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "success_when_data_present": true,
  "any_data_paths": [
    "hourly",
    "daily"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://historical-forecast-api.open-meteo.com",
  "url_pattern": "/v1/forecast",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "latitude",
    "longitude",
    "generationtime_ms",
    "utc_offset_seconds",
    "timezone",
    "timezone_abbreviation",
    "elevation",
    "current_units",
    "current",
    "hourly_units",
    "hourly",
    "daily_units",
    "daily",
    "results",
    "reason",
    "error"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 不同模型的空间分辨率、时间范围和更新频率不同

## Open-Meteo海洋预报 (`openmeteo-marine`)

- 状态：`启用`
- 说明：读取海浪、涌浪、海温、潮汐和海洋气象变量。
- 适用：读取海浪、涌浪、海温、潮汐和海洋气象变量。
- 地域：全球；具体覆盖依赖模型
- 新鲜度：请求时返回；更新频率依模型而定
- 成本等级：`free-public-or-provider-policy`
- 详情文件：`connectors/openmeteo-marine.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`d5730d1b5a2fd43ea9e20667533a01178931c8319df7ec20d8d2e08dc0059e1e`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "latitude",
    "longitude",
    "current",
    "hourly",
    "daily",
    "timezone",
    "forecast_days",
    "past_days",
    "start_date",
    "end_date",
    "wave_height_min",
    "wave_height_max",
    "timeformat"
  ],
  "parameter_rules": {
    "properties": {
      "latitude": {
        "type": "number",
        "minimum": -90,
        "maximum": 90
      },
      "longitude": {
        "type": "number",
        "minimum": -180,
        "maximum": 180
      },
      "start_date": {
        "type": "string",
        "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
        "max_length": 10
      },
      "end_date": {
        "type": "string",
        "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
        "max_length": 10
      },
      "current": {
        "type": "string",
        "min_length": 1,
        "max_length": 2000
      },
      "hourly": {
        "type": "string",
        "min_length": 1,
        "max_length": 2000
      },
      "daily": {
        "type": "string",
        "min_length": 1,
        "max_length": 2000
      },
      "forecast_days": {
        "type": "integer",
        "minimum": 1,
        "maximum": 365
      },
      "past_days": {
        "type": "integer",
        "minimum": 0,
        "maximum": 365
      }
    },
    "required_any_of": [
      [
        "latitude"
      ],
      [
        "longitude"
      ]
    ]
  },
  "parameter_notes": {
    "latitude": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "longitude": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "current": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "hourly": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "daily": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "timezone": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "forecast_days": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "past_days": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "start_date": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "end_date": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "wave_height_min": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "wave_height_max": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "timeformat": "Open-Meteo官方参数；变量列表可用逗号分隔"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "success_when_data_present": true,
  "any_data_paths": [
    "current",
    "hourly",
    "daily"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://marine-api.open-meteo.com",
  "url_pattern": "/v1/marine",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "latitude",
    "longitude",
    "generationtime_ms",
    "utc_offset_seconds",
    "timezone",
    "timezone_abbreviation",
    "elevation",
    "current_units",
    "current",
    "hourly_units",
    "hourly",
    "daily_units",
    "daily",
    "results",
    "reason",
    "error"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 不同模型的空间分辨率、时间范围和更新频率不同

## Open-Meteo季节预报 (`openmeteo-seasonal`)

- 状态：`启用`
- 说明：读取数月尺度的季节集合预报。
- 适用：读取数月尺度的季节集合预报。
- 地域：全球；具体覆盖依赖模型
- 新鲜度：请求时返回；更新频率依模型而定
- 成本等级：`free-public-or-provider-policy`
- 详情文件：`connectors/openmeteo-seasonal.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`f1761acbbc25de4800feb5dd6901ac000f937971cb64f7833b30614dea80fc8f`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "latitude",
    "longitude",
    "daily",
    "models",
    "forecast_days",
    "timezone",
    "timeformat",
    "temperature_unit",
    "wind_speed_unit",
    "precipitation_unit"
  ],
  "parameter_rules": {
    "properties": {
      "latitude": {
        "type": "number",
        "minimum": -90,
        "maximum": 90
      },
      "longitude": {
        "type": "number",
        "minimum": -180,
        "maximum": 180
      },
      "daily": {
        "type": "string",
        "min_length": 1,
        "max_length": 2000
      },
      "models": {
        "type": "string",
        "min_length": 1,
        "max_length": 2000
      },
      "forecast_days": {
        "type": "integer",
        "minimum": 1,
        "maximum": 365
      }
    },
    "required_any_of": [
      [
        "latitude"
      ],
      [
        "longitude"
      ],
      [
        "daily"
      ]
    ]
  },
  "parameter_notes": {
    "latitude": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "longitude": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "daily": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "models": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "forecast_days": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "timezone": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "timeformat": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "temperature_unit": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "wind_speed_unit": "Open-Meteo官方参数；变量列表可用逗号分隔",
    "precipitation_unit": "Open-Meteo官方参数；变量列表可用逗号分隔"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "success_when_data_present": true,
  "any_data_paths": [
    "daily"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://seasonal-api.open-meteo.com",
  "url_pattern": "/v1/seasonal",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "latitude",
    "longitude",
    "generationtime_ms",
    "utc_offset_seconds",
    "timezone",
    "timezone_abbreviation",
    "elevation",
    "current_units",
    "current",
    "hourly_units",
    "hourly",
    "daily_units",
    "daily",
    "results",
    "reason",
    "error"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 5,
      "every": "1s",
      "capacity": 5
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 不同模型的空间分辨率、时间范围和更新频率不同

## OpenStreetMap 周边商业与公共设施 (`osm-commercial-around`)

- 状态：`启用`
- 说明：使用固定、受限的 Overpass QL 模板，在指定公开坐标和半径内检索商店、餐饮、旅游、办公、公共交通及车站要素。
- 适用：商业设施密度；业态结构和竞争代理；公共交通与服务设施可达性
- 地域：全球；完整度取决于OpenStreetMap社区数据
- 新鲜度：随OpenStreetMap和Overpass实例更新
- 成本等级：`free-public-fair-use`
- 详情文件：`connectors/osm-commercial-around.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`a4af951ac7843d7df446a0ab4b4b04090a1c3b3155bfb0529b77276efcc2930d`

请求契约：

```json
{
  "path_parameter_names": [
    "latitude",
    "longitude",
    "radius"
  ],
  "path_parameters": {
    "latitude": {
      "pattern": "^-?[0-9]{1,2}(?:\\.[0-9]{1,7})?$",
      "max_length": 11
    },
    "longitude": {
      "pattern": "^-?(?:1[0-7][0-9]|[0-9]{1,2})(?:\\.[0-9]{1,7})?$",
      "max_length": 12
    },
    "radius": {
      "pattern": "^(?:[1-9][0-9]{2,3}|1[0-9]{4}|20000)$",
      "max_length": 5
    }
  },
  "query_parameter_names": [],
  "parameter_rules": {},
  "parameter_notes": {
    "latitude": "必填；WGS84纬度，预校验后进入固定查询模板",
    "longitude": "必填；WGS84经度，预校验后进入固定查询模板",
    "radius": "必填；100至20000米，建议城市商业模型使用1000至3000米"
  },
  "example_parameters": {
    "latitude": "26.0620",
    "longitude": "119.2920",
    "radius": "2000"
  },
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "version",
  "success_values": [
    0.6
  ],
  "any_data_paths": [
    "elements"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://overpass-api.de",
  "url_pattern": "/api/interpreter?data=%5Bout%3Ajson%5D%5Btimeout%3A25%5D%3B%0Anwr%28around%3A{radius}%2C{latitude}%2C{longitude}%29%5B~%22%5E%28shop%7Camenity%7Ctourism%7Coffice%7Cpublic_transport%7Crailway%29%24%22~%22.%22%5D%3B%0Aout%20center%20tags%20qt%20300%3B",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "version",
    "generator",
    "osm3s",
    "elements",
    "remark"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 1,
      "every": "2s",
      "capacity": 1
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 只执行固定Overpass模板，不接受任意QL、URL或标签表达式
- 单次最多返回300个排序后的要素，因此高密度区域可能发生截断
- OSM要素数量不是客流、销售额或完整商户名录
- 道路时间、室内动线、楼层分布、租金和经营状态不在本接口范围内

## OpenStreetMap逆地理编码 (`osm-nominatim-reverse`)

- 状态：`启用`
- 说明：将坐标解析为OSM地址、行政区和对象信息。
- 适用：坐标归属地核验；行政区识别
- 地域：全球
- 新鲜度：随OSM社区更新
- 成本等级：`free-public`
- 详情文件：`connectors/osm-nominatim-reverse.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`dbc194b301e91ad99950b0188bed1e2092f4c54fcf4ffdf918ad0bea3d96aef6`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "lat",
    "lon",
    "format",
    "zoom",
    "addressdetails",
    "extratags",
    "namedetails",
    "accept-language"
  ],
  "parameter_rules": {
    "properties": {
      "lat": {
        "type": "number",
        "minimum": -90,
        "maximum": 90
      },
      "lon": {
        "type": "number",
        "minimum": -180,
        "maximum": 180
      },
      "zoom": {
        "type": "integer",
        "minimum": 0,
        "maximum": 18
      }
    },
    "required_any_of": [
      [
        "lat"
      ],
      [
        "lon"
      ]
    ]
  },
  "parameter_notes": {
    "lat": "Nominatim参数",
    "lon": "Nominatim参数",
    "format": "Nominatim参数",
    "zoom": "Nominatim参数",
    "addressdetails": "Nominatim参数",
    "extratags": "Nominatim参数",
    "namedetails": "Nominatim参数",
    "accept-language": "Nominatim参数"
  },
  "example_parameters": {
    "lat": 26.0745,
    "lon": 119.2965,
    "format": "jsonv2"
  },
  "input_headers": [
    "User-Agent"
  ],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "success_when_data_present": true,
  "any_data_paths": [
    "place_id",
    "display_name",
    "address"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://nominatim.openstreetmap.org",
  "url_pattern": "/reverse",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "place_id",
    "licence",
    "osm_type",
    "osm_id",
    "lat",
    "lon",
    "class",
    "type",
    "place_rank",
    "importance",
    "addresstype",
    "name",
    "display_name",
    "address",
    "boundingbox",
    "extratags",
    "namedetails"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 1,
      "every": "1s",
      "capacity": 1
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 公共Nominatim限流严格；不得批量高频调用

## OpenStreetMap Nominatim 地点搜索 (`osm-nominatim-search`)

- 状态：`启用`
- 说明：使用 OpenStreetMap Nominatim 在固定公开主机上搜索公开地点并返回 GeocodeJSON 坐标和地址属性。
- 适用：公开商业设施定位；地址与行政区核验；无密钥空间分析锚点
- 地域：全球；完整度取决于OpenStreetMap社区数据
- 新鲜度：随OpenStreetMap与Nominatim索引更新
- 成本等级：`free-public-fair-use`
- 详情文件：`connectors/osm-nominatim-search.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`97150c005ba33ae41fc2ff5c5d88147739c4fb0a485f5eea029e583546c50151`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "q",
    "format",
    "limit",
    "countrycodes",
    "addressdetails",
    "extratags",
    "namedetails",
    "accept-language"
  ],
  "parameter_rules": {},
  "parameter_notes": {
    "q": "必填；结构化地点查询文本",
    "format": "必填；正式票据使用geocodejson",
    "limit": "可选；返回数量，建议不超过5",
    "countrycodes": "可选；国家代码过滤，例如cn",
    "addressdetails": "可选；地址明细",
    "extratags": "可选；额外标签",
    "namedetails": "可选；名称明细",
    "accept-language": "可选；返回语言"
  },
  "example_parameters": {
    "q": "福州宝龙城市广场,台江区,福州市,福建省,中国",
    "format": "geocodejson",
    "limit": 5,
    "countrycodes": "cn",
    "addressdetails": 1,
    "extratags": 1,
    "namedetails": 1,
    "accept-language": "zh-CN"
  },
  "input_headers": [
    "User-Agent"
  ],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "type",
  "success_values": [
    "FeatureCollection"
  ],
  "any_data_paths": [
    "features"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://nominatim.openstreetmap.org",
  "url_pattern": "/search",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "type",
    "geocoding",
    "features",
    "bbox"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 1,
      "every": "1s",
      "capacity": 1
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- Nominatim是地点搜索而非完整POI枚举，周边设施使用独立Overpass连接器
- 结果依赖OpenStreetMap覆盖和名称标注，必须核验名称、地址和geometry
- 公开服务执行每秒一次限流；不得批量抓取或高频调用
- 坐标为WGS84经纬度，geometry.coordinates顺序为经度、纬度

## 天地图地名与POI搜索 (`tianditu-place-search`)

- 状态：`启用`
- 说明：调用天地图地名搜索V2.0固定接口，使用受控postStr查询公开地名、POI、行政区或统计结果。
- 适用：中国地点与POI核验；行政区和公共设施搜索；空间分析锚点补充
- 地域：中国；具体覆盖和更新频率以天地图服务为准
- 新鲜度：请求时读取天地图当前公开数据
- 成本等级：`provider-key-quota`
- 详情文件：`connectors/tianditu-place-search.connector.json`
- Secret环境变量名：`TIANDITU_API_KEY`（仅名称）
- 连接器SHA-256：`b251a928f66892a0fa2c597e15dd99ed56334ece1e77aa6f8987be792e32acef`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "postStr",
    "type"
  ],
  "parameter_rules": {},
  "parameter_notes": {
    "postStr": "必填；字符串化JSON。建议普通搜索固定包含keyWord、level、mapBound、queryType、start、count",
    "type": "必填；固定填写query；tk由服务端Secret注入，不得由客户端提交"
  },
  "example_parameters": {
    "postStr": "{\"keyWord\":\"福州宝龙城市广场\",\"level\":12,\"mapBound\":\"119.20,25.95,119.45,26.20\",\"queryType\":1,\"start\":0,\"count\":10}",
    "type": "query"
  },
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "status.infocode",
  "success_values": [
    1000
  ],
  "error_code_path": "status.infocode",
  "message_path": "status.cndesc",
  "any_data_paths": [
    "pois",
    "statistics",
    "area",
    "lineData",
    "prompt"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.tianditu.gov.cn",
  "url_pattern": "/v2/search",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "resultType",
    "count",
    "keyword",
    "pois",
    "statistics",
    "priorityCitys",
    "allAdmins",
    "area",
    "lineData",
    "prompt",
    "status"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 1,
      "every": "1s",
      "capacity": 1
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 需要在天地图开发者控制台申请Key，并配置独立 Repository Secret TIANDITU_API_KEY
- postStr必须符合天地图官方地名搜索V2.0参数规则；本连接器不接受任意URL
- POI结果和坐标必须与高德、OpenStreetMap或现场信息交叉核验
- 配额、许可、坐标体系和使用限制以天地图账户及官方条款为准

## Wikidata实体声明 (`wikidata-claims`)

- 状态：`启用`
- 说明：按实体和可选属性读取结构化声明。
- 适用：按实体和可选属性读取结构化声明。
- 地域：全球
- 新鲜度：实时读取Wikidata当前版本
- 成本等级：`free-public`
- 详情文件：`connectors/wikidata-claims.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`223ddbd42371c13fcf98c47a685ed1c0b7fa69d191732438680ed9c306a61d54`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "action",
    "entity",
    "property",
    "rank",
    "format"
  ],
  "parameter_rules": {},
  "parameter_notes": {
    "action": "Wikidata Action API参数",
    "entity": "Wikidata Action API参数",
    "property": "Wikidata Action API参数",
    "rank": "Wikidata Action API参数",
    "format": "Wikidata Action API参数"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "success_when_data_present": true,
  "any_data_paths": [
    "claims"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://www.wikidata.org",
  "url_pattern": "/w/api.php",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "entities",
    "claims",
    "success",
    "error"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 1,
      "every": "1s",
      "capacity": 1
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 开放协作数据需核验来源与修订历史；不开放任意SPARQL查询

## Wikidata实体原始JSON (`wikidata-entity-data`)

- 状态：`启用`
- 说明：按QID读取完整实体JSON文档。
- 适用：按QID读取完整实体JSON文档。
- 地域：全球
- 新鲜度：实时读取Wikidata当前版本
- 成本等级：`free-public`
- 详情文件：`connectors/wikidata-entity-data.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`f8323c864f45220958108a5eead1c32a88bafdd5511201d189a94c4427f6faf0`

请求契约：

```json
{
  "path_parameter_names": [
    "entity_id"
  ],
  "path_parameters": {
    "entity_id": {
      "pattern": "^[QPL][0-9]{1,20}$",
      "max_length": 21
    }
  },
  "query_parameter_names": [],
  "parameter_rules": {},
  "parameter_notes": {},
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "success_when_data_present": true,
  "any_data_paths": [
    "entities"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://www.wikidata.org",
  "url_pattern": "/wiki/Special:EntityData/{entity_id}.json",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "entities",
    "claims",
    "success",
    "error"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 1,
      "every": "1s",
      "capacity": 1
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 开放协作数据需核验来源与修订历史；不开放任意SPARQL查询

## Wikidata实体详情 (`wikidata-entity-get`)

- 状态：`启用`
- 说明：按QID、站点标题或页面标题读取标签、描述、别名、声明和站点链接。
- 适用：按QID、站点标题或页面标题读取标签、描述、别名、声明和站点链接。
- 地域：全球
- 新鲜度：实时读取Wikidata当前版本
- 成本等级：`free-public`
- 详情文件：`connectors/wikidata-entity-get.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`6853309aba3e05fde88785ad9af98631773aca57891bf014554b48cf21ef39ad`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "action",
    "ids",
    "sites",
    "titles",
    "props",
    "languages",
    "sitefilter",
    "languagefallback",
    "normalize",
    "redirects",
    "format"
  ],
  "parameter_rules": {},
  "parameter_notes": {
    "action": "Wikidata Action API参数",
    "ids": "Wikidata Action API参数",
    "sites": "Wikidata Action API参数",
    "titles": "Wikidata Action API参数",
    "props": "Wikidata Action API参数",
    "languages": "Wikidata Action API参数",
    "sitefilter": "Wikidata Action API参数",
    "languagefallback": "Wikidata Action API参数",
    "normalize": "Wikidata Action API参数",
    "redirects": "Wikidata Action API参数",
    "format": "Wikidata Action API参数"
  },
  "example_parameters": {},
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "success_when_data_present": true,
  "any_data_paths": [
    "entities"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://www.wikidata.org",
  "url_pattern": "/w/api.php",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "entities",
    "claims",
    "success",
    "error"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 1,
      "every": "1s",
      "capacity": 1
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 开放协作数据需核验来源与修订历史；不开放任意SPARQL查询

## Wikidata 公开实体搜索 (`wikidata-entity-search`)

- 状态：`启用`
- 说明：调用Wikidata官方Wikibase接口，按名称和别名搜索公开实体、标签、描述与实体ID。
- 适用：公开实体识别；名称消歧；为跨数据源任务取得稳定Wikidata ID
- 地域：全球
- 新鲜度：请求时读取Wikidata当前公开数据
- 成本等级：`free-public`
- 详情文件：`connectors/wikidata-entity-search.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`8a85db3c714af46ba389164e9fd05a635dd1aa1e43303329b250aa1a38974555`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "action",
    "search",
    "language",
    "uselang",
    "type",
    "limit",
    "continue",
    "format"
  ],
  "parameter_rules": {},
  "parameter_notes": {
    "action": "固定填写wbsearchentities",
    "search": "必填；实体名称或关键词",
    "language": "必填；搜索语言代码",
    "uselang": "可选；返回界面语言",
    "type": "可选；item或property",
    "limit": "可选；结果数量",
    "continue": "可选；分页游标",
    "format": "固定填写json"
  },
  "example_parameters": {
    "action": "wbsearchentities",
    "search": "Fuzhou",
    "language": "en",
    "uselang": "zh",
    "type": "item",
    "limit": 5,
    "format": "json"
  },
  "input_headers": [],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "success",
  "success_values": [
    1
  ],
  "any_data_paths": [
    "search"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://www.wikidata.org",
  "url_pattern": "/w/api.php",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "searchinfo",
    "search",
    "search-continue",
    "success"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 1,
      "every": "1s",
      "capacity": 1
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 只用于公开实体搜索，不提供登录、编辑、写入或任意SPARQL执行
- 同名实体必须结合描述、国家和实体ID消歧
- Wikidata为协作式知识库，关键结论仍需结合原始来源核验

## 世界银行国家与经济体目录 (`worldbank-countries`)

- 状态：`启用`
- 说明：读取国家、地区、收入组、经纬度和资本信息。
- 适用：读取国家、地区、收入组、经纬度和资本信息。
- 地域：全球
- 新鲜度：随世界银行数据发布更新
- 成本等级：`free-public`
- 详情文件：`connectors/worldbank-countries.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`b2a028f95ee126284f90a362679f904c2a7530529ea1332860292a1f8ef9ccff`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "format",
    "per_page",
    "page"
  ],
  "parameter_rules": {},
  "parameter_notes": {
    "format": "世界银行API参数；建议format=json",
    "per_page": "世界银行API参数；建议format=json",
    "page": "世界银行API参数；建议format=json"
  },
  "example_parameters": {
    "format": "json"
  },
  "input_headers": [
    "User-Agent"
  ],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "success_when_data_present": true,
  "any_data_paths": [
    "1"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.worldbank.org",
  "url_pattern": "/v2/country",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [],
  "resilience": {
    "rate_limit": {
      "max_rate": 2,
      "every": "1s",
      "capacity": 2
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 部分指标存在发布滞后、缺失值和口径差异

## 世界银行单一经济体元数据 (`worldbank-country`)

- 状态：`启用`
- 说明：按国家或地区代码读取经济体元数据。
- 适用：按国家或地区代码读取经济体元数据。
- 地域：全球
- 新鲜度：随世界银行数据发布更新
- 成本等级：`free-public`
- 详情文件：`connectors/worldbank-country.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`b7c9f57073f4acd11f39c819fde26872c4241ea873c7285af6dbe3ac2b2cdc74`

请求契约：

```json
{
  "path_parameter_names": [
    "country_code"
  ],
  "path_parameters": {
    "country_code": {
      "pattern": "^[A-Za-z0-9]{2,3}$",
      "max_length": 3
    }
  },
  "query_parameter_names": [
    "format"
  ],
  "parameter_rules": {},
  "parameter_notes": {
    "format": "世界银行API参数；建议format=json"
  },
  "example_parameters": {
    "format": "json"
  },
  "input_headers": [
    "User-Agent"
  ],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "success_when_data_present": true,
  "any_data_paths": [
    "1"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.worldbank.org",
  "url_pattern": "/v2/country/{country_code}",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [],
  "resilience": {
    "rate_limit": {
      "max_rate": 2,
      "every": "1s",
      "capacity": 2
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 部分指标存在发布滞后、缺失值和口径差异

## 世界银行收入组目录 (`worldbank-income-levels`)

- 状态：`启用`
- 说明：读取低收入、中等收入和高收入分组。
- 适用：读取低收入、中等收入和高收入分组。
- 地域：全球
- 新鲜度：随世界银行数据发布更新
- 成本等级：`free-public`
- 详情文件：`connectors/worldbank-income-levels.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`919ea265578b99e196c2399cbb71d9e44aafa6cb3ef7e8eb9eb2fc44e1ab879f`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "format",
    "per_page",
    "page"
  ],
  "parameter_rules": {},
  "parameter_notes": {
    "format": "世界银行API参数；建议format=json",
    "per_page": "世界银行API参数；建议format=json",
    "page": "世界银行API参数；建议format=json"
  },
  "example_parameters": {
    "format": "json"
  },
  "input_headers": [
    "User-Agent"
  ],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "success_when_data_present": true,
  "any_data_paths": [
    "1"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.worldbank.org",
  "url_pattern": "/v2/incomeLevel",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [],
  "resilience": {
    "rate_limit": {
      "max_rate": 2,
      "every": "1s",
      "capacity": 2
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 部分指标存在发布滞后、缺失值和口径差异

## 世界银行发展指标时间序列 (`worldbank-indicator-jsonstat`)

- 状态：`启用`
- 说明：通过世界银行 Indicators API V2 按国家和指标代码读取公开发展时间序列；调用方必须显式请求 JSON-stat 格式。
- 适用：城市化与人口趋势宏观背景；人均收入和消费能力基准；商业环境跨来源交叉核验
- 地域：全球国家和地区；本连接器限制单个2至3位国家代码
- 新鲜度：随世界银行上游数据库更新；具体更新时间和年份以响应元数据为准
- 成本等级：`free-public`
- 详情文件：`connectors/worldbank-indicator-jsonstat.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`d2aa4ee92abc259f9891c83b65a7c297b48ede159a55b68e2d79572592521eaa`

请求契约：

```json
{
  "path_parameter_names": [
    "country_code",
    "indicator_code"
  ],
  "path_parameters": {
    "country_code": {
      "pattern": "^[A-Za-z]{2,3}$",
      "max_length": 3
    },
    "indicator_code": {
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{1,63}$",
      "max_length": 64
    }
  },
  "query_parameter_names": [
    "format",
    "date",
    "mrv",
    "mrnev",
    "gapfill",
    "frequency",
    "source",
    "per_page",
    "page",
    "footnote",
    "scale",
    "ctrycode"
  ],
  "parameter_rules": {},
  "parameter_notes": {
    "country_code": "必填；2至3位国家或地区代码，例如CHN",
    "indicator_code": "必填；世界银行指标代码",
    "format": "必填；本连接器正式票据使用jsonstat",
    "date": "可选；年份或年份区间，例如2015:2025",
    "mrv": "可选；最近若干期",
    "mrnev": "可选；最近非空若干期",
    "gapfill": "可选；是否填补空期",
    "frequency": "可选；频率",
    "source": "可选；数据源编号",
    "per_page": "可选；分页大小",
    "page": "可选；页码",
    "footnote": "可选；脚注",
    "scale": "可选；缩放",
    "ctrycode": "可选；国家代码响应选项"
  },
  "example_parameters": {
    "country_code": "CHN",
    "indicator_code": "SP.URB.TOTL.IN.ZS",
    "format": "jsonstat",
    "date": "2015:2025"
  },
  "input_headers": [
    "User-Agent"
  ],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "status_path": "class",
  "success_values": [
    "dataset"
  ],
  "any_data_paths": [
    "value"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.worldbank.org",
  "url_pattern": "/v2/country/{country_code}/indicator/{indicator_code}",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [
    "version",
    "class",
    "label",
    "source",
    "updated",
    "id",
    "size",
    "role",
    "dimension",
    "value",
    "status"
  ],
  "resilience": {
    "rate_limit": {
      "max_rate": 2,
      "every": "1s",
      "capacity": 2
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 世界银行指标通常是国家或地区级，不代表福州或宝龙周边本地实测值
- 正式票据必须显式传format=jsonstat；响应合同要求class=dataset且value非空
- 指标定义、基年、币种、许可和修订以响应元数据及原始数据源为准
- 关键商业判断必须与本地人口、POI、交通和现场数据组合使用

## 世界银行单一指标元数据 (`worldbank-indicator`)

- 状态：`启用`
- 说明：按指标代码读取名称、定义、来源和主题。
- 适用：按指标代码读取名称、定义、来源和主题。
- 地域：全球
- 新鲜度：随世界银行数据发布更新
- 成本等级：`free-public`
- 详情文件：`connectors/worldbank-indicator.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`a45f3f705bd2c3d5273aaf00c6415e7ebf185e9e5a43667e204bb028f3bd3ff3`

请求契约：

```json
{
  "path_parameter_names": [
    "indicator_code"
  ],
  "path_parameters": {
    "indicator_code": {
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{1,63}$",
      "max_length": 64
    }
  },
  "query_parameter_names": [
    "format"
  ],
  "parameter_rules": {},
  "parameter_notes": {
    "format": "世界银行API参数；建议format=json"
  },
  "example_parameters": {
    "format": "json"
  },
  "input_headers": [
    "User-Agent"
  ],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "success_when_data_present": true,
  "any_data_paths": [
    "1"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.worldbank.org",
  "url_pattern": "/v2/indicator/{indicator_code}",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [],
  "resilience": {
    "rate_limit": {
      "max_rate": 2,
      "every": "1s",
      "capacity": 2
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 部分指标存在发布滞后、缺失值和口径差异

## 世界银行指标目录 (`worldbank-indicators`)

- 状态：`启用`
- 说明：分页读取指标代码、名称、来源和说明。
- 适用：分页读取指标代码、名称、来源和说明。
- 地域：全球
- 新鲜度：随世界银行数据发布更新
- 成本等级：`free-public`
- 详情文件：`connectors/worldbank-indicators.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`71f3d4c868ee92e250f461fa8c6b2e7b08856e3a43b377f7bd0a91310e887696`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "format",
    "source",
    "per_page",
    "page"
  ],
  "parameter_rules": {},
  "parameter_notes": {
    "format": "世界银行API参数；建议format=json",
    "source": "世界银行API参数；建议format=json",
    "per_page": "世界银行API参数；建议format=json",
    "page": "世界银行API参数；建议format=json"
  },
  "example_parameters": {
    "format": "json"
  },
  "input_headers": [
    "User-Agent"
  ],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "success_when_data_present": true,
  "any_data_paths": [
    "1"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.worldbank.org",
  "url_pattern": "/v2/indicator",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [],
  "resilience": {
    "rate_limit": {
      "max_rate": 2,
      "every": "1s",
      "capacity": 2
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 部分指标存在发布滞后、缺失值和口径差异

## 世界银行贷款类型目录 (`worldbank-lending-types`)

- 状态：`启用`
- 说明：读取IDA、IBRD等贷款分类。
- 适用：读取IDA、IBRD等贷款分类。
- 地域：全球
- 新鲜度：随世界银行数据发布更新
- 成本等级：`free-public`
- 详情文件：`connectors/worldbank-lending-types.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`2b6dfb6ff7016fec6427d1c126cfdbb7905d631745f4afb75e13da664a3f7287`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "format",
    "per_page",
    "page"
  ],
  "parameter_rules": {},
  "parameter_notes": {
    "format": "世界银行API参数；建议format=json",
    "per_page": "世界银行API参数；建议format=json",
    "page": "世界银行API参数；建议format=json"
  },
  "example_parameters": {
    "format": "json"
  },
  "input_headers": [
    "User-Agent"
  ],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "success_when_data_present": true,
  "any_data_paths": [
    "1"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.worldbank.org",
  "url_pattern": "/v2/lendingType",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [],
  "resilience": {
    "rate_limit": {
      "max_rate": 2,
      "every": "1s",
      "capacity": 2
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 部分指标存在发布滞后、缺失值和口径差异

## 世界银行数据源目录 (`worldbank-sources`)

- 状态：`启用`
- 说明：读取数据库来源、更新时间和元数据。
- 适用：读取数据库来源、更新时间和元数据。
- 地域：全球
- 新鲜度：随世界银行数据发布更新
- 成本等级：`free-public`
- 详情文件：`connectors/worldbank-sources.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`2db2dad4c3540288d30c75c7597b98252915a9b550df69a8678ce0f3dc85f4db`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "format",
    "per_page",
    "page"
  ],
  "parameter_rules": {},
  "parameter_notes": {
    "format": "世界银行API参数；建议format=json",
    "per_page": "世界银行API参数；建议format=json",
    "page": "世界银行API参数；建议format=json"
  },
  "example_parameters": {
    "format": "json"
  },
  "input_headers": [
    "User-Agent"
  ],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "success_when_data_present": true,
  "any_data_paths": [
    "1"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.worldbank.org",
  "url_pattern": "/v2/source",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [],
  "resilience": {
    "rate_limit": {
      "max_rate": 2,
      "every": "1s",
      "capacity": 2
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 部分指标存在发布滞后、缺失值和口径差异

## 世界银行主题目录 (`worldbank-topics`)

- 状态：`启用`
- 说明：读取经济、社会、环境和治理主题。
- 适用：读取经济、社会、环境和治理主题。
- 地域：全球
- 新鲜度：随世界银行数据发布更新
- 成本等级：`free-public`
- 详情文件：`connectors/worldbank-topics.connector.json`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`324981ab0e03779b014f8522a037dedbf2c777b8102a50f6b61a1a32f0751dbc`

请求契约：

```json
{
  "path_parameter_names": [],
  "path_parameters": {},
  "query_parameter_names": [
    "format",
    "per_page",
    "page"
  ],
  "parameter_rules": {},
  "parameter_notes": {
    "format": "世界银行API参数；建议format=json",
    "per_page": "世界银行API参数；建议format=json",
    "page": "世界银行API参数；建议format=json"
  },
  "example_parameters": {
    "format": "json"
  },
  "input_headers": [
    "User-Agent"
  ],
  "additional_parameters_allowed": false
}
```

响应契约：

```json
{
  "success_when_data_present": true,
  "any_data_paths": [
    "1"
  ]
}
```

安全后端契约：

```json
{
  "host": "https://api.worldbank.org",
  "url_pattern": "/v2/topic",
  "method": "GET",
  "encoding": "json",
  "allowed_response_fields": [],
  "resilience": {
    "rate_limit": {
      "max_rate": 2,
      "every": "1s",
      "capacity": 2
    }
  },
  "rate_limit_enabled": true,
  "circuit_breaker_enabled": true,
  "ssrf_static_policy": "public-host-or-loopback-test-only"
}
```

限制：
- 部分指标存在发布滞后、缺失值和口径差异
