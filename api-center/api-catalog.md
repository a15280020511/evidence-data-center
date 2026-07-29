# API 中心能力目录

- 普通连接器总数：`21`
- 普通连接器已启用：`21`
- 托管提供方总数：`6`
- 托管提供方已启用：`6`
- 目录 SHA-256：`0fc90a153262cadc9dfa314fc3d021b988cfb5589151d76f14aefc903b925247`
- 选择者：`GPTs 使用中心`
- 维修者：`普通网页 GPT + GitHub 插件`
- Secret 值：`不暴露`

GPTs先读本目录。BigQuery、Earth Engine、AKShare、Ashare与AIFin Market的完整操作目录分别在 `google-cloud/provider-catalog.json`、`akshare/provider-catalog.json`和`aifin-market/provider-catalog.json`；普通接口详情仍在连接器和元数据文件中。

## 托管提供方

| 提供方 | ID | 状态 | 票据前缀 | 操作数量 |
|---|---|---|---|---|
| Google BigQuery | `bigquery` | 启用 | `[api-gcp]` | `7` |
| Google Earth Engine | `earth-engine` | 启用 | `[api-gcp]` | `6` |
| Google Data Commons | `data-commons` | 启用 | `[api-dc]` | `5` |
| AKShare 中国金融公开数据 | `akshare` | 启用 | `[api-akshare]` | `5` |
| Ashare 轻量 A 股行情 | `ashare` | 启用 | `[api-ashare]` | `1` |
| Wind AIFin Market 金融数据与能力 | `aifin-market` | 启用 | `[api-aifin]` | `7` |

## 普通连接器

| 能力 | ID | 状态 | 分类 | 端点 | 参数 |
|---|---|---|---|---|---|
| 高德驾车路线规划 | `amap-direction-driving` | 启用 | `routing` | `GET /data/amap/direction/driving` | `origin, destination, waypoints, strategy, show_fields` |
| 高德步行路线规划 | `amap-direction-walking` | 启用 | `routing` | `GET /data/amap/direction/walking` | `origin, destination, show_fields` |
| 高德多点距离测量 | `amap-distance` | 启用 | `distance` | `GET /data/amap/distance` | `origins, destination, type` |
| 高德地址转坐标 | `amap-geocode` | 启用 | `geocoding` | `GET /data/amap/geocode` | `address, city, batch` |
| 高德 POI 关键词搜索 | `amap-place-text` | 启用 | `poi` | `GET /data/amap/place/text` | `keywords, types, region, page_size, page_num` |
| 高德坐标转地址 | `amap-regeocode` | 启用 | `geocoding` | `GET /data/amap/regeocode` | `location, radius, extensions` |
| 高德城市天气 | `amap-weather` | 启用 | `weather` | `GET /data/amap/weather` | `city, extensions` |
| 百度地图驾车路线规划 | `baidu-direction-driving` | 启用 | `china-routing` | `GET /data/baidu/direction/driving` | `origin, destination, waypoints, tactics, coord_type, ret_coordtype` |
| 百度地图地址转坐标 | `baidu-geocode` | 启用 | `china-geocoding` | `GET /data/baidu/geocode` | `address, city, output, ret_coordtype` |
| 百度地图POI搜索 | `baidu-place-search` | 启用 | `china-poi` | `GET /data/baidu/place/search` | `query, region, bounds, location, radius, scope, tag, page_size, page_num, output, coord_type, ret_coordtype` |
| ChinaData.live 中国统计数据集 | `chinadata-live-dataset` | 启用 | `china-statistics` | `GET /data/chinadata/dataset/{dataset_id}` | `dataset_id` |
| DBnomics 经济时间序列 | `dbnomics-series` | 启用 | `economic-time-series` | `GET /data/dbnomics/series/{provider_code}/{dataset_code}/{series_code}` | `provider_code, dataset_code, series_code, observations, facets, metadata, align_periods, limit, offset` |
| NewsAPI 全网新闻检索 | `newsapi-everything` | 启用 | `news-search` | `GET /data/newsapi/everything` | `q, searchIn, sources, domains, excludeDomains, from, to, language, sortBy, pageSize, page` |
| NewsAPI 新闻来源目录 | `newsapi-sources` | 启用 | `news-source-catalog` | `GET /data/newsapi/sources` | `category, language, country` |
| NewsAPI 头条新闻 | `newsapi-top-headlines` | 启用 | `news-headlines` | `GET /data/newsapi/top-headlines` | `q, sources, country, category, pageSize, page` |
| Open‑Meteo 全球天气预报 | `openmeteo-forecast` | 启用 | `global-weather` | `GET /data/openmeteo/forecast` | `latitude, longitude, current, hourly, daily, timezone, forecast_days, past_days, temperature_unit, wind_speed_unit, precipitation_unit, timeformat` |
| OpenStreetMap 周边商业与公共设施 | `osm-commercial-around` | 启用 | `commercial-spatial-poi` | `GET /data/osm/commercial/around/{latitude}/{longitude}/{radius}` | `latitude, longitude, radius` |
| OpenStreetMap Nominatim 地点搜索 | `osm-nominatim-search` | 启用 | `open-geocoding` | `GET /data/osm/nominatim/search` | `q, format, limit, countrycodes, addressdetails, extratags, namedetails, accept-language` |
| 天地图地名与POI搜索 | `tianditu-place-search` | 启用 | `china-place-search` | `GET /data/tianditu/place/search` | `postStr, type` |
| Wikidata 公开实体搜索 | `wikidata-entity-search` | 启用 | `knowledge-graph` | `GET /data/wikidata/entity/search` | `action, search, language, uselang, type, limit, continue, format` |
| 世界银行发展指标时间序列 | `worldbank-indicator-jsonstat` | 启用 | `global-development-indicators` | `GET /data/worldbank/indicator/{country_code}/{indicator_code}` | `country_code, indicator_code, format, date, mrv, mrnev, gapfill, frequency, source, per_page, page, footnote, scale, ctrycode` |

## 使用规则

1. GPTs只能选择已启用能力；
2. BigQuery和Earth Engine使用 `[api-gcp]` 票据，并先读完整托管目录；
3. BigQuery执行必须先dry-run，受扫描费用、项目和行数上限约束；
4. Earth Engine只允许目录读取和只读值计算，禁止导出或修改资产；
5. AKShare使用 `[api-akshare]`，Ashare使用 `[api-ashare]`，AIFin Market使用 `[api-aifin]`；
6. 普通连接器继续使用 `[api]` 票据和固定参数白名单；
7. 所有目录只暴露Secret环境变量名称，不暴露值。

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
| `catalog-datasets` | 列出指定获准项目中的全部可见数据集。 | `project_id, max_results, page_token` |
| `catalog-tables` | 列出指定数据集中的表、视图、外部表和物化视图。 | `project_id, dataset_id, max_results, page_token` |
| `catalog-table` | 读取指定表的完整安全元数据和字段结构，不读取表中数据。 | `project_id, dataset_id, table_id` |
| `catalog-routines` | 列出指定数据集中的用户定义函数和存储过程目录。 | `project_id, dataset_id, max_results, page_token` |
| `catalog-models` | 列出指定数据集中的BigQuery ML模型目录。 | `project_id, dataset_id, max_results, page_token` |
| `query-readonly` | 先dry-run估算扫描量，再执行只读GoogleSQL并返回有限行数和费用证据。 | `sql, location, maximum_bytes_billed, max_rows, timeout_ms, query_parameters_json` |

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
| `catalog-dataset-root` | 读取官方Earth Engine STAC总目录入口。 | `无` |
| `catalog-dataset-search` | 在官方STAC对象名称中搜索数据集，并返回可继续读取的对象路径。 | `search, max_results, page_token` |
| `catalog-dataset` | 按官方STAC对象路径读取一个数据集或子目录的完整元数据。 | `object_path` |
| `catalog-algorithms` | 从Earth Engine API读取全部算法的名称、说明、返回类型和参数，并支持搜索和分页。 | `search, offset, max_results` |
| `compute-value-readonly` | 执行经过结构和算法安全校验的Earth Engine序列表达式，只返回JSON值。 | `expression_json, workload_tag` |

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
| `resolve-place` | 按一个或多个公开地点名称解析Data Commons地点DCID。 | `nodes_json, property` |
| `resolve-indicator` | 按指标描述解析统计变量或主题DCID。 | `nodes_json` |
| `node-properties` | 按固定关系表达式读取节点属性、相邻实体或行政层级关系。 | `nodes_json, property` |
| `observations` | 读取指定实体和统计变量的最新、指定日期或完整时间序列观测，并保留facet来源。 | `entity_dcids_json, variable_dcids_json, date, select_json, facet_ids_json, domains_json` |

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
- 说明：通过固定、只读、限量的AKShare函数读取中国A股行情、历史K线、公司资料和财务指标。
- 目录策略：GPTs可读取完整固定操作目录，但不能提交任意AKShare函数名、URL或Python代码。
- 执行策略：每张票据只执行一个固定只读函数；限制行数、日期范围和响应大小；不连接券商、不下单。
- 票据前缀：`[api-akshare]`
- Secret环境变量名：`无`（仅名称）
- 提供方SHA-256：`0a18d0913d6766e063cea65d53d9e2985eafcb7eeaf45a54ed044ca07df4db86`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取AKShare适配器完整安全能力和限制，不访问上游。 | `无` |
| `stock-a-share-spot` | 读取A股实时行情总表，可按证券代码过滤并限制返回行数。 | `symbols, max_rows` |
| `stock-a-share-history` | 按证券代码、周期、日期和复权方式读取A股历史行情。 | `symbol, period, start_date, end_date, adjust, max_rows, timeout_seconds` |
| `stock-company-info` | 读取单只A股公开公司基础资料。 | `symbol, timeout_seconds` |
| `stock-financial-indicators` | 读取单只A股公开财务分析指标。 | `symbol, indicator, max_rows` |

限制：

```json
{
  "max_rows_default": 500,
  "max_rows_hard": 5000,
  "timeout_seconds_default": 20,
  "timeout_seconds_hard": 60,
  "arbitrary_functions_allowed": false,
  "arbitrary_urls_allowed": false,
  "brokerage_execution_allowed": false
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
- 说明：通过万得官方MCP端点，以固定、只读、限量操作访问股票、金融新闻、宏观经济和通用金融数据。
- 目录策略：GPTs可读取固定操作目录和参数名称；不得提交任意MCP端点、server_type、tool_name、脚本或密钥。
- 执行策略：每张票据只执行一个固定只读操作；先初始化MCP，再调用白名单工具；限制响应大小；不下单、不写入、不执行任意代码。
- 票据前缀：`[api-aifin]`
- Secret环境变量名：`WIND_API_KEY`（仅名称）
- 提供方SHA-256：`ffad3038d5f25148eee8beba9a9f59967baf07315816fbef65351e241c26aa10`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地AIFin Market固定能力与限制，不访问上游。 | `无` |
| `catalog-tools` | 列出指定受支持Wind MCP服务当前公开工具目录。 | `server_type` |
| `stock-quote` | 读取单只A股、港股或美股标的的最新行情快照。 | `windcode` |
| `stock-price-indicators` | 读取单只股票指定价格指标。 | `windcode, indexes` |
| `financial-news` | 按查询词读取有限条数的万得金融新闻结果。 | `query, top_k` |
| `economic-data` | 按自然语言查询Wind EDB宏观或行业经济指标。 | `executionMode, question, observation, beginDate, endDate` |
| `analytics-query` | 在专项工具无法覆盖时执行单个通用结构化金融取数问题。 | `question` |

限制：

```json
{
  "max_operations_per_ticket": 1,
  "max_response_bytes": 200000,
  "timeout_seconds": 60,
  "arbitrary_server_types_allowed": false,
  "arbitrary_tool_names_allowed": false,
  "arbitrary_urls_allowed": false,
  "trading_or_order_execution_allowed": false,
  "write_operations_allowed": false
}
```

## 已由托管提供方替代的旧连接器

- `gdelt-doc-articles` → bigquery/query-readonly against gdelt-bq.gdeltv2
- `nasa-black-marble-granules` → earth-engine catalog and compute using NASA/VIIRS/002/VNP46A2
- `worldpop-population-stats` → earth-engine catalog and compute using WorldPop/GP/100m/pop

## 高德驾车路线规划 (`amap-direction-driving`)

- 状态：`启用`
- 说明：根据起点、终点及可选途经点取得驾车路线、距离、预计时间和路线步骤。
- 适用：路线比较；通勤与配送测算；候选区域之间的行驶成本估算
- 地域：中国大陆
- 新鲜度：请求时实时返回；交通时效以供应商响应为准
- 成本等级：`provider-quota`
- 详情文件：`connectors/amap-direction-driving.connector.json`
- 元数据位置：`catalog-metadata.json#/connectors/amap-direction-driving`
- Secret环境变量名：`AMAP_API_KEY`（仅名称）
- 连接器SHA-256：`17ea913d9880ac5b6125d1d76fb3a6da5c95128d30098997075a675e9b0421ed`

示例参数：

```json
{
  "origin": "119.2965,26.0745",
  "destination": "119.3062,26.0637"
}
```

限制：
- 不代表网约车平台实时订单热度
- 交通时间可能受实时拥堵和供应商策略影响

## 高德步行路线规划 (`amap-direction-walking`)

- 状态：`启用`
- 说明：取得两点之间的步行路线、距离、预计时间和路线步骤。
- 适用：短距离可达性；最后一公里分析；步行接驳测算
- 地域：中国大陆
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/amap-direction-walking.connector.json`
- 元数据位置：`catalog-metadata.json#/connectors/amap-direction-walking`
- Secret环境变量名：`AMAP_API_KEY`（仅名称）
- 连接器SHA-256：`57fbda206123099aa2c731e60d04582001ce0f79aa32c9cc7d8dc63ae952e7d4`

示例参数：

```json
{
  "origin": "119.2965,26.0745",
  "destination": "119.3000,26.0700"
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
- 元数据位置：`catalog-metadata.json#/connectors/amap-distance`
- Secret环境变量名：`AMAP_API_KEY`（仅名称）
- 连接器SHA-256：`f5b496e25bfe652cda2008f73ea1344d9f6b2c01772107be70aeb63710b77aae`

示例参数：

```json
{
  "origins": "119.2965,26.0745|119.3100,26.0800",
  "destination": "119.3062,26.0637",
  "type": "1"
}
```

限制：
- 仅提供距离和时间，不提供订单需求概率

## 高德地址转坐标 (`amap-geocode`)

- 状态：`启用`
- 说明：把公开地址转换为经纬度坐标和标准化地址信息。
- 适用：地点定位；路线任务准备；公开地址标准化
- 地域：中国大陆
- 新鲜度：请求时返回
- 成本等级：`provider-quota`
- 详情文件：`connectors/amap-geocode.connector.json`
- 元数据位置：`catalog-metadata.json#/connectors/amap-geocode`
- Secret环境变量名：`AMAP_API_KEY`（仅名称）
- 连接器SHA-256：`76cd76a735a9bff1bcbef92cd18881600c9d67f22cef8c856851e6da2a3565b5`

示例参数：

```json
{
  "address": "福州宝龙城市广场",
  "city": "福州"
}
```

限制：
- 模糊地址可能返回多个候选
- 不得提交私人住宅精确地址或个人轨迹

## 高德 POI 关键词搜索 (`amap-place-text`)

- 状态：`启用`
- 说明：按关键词、类型和区域搜索公开兴趣点及其坐标、地址和类别。
- 适用：候选地点发现；商圈与设施清单；公开地点核验
- 地域：中国大陆
- 新鲜度：请求时返回；POI 更新频率由供应商决定
- 成本等级：`provider-quota`
- 详情文件：`connectors/amap-place-text.connector.json`
- 元数据位置：`catalog-metadata.json#/connectors/amap-place-text`
- Secret环境变量名：`AMAP_API_KEY`（仅名称）
- 连接器SHA-256：`1e0a6151c5c88814877ba69d70dc34ccfe1d7c36c8ccebe218ed634bc2e1a9ce`

示例参数：

```json
{
  "keywords": "商场",
  "region": "福州",
  "page_size": 20,
  "page_num": 1
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
- 元数据位置：`catalog-metadata.json#/connectors/amap-regeocode`
- Secret环境变量名：`AMAP_API_KEY`（仅名称）
- 连接器SHA-256：`bac6fa7f5da6be5b711bd6e14a94b61b3d6f138b70efe9b4797dfbd5bbeb2800`

示例参数：

```json
{
  "location": "119.2965,26.0745",
  "extensions": "all"
}
```

限制：
- 不得用于处理私人实时轨迹
- 附近POI并不代表实时需求

## 高德城市天气 (`amap-weather`)

- 状态：`启用`
- 说明：取得指定城市的实时天气或预报信息。
- 适用：需求情景调整；出行风险分析；配送和网约车天气修正
- 地域：中国大陆
- 新鲜度：实时或预报；以响应时间为准
- 成本等级：`provider-quota`
- 详情文件：`connectors/amap-weather.connector.json`
- 元数据位置：`catalog-metadata.json#/connectors/amap-weather`
- Secret环境变量名：`AMAP_API_KEY`（仅名称）
- 连接器SHA-256：`d86b2afd7067da126fe4d377222fef5824975f0333ae09bf75a4f819b29ff608`

示例参数：

```json
{
  "city": "350100",
  "extensions": "base"
}
```

限制：
- 天气预报存在不确定性
- 不能替代平台订单或交通实时数据

## 百度地图驾车路线规划 (`baidu-direction-driving`)

- 状态：`启用`
- 说明：根据起终点及可选途经点读取驾车路线、距离、耗时和步骤。
- 适用：路线比较；配送与通勤成本估算；候选区域之间的可达性建模
- 地域：中国；以百度地图道路覆盖为准
- 新鲜度：请求时读取；交通时效以百度响应为准
- 成本等级：`provider-key-quota`
- 详情文件：`connectors/baidu-direction-driving.connector.json`
- 元数据位置：`catalog-metadata.json#/connectors/baidu-direction-driving`
- Secret环境变量名：`BAIDU_MAP_API_KEY`（仅名称）
- 连接器SHA-256：`e0e09d46fa8a7dc9468a0718d872fd77f642bf444042f0e2d0c38433e8f5b615`

示例参数：

```json
{
  "origin": "26.0745,119.2965",
  "destination": "26.0637,119.3062",
  "coord_type": "gcj02",
  "ret_coordtype": "gcj02"
}
```

限制：
- 路线耗时不代表网约车订单热度
- 需要BAIDU_MAP_API_KEY
- 实时交通能力和配额取决于百度账户及接口返回
- 坐标顺序和坐标系必须在调用前核验

## 百度地图地址转坐标 (`baidu-geocode`)

- 状态：`启用`
- 说明：使用百度地图地理编码服务把公开地址转换为坐标和可信度等结果。
- 适用：公开地点定位；路线任务准备；地址与坐标交叉核验
- 地域：中国；以百度地图覆盖为准
- 新鲜度：请求时读取百度地图当前数据
- 成本等级：`provider-key-quota`
- 详情文件：`connectors/baidu-geocode.connector.json`
- 元数据位置：`catalog-metadata.json#/connectors/baidu-geocode`
- Secret环境变量名：`BAIDU_MAP_API_KEY`（仅名称）
- 连接器SHA-256：`cbffb7b788ab5e19aed770f4e9a7e2cc4b15a58e98a58b21684abe52468da440`

示例参数：

```json
{
  "address": "福州宝龙城市广场",
  "city": "福州",
  "output": "json",
  "ret_coordtype": "gcj02ll"
}
```

限制：
- 需要BAIDU_MAP_API_KEY
- 百度坐标体系与WGS84不同，建模前必须统一坐标
- 不得提交私人住宅精确地址、个人实时位置或轨迹
- 配额和许可由百度地图开放平台账户决定

## 百度地图POI搜索 (`baidu-place-search`)

- 状态：`启用`
- 说明：按关键词和区域、边界或中心点搜索公开兴趣点。
- 适用：商圈与设施清单；竞争和业态代理变量；公开地点交叉核验
- 地域：中国；以百度地图覆盖为准
- 新鲜度：请求时读取百度地图当前POI数据
- 成本等级：`provider-key-quota`
- 详情文件：`connectors/baidu-place-search.connector.json`
- 元数据位置：`catalog-metadata.json#/connectors/baidu-place-search`
- Secret环境变量名：`BAIDU_MAP_API_KEY`（仅名称）
- 连接器SHA-256：`9404cfb3553a63c2492f7ede41e5efe80b30c8f82ad616768b44678d95067c98`

示例参数：

```json
{
  "query": "商场",
  "region": "福州",
  "scope": 2,
  "page_size": 20,
  "page_num": 0,
  "output": "json",
  "ret_coordtype": "gcj02ll"
}
```

限制：
- POI数量不等于实时客流、销售额或完整商户名录
- 需要BAIDU_MAP_API_KEY
- 页数和配额受上游限制
- 坐标体系必须在计算中心显式标注

## ChinaData.live 中国统计数据集 (`chinadata-live-dataset`)

- 状态：`启用`
- 说明：按稳定数据集 slug 获取 ChinaData.live 整理的中国宏观、人口、产业、能源和贸易等公开时间序列。
- 适用：中国宏观指标取数；人口与产业趋势；与官方或国际来源交叉核验
- 地域：中国；具体地域和口径以数据集元数据为准
- 新鲜度：随 ChinaData.live 对上游官方或国际来源的更新而更新
- 成本等级：`free-public-fair-use`
- 详情文件：`connectors/chinadata-live-dataset.connector.json`
- 元数据位置：`catalog-metadata.json#/connectors/chinadata-live-dataset`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`02ed5a5fff883cda4683ec734bbadd888c7952fdb7c1efa16cfcb756296e6ed5`

示例参数：

```json
{
  "dataset_id": "china-gdp"
}
```

限制：
- ChinaData.live 是独立数据门户，不是中国政府机构
- 必须保留响应中的 source、unit、frequency 和原始来源说明
- 公开 API 用于研究、评估和轻量调用，受公平使用和源数据许可约束
- 关键政策或投资结论应回到国家统计局、海关或原始国际机构复核

## DBnomics 经济时间序列 (`dbnomics-series`)

- 状态：`启用`
- 说明：通过 DBnomics v22 统一接口读取指定提供方、数据集和序列的元数据及观测值。
- 适用：中国国家统计局序列；国际宏观指标交叉验证；可复现历史时间序列分析
- 地域：全球；可通过 NBS 等提供方读取中国数据
- 新鲜度：DBnomics 抓取器通常在上游发布后自动更新，并保留历史修订
- 成本等级：`free-public`
- 详情文件：`connectors/dbnomics-series.connector.json`
- 元数据位置：`catalog-metadata.json#/connectors/dbnomics-series`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`6f1cde18cc298975abe3c2683b777d373b16aa71e39981e449b87ceaffefee3f`

示例参数：

```json
{
  "provider_code": "NBS",
  "dataset_code": "A_A0201",
  "series_code": "A020106",
  "observations": 1
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
- 元数据位置：`catalog-metadata.json#/connectors/newsapi-everything`
- Secret环境变量名：`NEWSAPI_API_KEY`（仅名称）
- 连接器SHA-256：`d53a3b43ed4f4c58731c5121d08714a07b3639318d3142551d4aef72d287af19`

示例参数：

```json
{
  "q": "\"福州\" AND 商业",
  "language": "zh",
  "sortBy": "publishedAt",
  "pageSize": 20,
  "page": 1
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
- 元数据位置：`catalog-metadata.json#/connectors/newsapi-sources`
- Secret环境变量名：`NEWSAPI_API_KEY`（仅名称）
- 连接器SHA-256：`adacca590d8e6d1790d3b1a29ad292f247c7bda3cd7d381a5a4cdbe7f6e6bd61`

示例参数：

```json
{
  "language": "zh",
  "country": "cn"
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
- 元数据位置：`catalog-metadata.json#/connectors/newsapi-top-headlines`
- Secret环境变量名：`NEWSAPI_API_KEY`（仅名称）
- 连接器SHA-256：`03a4fce728dbf80a6c7b87e774e72f350d5cf5562a52de366ced920ba5a05e35`

示例参数：

```json
{
  "country": "cn",
  "category": "business",
  "pageSize": 20,
  "page": 1
}
```

限制：
- sources不能与country或category混用，错误组合会由上游拒绝
- 免费Developer套餐并不适合真正的实时生产监控
- 只提供新闻元数据和摘要片段，不提供完整正文
- 头条排序、来源覆盖和国家分类由NewsAPI决定，不能视为完整媒体样本

## Open‑Meteo 全球天气预报 (`openmeteo-forecast`)

- 状态：`启用`
- 说明：按经纬度读取当前天气、小时预报或逐日预报，适合全球天气情景与出行风险修正。
- 适用：全球天气查询；商业与出行情景修正；配送和网约车天气风险建模
- 地域：全球经纬度
- 新鲜度：请求时读取Open‑Meteo当前模型结果；更新频率取决于具体预报模型
- 成本等级：`free-public-fair-use`
- 详情文件：`connectors/openmeteo-forecast.connector.json`
- 元数据位置：`catalog-metadata.json#/connectors/openmeteo-forecast`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`2680f2991acee80c8a4b29a1f39126e28ad13a98ad9edb1b56f7a3f63dcee97f`

示例参数：

```json
{
  "latitude": 26.0745,
  "longitude": 119.2965,
  "current": "temperature_2m,precipitation,weather_code,wind_speed_10m",
  "hourly": "temperature_2m,precipitation_probability",
  "forecast_days": 3,
  "timezone": "Asia/Shanghai"
}
```

限制：
- 天气预报具有模型不确定性，不等于现场观测
- 免费公共服务受公平使用和上游可用性限制
- 经纬度必须为WGS84；不得提交个人实时轨迹

## OpenStreetMap 周边商业与公共设施 (`osm-commercial-around`)

- 状态：`启用`
- 说明：使用固定、受限的 Overpass QL 模板，在指定公开坐标和半径内检索商店、餐饮、旅游、办公、公共交通及车站要素。
- 适用：商业设施密度；业态结构和竞争代理；公共交通与服务设施可达性
- 地域：全球；完整度取决于OpenStreetMap社区数据
- 新鲜度：随OpenStreetMap和Overpass实例更新
- 成本等级：`free-public-fair-use`
- 详情文件：`connectors/osm-commercial-around.connector.json`
- 元数据位置：`catalog-metadata.json#/connectors/osm-commercial-around`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`a4af951ac7843d7df446a0ab4b4b04090a1c3b3155bfb0529b77276efcc2930d`

示例参数：

```json
{
  "latitude": "26.0620",
  "longitude": "119.2920",
  "radius": "2000"
}
```

限制：
- 只执行固定Overpass模板，不接受任意QL、URL或标签表达式
- 单次最多返回300个排序后的要素，因此高密度区域可能发生截断
- OSM要素数量不是客流、销售额或完整商户名录
- 道路时间、室内动线、楼层分布、租金和经营状态不在本接口范围内

## OpenStreetMap Nominatim 地点搜索 (`osm-nominatim-search`)

- 状态：`启用`
- 说明：使用 OpenStreetMap Nominatim 在固定公开主机上搜索公开地点并返回 GeocodeJSON 坐标和地址属性。
- 适用：公开商业设施定位；地址与行政区核验；无密钥空间分析锚点
- 地域：全球；完整度取决于OpenStreetMap社区数据
- 新鲜度：随OpenStreetMap与Nominatim索引更新
- 成本等级：`free-public-fair-use`
- 详情文件：`connectors/osm-nominatim-search.connector.json`
- 元数据位置：`catalog-metadata.json#/connectors/osm-nominatim-search`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`97150c005ba33ae41fc2ff5c5d88147739c4fb0a485f5eea029e583546c50151`

示例参数：

```json
{
  "q": "福州宝龙城市广场,台江区,福州市,福建省,中国",
  "format": "geocodejson",
  "limit": 5,
  "countrycodes": "cn",
  "addressdetails": 1,
  "extratags": 1,
  "namedetails": 1,
  "accept-language": "zh-CN"
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
- 元数据位置：`catalog-metadata.json#/connectors/tianditu-place-search`
- Secret环境变量名：`TIANDITU_API_KEY`（仅名称）
- 连接器SHA-256：`b251a928f66892a0fa2c597e15dd99ed56334ece1e77aa6f8987be792e32acef`

示例参数：

```json
{
  "postStr": "{\"keyWord\":\"福州宝龙城市广场\",\"level\":12,\"mapBound\":\"119.20,25.95,119.45,26.20\",\"queryType\":1,\"start\":0,\"count\":10}",
  "type": "query"
}
```

限制：
- 需要在天地图开发者控制台申请Key，并在仓库API_CENTER_SECRETS_JSON中配置TIANDITU_API_KEY
- postStr必须符合天地图官方地名搜索V2.0参数规则；本连接器不接受任意URL
- POI结果和坐标必须与高德、OpenStreetMap或现场信息交叉核验
- 配额、许可、坐标体系和使用限制以天地图账户及官方条款为准

## Wikidata 公开实体搜索 (`wikidata-entity-search`)

- 状态：`启用`
- 说明：调用Wikidata官方Wikibase接口，按名称和别名搜索公开实体、标签、描述与实体ID。
- 适用：公开实体识别；名称消歧；为跨数据源任务取得稳定Wikidata ID
- 地域：全球
- 新鲜度：请求时读取Wikidata当前公开数据
- 成本等级：`free-public`
- 详情文件：`connectors/wikidata-entity-search.connector.json`
- 元数据位置：`catalog-metadata.json#/connectors/wikidata-entity-search`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`8a85db3c714af46ba389164e9fd05a635dd1aa1e43303329b250aa1a38974555`

示例参数：

```json
{
  "action": "wbsearchentities",
  "search": "Fuzhou",
  "language": "en",
  "uselang": "zh",
  "type": "item",
  "limit": 5,
  "format": "json"
}
```

限制：
- 只用于公开实体搜索，不提供登录、编辑、写入或任意SPARQL执行
- 同名实体必须结合描述、国家和实体ID消歧
- Wikidata为协作式知识库，关键结论仍需结合原始来源核验

## 世界银行发展指标时间序列 (`worldbank-indicator-jsonstat`)

- 状态：`启用`
- 说明：通过世界银行 Indicators API V2 按国家和指标代码读取公开发展时间序列；调用方必须显式请求 JSON-stat 格式。
- 适用：城市化与人口趋势宏观背景；人均收入和消费能力基准；商业环境跨来源交叉核验
- 地域：全球国家和地区；本连接器限制单个2至3位国家代码
- 新鲜度：随世界银行上游数据库更新；具体更新时间和年份以响应元数据为准
- 成本等级：`free-public`
- 详情文件：`connectors/worldbank-indicator-jsonstat.connector.json`
- 元数据位置：`catalog-metadata.json#/connectors/worldbank-indicator-jsonstat`
- Secret环境变量名：`无`（仅名称）
- 连接器SHA-256：`d2aa4ee92abc259f9891c83b65a7c297b48ede159a55b68e2d79572592521eaa`

示例参数：

```json
{
  "country_code": "CHN",
  "indicator_code": "SP.URB.TOTL.IN.ZS",
  "format": "jsonstat",
  "date": "2015:2025"
}
```

限制：
- 世界银行指标通常是国家或地区级，不代表福州或宝龙周边本地实测值
- 正式票据必须显式传format=jsonstat；响应合同要求class=dataset且value非空
- 指标定义、基年、币种、许可和修订以响应元数据及原始数据源为准
- 关键商业判断必须与本地人口、POI、交通和现场数据组合使用
