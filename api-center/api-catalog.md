# 情报中心能力目录

- 开放模式：`maximum-safe-readonly`
- 普通连接器：`68/68` 已启用
- 托管提供方：`61/61` 已启用
- 托管操作总数：`674`
- 已公开参数总数：`2376`
- 目录 SHA-256：`de95ccf64f1f918ea601222515201874ab0b0e5554c3cb3b7716743ea80a6ac8`
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
| AKShare 中国金融公开数据 | `akshare` | 启用 | `[api-akshare]` | `17` | 否 |
| Ashare 轻量 A 股行情 | `ashare` | 启用 | `[api-ashare]` | `1` | 否 |
| Wind AIFin Market 金融数据与能力 | `aifin-market` | 启用 | `[api-aifin]` | `17` | 否 |
| 元典法律智能开放平台 | `yuandian-law` | 启用 | `[api-yuandian]` | `40` | 否 |
| 天眼查开放平台 | `tianyancha` | 启用 | `[api-company]` | `3` | 否 |
| 东方财富妙想金融 API | `miaoxiang` | 启用 | `[api-mx]` | `4` | 否 |
| Jina AI Reader | `jina-reader` | 启用 | `[api-web]` | `2` | 否 |
| Exa Search API | `exa` | 启用 | `[api-web]` | `3` | 否 |
| Tavily Context API | `tavily` | 启用 | `[api-context]` | `5` | 否 |
| Firecrawl Context API（火行者） | `firecrawl` | 启用 | `[api-context]` | `4` | 否 |
| Browserless REST API | `browserless` | 启用 | `[api-browserless]` | `8` | 否 |
| TickFlow 金融行情 API | `tickflow` | 启用 | `[api-tickflow]` | `5` | 否 |
| SerpAPI 搜索结果 API | `serpapi` | 启用 | `[api-serpapi]` | `4` | 否 |
| Tushare Pro 中国金融数据 API | `tushare` | 启用 | `[api-tushare]` | `20` | 否 |
| BaoStock 中国证券免费数据 | `baostock` | 启用 | `[api-baostock]` | `20` | 否 |
| EODHD 全球金融市场数据 | `eodhd` | 启用 | `[api-eodhd]` | `25` | 否 |
| Google Data Commons | `data-commons` | 启用 | `[api-dc]` | `5` | 否 |
| 和风天气 QWeather | `qweather` | 启用 | `[api-qweather]` | `18` | 否 |
| Xweather 全球专业天气数据 | `xweather` | 启用 | `[api-xweather]` | `10` | 否 |
| 东方财富妙想 MCP | `miaoxiang-mcp` | 启用 | `[api-mx-mcp]` | `13` | 否 |
| East Asia Econ 东亚宏观数据库 | `east-asia-econ` | 启用 | `[api-east-asia-econ]` | `6` | 否 |
| Alpha Vantage 全球金融与宏观数据 | `alpha-vantage` | 启用 | `[api-alpha-vantage]` | `66` | 否 |
| Overture Maps 全球开放地图数据 | `overture-maps` | 启用 | `[api-overture]` | `7` | 否 |
| OECD Data Explorer SDMX | `oecd` | 启用 | `[api-oecd]` | `6` | 否 |
| AlphaFeed 中国与全球证券行情 | `alphafeed` | 启用 | `[api-alphafeed]` | `10` | 否 |
| WHO GHO OData 全球卫生数据 | `who-gho-odata` | 启用 | `[intel-who-gho]` | `8` | 否 |
| Mediastack 全球新闻情报 | `mediastack` | 启用 | `[intel-mediastack]` | `5` | 否 |
| Statistics of the World 全球统计 | `statistics-of-the-world` | 启用 | `[intel-sotw]` | `11` | 否 |
| AISstream 全球船舶实时AIS | `aisstream` | 启用 | `[intel-aisstream]` | `4` | 否 |
| 互联网档案馆 Internet Archive | `internet-archive` | 启用 | `[intel-internet-archive]` | `6` | 否 |
| Marketstack 全球股票 EOD 与历史数据 | `marketstack` | 启用 | `[intel-marketstack]` | `11` | 否 |
| NASA Open APIs 与 Earthdata GIBS | `nasa` | 启用 | `[intel-nasa]` | `25` | 否 |
| 挪威气象研究所 Geosatellite | `metno-geosatellite` | 启用 | `[intel-metno-geosatellite]` | `4` | 否 |
| 哥白尼数据空间 Copernicus CDSE | `copernicus-cdse` | 启用 | `[intel-copernicus]` | `7` | 否 |
| 美国能源信息署 EIA 能源数据 | `eia` | 启用 | `[intel-eia]` | `6` | 否 |
| 联合国 UN Comtrade 全球贸易数据 | `un-comtrade` | 启用 | `[intel-un-comtrade]` | `10` | 否 |
| OpenSky Network 全球航空状态与航迹数据 | `opensky-network` | 启用 | `[intel-opensky]` | `9` | 否 |
| HexDB 航空器型号、注册与航线补全 | `hexdb-aviation` | 启用 | `[intel-hexdb]` | `6` | 否 |
| WTO Timeseries 国际贸易与关税统计 | `wto` | 启用 | `[intel-wto]` | `7` | 否 |
| IMF SDMX 3.0 全球宏观、财政与金融统计 | `imf` | 启用 | `[intel-imf]` | `6` | 否 |
| World Bank Documents & Reports API | `worldbank-documents` | 启用 | `[intel-worldbank-docs]` | `7` | 否 |
| Bank for International Settlements SDMX API | `bis` | 启用 | `[intel-bis]` | `8` | 否 |
| Asian Development Bank KIDB SDMX | `adb` | 启用 | `[intel-adb]` | `8` | 否 |
| Wolfram|Alpha 计算知识 API | `wolfram-alpha` | 启用 | `[api-wolfram]` | `4` | 否 |
| LlamaParse 文档解析 API | `llamaparse` | 启用 | `[api-llamaparse]` | `3` | 否 |
| 全球公共数据、空间地理与中国数据 | `public-data-geospatial` | 启用 | `[intel-public-data]` | `35` | 否 |
| Cloudflare 情报与云端浏览器 | `cloudflare` | 启用 | `[intel-cloudflare]` | `22` | 否 |
| FRED 官方经济与金融时间序列 | `fred` | 启用 | `[intel-fred]` | `25` | 否 |
| Hugging Face Hub 公共模型与数据情报 | `huggingface-hub` | 启用 | `[intel-huggingface]` | `11` | 否 |
| 证据标准化、去重、谱系与传输清单 | `evidence-standardization` | 启用 | `[intel-evidence-standardize]` | `8` | 否 |
| 全球研报、政策、法律与公司文本情报 | `global-research-intelligence` | 启用 | `[intel-global-research]` | `23` | 否 |
| OpenBB 免费官方数据补充层 | `openbb-free` | 启用 | `[intel-openbb-free]` | `7` | 否 |
| 全球开放聚合数据层 | `open-data-aggregators` | 启用 | `[intel-open-data]` | `13` | 否 |
| NIH/NCBI/FDA 公共卫生与生物医学数据 | `nih-public-health` | 启用 | `[intel-nih-health]` | `6` | 否 |
| OpenStreetMap / Overpass / Nominatim | `openstreetmap` | 启用 | `[intel-osm]` | `6` | 否 |
| GNews 全球新闻情报 | `gnews` | 启用 | `[intel-gnews]` | `3` | 否 |
| 全球开放文献与资料库 | `global-literature-libraries` | 启用 | `[intel-literature]` | `10` | 否 |
| 全球文献档案资料库第二波 | `global-knowledge-archives` | 启用 | `[intel-knowledge]` | `9` | 否 |
| 全球知识织网第三波 | `global-knowledge-fabric` | 启用 | `[intel-knowledge-fabric]` | `9` | 否 |

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
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`92ce9c51980065a31186c2bc2273959f6e43c6441df5f29dea8affef1b6659c3`

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
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`90546500a5762ec00c17ea64e49cf60bada2bfe850551587abd8f0e161c73938`

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

## AKShare 中国金融公开数据 (`akshare`)

- 状态：`启用`
- 说明：通过固定、只读、限量的AKShare函数读取A股、ETF、资金流、财务报表、板块与中国宏观经济公共数据。
- 目录策略：GPTs可读取完整固定操作目录并选择高价值只读能力；不得提交任意AKShare函数名、URL、Python代码或动态导入目标。
- 执行策略：每张票据只执行一个固定白名单函数；严格校验证券代码、市场、周期、日期、报表类型、指标枚举、行数和超时；不连接券商、不下单。
- 票据前缀：`[api-akshare]`
- Secret环境变量名：`无`（仅名称）
- Repository Variable名：`无`（仅名称）
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
- Repository Variable名：`无`（仅名称）
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
- Repository Variable名：`无`（仅名称）
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
- Repository Variable名：`无`（仅名称）
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

## 天眼查开放平台 (`tianyancha`)

- 状态：`启用`
- 说明：通过天眼查官方开放平台读取企业基本信息和企业年报等公开企业数据。
- 目录策略：仅暴露仓库固定登记的天眼查官方只读接口，不接受任意 URL、请求头或代码。
- 执行策略：后端固定使用 Authorization Token；每张票据执行一个只读请求并过滤直接联系方式与个人身份字段。
- 票据前缀：`[api-company]`
- Secret环境变量名：`TIANYANCHA_API_TOKEN`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`cfae6391c6824cc14c5d90bbc3c90c2ec5bfe97910735691ff687db980909544`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取天眼查适配器本地安全能力目录，不访问上游且不需要密钥。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `company-basic` | 调用天眼查企业基本信息接口，按企业名称、企业ID、注册号或统一社会信用代码查询。 | `keyword` |

`company-basic` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "keyword": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    }
  },
  "required": [
    "keyword"
  ]
}
```

| `company-annual-reports` | 调用天眼查企业年报接口，按企业名称、企业ID、注册号或统一社会信用代码读取年报。 | `keyword, year` |

`company-annual-reports` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "keyword": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "year": {
      "type": "integer",
      "minimum": 1980,
      "maximum": 2100
    }
  },
  "required": [
    "keyword"
  ]
}
```

限制：

```json
{
  "requests_per_ticket": 1,
  "timeout_seconds_max": 60,
  "max_response_bytes": 2000000
}
```

## 东方财富妙想金融 API (`miaoxiang`)

- 状态：`启用`
- 说明：通过东方财富妙想金融能力读取金融资讯、行情与财务数据，并执行只读智能选股。
- 目录策略：仅登记东方财富妙想公开发布的固定只读接口；不接受任意 URL、请求头、代码或未登记路径。
- 执行策略：每张票据执行一个只读请求；禁止修改自选股、模拟交易、撤单、账户资金和其他写操作。
- 票据前缀：`[api-mx]`
- Secret环境变量名：`MX_APIKEY`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`ccd53455ebe7f9945eae858c350bf635362edf29ccbc98a89dae3f93c0ea2843`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取妙想适配器的本地安全能力目录，不访问上游且不需要密钥。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `financial-search` | 调用妙想资讯搜索，检索金融新闻、公告、研报、政策和市场事件。 | `query` |

`financial-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    }
  },
  "required": [
    "query"
  ]
}
```

| `financial-data` | 调用妙想金融数据查询，读取行情、资金、估值、财务、企业关系和经营数据。 | `query` |

`financial-data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    }
  },
  "required": [
    "query"
  ]
}
```

| `stock-screen` | 调用妙想智能选股，根据自然语言条件筛选证券并返回分页结果。 | `keyword, page_no, page_size` |

`stock-screen` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "keyword": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    },
    "page_no": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    },
    "page_size": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    }
  },
  "required": [
    "keyword"
  ]
}
```

限制：

```json
{
  "requests_per_ticket": 1,
  "timeout_seconds_max": 60,
  "max_response_bytes": 2000000,
  "max_query_characters": 500,
  "stock_screen_page_size_max": 100
}
```

## Jina AI Reader (`jina-reader`)

- 状态：`启用`
- 说明：使用 Jina Reader 将公开网页或公开 PDF 转换为适合大模型使用的 Markdown/JSON 内容。
- 目录策略：只允许读取调用方明确提供的公开 HTTPS URL；禁止内网、回环、链路本地、保留地址、登录态 Cookie、任意请求头和任意代码。
- 执行策略：无 Key 时使用 Jina Reader 官方匿名基础额度；配置 JINA_API_KEY 时仅在后端 Authorization Bearer 头注入以提高额度。每张票据最多读取一个 URL。
- 票据前缀：`[api-web]`
- Secret环境变量名：`无`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`44e58ffbc0199c0920a3f86db7093bd389aef67fb7a2d1a95f14dd669d18f4b6`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取 Jina Reader 本地安全能力目录，不访问上游且不需要密钥。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `read-url` | 通过 r.jina.ai 读取一个公开 HTTPS 网页或 PDF，返回 LLM 友好的正文。 | `url, max_tokens, no_cache` |

`read-url` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "url": {
      "type": "string",
      "minLength": 9,
      "maxLength": 2048,
      "pattern": "^https://"
    },
    "max_tokens": {
      "type": "integer",
      "minimum": 500,
      "maximum": 20000
    },
    "no_cache": {
      "type": "boolean"
    }
  },
  "required": [
    "url"
  ]
}
```

限制：

```json
{
  "requests_per_ticket": 1,
  "timeout_seconds_max": 120,
  "max_response_bytes": 5000000,
  "max_tokens": 20000
}
```

## Exa Search API (`exa`)

- 状态：`启用`
- 说明：使用 Exa 官方搜索与 Contents API 搜索公开网页并提取干净、适合大模型使用的内容。
- 目录策略：只暴露固定的 Exa /search 与 /contents 只读接口；禁止 Answer、Agent、Research、Websets、联系人富集、任意 URL 主机和任意请求头。
- 执行策略：EXA_API_KEY 仅在后端 x-api-key 头注入；每张票据只执行一次调用；搜索最多10条，Contents最多5个公开 HTTPS URL，不启用摘要或联系人富集。
- 票据前缀：`[api-web]`
- Secret环境变量名：`EXA_API_KEY`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`9ae67e37ccc9cb17e849551300f7c87b705415ff90d759e972cc9c5d3d4164ce`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取 Exa 本地安全能力目录，不访问上游且不需要密钥。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `search` | 调用 Exa /search 搜索公开网页，可返回结果元数据及受限的 highlights 或正文。 | `query, num_results, search_type, content_mode, max_characters` |

`search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 1000
    },
    "num_results": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10
    },
    "search_type": {
      "type": "string",
      "enum": [
        "auto",
        "fast",
        "instant"
      ]
    },
    "content_mode": {
      "type": "string",
      "enum": [
        "none",
        "highlights",
        "text"
      ]
    },
    "max_characters": {
      "type": "integer",
      "minimum": 500,
      "maximum": 20000
    }
  },
  "required": [
    "query"
  ]
}
```

| `contents` | 调用 Exa /contents 读取最多5个已知公开 HTTPS URL 的正文或 highlights。 | `urls, content_mode, highlight_query, max_characters, max_age_hours` |

`contents` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "urls": {
      "type": "array",
      "minItems": 1,
      "maxItems": 5,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "minLength": 9,
        "maxLength": 2048,
        "pattern": "^https://"
      }
    },
    "content_mode": {
      "type": "string",
      "enum": [
        "highlights",
        "text"
      ]
    },
    "highlight_query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 1000
    },
    "max_characters": {
      "type": "integer",
      "minimum": 500,
      "maximum": 20000
    },
    "max_age_hours": {
      "type": "integer",
      "minimum": 0,
      "maximum": 720
    }
  },
  "required": [
    "urls"
  ]
}
```

限制：

```json
{
  "requests_per_ticket": 1,
  "timeout_seconds_max": 120,
  "max_response_bytes": 5000000,
  "search_results_max": 10,
  "content_urls_max": 5
}
```

## Tavily Context API (`tavily`)

- 状态：`启用`
- 说明：使用 Tavily 官方 Search、Extract、Map 与 Crawl API 获取面向大模型的实时公开网页证据。
- 目录策略：只暴露 Tavily 固定只读端点；禁止 Research、异步研究任务、自动参数升级、任意请求头、任意代码和非公开 URL。
- 执行策略：TAVILY_API_KEY 仅在后端 Authorization Bearer 头注入；每张票据执行一次请求；Search 默认 basic 且关闭自动参数和生成式答案；Extract 最多5个 URL；Map 最多50个链接；Crawl 最多20页且深度最多2。
- 票据前缀：`[api-context]`
- Secret环境变量名：`TAVILY_API_KEY`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`c8e9b195cf48b60dd7657f55a575745b00cee16dda1b6fa52c76e10deb6365a0`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取 Tavily 本地安全能力目录，不访问上游且不需要密钥。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `search` | 调用 Tavily /search 搜索公开网页，固定关闭自动参数和生成式答案。 | `query, search_depth, topic, max_results, time_range, include_domains, exclude_domains, country, include_raw_content` |

`search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 1000
    },
    "search_depth": {
      "type": "string",
      "enum": [
        "basic",
        "fast",
        "ultra-fast",
        "advanced"
      ]
    },
    "topic": {
      "type": "string",
      "enum": [
        "general",
        "news",
        "finance"
      ]
    },
    "max_results": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10
    },
    "time_range": {
      "type": "string",
      "enum": [
        "day",
        "week",
        "month",
        "year"
      ]
    },
    "include_domains": {
      "type": "array",
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 253
      }
    },
    "exclude_domains": {
      "type": "array",
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 253
      }
    },
    "country": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64
    },
    "include_raw_content": {
      "type": "boolean"
    }
  },
  "required": [
    "query"
  ]
}
```

| `extract` | 调用 Tavily /extract 提取最多5个公开 HTTPS URL 的 Markdown 或纯文本。 | `urls, extract_depth, query, format, include_images` |

`extract` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "urls": {
      "type": "array",
      "minItems": 1,
      "maxItems": 5,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "minLength": 9,
        "maxLength": 2048,
        "pattern": "^https://"
      }
    },
    "extract_depth": {
      "type": "string",
      "enum": [
        "basic",
        "advanced"
      ]
    },
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 1000
    },
    "format": {
      "type": "string",
      "enum": [
        "markdown",
        "text"
      ]
    },
    "include_images": {
      "type": "boolean"
    }
  },
  "required": [
    "urls"
  ]
}
```

| `map` | 调用 Tavily /map 发现一个公开站点的受限 URL 结构，不允许外部域名。 | `url, instructions, max_depth, max_breadth, limit, select_paths, exclude_paths` |

`map` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "url": {
      "type": "string",
      "minLength": 9,
      "maxLength": 2048,
      "pattern": "^https://"
    },
    "instructions": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    },
    "max_depth": {
      "type": "integer",
      "minimum": 1,
      "maximum": 3
    },
    "max_breadth": {
      "type": "integer",
      "minimum": 1,
      "maximum": 20
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50
    },
    "select_paths": {
      "type": "array",
      "maxItems": 10,
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 200
      }
    },
    "exclude_paths": {
      "type": "array",
      "maxItems": 10,
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 200
      }
    }
  },
  "required": [
    "url"
  ]
}
```

| `crawl` | 调用 Tavily /crawl 对一个公开站点执行受限同步爬取，最多20页、深度最多2。 | `url, instructions, max_depth, max_breadth, limit, select_paths, exclude_paths, extract_depth, format` |

`crawl` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "url": {
      "type": "string",
      "minLength": 9,
      "maxLength": 2048,
      "pattern": "^https://"
    },
    "instructions": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    },
    "max_depth": {
      "type": "integer",
      "minimum": 1,
      "maximum": 2
    },
    "max_breadth": {
      "type": "integer",
      "minimum": 1,
      "maximum": 20
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 20
    },
    "select_paths": {
      "type": "array",
      "maxItems": 10,
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 200
      }
    },
    "exclude_paths": {
      "type": "array",
      "maxItems": 10,
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 200
      }
    },
    "extract_depth": {
      "type": "string",
      "enum": [
        "basic",
        "advanced"
      ]
    },
    "format": {
      "type": "string",
      "enum": [
        "markdown",
        "text"
      ]
    }
  },
  "required": [
    "url"
  ]
}
```

限制：

```json
{
  "requests_per_ticket": 1,
  "timeout_seconds_max": 150,
  "max_response_bytes": 5000000,
  "search_results_max": 10,
  "extract_urls_max": 5,
  "map_links_max": 50,
  "crawl_pages_max": 20,
  "crawl_depth_max": 2,
  "research_allowed": false,
  "auto_parameters_allowed": false
}
```

## Firecrawl Context API（火行者） (`firecrawl`)

- 状态：`启用`
- 说明：使用 Firecrawl v2 Search、Scrape 与 Map API 搜索公开网页、提取正文并发现站点 URL。
- 目录策略：只暴露 Firecrawl v2 固定只读 Search、Scrape、Map；禁止 Crawl 异步任务、Agent、Browser、Interact、Actions、任意请求头、Cookie、登录态和非公开 URL。
- 执行策略：FIRECRAWL_API_KEY 仅在后端 Authorization Bearer 头注入；每张票据执行一次请求；Search最多10条；Scrape仅允许Markdown和Links并启用零数据保留；Map最多100个链接且默认不含子域名。
- 票据前缀：`[api-context]`
- Secret环境变量名：`FIRECRAWL_API_KEY`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`a44c4d567f550e422b27f53ae4531d69e2096d249e590d953835c16fedc56375`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取 Firecrawl 本地安全能力目录，不访问上游且不需要密钥。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `search` | 调用 Firecrawl v2 /search 搜索公开网页，可选择返回受限 Markdown。 | `query, limit, country, time_range, include_markdown` |

`search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 1000
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10
    },
    "country": {
      "type": "string",
      "minLength": 2,
      "maxLength": 2,
      "pattern": "^[A-Za-z]{2}$"
    },
    "time_range": {
      "type": "string",
      "enum": [
        "day",
        "week",
        "month",
        "year"
      ]
    },
    "include_markdown": {
      "type": "boolean"
    }
  },
  "required": [
    "query"
  ]
}
```

| `scrape` | 调用 Firecrawl v2 /scrape 读取一个公开 HTTPS URL，仅返回 Markdown 和/或链接。 | `url, formats, only_main_content, max_age_ms, timeout_ms` |

`scrape` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "url": {
      "type": "string",
      "minLength": 9,
      "maxLength": 2048,
      "pattern": "^https://"
    },
    "formats": {
      "type": "array",
      "minItems": 1,
      "maxItems": 2,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "enum": [
          "markdown",
          "links"
        ]
      }
    },
    "only_main_content": {
      "type": "boolean"
    },
    "max_age_ms": {
      "type": "integer",
      "minimum": 0,
      "maximum": 604800000
    },
    "timeout_ms": {
      "type": "integer",
      "minimum": 1000,
      "maximum": 60000
    }
  },
  "required": [
    "url"
  ]
}
```

| `map` | 调用 Firecrawl v2 /map 获取一个公开站点的受限 URL 列表。 | `url, search, sitemap, include_subdomains, ignore_query_parameters, limit` |

`map` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "url": {
      "type": "string",
      "minLength": 9,
      "maxLength": 2048,
      "pattern": "^https://"
    },
    "search": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    },
    "sitemap": {
      "type": "string",
      "enum": [
        "skip",
        "include",
        "only"
      ]
    },
    "include_subdomains": {
      "type": "boolean"
    },
    "ignore_query_parameters": {
      "type": "boolean"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    }
  },
  "required": [
    "url"
  ]
}
```

限制：

```json
{
  "requests_per_ticket": 1,
  "timeout_seconds_max": 150,
  "max_response_bytes": 5000000,
  "search_results_max": 10,
  "scrape_urls_max": 1,
  "map_links_max": 100,
  "browser_interaction_allowed": false,
  "actions_allowed": false,
  "arbitrary_headers_allowed": false,
  "async_crawl_allowed": false
}
```

## Browserless REST API (`browserless`)

- 状态：`启用`
- 说明：通过 Browserless 托管无头浏览器读取 JavaScript 渲染网页、结构化抓取、生成截图和 PDF、执行 Lighthouse 审计，并提供受限的搜索与站点地图能力。
- 目录策略：仅允许固定 Browserless Cloud REST 主机和公开 HTTPS 目标；禁止任意 JavaScript、Function、Download、Export、BQL、BaaS、WebSocket、Profile、Cookie、Authorization、自定义请求头、代理、地理代理、Unblock、CAPTCHA 求解和登录态页面。
- 执行策略：BROWSERLESS_TOKEN 仅在后端固定查询参数中注入且不进入日志或 Artifact；每张票据只调用一个固定 REST 端点；目标 URL 必须通过公开 HTTPS 与 SSRF 防护；二进制结果只作为 Artifact 文件保存。
- 票据前缀：`[api-browserless]`
- Secret环境变量名：`BROWSERLESS_TOKEN`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`930432038bc74e69f64242ed145e7dafc372bfb114b6a2fed2c625a01ab1f7d1`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取 Browserless 本地安全能力目录，不访问上游且不需要密钥。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `content` | 调用 /content 返回一个公开 HTTPS 页面的完整 JavaScript 渲染 HTML。 | `url` |

`content` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "url": {
      "type": "string",
      "minLength": 9,
      "maxLength": 2048,
      "pattern": "^https://"
    }
  },
  "required": [
    "url"
  ]
}
```

| `scrape` | 调用 /scrape 在完整渲染后按最多20个 CSS 选择器提取结构化 JSON。 | `url, selectors` |

`scrape` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "url": {
      "type": "string",
      "minLength": 9,
      "maxLength": 2048,
      "pattern": "^https://"
    },
    "selectors": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 500
      }
    }
  },
  "required": [
    "url",
    "selectors"
  ]
}
```

| `screenshot` | 调用 /screenshot 为一个公开 HTTPS 页面生成 PNG、JPEG 或 WebP 截图 Artifact。 | `url, image_type, full_page, quality` |

`screenshot` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "url": {
      "type": "string",
      "minLength": 9,
      "maxLength": 2048,
      "pattern": "^https://"
    },
    "image_type": {
      "type": "string",
      "enum": [
        "png",
        "jpeg",
        "webp"
      ]
    },
    "full_page": {
      "type": "boolean"
    },
    "quality": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    }
  },
  "required": [
    "url"
  ]
}
```

| `pdf` | 调用 /pdf 为一个公开 HTTPS 页面生成受限 PDF Artifact。 | `url, format, landscape, print_background` |

`pdf` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "url": {
      "type": "string",
      "minLength": 9,
      "maxLength": 2048,
      "pattern": "^https://"
    },
    "format": {
      "type": "string",
      "enum": [
        "A4",
        "Letter",
        "Legal",
        "A3",
        "A5"
      ]
    },
    "landscape": {
      "type": "boolean"
    },
    "print_background": {
      "type": "boolean"
    }
  },
  "required": [
    "url"
  ]
}
```

| `performance` | 调用 /performance 对公开 HTTPS 页面执行受限 Lighthouse 分类审计。 | `url, categories` |

`performance` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "url": {
      "type": "string",
      "minLength": 9,
      "maxLength": 2048,
      "pattern": "^https://"
    },
    "categories": {
      "type": "array",
      "minItems": 1,
      "maxItems": 5,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "enum": [
          "accessibility",
          "best-practices",
          "performance",
          "pwa",
          "seo"
        ]
      }
    }
  },
  "required": [
    "url"
  ]
}
```

| `search` | 调用 Cloud /search 对公开网页执行受限 Web 搜索，最多3条结果且不自动抓取结果页。 | `query, limit` |

`search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 1000
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 3
    }
  },
  "required": [
    "query"
  ]
}
```

| `map` | 调用 Cloud /map 发现一个公开 HTTPS 站点的受限 URL 结构，最多100条。 | `url, search, limit, sitemap, include_subdomains, ignore_query_parameters` |

`map` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "url": {
      "type": "string",
      "minLength": 9,
      "maxLength": 2048,
      "pattern": "^https://"
    },
    "search": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    },
    "sitemap": {
      "type": "string",
      "enum": [
        "include",
        "skip",
        "only"
      ]
    },
    "include_subdomains": {
      "type": "boolean"
    },
    "ignore_query_parameters": {
      "type": "boolean"
    }
  },
  "required": [
    "url"
  ]
}
```

限制：

```json
{
  "requests_per_ticket": 1,
  "timeout_seconds_max": 120,
  "max_response_bytes": 10000000,
  "target_urls_max": 1,
  "selectors_max": 20,
  "search_results_max": 3,
  "map_links_max": 100,
  "fixed_api_host": "production-sfo.browserless.io",
  "arbitrary_api_hosts_allowed": false,
  "arbitrary_code_allowed": false,
  "websocket_sessions_allowed": false,
  "profiles_allowed": false,
  "custom_headers_allowed": false,
  "cookies_allowed": false,
  "proxy_configuration_allowed": false,
  "captcha_or_unblock_allowed": false,
  "write_operations_allowed": false
}
```

## TickFlow 金融行情 API (`tickflow`)

- 状态：`启用`
- 说明：读取 A 股、ETF、美股和港股的实时行情、历史 K 线、日内 K 线及标的元数据。
- 目录策略：只允许调用 TickFlow 官方固定只读 REST 端点；禁止 WebSocket、交易、账户、订单、任意 URL、任意请求头和任意代码。
- 执行策略：TICKFLOW_API_KEY 仅在后端 x-api-key 请求头注入；每张票据最多执行一次同步只读请求，并限制标的数量、K 线数量、超时和响应体积。
- 票据前缀：`[api-tickflow]`
- Secret环境变量名：`TICKFLOW_API_KEY`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`36b2bb448fe84eb74a83051deafaa1514f290d6d89c13588d3e6d3ba4c72c671`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取 TickFlow 本地安全能力目录，不访问上游且不需要密钥。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `quotes` | 读取一个或多个标的、或受支持标的池的实时行情快照。 | `symbols, universes` |

`quotes` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbols": {
      "type": "array",
      "minItems": 1,
      "maxItems": 100,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "minLength": 3,
        "maxLength": 32
      }
    },
    "universes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 5,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "enum": [
          "CN_Equity_A",
          "CN_ETF",
          "CN_Index",
          "US_Equity",
          "HK_Equity"
        ]
      }
    }
  },
  "anyOf": [
    {
      "required": [
        "symbols"
      ]
    },
    {
      "required": [
        "universes"
      ]
    }
  ]
}
```

| `klines` | 读取单个标的的历史 K 线，支持分钟、日、周、月、季和年周期及复权。 | `symbol, period, count, start_time, end_time, adjust` |

`klines` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "symbol"
  ],
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 3,
      "maxLength": 32
    },
    "period": {
      "type": "string",
      "enum": [
        "1m",
        "5m",
        "10m",
        "15m",
        "30m",
        "60m",
        "1d",
        "1w",
        "1M",
        "1Q",
        "1Y"
      ]
    },
    "count": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10000
    },
    "start_time": {
      "type": "integer",
      "minimum": 0
    },
    "end_time": {
      "type": "integer",
      "minimum": 0
    },
    "adjust": {
      "type": "string",
      "enum": [
        "forward",
        "backward",
        "forward_additive",
        "backward_additive",
        "none"
      ]
    }
  }
}
```

| `intraday-klines` | 读取单个标的的当日分钟 K 线。 | `symbol, period, count` |

`intraday-klines` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "symbol"
  ],
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 3,
      "maxLength": 32
    },
    "period": {
      "type": "string",
      "enum": [
        "1m",
        "5m",
        "10m",
        "15m",
        "30m",
        "60m"
      ]
    },
    "count": {
      "type": "integer",
      "minimum": 1,
      "maximum": 2000
    }
  }
}
```

| `instruments` | 读取最多 100 个标的的名称、交易所、地区、类型及上市信息等元数据。 | `symbols` |

`instruments` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "symbols"
  ],
  "properties": {
    "symbols": {
      "type": "array",
      "minItems": 1,
      "maxItems": 100,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "minLength": 3,
        "maxLength": 32
      }
    }
  }
}
```

限制：

```json
{
  "requests_per_ticket": 1,
  "timeout_seconds_max": 60,
  "max_response_bytes": 3000000,
  "symbols_max": 100,
  "kline_count_max": 10000,
  "write_or_trade_allowed": false,
  "websocket_allowed": false
}
```

## SerpAPI 搜索结果 API (`serpapi`)

- 状态：`启用`
- 说明：通过 SerpAPI 官方同步接口读取结构化 Google 网页、Google News 和 Google Scholar 搜索结果。
- 目录策略：只暴露固定的 Google、Google News 和 Google Scholar 同步 JSON 搜索；禁止异步任务、搜索归档、HTML 输出、任意引擎、任意端点和任意请求头。
- 执行策略：SERPAPI_API_KEY 仅在后端 api_key 查询参数注入且不会写入日志或 Artifact；每张票据执行一次同步搜索，固定 JSON 输出并限制分页、地区、语言和响应体积。
- 票据前缀：`[api-serpapi]`
- Secret环境变量名：`SERPAPI_API_KEY`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`76d40e7ea071c4d19a624b64430d831ca87801b8e750f5f3ee3839ada48c8e5d`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取 SerpAPI 本地安全能力目录，不访问上游且不需要密钥。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `google-search` | 执行同步 Google 网页搜索并返回结构化 JSON 结果。 | `query, location, gl, hl, start, device, safe, time_range` |

`google-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "query"
  ],
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 1000
    },
    "location": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "gl": {
      "type": "string",
      "pattern": "^[A-Za-z]{2}$"
    },
    "hl": {
      "type": "string",
      "pattern": "^[a-z]{2}(?:-[a-z]{2})?$",
      "minLength": 2,
      "maxLength": 5
    },
    "start": {
      "type": "integer",
      "minimum": 0,
      "maximum": 90,
      "multipleOf": 10
    },
    "device": {
      "type": "string",
      "enum": [
        "desktop",
        "tablet",
        "mobile"
      ]
    },
    "safe": {
      "type": "string",
      "enum": [
        "active",
        "off"
      ]
    },
    "time_range": {
      "type": "string",
      "enum": [
        "day",
        "week",
        "month",
        "year"
      ]
    }
  }
}
```

| `google-news` | 执行同步 Google News 搜索并返回结构化 JSON 结果。 | `query, gl, hl, sort_by_date, start, time_range` |

`google-news` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "query"
  ],
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 1000
    },
    "gl": {
      "type": "string",
      "pattern": "^[A-Za-z]{2}$"
    },
    "hl": {
      "type": "string",
      "pattern": "^[a-z]{2}(?:-[a-z]{2})?$",
      "minLength": 2,
      "maxLength": 5
    },
    "sort_by_date": {
      "type": "boolean"
    },
    "start": {
      "type": "integer",
      "minimum": 0,
      "maximum": 90,
      "multipleOf": 10
    },
    "time_range": {
      "type": "string",
      "enum": [
        "day",
        "week",
        "month",
        "year"
      ]
    }
  }
}
```

| `google-scholar` | 执行同步 Google Scholar 文献搜索并返回结构化 JSON 结果。 | `query, hl, start, year_low, year_high, sort_by_date` |

`google-scholar` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "query"
  ],
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 1000
    },
    "hl": {
      "type": "string",
      "pattern": "^[a-z]{2}(?:-[a-z]{2})?$",
      "minLength": 2,
      "maxLength": 5
    },
    "start": {
      "type": "integer",
      "minimum": 0,
      "maximum": 90,
      "multipleOf": 10
    },
    "year_low": {
      "type": "integer",
      "minimum": 1900,
      "maximum": 2100
    },
    "year_high": {
      "type": "integer",
      "minimum": 1900,
      "maximum": 2100
    },
    "sort_by_date": {
      "type": "boolean"
    }
  }
}
```

限制：

```json
{
  "requests_per_ticket": 1,
  "timeout_seconds_max": 60,
  "max_response_bytes": 3000000,
  "result_offset_max": 90,
  "async_allowed": false,
  "html_output_allowed": false,
  "arbitrary_engine_allowed": false
}
```

## Tushare Pro 中国金融数据 API (`tushare`)

- 状态：`启用`
- 说明：通过 Tushare Pro 官方 HTTPS JSON API 读取中国股票、指数、基金、财务、资金流和交易日历数据。实际可用范围由账户积分和接口权限决定。
- 目录策略：仅开放显式登记的 Tushare Pro 只读 api_name；禁止任意 API 名称、任意 URL、交易、下单、账户操作、写入和自定义请求头。
- 执行策略：TUSHARE_API_TOKEN 仅在后端 HTTPS POST JSON 中注入，不写入日志、Issue 或 Artifact；每张票据最多一次正常请求和一次瞬态故障重试，并限制参数、超时、响应体积和分页。
- 票据前缀：`[api-tushare]`
- Secret环境变量名：`TUSHARE_API_TOKEN`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`17b75ee3179f49be521afbdd4bb310f963983cc17161a6a806a5119f81a460eb`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地安全能力目录，不访问上游且不需要 Token。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `trade-calendar` | 读取各交易所交易日历。 | `exchange, start_date, end_date, is_open, fields` |

`trade-calendar` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "exchange": {
      "type": "string",
      "maxLength": 16
    },
    "start_date": {
      "$ref": "#/$defs/date"
    },
    "end_date": {
      "$ref": "#/$defs/date"
    },
    "is_open": {
      "type": "string",
      "enum": [
        "0",
        "1"
      ]
    },
    "fields": {
      "$ref": "#/$defs/fields"
    }
  },
  "$defs": {
    "date": {
      "type": "string",
      "pattern": "^[0-9]{8}$"
    },
    "fields": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_,]*$",
      "maxLength": 2000
    }
  }
}
```

| `stock-basic` | 读取 A 股证券基础信息和上市状态。 | `ts_code, name, market, exchange, list_status, is_hs, fields` |

`stock-basic` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "ts_code": {
      "$ref": "#/$defs/code"
    },
    "name": {
      "type": "string",
      "maxLength": 80
    },
    "market": {
      "type": "string",
      "maxLength": 40
    },
    "exchange": {
      "type": "string",
      "maxLength": 16
    },
    "list_status": {
      "type": "string",
      "enum": [
        "L",
        "D",
        "P"
      ]
    },
    "is_hs": {
      "type": "string",
      "enum": [
        "N",
        "H",
        "S"
      ]
    },
    "fields": {
      "$ref": "#/$defs/fields"
    }
  },
  "$defs": {
    "code": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]{1,32}$"
    },
    "fields": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_,]*$",
      "maxLength": 2000
    }
  }
}
```

| `daily-quotes` | 读取 A 股日线行情。 | `ts_code, trade_date, start_date, end_date, offset, limit, fields` |

`daily-quotes` 参数Schema：

```json
{
  "$ref": "#/$defs/marketQuery",
  "$defs": {
    "marketQuery": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "ts_code": {
          "$ref": "#/$defs/code"
        },
        "trade_date": {
          "$ref": "#/$defs/date"
        },
        "start_date": {
          "$ref": "#/$defs/date"
        },
        "end_date": {
          "$ref": "#/$defs/date"
        },
        "offset": {
          "type": "integer",
          "minimum": 0,
          "maximum": 1000000
        },
        "limit": {
          "type": "integer",
          "minimum": 1,
          "maximum": 5000
        },
        "fields": {
          "$ref": "#/$defs/fields"
        }
      }
    },
    "date": {
      "type": "string",
      "pattern": "^[0-9]{8}$"
    },
    "code": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]{1,32}$"
    },
    "fields": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_,]*$",
      "maxLength": 2000
    }
  }
}
```

| `weekly-quotes` | 读取 A 股周线行情。 | `ts_code, trade_date, start_date, end_date, offset, limit, fields` |

`weekly-quotes` 参数Schema：

```json
{
  "$ref": "#/$defs/marketQuery",
  "$defs": {
    "marketQuery": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "ts_code": {
          "$ref": "#/$defs/code"
        },
        "trade_date": {
          "$ref": "#/$defs/date"
        },
        "start_date": {
          "$ref": "#/$defs/date"
        },
        "end_date": {
          "$ref": "#/$defs/date"
        },
        "offset": {
          "type": "integer",
          "minimum": 0,
          "maximum": 1000000
        },
        "limit": {
          "type": "integer",
          "minimum": 1,
          "maximum": 5000
        },
        "fields": {
          "$ref": "#/$defs/fields"
        }
      }
    },
    "date": {
      "type": "string",
      "pattern": "^[0-9]{8}$"
    },
    "code": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]{1,32}$"
    },
    "fields": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_,]*$",
      "maxLength": 2000
    }
  }
}
```

| `monthly-quotes` | 读取 A 股月线行情。 | `ts_code, trade_date, start_date, end_date, offset, limit, fields` |

`monthly-quotes` 参数Schema：

```json
{
  "$ref": "#/$defs/marketQuery",
  "$defs": {
    "marketQuery": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "ts_code": {
          "$ref": "#/$defs/code"
        },
        "trade_date": {
          "$ref": "#/$defs/date"
        },
        "start_date": {
          "$ref": "#/$defs/date"
        },
        "end_date": {
          "$ref": "#/$defs/date"
        },
        "offset": {
          "type": "integer",
          "minimum": 0,
          "maximum": 1000000
        },
        "limit": {
          "type": "integer",
          "minimum": 1,
          "maximum": 5000
        },
        "fields": {
          "$ref": "#/$defs/fields"
        }
      }
    },
    "date": {
      "type": "string",
      "pattern": "^[0-9]{8}$"
    },
    "code": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]{1,32}$"
    },
    "fields": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_,]*$",
      "maxLength": 2000
    }
  }
}
```

| `adjust-factor` | 读取 A 股复权因子。 | `ts_code, trade_date, start_date, end_date, offset, limit, fields` |

`adjust-factor` 参数Schema：

```json
{
  "$ref": "#/$defs/marketQuery",
  "$defs": {
    "marketQuery": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "ts_code": {
          "$ref": "#/$defs/code"
        },
        "trade_date": {
          "$ref": "#/$defs/date"
        },
        "start_date": {
          "$ref": "#/$defs/date"
        },
        "end_date": {
          "$ref": "#/$defs/date"
        },
        "offset": {
          "type": "integer",
          "minimum": 0,
          "maximum": 1000000
        },
        "limit": {
          "type": "integer",
          "minimum": 1,
          "maximum": 5000
        },
        "fields": {
          "$ref": "#/$defs/fields"
        }
      }
    },
    "date": {
      "type": "string",
      "pattern": "^[0-9]{8}$"
    },
    "code": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]{1,32}$"
    },
    "fields": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_,]*$",
      "maxLength": 2000
    }
  }
}
```

| `daily-basic` | 读取每日估值、市值、换手率和股本指标。 | `ts_code, trade_date, start_date, end_date, offset, limit, fields` |

`daily-basic` 参数Schema：

```json
{
  "$ref": "#/$defs/marketQuery",
  "$defs": {
    "marketQuery": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "ts_code": {
          "$ref": "#/$defs/code"
        },
        "trade_date": {
          "$ref": "#/$defs/date"
        },
        "start_date": {
          "$ref": "#/$defs/date"
        },
        "end_date": {
          "$ref": "#/$defs/date"
        },
        "offset": {
          "type": "integer",
          "minimum": 0,
          "maximum": 1000000
        },
        "limit": {
          "type": "integer",
          "minimum": 1,
          "maximum": 5000
        },
        "fields": {
          "$ref": "#/$defs/fields"
        }
      }
    },
    "date": {
      "type": "string",
      "pattern": "^[0-9]{8}$"
    },
    "code": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]{1,32}$"
    },
    "fields": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_,]*$",
      "maxLength": 2000
    }
  }
}
```

| `money-flow` | 读取个股资金流向。 | `ts_code, trade_date, start_date, end_date, offset, limit, fields` |

`money-flow` 参数Schema：

```json
{
  "$ref": "#/$defs/marketQuery",
  "$defs": {
    "marketQuery": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "ts_code": {
          "$ref": "#/$defs/code"
        },
        "trade_date": {
          "$ref": "#/$defs/date"
        },
        "start_date": {
          "$ref": "#/$defs/date"
        },
        "end_date": {
          "$ref": "#/$defs/date"
        },
        "offset": {
          "type": "integer",
          "minimum": 0,
          "maximum": 1000000
        },
        "limit": {
          "type": "integer",
          "minimum": 1,
          "maximum": 5000
        },
        "fields": {
          "$ref": "#/$defs/fields"
        }
      }
    },
    "date": {
      "type": "string",
      "pattern": "^[0-9]{8}$"
    },
    "code": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]{1,32}$"
    },
    "fields": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_,]*$",
      "maxLength": 2000
    }
  }
}
```

| `margin-summary` | 读取融资融券交易汇总。 | `trade_date, exchange_id, start_date, end_date, fields` |

`margin-summary` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "trade_date": {
      "$ref": "#/$defs/date"
    },
    "exchange_id": {
      "type": "string",
      "maxLength": 16
    },
    "start_date": {
      "$ref": "#/$defs/date"
    },
    "end_date": {
      "$ref": "#/$defs/date"
    },
    "fields": {
      "$ref": "#/$defs/fields"
    }
  },
  "$defs": {
    "date": {
      "type": "string",
      "pattern": "^[0-9]{8}$"
    },
    "fields": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_,]*$",
      "maxLength": 2000
    }
  }
}
```

| `top-list` | 读取龙虎榜每日明细。 | `trade_date, ts_code, fields` |

`top-list` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "trade_date": {
      "$ref": "#/$defs/date"
    },
    "ts_code": {
      "$ref": "#/$defs/code"
    },
    "fields": {
      "$ref": "#/$defs/fields"
    }
  },
  "$defs": {
    "date": {
      "type": "string",
      "pattern": "^[0-9]{8}$"
    },
    "code": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]{1,32}$"
    },
    "fields": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_,]*$",
      "maxLength": 2000
    }
  }
}
```

| `income-statement` | 读取上市公司利润表。 | `ts_code, ann_date, start_date, end_date, period, report_type, comp_type, offset, limit, fields` |

`income-statement` 参数Schema：

```json
{
  "$ref": "#/$defs/financeQuery",
  "$defs": {
    "financeQuery": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "ts_code": {
          "$ref": "#/$defs/code"
        },
        "ann_date": {
          "$ref": "#/$defs/date"
        },
        "start_date": {
          "$ref": "#/$defs/date"
        },
        "end_date": {
          "$ref": "#/$defs/date"
        },
        "period": {
          "$ref": "#/$defs/date"
        },
        "report_type": {
          "type": "string",
          "maxLength": 8
        },
        "comp_type": {
          "type": "string",
          "maxLength": 8
        },
        "offset": {
          "type": "integer",
          "minimum": 0,
          "maximum": 1000000
        },
        "limit": {
          "type": "integer",
          "minimum": 1,
          "maximum": 5000
        },
        "fields": {
          "$ref": "#/$defs/fields"
        }
      }
    },
    "date": {
      "type": "string",
      "pattern": "^[0-9]{8}$"
    },
    "code": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]{1,32}$"
    },
    "fields": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_,]*$",
      "maxLength": 2000
    }
  }
}
```

| `balance-sheet` | 读取上市公司资产负债表。 | `ts_code, ann_date, start_date, end_date, period, report_type, comp_type, offset, limit, fields` |

`balance-sheet` 参数Schema：

```json
{
  "$ref": "#/$defs/financeQuery",
  "$defs": {
    "financeQuery": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "ts_code": {
          "$ref": "#/$defs/code"
        },
        "ann_date": {
          "$ref": "#/$defs/date"
        },
        "start_date": {
          "$ref": "#/$defs/date"
        },
        "end_date": {
          "$ref": "#/$defs/date"
        },
        "period": {
          "$ref": "#/$defs/date"
        },
        "report_type": {
          "type": "string",
          "maxLength": 8
        },
        "comp_type": {
          "type": "string",
          "maxLength": 8
        },
        "offset": {
          "type": "integer",
          "minimum": 0,
          "maximum": 1000000
        },
        "limit": {
          "type": "integer",
          "minimum": 1,
          "maximum": 5000
        },
        "fields": {
          "$ref": "#/$defs/fields"
        }
      }
    },
    "date": {
      "type": "string",
      "pattern": "^[0-9]{8}$"
    },
    "code": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]{1,32}$"
    },
    "fields": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_,]*$",
      "maxLength": 2000
    }
  }
}
```

| `cash-flow-statement` | 读取上市公司现金流量表。 | `ts_code, ann_date, start_date, end_date, period, report_type, comp_type, offset, limit, fields` |

`cash-flow-statement` 参数Schema：

```json
{
  "$ref": "#/$defs/financeQuery",
  "$defs": {
    "financeQuery": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "ts_code": {
          "$ref": "#/$defs/code"
        },
        "ann_date": {
          "$ref": "#/$defs/date"
        },
        "start_date": {
          "$ref": "#/$defs/date"
        },
        "end_date": {
          "$ref": "#/$defs/date"
        },
        "period": {
          "$ref": "#/$defs/date"
        },
        "report_type": {
          "type": "string",
          "maxLength": 8
        },
        "comp_type": {
          "type": "string",
          "maxLength": 8
        },
        "offset": {
          "type": "integer",
          "minimum": 0,
          "maximum": 1000000
        },
        "limit": {
          "type": "integer",
          "minimum": 1,
          "maximum": 5000
        },
        "fields": {
          "$ref": "#/$defs/fields"
        }
      }
    },
    "date": {
      "type": "string",
      "pattern": "^[0-9]{8}$"
    },
    "code": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]{1,32}$"
    },
    "fields": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_,]*$",
      "maxLength": 2000
    }
  }
}
```

| `financial-indicator` | 读取上市公司财务指标。 | `ts_code, ann_date, start_date, end_date, period, offset, limit, fields` |

`financial-indicator` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "ts_code": {
      "$ref": "#/$defs/code"
    },
    "ann_date": {
      "$ref": "#/$defs/date"
    },
    "start_date": {
      "$ref": "#/$defs/date"
    },
    "end_date": {
      "$ref": "#/$defs/date"
    },
    "period": {
      "$ref": "#/$defs/date"
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 1000000
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 5000
    },
    "fields": {
      "$ref": "#/$defs/fields"
    }
  },
  "$defs": {
    "date": {
      "type": "string",
      "pattern": "^[0-9]{8}$"
    },
    "code": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]{1,32}$"
    },
    "fields": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_,]*$",
      "maxLength": 2000
    }
  }
}
```

| `index-basic` | 读取指数基础信息。 | `ts_code, name, market, publisher, category, fields` |

`index-basic` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "ts_code": {
      "$ref": "#/$defs/code"
    },
    "name": {
      "type": "string",
      "maxLength": 80
    },
    "market": {
      "type": "string",
      "maxLength": 32
    },
    "publisher": {
      "type": "string",
      "maxLength": 80
    },
    "category": {
      "type": "string",
      "maxLength": 40
    },
    "fields": {
      "$ref": "#/$defs/fields"
    }
  },
  "$defs": {
    "code": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]{1,32}$"
    },
    "fields": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_,]*$",
      "maxLength": 2000
    }
  }
}
```

| `index-daily` | 读取指数日线行情。 | `ts_code, trade_date, start_date, end_date, offset, limit, fields` |

`index-daily` 参数Schema：

```json
{
  "$ref": "#/$defs/marketQuery",
  "$defs": {
    "marketQuery": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "ts_code": {
          "$ref": "#/$defs/code"
        },
        "trade_date": {
          "$ref": "#/$defs/date"
        },
        "start_date": {
          "$ref": "#/$defs/date"
        },
        "end_date": {
          "$ref": "#/$defs/date"
        },
        "offset": {
          "type": "integer",
          "minimum": 0,
          "maximum": 1000000
        },
        "limit": {
          "type": "integer",
          "minimum": 1,
          "maximum": 5000
        },
        "fields": {
          "$ref": "#/$defs/fields"
        }
      }
    },
    "date": {
      "type": "string",
      "pattern": "^[0-9]{8}$"
    },
    "code": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]{1,32}$"
    },
    "fields": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_,]*$",
      "maxLength": 2000
    }
  }
}
```

| `fund-basic` | 读取公募基金基础信息。 | `market, status, fields` |

`fund-basic` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "market": {
      "type": "string",
      "maxLength": 16
    },
    "status": {
      "type": "string",
      "maxLength": 16
    },
    "fields": {
      "$ref": "#/$defs/fields"
    }
  },
  "$defs": {
    "fields": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_,]*$",
      "maxLength": 2000
    }
  }
}
```

| `fund-nav` | 读取公募基金净值。 | `ts_code, ann_date, nav_date, market, start_date, end_date, offset, limit, fields` |

`fund-nav` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "ts_code": {
      "$ref": "#/$defs/code"
    },
    "ann_date": {
      "$ref": "#/$defs/date"
    },
    "nav_date": {
      "$ref": "#/$defs/date"
    },
    "market": {
      "type": "string",
      "maxLength": 16
    },
    "start_date": {
      "$ref": "#/$defs/date"
    },
    "end_date": {
      "$ref": "#/$defs/date"
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 1000000
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 5000
    },
    "fields": {
      "$ref": "#/$defs/fields"
    }
  },
  "$defs": {
    "date": {
      "type": "string",
      "pattern": "^[0-9]{8}$"
    },
    "code": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]{1,32}$"
    },
    "fields": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_,]*$",
      "maxLength": 2000
    }
  }
}
```

| `hk-hold` | 读取沪深港通持股明细。 | `trade_date, ts_code, exchange, start_date, end_date, offset, limit, fields` |

`hk-hold` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "trade_date": {
      "$ref": "#/$defs/date"
    },
    "ts_code": {
      "$ref": "#/$defs/code"
    },
    "exchange": {
      "type": "string",
      "maxLength": 16
    },
    "start_date": {
      "$ref": "#/$defs/date"
    },
    "end_date": {
      "$ref": "#/$defs/date"
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 1000000
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 5000
    },
    "fields": {
      "$ref": "#/$defs/fields"
    }
  },
  "$defs": {
    "date": {
      "type": "string",
      "pattern": "^[0-9]{8}$"
    },
    "code": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]{1,32}$"
    },
    "fields": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_,]*$",
      "maxLength": 2000
    }
  }
}
```

限制：

```json
{
  "requests_per_ticket_max": 2,
  "timeout_seconds_max": 60,
  "max_response_bytes": 5000000,
  "limit_max": 5000,
  "offset_max": 1000000,
  "arbitrary_api_names_allowed": false,
  "arbitrary_urls_allowed": false,
  "arbitrary_headers_allowed": false,
  "write_operations_allowed": false,
  "trading_or_order_execution_allowed": false,
  "secret_values_exposed": false
}
```

## BaoStock 中国证券免费数据 (`baostock`)

- 状态：`启用`
- 说明：通过官方 baostock Python 客户端读取中国证券历史行情、交易日历、证券基础、指数成分、财务能力指标、业绩报告和宏观利率数据。无需 API Key。
- 目录策略：仅开放显式登记的 BaoStock 查询函数；禁止任意函数、任意网络地址、交易、下单、账户操作、写入和自定义代码。
- 执行策略：每张票据只允许一次登录、一次白名单查询和一次登出；所有生产票据使用仓库级全局串行并发组，禁止并发连接。每个上海自然日最多预占 50000 次上游查询，第 50000 次后立即激活当天本地黑名单；配额台账异常时失败关闭，禁止访问 BaoStock。
- 票据前缀：`[api-baostock]`
- Secret环境变量名：`无`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`396936b20d6f23f465158560441182ffcc47c2ab361877581e706dc8a439eb72`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地 BaoStock 安全能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `trade-dates` | 读取指定日期范围内的交易日历。 | `start_date, end_date` |

`trade-dates` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "start_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "end_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  },
  "required": [
    "start_date",
    "end_date"
  ]
}
```

| `all-stocks` | 读取指定交易日全部证券代码和交易状态。 | `day` |

`all-stocks` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "day": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  },
  "required": [
    "day"
  ]
}
```

| `stock-basic` | 按证券代码或名称读取证券基础资料。 | `code, code_name` |

`stock-basic` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "code": {
      "type": "string",
      "pattern": "^(sh|sz|bj)\\.[0-9]{6}$"
    },
    "code_name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 80
    },
    "max_rows": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10000
    }
  }
}
```

| `history-k` | 读取沪深京证券日/周/月或 5/15/30/60 分钟历史 K 线及估值字段。 | `code, fields, start_date, end_date, frequency, adjustflag` |

`history-k` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "code": {
      "type": "string",
      "pattern": "^(sh|sz|bj)\\.[0-9]{6}$"
    },
    "fields": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_,]+$",
      "maxLength": 1000
    },
    "start_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "end_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "frequency": {
      "type": "string",
      "enum": [
        "d",
        "w",
        "m",
        "5",
        "15",
        "30",
        "60"
      ]
    },
    "adjustflag": {
      "type": "string",
      "enum": [
        "1",
        "2",
        "3"
      ]
    }
  },
  "required": [
    "code",
    "fields",
    "start_date",
    "end_date"
  ]
}
```

| `adjust-factor` | 读取证券除权除息与复权因子。 | `code, start_date, end_date` |

`adjust-factor` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "code": {
      "type": "string",
      "pattern": "^(sh|sz|bj)\\.[0-9]{6}$"
    },
    "start_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "end_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  },
  "required": [
    "code",
    "start_date",
    "end_date"
  ]
}
```

| `stock-industry` | 读取证券行业分类。 | `code, date` |

`stock-industry` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "code": {
      "type": "string",
      "pattern": "^(sh|sz|bj)\\.[0-9]{6}$"
    },
    "date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  }
}
```

| `sz50-constituents` | 读取上证 50 成分股。 | `date` |

`sz50-constituents` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  }
}
```

| `hs300-constituents` | 读取沪深 300 成分股。 | `date` |

`hs300-constituents` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  }
}
```

| `zz500-constituents` | 读取中证 500 成分股。 | `date` |

`zz500-constituents` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  }
}
```

| `profit-data` | 读取季度盈利能力数据。 | `code, year, quarter` |

`profit-data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "code": {
      "type": "string",
      "pattern": "^(sh|sz|bj)\\.[0-9]{6}$"
    },
    "year": {
      "type": "integer",
      "minimum": 1990,
      "maximum": 2100
    },
    "quarter": {
      "type": "integer",
      "minimum": 1,
      "maximum": 4
    }
  },
  "required": [
    "code",
    "year",
    "quarter"
  ]
}
```

| `operation-data` | 读取季度营运能力数据。 | `code, year, quarter` |

`operation-data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "code": {
      "type": "string",
      "pattern": "^(sh|sz|bj)\\.[0-9]{6}$"
    },
    "year": {
      "type": "integer",
      "minimum": 1990,
      "maximum": 2100
    },
    "quarter": {
      "type": "integer",
      "minimum": 1,
      "maximum": 4
    }
  },
  "required": [
    "code",
    "year",
    "quarter"
  ]
}
```

| `growth-data` | 读取季度成长能力数据。 | `code, year, quarter` |

`growth-data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "code": {
      "type": "string",
      "pattern": "^(sh|sz|bj)\\.[0-9]{6}$"
    },
    "year": {
      "type": "integer",
      "minimum": 1990,
      "maximum": 2100
    },
    "quarter": {
      "type": "integer",
      "minimum": 1,
      "maximum": 4
    }
  },
  "required": [
    "code",
    "year",
    "quarter"
  ]
}
```

| `balance-data` | 读取季度偿债能力数据。 | `code, year, quarter` |

`balance-data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "code": {
      "type": "string",
      "pattern": "^(sh|sz|bj)\\.[0-9]{6}$"
    },
    "year": {
      "type": "integer",
      "minimum": 1990,
      "maximum": 2100
    },
    "quarter": {
      "type": "integer",
      "minimum": 1,
      "maximum": 4
    }
  },
  "required": [
    "code",
    "year",
    "quarter"
  ]
}
```

| `cash-flow-data` | 读取季度现金流量数据。 | `code, year, quarter` |

`cash-flow-data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "code": {
      "type": "string",
      "pattern": "^(sh|sz|bj)\\.[0-9]{6}$"
    },
    "year": {
      "type": "integer",
      "minimum": 1990,
      "maximum": 2100
    },
    "quarter": {
      "type": "integer",
      "minimum": 1,
      "maximum": 4
    }
  },
  "required": [
    "code",
    "year",
    "quarter"
  ]
}
```

| `dupont-data` | 读取季度杜邦分析数据。 | `code, year, quarter` |

`dupont-data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "code": {
      "type": "string",
      "pattern": "^(sh|sz|bj)\\.[0-9]{6}$"
    },
    "year": {
      "type": "integer",
      "minimum": 1990,
      "maximum": 2100
    },
    "quarter": {
      "type": "integer",
      "minimum": 1,
      "maximum": 4
    }
  },
  "required": [
    "code",
    "year",
    "quarter"
  ]
}
```

| `performance-express` | 读取业绩快报。 | `code, start_date, end_date` |

`performance-express` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "code": {
      "type": "string",
      "pattern": "^(sh|sz|bj)\\.[0-9]{6}$"
    },
    "start_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "end_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  },
  "required": [
    "start_date",
    "end_date"
  ]
}
```

| `forecast-report` | 读取业绩预告。 | `code, start_date, end_date` |

`forecast-report` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "code": {
      "type": "string",
      "pattern": "^(sh|sz|bj)\\.[0-9]{6}$"
    },
    "start_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "end_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  },
  "required": [
    "start_date",
    "end_date"
  ]
}
```

| `deposit-rate` | 读取中国存款基准利率。 | `start_date, end_date` |

`deposit-rate` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "start_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "end_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  },
  "required": [
    "start_date",
    "end_date"
  ]
}
```

| `shibor` | 读取上海银行间同业拆放利率。 | `start_date, end_date` |

`shibor` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "start_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "end_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  },
  "required": [
    "start_date",
    "end_date"
  ]
}
```

限制：

```json
{
  "queries_per_ticket_max": 1,
  "timeout_seconds_max": 60,
  "max_response_bytes": 5000000,
  "max_rows": 10000,
  "arbitrary_functions_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_code_allowed": false,
  "write_operations_allowed": false,
  "trading_or_order_execution_allowed": false,
  "credentials_required": false,
  "secret_values_exposed": false,
  "daily_request_limit": 50000,
  "daily_quota_timezone": "Asia/Shanghai",
  "max_parallel_connections": 1,
  "global_serial_connection_required": true,
  "concurrency_group": "api-baostock-global-single-connection",
  "local_blacklist_at_daily_limit": true,
  "quota_ledger_fail_closed": true,
  "quota_ledger_issue_number": 297,
  "catalog_operations_consume_quota": false
}
```

## EODHD 全球金融市场数据 (`eodhd`)

- 状态：`启用`
- 说明：通过 EODHD 官方 HTTPS REST API 读取全球交易所、证券目录、历史和实时行情、基本面、公司行动、技术指标、新闻情绪、筛选器、企业日历、宏观事件及交易时段。
- 目录策略：仅开放显式登记的固定 GET 路径和参数 Schema；禁止任意 URL、任意路径、任意请求头、用户自定义 api_token、WebSocket、交易、下单、账户修改和数据写入。
- 执行策略：EODHD_API_TOKEN 仅在后端查询参数中注入且不会进入日志、Issue 或 Artifact；每张票据最多一次正常请求和一次瞬态故障重试，并限制超时、响应体积、结果行数和筛选器结构。
- 票据前缀：`[api-eodhd]`
- Secret环境变量名：`EODHD_API_TOKEN`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`124c5e16ef567d8df1bbbfd7b261ac7b6a23f70cc73799ab2c27c73d3fc5ed58`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地 EODHD 安全能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `exchanges-list` | 读取 EODHD 支持的全球交易所、虚拟市场和基础元数据。 | `无` |

`exchanges-list` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `exchange-symbols` | 读取指定交易所当前或退市证券目录。 | `exchange, delisted, type` |

`exchange-symbols` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "exchange": {
      "type": "string",
      "maxLength": 32,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9 _.-]{0,31}$"
    },
    "delisted": {
      "type": "boolean"
    },
    "type": {
      "type": "string",
      "maxLength": 32,
      "enum": [
        "common_stock",
        "preferred_stock",
        "stock",
        "etf",
        "fund"
      ]
    }
  },
  "required": [
    "exchange"
  ]
}
```

| `symbol-search` | 按代码或名称搜索全球证券、基金、指数、外汇、债券和数字资产。 | `query, exchange, limit, bonds_only` |

`symbol-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "maxLength": 120,
      "pattern": "^[^/?#\\\\]{1,120}$"
    },
    "exchange": {
      "type": "string",
      "maxLength": 32,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9 _.-]{0,31}$"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    },
    "bonds_only": {
      "type": "boolean"
    }
  },
  "required": [
    "query"
  ]
}
```

| `eod-history` | 读取单一证券的日、周或月末历史 OHLCV 与复权价格。 | `symbol, from_date, to_date, period, order` |

`eod-history` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    },
    "from_date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "to_date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "period": {
      "type": "string",
      "maxLength": 1,
      "enum": [
        "d",
        "w",
        "m"
      ]
    },
    "order": {
      "type": "string",
      "maxLength": 1,
      "enum": [
        "a",
        "d"
      ]
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `intraday-history` | 读取单一证券的分钟或小时级历史行情。 | `symbol, interval, from_timestamp, to_timestamp` |

`intraday-history` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    },
    "interval": {
      "type": "string",
      "maxLength": 2,
      "enum": [
        "1m",
        "5m",
        "1h"
      ]
    },
    "from_timestamp": {
      "type": "integer",
      "minimum": 0,
      "maximum": 4102444800
    },
    "to_timestamp": {
      "type": "integer",
      "minimum": 0,
      "maximum": 4102444800
    }
  },
  "required": [
    "symbol",
    "interval"
  ]
}
```

| `real-time-quote` | 读取单一证券的实时或延迟报价快照；数据权限由 EODHD 套餐决定。 | `symbol` |

`real-time-quote` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `fundamentals` | 读取股票、ETF、基金或指数的结构化基本面数据。 | `symbol, filter` |

`fundamentals` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    },
    "filter": {
      "type": "string",
      "maxLength": 300,
      "pattern": "^[A-Za-z0-9._,-]+$"
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `dividends-history` | 读取单一证券的历史分红记录。 | `symbol, from_date, to_date` |

`dividends-history` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    },
    "from_date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "to_date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `splits-history` | 读取单一证券的历史拆股和合股记录。 | `symbol, from_date, to_date` |

`splits-history` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    },
    "from_date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "to_date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `bulk-eod` | 按交易所和日期读取整市场 EOD、拆股或分红批量数据。 | `exchange, date, type, symbols` |

`bulk-eod` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "exchange": {
      "type": "string",
      "maxLength": 32,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9 _.-]{0,31}$"
    },
    "date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "type": {
      "type": "string",
      "maxLength": 16,
      "enum": [
        "eod",
        "splits",
        "dividends"
      ]
    },
    "symbols": {
      "type": "string",
      "maxLength": 1000,
      "pattern": "^[A-Za-z0-9._,:-]+$"
    }
  },
  "required": [
    "exchange"
  ]
}
```

| `historical-market-cap` | 读取美国股票或数字资产的历史市值序列。 | `symbol, from_date, to_date` |

`historical-market-cap` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    },
    "from_date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "to_date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `technical-indicator` | 在固定证券和日期范围上计算 EODHD 技术指标。 | `symbol, function, period, from_date, to_date, order, splitadjusted` |

`technical-indicator` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    },
    "function": {
      "type": "string",
      "maxLength": 24,
      "enum": [
        "sma",
        "ema",
        "wma",
        "volatility",
        "rsi",
        "stddev",
        "stoch",
        "stochrsi",
        "slope",
        "dmi",
        "adx",
        "macd",
        "atr",
        "cci",
        "sar",
        "beta",
        "bbands"
      ]
    },
    "period": {
      "type": "integer",
      "minimum": 2,
      "maximum": 1000
    },
    "from_date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "to_date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "order": {
      "type": "string",
      "maxLength": 1,
      "enum": [
        "a",
        "d"
      ]
    },
    "splitadjusted": {
      "type": "boolean"
    }
  },
  "required": [
    "symbol",
    "function"
  ]
}
```

| `financial-news` | 读取按证券或主题过滤的金融新闻。 | `symbols, tag, from_date, to_date, limit, offset` |

`financial-news` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbols": {
      "type": "string",
      "maxLength": 1000,
      "pattern": "^[A-Za-z0-9._,:-]+$"
    },
    "tag": {
      "type": "string",
      "maxLength": 120,
      "pattern": "^[^/?#\\\\]{1,120}$"
    },
    "from_date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "to_date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000
    }
  }
}
```

| `sentiments` | 读取一个或多个证券的每日新闻情绪分数。 | `symbols, from_date, to_date` |

`sentiments` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbols": {
      "type": "string",
      "maxLength": 1000,
      "pattern": "^[A-Za-z0-9._,:-]+$"
    },
    "from_date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "to_date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  },
  "required": [
    "symbols"
  ]
}
```

| `screener` | 使用受控字段和比较运算筛选全球股票。 | `filters_json, sort, signals, limit, offset` |

`screener` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "filters_json": {
      "type": "string",
      "maxLength": 4000
    },
    "sort": {
      "type": "string",
      "maxLength": 80,
      "pattern": "^[A-Za-z0-9_]+\\.(asc|desc)$"
    },
    "signals": {
      "type": "string",
      "maxLength": 500,
      "pattern": "^[A-Za-z0-9_,.-]+$"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000
    }
  }
}
```

| `calendar-earnings` | 读取历史和未来财报发布日期。 | `symbols, from_date, to_date` |

`calendar-earnings` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbols": {
      "type": "string",
      "maxLength": 1000,
      "pattern": "^[A-Za-z0-9._,:-]+$"
    },
    "from_date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "to_date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  }
}
```

| `calendar-trends` | 读取证券盈利预期趋势。 | `symbols, from_date, to_date` |

`calendar-trends` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbols": {
      "type": "string",
      "maxLength": 1000,
      "pattern": "^[A-Za-z0-9._,:-]+$"
    },
    "from_date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "to_date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  }
}
```

| `calendar-ipos` | 读取历史和未来 IPO 日历。 | `symbols, from_date, to_date` |

`calendar-ipos` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbols": {
      "type": "string",
      "maxLength": 1000,
      "pattern": "^[A-Za-z0-9._,:-]+$"
    },
    "from_date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "to_date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  }
}
```

| `calendar-splits` | 读取历史和未来拆股日历。 | `symbols, from_date, to_date` |

`calendar-splits` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbols": {
      "type": "string",
      "maxLength": 1000,
      "pattern": "^[A-Za-z0-9._,:-]+$"
    },
    "from_date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "to_date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  }
}
```

| `calendar-dividends` | 读取历史和未来分红日历并支持分页。 | `symbol, from_date, to_date, limit, offset` |

`calendar-dividends` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    },
    "from_date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "to_date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000
    }
  }
}
```

| `macro-indicator` | 读取指定国家和宏观指标的历史序列。 | `country, indicator` |

`macro-indicator` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "country": {
      "type": "string",
      "maxLength": 80,
      "pattern": "^[A-Za-z][A-Za-z ._-]{1,79}$"
    },
    "indicator": {
      "type": "string",
      "maxLength": 80,
      "pattern": "^[A-Za-z0-9_ -]{1,80}$"
    }
  },
  "required": [
    "country",
    "indicator"
  ]
}
```

| `economic-events` | 读取受控日期、国家和事件范围内的宏观经济事件。 | `from_date, to_date, country, comparison, limit, offset` |

`economic-events` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "from_date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "to_date": {
      "type": "string",
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "country": {
      "type": "string",
      "maxLength": 80,
      "pattern": "^[A-Za-z][A-Za-z ,._-]{1,79}$"
    },
    "comparison": {
      "type": "string",
      "maxLength": 16,
      "enum": [
        "mom",
        "qoq",
        "yoy"
      ]
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000
    }
  }
}
```

| `exchange-details-list` | 读取 EODHD v2 交易所详情目录。 | `无` |

`exchange-details-list` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `exchange-details` | 读取指定交易所时区、交易时段、节假日和提前收市信息。 | `exchange` |

`exchange-details` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "exchange": {
      "type": "string",
      "maxLength": 32,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9 _.-]{0,31}$"
    }
  },
  "required": [
    "exchange"
  ]
}
```

限制：

```json
{
  "requests_per_ticket_max": 2,
  "timeout_seconds_max": 60,
  "max_response_bytes": 20000000,
  "max_rows": 50000,
  "arbitrary_urls_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "client_supplied_token_allowed": false,
  "websocket_allowed": false,
  "write_operations_allowed": false,
  "trading_or_order_execution_allowed": false,
  "secret_values_exposed": false
}
```

## Google Data Commons (`data-commons`)

- 状态：`启用`
- 说明：通过官方 REST V2 查询全球公共统计知识图谱，支持地点与指标解析、图节点关系和统计观测。
- 目录策略：仅开放 REST V2 的 resolve、node 和 observation 三个固定 POST 端点；优先读取中国起步目录，不假设所有城市或县均有数据。
- 执行策略：API Key 仅以 X-API-Key 后端请求头注入；每张票据只执行一个白名单操作，限制节点数、变量数、关系表达式、超时和响应体积。
- 票据前缀：`[api-dc]`
- Secret环境变量名：`GOOGLE_DATA_COMMONS_API_KEY`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`be48fabd30ef0c7cda43239e538ac2ea929f49d7fc323508c8301a8d93b7a2a7`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取受控能力和中国起步目录，不调用上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `resolve-place` | 按一个或多个公开地点名称解析 Data Commons 地点 DCID。 | `nodes_json, property` |

`resolve-place` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "nodes_json": {
      "type": "string",
      "minLength": 2,
      "maxLength": 6000
    },
    "property": {
      "type": "string",
      "maxLength": 300
    }
  },
  "required": [
    "nodes_json"
  ]
}
```

| `resolve-indicator` | 按公开指标名称或描述解析统计变量或主题 DCID。 | `nodes_json` |

`resolve-indicator` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "nodes_json": {
      "type": "string",
      "minLength": 2,
      "maxLength": 6000
    }
  },
  "required": [
    "nodes_json"
  ]
}
```

| `node-properties` | 按受控关系表达式读取节点属性、相邻实体或行政层级关系。 | `nodes_json, property` |

`node-properties` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "nodes_json": {
      "type": "string",
      "minLength": 2,
      "maxLength": 6000
    },
    "property": {
      "type": "string",
      "minLength": 1,
      "maxLength": 300
    }
  },
  "required": [
    "nodes_json",
    "property"
  ]
}
```

| `observations` | 读取公开实体和统计变量的最新值、指定日期或完整时间序列，并保留 facet 来源。 | `entity_dcids_json, variable_dcids_json, date, select_json, facet_ids_json, domains_json` |

`observations` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "entity_dcids_json": {
      "type": "string",
      "minLength": 2,
      "maxLength": 6000
    },
    "variable_dcids_json": {
      "type": "string",
      "minLength": 2,
      "maxLength": 6000
    },
    "date": {
      "type": "string",
      "maxLength": 40
    },
    "select_json": {
      "type": "string",
      "maxLength": 300
    },
    "facet_ids_json": {
      "type": "string",
      "maxLength": 6000
    },
    "domains_json": {
      "type": "string",
      "maxLength": 6000
    }
  },
  "required": [
    "entity_dcids_json",
    "variable_dcids_json"
  ]
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "max_nodes": 20,
  "max_variables": 20,
  "max_select_fields": 5,
  "max_relation_expression_characters": 300,
  "max_response_bytes": 1000000,
  "timeout_seconds_max": 60,
  "arbitrary_urls_allowed": false,
  "arbitrary_endpoints_allowed": false,
  "arbitrary_headers_allowed": false,
  "client_supplied_api_key_allowed": false,
  "sparql_allowed": false,
  "natural_language_api_allowed": false,
  "mcp_allowed": false,
  "write_operations_allowed": false,
  "personal_data_allowed": false,
  "secret_values_exposed": false
}
```

## 和风天气 QWeather (`qweather`)

- 状态：`启用`
- 说明：通过开发者专属 API Host 读取全球地理位置、城市天气、格点天气、分钟级降水、空气质量、生活指数、短期历史天气和太阳辐射数据。
- 目录策略：仅开放显式登记的固定 GET 路径和参数 Schema；固定使用用户专属 Host ka6r72kcc3.re.qweatherapi.com。
- 执行策略：QWEATHER_API_KEY 仅在后端 X-QW-Api-Key 请求头注入，不写入日志、Issue 或 Artifact；禁止任意 URL、Host、路径、请求头和客户端密钥。
- 票据前缀：`[api-qweather]`
- Secret环境变量名：`QWEATHER_API_KEY`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`17d05469d868d3c16103aec70b326c2a000291a5a845a9908f56e07a9743d352`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地和风天气安全能力目录，不调用上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `geo-city-lookup` | 全球城市、行政区或坐标反向解析，返回 LocationID、经纬度、时区和行政层级。 | `location, adm, range, number, lang` |

`geo-city-lookup` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "location": {
      "type": "string",
      "minLength": 1,
      "maxLength": 120,
      "pattern": "^[^/?#\\\\]{1,120}$"
    },
    "adm": {
      "type": "string",
      "maxLength": 100
    },
    "range": {
      "type": "string",
      "pattern": "^[A-Za-z]{2}$"
    },
    "number": {
      "type": "integer",
      "minimum": 1,
      "maximum": 20
    },
    "lang": {
      "type": "string",
      "enum": [
        "zh",
        "en",
        "fr",
        "es",
        "ja",
        "ko",
        "ru",
        "de",
        "pt",
        "it",
        "th",
        "ar"
      ]
    }
  },
  "required": [
    "location"
  ]
}
```

| `geo-city-top` | 读取全球或指定国家/地区的热门城市。 | `range, number, lang` |

`geo-city-top` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "range": {
      "type": "string",
      "pattern": "^[A-Za-z]{2}$"
    },
    "number": {
      "type": "integer",
      "minimum": 1,
      "maximum": 20
    },
    "lang": {
      "type": "string",
      "enum": [
        "zh",
        "en",
        "fr",
        "es",
        "ja",
        "ko",
        "ru",
        "de",
        "pt",
        "it",
        "th",
        "ar"
      ]
    }
  }
}
```

| `geo-poi-lookup` | 按关键字、坐标、LocationID 或 Adcode 搜索景点或潮汐站。 | `location, type, city, number, lang` |

`geo-poi-lookup` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "location": {
      "type": "string",
      "minLength": 1,
      "maxLength": 120,
      "pattern": "^[^/?#\\\\]{1,120}$"
    },
    "type": {
      "type": "string",
      "enum": [
        "scenic",
        "TSTA"
      ]
    },
    "city": {
      "type": "string",
      "maxLength": 100
    },
    "number": {
      "type": "integer",
      "minimum": 1,
      "maximum": 20
    },
    "lang": {
      "type": "string",
      "enum": [
        "zh",
        "en",
        "fr",
        "es",
        "ja",
        "ko",
        "ru",
        "de",
        "pt",
        "it",
        "th",
        "ar"
      ]
    }
  },
  "required": [
    "location",
    "type"
  ]
}
```

| `geo-poi-range` | 在指定坐标半径内搜索景点或潮汐站。 | `location, type, radius, number, lang` |

`geo-poi-range` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "location": {
      "type": "string",
      "maxLength": 32,
      "pattern": "^-?(?:180(?:\\.0{1,2})?|(?:1[0-7]\\d|[1-9]?\\d)(?:\\.\\d{1,2})?),-?(?:90(?:\\.0{1,2})?|(?:[1-8]?\\d)(?:\\.\\d{1,2})?)$"
    },
    "type": {
      "type": "string",
      "enum": [
        "scenic",
        "TSTA"
      ]
    },
    "radius": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50
    },
    "number": {
      "type": "integer",
      "minimum": 1,
      "maximum": 20
    },
    "lang": {
      "type": "string",
      "enum": [
        "zh",
        "en",
        "fr",
        "es",
        "ja",
        "ko",
        "ru",
        "de",
        "pt",
        "it",
        "th",
        "ar"
      ]
    }
  },
  "required": [
    "location",
    "type"
  ]
}
```

| `weather-now` | 读取全球城市实时天气观测。 | `location, lang, unit` |

`weather-now` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "location": {
      "type": "string",
      "minLength": 1,
      "maxLength": 120,
      "pattern": "^[^/?#\\\\]{1,120}$"
    },
    "lang": {
      "type": "string",
      "enum": [
        "zh",
        "en",
        "fr",
        "es",
        "ja",
        "ko",
        "ru",
        "de",
        "pt",
        "it",
        "th",
        "ar"
      ]
    },
    "unit": {
      "type": "string",
      "enum": [
        "m",
        "i"
      ]
    }
  },
  "required": [
    "location"
  ]
}
```

| `weather-daily` | 读取全球城市 3 至 30 日天气预报。 | `days, location, lang, unit` |

`weather-daily` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "days": {
      "type": "string",
      "enum": [
        "3d",
        "7d",
        "10d",
        "15d",
        "30d"
      ]
    },
    "location": {
      "type": "string",
      "minLength": 1,
      "maxLength": 120,
      "pattern": "^[^/?#\\\\]{1,120}$"
    },
    "lang": {
      "type": "string",
      "enum": [
        "zh",
        "en",
        "fr",
        "es",
        "ja",
        "ko",
        "ru",
        "de",
        "pt",
        "it",
        "th",
        "ar"
      ]
    },
    "unit": {
      "type": "string",
      "enum": [
        "m",
        "i"
      ]
    }
  },
  "required": [
    "days",
    "location"
  ]
}
```

| `weather-hourly` | 读取全球城市未来 24 至 168 小时逐小时天气预报。 | `hours, location, lang, unit` |

`weather-hourly` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "hours": {
      "type": "string",
      "enum": [
        "24h",
        "72h",
        "168h"
      ]
    },
    "location": {
      "type": "string",
      "minLength": 1,
      "maxLength": 120,
      "pattern": "^[^/?#\\\\]{1,120}$"
    },
    "lang": {
      "type": "string",
      "enum": [
        "zh",
        "en",
        "fr",
        "es",
        "ja",
        "ko",
        "ru",
        "de",
        "pt",
        "it",
        "th",
        "ar"
      ]
    },
    "unit": {
      "type": "string",
      "enum": [
        "m",
        "i"
      ]
    }
  },
  "required": [
    "hours",
    "location"
  ]
}
```

| `minutely-precipitation` | 读取中国坐标未来两小时每 5 分钟降水临近预报。 | `location, lang` |

`minutely-precipitation` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "location": {
      "type": "string",
      "maxLength": 32,
      "pattern": "^-?(?:180(?:\\.0{1,2})?|(?:1[0-7]\\d|[1-9]?\\d)(?:\\.\\d{1,2})?),-?(?:90(?:\\.0{1,2})?|(?:[1-8]?\\d)(?:\\.\\d{1,2})?)$"
    },
    "lang": {
      "type": "string",
      "enum": [
        "zh",
        "en",
        "fr",
        "es",
        "ja",
        "ko",
        "ru",
        "de",
        "pt",
        "it",
        "th",
        "ar"
      ]
    }
  },
  "required": [
    "location"
  ]
}
```

| `grid-weather-now` | 读取全球坐标 3–5 公里格点实时天气。 | `location, lang, unit` |

`grid-weather-now` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "location": {
      "type": "string",
      "maxLength": 32,
      "pattern": "^-?(?:180(?:\\.0{1,2})?|(?:1[0-7]\\d|[1-9]?\\d)(?:\\.\\d{1,2})?),-?(?:90(?:\\.0{1,2})?|(?:[1-8]?\\d)(?:\\.\\d{1,2})?)$"
    },
    "lang": {
      "type": "string",
      "enum": [
        "zh",
        "en",
        "fr",
        "es",
        "ja",
        "ko",
        "ru",
        "de",
        "pt",
        "it",
        "th",
        "ar"
      ]
    },
    "unit": {
      "type": "string",
      "enum": [
        "m",
        "i"
      ]
    }
  },
  "required": [
    "location"
  ]
}
```

| `grid-weather-daily` | 读取全球坐标 3 或 7 日格点天气预报。 | `days, location, lang, unit` |

`grid-weather-daily` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "days": {
      "type": "string",
      "enum": [
        "3d",
        "7d"
      ]
    },
    "location": {
      "type": "string",
      "maxLength": 32,
      "pattern": "^-?(?:180(?:\\.0{1,2})?|(?:1[0-7]\\d|[1-9]?\\d)(?:\\.\\d{1,2})?),-?(?:90(?:\\.0{1,2})?|(?:[1-8]?\\d)(?:\\.\\d{1,2})?)$"
    },
    "lang": {
      "type": "string",
      "enum": [
        "zh",
        "en",
        "fr",
        "es",
        "ja",
        "ko",
        "ru",
        "de",
        "pt",
        "it",
        "th",
        "ar"
      ]
    },
    "unit": {
      "type": "string",
      "enum": [
        "m",
        "i"
      ]
    }
  },
  "required": [
    "days",
    "location"
  ]
}
```

| `grid-weather-hourly` | 读取全球坐标 24 或 72 小时格点天气预报。 | `hours, location, lang, unit` |

`grid-weather-hourly` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "hours": {
      "type": "string",
      "enum": [
        "24h",
        "72h"
      ]
    },
    "location": {
      "type": "string",
      "maxLength": 32,
      "pattern": "^-?(?:180(?:\\.0{1,2})?|(?:1[0-7]\\d|[1-9]?\\d)(?:\\.\\d{1,2})?),-?(?:90(?:\\.0{1,2})?|(?:[1-8]?\\d)(?:\\.\\d{1,2})?)$"
    },
    "lang": {
      "type": "string",
      "enum": [
        "zh",
        "en",
        "fr",
        "es",
        "ja",
        "ko",
        "ru",
        "de",
        "pt",
        "it",
        "th",
        "ar"
      ]
    },
    "unit": {
      "type": "string",
      "enum": [
        "m",
        "i"
      ]
    }
  },
  "required": [
    "hours",
    "location"
  ]
}
```

| `air-quality-current` | 读取全球坐标 1×1 公里实时空气质量、污染物和健康建议。 | `latitude, longitude, lang` |

`air-quality-current` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
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
    "lang": {
      "type": "string",
      "enum": [
        "zh",
        "en",
        "fr",
        "es",
        "ja",
        "ko",
        "ru",
        "de",
        "pt",
        "it",
        "th",
        "ar"
      ]
    }
  },
  "required": [
    "latitude",
    "longitude"
  ]
}
```

| `air-quality-hourly` | 读取全球坐标未来 24 小时空气质量预报。 | `latitude, longitude, lang, local_time` |

`air-quality-hourly` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
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
    "lang": {
      "type": "string",
      "enum": [
        "zh",
        "en",
        "fr",
        "es",
        "ja",
        "ko",
        "ru",
        "de",
        "pt",
        "it",
        "th",
        "ar"
      ]
    },
    "local_time": {
      "type": "boolean"
    }
  },
  "required": [
    "latitude",
    "longitude"
  ]
}
```

| `air-quality-daily` | 读取全球坐标未来 3 日空气质量预报。 | `latitude, longitude, lang, local_time` |

`air-quality-daily` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
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
    "lang": {
      "type": "string",
      "enum": [
        "zh",
        "en",
        "fr",
        "es",
        "ja",
        "ko",
        "ru",
        "de",
        "pt",
        "it",
        "th",
        "ar"
      ]
    },
    "local_time": {
      "type": "boolean"
    }
  },
  "required": [
    "latitude",
    "longitude"
  ]
}
```

| `weather-indices` | 读取中国和全球城市 1 或 3 日天气生活指数。 | `days, location, type, lang` |

`weather-indices` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "days": {
      "type": "string",
      "enum": [
        "1d",
        "3d"
      ]
    },
    "location": {
      "type": "string",
      "minLength": 1,
      "maxLength": 120,
      "pattern": "^[^/?#\\\\]{1,120}$"
    },
    "type": {
      "type": "string",
      "pattern": "^(?:[1-9]|1[0-6])(?:,(?:[1-9]|1[0-6])){0,15}$",
      "maxLength": 64
    },
    "lang": {
      "type": "string",
      "enum": [
        "zh",
        "en",
        "fr",
        "es",
        "ja",
        "ko",
        "ru",
        "de",
        "pt",
        "it",
        "th",
        "ar"
      ]
    }
  },
  "required": [
    "days",
    "location",
    "type"
  ]
}
```

| `historical-weather` | 读取最近 10 天内指定日期的历史天气再分析数据。 | `location, date, lang, unit` |

`historical-weather` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "location": {
      "type": "string",
      "pattern": "^[0-9A-Za-z_-]{3,32}$"
    },
    "date": {
      "type": "string",
      "pattern": "^[0-9]{8}$"
    },
    "lang": {
      "type": "string",
      "enum": [
        "zh",
        "en",
        "fr",
        "es",
        "ja",
        "ko",
        "ru",
        "de",
        "pt",
        "it",
        "th",
        "ar"
      ]
    },
    "unit": {
      "type": "string",
      "enum": [
        "m",
        "i"
      ]
    }
  },
  "required": [
    "location",
    "date"
  ]
}
```

| `solar-radiation-forecast` | 读取全球坐标未来 1–60 小时太阳辐射预报。 | `latitude, longitude, hours, interval, tilt, azimuth, extra` |

`solar-radiation-forecast` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
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
    "hours": {
      "type": "integer",
      "minimum": 1,
      "maximum": 60
    },
    "interval": {
      "type": "integer",
      "enum": [
        15,
        30,
        60
      ]
    },
    "tilt": {
      "type": "integer",
      "minimum": 0,
      "maximum": 90
    },
    "azimuth": {
      "type": "integer",
      "minimum": 0,
      "maximum": 359
    },
    "extra": {
      "type": "string",
      "pattern": "^(?:weather|poa)(?:,(?:weather|poa))?$"
    }
  },
  "required": [
    "latitude",
    "longitude"
  ]
}
```

限制：

```json
{
  "requests_per_ticket_max": 2,
  "timeout_seconds_max": 60,
  "max_response_bytes": 5000000,
  "max_rows": 5000,
  "fixed_api_host": "ka6r72kcc3.re.qweatherapi.com",
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "client_supplied_api_key_allowed": false,
  "redirects_allowed": false,
  "write_operations_allowed": false,
  "personal_data_allowed": false,
  "secret_values_exposed": false
}
```

## Xweather 全球专业天气数据 (`xweather`)

- 状态：`启用`
- 说明：通过 Xweather 官方 Weather API 读取全球地点、实时观测、插值条件、15 日预报、官方预警、空气质量、日月和历史观测汇总。
- 目录策略：固定开放 10 项核心只读能力；所有端点、路径、参数、时间范围、返回条数和响应体积受白名单与硬上限约束。
- 执行策略：Client ID 由 GitHub Repository Variable 注入，Client Secret 仅由 Repository Secret 注入；不接受客户端凭据、任意 URL、任意查询、路线批量、写操作或 Webhook。
- 票据前缀：`[api-xweather]`
- Secret环境变量名：`XWEATHER_CLIENT_SECRET`（仅名称）
- Repository Variable名：`XWEATHER_CLIENT_ID`（仅名称）
- 提供方SHA-256：`c94519d010f5fd3dc128c75c27872a7b296c3e0685fbb099b31cfc5b6c065f90`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地 Xweather 安全能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `places-closest` | 按城市、邮编、站点或经纬度查询最近地理位置。 | `p, limit, fields` |

`places-closest` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "p": {
      "type": "string",
      "minLength": 1,
      "maxLength": 120,
      "pattern": "^[^/?#\\\\&=%]{1,120}$"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 20
    },
    "fields": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500,
      "pattern": "^[A-Za-z0-9._,-]{1,500}$"
    }
  },
  "required": [
    "p"
  ]
}
```

| `observations-current` | 读取指定位置最近的全球气象站实时观测。 | `location, filter, fields` |

`observations-current` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "location": {
      "type": "string",
      "minLength": 1,
      "maxLength": 120,
      "pattern": "^[^/?#\\\\&=%]{1,120}$"
    },
    "filter": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9._,-]{1,64}$"
    },
    "fields": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500,
      "pattern": "^[A-Za-z0-9._,-]{1,500}$"
    }
  },
  "required": [
    "location"
  ]
}
```

| `conditions` | 读取全球位置当前、历史、未来逐小时条件或分钟级降水条件。 | `location, from, to, at_time, filter, limit, fields` |

`conditions` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "location": {
      "type": "string",
      "minLength": 1,
      "maxLength": 120,
      "pattern": "^[^/?#\\\\&=%]{1,120}$"
    },
    "from": {
      "type": "string",
      "minLength": 1,
      "maxLength": 32,
      "pattern": "^[A-Za-z0-9:+._-]{1,32}$"
    },
    "to": {
      "type": "string",
      "minLength": 1,
      "maxLength": 32,
      "pattern": "^[A-Za-z0-9:+._-]{1,32}$"
    },
    "at_time": {
      "type": "string",
      "minLength": 1,
      "maxLength": 32,
      "pattern": "^[A-Za-z0-9:+._-]{1,32}$"
    },
    "filter": {
      "type": "string",
      "enum": [
        "1hr",
        "minutelyprecip"
      ]
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 72
    },
    "fields": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500,
      "pattern": "^[A-Za-z0-9._,-]{1,500}$"
    }
  },
  "required": [
    "location"
  ]
}
```

| `forecasts` | 读取全球位置最长 15 日的日、昼夜或小时天气预报。 | `location, filter, limit, fields` |

`forecasts` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "location": {
      "type": "string",
      "minLength": 1,
      "maxLength": 120,
      "pattern": "^[^/?#\\\\&=%]{1,120}$"
    },
    "filter": {
      "type": "string",
      "enum": [
        "day",
        "daynight",
        "mdnt2mdnt",
        "1hr",
        "3hr",
        "6hr"
      ]
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 31
    },
    "fields": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500,
      "pattern": "^[A-Za-z0-9._,-]{1,500}$"
    }
  },
  "required": [
    "location"
  ]
}
```

| `alerts` | 读取指定位置当前有效的官方天气预警。 | `location, limit, fields` |

`alerts` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "location": {
      "type": "string",
      "minLength": 1,
      "maxLength": 120,
      "pattern": "^[^/?#\\\\&=%]{1,120}$"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 20
    },
    "fields": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500,
      "pattern": "^[A-Za-z0-9._,-]{1,500}$"
    }
  },
  "required": [
    "location"
  ]
}
```

| `air-quality` | 读取全球位置当前空气质量、AQI、AQHI 和污染物信息。 | `location, filter, fields` |

`air-quality` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "location": {
      "type": "string",
      "minLength": 1,
      "maxLength": 120,
      "pattern": "^[^/?#\\\\&=%]{1,120}$"
    },
    "filter": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9._,-]{1,64}$"
    },
    "fields": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500,
      "pattern": "^[A-Za-z0-9._,-]{1,500}$"
    }
  },
  "required": [
    "location"
  ]
}
```

| `sunmoon` | 读取全球位置日出日落、曙暮光和月升月落数据。 | `location, from, to, limit` |

`sunmoon` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "location": {
      "type": "string",
      "minLength": 1,
      "maxLength": 120,
      "pattern": "^[^/?#\\\\&=%]{1,120}$"
    },
    "from": {
      "type": "string",
      "minLength": 1,
      "maxLength": 32,
      "pattern": "^[A-Za-z0-9:+._-]{1,32}$"
    },
    "to": {
      "type": "string",
      "minLength": 1,
      "maxLength": 32,
      "pattern": "^[A-Za-z0-9:+._-]{1,32}$"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 31
    }
  },
  "required": [
    "location"
  ]
}
```

| `moon-phases` | 读取全球位置主要月相发生时间。 | `location, from, to, limit` |

`moon-phases` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "location": {
      "type": "string",
      "minLength": 1,
      "maxLength": 120,
      "pattern": "^[^/?#\\\\&=%]{1,120}$"
    },
    "from": {
      "type": "string",
      "minLength": 1,
      "maxLength": 32,
      "pattern": "^[A-Za-z0-9:+._-]{1,32}$"
    },
    "to": {
      "type": "string",
      "minLength": 1,
      "maxLength": 32,
      "pattern": "^[A-Za-z0-9:+._-]{1,32}$"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 31
    }
  },
  "required": [
    "location"
  ]
}
```

| `observations-summary` | 读取指定位置最多 30 日的历史观测日汇总。 | `location, from, to, plimit, fields` |

`observations-summary` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "location": {
      "type": "string",
      "minLength": 1,
      "maxLength": 120,
      "pattern": "^[^/?#\\\\&=%]{1,120}$"
    },
    "from": {
      "type": "string",
      "minLength": 1,
      "maxLength": 32,
      "pattern": "^[A-Za-z0-9:+._-]{1,32}$"
    },
    "to": {
      "type": "string",
      "minLength": 1,
      "maxLength": 32,
      "pattern": "^[A-Za-z0-9:+._-]{1,32}$"
    },
    "fields": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500,
      "pattern": "^[A-Za-z0-9._,-]{1,500}$"
    },
    "plimit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 30
    }
  },
  "required": [
    "location"
  ]
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "timeout_seconds_max": 120,
  "max_response_bytes": 20000000,
  "max_rows": 5000,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "arbitrary_query_parameters_allowed": false,
  "redirects_allowed": false,
  "write_operations_allowed": false,
  "webhooks_allowed": false,
  "route_queries_allowed": false,
  "client_supplied_credentials_allowed": false,
  "personal_data_allowed": false,
  "secret_values_exposed": false,
  "fixed_api_host": "data.api.xweather.com",
  "provider_concurrency_max": 1,
  "transient_retry_max": 1,
  "plan_or_multiplier_dependent_endpoints": true
}
```

## 东方财富妙想 MCP (`miaoxiang-mcp`)

- 状态：`启用`
- 说明：通过东方财富官方 Streamable HTTP MCP Server 读取 A股、港股、美股、基金、债券、指数板块、宏观经济、公告研报和证券筛选数据。
- 目录策略：仅开放 MCP 上游实际发现并经仓库固定登记的 11 个只读工具，以及本地目录和 tools/list；禁止任意 JSON-RPC 方法、任意工具名和动态端点。
- 执行策略：每张票据只执行一个固定只读工具调用；后端通过 em_api_key 请求头注入 EM_API_KEY；禁止自选股修改、模拟交易、下单、账户操作和其他写操作。
- 票据前缀：`[api-mx-mcp]`
- Secret环境变量名：`EM_API_KEY`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`7a4fbf351f300bd5f746b94e48e374b24911a38b38211157a6c14ea72cf6a1de`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地妙想 MCP 安全能力目录，不访问上游且不需要密钥。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `mcp-tools-list` | 通过 MCP initialize 和 tools/list 读取上游当前工具目录，用于协议与能力验证。 | `无` |

`mcp-tools-list` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `us-finance-data` | 基于东方财富数据库，支持自然语言查询美股金融数据，覆盖美股证券与公司基本资料、股本与股东结构、行情与技术指标、量化风险指标、财务三表与估值盈利预测，以及IPO/回购/分红等，单次请求最多支持500只股票，可发起多次请求。例如：苹果和特斯拉近10个交易日的涨跌幅、换手率 | `query` |

`us-finance-data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    }
  },
  "required": [
    "query"
  ]
}
```

| `hk-finance-data` | 基于东方财富数据库，支持自然语言查询港股金融数据，覆盖港股证券与公司基本资料、股本与股东结构、行情与技术指标、量化风险指标、财务三表与估值盈利预测，以及IPO/回购/分红等，单次请求最多支持500只股票，可发起多次请求。例如：智谱、minimax的所属行业、上市日期与发行价 | `query` |

`hk-finance-data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    }
  },
  "required": [
    "query"
  ]
}
```

| `comprehensive-finance-data` | 基于东方财富数据库，支持自然语言综合性查询金融数据，当无法确定品种或者是其他品种（例如企业发行人、非上市公司等）可以使用此工具，单次请求最多支持500只证券或实体，可发起多次请求。例如：华为技术有限公司的企业基本信息 | `query` |

`comprehensive-finance-data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    }
  },
  "required": [
    "query"
  ]
}
```

| `macro-data` | 基于东方财富数据库，查询宏观经济、行业经济与大宗商品高频/历史指标数据。适用全球及中国宏观指标、区域经济指标、行业景气与产业链数据、主要产品量价数据；不适用于具体证券行情、财务、公告和筛选。 | `query` |

`macro-data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    }
  },
  "required": [
    "query"
  ]
}
```

| `stocks-screener` | 按条件筛选多只证券，支持A股、港股、美股、基金和债券；不用于查询特定标的数据或新闻研报。 | `query` |

`stocks-screener` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    }
  },
  "required": [
    "query"
  ]
}
```

| `finance-search-news` | 检索个股、行业、板块、指数和宏观策略相关的新闻、研报、评级观点、目标价、盈利预测、风险提示和行业趋势。 | `query` |

`finance-search-news` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    }
  },
  "required": [
    "query"
  ]
}
```

| `finance-search-notice` | 搜索上市公司、基金、债券、港美股、交易所和监管机构的公告、披露文件、定期报告及重大事项。 | `query` |

`finance-search-notice` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    }
  },
  "required": [
    "query"
  ]
}
```

| `ashare-finance-data` | 查询A股基本资料、行情与技术指标、财务与估值、股本股东、公司事件和量化风险指标。 | `query` |

`ashare-finance-data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    }
  },
  "required": [
    "query"
  ]
}
```

| `fund-finance-data` | 查询基金基本资料、发行信息、净值与绩效、排名、财务分红、份额持有人、资产配置和持仓明细。 | `query` |

`fund-finance-data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    }
  },
  "required": [
    "query"
  ]
}
```

| `bond-finance-data` | 查询债券基本信息、发行兑付、行情报价、估值分析、久期凸性、发行人财务、信用评级和可转债条款。 | `query` |

`bond-finance-data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    }
  },
  "required": [
    "query"
  ]
}
```

| `index-block-finance-data` | 查询指数、行业、概念和市场板块的行情、技术指标、财务估值及成分股聚合指标。 | `query` |

`index-block-finance-data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    }
  },
  "required": [
    "query"
  ]
}
```

限制：

```json
{
  "requests_per_ticket_max": 3,
  "timeout_seconds_max": 120,
  "max_response_bytes": 5000000,
  "max_rows": 5000,
  "max_query_characters": 500,
  "fixed_mcp_host": "mxapi.eastmoney.com",
  "fixed_mcp_path": "/mxds/mcp",
  "fixed_mcp_tool_count": 11,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "client_supplied_api_key_allowed": false,
  "arbitrary_jsonrpc_methods_allowed": false,
  "arbitrary_mcp_tool_names_allowed": false,
  "resources_allowed": false,
  "prompts_allowed": false,
  "write_operations_allowed": false,
  "watchlist_mutation_allowed": false,
  "simulated_trading_allowed": false,
  "trading_or_order_execution_allowed": false,
  "personal_data_allowed": false,
  "secret_values_exposed": false
}
```

## East Asia Econ 东亚宏观数据库 (`east-asia-econ`)

- 状态：`启用`
- 说明：通过 East Asia Econ 官方只读 REST API 搜索并读取中国、日本、韩国、台湾及区域汇总的月度、季度和年度经济序列。
- 目录策略：开放固定的搜索、序列元数据、数据库统计、序列数据和账户用量接口；搜索、元数据和统计无需密钥，序列数据与用量由后端注入独立 API Key。
- 执行策略：仅允许固定 HTTPS GET 路径与白名单查询参数；每张票据最多一次上游请求，不重试付费或限额查询；API Key 仅写入 X-API-Key 请求头，不进入 Issue、日志、目录或 Artifact。
- 票据前缀：`[api-east-asia-econ]`
- Secret环境变量名：`EAST_ASIA_ECON_API_KEY`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`0c433a9dd653a1039c389b5eed82ad054487980f2d11516e32dbee1a3191f0d7`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地 East Asia Econ 安全能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `search-series` | 按关键词、经济体和频率搜索可用经济序列；官方搜索接口无需认证。 | `q, country, freq, limit` |

`search-series` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "q": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "country": {
      "type": "string",
      "enum": [
        "cn",
        "jp",
        "kr",
        "tw",
        "region"
      ]
    },
    "freq": {
      "type": "string",
      "enum": [
        "m",
        "q",
        "a"
      ]
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    }
  },
  "required": [
    "q"
  ]
}
```

| `series-info` | 读取指定序列的可用频率、日期范围和观测数量；无需下载数据或消耗序列查询额度。 | `series_name` |

`series-info` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "series_name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    }
  },
  "required": [
    "series_name"
  ]
}
```

| `database-stats` | 读取数据库总序列数及按经济体、频率划分的汇总统计；无需认证。 | `无` |

`database-stats` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `series-data` | 下载指定经济序列的月度、季度或年度观测值，可按起止日期过滤。 | `series_name, freq, start, end` |

`series-data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "series_name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    },
    "freq": {
      "type": "string",
      "enum": [
        "m",
        "q",
        "a"
      ]
    },
    "start": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "end": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  },
  "required": [
    "series_name"
  ]
}
```

| `usage` | 读取当前 East Asia Econ API Key 的月度用量、额度和会员层级。 | `无` |

`usage` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

限制：

```json
{
  "fixed_api_host": "data-api.eastasiaecon.com",
  "requests_per_ticket_max": 1,
  "timeout_seconds_max": 60,
  "max_response_bytes": 20000000,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "client_supplied_api_key_allowed": false,
  "redirects_allowed": false,
  "write_operations_allowed": false,
  "personal_data_allowed": false,
  "secret_values_exposed": false
}
```

## Alpha Vantage 全球金融与宏观数据 (`alpha-vantage`)

- 状态：`启用`
- 说明：通过 Alpha Vantage 官方 HTTPS Query API 读取全球股票、指数、期权、基本面、公司行动、新闻情绪、外汇、数字资产、商品、美国宏观经济和技术指标。
- 目录策略：仅开放目录中显式登记的固定 Alpha Vantage function 和参数 Schema；禁止任意 function、任意 URL、任意主机、任意请求头、客户端自带 apikey、CSV、交易、下单、账户修改和数据写入。
- 执行策略：ALPHA_VANTAGE_API_KEY 仅由后端注入固定 HTTPS GET 查询；每张票据最多一次上游请求且全 Provider 串行，避免消耗免费密钥每日 25 次额度；响应、超时和体积受限，错误和额度提示结构化返回。
- 票据前缀：`[api-alpha-vantage]`
- Secret环境变量名：`ALPHA_VANTAGE_API_KEY`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`15e466cbf2cd445f58ae15b1d0d47561ef682ed72198b7637e54bf193b6b77bc`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地 Alpha Vantage 安全能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `symbol-search` | 按关键词搜索全球股票、ETF 和基金代码。 | `keywords` |

`symbol-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "keywords": {
      "type": "string",
      "minLength": 1,
      "maxLength": 120
    }
  }
}
```

| `global-quote` | 读取单一全球证券的最新报价快照。 | `symbol, entitlement` |

`global-quote` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    },
    "entitlement": {
      "type": "string",
      "enum": [
        "delayed",
        "realtime"
      ]
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `market-status` | 读取全球主要市场开闭市状态。 | `无` |

`market-status` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `stock-intraday` | 读取全球股票分钟级 OHLCV 时间序列。 | `symbol, interval, outputsize, month, adjusted, extended_hours, entitlement` |

`stock-intraday` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    },
    "interval": {
      "type": "string",
      "enum": [
        "1min",
        "5min",
        "15min",
        "30min",
        "60min"
      ]
    },
    "outputsize": {
      "type": "string",
      "enum": [
        "compact",
        "full"
      ]
    },
    "month": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}$"
    },
    "adjusted": {
      "type": "boolean"
    },
    "extended_hours": {
      "type": "boolean"
    },
    "entitlement": {
      "type": "string",
      "enum": [
        "delayed",
        "realtime"
      ]
    }
  },
  "required": [
    "symbol",
    "interval"
  ]
}
```

| `stock-daily` | 读取全球股票日线 OHLCV；compact 可用于免费密钥。 | `symbol, outputsize` |

`stock-daily` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    },
    "outputsize": {
      "type": "string",
      "enum": [
        "compact",
        "full"
      ]
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `stock-daily-adjusted` | 读取复权日线、分红和拆股事件。 | `symbol, outputsize, entitlement` |

`stock-daily-adjusted` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    },
    "outputsize": {
      "type": "string",
      "enum": [
        "compact",
        "full"
      ]
    },
    "entitlement": {
      "type": "string",
      "enum": [
        "delayed",
        "realtime"
      ]
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `stock-weekly` | 读取全球股票周线 OHLCV。 | `symbol` |

`stock-weekly` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `stock-weekly-adjusted` | 读取全球股票复权周线。 | `symbol` |

`stock-weekly-adjusted` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `stock-monthly` | 读取全球股票月线 OHLCV。 | `symbol` |

`stock-monthly` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `stock-monthly-adjusted` | 读取全球股票复权月线。 | `symbol` |

`stock-monthly-adjusted` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `realtime-bulk-quotes` | 批量读取最多 50 个证券的实时报价。 | `symbol` |

`realtime-bulk-quotes` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 512,
      "pattern": "^[A-Za-z0-9._:-]+(,[A-Za-z0-9._:-]+){0,49}$"
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `index-catalog` | 读取 Alpha Vantage 支持的市场指数目录。 | `无` |

`index-catalog` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `index-data` | 读取主要市场指数的日、周或月 OHLC。 | `symbol, interval` |

`index-data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    },
    "interval": {
      "type": "string",
      "enum": [
        "daily",
        "weekly",
        "monthly"
      ]
    }
  },
  "required": [
    "symbol",
    "interval"
  ]
}
```

| `realtime-options` | 读取美国股票实时期权链或指定合约。 | `symbol, require_greeks, contract` |

`realtime-options` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    },
    "require_greeks": {
      "type": "boolean"
    },
    "contract": {
      "type": "string",
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9]+$"
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `historical-options` | 读取美国股票历史期权链。 | `symbol, date` |

`historical-options` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    },
    "date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `news-sentiment` | 读取股票、外汇、数字资产和宏观主题新闻及情绪。 | `tickers, topics, time_from, time_to, sort, limit` |

`news-sentiment` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "tickers": {
      "type": "string",
      "maxLength": 300,
      "pattern": "^[A-Za-z0-9._:-]+(,[A-Za-z0-9._:-]+){0,19}$"
    },
    "topics": {
      "type": "string",
      "maxLength": 300,
      "pattern": "^[a-z_]+(,[a-z_]+){0,9}$"
    },
    "time_from": {
      "type": "string",
      "pattern": "^[0-9]{8}T[0-9]{4}$"
    },
    "time_to": {
      "type": "string",
      "pattern": "^[0-9]{8}T[0-9]{4}$"
    },
    "sort": {
      "type": "string",
      "enum": [
        "LATEST",
        "EARLIEST",
        "RELEVANCE"
      ]
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000
    }
  }
}
```

| `top-gainers-losers` | 读取美国市场涨幅榜、跌幅榜和最活跃榜。 | `无` |

`top-gainers-losers` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `company-overview` | 读取上市公司概览、估值和关键财务指标。 | `symbol` |

`company-overview` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `income-statement` | 读取公司年度和季度利润表。 | `symbol` |

`income-statement` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `balance-sheet` | 读取公司年度和季度资产负债表。 | `symbol` |

`balance-sheet` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `cash-flow` | 读取公司年度和季度现金流量表。 | `symbol` |

`cash-flow` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `earnings` | 读取公司年度和季度每股收益。 | `symbol` |

`earnings` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `earnings-estimates` | 读取公司盈利预测和分析师共识。 | `symbol, horizon` |

`earnings-estimates` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    },
    "horizon": {
      "type": "string",
      "enum": [
        "3month",
        "6month",
        "12month"
      ]
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `listing-status` | 读取美国股票与 ETF 上市或退市状态。 | `date, state` |

`listing-status` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "state": {
      "type": "string",
      "enum": [
        "active",
        "delisted"
      ]
    }
  }
}
```

| `earnings-calendar` | 读取未来企业财报日历。 | `symbol, horizon` |

`earnings-calendar` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    },
    "horizon": {
      "type": "string",
      "enum": [
        "3month",
        "6month",
        "12month"
      ]
    }
  }
}
```

| `ipo-calendar` | 读取未来 IPO 日历。 | `无` |

`ipo-calendar` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `dividends` | 读取公司历史和未来已公告分红。 | `symbol` |

`dividends` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `splits` | 读取公司历史拆股和合股事件。 | `symbol` |

`splits` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `shares-outstanding` | 读取公司基本和稀释流通股数。 | `symbol` |

`shares-outstanding` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `insider-transactions` | 读取公司内部人交易。 | `symbol` |

`insider-transactions` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `institutional-holdings` | 读取机构持仓汇总与明细。 | `symbol` |

`institutional-holdings` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `etf-profile` | 读取 ETF 净资产、持仓和行业配置。 | `symbol` |

`etf-profile` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `currency-exchange-rate` | 读取两种法币或数字资产间的实时汇率。 | `from_currency, to_currency` |

`currency-exchange-rate` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "from_currency": {
      "type": "string",
      "pattern": "^[A-Z]{3}$"
    },
    "to_currency": {
      "type": "string",
      "pattern": "^[A-Z]{3}$"
    }
  },
  "required": [
    "from_currency",
    "to_currency"
  ]
}
```

| `fx-daily` | 读取外汇日线。 | `from_symbol, to_symbol, outputsize` |

`fx-daily` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "from_symbol": {
      "type": "string",
      "pattern": "^[A-Z]{3}$"
    },
    "to_symbol": {
      "type": "string",
      "pattern": "^[A-Z]{3}$"
    },
    "outputsize": {
      "type": "string",
      "enum": [
        "compact",
        "full"
      ]
    }
  },
  "required": [
    "from_symbol",
    "to_symbol"
  ]
}
```

| `fx-weekly` | 读取外汇周线。 | `from_symbol, to_symbol` |

`fx-weekly` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "from_symbol": {
      "type": "string",
      "pattern": "^[A-Z]{3}$"
    },
    "to_symbol": {
      "type": "string",
      "pattern": "^[A-Z]{3}$"
    }
  },
  "required": [
    "from_symbol",
    "to_symbol"
  ]
}
```

| `fx-monthly` | 读取外汇月线。 | `from_symbol, to_symbol` |

`fx-monthly` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "from_symbol": {
      "type": "string",
      "pattern": "^[A-Z]{3}$"
    },
    "to_symbol": {
      "type": "string",
      "pattern": "^[A-Z]{3}$"
    }
  },
  "required": [
    "from_symbol",
    "to_symbol"
  ]
}
```

| `digital-currency-daily` | 读取数字资产日线。 | `symbol, market` |

`digital-currency-daily` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "pattern": "^[A-Z]{3}$"
    },
    "market": {
      "type": "string",
      "pattern": "^[A-Z]{3}$"
    }
  },
  "required": [
    "symbol",
    "market"
  ]
}
```

| `digital-currency-weekly` | 读取数字资产周线。 | `symbol, market` |

`digital-currency-weekly` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "pattern": "^[A-Z]{3}$"
    },
    "market": {
      "type": "string",
      "pattern": "^[A-Z]{3}$"
    }
  },
  "required": [
    "symbol",
    "market"
  ]
}
```

| `digital-currency-monthly` | 读取数字资产月线。 | `symbol, market` |

`digital-currency-monthly` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "pattern": "^[A-Z]{3}$"
    },
    "market": {
      "type": "string",
      "pattern": "^[A-Z]{3}$"
    }
  },
  "required": [
    "symbol",
    "market"
  ]
}
```

| `gold-silver-spot` | 读取黄金或白银现货价格。 | `symbol` |

`gold-silver-spot` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "enum": [
        "GOLD",
        "XAU",
        "SILVER",
        "XAG"
      ]
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `gold-silver-history` | 读取黄金或白银历史价格。 | `symbol, interval` |

`gold-silver-history` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "enum": [
        "GOLD",
        "XAU",
        "SILVER",
        "XAG"
      ]
    },
    "interval": {
      "type": "string",
      "enum": [
        "daily",
        "weekly",
        "monthly"
      ]
    }
  },
  "required": [
    "symbol",
    "interval"
  ]
}
```

| `wti` | 读取西德克萨斯中质原油价格。 | `interval` |

`wti` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "interval": {
      "type": "string",
      "enum": [
        "daily",
        "weekly",
        "monthly"
      ]
    }
  },
  "required": [
    "interval"
  ]
}
```

| `brent` | 读取布伦特原油价格。 | `interval` |

`brent` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "interval": {
      "type": "string",
      "enum": [
        "daily",
        "weekly",
        "monthly"
      ]
    }
  },
  "required": [
    "interval"
  ]
}
```

| `natural-gas` | 读取亨利港天然气价格。 | `interval` |

`natural-gas` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "interval": {
      "type": "string",
      "enum": [
        "daily",
        "weekly",
        "monthly"
      ]
    }
  },
  "required": [
    "interval"
  ]
}
```

| `copper` | 读取铜价。 | `interval` |

`copper` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "interval": {
      "type": "string",
      "enum": [
        "daily",
        "weekly",
        "monthly"
      ]
    }
  },
  "required": [
    "interval"
  ]
}
```

| `aluminum` | 读取铝价。 | `interval` |

`aluminum` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "interval": {
      "type": "string",
      "enum": [
        "daily",
        "weekly",
        "monthly"
      ]
    }
  },
  "required": [
    "interval"
  ]
}
```

| `real-gdp` | 读取美国实际 GDP。 | `interval` |

`real-gdp` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "interval": {
      "type": "string",
      "enum": [
        "annual",
        "quarterly"
      ]
    }
  },
  "required": [
    "interval"
  ]
}
```

| `real-gdp-per-capita` | 读取美国人均实际 GDP。 | `无` |

`real-gdp-per-capita` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `treasury-yield` | 读取美国国债收益率。 | `interval, maturity` |

`treasury-yield` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "interval": {
      "type": "string",
      "enum": [
        "daily",
        "weekly",
        "monthly"
      ]
    },
    "maturity": {
      "type": "string",
      "enum": [
        "3month",
        "2year",
        "5year",
        "7year",
        "10year",
        "30year"
      ]
    }
  },
  "required": [
    "interval",
    "maturity"
  ]
}
```

| `federal-funds-rate` | 读取美国联邦基金利率。 | `interval` |

`federal-funds-rate` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "interval": {
      "type": "string",
      "enum": [
        "daily",
        "weekly",
        "monthly"
      ]
    }
  },
  "required": [
    "interval"
  ]
}
```

| `cpi` | 读取美国消费者价格指数。 | `interval` |

`cpi` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "interval": {
      "type": "string",
      "enum": [
        "monthly",
        "semiannual"
      ]
    }
  },
  "required": [
    "interval"
  ]
}
```

| `inflation` | 读取美国年度通胀率。 | `无` |

`inflation` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `retail-sales` | 读取美国月度零售销售。 | `无` |

`retail-sales` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `durable-goods` | 读取美国耐用品订单。 | `无` |

`durable-goods` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `unemployment` | 读取美国失业率。 | `无` |

`unemployment` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `nonfarm-payroll` | 读取美国非农就业人数。 | `无` |

`nonfarm-payroll` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `sma` | 计算简单移动平均线。 | `symbol, interval, time_period, series_type, month, entitlement` |

`sma` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    },
    "interval": {
      "type": "string",
      "enum": [
        "1min",
        "5min",
        "15min",
        "30min",
        "60min",
        "daily",
        "weekly",
        "monthly"
      ]
    },
    "time_period": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10000
    },
    "series_type": {
      "type": "string",
      "enum": [
        "open",
        "high",
        "low",
        "close"
      ]
    },
    "month": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}$"
    },
    "entitlement": {
      "type": "string",
      "enum": [
        "delayed",
        "realtime"
      ]
    }
  },
  "required": [
    "symbol",
    "interval",
    "time_period",
    "series_type"
  ]
}
```

| `ema` | 计算指数移动平均线。 | `symbol, interval, time_period, series_type, month, entitlement` |

`ema` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    },
    "interval": {
      "type": "string",
      "enum": [
        "1min",
        "5min",
        "15min",
        "30min",
        "60min",
        "daily",
        "weekly",
        "monthly"
      ]
    },
    "time_period": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10000
    },
    "series_type": {
      "type": "string",
      "enum": [
        "open",
        "high",
        "low",
        "close"
      ]
    },
    "month": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}$"
    },
    "entitlement": {
      "type": "string",
      "enum": [
        "delayed",
        "realtime"
      ]
    }
  },
  "required": [
    "symbol",
    "interval",
    "time_period",
    "series_type"
  ]
}
```

| `rsi` | 计算相对强弱指数。 | `symbol, interval, time_period, series_type, month, entitlement` |

`rsi` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    },
    "interval": {
      "type": "string",
      "enum": [
        "1min",
        "5min",
        "15min",
        "30min",
        "60min",
        "daily",
        "weekly",
        "monthly"
      ]
    },
    "time_period": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10000
    },
    "series_type": {
      "type": "string",
      "enum": [
        "open",
        "high",
        "low",
        "close"
      ]
    },
    "month": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}$"
    },
    "entitlement": {
      "type": "string",
      "enum": [
        "delayed",
        "realtime"
      ]
    }
  },
  "required": [
    "symbol",
    "interval",
    "time_period",
    "series_type"
  ]
}
```

| `macd` | 计算 MACD。 | `symbol, interval, time_period, series_type, month, entitlement, fastperiod, slowperiod, signalperiod, matype` |

`macd` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    },
    "interval": {
      "type": "string",
      "enum": [
        "1min",
        "5min",
        "15min",
        "30min",
        "60min",
        "daily",
        "weekly",
        "monthly"
      ]
    },
    "time_period": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10000
    },
    "series_type": {
      "type": "string",
      "enum": [
        "open",
        "high",
        "low",
        "close"
      ]
    },
    "month": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}$"
    },
    "entitlement": {
      "type": "string",
      "enum": [
        "delayed",
        "realtime"
      ]
    },
    "fastperiod": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10000
    },
    "slowperiod": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10000
    },
    "signalperiod": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10000
    },
    "matype": {
      "type": "integer",
      "minimum": 0,
      "maximum": 8
    }
  },
  "required": [
    "symbol",
    "interval",
    "series_type"
  ]
}
```

| `bbands` | 计算布林带。 | `symbol, interval, time_period, series_type, month, entitlement, nbdevup, nbdevdn, matype` |

`bbands` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    },
    "interval": {
      "type": "string",
      "enum": [
        "1min",
        "5min",
        "15min",
        "30min",
        "60min",
        "daily",
        "weekly",
        "monthly"
      ]
    },
    "time_period": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10000
    },
    "series_type": {
      "type": "string",
      "enum": [
        "open",
        "high",
        "low",
        "close"
      ]
    },
    "month": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}$"
    },
    "entitlement": {
      "type": "string",
      "enum": [
        "delayed",
        "realtime"
      ]
    },
    "nbdevup": {
      "type": "number",
      "minimum": 0.1,
      "maximum": 20
    },
    "nbdevdn": {
      "type": "number",
      "minimum": 0.1,
      "maximum": 20
    },
    "matype": {
      "type": "integer",
      "minimum": 0,
      "maximum": 8
    }
  },
  "required": [
    "symbol",
    "interval",
    "time_period",
    "series_type"
  ]
}
```

| `atr` | 计算平均真实波幅。 | `symbol, interval, time_period, month, entitlement` |

`atr` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    },
    "interval": {
      "type": "string",
      "enum": [
        "1min",
        "5min",
        "15min",
        "30min",
        "60min",
        "daily",
        "weekly",
        "monthly"
      ]
    },
    "time_period": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10000
    },
    "month": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}$"
    },
    "entitlement": {
      "type": "string",
      "enum": [
        "delayed",
        "realtime"
      ]
    }
  },
  "required": [
    "symbol",
    "interval",
    "time_period"
  ]
}
```

| `adx` | 计算平均趋向指数。 | `symbol, interval, time_period, month, entitlement` |

`adx` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    },
    "interval": {
      "type": "string",
      "enum": [
        "1min",
        "5min",
        "15min",
        "30min",
        "60min",
        "daily",
        "weekly",
        "monthly"
      ]
    },
    "time_period": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10000
    },
    "month": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}$"
    },
    "entitlement": {
      "type": "string",
      "enum": [
        "delayed",
        "realtime"
      ]
    }
  },
  "required": [
    "symbol",
    "interval",
    "time_period"
  ]
}
```

| `stoch` | 计算随机指标。 | `symbol, interval, fastkperiod, slowkperiod, slowdperiod, slowkmatype, slowdmatype, month, entitlement` |

`stoch` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    },
    "interval": {
      "type": "string",
      "enum": [
        "1min",
        "5min",
        "15min",
        "30min",
        "60min",
        "daily",
        "weekly",
        "monthly"
      ]
    },
    "fastkperiod": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10000
    },
    "slowkperiod": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10000
    },
    "slowdperiod": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10000
    },
    "slowkmatype": {
      "type": "integer",
      "minimum": 0,
      "maximum": 8
    },
    "slowdmatype": {
      "type": "integer",
      "minimum": 0,
      "maximum": 8
    },
    "month": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}$"
    },
    "entitlement": {
      "type": "string",
      "enum": [
        "delayed",
        "realtime"
      ]
    }
  },
  "required": [
    "symbol",
    "interval"
  ]
}
```

| `obv` | 计算能量潮指标。 | `symbol, interval, month, entitlement` |

`obv` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"
    },
    "interval": {
      "type": "string",
      "enum": [
        "1min",
        "5min",
        "15min",
        "30min",
        "60min",
        "daily",
        "weekly",
        "monthly"
      ]
    },
    "month": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}$"
    },
    "entitlement": {
      "type": "string",
      "enum": [
        "delayed",
        "realtime"
      ]
    }
  },
  "required": [
    "symbol",
    "interval"
  ]
}
```

限制：

```json
{
  "fixed_api_host": "www.alphavantage.co",
  "fixed_api_path": "/query",
  "requests_per_ticket_max": 1,
  "provider_concurrency_max": 1,
  "free_key_documented_requests_per_day": 25,
  "timeout_seconds_max": 60,
  "max_response_bytes": 20000000,
  "arbitrary_functions_allowed": false,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "client_supplied_api_key_allowed": false,
  "redirects_allowed": false,
  "csv_allowed": false,
  "write_operations_allowed": false,
  "trading_or_order_execution_allowed": false,
  "personal_data_allowed": false,
  "secret_values_exposed": false
}
```

## Overture Maps 全球开放地图数据 (`overture-maps`)

- 状态：`启用`
- 说明：通过 Overture 官方 STAC 目录和匿名对象存储，以受限边界框读取全球地址、建筑、行政区、地点、交通与基础底图要素。
- 目录策略：开放固定发布目录、要素类型、计数、城市级边界框提取和 GERS 查询；不开放全量全球下载、任意对象存储路径或任意 URL。
- 执行策略：只调用 Overture 官方 Python 客户端固定只读函数；边界框面积、要素类型、发布格式、返回条数和响应体积均受硬限制。
- 票据前缀：`[api-overture]`
- Secret环境变量名：`无`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`acec22ea8fb41dd662e964c99293ee8ae1fd72fed70b8332069a485e44787459`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地 Overture Maps 安全能力目录，不访问上游. | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `list-feature-types` | 读取固定开放的 Overture 主题与要素类型清单，不访问上游. | `无` |

`list-feature-types` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `list-releases` | 读取 Overture STAC 目录中的当前可用发布版本. | `无` |

`list-releases` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `latest-release` | 读取 Overture STAC 目录标记的最新发布版本. | `无` |

`latest-release` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `count-features` | 按城市级经纬度边界框统计指定 Overture 要素类型数量. | `feature_type, bbox, release` |

`count-features` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "feature_type": {
      "type": "string",
      "enum": [
        "address",
        "bathymetry",
        "building",
        "building_part",
        "division",
        "division_area",
        "division_boundary",
        "place",
        "segment",
        "connector",
        "infrastructure",
        "land",
        "land_cover",
        "land_use",
        "water"
      ]
    },
    "bbox": {
      "type": "array",
      "minItems": 4,
      "maxItems": 4,
      "items": {
        "type": "number",
        "minimum": -180,
        "maximum": 180
      }
    },
    "release": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}\\.[0-9]+$"
    }
  },
  "required": [
    "feature_type",
    "bbox"
  ]
}
```

| `query-features` | 按城市级边界框提取指定类型的有限条 GeoJSON 要素. | `feature_type, bbox, release, limit` |

`query-features` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "feature_type": {
      "type": "string",
      "enum": [
        "address",
        "bathymetry",
        "building",
        "building_part",
        "division",
        "division_area",
        "division_boundary",
        "place",
        "segment",
        "connector",
        "infrastructure",
        "land",
        "land_cover",
        "land_use",
        "water"
      ]
    },
    "bbox": {
      "type": "array",
      "minItems": 4,
      "maxItems": 4,
      "items": {
        "type": "number",
        "minimum": -180,
        "maximum": 180
      }
    },
    "release": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}\\.[0-9]+$"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000
    }
  },
  "required": [
    "feature_type",
    "bbox"
  ]
}
```

| `lookup-gers` | 按固定 UUID 格式查询 Overture Global Entity Reference System 注册表. | `gers_id` |

`lookup-gers` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "gers_id": {
      "type": "string",
      "format": "uuid"
    }
  },
  "required": [
    "gers_id"
  ]
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "timeout_seconds_max": 120,
  "max_response_bytes": 20000000,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "redirects_allowed": false,
  "write_operations_allowed": false,
  "personal_data_allowed": false,
  "secret_values_exposed": false,
  "fixed_api_hosts": [
    "stac.overturemaps.org",
    "overturemaps-us-west-2.s3.us-west-2.amazonaws.com"
  ],
  "bbox_area_square_degrees_max": 4.0,
  "features_per_ticket_max": 1000,
  "anonymous_object_storage_only": true,
  "whole_world_download_allowed": false,
  "arbitrary_s3_paths_allowed": false,
  "arbitrary_feature_types_allowed": false
}
```

## OECD Data Explorer SDMX (`oecd`)

- 状态：`启用`
- 说明：通过 OECD 官方免费 SDMX REST API 读取经济、社会、贸易、产业、就业、教育、能源与公共治理统计。
- 目录策略：开放固定的数据流、结构、代码表和数据查询操作；所有路径组件、维度键、格式、时间范围和响应体积均受白名单约束。
- 执行策略：仅允许对 sdmx.oecd.org/public/rest/v1 发起一次 HTTPS GET；不跟随重定向，不接受任意 URL、请求头或写操作。
- 票据前缀：`[api-oecd]`
- Secret环境变量名：`无`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`624be06b79018397cd4bf8865f29577681a5a505b76cfd539b494d517a1125a9`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地 OECD SDMX 安全能力目录，不访问上游. | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `list-dataflows` | 读取 OECD 当前公开数据流目录. | `format` |

`list-dataflows` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string",
      "enum": [
        "json"
      ]
    }
  }
}
```

| `get-dataflow` | 读取指定 OECD SDMX 数据流定义. | `agency, flow, version, format` |

`get-dataflow` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "agency": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,127}$"
    },
    "flow": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,127}$"
    },
    "version": {
      "type": "string",
      "pattern": "^(latest|[0-9]+(?:\\.[0-9]+){0,3})$"
    },
    "format": {
      "type": "string",
      "enum": [
        "json"
      ]
    }
  },
  "required": [
    "agency",
    "flow"
  ]
}
```

| `get-datastructure` | 读取指定 OECD SDMX 数据结构定义. | `agency, structure_id, version, format` |

`get-datastructure` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "agency": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,127}$"
    },
    "structure_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,127}$"
    },
    "version": {
      "type": "string",
      "pattern": "^(latest|[0-9]+(?:\\.[0-9]+){0,3})$"
    },
    "format": {
      "type": "string",
      "enum": [
        "json"
      ]
    }
  },
  "required": [
    "agency",
    "structure_id"
  ]
}
```

| `get-codelist` | 读取指定 OECD SDMX 代码表. | `agency, codelist_id, version, format` |

`get-codelist` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "agency": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,127}$"
    },
    "codelist_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,127}$"
    },
    "version": {
      "type": "string",
      "pattern": "^(latest|[0-9]+(?:\\.[0-9]+){0,3})$"
    },
    "format": {
      "type": "string",
      "enum": [
        "json"
      ]
    }
  },
  "required": [
    "agency",
    "codelist_id"
  ]
}
```

| `get-data` | 按固定数据流、维度键和时间范围读取 OECD 统计数据. | `agency, flow, version, key, start_period, end_period, dimension_at_observation, format` |

`get-data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "agency": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,127}$"
    },
    "flow": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,127}$"
    },
    "version": {
      "type": "string",
      "pattern": "^(latest|[0-9]+(?:\\.[0-9]+){0,3})$"
    },
    "key": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500,
      "pattern": "^[A-Za-z0-9+._@-]+$"
    },
    "start_period": {
      "type": "string",
      "minLength": 4,
      "maxLength": 32,
      "pattern": "^[0-9]{4}(?:-[A-Za-z0-9]{1,8})?$"
    },
    "end_period": {
      "type": "string",
      "minLength": 4,
      "maxLength": 32,
      "pattern": "^[0-9]{4}(?:-[A-Za-z0-9]{1,8})?$"
    },
    "dimension_at_observation": {
      "type": "string",
      "enum": [
        "AllDimensions",
        "TimeDimension",
        "MeasureDimension"
      ]
    },
    "format": {
      "type": "string",
      "enum": [
        "json",
        "csv"
      ]
    }
  },
  "required": [
    "agency",
    "flow",
    "key"
  ]
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "timeout_seconds_max": 120,
  "max_response_bytes": 20000000,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "redirects_allowed": false,
  "write_operations_allowed": false,
  "personal_data_allowed": false,
  "secret_values_exposed": false,
  "fixed_api_host": "sdmx.oecd.org",
  "fixed_api_prefix": "/public/rest/v1",
  "rate_limit_policy": "single-request-per-ticket",
  "arbitrary_sdmx_resource_types_allowed": false,
  "bulk_download_endpoints_allowed": false
}
```

## AlphaFeed 中国与全球证券行情 (`alphafeed`)

- 状态：`启用`
- 说明：通过 AlphaFeed 官方 Python SDK 读取 A股、ETF、美股和港股行情、K线、分时、盘口、标的信息与复权因子。
- 目录策略：固定开放官方 SDK 的 9 类只读数据操作；一个票据只执行一个固定 SDK 方法，批量标的数量和 K 线条数受硬限制。
- 执行策略：API Key 仅由 GitHub Actions 后端注入；不接受客户端密钥、任意方法、任意主机、交易、下单、WebSocket 或写操作。
- 票据前缀：`[api-alphafeed]`
- Secret环境变量名：`ALPHAFEED_API_KEY`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`f74609460418fd7363f97d939eefa8b1c711801f9c9ecf61fcb77fcf465ba289`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地 AlphaFeed 安全能力目录，不访问上游. | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `quotes` | 按证券代码或固定标的池读取 A股、美股、港股和 ETF 实时行情. | `symbols, universe` |

`quotes` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbols": {
      "type": "array",
      "minItems": 1,
      "maxItems": 100,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Z0-9][A-Z0-9.-]{0,31}\\.(?:SH|SZ|BJ|US|HK)$"
      }
    },
    "universe": {
      "type": "string",
      "enum": [
        "CN_Stock",
        "US_Stock",
        "HK_Stock",
        "CN_ETF"
      ]
    }
  }
}
```

| `klines` | 读取单只证券的分钟、日、周或月 K 线. | `symbol, period, count, adjust` |

`klines` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "pattern": "^[A-Z0-9][A-Z0-9.-]{0,31}\\.(?:SH|SZ|BJ|US|HK)$"
    },
    "period": {
      "type": "string",
      "enum": [
        "1m",
        "5m",
        "15m",
        "30m",
        "60m",
        "1d",
        "1w",
        "1mo"
      ]
    },
    "count": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000
    },
    "adjust": {
      "type": "string",
      "enum": [
        "forward",
        "backward",
        "forward_additive",
        "backward_additive",
        "none"
      ]
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `klines-batch` | 批量读取最多 20 只证券的有限 K 线. | `symbols, period, count, adjust` |

`klines-batch` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbols": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Z0-9][A-Z0-9.-]{0,31}\\.(?:SH|SZ|BJ|US|HK)$"
      }
    },
    "period": {
      "type": "string",
      "enum": [
        "1m",
        "5m",
        "15m",
        "30m",
        "60m",
        "1d",
        "1w",
        "1mo"
      ]
    },
    "count": {
      "type": "integer",
      "minimum": 1,
      "maximum": 500
    },
    "adjust": {
      "type": "string",
      "enum": [
        "forward",
        "backward",
        "forward_additive",
        "backward_additive",
        "none"
      ]
    }
  },
  "required": [
    "symbols"
  ]
}
```

| `intraday` | 读取单只证券当日 1 分钟或 5 分钟分时. | `symbol, period` |

`intraday` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "pattern": "^[A-Z0-9][A-Z0-9.-]{0,31}\\.(?:SH|SZ|BJ|US|HK)$"
    },
    "period": {
      "type": "string",
      "enum": [
        "1m",
        "5m"
      ]
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `intraday-batch` | 批量读取最多 20 只证券的当日分时. | `symbols, period` |

`intraday-batch` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbols": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Z0-9][A-Z0-9.-]{0,31}\\.(?:SH|SZ|BJ|US|HK)$"
      }
    },
    "period": {
      "type": "string",
      "enum": [
        "1m",
        "5m"
      ]
    }
  },
  "required": [
    "symbols"
  ]
}
```

| `depth` | 读取单只 A 股证券五档盘口. | `symbol` |

`depth` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "pattern": "^[A-Z0-9][A-Z0-9.-]{0,31}\\.(?:SH|SZ|BJ|US|HK)$"
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `instrument` | 读取单只证券基础信息. | `symbol` |

`instrument` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "pattern": "^[A-Z0-9][A-Z0-9.-]{0,31}\\.(?:SH|SZ|BJ|US|HK)$"
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `instruments-batch` | 批量读取最多 100 只证券基础信息. | `symbols` |

`instruments-batch` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbols": {
      "type": "array",
      "minItems": 1,
      "maxItems": 100,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Z0-9][A-Z0-9.-]{0,31}\\.(?:SH|SZ|BJ|US|HK)$"
      }
    }
  },
  "required": [
    "symbols"
  ]
}
```

| `adjustment-factors` | 批量读取最多 100 只证券复权因子. | `symbols` |

`adjustment-factors` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbols": {
      "type": "array",
      "minItems": 1,
      "maxItems": 100,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Z0-9][A-Z0-9.-]{0,31}\\.(?:SH|SZ|BJ|US|HK)$"
      }
    }
  },
  "required": [
    "symbols"
  ]
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "timeout_seconds_max": 120,
  "max_response_bytes": 20000000,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "redirects_allowed": false,
  "write_operations_allowed": false,
  "personal_data_allowed": false,
  "secret_values_exposed": false,
  "fixed_api_host": "api.alphafeed.org",
  "sdk_version": "0.1.4",
  "sdk_calls_per_ticket_max": 1,
  "symbols_per_batch_max": 100,
  "kline_batch_symbols_max": 20,
  "kline_rows_per_symbol_max": 1000,
  "arbitrary_sdk_methods_allowed": false,
  "client_supplied_api_key_allowed": false,
  "websocket_allowed": false,
  "trading_or_order_execution_allowed": false
}
```

## WHO GHO OData 全球卫生数据 (`who-gho-odata`)

- 状态：`启用`
- 说明：通过世界卫生组织 Global Health Observatory 公开 OData 接口读取全球卫生指标、维度、国家、地区和历史观测值。
- 目录策略：开放8项固定免密只读操作；指标代码、维度、国家、地区、年份、性别和分页均受Schema约束，不接受任意OData表达式。
- 执行策略：每张票据最多一次固定HTTPS GET；不跟随重定向，不接受任意URL、主机、路径、请求头、$filter、$select、$expand、函数或写操作。
- 票据前缀：`[intel-who-gho]`
- Secret环境变量名：`无`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`484b5f3f91587357dd6391cf06859362f9f8a100a09270ce55fd505e82225fed`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地 WHO GHO OData 安全能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "maxProperties": 0
}
```

| `list-dimensions` | 读取 WHO GHO 可用维度目录。 | `top, skip` |

`list-dimensions` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "top": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000,
      "default": 100
    },
    "skip": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000,
      "default": 0
    }
  }
}
```

| `list-dimension-values` | 读取固定公共维度的代码和值。 | `dimension, top, skip` |

`list-dimension-values` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "dimension": {
      "type": "string",
      "enum": [
        "COUNTRY",
        "REGION",
        "SEX",
        "AGEGROUP",
        "GHO",
        "PUBLISHSTATE",
        "WORLDBANKINCOMEGROUP"
      ]
    },
    "top": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000,
      "default": 100
    },
    "skip": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000,
      "default": 0
    }
  },
  "required": [
    "dimension"
  ]
}
```

| `list-indicators` | 分页读取 WHO GHO 指标代码和名称目录。 | `top, skip` |

`list-indicators` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "top": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000,
      "default": 100
    },
    "skip": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000,
      "default": 0
    }
  }
}
```

| `search-indicators` | 按受控文本条件搜索 WHO GHO 指标名称。 | `query, match, top, skip` |

`search-indicators` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 2,
      "maxLength": 120,
      "pattern": "^[A-Za-z0-9 .,/()%-]+$"
    },
    "match": {
      "type": "string",
      "enum": [
        "contains",
        "exact"
      ],
      "default": "contains"
    },
    "top": {
      "type": "integer",
      "minimum": 1,
      "maximum": 200,
      "default": 50
    },
    "skip": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000,
      "default": 0
    }
  },
  "required": [
    "query"
  ]
}
```

| `get-indicator-data` | 按指标、国家或地区、年份和性别读取 WHO GHO 观测值；只构造固定 OData 条件。 | `indicator_code, country, region, year_from, year_to, sex, top, skip` |

`get-indicator-data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "indicator_code": {
      "type": "string",
      "minLength": 2,
      "maxLength": 128,
      "pattern": "^[A-Z0-9][A-Z0-9_]{1,127}$"
    },
    "country": {
      "type": "string",
      "pattern": "^[A-Z]{3}$"
    },
    "region": {
      "type": "string",
      "enum": [
        "AFR",
        "AMR",
        "SEAR",
        "EUR",
        "EMR",
        "WPR",
        "GLOBAL"
      ]
    },
    "year_from": {
      "type": "integer",
      "minimum": 1900,
      "maximum": 2100
    },
    "year_to": {
      "type": "integer",
      "minimum": 1900,
      "maximum": 2100
    },
    "sex": {
      "type": "string",
      "enum": [
        "BTSX",
        "MLE",
        "FMLE"
      ]
    },
    "top": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000,
      "default": 100
    },
    "skip": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000,
      "default": 0
    }
  },
  "required": [
    "indicator_code"
  ]
}
```

| `get-countries` | 读取 WHO GHO 国家代码和值目录。 | `top, skip` |

`get-countries` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "top": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000,
      "default": 100
    },
    "skip": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000,
      "default": 0
    }
  }
}
```

| `get-regions` | 读取 WHO GHO 地区代码和值目录。 | `top, skip` |

`get-regions` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "top": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000,
      "default": 100
    },
    "skip": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000,
      "default": 0
    }
  }
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "timeout_seconds_max": 120,
  "max_response_bytes": 20000000,
  "provider_concurrency_max": 1,
  "transient_retry_max": 0,
  "fixed_api_host": "ghoapi.azureedge.net",
  "fixed_api_prefix": "/api",
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "arbitrary_odata_filters_allowed": false,
  "arbitrary_odata_select_allowed": false,
  "arbitrary_odata_expand_allowed": false,
  "arbitrary_odata_functions_allowed": false,
  "redirects_allowed": false,
  "write_operations_allowed": false,
  "personal_data_allowed": false,
  "secret_values_exposed": false,
  "authentication_required": false,
  "automatic_pagination_allowed": false,
  "whole_database_download_allowed": false,
  "legacy_endpoint_migration_watch_required": true
}
```

## Mediastack 全球新闻情报 (`mediastack`)

- 状态：`启用`
- 说明：通过 Mediastack 官方 REST API读取全球新闻文章与新闻来源目录；固定只读、单请求、受限分页，不自动抓取文章正文。
- 目录策略：固定开放5项能力：1项本地目录、最新新闻、关键词新闻检索、历史新闻检索和来源目录；每张票据最多一次请求，limit不超过100，不自动翻页。
- 执行策略：API Key仅由GitHub Repository Secret注入为access_key查询参数；不接受客户端凭据、任意URL、任意路径、任意请求头、写操作、Webhook、后台轮询或文章正文抓取。
- 票据前缀：`[intel-mediastack]`
- Secret环境变量名：`MEDIASTACK_API_KEY`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`8b5110b8cf56941059252e4aa874b6f9d8e1771c1a520a2c663a92d5b27e8c32`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地 Mediastack 安全能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "maxProperties": 0
}
```

| `latest-news` | 读取最新或延迟新闻，可按国家、语言、分类和来源过滤。 | `countries, languages, categories, sources, sort, limit, offset` |

`latest-news` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "countries": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[a-z]{2}$"
      }
    },
    "languages": {
      "type": "array",
      "minItems": 1,
      "maxItems": 13,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[a-z]{2}$"
      }
    },
    "categories": {
      "type": "array",
      "minItems": 1,
      "maxItems": 7,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "enum": [
          "general",
          "business",
          "entertainment",
          "health",
          "science",
          "sports",
          "technology"
        ]
      }
    },
    "sources": {
      "type": "array",
      "minItems": 1,
      "maxItems": 50,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^-?[A-Za-z0-9._-]{1,100}$"
      }
    },
    "sort": {
      "type": "string",
      "enum": [
        "published_desc",
        "published_asc",
        "popularity"
      ],
      "default": "published_desc"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 25
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000,
      "default": 0
    }
  },
  "maxProperties": 7
}
```

| `search-news` | 按关键词检索新闻，可组合国家、语言、分类、来源、排序和受限分页。 | `keywords, countries, languages, categories, sources, sort, limit, offset` |

`search-news` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "keywords": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    },
    "countries": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[a-z]{2}$"
      }
    },
    "languages": {
      "type": "array",
      "minItems": 1,
      "maxItems": 13,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[a-z]{2}$"
      }
    },
    "categories": {
      "type": "array",
      "minItems": 1,
      "maxItems": 7,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "enum": [
          "general",
          "business",
          "entertainment",
          "health",
          "science",
          "sports",
          "technology"
        ]
      }
    },
    "sources": {
      "type": "array",
      "minItems": 1,
      "maxItems": 50,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^-?[A-Za-z0-9._-]{1,100}$"
      }
    },
    "sort": {
      "type": "string",
      "enum": [
        "published_desc",
        "published_asc",
        "popularity"
      ],
      "default": "published_desc"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 25
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000,
      "default": 0
    }
  },
  "maxProperties": 8,
  "required": [
    "keywords"
  ]
}
```

| `historical-news` | 按单日或日期区间检索历史新闻；历史权限取决于 Mediastack 套餐。 | `date, keywords, countries, languages, categories, sources, sort, limit, offset` |

`historical-news` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "date": {
      "type": "string",
      "pattern": "^\\d{4}-\\d{2}-\\d{2}(,\\d{4}-\\d{2}-\\d{2})?$"
    },
    "keywords": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    },
    "countries": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[a-z]{2}$"
      }
    },
    "languages": {
      "type": "array",
      "minItems": 1,
      "maxItems": 13,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[a-z]{2}$"
      }
    },
    "categories": {
      "type": "array",
      "minItems": 1,
      "maxItems": 7,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "enum": [
          "general",
          "business",
          "entertainment",
          "health",
          "science",
          "sports",
          "technology"
        ]
      }
    },
    "sources": {
      "type": "array",
      "minItems": 1,
      "maxItems": 50,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^-?[A-Za-z0-9._-]{1,100}$"
      }
    },
    "sort": {
      "type": "string",
      "enum": [
        "published_desc",
        "published_asc",
        "popularity"
      ],
      "default": "published_desc"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 25
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000,
      "default": 0
    }
  },
  "maxProperties": 9,
  "required": [
    "date"
  ]
}
```

| `list-sources` | 读取 Mediastack 支持的新闻来源目录，可按关键词、国家、语言和分类过滤。 | `search, countries, languages, categories, limit, offset` |

`list-sources` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "search": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "countries": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[a-z]{2}$"
      }
    },
    "languages": {
      "type": "array",
      "minItems": 1,
      "maxItems": 13,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[a-z]{2}$"
      }
    },
    "categories": {
      "type": "array",
      "minItems": 1,
      "maxItems": 7,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "enum": [
          "general",
          "business",
          "entertainment",
          "health",
          "science",
          "sports",
          "technology"
        ]
      }
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 25
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000,
      "default": 0
    }
  },
  "maxProperties": 6
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "provider_concurrency_max": 1,
  "transient_retry_max": 1,
  "timeout_seconds_max": 90,
  "max_response_bytes": 10000000,
  "max_rows": 100,
  "max_offset": 10000,
  "max_date_range_days": 366,
  "free_plan_requests_per_month": 100,
  "free_plan_delayed_news": true,
  "historical_news_plan_dependent": true,
  "commercial_use_plan_dependent": true,
  "fixed_api_host": "api.mediastack.com",
  "fixed_paths": [
    "/v1/news",
    "/v1/sources"
  ],
  "arbitrary_urls_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "client_supplied_credentials_allowed": false,
  "redirects_allowed": false,
  "automatic_pagination_allowed": false,
  "background_monitoring_allowed": false,
  "article_body_fetching_allowed": false,
  "write_operations_allowed": false,
  "secret_values_exposed": false
}
```

## Statistics of the World 全球统计 (`statistics-of-the-world`)

- 状态：`启用`
- 说明：聚合 IMF、World Bank、WHO、FRED、ECB、UN 等来源的国家、指标、历史、排名和高频统计数据。
- 目录策略：仅开放官方文档明确列出的固定只读 JSON 端点；聚合数据必须保留上游来源、年份、单位和许可元数据，不得替代原始官方源作为唯一证据。
- 执行策略：每张票最多一次 HTTPS GET；可匿名调用，若配置 SOTW_API_KEY 则仅通过后端 X-API-Key 请求头发送；禁止任意 URL、路径、请求头、批量全库下载、自然语言聊天和写操作。
- 票据前缀：`[intel-sotw]`
- Secret环境变量名：`无`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`e4fdbd93284bf812c7ef289c616a13e57404ef72f80f7006637db67bde654c4d`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地安全能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `list-countries` | 列出国家及地区元数据。 | `无` |

`list-countries` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `get-country` | 读取一个 ISO Alpha-3 国家及其最新指标。 | `country` |

`get-country` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "country"
  ],
  "properties": {
    "country": {
      "type": "string",
      "pattern": "^[A-Z]{3}$"
    }
  }
}
```

| `list-indicators` | 列出公开指标目录及分类。 | `无` |

`list-indicators` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `get-indicator` | 读取一个指标的元数据及国家横截面。 | `indicator` |

`get-indicator` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "indicator"
  ],
  "properties": {
    "indicator": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{1,127}$"
    }
  }
}
```

| `get-history` | 读取一个指标与一个国家的历史时间序列。 | `indicator, country` |

`get-history` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "indicator",
    "country"
  ],
  "properties": {
    "indicator": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{1,127}$"
    },
    "country": {
      "type": "string",
      "pattern": "^[A-Z]{3}$"
    }
  }
}
```

| `get-rankings` | 按指标读取国家排名，结果数量受限。 | `indicator, limit` |

`get-rankings` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "indicator"
  ],
  "properties": {
    "indicator": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{1,127}$"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 500
    }
  }
}
```

| `search-indicators` | 按受限关键词搜索指标。 | `query` |

`search-indicators` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "query"
  ],
  "properties": {
    "query": {
      "type": "string",
      "minLength": 2,
      "maxLength": 100,
      "pattern": "^[A-Za-z0-9 ()%+.,/_-]+$"
    }
  }
}
```

| `compare-countries` | 并列比较 2 至 10 个 ISO Alpha-3 国家。 | `countries` |

`compare-countries` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "countries"
  ],
  "properties": {
    "countries": {
      "type": "array",
      "minItems": 2,
      "maxItems": 10,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Z]{3}$"
      }
    }
  }
}
```

| `list-series` | 列出高频统计序列及许可元数据，不下载全量观测。 | `无` |

`list-series` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `get-series` | 读取一个高频序列，可限定国家、起始日期和仅最新值。 | `series, geo, from, latest` |

`get-series` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "series"
  ],
  "properties": {
    "series": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{1,127}$"
    },
    "geo": {
      "type": "string",
      "pattern": "^[A-Z]{3}$"
    },
    "from": {
      "type": "string",
      "format": "date"
    },
    "latest": {
      "type": "boolean"
    }
  }
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "provider_concurrency_max": 1,
  "timeout_seconds_max": 60,
  "max_response_bytes": 10000000,
  "max_rows": 500,
  "max_compare_countries": 10,
  "free_key_requests_per_day_documented": 1000,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "client_supplied_credentials_allowed": false,
  "automatic_pagination_allowed": false,
  "bulk_download_allowed": false,
  "natural_language_chat_allowed": false,
  "redirects_allowed": false,
  "write_operations_allowed": false,
  "personal_data_allowed": false,
  "secret_values_exposed": false,
  "fixed_api_host": "statisticsoftheworld.com",
  "fixed_api_prefixes": [
    "/api/v1",
    "/api/v2"
  ]
}
```

## AISstream 全球船舶实时AIS (`aisstream`)

- 状态：`启用`
- 说明：通过 AISstream.io 的固定 WSS 端点，在严格时间、区域、消息数和响应大小边界内读取实时船舶AIS消息。
- 目录策略：开放4项固定只读操作；API Key仅由GitHub Actions后端注入，客户端不得提交或覆盖。
- 执行策略：每张票据最多建立1条WSS连接，持续不超过30秒，最多4个有限区域、20个MMSI、8种消息类型和200条消息；禁止全球无限流、后台常驻和转发。
- 票据前缀：`[intel-aisstream]`
- Secret环境变量名：`AISSTREAM_API_KEY`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`e15b0c24f1a4fba31b3fa4d53c06cf3a2239e44e2c47808c39224b4cc89388bb`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地AISstream安全能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "maxProperties": 0
}
```

| `collect-messages` | 按有限地理区域、可选MMSI和消息类型，在短时间窗口内收集实时AIS消息。 | `bounding_boxes, mmsi, message_types, duration_seconds, max_messages` |

`collect-messages` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "bounding_boxes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 4,
      "items": {
        "type": "array",
        "minItems": 2,
        "maxItems": 2,
        "items": {
          "type": "array",
          "minItems": 2,
          "maxItems": 2,
          "prefixItems": [
            {
              "type": "number",
              "minimum": -90,
              "maximum": 90
            },
            {
              "type": "number",
              "minimum": -180,
              "maximum": 180
            }
          ]
        }
      }
    },
    "mmsi": {
      "type": "array",
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[0-9]{9}$"
      }
    },
    "message_types": {
      "type": "array",
      "maxItems": 8,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "enum": [
          "AddressedBinaryMessage",
          "AddressedSafetyMessage",
          "AidsToNavigationReport",
          "AssignedModeCommand",
          "BaseStationReport",
          "BinaryAcknowledge",
          "BinaryBroadcastMessage",
          "ChannelManagement",
          "CoordinatedUTCInquiry",
          "DataLinkManagementMessage",
          "DataLinkManagementMessageData",
          "ExtendedClassBPositionReport",
          "GnssBroadcastBinaryMessage",
          "GroupAssignmentCommand",
          "Interrogation",
          "LongRangeAisBroadcastMessage",
          "MultiSlotBinaryMessage",
          "PositionReport",
          "SafetyBroadcastMessage",
          "ShipStaticData",
          "SingleSlotBinaryMessage",
          "StandardClassBPositionReport",
          "StandardSearchAndRescueAircraftReport",
          "StaticDataReport",
          "UnknownMessage"
        ]
      }
    },
    "duration_seconds": {
      "type": "integer",
      "minimum": 1,
      "maximum": 30,
      "default": 10
    },
    "max_messages": {
      "type": "integer",
      "minimum": 1,
      "maximum": 200,
      "default": 50
    }
  },
  "required": [
    "bounding_boxes"
  ]
}
```

| `collect-vessel-positions` | 按有限地理区域和可选MMSI收集Class A/B位置类消息。 | `bounding_boxes, mmsi, duration_seconds, max_messages` |

`collect-vessel-positions` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "bounding_boxes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 4,
      "items": {
        "type": "array",
        "minItems": 2,
        "maxItems": 2,
        "items": {
          "type": "array",
          "minItems": 2,
          "maxItems": 2,
          "prefixItems": [
            {
              "type": "number",
              "minimum": -90,
              "maximum": 90
            },
            {
              "type": "number",
              "minimum": -180,
              "maximum": 180
            }
          ]
        }
      }
    },
    "mmsi": {
      "type": "array",
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[0-9]{9}$"
      }
    },
    "duration_seconds": {
      "type": "integer",
      "minimum": 1,
      "maximum": 30,
      "default": 10
    },
    "max_messages": {
      "type": "integer",
      "minimum": 1,
      "maximum": 200,
      "default": 50
    }
  },
  "required": [
    "bounding_boxes"
  ]
}
```

| `collect-vessel-static` | 按有限地理区域和可选MMSI收集船舶静态资料类消息。 | `bounding_boxes, mmsi, duration_seconds, max_messages` |

`collect-vessel-static` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "bounding_boxes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 4,
      "items": {
        "type": "array",
        "minItems": 2,
        "maxItems": 2,
        "items": {
          "type": "array",
          "minItems": 2,
          "maxItems": 2,
          "prefixItems": [
            {
              "type": "number",
              "minimum": -90,
              "maximum": 90
            },
            {
              "type": "number",
              "minimum": -180,
              "maximum": 180
            }
          ]
        }
      }
    },
    "mmsi": {
      "type": "array",
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[0-9]{9}$"
      }
    },
    "duration_seconds": {
      "type": "integer",
      "minimum": 1,
      "maximum": 30,
      "default": 10
    },
    "max_messages": {
      "type": "integer",
      "minimum": 1,
      "maximum": 200,
      "default": 50
    }
  },
  "required": [
    "bounding_boxes"
  ]
}
```

限制：

```json
{
  "connections_per_ticket_max": 1,
  "stream_duration_seconds_max": 30,
  "timeout_seconds_max": 45,
  "max_response_bytes": 20000000,
  "provider_concurrency_max": 1,
  "transient_retry_max": 0,
  "fixed_api_host": "stream.aisstream.io",
  "fixed_websocket_path": "/v0/stream",
  "bounding_boxes_max": 4,
  "bounding_box_area_square_degrees_max": 400,
  "combined_bounding_box_area_square_degrees_max": 800,
  "mmsi_filter_count_max": 20,
  "message_type_filter_count_max": 8,
  "messages_per_ticket_max": 200,
  "worldwide_subscription_allowed": false,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "client_supplied_credentials_allowed": false,
  "background_streaming_allowed": false,
  "stream_relay_allowed": false,
  "write_operations_allowed": false,
  "trading_or_order_execution_allowed": false,
  "secret_values_exposed": false,
  "authentication_required": true
}
```

## 互联网档案馆 Internet Archive (`internet-archive`)

- 状态：`启用`
- 说明：通过Internet Archive公开接口搜索数字馆藏、读取项目元数据和文件目录，并查询Wayback网页存档可用性与有限捕获记录。
- 目录策略：开放6项固定免密只读操作；不开放上传、修改、删除、借阅、登录、任意文件下载或网页回放抓取。
- 执行策略：每张票据最多一次固定HTTPS GET；搜索、字段、分页、排序、标识符、URL、时间范围和返回行数均受Schema约束，不跟随重定向。
- 票据前缀：`[intel-internet-archive]`
- Secret环境变量名：`无`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`3dbf98875d81988ebb952fbd73f9b8506685ad121b3e226ab05d397ccee2b8df`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地互联网档案馆安全能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "maxProperties": 0
}
```

| `search-items` | 通过Advanced Search API按受控查询、字段、分页和排序搜索馆藏元数据。 | `query, rows, page, fields, sort` |

`search-items` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    },
    "rows": {
      "type": "integer",
      "minimum": 1,
      "maximum": 200,
      "default": 50
    },
    "page": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000,
      "default": 1
    },
    "fields": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z][A-Za-z0-9_]{0,63}$"
      }
    },
    "sort": {
      "type": "string",
      "enum": [
        "downloads desc",
        "downloads asc",
        "date desc",
        "date asc",
        "addeddate desc",
        "addeddate asc",
        "titleSorter asc",
        "titleSorter desc"
      ],
      "default": "downloads desc"
    }
  },
  "required": [
    "query"
  ]
}
```

| `get-item-metadata` | 按固定identifier读取项目元数据。 | `identifier` |

`get-item-metadata` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "identifier": {
      "type": "string",
      "minLength": 1,
      "maxLength": 255,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,254}$"
    }
  },
  "required": [
    "identifier"
  ]
}
```

| `list-item-files` | 按固定identifier读取项目文件目录及校验元数据，不下载文件内容。 | `identifier` |

`list-item-files` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "identifier": {
      "type": "string",
      "minLength": 1,
      "maxLength": 255,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,254}$"
    }
  },
  "required": [
    "identifier"
  ]
}
```

| `wayback-availability` | 查询指定HTTP(S) URL在Wayback Machine中是否有可用快照。 | `url, timestamp` |

`wayback-availability` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "url": {
      "type": "string",
      "minLength": 8,
      "maxLength": 1000,
      "pattern": "^https?://[^\\s]+$"
    },
    "timestamp": {
      "type": "string",
      "pattern": "^[0-9]{4,14}$"
    }
  },
  "required": [
    "url"
  ]
}
```

| `wayback-captures` | 通过固定CDX端点读取指定URL的有限去重成功捕获记录。 | `url, from_timestamp, to_timestamp, limit` |

`wayback-captures` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "url": {
      "type": "string",
      "minLength": 8,
      "maxLength": 1000,
      "pattern": "^https?://[^\\s]+$"
    },
    "from_timestamp": {
      "type": "string",
      "pattern": "^[0-9]{4,14}$"
    },
    "to_timestamp": {
      "type": "string",
      "pattern": "^[0-9]{4,14}$"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 200,
      "default": 50
    }
  },
  "required": [
    "url"
  ]
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "timeout_seconds_max": 120,
  "max_response_bytes": 20000000,
  "provider_concurrency_max": 1,
  "transient_retry_max": 0,
  "fixed_api_hosts": [
    "archive.org",
    "web.archive.org"
  ],
  "fixed_paths": [
    "/advancedsearch.php",
    "/metadata/{identifier}",
    "/wayback/available",
    "/cdx/search/cdx"
  ],
  "search_rows_max": 200,
  "search_page_max": 1000,
  "metadata_files_returned_max": 500,
  "wayback_capture_rows_max": 200,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "redirects_allowed": false,
  "file_downloads_allowed": false,
  "archived_page_body_fetching_allowed": false,
  "bulk_collection_download_allowed": false,
  "uploads_allowed": false,
  "write_operations_allowed": false,
  "authentication_required": false,
  "secret_values_exposed": false,
  "automatic_pagination_allowed": false
}
```

## Marketstack 全球股票 EOD 与历史数据 (`marketstack`)

- 状态：`启用`
- 说明：通过 Marketstack v2 固定 HTTPS REST 端点读取免费计划可用的全球股票日线、最多一年历史、拆股、分红以及证券、交易所、币种和时区目录。
- 目录策略：仅开放免费计划明确提供的11项固定只读操作；禁止任意URL、路径、请求头、客户端密钥、盘中与实时轮询、付费数据面、自动翻页、交易和写入。
- 执行策略：MARKETSTACK_ACCESS_KEY仅由GitHub Actions后端注入查询参数；每张票据只发送一次GET请求且不自动重试，最多5个证券代码，历史跨度最多366天，limit最大100。
- 票据前缀：`[intel-marketstack]`
- Secret环境变量名：`MARKETSTACK_ACCESS_KEY`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`115f416ff077df84439e8edec577f10821914b0cb9a24744ca182807b05c0a2d`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地Marketstack安全能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "maxProperties": 0
}
```

| `eod-latest` | 读取最多5个证券的最新可用日终OHLCV与复权数据。 | `symbols, limit, offset` |

`eod-latest` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbols": {
      "type": "array",
      "minItems": 1,
      "maxItems": 5,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,31}$"
      }
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 100
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000,
      "default": 0
    }
  },
  "required": [
    "symbols"
  ]
}
```

| `eod-history` | 读取最多5个证券、最大366天范围的历史日终OHLCV与复权数据。 | `symbols, date_from, date_to, sort, limit, offset` |

`eod-history` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbols": {
      "type": "array",
      "minItems": 1,
      "maxItems": 5,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,31}$"
      }
    },
    "date_from": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "date_to": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "sort": {
      "type": "string",
      "enum": [
        "ASC",
        "DESC",
        "asc",
        "desc"
      ],
      "default": "DESC"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 100
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000,
      "default": 0
    }
  },
  "required": [
    "symbols"
  ]
}
```

| `eod-by-date` | 读取指定交易日、最多5个证券的日终数据。 | `date, symbols, limit, offset` |

`eod-by-date` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "symbols": {
      "type": "array",
      "minItems": 1,
      "maxItems": 5,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,31}$"
      }
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 100
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000,
      "default": 0
    }
  },
  "required": [
    "date",
    "symbols"
  ]
}
```

| `dividends` | 读取最多5个证券、最大366天范围的历史分红记录。 | `symbols, date_from, date_to, limit, offset` |

`dividends` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbols": {
      "type": "array",
      "minItems": 1,
      "maxItems": 5,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,31}$"
      }
    },
    "date_from": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "date_to": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 100
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000,
      "default": 0
    }
  },
  "required": [
    "symbols"
  ]
}
```

| `splits` | 读取最多5个证券、最大366天范围的历史拆股记录。 | `symbols, date_from, date_to, limit, offset` |

`splits` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbols": {
      "type": "array",
      "minItems": 1,
      "maxItems": 5,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,31}$"
      }
    },
    "date_from": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "date_to": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 100
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000,
      "default": 0
    }
  },
  "required": [
    "symbols"
  ]
}
```

| `tickers-list` | 按有限搜索词和可选交易所代码读取Marketstack证券目录。 | `search, exchange, limit, offset` |

`tickers-list` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "search": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100
    },
    "exchange": {
      "type": "string",
      "pattern": "^[A-Za-z0-9]{2,12}$"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 100
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000,
      "default": 0
    }
  }
}
```

| `ticker-info` | 读取单一证券代码的静态目录和交易所信息。 | `symbol` |

`ticker-info` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "symbol": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,31}$"
    }
  },
  "required": [
    "symbol"
  ]
}
```

| `exchanges-list` | 读取Marketstack支持的交易所目录。 | `limit, offset` |

`exchanges-list` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 100
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000,
      "default": 0
    }
  }
}
```

| `currencies-list` | 读取Marketstack支持的币种目录。 | `limit, offset` |

`currencies-list` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 100
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000,
      "default": 0
    }
  }
}
```

| `timezones-list` | 读取Marketstack支持的时区目录。 | `limit, offset` |

`timezones-list` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 100
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000,
      "default": 0
    }
  }
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "transient_retry_max": 0,
  "provider_concurrency_max": 1,
  "timeout_seconds_max": 60,
  "max_response_bytes": 10000000,
  "rows_per_request_max": 100,
  "symbols_per_ticket_max": 5,
  "historical_span_days_max": 366,
  "free_plan_requests_per_month": 100,
  "fixed_api_host": "api.marketstack.com",
  "fixed_api_prefix": "/v2",
  "automatic_pagination_allowed": false,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "arbitrary_query_parameters_allowed": false,
  "client_supplied_credentials_allowed": false,
  "intraday_or_realtime_operations_allowed": false,
  "paid_plan_only_operations_allowed": false,
  "websocket_allowed": false,
  "write_operations_allowed": false,
  "trading_or_order_execution_allowed": false,
  "secret_values_exposed": false,
  "authentication_required": true
}
```

## NASA Open APIs 与 Earthdata GIBS (`nasa`)

- 状态：`启用`
- 说明：通过 NASA 官方固定只读端点读取天文图片、近地小行星、空间天气、EPIC 地球影像元数据、NASA 图像资料库以及 Earthdata GIBS 地球观测图层和单瓦片影像。
- 目录策略：只开放25项固定只读操作；旧 Earth API 与 Mars Rover Photos API 已归档且不开放；禁止任意URL、任意主机、任意路径、批量影像下载、后台轮询、上传和写入。
- 执行策略：每张票据最多一次上游GET且不自动重试；api.nasa.gov操作由后端注入NASA_API_KEY；NASA Image Library和GIBS免密；所有响应受字节上限约束。
- 票据前缀：`[intel-nasa]`
- Secret环境变量名：`NASA_API_KEY`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`4215636150fb5168bf1a45d7c7433ac6f6ec014d1e03c758548b459956f9c679`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地 NASA 安全能力目录，不访问上游. | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `apod` | 读取 NASA Astronomy Picture of the Day 单日、有限日期范围或有限随机结果. | `date, start_date, end_date, count, thumbs` |

`apod` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "start_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "end_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "count": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10
    },
    "thumbs": {
      "type": "boolean"
    }
  }
}
```

| `neo-feed` | 按最多7天接近日期窗口读取近地小行星列表. | `start_date, end_date` |

`neo-feed` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "start_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "end_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  },
  "required": [
    "start_date"
  ]
}
```

| `neo-lookup` | 按 NASA JPL 小天体 ID 查询单个近地天体. | `asteroid_id` |

`neo-lookup` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asteroid_id": {
      "type": "string",
      "pattern": "^[0-9]{1,20}$"
    }
  },
  "required": [
    "asteroid_id"
  ]
}
```

| `neo-browse` | 分页浏览近地天体目录. | `page, size` |

`neo-browse` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "page": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000
    },
    "size": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    }
  }
}
```

| `donki-cme` | 读取日冕物质抛射事件. | `start_date, end_date` |

`donki-cme` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "start_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "end_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  }
}
```

| `donki-cme-analysis` | 读取日冕物质抛射分析结果. | `start_date, end_date, most_accurate_only, complete_entry_only, speed, half_angle, catalog` |

`donki-cme-analysis` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "start_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "end_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "most_accurate_only": {
      "type": "boolean"
    },
    "complete_entry_only": {
      "type": "boolean"
    },
    "speed": {
      "type": "integer",
      "minimum": 0,
      "maximum": 5000
    },
    "half_angle": {
      "type": "integer",
      "minimum": 0,
      "maximum": 180
    },
    "catalog": {
      "type": "string",
      "enum": [
        "ALL",
        "SWRC_CATALOG",
        "JANG_ET_AL_CATALOG"
      ]
    }
  }
}
```

| `donki-gst` | 读取地磁暴事件. | `start_date, end_date` |

`donki-gst` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "start_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "end_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  }
}
```

| `donki-ips` | 读取行星际激波事件. | `start_date, end_date, location, catalog` |

`donki-ips` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "start_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "end_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "location": {
      "type": "string",
      "enum": [
        "ALL",
        "Earth",
        "MESSENGER",
        "STEREO A",
        "STEREO B"
      ]
    },
    "catalog": {
      "type": "string",
      "enum": [
        "ALL",
        "SWRC_CATALOG",
        "WINSLOW_MESSENGER_ICME_CATALOG"
      ]
    }
  }
}
```

| `donki-flr` | 读取太阳耀斑事件. | `start_date, end_date` |

`donki-flr` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "start_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "end_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  }
}
```

| `donki-sep` | 读取太阳高能粒子事件. | `start_date, end_date` |

`donki-sep` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "start_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "end_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  }
}
```

| `donki-mpc` | 读取磁层顶穿越事件. | `start_date, end_date` |

`donki-mpc` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "start_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "end_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  }
}
```

| `donki-rbe` | 读取辐射带增强事件. | `start_date, end_date` |

`donki-rbe` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "start_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "end_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  }
}
```

| `donki-hss` | 读取高速太阳风流事件. | `start_date, end_date` |

`donki-hss` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "start_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "end_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  }
}
```

| `donki-notifications` | 读取 DONKI 空间天气通知. | `start_date, end_date, type` |

`donki-notifications` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "start_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "end_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "type": {
      "type": "string",
      "enum": [
        "all",
        "FLR",
        "SEP",
        "CME",
        "IPS",
        "MPC",
        "GST",
        "RBE",
        "report"
      ]
    }
  }
}
```

| `epic-natural` | 读取 EPIC 自然色地球影像元数据，可限定单日. | `date` |

`epic-natural` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  }
}
```

| `epic-enhanced` | 读取 EPIC 增强色地球影像元数据，可限定单日. | `date` |

`epic-enhanced` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  }
}
```

| `nasa-images-search` | 检索 NASA 图像与视频资料库单页结果. | `q, media_type, year_start, year_end, page` |

`nasa-images-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "q": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "media_type": {
      "type": "string",
      "enum": [
        "image",
        "video",
        "audio"
      ]
    },
    "year_start": {
      "type": "integer",
      "minimum": 1900,
      "maximum": 2100
    },
    "year_end": {
      "type": "integer",
      "minimum": 1900,
      "maximum": 2100
    },
    "page": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    }
  },
  "required": [
    "q"
  ]
}
```

| `nasa-images-asset` | 读取单一 NASA ID 的媒体资产清单. | `nasa_id` |

`nasa-images-asset` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "nasa_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$"
    }
  },
  "required": [
    "nasa_id"
  ]
}
```

| `nasa-images-metadata` | 读取单一 NASA ID 的原始元数据. | `nasa_id` |

`nasa-images-metadata` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "nasa_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$"
    }
  },
  "required": [
    "nasa_id"
  ]
}
```

| `nasa-images-captions` | 读取单一 NASA ID 的字幕或文本轨道. | `nasa_id` |

`nasa-images-captions` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "nasa_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$"
    }
  },
  "required": [
    "nasa_id"
  ]
}
```

| `gibs-wmts-capabilities` | 读取 Earthdata GIBS WMTS 能力 XML. | `projection, catalog` |

`gibs-wmts-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "projection": {
      "type": "string",
      "enum": [
        "epsg4326",
        "epsg3857"
      ]
    },
    "catalog": {
      "type": "string",
      "enum": [
        "best",
        "nrt",
        "std",
        "all"
      ]
    }
  }
}
```

| `gibs-wms-capabilities` | 读取 Earthdata GIBS WMS 1.3.0 能力 XML. | `projection, catalog` |

`gibs-wms-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "projection": {
      "type": "string",
      "enum": [
        "epsg4326",
        "epsg3857"
      ]
    },
    "catalog": {
      "type": "string",
      "enum": [
        "best",
        "nrt",
        "std",
        "all"
      ]
    }
  }
}
```

| `gibs-layer-metadata` | 读取单一 GIBS 图层元数据 JSON. | `layer` |

`gibs-layer-metadata` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "layer": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.-]{0,199}$"
    }
  },
  "required": [
    "layer"
  ]
}
```

| `gibs-tile` | 读取单一 Earthdata GIBS WMTS 影像瓦片. | `projection, catalog, layer, date, tile_matrix_set, tile_matrix, tile_row, tile_col, format` |

`gibs-tile` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "projection": {
      "type": "string",
      "enum": [
        "epsg4326",
        "epsg3857"
      ]
    },
    "catalog": {
      "type": "string",
      "enum": [
        "best",
        "nrt",
        "std",
        "all"
      ]
    },
    "layer": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.-]{0,199}$"
    },
    "date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "tile_matrix_set": {
      "type": "string",
      "enum": [
        "31.25m",
        "62.5m",
        "125m",
        "250m",
        "500m",
        "1km",
        "2km",
        "4km",
        "8km",
        "16km"
      ]
    },
    "tile_matrix": {
      "type": "integer",
      "minimum": 0,
      "maximum": 30
    },
    "tile_row": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000
    },
    "tile_col": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000
    },
    "format": {
      "type": "string",
      "enum": [
        "jpg",
        "png"
      ]
    }
  },
  "required": [
    "layer",
    "date",
    "tile_matrix_set",
    "tile_matrix",
    "tile_row",
    "tile_col",
    "format"
  ]
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "transient_retry_max": 0,
  "provider_concurrency_max": 1,
  "timeout_seconds_max": 60,
  "max_response_bytes": 10000000,
  "apod_date_span_days_max": 31,
  "apod_random_count_max": 10,
  "neo_feed_span_days_max": 7,
  "donki_date_span_days_max": 31,
  "nasa_images_page_max": 100,
  "gibs_tiles_per_ticket_max": 1,
  "fixed_hosts": [
    "api.nasa.gov",
    "images-api.nasa.gov",
    "gibs.earthdata.nasa.gov"
  ],
  "automatic_pagination_allowed": false,
  "bulk_download_allowed": false,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "client_supplied_credentials_allowed": false,
  "background_polling_allowed": false,
  "archived_earth_api_allowed": false,
  "archived_mars_rover_api_allowed": false,
  "write_operations_allowed": false,
  "secret_values_exposed": false
}
```

## 挪威气象研究所 Geosatellite (`metno-geosatellite`)

- 状态：`启用`
- 说明：通过 MET Norway Geosatellite 1.4 固定只读端点获取地球同步气象卫星静态图、欧洲动画和按区域过滤的可用影像清单。
- 目录策略：只开放4项固定只读操作；固定访问api.met.no；不开放任意URL、任意主机、任意路径、small缩略图、批量全目录下载、后台轮询或写入。
- 执行策略：每张票据最多一次HTTPS GET，不自动重试或翻页；使用可识别User-Agent；遵守Expires、Last-Modified和ETag缓存头；响应受30MB硬上限约束。
- 票据前缀：`[intel-metno-geosatellite]`
- Secret环境变量名：`无`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`c6002056463a8b97d0cb136bceaa50a12355fd64b6113e0bc79f33d41e0f88ac`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地MET Norway Geosatellite安全能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `get-static-image` | 获取指定区域、光谱和可选UTC时刻的PNG卫星图；未给time时返回最新图。 | `area, spectrum, time` |

`get-static-image` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "area": {
      "type": "string",
      "enum": [
        "africa",
        "atlantic_ocean",
        "europe",
        "global",
        "mediterranean"
      ]
    },
    "spectrum": {
      "type": "string",
      "enum": [
        "infrared",
        "visible"
      ],
      "default": "infrared"
    },
    "time": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:00Z$"
    }
  },
  "required": [
    "area"
  ]
}
```

| `get-europe-animation` | 获取欧洲区域的MP4或WebM卫星动画。 | `format` |

`get-europe-animation` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string",
      "enum": [
        "mp4",
        "webm"
      ],
      "default": "mp4"
    }
  }
}
```

| `list-available` | 按必选区域和可选光谱读取静态PNG影像可用清单，禁止无过滤全目录请求。 | `area, spectrum` |

`list-available` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "area": {
      "type": "string",
      "enum": [
        "africa",
        "atlantic_ocean",
        "europe",
        "global",
        "mediterranean"
      ]
    },
    "spectrum": {
      "type": "string",
      "enum": [
        "infrared",
        "visible"
      ]
    }
  },
  "required": [
    "area"
  ]
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "transient_retry_max": 0,
  "provider_concurrency_max": 1,
  "timeout_seconds_max": 90,
  "max_response_bytes": 30000000,
  "fixed_api_host": "api.met.no",
  "supported_areas": [
    "africa",
    "atlantic_ocean",
    "europe",
    "global",
    "mediterranean"
  ],
  "supported_spectra": [
    "infrared",
    "visible"
  ],
  "supported_video_area": "europe",
  "supported_video_formats": [
    "mp4",
    "webm"
  ],
  "small_size_images_allowed": false,
  "unfiltered_availability_listing_allowed": false,
  "automatic_pagination_allowed": false,
  "bulk_download_allowed": false,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "client_supplied_user_agent_allowed": false,
  "background_polling_allowed": false,
  "write_operations_allowed": false,
  "secret_values_exposed": false,
  "fixed_paths": [
    "/weatherapi/geosatellite/1.4/",
    "/weatherapi/geosatellite/1.4/europe.mp4",
    "/weatherapi/geosatellite/1.4/europe.webm",
    "/weatherapi/geosatellite/1.4/available.json"
  ]
}
```

## 哥白尼数据空间 Copernicus CDSE (`copernicus-cdse`)

- 状态：`启用`
- 说明：通过 Copernicus Data Space Ecosystem 的公开 STAC 目录和 Sentinel Hub Processing API 搜索、定位并渲染 Sentinel 卫星影像。
- 目录策略：固定开放7项只读能力：本地目录、公开STAC集合/检索/单产品元数据，以及Sentinel-2 L2A真彩色、假彩色和NDVI PNG渲染。
- 执行策略：STAC目录操作免密；渲染操作使用Repository Variable中的OAuth Client ID和Repository Secret中的Client Secret。每票据最多一次目录请求，或一次令牌请求加一次处理请求；不自动重试、翻页、批量下载或写入。
- 票据前缀：`[intel-copernicus]`
- Secret环境变量名：`COPERNICUS_CLIENT_SECRET`（仅名称）
- Repository Variable名：`COPERNICUS_CLIENT_ID`（仅名称）
- 提供方SHA-256：`69acc2742d25b169c9a97e8d2e5e86b550cc2922bbb1e6a8563a2af8c7078fee`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地Copernicus安全能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `stac-list-collections` | 读取公开CDSE STAC集合目录，受返回条数和体积上限约束。 | `无` |

`stac-list-collections` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `stac-search-items` | 按集合、WGS84范围、时间和可选云量搜索最新Sentinel产品元数据。 | `collection, bbox, start_time, end_time, cloud_cover_max, limit` |

`stac-search-items` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "collection": {
      "type": "string",
      "enum": [
        "sentinel-1-grd",
        "sentinel-2-l1c",
        "sentinel-2-l2a",
        "sentinel-2-global-mosaics"
      ]
    },
    "bbox": {
      "type": "array",
      "minItems": 4,
      "maxItems": 4,
      "items": {
        "type": "number"
      }
    },
    "start_time": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
    },
    "end_time": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
    },
    "cloud_cover_max": {
      "type": "number",
      "minimum": 0,
      "maximum": 100
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 20
    }
  },
  "required": [
    "collection",
    "bbox",
    "start_time",
    "end_time"
  ]
}
```

| `stac-get-item` | 读取白名单集合中的单个STAC产品元数据。 | `collection, item_id` |

`stac-get-item` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "collection": {
      "type": "string",
      "enum": [
        "sentinel-1-grd",
        "sentinel-2-l1c",
        "sentinel-2-l2a",
        "sentinel-2-global-mosaics"
      ]
    },
    "item_id": {
      "type": "string",
      "minLength": 3,
      "maxLength": 256,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{2,255}$"
    }
  },
  "required": [
    "collection",
    "item_id"
  ]
}
```

| `render-true-color-png` | 使用固定真彩色脚本渲染指定区域和时间段的Sentinel-2 L2A PNG。 | `bbox, start_time, end_time, cloud_cover_max, mosaicking_order, width, height` |

`render-true-color-png` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "bbox": {
      "type": "array",
      "minItems": 4,
      "maxItems": 4,
      "items": {
        "type": "number"
      }
    },
    "start_time": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
    },
    "end_time": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
    },
    "cloud_cover_max": {
      "type": "number",
      "minimum": 0,
      "maximum": 100
    },
    "mosaicking_order": {
      "type": "string",
      "enum": [
        "leastCC",
        "mostRecent",
        "leastRecent"
      ]
    },
    "width": {
      "type": "integer",
      "minimum": 64,
      "maximum": 2048
    },
    "height": {
      "type": "integer",
      "minimum": 64,
      "maximum": 2048
    }
  },
  "required": [
    "bbox",
    "start_time",
    "end_time"
  ]
}
```

| `render-false-color-png` | 使用固定近红外假彩色脚本渲染Sentinel-2 L2A PNG，用于突出植被和地表差异。 | `bbox, start_time, end_time, cloud_cover_max, mosaicking_order, width, height` |

`render-false-color-png` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "bbox": {
      "type": "array",
      "minItems": 4,
      "maxItems": 4,
      "items": {
        "type": "number"
      }
    },
    "start_time": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
    },
    "end_time": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
    },
    "cloud_cover_max": {
      "type": "number",
      "minimum": 0,
      "maximum": 100
    },
    "mosaicking_order": {
      "type": "string",
      "enum": [
        "leastCC",
        "mostRecent",
        "leastRecent"
      ]
    },
    "width": {
      "type": "integer",
      "minimum": 64,
      "maximum": 2048
    },
    "height": {
      "type": "integer",
      "minimum": 64,
      "maximum": 2048
    }
  },
  "required": [
    "bbox",
    "start_time",
    "end_time"
  ]
}
```

| `render-ndvi-png` | 使用固定NDVI脚本渲染Sentinel-2 L2A植被指数PNG。 | `bbox, start_time, end_time, cloud_cover_max, mosaicking_order, width, height` |

`render-ndvi-png` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "bbox": {
      "type": "array",
      "minItems": 4,
      "maxItems": 4,
      "items": {
        "type": "number"
      }
    },
    "start_time": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
    },
    "end_time": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
    },
    "cloud_cover_max": {
      "type": "number",
      "minimum": 0,
      "maximum": 100
    },
    "mosaicking_order": {
      "type": "string",
      "enum": [
        "leastCC",
        "mostRecent",
        "leastRecent"
      ]
    },
    "width": {
      "type": "integer",
      "minimum": 64,
      "maximum": 2048
    },
    "height": {
      "type": "integer",
      "minimum": 64,
      "maximum": 2048
    }
  },
  "required": [
    "bbox",
    "start_time",
    "end_time"
  ]
}
```

限制：

```json
{
  "requests_per_ticket_max": 2,
  "catalog_requests_per_ticket_max": 1,
  "processing_requests_per_ticket_max": 1,
  "oauth_requests_per_ticket_max": 1,
  "provider_concurrency_max": 1,
  "transient_retry_max": 0,
  "timeout_seconds_max": 180,
  "max_response_bytes": 30000000,
  "max_rows": 100,
  "bbox_span_degrees_max": 1.0,
  "render_time_span_days_max": 90,
  "search_time_span_days_max": 366,
  "render_width_max": 2048,
  "render_height_max": 2048,
  "render_pixels_max": 4194304,
  "supported_collections": [
    "sentinel-1-grd",
    "sentinel-2-l1c",
    "sentinel-2-l2a",
    "sentinel-2-global-mosaics"
  ],
  "render_collection": "sentinel-2-l2a",
  "fixed_stac_host": "stac.dataspace.copernicus.eu",
  "fixed_processing_host": "sh.dataspace.copernicus.eu",
  "fixed_identity_host": "identity.dataspace.copernicus.eu",
  "automatic_pagination_allowed": false,
  "automatic_retry_allowed": false,
  "bulk_download_allowed": false,
  "native_product_download_allowed": false,
  "batch_processing_allowed": false,
  "arbitrary_evalscripts_allowed": false,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "client_supplied_credentials_allowed": false,
  "oauth_token_persistence_allowed": false,
  "write_operations_allowed": false,
  "secret_values_exposed": false
}
```

## 美国能源信息署 EIA 能源数据 (`eia`)

- 状态：`启用`
- 说明：通过美国能源信息署 EIA 官方 API v2 读取能源数据树、路线元数据、Facet 值、结构化能源时间序列和兼容的历史 Series ID，覆盖电力、石油、天然气、煤炭、核能、可再生能源、国际能源、州级能源、短期展望等公开数据。
- 目录策略：固定访问 api.eia.gov 的 API v2；开放受约束的层级路线发现、元数据、Facet、数据查询和 Series ID 兼容读取。禁止任意主机、完整 URL、路径穿越、客户端密钥、任意请求头、XML、大文件批量下载、后台抓取和写操作。
- 执行策略：EIA_API_KEY 仅由 GitHub Actions 后端注入 URL 查询参数。每张票据最多一次 GET，不自动重试或翻页；数据返回最多5000行，限制路线深度、列数、Facet数量和值数量、排序规则、超时和响应体积。EIA 会在调试回显中包含请求参数，执行器会递归清除密钥后才写入 Snapshot 和 Artifact。
- 票据前缀：`[intel-eia]`
- Secret环境变量名：`EIA_API_KEY`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`08f4919b0570ec00deba2ce943d66d1386e53cf372e0a9589b42e95539a00e29`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地 EIA 安全能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "maxProperties": 0
}
```

| `api-root` | 读取 EIA API v2 根目录，发现当前顶级能源数据路线。 | `无` |

`api-root` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "maxProperties": 0
}
```

| `route-metadata` | 读取指定 EIA 层级路线的子路线、频率、Facet、数据列、时间范围和说明元数据。 | `route` |

`route-metadata` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "route": {
      "type": "string",
      "minLength": 1,
      "maxLength": 519,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._/-]*$"
    }
  },
  "required": [
    "route"
  ]
}
```

| `facet-values` | 读取指定路线和 Facet 的可用过滤值，支持有限 offset/length。 | `route, facet, offset, length` |

`facet-values` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "route": {
      "type": "string",
      "minLength": 1,
      "maxLength": 519,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._/-]*$"
    },
    "facet": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$"
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000000,
      "default": 0
    },
    "length": {
      "type": "integer",
      "minimum": 1,
      "maximum": 5000,
      "default": 500
    }
  },
  "required": [
    "route",
    "facet"
  ]
}
```

| `route-data` | 按路线、数据列、频率、时间、Facet、排序和分页参数读取 EIA 结构化能源数据。 | `route, data, frequency, facets, start, end, sort, offset, length` |

`route-data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "route": {
      "type": "string",
      "minLength": 1,
      "maxLength": 519,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._/-]*$"
    },
    "data": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$"
      }
    },
    "frequency": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$"
    },
    "facets": {
      "type": "object",
      "maxProperties": 12,
      "additionalProperties": {
        "type": "array",
        "minItems": 1,
        "maxItems": 50,
        "uniqueItems": true,
        "items": {
          "type": "string",
          "minLength": 1,
          "maxLength": 200
        }
      }
    },
    "start": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9:+._-]{0,31}$"
    },
    "end": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9:+._-]{0,31}$"
    },
    "sort": {
      "type": "array",
      "maxItems": 4,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "column",
          "direction"
        ],
        "properties": {
          "column": {
            "type": "string",
            "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$"
          },
          "direction": {
            "type": "string",
            "enum": [
              "asc",
              "desc",
              "ASC",
              "DESC"
            ]
          }
        }
      }
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000000,
      "default": 0
    },
    "length": {
      "type": "integer",
      "minimum": 1,
      "maximum": 5000,
      "default": 500
    }
  },
  "required": [
    "route",
    "data"
  ]
}
```

| `series-by-id` | 通过 API v2 的 seriesid 兼容路线读取一个历史 EIA APIv1 Series ID。 | `series_id` |

`series-by-id` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "series_id": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,199}$"
    }
  },
  "required": [
    "series_id"
  ]
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "transient_retry_max": 0,
  "provider_concurrency_max": 1,
  "timeout_seconds_max": 60,
  "max_response_bytes": 20000000,
  "rows_per_response_max": 5000,
  "route_segments_max": 8,
  "data_columns_max": 20,
  "facet_keys_max": 12,
  "facet_values_per_key_max": 50,
  "facet_values_total_max": 100,
  "sort_rules_max": 4,
  "fixed_api_host": "api.eia.gov",
  "fixed_api_prefix": "/v2",
  "automatic_retry_allowed": false,
  "automatic_pagination_allowed": false,
  "bulk_download_allowed": false,
  "xml_output_allowed": false,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "path_traversal_allowed": false,
  "arbitrary_headers_allowed": false,
  "client_supplied_credentials_allowed": false,
  "background_crawling_allowed": false,
  "write_operations_allowed": false,
  "secret_values_exposed": false,
  "authentication_required": true
}
```

## 联合国 UN Comtrade 全球贸易数据 (`un-comtrade`)

- 状态：`启用`
- 说明：通过联合国统计司 UN Comtrade 官方 API 读取全球货物与服务贸易、关税行、数据可用性、最近发布、元数据、贸易差额以及报告方和伙伴方参考代码。
- 目录策略：固定访问 comtradeapi.un.org；开放无需密钥的预览和固定参考表，以及使用独立 Subscription Key 的免费数据接口。禁止 Bulk、Async、文件下载、任意 URL、任意主机、客户端密钥、任意请求头、自动翻页和写操作。
- 执行策略：每张票据只发送一次 GET，不自动重试或翻页；预览最多500条，正式数据、关税行和贸易差额在情报中心内硬限制为5000条。最多12个时期、5个报告方、20个商品代码、10个伙伴和20 MB响应。Subscription Key仅由GitHub Actions后端注入并在落盘前递归清除。
- 票据前缀：`[intel-un-comtrade]`
- Secret环境变量名：`UN_COMTRADE_API_KEY`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`45d51c68e656c8338e7ba5f39f18368c28f78e548d6c54cd9da400efd115aa2e`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地UN Comtrade安全能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "maxProperties": 0
}
```

| `preview-trade` | 无需密钥预览一个时期和一个商品代码的货物或服务贸易数据，最多500条。 | `type_code, frequency, classification, periods, reporter_codes, commodity_codes, flow_codes, partner_codes, partner2_codes, customs_codes, mode_of_transport_codes, max_records, breakdown_mode, count_only, include_descriptions` |

`preview-trade` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "type_code": {
      "type": "string",
      "enum": [
        "C",
        "S",
        "c",
        "s"
      ]
    },
    "frequency": {
      "type": "string",
      "enum": [
        "A",
        "M",
        "a",
        "m"
      ]
    },
    "classification": {
      "type": "string",
      "pattern": "^[A-Za-z][A-Za-z0-9]{0,7}$"
    },
    "periods": {
      "type": "array",
      "minItems": 1,
      "maxItems": 1,
      "uniqueItems": true,
      "items": {
        "type": [
          "string",
          "integer"
        ]
      }
    },
    "reporter_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 5,
      "uniqueItems": true,
      "items": {
        "type": "integer",
        "minimum": 0,
        "maximum": 9999
      }
    },
    "commodity_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 1,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^(?:TOTAL|[A-Za-z0-9.]{1,20})$"
      }
    },
    "flow_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 6,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z][A-Za-z0-9]{0,5}$"
      }
    },
    "partner_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 10,
      "uniqueItems": true,
      "items": {
        "type": "integer",
        "minimum": 0,
        "maximum": 9999
      }
    },
    "partner2_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 5,
      "uniqueItems": true,
      "items": {
        "type": "integer",
        "minimum": 0,
        "maximum": 9999
      }
    },
    "customs_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 10,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$"
      }
    },
    "mode_of_transport_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 10,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$"
      }
    },
    "max_records": {
      "type": "integer",
      "minimum": 1,
      "maximum": 500,
      "default": 500
    },
    "breakdown_mode": {
      "type": "string",
      "enum": [
        "classic",
        "plus"
      ]
    },
    "count_only": {
      "type": "boolean"
    },
    "include_descriptions": {
      "type": "boolean"
    }
  },
  "required": [
    "type_code",
    "frequency",
    "classification",
    "periods",
    "reporter_codes",
    "commodity_codes",
    "flow_codes"
  ]
}
```

| `final-trade` | 使用免费Subscription Key读取正式货物或服务贸易数据，情报中心单次最多5000条。 | `type_code, frequency, classification, periods, reporter_codes, commodity_codes, flow_codes, partner_codes, partner2_codes, customs_codes, mode_of_transport_codes, max_records, breakdown_mode, count_only, include_descriptions` |

`final-trade` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "type_code": {
      "type": "string",
      "enum": [
        "C",
        "S",
        "c",
        "s"
      ]
    },
    "frequency": {
      "type": "string",
      "enum": [
        "A",
        "M",
        "a",
        "m"
      ]
    },
    "classification": {
      "type": "string",
      "pattern": "^[A-Za-z][A-Za-z0-9]{0,7}$"
    },
    "periods": {
      "type": "array",
      "minItems": 1,
      "maxItems": 12,
      "uniqueItems": true,
      "items": {
        "type": [
          "string",
          "integer"
        ]
      }
    },
    "reporter_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 5,
      "uniqueItems": true,
      "items": {
        "type": "integer",
        "minimum": 0,
        "maximum": 9999
      }
    },
    "commodity_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^(?:TOTAL|[A-Za-z0-9.]{1,20})$"
      }
    },
    "flow_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 6,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z][A-Za-z0-9]{0,5}$"
      }
    },
    "partner_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 10,
      "uniqueItems": true,
      "items": {
        "type": "integer",
        "minimum": 0,
        "maximum": 9999
      }
    },
    "partner2_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 5,
      "uniqueItems": true,
      "items": {
        "type": "integer",
        "minimum": 0,
        "maximum": 9999
      }
    },
    "customs_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 10,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$"
      }
    },
    "mode_of_transport_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 10,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$"
      }
    },
    "max_records": {
      "type": "integer",
      "minimum": 1,
      "maximum": 5000,
      "default": 5000
    },
    "breakdown_mode": {
      "type": "string",
      "enum": [
        "classic",
        "plus"
      ]
    },
    "count_only": {
      "type": "boolean"
    },
    "include_descriptions": {
      "type": "boolean"
    }
  },
  "required": [
    "type_code",
    "frequency",
    "classification",
    "periods",
    "reporter_codes",
    "commodity_codes",
    "flow_codes"
  ]
}
```

| `tariffline-trade` | 读取正式货物关税行数据，禁止服务类型，单次最多5000条。 | `type_code, frequency, classification, periods, reporter_codes, commodity_codes, flow_codes, partner_codes, partner2_codes, customs_codes, mode_of_transport_codes, max_records, breakdown_mode, count_only, include_descriptions` |

`tariffline-trade` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "type_code": {
      "type": "string",
      "enum": [
        "C",
        "c"
      ]
    },
    "frequency": {
      "type": "string",
      "enum": [
        "A",
        "M",
        "a",
        "m"
      ]
    },
    "classification": {
      "type": "string",
      "pattern": "^[A-Za-z][A-Za-z0-9]{0,7}$"
    },
    "periods": {
      "type": "array",
      "minItems": 1,
      "maxItems": 12,
      "uniqueItems": true,
      "items": {
        "type": [
          "string",
          "integer"
        ]
      }
    },
    "reporter_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 5,
      "uniqueItems": true,
      "items": {
        "type": "integer",
        "minimum": 0,
        "maximum": 9999
      }
    },
    "commodity_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^(?:TOTAL|[A-Za-z0-9.]{1,20})$"
      }
    },
    "flow_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 6,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z][A-Za-z0-9]{0,5}$"
      }
    },
    "partner_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 10,
      "uniqueItems": true,
      "items": {
        "type": "integer",
        "minimum": 0,
        "maximum": 9999
      }
    },
    "partner2_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 5,
      "uniqueItems": true,
      "items": {
        "type": "integer",
        "minimum": 0,
        "maximum": 9999
      }
    },
    "customs_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 10,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$"
      }
    },
    "mode_of_transport_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 10,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$"
      }
    },
    "max_records": {
      "type": "integer",
      "minimum": 1,
      "maximum": 5000,
      "default": 5000
    },
    "breakdown_mode": {
      "type": "string",
      "enum": [
        "classic",
        "plus"
      ]
    },
    "count_only": {
      "type": "boolean"
    },
    "include_descriptions": {
      "type": "boolean"
    }
  },
  "required": [
    "type_code",
    "frequency",
    "classification",
    "periods",
    "reporter_codes",
    "commodity_codes",
    "flow_codes"
  ]
}
```

| `data-availability` | 查询正式贸易数据集可用性，可按时期、报告方和发布日期过滤。 | `type_code, frequency, classification, periods, reporter_codes, published_date_from, published_date_to` |

`data-availability` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "type_code": {
      "type": "string",
      "enum": [
        "C",
        "S",
        "c",
        "s"
      ]
    },
    "frequency": {
      "type": "string",
      "enum": [
        "A",
        "M",
        "a",
        "m"
      ]
    },
    "classification": {
      "type": "string",
      "pattern": "^[A-Za-z][A-Za-z0-9]{0,7}$"
    },
    "periods": {
      "type": "array",
      "minItems": 1,
      "maxItems": 12,
      "uniqueItems": true,
      "items": {
        "type": [
          "string",
          "integer"
        ]
      }
    },
    "reporter_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 10,
      "uniqueItems": true,
      "items": {
        "type": "integer",
        "minimum": 0,
        "maximum": 9999
      }
    },
    "published_date_from": {
      "type": "string",
      "format": "date"
    },
    "published_date_to": {
      "type": "string",
      "format": "date"
    }
  },
  "required": [
    "type_code",
    "frequency",
    "classification"
  ]
}
```

| `live-updates` | 读取UN Comtrade最近数据发布和修订进度。 | `无` |

`live-updates` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "maxProperties": 0
}
```

| `metadata` | 读取指定数据集的发布说明、脚注和元数据信息。 | `type_code, frequency, classification, periods, reporter_codes` |

`metadata` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "type_code": {
      "type": "string",
      "enum": [
        "C",
        "S",
        "c",
        "s"
      ]
    },
    "frequency": {
      "type": "string",
      "enum": [
        "A",
        "M",
        "a",
        "m"
      ]
    },
    "classification": {
      "type": "string",
      "pattern": "^[A-Za-z][A-Za-z0-9]{0,7}$"
    },
    "periods": {
      "type": "array",
      "minItems": 1,
      "maxItems": 12,
      "uniqueItems": true,
      "items": {
        "type": [
          "string",
          "integer"
        ]
      }
    },
    "reporter_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 5,
      "uniqueItems": true,
      "items": {
        "type": "integer",
        "minimum": 0,
        "maximum": 9999
      }
    }
  },
  "required": [
    "type_code",
    "frequency",
    "classification",
    "periods",
    "reporter_codes"
  ]
}
```

| `trade-balance` | 读取货物贸易差额工具结果，单次最多5000条。 | `type_code, frequency, classification, periods, reporter_codes, commodity_codes, partner_codes, partner2_codes, customs_codes, mode_of_transport_codes, max_records, breakdown_mode, include_descriptions` |

`trade-balance` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "type_code": {
      "type": "string",
      "enum": [
        "C",
        "c"
      ]
    },
    "frequency": {
      "type": "string",
      "enum": [
        "A",
        "M",
        "a",
        "m"
      ]
    },
    "classification": {
      "type": "string",
      "pattern": "^[A-Za-z][A-Za-z0-9]{0,7}$"
    },
    "periods": {
      "type": "array",
      "minItems": 1,
      "maxItems": 12,
      "uniqueItems": true,
      "items": {
        "type": [
          "string",
          "integer"
        ]
      }
    },
    "reporter_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 5,
      "uniqueItems": true,
      "items": {
        "type": "integer",
        "minimum": 0,
        "maximum": 9999
      }
    },
    "commodity_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^(?:TOTAL|[A-Za-z0-9.]{1,20})$"
      }
    },
    "partner_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 10,
      "uniqueItems": true,
      "items": {
        "type": "integer",
        "minimum": 0,
        "maximum": 9999
      }
    },
    "partner2_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 5,
      "uniqueItems": true,
      "items": {
        "type": "integer",
        "minimum": 0,
        "maximum": 9999
      }
    },
    "customs_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 10,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$"
      }
    },
    "mode_of_transport_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 10,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$"
      }
    },
    "max_records": {
      "type": "integer",
      "minimum": 1,
      "maximum": 5000,
      "default": 5000
    },
    "breakdown_mode": {
      "type": "string",
      "enum": [
        "classic",
        "plus"
      ]
    },
    "include_descriptions": {
      "type": "boolean"
    }
  },
  "required": [
    "type_code",
    "frequency",
    "classification",
    "periods",
    "reporter_codes",
    "commodity_codes"
  ]
}
```

| `reporters-reference` | 读取固定的UN Comtrade报告国家和地区参考代码表。 | `无` |

`reporters-reference` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "maxProperties": 0
}
```

| `partners-reference` | 读取固定的UN Comtrade伙伴国家和地区参考代码表。 | `无` |

`partners-reference` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "maxProperties": 0
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "transient_retry_max": 0,
  "provider_concurrency_max": 1,
  "timeout_seconds_max": 60,
  "max_response_bytes": 20000000,
  "preview_records_max": 500,
  "records_per_request_max": 5000,
  "official_free_records_per_call_max": 100000,
  "free_api_calls_per_day": 500,
  "periods_per_ticket_max": 12,
  "reporters_per_ticket_max": 5,
  "commodity_codes_per_ticket_max": 20,
  "partners_per_ticket_max": 10,
  "fixed_api_host": "comtradeapi.un.org",
  "fixed_data_prefix": "/data/v1",
  "fixed_public_prefix": "/public/v1",
  "keyless_preview_allowed": true,
  "automatic_retry_allowed": false,
  "automatic_pagination_allowed": false,
  "bulk_api_allowed": false,
  "async_api_allowed": false,
  "file_downloads_allowed": false,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "client_supplied_credentials_allowed": false,
  "background_crawling_allowed": false,
  "write_operations_allowed": false,
  "secret_values_exposed": false,
  "authentication_required": true
}
```

## OpenSky Network 全球航空状态与航迹数据 (`opensky-network`)

- 状态：`启用`
- 说明：通过OpenSky Network官方REST API读取受限范围内的实时飞机状态、最近状态、本人接收器状态、航班、机场到离港和单机航迹。
- 目录策略：固定访问opensky-network.org和auth.opensky-network.org；最新状态支持匿名读取，其余能力使用OAuth2 Client Credentials。禁止全球无过滤状态查询、Trino历史查询、批量下载、任意URL、任意主机、客户端凭据、后台轮询和写操作。
- 执行策略：每张票据最多一次OAuth令牌POST和一次业务GET，不自动重试或翻页。状态查询必须按最多20个ICAO24或最大400平方度边界框过滤；历史状态限最近1小时；航班区间严格遵循官方2小时/2天限制；航迹限最近30天。
- 票据前缀：`[intel-opensky]`
- Secret环境变量名：`OPEN_SKY_CLIENT_SECRET`（仅名称）
- Repository Variable名：`OPEN_SKY_CLIENT_ID`（仅名称）
- 提供方SHA-256：`218564dbd30dff0ffbad39429d90b6fcbca9c35ecfdebad2ff12bd87629477b8`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地OpenSky安全能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `states-current` | 按ICAO24或最大400平方度边界框读取最新状态向量；可匿名或使用OAuth。 | `icao24, lamin, lomin, lamax, lomax, extended` |

`states-current` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "icao24": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[0-9A-Fa-f]{6}$"
      }
    },
    "lamin": {
      "type": "number",
      "minimum": -90,
      "maximum": 90
    },
    "lomin": {
      "type": "number",
      "minimum": -180,
      "maximum": 180
    },
    "lamax": {
      "type": "number",
      "minimum": -90,
      "maximum": 90
    },
    "lomax": {
      "type": "number",
      "minimum": -180,
      "maximum": 180
    },
    "extended": {
      "type": "boolean"
    }
  }
}
```

| `states-recent` | 使用OAuth读取最近一小时内的状态向量。 | `icao24, lamin, lomin, lamax, lomax, extended, time` |

`states-recent` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "icao24": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[0-9A-Fa-f]{6}$"
      }
    },
    "lamin": {
      "type": "number",
      "minimum": -90,
      "maximum": 90
    },
    "lomin": {
      "type": "number",
      "minimum": -180,
      "maximum": 180
    },
    "lamax": {
      "type": "number",
      "minimum": -90,
      "maximum": 90
    },
    "lomax": {
      "type": "number",
      "minimum": -180,
      "maximum": 180
    },
    "extended": {
      "type": "boolean"
    },
    "time": {
      "type": "integer",
      "minimum": 1
    }
  },
  "required": [
    "time"
  ]
}
```

| `states-own` | 使用OAuth读取本人接收器观测到的状态向量，必须按接收器或ICAO24过滤。 | `icao24, serials, time` |

`states-own` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "icao24": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[0-9A-Fa-f]{6}$"
      }
    },
    "serials": {
      "type": "array",
      "minItems": 1,
      "maxItems": 10,
      "uniqueItems": true,
      "items": {
        "type": "integer",
        "minimum": 1,
        "maximum": 2147483647
      }
    },
    "time": {
      "type": "integer",
      "minimum": 0
    }
  }
}
```

| `flights-interval` | 使用OAuth读取最多两小时的网络航班区间。 | `begin, end` |

`flights-interval` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "begin": {
      "type": "integer",
      "minimum": 0
    },
    "end": {
      "type": "integer",
      "minimum": 1
    }
  },
  "required": [
    "begin",
    "end"
  ]
}
```

| `flights-aircraft` | 使用OAuth读取单架飞机最多两天的已完成航班。 | `icao24, begin, end` |

`flights-aircraft` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "icao24": {
      "type": "array",
      "minItems": 1,
      "maxItems": 1,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[0-9A-Fa-f]{6}$"
      }
    },
    "begin": {
      "type": "integer",
      "minimum": 0
    },
    "end": {
      "type": "integer",
      "minimum": 1
    }
  },
  "required": [
    "icao24",
    "begin",
    "end"
  ]
}
```

| `airport-arrivals` | 使用OAuth读取机场最多两天的已完成到港航班。 | `airport, begin, end` |

`airport-arrivals` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "airport": {
      "type": "string",
      "pattern": "^[A-Za-z0-9]{4}$"
    },
    "begin": {
      "type": "integer",
      "minimum": 0
    },
    "end": {
      "type": "integer",
      "minimum": 1
    }
  },
  "required": [
    "airport",
    "begin",
    "end"
  ]
}
```

| `airport-departures` | 使用OAuth读取机场最多两天的已完成离港航班。 | `airport, begin, end` |

`airport-departures` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "airport": {
      "type": "string",
      "pattern": "^[A-Za-z0-9]{4}$"
    },
    "begin": {
      "type": "integer",
      "minimum": 0
    },
    "end": {
      "type": "integer",
      "minimum": 1
    }
  },
  "required": [
    "airport",
    "begin",
    "end"
  ]
}
```

| `track-aircraft` | 使用OAuth读取单架飞机实时或最近30天内的实验性航迹。 | `icao24, time` |

`track-aircraft` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "icao24": {
      "type": "array",
      "minItems": 1,
      "maxItems": 1,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[0-9A-Fa-f]{6}$"
      }
    },
    "time": {
      "type": "integer",
      "minimum": 0
    }
  },
  "required": [
    "icao24",
    "time"
  ]
}
```

限制：

```json
{
  "network_requests_per_ticket_max": 2,
  "business_requests_per_ticket_max": 1,
  "oauth_token_requests_per_ticket_max": 1,
  "transient_retry_max": 0,
  "provider_concurrency_max": 1,
  "timeout_seconds_max": 60,
  "max_response_bytes": 20000000,
  "anonymous_credits_per_day": 400,
  "standard_user_credits_per_day_per_endpoint_bucket": 4000,
  "state_history_seconds_max": 3600,
  "state_bbox_area_square_degrees_max": 400,
  "icao24_per_ticket_max": 20,
  "flight_interval_seconds_max": 7200,
  "aircraft_or_airport_interval_seconds_max": 172800,
  "track_history_days_max": 30,
  "fixed_api_host": "opensky-network.org",
  "fixed_auth_host": "auth.opensky-network.org",
  "oauth2_client_credentials_required_for_historical_operations": true,
  "anonymous_current_states_allowed": true,
  "global_state_query_allowed": false,
  "automatic_retry_allowed": false,
  "automatic_pagination_allowed": false,
  "background_polling_allowed": false,
  "trino_historical_access_allowed": false,
  "bulk_download_allowed": false,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_headers_allowed": false,
  "client_supplied_credentials_allowed": false,
  "oauth_token_persistence_allowed": false,
  "write_operations_allowed": false,
  "secret_values_exposed": false,
  "authentication_required": false
}
```

## HexDB 航空器型号、注册与航线补全 (`hexdb-aviation`)

- 状态：`启用`
- 说明：使用 HexDB 的只读 REST API，按 ICAO24、航班呼号或机场代码补全 OpenSky 状态向量缺少的飞机注册号、制造商、具体型号、登记所有人、运营方代码、航线和机场基础信息。
- 目录策略：固定访问 hexdb.io 的公开只读 REST API；不允许任意 URL、批量抓取、图片抓取、后台轮询、自动重试或写操作。数据来自第三方和众包来源，仅作为证据补全，不替代航空主管机关登记。
- 执行策略：每张票据最多一次 GET，只允许单个 ICAO24、单个呼号或单个机场代码。上游当前公开说明为每 5 分钟不超过 1000 次请求，情报中心进一步限制为全局并发 1、无重试、无自动翻页。
- 票据前缀：`[intel-hexdb]`
- Secret环境变量名：`无`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`d43a95964080a2a0b0481d5769a06139cec8f6c33768e662486fcfb6223d47ab`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地 HexDB 安全能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `aircraft-by-icao24` | 按六位 ICAO24/Mode-S 地址读取注册号、制造商、ICAO 机型代码、具体机型、登记所有人和运营方代码。 | `icao24` |

`aircraft-by-icao24` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "icao24": {
      "type": "string",
      "pattern": "^[0-9A-Fa-f]{6}$"
    }
  },
  "required": [
    "icao24"
  ]
}
```

| `route-by-icao-callsign` | 按 ICAO 航班呼号读取推定起点—终点机场代码。 | `callsign` |

`route-by-icao-callsign` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "callsign": {
      "type": "string",
      "pattern": "^[A-Za-z0-9]{2,12}$"
    }
  },
  "required": [
    "callsign"
  ]
}
```

| `route-by-iata-callsign` | 按 IATA 航班呼号读取推定起点—终点机场代码。 | `callsign` |

`route-by-iata-callsign` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "callsign": {
      "type": "string",
      "pattern": "^[A-Za-z0-9]{2,12}$"
    }
  },
  "required": [
    "callsign"
  ]
}
```

| `airport-by-icao` | 按四位 ICAO 机场代码读取机场名称、IATA 代码、国家、地区及坐标。 | `airport` |

`airport-by-icao` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "airport": {
      "type": "string",
      "pattern": "^[A-Za-z0-9]{4}$"
    }
  },
  "required": [
    "airport"
  ]
}
```

| `airport-by-iata` | 按三位 IATA 机场代码读取机场名称、ICAO 代码、国家、地区及坐标。 | `airport` |

`airport-by-iata` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "airport": {
      "type": "string",
      "pattern": "^[A-Za-z0-9]{3}$"
    }
  },
  "required": [
    "airport"
  ]
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "transient_retry_max": 0,
  "provider_concurrency_max": 1,
  "timeout_seconds_max": 30,
  "max_response_bytes": 2000000,
  "upstream_requests_per_window_max": 1000,
  "upstream_rate_window_seconds": 300,
  "fixed_api_host": "hexdb.io",
  "single_identifier_per_ticket_required": true,
  "automatic_retry_allowed": false,
  "automatic_pagination_allowed": false,
  "background_polling_allowed": false,
  "bulk_lookup_allowed": false,
  "image_retrieval_allowed": false,
  "legacy_text_endpoints_allowed": false,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_headers_allowed": false,
  "client_supplied_credentials_allowed": false,
  "write_operations_allowed": false,
  "secret_values_exposed": false,
  "authentication_required": false
}
```

## WTO Timeseries 国际贸易与关税统计 (`wto`)

- 状态：`启用`
- 说明：通过 WTO 官方 Timeseries API 读取贸易、关税、市场准入、非关税措施及相关指标。
- 目录策略：固定访问 api.wto.org/timeseries/v1；订阅密钥仅经后端请求头发送。
- 执行策略：每张票据最多一次 GET；无重试、无自动翻页、最多500条。
- 票据前缀：`[intel-wto]`
- Secret环境变量名：`WTO_API_KEY`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`c7f7c35db19f28776454639121531431bd67a89cca7b7242176c647ceef12d78`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地 WTO 能力目录。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `indicator-categories` | 读取 WTO 指标分类。 | `lang` |

`indicator-categories` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "lang": {
      "type": "integer",
      "enum": [
        1,
        2,
        3
      ]
    }
  }
}
```

| `indicators` | 读取 WTO 指标目录。 | `lang` |

`indicators` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "lang": {
      "type": "integer",
      "enum": [
        1,
        2,
        3
      ]
    }
  }
}
```

| `reporters` | 读取报告经济体目录。 | `lang` |

`reporters` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "lang": {
      "type": "integer",
      "enum": [
        1,
        2,
        3
      ]
    }
  }
}
```

| `partners` | 读取伙伴经济体目录。 | `lang` |

`partners` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "lang": {
      "type": "integer",
      "enum": [
        1,
        2,
        3
      ]
    }
  }
}
```

| `data-count` | 按受限条件读取 WTO 匹配记录数。 | `indicator_codes, reporter_codes, partner_codes, periods, product_codes, product_subsector, mode, decimals, offset, max_records, heading_style, lang, include_metadata` |

`data-count` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "indicator_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 10,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@+-]{0,79}$"
      }
    },
    "reporter_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@+-]{0,79}$"
      }
    },
    "partner_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@+-]{0,79}$"
      }
    },
    "periods": {
      "type": "array",
      "minItems": 1,
      "maxItems": 24,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[0-9]{4}(?:-(?:M[0-9]{2}|Q[1-4]))?$"
      }
    },
    "product_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@+-]{0,79}$"
      }
    },
    "product_subsector": {
      "type": "boolean"
    },
    "mode": {
      "type": "string",
      "enum": [
        "full",
        "codes"
      ]
    },
    "decimals": {
      "oneOf": [
        {
          "type": "string",
          "const": "default"
        },
        {
          "type": "integer",
          "minimum": 0,
          "maximum": 6
        }
      ]
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000
    },
    "max_records": {
      "type": "integer",
      "minimum": 1,
      "maximum": 500
    },
    "heading_style": {
      "type": "string",
      "enum": [
        "H",
        "C"
      ]
    },
    "lang": {
      "type": "integer",
      "enum": [
        1,
        2,
        3
      ]
    },
    "include_metadata": {
      "type": "boolean"
    }
  },
  "required": [
    "indicator_codes"
  ]
}
```

| `data` | 按受限条件读取 WTO 时间序列。 | `indicator_codes, reporter_codes, partner_codes, periods, product_codes, product_subsector, mode, decimals, offset, max_records, heading_style, lang, include_metadata` |

`data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "indicator_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 10,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@+-]{0,79}$"
      }
    },
    "reporter_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@+-]{0,79}$"
      }
    },
    "partner_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@+-]{0,79}$"
      }
    },
    "periods": {
      "type": "array",
      "minItems": 1,
      "maxItems": 24,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[0-9]{4}(?:-(?:M[0-9]{2}|Q[1-4]))?$"
      }
    },
    "product_codes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@+-]{0,79}$"
      }
    },
    "product_subsector": {
      "type": "boolean"
    },
    "mode": {
      "type": "string",
      "enum": [
        "full",
        "codes"
      ]
    },
    "decimals": {
      "oneOf": [
        {
          "type": "string",
          "const": "default"
        },
        {
          "type": "integer",
          "minimum": 0,
          "maximum": 6
        }
      ]
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000
    },
    "max_records": {
      "type": "integer",
      "minimum": 1,
      "maximum": 500
    },
    "heading_style": {
      "type": "string",
      "enum": [
        "H",
        "C"
      ]
    },
    "lang": {
      "type": "integer",
      "enum": [
        1,
        2,
        3
      ]
    },
    "include_metadata": {
      "type": "boolean"
    }
  },
  "required": [
    "indicator_codes"
  ]
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "transient_retry_max": 0,
  "provider_concurrency_max": 1,
  "timeout_seconds_max": 60,
  "max_response_bytes": 20000000,
  "records_per_ticket_max": 500,
  "fixed_api_host": "api.wto.org",
  "fixed_api_prefix": "/timeseries/v1",
  "automatic_retry_allowed": false,
  "automatic_pagination_allowed": false,
  "bulk_download_allowed": false,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_headers_allowed": false,
  "client_supplied_credentials_allowed": false,
  "write_operations_allowed": false,
  "secret_values_exposed": false
}
```

## IMF SDMX 3.0 全球宏观、财政与金融统计 (`imf`)

- 状态：`启用`
- 说明：通过 IMF 当前官方 SDMX 3.0 API 读取 WEO、CPI、BOP、财政、货币金融、贸易及其他公开统计数据流、结构、代码表、概念表和观测值。
- 目录策略：固定访问 api.imf.org/external/sdmx/3.0；订阅密钥仅通过 Ocp-Apim-Subscription-Key 后端请求头发送，不进入 URL、Issue、日志或 Artifact。
- 执行策略：每张票据最多一次 GET；无自动重试、无自动翻页；只允许固定 SDMX 结构资源和单一受限数据键。
- 票据前缀：`[intel-imf]`
- Secret环境变量名：`IMF_API_KEY`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`52169236e694640319593d6cc7fffd1ef578831195fec2c2951b287613b15261`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地 IMF SDMX 安全能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `get-dataflow` | 读取指定 IMF SDMX 数据流定义。 | `agency, flow, version` |

`get-dataflow` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "agency": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@+-]{0,79}$"
    },
    "flow": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@+-]{0,79}$"
    },
    "version": {
      "type": "string",
      "pattern": "^(?:\\+|latest|[0-9]+(?:\\.[0-9]+){0,3})$"
    }
  },
  "required": [
    "agency",
    "flow"
  ]
}
```

| `get-datastructure` | 读取指定 IMF SDMX 数据结构定义。 | `agency, structure_id, version` |

`get-datastructure` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "agency": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@+-]{0,79}$"
    },
    "structure_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@+-]{0,79}$"
    },
    "version": {
      "type": "string",
      "pattern": "^(?:\\+|latest|[0-9]+(?:\\.[0-9]+){0,3})$"
    }
  },
  "required": [
    "agency",
    "structure_id"
  ]
}
```

| `get-codelist` | 读取指定 IMF SDMX 代码表。 | `agency, codelist_id, version` |

`get-codelist` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "agency": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@+-]{0,79}$"
    },
    "codelist_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@+-]{0,79}$"
    },
    "version": {
      "type": "string",
      "pattern": "^(?:\\+|latest|[0-9]+(?:\\.[0-9]+){0,3})$"
    }
  },
  "required": [
    "agency",
    "codelist_id"
  ]
}
```

| `get-conceptscheme` | 读取指定 IMF SDMX 概念表。 | `agency, conceptscheme_id, version` |

`get-conceptscheme` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "agency": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@+-]{0,79}$"
    },
    "conceptscheme_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@+-]{0,79}$"
    },
    "version": {
      "type": "string",
      "pattern": "^(?:\\+|latest|[0-9]+(?:\\.[0-9]+){0,3})$"
    }
  },
  "required": [
    "agency",
    "conceptscheme_id"
  ]
}
```

| `get-data` | 按固定数据流、版本、受限维度键和可选时期范围读取 IMF SDMX 观测数据。 | `agency, flow, version, key, start_period, end_period, dimension_at_observation` |

`get-data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "agency": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@+-]{0,79}$"
    },
    "flow": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@+-]{0,79}$"
    },
    "version": {
      "type": "string",
      "pattern": "^(?:\\+|latest|[0-9]+(?:\\.[0-9]+){0,3})$"
    },
    "key": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500,
      "pattern": "^[A-Za-z0-9*+._@-]+$"
    },
    "start_period": {
      "type": "string",
      "pattern": "^[0-9]{4}(?:-(?:M[0-9]{2}|Q[1-4]))?$"
    },
    "end_period": {
      "type": "string",
      "pattern": "^[0-9]{4}(?:-(?:M[0-9]{2}|Q[1-4]))?$"
    },
    "dimension_at_observation": {
      "type": "string",
      "enum": [
        "AllDimensions",
        "TimeDimension",
        "MeasureDimension"
      ]
    }
  },
  "required": [
    "agency",
    "flow",
    "key"
  ]
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "transient_retry_max": 0,
  "provider_concurrency_max": 1,
  "timeout_seconds_max": 120,
  "max_response_bytes": 20000000,
  "fixed_api_host": "api.imf.org",
  "fixed_api_prefix": "/external/sdmx/3.0",
  "subscription_key_header": "Ocp-Apim-Subscription-Key",
  "data_key_length_max": 500,
  "automatic_retry_allowed": false,
  "automatic_pagination_allowed": false,
  "bulk_download_allowed": false,
  "arbitrary_sdmx_resource_types_allowed": false,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_headers_allowed": false,
  "client_supplied_credentials_allowed": false,
  "write_operations_allowed": false,
  "secret_values_exposed": false,
  "authentication_required": true
}
```

## World Bank Documents & Reports API (`worldbank-documents`)

- 状态：`启用`
- 说明：检索世界银行 Documents & Reports 官方公开报告、项目文件、研究论文、董事会文件和元数据。
- 目录策略：固定访问 search.worldbank.org/api/v3/wds；仅返回公开元数据和官方文档链接，不抓取或批量下载文档正文。
- 执行策略：每张票据最多一次 HTTPS GET；不自动重试或翻页；每页最多50条、offset最多10000；字段、Facet、筛选条件均采用固定白名单。
- 票据前缀：`[intel-worldbank-docs]`
- Secret环境变量名：`无`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`ae66f469a549fd6079f6060cb4fb7f71310026120928a39f9643fa5490c852ae`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地 World Bank Documents & Reports 安全能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `search-documents` | 按关键词、国家、语言、文件类型、项目、日期等受约束条件检索世界银行公开文档。 | `query, country, language, document_type, project_id, report_number, start_date, end_date, rows, offset, fields, sort, order` |

`search-documents` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 300
    },
    "country": {
      "type": "string",
      "minLength": 1,
      "maxLength": 120
    },
    "language": {
      "type": "string",
      "minLength": 1,
      "maxLength": 80
    },
    "document_type": {
      "type": "string",
      "minLength": 1,
      "maxLength": 120
    },
    "project_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]{1,80}$"
    },
    "report_number": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._/-]{1,80}$"
    },
    "start_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "end_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "rows": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000
    },
    "fields": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "enum": [
          "id",
          "guid",
          "display_title",
          "docdt",
          "docty",
          "majdocty",
          "count",
          "countcode",
          "lang",
          "authr",
          "abstracts",
          "projectid",
          "projn",
          "repnb",
          "repnme",
          "pdfurl",
          "txturl",
          "url",
          "topicv3",
          "keywd",
          "src_cit"
        ]
      }
    },
    "sort": {
      "type": "string",
      "enum": [
        "docdt",
        "display_title",
        "repnb",
        "docty"
      ]
    },
    "order": {
      "type": "string",
      "enum": [
        "asc",
        "desc"
      ]
    }
  },
  "required": [
    "query"
  ]
}
```

| `get-document` | 按 Documents & Reports 文档 ID 读取公开文档元数据。 | `document_id, fields` |

`get-document` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "document_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_:-]{1,120}$"
    },
    "fields": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "enum": [
          "id",
          "guid",
          "display_title",
          "docdt",
          "docty",
          "majdocty",
          "count",
          "countcode",
          "lang",
          "authr",
          "abstracts",
          "projectid",
          "projn",
          "repnb",
          "repnme",
          "pdfurl",
          "txturl",
          "url",
          "topicv3",
          "keywd",
          "src_cit"
        ]
      }
    }
  },
  "required": [
    "document_id"
  ]
}
```

| `project-documents` | 按世界银行项目 ID 检索公开项目文件。 | `project_id, rows, offset, fields, start_date, end_date` |

`project-documents` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "project_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]{1,80}$"
    },
    "rows": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000
    },
    "fields": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "enum": [
          "id",
          "guid",
          "display_title",
          "docdt",
          "docty",
          "majdocty",
          "count",
          "countcode",
          "lang",
          "authr",
          "abstracts",
          "projectid",
          "projn",
          "repnb",
          "repnme",
          "pdfurl",
          "txturl",
          "url",
          "topicv3",
          "keywd",
          "src_cit"
        ]
      }
    },
    "start_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "end_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  },
  "required": [
    "project_id"
  ]
}
```

| `report-documents` | 按报告编号检索公开报告及卷册元数据。 | `report_number, rows, offset, fields` |

`report-documents` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "report_number": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._/-]{1,80}$"
    },
    "rows": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000
    },
    "fields": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "enum": [
          "id",
          "guid",
          "display_title",
          "docdt",
          "docty",
          "majdocty",
          "count",
          "countcode",
          "lang",
          "authr",
          "abstracts",
          "projectid",
          "projn",
          "repnb",
          "repnme",
          "pdfurl",
          "txturl",
          "url",
          "topicv3",
          "keywd",
          "src_cit"
        ]
      }
    }
  },
  "required": [
    "report_number"
  ]
}
```

| `recent-documents` | 按日期范围读取最新公开文档。 | `start_date, end_date, query, rows, offset, fields, sort, order` |

`recent-documents` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "start_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "end_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 300
    },
    "rows": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000
    },
    "fields": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "enum": [
          "id",
          "guid",
          "display_title",
          "docdt",
          "docty",
          "majdocty",
          "count",
          "countcode",
          "lang",
          "authr",
          "abstracts",
          "projectid",
          "projn",
          "repnb",
          "repnme",
          "pdfurl",
          "txturl",
          "url",
          "topicv3",
          "keywd",
          "src_cit"
        ]
      }
    },
    "sort": {
      "type": "string",
      "enum": [
        "docdt",
        "display_title",
        "repnb",
        "docty"
      ]
    },
    "order": {
      "type": "string",
      "enum": [
        "asc",
        "desc"
      ]
    }
  },
  "required": [
    "start_date"
  ]
}
```

| `document-facets` | 读取受约束检索结果的国家、语言、文件类型、主题或行业 Facet。 | `query, facets, start_date, end_date` |

`document-facets` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 300
    },
    "facets": {
      "type": "array",
      "minItems": 1,
      "maxItems": 6,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "enum": [
          "count_exact",
          "lang_exact",
          "docty_exact",
          "majdocty_exact",
          "topic_exact",
          "sectr_exact"
        ]
      }
    },
    "start_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "end_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  },
  "required": [
    "facets"
  ]
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "provider_concurrency_max": 1,
  "records_per_ticket_max": 50,
  "offset_max": 10000,
  "fields_per_ticket_max": 20,
  "facets_per_ticket_max": 6,
  "timeout_seconds_max": 120,
  "max_response_bytes": 20000000,
  "fixed_api_host": "search.worldbank.org",
  "fixed_api_prefix": "/api/v3/wds",
  "document_body_download_allowed": false,
  "automatic_retry_allowed": false,
  "automatic_pagination_allowed": false,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "redirects_allowed": false,
  "write_operations_allowed": false,
  "personal_data_allowed": false,
  "secret_values_exposed": false
}
```

## Bank for International Settlements SDMX API (`bis`)

- 状态：`启用`
- 说明：读取国际清算银行公开的国际银行、全球流动性、信贷、汇率、衍生品、消费价格和央行资产等统计与结构元数据。
- 目录策略：固定访问 stats.bis.org/api/v2；仅开放 SDMX v2.1 数据、可用性和结构查询；禁止任意 URL、主机、请求头和批量下载。
- 执行策略：每张票据最多一次 HTTPS GET；不自动重试或翻页；序列键和时间范围必须显式提供；响应最大20MB。
- 票据前缀：`[intel-bis]`
- Secret环境变量名：`无`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`775226b29d473da42f432bd6a05d1ef320b61739ea29bd80365a2e809828cd15`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地 BIS SDMX 安全能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `list-dataflows` | 读取 BIS 公开 SDMX 数据流目录。 | `references` |

`list-dataflows` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "references": {
      "type": "string",
      "enum": [
        "none",
        "parents",
        "ancestors",
        "children",
        "descendants",
        "all"
      ]
    }
  }
}
```

| `get-dataflow` | 读取指定 BIS 数据流定义。 | `agency, flow, version, references` |

`get-dataflow` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "agency": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}$"
    },
    "flow": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}$"
    },
    "version": {
      "type": "string",
      "pattern": "^(?:latest|[0-9]+(?:\\.[0-9]+){0,3})$"
    },
    "references": {
      "type": "string",
      "enum": [
        "none",
        "parents",
        "ancestors",
        "children",
        "descendants",
        "all"
      ]
    }
  },
  "required": [
    "flow"
  ]
}
```

| `get-datastructure` | 读取指定 BIS 数据结构定义。 | `agency, structure_id, version, references` |

`get-datastructure` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "agency": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}$"
    },
    "structure_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}$"
    },
    "version": {
      "type": "string",
      "pattern": "^(?:latest|[0-9]+(?:\\.[0-9]+){0,3})$"
    },
    "references": {
      "type": "string",
      "enum": [
        "none",
        "parents",
        "ancestors",
        "children",
        "descendants",
        "all"
      ]
    }
  },
  "required": [
    "structure_id"
  ]
}
```

| `get-codelist` | 读取指定 BIS 代码表。 | `agency, codelist_id, version, references` |

`get-codelist` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "agency": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}$"
    },
    "codelist_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}$"
    },
    "version": {
      "type": "string",
      "pattern": "^(?:latest|[0-9]+(?:\\.[0-9]+){0,3})$"
    },
    "references": {
      "type": "string",
      "enum": [
        "none",
        "parents",
        "ancestors",
        "children",
        "descendants",
        "all"
      ]
    }
  },
  "required": [
    "codelist_id"
  ]
}
```

| `get-conceptscheme` | 读取指定 BIS 概念表。 | `agency, conceptscheme_id, version, references` |

`get-conceptscheme` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "agency": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}$"
    },
    "conceptscheme_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}$"
    },
    "version": {
      "type": "string",
      "pattern": "^(?:latest|[0-9]+(?:\\.[0-9]+){0,3})$"
    },
    "references": {
      "type": "string",
      "enum": [
        "none",
        "parents",
        "ancestors",
        "children",
        "descendants",
        "all"
      ]
    }
  },
  "required": [
    "conceptscheme_id"
  ]
}
```

| `get-data` | 按 SDMX 数据流、序列键和时间范围读取 BIS 统计。 | `context, agency, flow, version, key, start_period, end_period, format, detail, dimension_at_observation` |

`get-data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "context": {
      "type": "string",
      "enum": [
        "dataflow",
        "datastructure"
      ]
    },
    "agency": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}$"
    },
    "flow": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}$"
    },
    "version": {
      "type": "string",
      "pattern": "^(?:latest|[0-9]+(?:\\.[0-9]+){0,3})$"
    },
    "key": {
      "type": "string",
      "pattern": "^[A-Za-z0-9*+.,_@-]{1,500}$"
    },
    "start_period": {
      "type": "string",
      "pattern": "^[0-9]{4}(?:-(?:M[0-9]{2}|Q[1-4]|S[12]))?$"
    },
    "end_period": {
      "type": "string",
      "pattern": "^[0-9]{4}(?:-(?:M[0-9]{2}|Q[1-4]|S[12]))?$"
    },
    "format": {
      "type": "string",
      "enum": [
        "json",
        "csv"
      ]
    },
    "detail": {
      "type": "string",
      "enum": [
        "full",
        "dataonly",
        "serieskeysonly",
        "nodata"
      ]
    },
    "dimension_at_observation": {
      "type": "string",
      "enum": [
        "AllDimensions",
        "TimeDimension",
        "MeasureDimension"
      ]
    }
  },
  "required": [
    "flow",
    "key"
  ]
}
```

| `get-availability` | 读取指定 BIS 数据集和序列键的数据可用性约束。 | `context, agency, flow, version, key, component_id` |

`get-availability` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "context": {
      "type": "string",
      "enum": [
        "dataflow",
        "datastructure"
      ]
    },
    "agency": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}$"
    },
    "flow": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}$"
    },
    "version": {
      "type": "string",
      "pattern": "^(?:latest|[0-9]+(?:\\.[0-9]+){0,3})$"
    },
    "key": {
      "type": "string",
      "pattern": "^[A-Za-z0-9*+.,_@-]{1,500}$"
    },
    "component_id": {
      "type": "string",
      "pattern": "^(?:[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}|all)$"
    }
  },
  "required": [
    "flow",
    "key"
  ]
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "provider_concurrency_max": 1,
  "timeout_seconds_max": 120,
  "max_response_bytes": 20000000,
  "key_length_max": 500,
  "fixed_api_host": "stats.bis.org",
  "fixed_api_prefix": "/api/v2",
  "sdmx_rest_version": "2.1.0",
  "automatic_retry_allowed": false,
  "automatic_pagination_allowed": false,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "bulk_download_allowed": false,
  "redirects_allowed": false,
  "write_operations_allowed": false,
  "personal_data_allowed": false,
  "source_citation_required": true,
  "secret_values_exposed": false
}
```

## Asian Development Bank KIDB SDMX (`adb`)

- 状态：`启用`
- 说明：通过亚洲开发银行官方 Key Indicators Database SDMX API v4 读取亚洲及太平洋宏观、金融、社会、环境和可持续发展统计。
- 目录策略：仅开放固定的 ADB KIDB 数据流、结构元数据、指标目录和有界数据查询；不接受任意 URL、主机、请求头或空维度全库请求。
- 执行策略：每张票据最多一次 HTTPS GET；不自动重试或翻页；遵守官方每分钟20次限制；数据请求最多20个指标、20个经济体和25年。
- 票据前缀：`[intel-adb]`
- Secret环境变量名：`无`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`0bbf83a649e64b79a42cb8d1981b0af99ddc98443840c16137e89361b2d5b51b`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地 ADB KIDB 安全能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `list-dataflows` | 读取 ADB KIDB 当前公开数据流目录。 | `无` |

`list-dataflows` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `get-dataflow` | 读取指定 ADB SDMX 数据流定义。 | `agency, flow, version, references` |

`get-dataflow` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "agency": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}$"
    },
    "flow": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}$"
    },
    "version": {
      "type": "string",
      "pattern": "^(?:\\+|latest|[0-9]+(?:\\.[0-9]+){0,3})$"
    },
    "references": {
      "type": "string",
      "enum": [
        "none",
        "parents",
        "ancestors",
        "children",
        "descendants",
        "all"
      ]
    }
  },
  "required": [
    "flow"
  ]
}
```

| `get-datastructure` | 读取指定 ADB SDMX 数据结构定义。 | `agency, structure_id, version, references` |

`get-datastructure` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "agency": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}$"
    },
    "structure_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}$"
    },
    "version": {
      "type": "string",
      "pattern": "^(?:\\+|latest|[0-9]+(?:\\.[0-9]+){0,3})$"
    },
    "references": {
      "type": "string",
      "enum": [
        "none",
        "parents",
        "ancestors",
        "children",
        "descendants",
        "all"
      ]
    }
  },
  "required": [
    "structure_id"
  ]
}
```

| `get-codelist` | 读取指定 ADB SDMX 代码表。 | `agency, codelist_id, version, references` |

`get-codelist` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "agency": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}$"
    },
    "codelist_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}$"
    },
    "version": {
      "type": "string",
      "pattern": "^(?:\\+|latest|[0-9]+(?:\\.[0-9]+){0,3})$"
    },
    "references": {
      "type": "string",
      "enum": [
        "none",
        "parents",
        "ancestors",
        "children",
        "descendants",
        "all"
      ]
    }
  },
  "required": [
    "codelist_id"
  ]
}
```

| `get-conceptscheme` | 读取指定 ADB SDMX 概念表。 | `agency, conceptscheme_id, version, references` |

`get-conceptscheme` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "agency": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}$"
    },
    "conceptscheme_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}$"
    },
    "version": {
      "type": "string",
      "pattern": "^(?:\\+|latest|[0-9]+(?:\\.[0-9]+){0,3})$"
    },
    "references": {
      "type": "string",
      "enum": [
        "none",
        "parents",
        "ancestors",
        "children",
        "descendants",
        "all"
      ]
    }
  },
  "required": [
    "conceptscheme_id"
  ]
}
```

| `list-indicators` | 读取指定 ADB 数据流中的指标代码目录。 | `dataflow` |

`list-indicators` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "dataflow": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}$"
    }
  },
  "required": [
    "dataflow"
  ]
}
```

| `get-data` | 按数据流、指标、经济体和时间范围读取 ADB KIDB 统计。 | `dataflow, indicators, economies, start_period, end_period, sdmx_version, format, grouping` |

`get-data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "dataflow": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}$"
    },
    "indicators": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,39}$"
      }
    },
    "economies": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z0-9][A-Za-z0-9_.@-]{0,39}$"
      }
    },
    "start_period": {
      "type": "integer",
      "minimum": 2000,
      "maximum": 2024
    },
    "end_period": {
      "type": "integer",
      "minimum": 2000,
      "maximum": 2024
    },
    "sdmx_version": {
      "type": "string",
      "enum": [
        "3.0",
        "2.1"
      ]
    },
    "format": {
      "type": "string",
      "enum": [
        "json",
        "csv"
      ]
    },
    "grouping": {
      "type": "string",
      "enum": [
        "indicator",
        "economy"
      ]
    }
  },
  "required": [
    "dataflow",
    "indicators",
    "economies"
  ]
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "provider_concurrency_max": 1,
  "official_rate_limit_queries_per_minute": 20,
  "timeout_seconds_max": 120,
  "max_response_bytes": 20000000,
  "indicators_per_ticket_max": 20,
  "economies_per_ticket_max": 20,
  "period_span_years_max": 25,
  "documented_start_period_min": 2000,
  "documented_end_period_max": 2024,
  "fixed_api_host": "kidb.adb.org",
  "fixed_api_prefix": "/api/v4/sdmx",
  "automatic_retry_allowed": false,
  "automatic_pagination_allowed": false,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "empty_dimension_bulk_queries_allowed": false,
  "bulk_download_allowed": false,
  "redirects_allowed": false,
  "write_operations_allowed": false,
  "personal_data_allowed": false,
  "secret_values_exposed": false
}
```

## Wolfram|Alpha 计算知识 API (`wolfram-alpha`)

- 状态：`启用`
- 说明：通过 Wolfram|Alpha 官方 API 读取可验证的计算知识、短答案、完整结果与面向大模型的文本结果。
- 目录策略：只允许调用 Wolfram|Alpha 官方固定 GET 端点；禁止任意 URL、任意请求头、图片生成端点、异步状态修改和任何写入。
- 执行策略：WOLFRAM_ALPHA_APP_ID 仅在后端 appid 查询参数注入；每张票据执行一次只读查询，固定输出类型并限制输入、超时和响应体积。
- 票据前缀：`[api-wolfram]`
- Secret环境变量名：`WOLFRAM_ALPHA_APP_ID`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`d510d42245f91826f4ff38f567b17c9bf7f6a60972b51c7202ac00e04e3a796a`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取 Wolfram|Alpha 本地安全能力目录，不访问上游且不需要 AppID。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `full-results` | 调用 Full Results API v2，以 JSON 返回 pods、假设、来源和纯文本结果。 | `input, units, location, languagecode, upstream_timeout_seconds` |

`full-results` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "input"
  ],
  "properties": {
    "input": {
      "type": "string",
      "minLength": 1,
      "maxLength": 2000
    },
    "units": {
      "type": "string",
      "enum": [
        "default",
        "metric",
        "imperial"
      ]
    },
    "location": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "languagecode": {
      "type": "string",
      "pattern": "^[A-Za-z]{2}$"
    },
    "upstream_timeout_seconds": {
      "type": "integer",
      "minimum": 1,
      "maximum": 30
    }
  }
}
```

| `short-answer` | 调用 Short Answers API，返回单行计算答案。 | `input, units, location, upstream_timeout_seconds` |

`short-answer` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "input"
  ],
  "properties": {
    "input": {
      "type": "string",
      "minLength": 1,
      "maxLength": 2000
    },
    "units": {
      "type": "string",
      "enum": [
        "default",
        "metric",
        "imperial"
      ]
    },
    "location": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "upstream_timeout_seconds": {
      "type": "integer",
      "minimum": 1,
      "maximum": 30
    }
  }
}
```

| `llm-result` | 调用 Wolfram|Alpha LLM API，返回便于 GPTs 消化的计算知识文本。 | `input, units, location, languagecode, upstream_timeout_seconds` |

`llm-result` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "input"
  ],
  "properties": {
    "input": {
      "type": "string",
      "minLength": 1,
      "maxLength": 2000
    },
    "units": {
      "type": "string",
      "enum": [
        "default",
        "metric",
        "imperial"
      ]
    },
    "location": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "languagecode": {
      "type": "string",
      "pattern": "^[A-Za-z]{2}$"
    },
    "upstream_timeout_seconds": {
      "type": "integer",
      "minimum": 1,
      "maximum": 30
    }
  }
}
```

限制：

```json
{
  "requests_per_ticket": 1,
  "timeout_seconds_max": 120,
  "max_response_bytes": 5000000,
  "input_characters_max": 2000,
  "arbitrary_urls_allowed": false,
  "arbitrary_headers_allowed": false,
  "write_operations_allowed": false,
  "image_endpoints_enabled": false,
  "secret_values_exposed": false
}
```

## LlamaParse 文档解析 API (`llamaparse`)

- 状态：`启用`
- 说明：通过 LlamaParse v2 将固定白名单来源的公开文档解析为 Markdown、文本、结构化项目和元数据。
- 目录策略：只允许 LlamaParse 官方 NA/EU 固定 HTTPS 主机、固定 Parse v2 端点和受限公开文档来源；禁止任意 URL、Webhook、任意请求头、文件回写和索引写入。
- 执行策略：LLAMA_CLOUD_API_KEY 仅在后端 Bearer 请求头注入；新建解析任务后在单张票据内有限轮询，并过滤预签名下载 URL、Authorization 和密钥。
- 票据前缀：`[api-llamaparse]`
- Secret环境变量名：`LLAMA_CLOUD_API_KEY`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`5104c79c0f79e9b401c203957b4c122b2b26f1462e220816ccb475b96c52fc0e`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取 LlamaParse 本地安全能力目录，不访问上游且不需要密钥。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `parse-public-document` | 提交白名单公共 HTTPS 文档 URL，创建 Parse v2 作业并有限轮询至完成。 | `source_url, tier, version, region, max_pages, custom_prompt, disable_cache, expand` |

`parse-public-document` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "source_url"
  ],
  "properties": {
    "source_url": {
      "type": "string",
      "minLength": 12,
      "maxLength": 2000,
      "pattern": "^https://"
    },
    "tier": {
      "type": "string",
      "enum": [
        "fast",
        "cost_effective",
        "agentic",
        "agentic_plus"
      ]
    },
    "version": {
      "type": "string",
      "pattern": "^(latest|[0-9]{4}-[0-9]{2}-[0-9]{2})$"
    },
    "region": {
      "type": "string",
      "enum": [
        "na",
        "eu"
      ]
    },
    "max_pages": {
      "type": "integer",
      "minimum": 1,
      "maximum": 200
    },
    "custom_prompt": {
      "type": "string",
      "minLength": 1,
      "maxLength": 1000
    },
    "disable_cache": {
      "type": "boolean"
    },
    "expand": {
      "type": "array",
      "minItems": 1,
      "maxItems": 5,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "enum": [
          "text",
          "markdown",
          "items",
          "metadata",
          "job_metadata",
          "text_full",
          "markdown_full"
        ]
      }
    }
  }
}
```

| `get-job` | 读取既有 Parse v2 作业的状态和选定结果字段。 | `job_id, region, expand` |

`get-job` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "job_id"
  ],
  "properties": {
    "job_id": {
      "type": "string",
      "minLength": 8,
      "maxLength": 128,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$"
    },
    "region": {
      "type": "string",
      "enum": [
        "na",
        "eu"
      ]
    },
    "expand": {
      "type": "array",
      "minItems": 1,
      "maxItems": 5,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "enum": [
          "text",
          "markdown",
          "items",
          "metadata",
          "job_metadata",
          "text_full",
          "markdown_full"
        ]
      }
    }
  }
}
```

限制：

```json
{
  "requests_per_ticket": 302,
  "create_requests_per_ticket": 1,
  "poll_timeout_seconds_max": 600,
  "timeout_seconds_max": 120,
  "max_response_bytes": 5000000,
  "max_pages": 200,
  "public_document_host_allowlist": [
    "raw.githubusercontent.com",
    "github.com",
    "arxiv.org",
    "export.arxiv.org",
    "openaccess.thecvf.com",
    "aclanthology.org",
    "proceedings.neurips.cc",
    "papers.ssrn.com",
    "openreview.net",
    "sec.gov",
    "www.sec.gov",
    "annualreports.com",
    "www.annualreports.com"
  ],
  "arbitrary_urls_allowed": false,
  "arbitrary_headers_allowed": false,
  "webhooks_allowed": false,
  "write_operations_allowed": false,
  "presigned_urls_exposed": false,
  "secret_values_exposed": false
}
```

## 全球公共数据、空间地理与中国数据 (`public-data-geospatial`)

- 状态：`启用`
- 说明：统一开放免费或有免费额度的全球公共数据、空间地理、道路交通及中国大陆官方数据能力。
- 目录策略：仅允许调用代码内固定官方主机和固定只读端点；禁止任意 URL、任意请求头、自动翻页、批量镜像、登录绕过、写入、交易或个人数据查询。
- 执行策略：每张票据最多执行一次上游只读请求；密钥和用户名仅由后端环境注入；无密钥操作可直接运行，有密钥操作缺少相应字段时结构化失败。
- 票据前缀：`[intel-public-data]`
- Secret环境变量名：`无`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`d5fe5865aa0cc96fb5ff5fe0fd7b41ce39ba53a27011213a2eabb2ee074e0dc4`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地能力、鉴权字段和使用限制目录。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `ilostat-dataflows` | 读取 ILOSTAT 官方 SDMX 数据流目录。 | `无` |

`ilostat-dataflows` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `unicef-dataflows` | 读取 UNICEF Data Warehouse 官方 SDMX 数据流目录。 | `无` |

`unicef-dataflows` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `un-sdg-indicators` | 读取联合国统计司官方 SDG 指标与序列目录。 | `include_children` |

`un-sdg-indicators` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "include_children": {
      "type": "boolean"
    }
  }
}
```

| `faostat-definitions` | 读取 FAOSTAT 官方 API 的定义/目录资源。 | `language` |

`faostat-definitions` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "language": {
      "type": "string",
      "enum": [
        "en",
        "zh",
        "fr",
        "es",
        "ar",
        "ru"
      ]
    }
  }
}
```

| `worldpop-catalog` | 读取 WorldPop REST 数据集与元数据目录。 | `alias, iso3` |

`worldpop-catalog` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "alias": {
      "type": "string",
      "maxLength": 80
    },
    "iso3": {
      "type": "string",
      "pattern": "^[A-Z]{3}$"
    }
  }
}
```

| `worldpop-services` | 读取 WorldPop 空间统计服务目录。 | `无` |

`worldpop-services` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `gbif-occurrences` | 检索 GBIF 全球生物多样性出现记录。 | `scientific_name, country, year, decimal_latitude, decimal_longitude, radius_km, limit, offset` |

`gbif-occurrences` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "scientific_name": {
      "type": "string",
      "maxLength": 200
    },
    "country": {
      "type": "string",
      "pattern": "^[A-Z]{2}$"
    },
    "year": {
      "type": "string",
      "maxLength": 20
    },
    "decimal_latitude": {
      "type": "number",
      "minimum": -90,
      "maximum": 90
    },
    "decimal_longitude": {
      "type": "number",
      "minimum": -180,
      "maximum": 180
    },
    "radius_km": {
      "type": "number",
      "minimum": 0.1,
      "maximum": 100
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000
    }
  }
}
```

| `unhcr-population` | 查询 UNHCR Refugee Data Finder 官方人口统计。 | `year_from, year_to, coa, coo, limit, page` |

`unhcr-population` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "year_from": {
      "type": "integer",
      "minimum": 1951,
      "maximum": 2100
    },
    "year_to": {
      "type": "integer",
      "minimum": 1951,
      "maximum": 2100
    },
    "coa": {
      "type": "string",
      "maxLength": 80
    },
    "coo": {
      "type": "string",
      "maxLength": 80
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    },
    "page": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000
    }
  }
}
```

| `reliefweb-reports` | 检索 ReliefWeb 官方人道主义报告。 | `query, country, limit, offset` |

`reliefweb-reports` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "maxLength": 300
    },
    "country": {
      "type": "string",
      "maxLength": 100
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000
    }
  }
}
```

| `gleif-lei-search` | 检索 GLEIF 官方 LEI 主体记录。 | `query, country, page_size, page_number` |

`gleif-lei-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "maxLength": 200
    },
    "country": {
      "type": "string",
      "pattern": "^[A-Z]{2}$"
    },
    "page_size": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    },
    "page_number": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000
    }
  },
  "required": [
    "query"
  ]
}
```

| `usaspending-awards` | 查询 USAspending 官方联邦支出奖项。 | `keywords, award_type_codes, start_date, end_date, page, limit` |

`usaspending-awards` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "keywords": {
      "type": "array",
      "items": {
        "type": "string",
        "maxLength": 100
      },
      "minItems": 1,
      "maxItems": 10
    },
    "award_type_codes": {
      "type": "array",
      "items": {
        "type": "string",
        "maxLength": 4
      },
      "minItems": 1,
      "maxItems": 20
    },
    "start_date": {
      "type": "string",
      "format": "date"
    },
    "end_date": {
      "type": "string",
      "format": "date"
    },
    "page": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    }
  },
  "required": [
    "keywords",
    "start_date",
    "end_date"
  ]
}
```

| `openfda-drug-events` | 查询 openFDA 药品不良事件公共数据。 | `search, limit, skip` |

`openfda-drug-events` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "search": {
      "type": "string",
      "maxLength": 500
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    },
    "skip": {
      "type": "integer",
      "minimum": 0,
      "maximum": 25000
    }
  },
  "required": [
    "search"
  ]
}
```

| `eurostat-data` | 读取 Eurostat 官方 SDMX 3.0 数据。 | `dataflow, key, start_period, end_period` |

`eurostat-data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "dataflow": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_.-]{1,80}$"
    },
    "key": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_+.-]{1,300}$"
    },
    "start_period": {
      "type": "string",
      "maxLength": 20
    },
    "end_period": {
      "type": "string",
      "maxLength": 20
    }
  },
  "required": [
    "dataflow",
    "key"
  ]
}
```

| `our-world-in-data-series` | 读取 Our World in Data Grapher CSV 序列。 | `slug` |

`our-world-in-data-series` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "slug": {
      "type": "string",
      "pattern": "^[a-z0-9][a-z0-9_-]{0,119}$"
    }
  },
  "required": [
    "slug"
  ]
}
```

| `hdx-hapi-metadata` | 读取 HDX Humanitarian API 标准化人道指标元数据。 | `无` |

`hdx-hapi-metadata` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `iati-activities` | 检索 IATI Datastore 发展援助活动。 | `query, rows, start` |

`iati-activities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "maxLength": 500
    },
    "rows": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    },
    "start": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000
    }
  },
  "required": [
    "query"
  ]
}
```

| `companies-house-search` | 检索英国 Companies House 官方企业记录。 | `query, items_per_page, start_index` |

`companies-house-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "maxLength": 200
    },
    "items_per_page": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    },
    "start_index": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000
    }
  },
  "required": [
    "query"
  ]
}
```

| `sam-opportunities` | 查询 SAM.gov 官方合同机会。 | `posted_from, posted_to, keywords, limit, offset` |

`sam-opportunities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "posted_from": {
      "type": "string",
      "pattern": "^[0-9]{2}/[0-9]{2}/[0-9]{4}$"
    },
    "posted_to": {
      "type": "string",
      "pattern": "^[0-9]{2}/[0-9]{2}/[0-9]{4}$"
    },
    "keywords": {
      "type": "string",
      "maxLength": 200
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 1000
    }
  },
  "required": [
    "posted_from",
    "posted_to"
  ]
}
```

| `openaq-locations` | 查询 OpenAQ 全球空气质量监测站。 | `country, city, coordinates, radius, limit, page` |

`openaq-locations` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "country": {
      "type": "string",
      "pattern": "^[A-Z]{2}$"
    },
    "city": {
      "type": "string",
      "maxLength": 100
    },
    "coordinates": {
      "type": "string",
      "pattern": "^-?[0-9.]+,-?[0-9.]+$"
    },
    "radius": {
      "type": "integer",
      "minimum": 1,
      "maximum": 25000
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    },
    "page": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000
    }
  }
}
```

| `usgs-earthquakes` | 查询 USGS 全球地震事件目录。 | `start_time, end_time, min_magnitude, latitude, longitude, max_radius_km, limit` |

`usgs-earthquakes` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "start_time": {
      "type": "string",
      "format": "date-time"
    },
    "end_time": {
      "type": "string",
      "format": "date-time"
    },
    "min_magnitude": {
      "type": "number",
      "minimum": -2,
      "maximum": 10
    },
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
    "max_radius_km": {
      "type": "number",
      "minimum": 1,
      "maximum": 20000
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 2000
    }
  }
}
```

| `overpass-query` | 执行受限只读 Overpass QL，获取道路、POI、行政边界、公共交通等 OSM 数据。 | `query, timeout_seconds` |

`overpass-query` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 8,
      "maxLength": 8000
    },
    "timeout_seconds": {
      "type": "integer",
      "minimum": 1,
      "maximum": 25
    }
  },
  "required": [
    "query"
  ]
}
```

| `geonames-search` | 检索 GeoNames 全球地名、行政区和地理实体。 | `query, country, feature_class, max_rows, start_row` |

`geonames-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "maxLength": 200
    },
    "country": {
      "type": "string",
      "pattern": "^[A-Z]{2}$"
    },
    "feature_class": {
      "type": "string",
      "pattern": "^[A-Z]$"
    },
    "max_rows": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    },
    "start_row": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000
    }
  },
  "required": [
    "query"
  ]
}
```

| `openrouteservice-directions` | 使用 OpenRouteService/HeiGIT 计算道路、步行、自行车等路线。 | `profile, coordinates, preference, units, language, instructions` |

`openrouteservice-directions` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "profile": {
      "type": "string",
      "enum": [
        "driving-car",
        "driving-hgv",
        "cycling-regular",
        "cycling-road",
        "cycling-mountain",
        "cycling-electric",
        "foot-walking",
        "foot-hiking",
        "wheelchair"
      ]
    },
    "coordinates": {
      "type": "array",
      "items": {
        "type": "array",
        "items": {
          "type": "number"
        },
        "minItems": 2,
        "maxItems": 2
      },
      "minItems": 2,
      "maxItems": 50
    },
    "preference": {
      "type": "string",
      "enum": [
        "fastest",
        "shortest",
        "recommended"
      ]
    },
    "units": {
      "type": "string",
      "enum": [
        "m",
        "km",
        "mi"
      ]
    },
    "language": {
      "type": "string",
      "maxLength": 8
    },
    "instructions": {
      "type": "boolean"
    }
  },
  "required": [
    "profile",
    "coordinates"
  ]
}
```

| `openrouteservice-matrix` | 使用 OpenRouteService/HeiGIT 计算时间与距离矩阵。 | `profile, locations, metrics, units` |

`openrouteservice-matrix` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "profile": {
      "type": "string",
      "enum": [
        "driving-car",
        "driving-hgv",
        "cycling-regular",
        "foot-walking",
        "wheelchair"
      ]
    },
    "locations": {
      "type": "array",
      "items": {
        "type": "array",
        "items": {
          "type": "number"
        },
        "minItems": 2,
        "maxItems": 2
      },
      "minItems": 2,
      "maxItems": 50
    },
    "metrics": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "distance",
          "duration"
        ]
      },
      "minItems": 1,
      "maxItems": 2
    },
    "units": {
      "type": "string",
      "enum": [
        "m",
        "km",
        "mi"
      ]
    }
  },
  "required": [
    "profile",
    "locations"
  ]
}
```

| `openrouteservice-isochrones` | 使用 OpenRouteService/HeiGIT 生成时间或距离等时圈。 | `profile, locations, range, range_type, units` |

`openrouteservice-isochrones` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "profile": {
      "type": "string",
      "enum": [
        "driving-car",
        "driving-hgv",
        "cycling-regular",
        "foot-walking",
        "wheelchair"
      ]
    },
    "locations": {
      "type": "array",
      "items": {
        "type": "array",
        "items": {
          "type": "number"
        },
        "minItems": 2,
        "maxItems": 2
      },
      "minItems": 1,
      "maxItems": 5
    },
    "range": {
      "type": "array",
      "items": {
        "type": "integer",
        "minimum": 1,
        "maximum": 10800
      },
      "minItems": 1,
      "maxItems": 10
    },
    "range_type": {
      "type": "string",
      "enum": [
        "time",
        "distance"
      ]
    },
    "units": {
      "type": "string",
      "enum": [
        "m",
        "km",
        "mi"
      ]
    }
  },
  "required": [
    "profile",
    "locations",
    "range"
  ]
}
```

| `openrouteservice-geocode` | 使用 HeiGIT Pelias 执行正向地理编码，支持中国地址与 POI。 | `text, focus_point_lat, focus_point_lon, country, size` |

`openrouteservice-geocode` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "text": {
      "type": "string",
      "maxLength": 300
    },
    "focus_point_lat": {
      "type": "number",
      "minimum": -90,
      "maximum": 90
    },
    "focus_point_lon": {
      "type": "number",
      "minimum": -180,
      "maximum": 180
    },
    "country": {
      "type": "string",
      "pattern": "^[A-Z]{2}$"
    },
    "size": {
      "type": "integer",
      "minimum": 1,
      "maximum": 40
    }
  },
  "required": [
    "text"
  ]
}
```

| `opentopography-globaldem` | 通过 OpenTopography 获取全球 DEM 高程裁剪。 | `dem_type, south, north, west, east, output_format` |

`opentopography-globaldem` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "dem_type": {
      "type": "string",
      "enum": [
        "SRTMGL3",
        "SRTMGL1",
        "SRTMGL1_E",
        "AW3D30",
        "AW3D30_E",
        "SRTM15Plus",
        "NASADEM",
        "COP30",
        "COP90"
      ]
    },
    "south": {
      "type": "number",
      "minimum": -90,
      "maximum": 90
    },
    "north": {
      "type": "number",
      "minimum": -90,
      "maximum": 90
    },
    "west": {
      "type": "number",
      "minimum": -180,
      "maximum": 180
    },
    "east": {
      "type": "number",
      "minimum": -180,
      "maximum": 180
    },
    "output_format": {
      "type": "string",
      "enum": [
        "GTiff",
        "AAIGrid",
        "HFA"
      ]
    }
  },
  "required": [
    "dem_type",
    "south",
    "north",
    "west",
    "east"
  ]
}
```

| `geoboundaries-release` | 读取 geoBoundaries 全球行政区边界发布元数据。 | `iso3, admin_level, product` |

`geoboundaries-release` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "iso3": {
      "type": "string",
      "pattern": "^[A-Z]{3}$"
    },
    "admin_level": {
      "type": "string",
      "pattern": "^ADM[0-5]$"
    },
    "product": {
      "type": "string",
      "enum": [
        "gbOpen",
        "gbHumanitarian",
        "gbAuthoritative"
      ]
    }
  },
  "required": [
    "iso3",
    "admin_level"
  ]
}
```

| `soilgrids-wcs-capabilities` | 读取 SoilGrids 官方 WCS 图层能力，避免使用暂停的 REST beta。 | `property` |

`soilgrids-wcs-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "property": {
      "type": "string",
      "enum": [
        "bdod",
        "cec",
        "cfvo",
        "clay",
        "nitrogen",
        "ocd",
        "ocs",
        "phh2o",
        "sand",
        "silt",
        "soc"
      ]
    }
  },
  "required": [
    "property"
  ]
}
```

| `global-fishing-watch-vessels` | 检索 Global Fishing Watch v3 船舶身份，限非商业用途。 | `query, limit` |

`global-fishing-watch-vessels` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "maxLength": 100
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50
    }
  },
  "required": [
    "query"
  ]
}
```

| `opencharge-map-poi` | 查询 Open Charge Map 全球充电设施点位。 | `latitude, longitude, distance_km, max_results` |

`opencharge-map-poi` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
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
    "distance_km": {
      "type": "number",
      "minimum": 0.1,
      "maximum": 500
    },
    "max_results": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    }
  },
  "required": [
    "latitude",
    "longitude"
  ]
}
```

| `transitland-routes` | 查询 Transitland 公共交通路线目录。 | `bbox, operator_onestop_id, limit` |

`transitland-routes` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "bbox": {
      "type": "string",
      "pattern": "^-?[0-9.]+,-?[0-9.]+,-?[0-9.]+,-?[0-9.]+$"
    },
    "operator_onestop_id": {
      "type": "string",
      "maxLength": 100
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    }
  }
}
```

| `china-local-open-data-catalog` | 读取本地维护的中国大陆地方政府开放数据门户目录（浙江、深圳、上海、北京、广东、福建等），不访问上游。 | `无` |

`china-local-open-data-catalog` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `china-science-data-centers` | 读取本地维护的中国国家科学数据中心目录，标注公开目录/API/OGC/注册审批状态，不访问上游。 | `无` |

`china-science-data-centers` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "automatic_retry_allowed": false,
  "automatic_pagination_allowed": false,
  "redirects_allowed": false,
  "arbitrary_urls_allowed": false,
  "arbitrary_headers_allowed": false,
  "write_operations_allowed": false,
  "secret_values_exposed": false,
  "optional_secret_environment_variables": [
    "OPENROUTESERVICE_API_KEY",
    "GEONAMES_USERNAME",
    "OPENAQ_API_KEY",
    "OPENFDA_API_KEY",
    "RELIEFWEB_APPNAME",
    "HDX_HAPI_APP_IDENTIFIER",
    "IATI_API_KEY",
    "COMPANIES_HOUSE_API_KEY",
    "SAM_GOV_API_KEY",
    "OPENTOPOGRAPHY_API_KEY",
    "GLOBAL_FISHING_WATCH_API_TOKEN",
    "OPENCHARGEMAP_API_KEY",
    "TRANSITLAND_API_KEY"
  ],
  "noncommercial_only_operations": [
    "global-fishing-watch-vessels"
  ],
  "china_first_operations": [
    "china-local-open-data-catalog",
    "china-science-data-centers"
  ],
  "known_upstream_constraints": [
    {
      "provider": "China National Bureau of Statistics National Data",
      "status": "not_exposed_as_production_operation",
      "reason": "Official upstream WAF returned HTTP 403 UrlACL to the GitHub Actions public-cloud egress during production acceptance on 2026-08-03.",
      "evidence_issue": 527
    }
  ]
}
```

## Cloudflare 情报与云端浏览器 (`cloudflare`)

- 状态：`启用`
- 说明：通过 Cloudflare Browser Rendering 获取动态网页证据，通过 Radar 获取全球互联网流量、故障、排名和攻击态势，并读取 URL Scanner 扫描证据。
- 目录策略：开放22项固定能力；禁止 Global API Key、任意 Cloudflare API 路径、任意请求头、Cookie、代理、浏览器脚本、Workers/R2/D1/Queues 写操作和 URL Scanner 提交。
- 执行策略：每张票据最多一个固定 Cloudflare HTTPS 请求；不自动分页、不自动重试、不跟随重定向；浏览器目标必须为解析到公网地址的 HTTPS URL。
- 票据前缀：`[intel-cloudflare]`
- Secret环境变量名：`CLOUDFLARE_API_TOKEN`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`4055697908613064a89c7c3a6faf041b1abf7ccc81306b59898aaadfc2784de4`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地 Cloudflare 情报能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "maxProperties": 0
}
```

| `browser-content` | 通过 Cloudflare Browser Rendering 获取执行 JavaScript 后的完整 HTML。 | `url` |

`browser-content` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "url": {
      "type": "string",
      "minLength": 8,
      "maxLength": 2048,
      "pattern": "^https://[^\\s]+$"
    }
  },
  "required": [
    "url"
  ],
  "maxProperties": 1
}
```

| `browser-markdown` | 将网页渲染后正文转换为 Markdown。 | `url` |

`browser-markdown` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "url": {
      "type": "string",
      "minLength": 8,
      "maxLength": 2048,
      "pattern": "^https://[^\\s]+$"
    }
  },
  "required": [
    "url"
  ],
  "maxProperties": 1
}
```

| `browser-links` | 提取渲染后页面中的链接。 | `url` |

`browser-links` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "url": {
      "type": "string",
      "minLength": 8,
      "maxLength": 2048,
      "pattern": "^https://[^\\s]+$"
    }
  },
  "required": [
    "url"
  ],
  "maxProperties": 1
}
```

| `browser-screenshot` | 获取渲染后网页截图。 | `url` |

`browser-screenshot` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "url": {
      "type": "string",
      "minLength": 8,
      "maxLength": 2048,
      "pattern": "^https://[^\\s]+$"
    }
  },
  "required": [
    "url"
  ],
  "maxProperties": 1
}
```

| `browser-pdf` | 将渲染后网页输出为 PDF。 | `url` |

`browser-pdf` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "url": {
      "type": "string",
      "minLength": 8,
      "maxLength": 2048,
      "pattern": "^https://[^\\s]+$"
    }
  },
  "required": [
    "url"
  ],
  "maxProperties": 1
}
```

| `browser-snapshot` | 获取 HTML、Markdown、截图和可访问性树组合快照。 | `url` |

`browser-snapshot` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "url": {
      "type": "string",
      "minLength": 8,
      "maxLength": 2048,
      "pattern": "^https://[^\\s]+$"
    }
  },
  "required": [
    "url"
  ],
  "maxProperties": 1
}
```

| `browser-accessibility-tree` | 获取渲染后页面的可访问性树。 | `url` |

`browser-accessibility-tree` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "url": {
      "type": "string",
      "minLength": 8,
      "maxLength": 2048,
      "pattern": "^https://[^\\s]+$"
    }
  },
  "required": [
    "url"
  ],
  "maxProperties": 1
}
```

| `radar-global-search` | 搜索 Cloudflare Radar 的地点、ASN、报告和其他实体。 | `query, limit` |

`radar-global-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50,
      "default": 20
    }
  },
  "required": [
    "query"
  ],
  "maxProperties": 2
}
```

| `radar-outages` | 读取最新互联网中断与异常事件。 | `date_range, location, asn, limit, offset` |

`radar-outages` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "date_range": {
      "type": "string",
      "minLength": 2,
      "maxLength": 16,
      "pattern": "^(?:[1-9]|[1-9][0-9]|[1-2][0-9]{2}|3[0-5][0-9]|36[0-4])d(?:control)?$|^(?:[1-9]|[1-4][0-9]|5[0-2])w(?:control)?$"
    },
    "location": {
      "type": "string",
      "pattern": "^[A-Za-z]{2}$"
    },
    "asn": {
      "type": "integer",
      "minimum": 1,
      "maximum": 4294967295
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 20
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000,
      "default": 0
    }
  },
  "maxProperties": 5
}
```

| `radar-outage-locations` | 按国家或地区汇总互联网中断数量。 | `date_range, location, asn` |

`radar-outage-locations` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "date_range": {
      "type": "string",
      "minLength": 2,
      "maxLength": 16,
      "pattern": "^(?:[1-9]|[1-9][0-9]|[1-2][0-9]{2}|3[0-5][0-9]|36[0-4])d(?:control)?$|^(?:[1-9]|[1-4][0-9]|5[0-2])w(?:control)?$"
    },
    "location": {
      "type": "string",
      "pattern": "^[A-Za-z]{2}$"
    },
    "asn": {
      "type": "integer",
      "minimum": 1,
      "maximum": 4294967295
    }
  },
  "maxProperties": 3
}
```

| `radar-http-summary` | 按固定维度读取 HTTP 请求分布摘要。 | `date_range, location, asn, dimension` |

`radar-http-summary` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "date_range": {
      "type": "string",
      "minLength": 2,
      "maxLength": 16,
      "pattern": "^(?:[1-9]|[1-9][0-9]|[1-2][0-9]{2}|3[0-5][0-9]|36[0-4])d(?:control)?$|^(?:[1-9]|[1-4][0-9]|5[0-2])w(?:control)?$"
    },
    "location": {
      "type": "string",
      "pattern": "^[A-Za-z]{2}$"
    },
    "asn": {
      "type": "integer",
      "minimum": 1,
      "maximum": 4294967295
    },
    "dimension": {
      "type": "string",
      "enum": [
        "ADM1",
        "API_TRAFFIC",
        "AS",
        "BOT_CLASS",
        "BROWSER_FAMILY",
        "DEVICE_TYPE",
        "HTTP_PROTOCOL",
        "HTTP_VERSION",
        "IP_VERSION",
        "OS",
        "TLS_VERSION"
      ]
    }
  },
  "required": [
    "dimension"
  ],
  "maxProperties": 4
}
```

| `radar-http-timeseries` | 读取 HTTP 请求时间序列。 | `date_range, location, asn, aggregation_interval` |

`radar-http-timeseries` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "date_range": {
      "type": "string",
      "minLength": 2,
      "maxLength": 16,
      "pattern": "^(?:[1-9]|[1-9][0-9]|[1-2][0-9]{2}|3[0-5][0-9]|36[0-4])d(?:control)?$|^(?:[1-9]|[1-4][0-9]|5[0-2])w(?:control)?$"
    },
    "location": {
      "type": "string",
      "pattern": "^[A-Za-z]{2}$"
    },
    "asn": {
      "type": "integer",
      "minimum": 1,
      "maximum": 4294967295
    },
    "aggregation_interval": {
      "type": "string",
      "enum": [
        "15m",
        "1h",
        "1d",
        "1w"
      ]
    }
  },
  "maxProperties": 4
}
```

| `radar-ranking-top` | 读取热门或趋势域名排名。 | `date_range, location, asn, ranking_type, limit` |

`radar-ranking-top` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "date_range": {
      "type": "string",
      "minLength": 2,
      "maxLength": 16,
      "pattern": "^(?:[1-9]|[1-9][0-9]|[1-2][0-9]{2}|3[0-5][0-9]|36[0-4])d(?:control)?$|^(?:[1-9]|[1-4][0-9]|5[0-2])w(?:control)?$"
    },
    "location": {
      "type": "string",
      "pattern": "^[A-Za-z]{2}$"
    },
    "asn": {
      "type": "integer",
      "minimum": 1,
      "maximum": 4294967295
    },
    "ranking_type": {
      "type": "string",
      "enum": [
        "POPULAR",
        "TRENDING_RISE",
        "TRENDING_STEADY"
      ],
      "default": "POPULAR"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 20
    }
  },
  "maxProperties": 5
}
```

| `radar-ranking-domain` | 读取指定域名的 Cloudflare Radar 排名详情。 | `domain, location` |

`radar-ranking-domain` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "domain": {
      "type": "string",
      "minLength": 4,
      "maxLength": 253,
      "pattern": "^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\\.)+[A-Za-z]{2,63}$"
    },
    "location": {
      "type": "string",
      "pattern": "^[A-Za-z]{2}$"
    }
  },
  "required": [
    "domain"
  ],
  "maxProperties": 2
}
```

| `radar-layer7-summary` | 按固定维度读取第七层攻击分布摘要。 | `date_range, location, asn, dimension` |

`radar-layer7-summary` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "date_range": {
      "type": "string",
      "minLength": 2,
      "maxLength": 16,
      "pattern": "^(?:[1-9]|[1-9][0-9]|[1-2][0-9]{2}|3[0-5][0-9]|36[0-4])d(?:control)?$|^(?:[1-9]|[1-4][0-9]|5[0-2])w(?:control)?$"
    },
    "location": {
      "type": "string",
      "pattern": "^[A-Za-z]{2}$"
    },
    "asn": {
      "type": "integer",
      "minimum": 1,
      "maximum": 4294967295
    },
    "dimension": {
      "type": "string",
      "enum": [
        "HTTP_METHOD",
        "HTTP_VERSION",
        "IP_VERSION",
        "MANAGED_RULES",
        "MITIGATION_PRODUCT",
        "INDUSTRY",
        "VERTICAL"
      ]
    }
  },
  "required": [
    "dimension"
  ],
  "maxProperties": 4
}
```

| `radar-layer7-top-attacks` | 读取第七层攻击来源与目标地区的主要组合。 | `date_range, location, asn` |

`radar-layer7-top-attacks` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "date_range": {
      "type": "string",
      "minLength": 2,
      "maxLength": 16,
      "pattern": "^(?:[1-9]|[1-9][0-9]|[1-2][0-9]{2}|3[0-5][0-9]|36[0-4])d(?:control)?$|^(?:[1-9]|[1-4][0-9]|5[0-2])w(?:control)?$"
    },
    "location": {
      "type": "string",
      "pattern": "^[A-Za-z]{2}$"
    },
    "asn": {
      "type": "integer",
      "minimum": 1,
      "maximum": 4294967295
    }
  },
  "maxProperties": 3
}
```

| `urlscanner-search` | 使用受控查询语法搜索 Cloudflare URL Scanner 已有扫描。 | `query, size` |

`urlscanner-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    },
    "size": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 20
    }
  },
  "required": [
    "query"
  ],
  "maxProperties": 2
}
```

| `urlscanner-result` | 按扫描 UUID 读取 URL Scanner 结果与判定。 | `scan_id` |

`urlscanner-result` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "scan_id": {
      "type": "string",
      "format": "uuid",
      "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
    }
  },
  "required": [
    "scan_id"
  ],
  "maxProperties": 1
}
```

| `urlscanner-har` | 按扫描 UUID 读取 HAR 网络请求记录。 | `scan_id` |

`urlscanner-har` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "scan_id": {
      "type": "string",
      "format": "uuid",
      "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
    }
  },
  "required": [
    "scan_id"
  ],
  "maxProperties": 1
}
```

| `urlscanner-dom` | 按扫描 UUID 读取 Chrome 渲染后的 DOM。 | `scan_id` |

`urlscanner-dom` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "scan_id": {
      "type": "string",
      "format": "uuid",
      "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
    }
  },
  "required": [
    "scan_id"
  ],
  "maxProperties": 1
}
```

| `urlscanner-screenshot` | 按扫描 UUID 读取扫描截图。 | `scan_id` |

`urlscanner-screenshot` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "scan_id": {
      "type": "string",
      "format": "uuid",
      "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
    }
  },
  "required": [
    "scan_id"
  ],
  "maxProperties": 1
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "timeout_seconds_max": 120,
  "max_response_bytes": 20000000,
  "provider_concurrency_max": 1,
  "transient_retry_max": 0,
  "fixed_api_hosts": [
    "api.cloudflare.com"
  ],
  "fixed_products": [
    "Browser Rendering",
    "Radar",
    "URL Scanner"
  ],
  "arbitrary_cloudflare_paths_allowed": false,
  "arbitrary_urls_allowed": false,
  "arbitrary_headers_allowed": false,
  "custom_cookies_allowed": false,
  "custom_browser_scripts_allowed": false,
  "redirects_allowed": false,
  "automatic_pagination_allowed": false,
  "automatic_retry_allowed": false,
  "urlscanner_submission_allowed": false,
  "workers_deployment_allowed": false,
  "r2_writes_allowed": false,
  "d1_writes_allowed": false,
  "queue_writes_allowed": false,
  "write_operations_allowed": false,
  "secret_values_exposed": false
}
```

## FRED 官方经济与金融时间序列 (`fred`)

- 状态：`启用`
- 说明：通过圣路易斯联邦储备银行官方 FRED API v1 读取 FRED/ALFRED 分类、发布、序列、观测值、修订日期、来源和标签数据。
- 目录策略：开放25项固定只读JSON能力；禁止API v2批量发布下载、Maps shape文件、任意URL、路径、请求头、客户端密钥、自动翻页和写操作。
- 执行策略：FRED_API_KEY仅由GitHub Actions后端注入查询参数；每张票据最多一次GET，不自动重试、不跟随重定向，limit最大1000。
- 票据前缀：`[intel-fred]`
- Secret环境变量名：`FRED_API_KEY`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`ac2782dbd152d88560672bb3a4b9a9f3afde7d2f51322bd49ffecc01a2d6b0c9`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地FRED安全能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "maxProperties": 0
}
```

| `category` | 读取一个FRED分类。 | `category_id` |

`category` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "category_id"
  ],
  "properties": {
    "category_id": {
      "type": "integer",
      "minimum": 0,
      "maximum": 2147483647
    }
  }
}
```

| `category-children` | 读取一个分类的直接子分类。 | `category_id` |

`category-children` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "category_id"
  ],
  "properties": {
    "category_id": {
      "type": "integer",
      "minimum": 0,
      "maximum": 2147483647
    }
  }
}
```

| `category-related` | 读取一个分类的相关分类。 | `category_id` |

`category-related` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "category_id"
  ],
  "properties": {
    "category_id": {
      "type": "integer",
      "minimum": 0,
      "maximum": 2147483647
    }
  }
}
```

| `category-series` | 读取指定分类中的经济序列。 | `category_id, limit, offset, order_by, sort_order` |

`category-series` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "category_id"
  ],
  "properties": {
    "category_id": {
      "type": "integer",
      "minimum": 0,
      "maximum": 2147483647
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000
    },
    "order_by": {
      "type": "string",
      "enum": [
        "series_id",
        "title",
        "units",
        "frequency",
        "seasonal_adjustment",
        "realtime_start",
        "realtime_end",
        "last_updated",
        "observation_start",
        "observation_end",
        "popularity",
        "group_popularity"
      ]
    },
    "sort_order": {
      "type": "string",
      "enum": [
        "asc",
        "desc"
      ]
    }
  }
}
```

| `releases` | 读取全部经济数据发布目录。 | `limit, offset, order_by, sort_order` |

`releases` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000
    },
    "order_by": {
      "type": "string",
      "enum": [
        "release_id",
        "name",
        "press_release",
        "realtime_start",
        "realtime_end"
      ]
    },
    "sort_order": {
      "type": "string",
      "enum": [
        "asc",
        "desc"
      ]
    }
  }
}
```

| `releases-dates` | 读取所有发布的发布日期。 | `limit, offset, sort_order, include_release_dates_with_no_data` |

`releases-dates` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000
    },
    "sort_order": {
      "type": "string",
      "enum": [
        "asc",
        "desc"
      ]
    },
    "include_release_dates_with_no_data": {
      "type": "boolean"
    }
  }
}
```

| `release` | 读取一个经济数据发布。 | `release_id` |

`release` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "release_id"
  ],
  "properties": {
    "release_id": {
      "type": "integer",
      "minimum": 1,
      "maximum": 2147483647
    }
  }
}
```

| `release-dates` | 读取指定发布的历史发布日期。 | `release_id, limit, offset, sort_order, include_release_dates_with_no_data` |

`release-dates` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "release_id"
  ],
  "properties": {
    "release_id": {
      "type": "integer",
      "minimum": 1,
      "maximum": 2147483647
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000
    },
    "sort_order": {
      "type": "string",
      "enum": [
        "asc",
        "desc"
      ]
    },
    "include_release_dates_with_no_data": {
      "type": "boolean"
    }
  }
}
```

| `release-series` | 读取指定发布包含的经济序列。 | `release_id, limit, offset, order_by, sort_order` |

`release-series` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "release_id"
  ],
  "properties": {
    "release_id": {
      "type": "integer",
      "minimum": 1,
      "maximum": 2147483647
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000
    },
    "order_by": {
      "type": "string",
      "enum": [
        "series_id",
        "title",
        "units",
        "frequency",
        "seasonal_adjustment",
        "realtime_start",
        "realtime_end",
        "last_updated",
        "observation_start",
        "observation_end",
        "popularity",
        "group_popularity"
      ]
    },
    "sort_order": {
      "type": "string",
      "enum": [
        "asc",
        "desc"
      ]
    }
  }
}
```

| `release-sources` | 读取指定发布的数据来源。 | `release_id` |

`release-sources` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "release_id"
  ],
  "properties": {
    "release_id": {
      "type": "integer",
      "minimum": 1,
      "maximum": 2147483647
    }
  }
}
```

| `series` | 读取一个FRED经济序列的元数据。 | `series_id, realtime_start, realtime_end` |

`series` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "series_id"
  ],
  "properties": {
    "series_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]{1,64}$"
    },
    "realtime_start": {
      "type": "string",
      "format": "date"
    },
    "realtime_end": {
      "type": "string",
      "format": "date"
    }
  }
}
```

| `series-categories` | 读取一个序列所属分类。 | `series_id, realtime_start, realtime_end` |

`series-categories` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "series_id"
  ],
  "properties": {
    "series_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]{1,64}$"
    },
    "realtime_start": {
      "type": "string",
      "format": "date"
    },
    "realtime_end": {
      "type": "string",
      "format": "date"
    }
  }
}
```

| `series-observations` | 读取一个序列的观测值，可限定观测日期、实时期、单位和频率。 | `series_id, observation_start, observation_end, realtime_start, realtime_end, limit, offset, sort_order, units, frequency, aggregation_method, output_type, vintage_dates` |

`series-observations` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "series_id"
  ],
  "properties": {
    "series_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]{1,64}$"
    },
    "observation_start": {
      "type": "string",
      "format": "date"
    },
    "observation_end": {
      "type": "string",
      "format": "date"
    },
    "realtime_start": {
      "type": "string",
      "format": "date"
    },
    "realtime_end": {
      "type": "string",
      "format": "date"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000
    },
    "sort_order": {
      "type": "string",
      "enum": [
        "asc",
        "desc"
      ]
    },
    "units": {
      "type": "string",
      "enum": [
        "lin",
        "chg",
        "ch1",
        "pch",
        "pc1",
        "pca",
        "cch",
        "cca",
        "log"
      ]
    },
    "frequency": {
      "type": "string",
      "enum": [
        "d",
        "w",
        "bw",
        "m",
        "q",
        "sa",
        "a",
        "wef",
        "weth",
        "wew",
        "wetu",
        "wem",
        "wesu",
        "wesa",
        "bwew",
        "bwem"
      ]
    },
    "aggregation_method": {
      "type": "string",
      "enum": [
        "avg",
        "sum",
        "eop"
      ]
    },
    "output_type": {
      "type": "integer",
      "minimum": 1,
      "maximum": 4
    },
    "vintage_dates": {
      "type": "array",
      "minItems": 1,
      "maxItems": 50,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "format": "date"
      }
    }
  }
}
```

| `series-release` | 读取一个序列对应的数据发布。 | `series_id, realtime_start, realtime_end` |

`series-release` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "series_id"
  ],
  "properties": {
    "series_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]{1,64}$"
    },
    "realtime_start": {
      "type": "string",
      "format": "date"
    },
    "realtime_end": {
      "type": "string",
      "format": "date"
    }
  }
}
```

| `series-search` | 按关键词或序列ID搜索经济序列。 | `search_text, search_type, limit, offset, order_by, sort_order` |

`series-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "search_text"
  ],
  "properties": {
    "search_text": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "search_type": {
      "type": "string",
      "enum": [
        "full_text",
        "series_id"
      ]
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000
    },
    "order_by": {
      "type": "string",
      "enum": [
        "search_rank",
        "series_id",
        "title",
        "units",
        "frequency",
        "seasonal_adjustment",
        "realtime_start",
        "realtime_end",
        "last_updated",
        "observation_start",
        "observation_end",
        "popularity",
        "group_popularity"
      ]
    },
    "sort_order": {
      "type": "string",
      "enum": [
        "asc",
        "desc"
      ]
    }
  }
}
```

| `series-updates` | 读取FRED服务器最近更新的经济序列。 | `limit, offset, filter_value` |

`series-updates` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000
    },
    "filter_value": {
      "type": "string",
      "enum": [
        "all",
        "macro",
        "regional"
      ]
    }
  }
}
```

| `series-vintagedates` | 读取一个序列发生修订或新增观测的历史日期。 | `series_id, limit, offset, sort_order` |

`series-vintagedates` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "series_id"
  ],
  "properties": {
    "series_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]{1,64}$"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000
    },
    "sort_order": {
      "type": "string",
      "enum": [
        "asc",
        "desc"
      ]
    }
  }
}
```

| `sources` | 读取全部经济数据来源。 | `limit, offset, order_by, sort_order` |

`sources` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000
    },
    "order_by": {
      "type": "string",
      "enum": [
        "source_id",
        "name",
        "realtime_start",
        "realtime_end"
      ]
    },
    "sort_order": {
      "type": "string",
      "enum": [
        "asc",
        "desc"
      ]
    }
  }
}
```

| `source` | 读取一个经济数据来源。 | `source_id` |

`source` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "source_id"
  ],
  "properties": {
    "source_id": {
      "type": "integer",
      "minimum": 1,
      "maximum": 2147483647
    }
  }
}
```

| `source-releases` | 读取指定来源对应的发布。 | `source_id, limit, offset, order_by, sort_order` |

`source-releases` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "source_id"
  ],
  "properties": {
    "source_id": {
      "type": "integer",
      "minimum": 1,
      "maximum": 2147483647
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000
    },
    "order_by": {
      "type": "string",
      "enum": [
        "release_id",
        "name",
        "press_release",
        "realtime_start",
        "realtime_end"
      ]
    },
    "sort_order": {
      "type": "string",
      "enum": [
        "asc",
        "desc"
      ]
    }
  }
}
```

| `tags` | 读取或搜索FRED标签。 | `tag_names, tag_group_id, search_text, limit, offset, order_by, sort_order` |

`tags` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "tag_names": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 100
      }
    },
    "tag_group_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]{1,32}$"
    },
    "search_text": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000
    },
    "order_by": {
      "type": "string",
      "enum": [
        "series_count",
        "popularity",
        "created",
        "name",
        "group_id"
      ]
    },
    "sort_order": {
      "type": "string",
      "enum": [
        "asc",
        "desc"
      ]
    }
  }
}
```

| `related-tags` | 读取与给定标签关联的标签。 | `tag_names, exclude_tag_names, tag_group_id, search_text, limit, offset, order_by, sort_order` |

`related-tags` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "tag_names"
  ],
  "properties": {
    "tag_names": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 100
      }
    },
    "exclude_tag_names": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 100
      }
    },
    "tag_group_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]{1,32}$"
    },
    "search_text": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000
    },
    "order_by": {
      "type": "string",
      "enum": [
        "series_count",
        "popularity",
        "created",
        "name",
        "group_id"
      ]
    },
    "sort_order": {
      "type": "string",
      "enum": [
        "asc",
        "desc"
      ]
    }
  }
}
```

| `tags-series` | 读取匹配一组标签的经济序列。 | `tag_names, exclude_tag_names, limit, offset, order_by, sort_order` |

`tags-series` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "tag_names"
  ],
  "properties": {
    "tag_names": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 100
      }
    },
    "exclude_tag_names": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 100
      }
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000
    },
    "order_by": {
      "type": "string",
      "enum": [
        "series_id",
        "title",
        "units",
        "frequency",
        "seasonal_adjustment",
        "realtime_start",
        "realtime_end",
        "last_updated",
        "observation_start",
        "observation_end",
        "popularity",
        "group_popularity"
      ]
    },
    "sort_order": {
      "type": "string",
      "enum": [
        "asc",
        "desc"
      ]
    }
  }
}
```

| `series-tags` | 读取一个经济序列的标签。 | `series_id, order_by, sort_order` |

`series-tags` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "series_id"
  ],
  "properties": {
    "series_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]{1,64}$"
    },
    "order_by": {
      "type": "string",
      "enum": [
        "series_count",
        "popularity",
        "created",
        "name",
        "group_id"
      ]
    },
    "sort_order": {
      "type": "string",
      "enum": [
        "asc",
        "desc"
      ]
    }
  }
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "transient_retry_max": 0,
  "provider_concurrency_max": 1,
  "timeout_seconds_max": 60,
  "max_response_bytes": 10000000,
  "rows_per_request_max": 1000,
  "fixed_api_host": "api.stlouisfed.org",
  "fixed_api_prefix": "/fred",
  "automatic_pagination_allowed": false,
  "bulk_v2_release_download_allowed": false,
  "maps_shapefile_download_allowed": false,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "arbitrary_query_parameters_allowed": false,
  "client_supplied_credentials_allowed": false,
  "redirects_allowed": false,
  "write_operations_allowed": false,
  "secret_values_exposed": false,
  "authentication_required": true
}
```

## Hugging Face Hub 公共模型与数据情报 (`huggingface-hub`)

- 状态：`启用`
- 说明：读取 Hugging Face Hub 上公开模型、数据集、Spaces、仓库目录、引用和文件元数据，用于模型市场、数据源与开源能力情报发现。
- 目录策略：仅开放11项固定公共只读能力；不使用登录令牌，不读取私有仓库，不执行推理、训练、Jobs、Space调用、文件下载、仓库克隆、写入或访问审批操作。
- 执行策略：固定使用 huggingface.co 官方 Hub API；每张票据最多一次受控 Hub 方法调用，搜索最多50项，目录最多100项，路径查询最多20项；不自动翻页、不递归全仓、不持久化缓存。
- 票据前缀：`[intel-huggingface]`
- Secret环境变量名：`无`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`6be00a64b355317fc9cc44cda61c226f088e6409e2ef23245edcd7ef1e1cb0c0`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地 Hugging Face 安全能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "maxProperties": 0
}
```

| `models-search` | 按关键词、作者、任务、库和排序方式搜索公开模型，最多50项。 | `query, author, task, library, sort, limit, gated` |

`models-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100
    },
    "author": {
      "type": "string",
      "minLength": 1,
      "maxLength": 96
    },
    "task": {
      "type": "string",
      "minLength": 1,
      "maxLength": 80
    },
    "library": {
      "type": "string",
      "minLength": 1,
      "maxLength": 80
    },
    "sort": {
      "type": "string",
      "enum": [
        "trendingScore",
        "downloads",
        "likes",
        "createdAt",
        "lastModified"
      ]
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50,
      "default": 20
    },
    "gated": {
      "type": "boolean"
    }
  },
  "maxProperties": 7
}
```

| `model-info` | 读取一个公开模型仓库的元数据、标签、下载、卡片和文件清单摘要。 | `repo_id, revision` |

`model-info` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "repo_id"
  ],
  "properties": {
    "repo_id": {
      "type": "string",
      "minLength": 1,
      "maxLength": 193,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,95}(?:/[A-Za-z0-9][A-Za-z0-9._-]{0,95})?$"
    },
    "revision": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._/-]{0,99}$"
    }
  },
  "maxProperties": 2
}
```

| `model-security` | 读取公开模型仓库的 Hub 安全扫描状态与模型元数据。 | `repo_id, revision` |

`model-security` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "repo_id"
  ],
  "properties": {
    "repo_id": {
      "type": "string",
      "minLength": 1,
      "maxLength": 193,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,95}(?:/[A-Za-z0-9][A-Za-z0-9._-]{0,95})?$"
    },
    "revision": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._/-]{0,99}$"
    }
  },
  "maxProperties": 2
}
```

| `datasets-search` | 按关键词、作者、语言、任务类别和排序方式搜索公开数据集，最多50项。 | `query, author, language, task_category, sort, limit, gated` |

`datasets-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100
    },
    "author": {
      "type": "string",
      "minLength": 1,
      "maxLength": 96
    },
    "language": {
      "type": "string",
      "minLength": 2,
      "maxLength": 32
    },
    "task_category": {
      "type": "string",
      "minLength": 1,
      "maxLength": 80
    },
    "sort": {
      "type": "string",
      "enum": [
        "trendingScore",
        "downloads",
        "likes",
        "createdAt",
        "lastModified"
      ]
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50,
      "default": 20
    },
    "gated": {
      "type": "boolean"
    }
  },
  "maxProperties": 7
}
```

| `dataset-info` | 读取一个公开数据集仓库的元数据、标签、卡片和文件清单摘要。 | `repo_id, revision` |

`dataset-info` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "repo_id"
  ],
  "properties": {
    "repo_id": {
      "type": "string",
      "minLength": 1,
      "maxLength": 193,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,95}(?:/[A-Za-z0-9][A-Za-z0-9._-]{0,95})?$"
    },
    "revision": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._/-]{0,99}$"
    }
  },
  "maxProperties": 2
}
```

| `spaces-search` | 按关键词、作者和排序方式搜索公开 Spaces，最多50项。 | `query, author, sort, limit` |

`spaces-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100
    },
    "author": {
      "type": "string",
      "minLength": 1,
      "maxLength": 96
    },
    "sort": {
      "type": "string",
      "enum": [
        "trendingScore",
        "likes",
        "createdAt",
        "lastModified"
      ]
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50,
      "default": 20
    }
  },
  "maxProperties": 4
}
```

| `space-info` | 读取一个公开 Space 的元数据、SDK、关联模型和数据集，不调用 Space。 | `repo_id, revision` |

`space-info` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "repo_id"
  ],
  "properties": {
    "repo_id": {
      "type": "string",
      "minLength": 1,
      "maxLength": 193,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,95}(?:/[A-Za-z0-9][A-Za-z0-9._-]{0,95})?$"
    },
    "revision": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._/-]{0,99}$"
    }
  },
  "maxProperties": 2
}
```

| `repo-tree` | 读取公开模型、数据集或 Space 指定目录的非递归文件树，最多100项。 | `repo_id, repo_type, revision, path, limit` |

`repo-tree` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "repo_id",
    "repo_type"
  ],
  "properties": {
    "repo_id": {
      "type": "string",
      "minLength": 1,
      "maxLength": 193,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,95}(?:/[A-Za-z0-9][A-Za-z0-9._-]{0,95})?$"
    },
    "repo_type": {
      "type": "string",
      "enum": [
        "model",
        "dataset",
        "space"
      ]
    },
    "revision": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._/-]{0,99}$"
    },
    "path": {
      "type": "string",
      "maxLength": 300,
      "pattern": "^(?!/)(?!.*(?:^|/)\\.\\.(?:/|$))[^\\x00-\\x1f\\x7f]*$"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 100
    }
  },
  "maxProperties": 5
}
```

| `repo-refs` | 读取公开模型、数据集或 Space 的分支和标签引用，不含 Pull Request 引用。 | `repo_id, repo_type` |

`repo-refs` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "repo_id",
    "repo_type"
  ],
  "properties": {
    "repo_id": {
      "type": "string",
      "minLength": 1,
      "maxLength": 193,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,95}(?:/[A-Za-z0-9][A-Za-z0-9._-]{0,95})?$"
    },
    "repo_type": {
      "type": "string",
      "enum": [
        "model",
        "dataset",
        "space"
      ]
    }
  },
  "maxProperties": 2
}
```

| `repo-paths-info` | 读取公开仓库最多20个指定路径的大小、Blob、LFS/Xet与安全元数据。 | `repo_id, repo_type, revision, paths, expand` |

`repo-paths-info` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "repo_id",
    "repo_type",
    "paths"
  ],
  "properties": {
    "repo_id": {
      "type": "string",
      "minLength": 1,
      "maxLength": 193,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,95}(?:/[A-Za-z0-9][A-Za-z0-9._-]{0,95})?$"
    },
    "repo_type": {
      "type": "string",
      "enum": [
        "model",
        "dataset",
        "space"
      ]
    },
    "revision": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._/-]{0,99}$"
    },
    "paths": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 300,
        "pattern": "^(?!/)(?!.*(?:^|/)\\.\\.(?:/|$))[^\\x00-\\x1f\\x7f]+$"
      }
    },
    "expand": {
      "type": "boolean",
      "default": false
    }
  },
  "maxProperties": 5
}
```

限制：

```json
{
  "hub_method_calls_per_ticket_max": 1,
  "provider_concurrency_max": 1,
  "search_results_max": 50,
  "repo_tree_entries_max": 100,
  "repo_paths_per_ticket_max": 20,
  "timeout_seconds_max": 60,
  "max_response_bytes": 10000000,
  "fixed_api_host": "huggingface.co",
  "public_repositories_only": true,
  "authentication_used": false,
  "private_repositories_allowed": false,
  "gated_file_download_allowed": false,
  "inference_allowed": false,
  "training_or_jobs_allowed": false,
  "space_invocation_allowed": false,
  "repository_clone_allowed": false,
  "file_download_allowed": false,
  "recursive_full_repository_listing_allowed": false,
  "automatic_pagination_allowed": false,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_headers_allowed": false,
  "client_supplied_credentials_allowed": false,
  "write_operations_allowed": false,
  "secret_values_exposed": false
}
```

## 证据标准化、去重、谱系与传输清单 (`evidence-standardization`)

- 状态：`启用`
- 说明：对已采集的公开、非个人证据执行本地规范化、指纹去重、来源谱系、版本差异、STIX离线校验、来源质量画像和传输清单生成。
- 目录策略：仅处理票据内已提供的公开、非个人结构化证据；不访问网络、不读取文件路径、不接受代码、不推断个人身份。
- 执行策略：每张票据执行一个固定本地操作；输入有界，输出包含哈希、状态和零网络零模型调用回执。
- 票据前缀：`[intel-evidence-standardize]`
- Secret环境变量名：`无`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`8e400600c569dcbc0f510453cd62b2adcb54f65371641e18ad2a2b65c8962bfc`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地证据标准化能力目录，不访问外部网络。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "maxProperties": 0
}
```

| `normalize-evidence-records` | 将公开、非个人的来源记录规范化为统一证据记录并生成内容哈希和稳定记录ID。 | `records` |

`normalize-evidence-records` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "records"
  ],
  "properties": {
    "records": {
      "type": "array",
      "minItems": 1,
      "maxItems": 1000,
      "items": {
        "type": "object"
      }
    }
  }
}
```

| `content-fingerprint` | 生成SHA-256和64位SimHash，识别精确重复和受限近重复内容。 | `near_duplicate_hamming_threshold, texts` |

`content-fingerprint` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "texts"
  ],
  "properties": {
    "texts": {
      "type": "array",
      "minItems": 1,
      "maxItems": 1000,
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 200000
      }
    },
    "near_duplicate_hamming_threshold": {
      "type": "integer",
      "minimum": 0,
      "maximum": 16
    }
  }
}
```

| `provenance-lineage` | 验证来源、快照、处理和传输节点形成的有向无环谱系图。 | `edges, nodes` |

`provenance-lineage` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "nodes",
    "edges"
  ],
  "properties": {
    "nodes": {
      "type": "array",
      "minItems": 1,
      "maxItems": 5000,
      "items": {
        "type": "object"
      }
    },
    "edges": {
      "type": "array",
      "maxItems": 20000,
      "items": {
        "type": "object"
      }
    }
  }
}
```

| `timeline-version-diff` | 按UTC时间排序公开文档版本并计算逐版本变更摘要。 | `versions` |

`timeline-version-diff` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "versions"
  ],
  "properties": {
    "versions": {
      "type": "array",
      "minItems": 2,
      "maxItems": 200,
      "items": {
        "type": "object"
      }
    }
  }
}
```

| `stix-bundle-validate` | 离线验证STIX 2.1 Bundle的对象身份、重复项和内部引用完整性。 | `bundle` |

`stix-bundle-validate` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "bundle"
  ],
  "properties": {
    "bundle": {
      "type": "object"
    }
  }
}
```

| `transfer-package-manifest` | 为GPTs证据中继生成公开、非个人文件清单和规范哈希。 | `files` |

`transfer-package-manifest` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "files"
  ],
  "properties": {
    "files": {
      "type": "array",
      "minItems": 1,
      "maxItems": 1000,
      "items": {
        "type": "object"
      }
    }
  }
}
```

| `source-quality-profile` | 按权威性、直接性、时效性、交叉印证和方法透明度形成来源质量画像。 | `sources` |

`source-quality-profile` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "sources"
  ],
  "properties": {
    "sources": {
      "type": "array",
      "minItems": 1,
      "maxItems": 1000,
      "items": {
        "type": "object"
      }
    }
  }
}
```

限制：

```json
{
  "requests_per_ticket": 0,
  "timeout_seconds_max": 60,
  "max_response_bytes": 10000000,
  "records_max": 1000,
  "graph_nodes_max": 5000,
  "graph_edges_max": 20000,
  "arbitrary_urls_allowed": false,
  "arbitrary_files_allowed": false,
  "arbitrary_code_allowed": false,
  "network_allowed": false,
  "personal_data_allowed": false,
  "secret_values_exposed": false
}
```

## 全球研报、政策、法律与公司文本情报 (`global-research-intelligence`)

- 状态：`启用`
- 说明：直接访问固定官方研究、出版、立法、司法、公司披露和金融文本 API，并提供经核验的中国及全球高价值来源清单。
- 目录策略：优先官方 API；每张票据仅执行一个固定只读操作；禁止任意 URL、任意主机、任意路径、自动翻页、批量下载、写入、交易和密钥回显。
- 执行策略：所有请求由固定操作构造器生成。需要凭证的操作仅从后端环境读取对应密钥；SEC 操作要求仓库变量 SEC_USER_AGENT 标识调用方。
- 票据前缀：`[intel-global-research]`
- Secret环境变量名：`无`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`6725f2703d87d7ae7a6d87a7e8398aaa34cacc8787812e797f916b8ce612451a`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地安全能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `source-inventory` | 读取用户提出的工具和数据源逐项核验、去重、替代与归属清单。 | `无` |

`source-inventory` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `think-tank-source-catalog` | 读取固定全球及中国智库、研究机构、政策报告来源目录，供现有网页/PDF读取 Provider 使用。 | `region, topic` |

`think-tank-source-catalog` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "region": {
      "type": "string",
      "enum": [
        "all",
        "china",
        "global",
        "north-america",
        "europe",
        "asia"
      ]
    },
    "topic": {
      "type": "string",
      "enum": [
        "all",
        "macro",
        "trade",
        "finance",
        "technology",
        "industry",
        "policy",
        "security"
      ]
    }
  }
}
```

| `search-arxiv` | 按受限检索式查询 arXiv 元数据、摘要、作者和 PDF 链接。 | `query, start, max_results, sort_by, sort_order` |

`search-arxiv` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "query"
  ],
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    },
    "start": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000
    },
    "max_results": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    },
    "sort_by": {
      "type": "string",
      "enum": [
        "relevance",
        "lastUpdatedDate",
        "submittedDate"
      ]
    },
    "sort_order": {
      "type": "string",
      "enum": [
        "ascending",
        "descending"
      ]
    }
  }
}
```

| `get-arxiv-entry` | 按 arXiv ID 读取单篇或少量论文元数据、摘要和 PDF 链接。 | `ids` |

`get-arxiv-entry` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ids"
  ],
  "properties": {
    "ids": {
      "type": "array",
      "minItems": 1,
      "maxItems": 20,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[A-Za-z0-9.\\/-]{1,40}$"
      }
    }
  }
}
```

| `identify-un-digital-library` | 读取联合国数字图书馆 OAI-PMH 仓库身份和能力信息。 | `无` |

`identify-un-digital-library` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `list-un-digital-library-records` | 按 OAI-PMH 规范分批读取联合国数字图书馆公开元数据。 | `metadata_prefix, set, from, until, resumption_token` |

`list-un-digital-library-records` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "metadata_prefix": {
      "type": "string",
      "enum": [
        "oai_dc",
        "marcxml"
      ]
    },
    "set": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "from": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "until": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "resumption_token": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    }
  }
}
```

| `get-un-digital-library-record` | 按 OAI 标识符读取联合国数字图书馆单条公开元数据。 | `identifier, metadata_prefix` |

`get-un-digital-library-record` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "identifier"
  ],
  "properties": {
    "identifier": {
      "type": "string",
      "minLength": 3,
      "maxLength": 300
    },
    "metadata_prefix": {
      "type": "string",
      "enum": [
        "oai_dc",
        "marcxml"
      ]
    }
  }
}
```

| `get-sec-submissions` | 按十位 CIK 读取 SEC 官方公司申报历史和最新文件元数据。 | `cik` |

`get-sec-submissions` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "cik"
  ],
  "properties": {
    "cik": {
      "type": "string",
      "pattern": "^[0-9]{1,10}$"
    }
  }
}
```

| `get-sec-company-facts` | 按十位 CIK 读取 SEC 官方 XBRL 公司全部事实数据。 | `cik` |

`get-sec-company-facts` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "cik"
  ],
  "properties": {
    "cik": {
      "type": "string",
      "pattern": "^[0-9]{1,10}$"
    }
  }
}
```

| `get-sec-xbrl-frame` | 读取 SEC 官方 XBRL 跨公司财务事实截面。 | `taxonomy, tag, unit, period` |

`get-sec-xbrl-frame` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "taxonomy",
    "tag",
    "unit",
    "period"
  ],
  "properties": {
    "taxonomy": {
      "type": "string",
      "enum": [
        "us-gaap",
        "dei",
        "ifrs-full"
      ]
    },
    "tag": {
      "type": "string",
      "pattern": "^[A-Za-z][A-Za-z0-9]{1,99}$"
    },
    "unit": {
      "type": "string",
      "pattern": "^[A-Za-z0-9-]{1,40}$"
    },
    "period": {
      "type": "string",
      "pattern": "^CY[0-9]{4}(Q[1-4])?I?$"
    }
  }
}
```

| `list-congress-bills` | 读取 Congress.gov v3 法案列表，可按届次、类型和更新时间范围约束。 | `congress, bill_type, from_datetime, to_datetime, limit, offset` |

`list-congress-bills` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "congress": {
      "type": "integer",
      "minimum": 1,
      "maximum": 200
    },
    "bill_type": {
      "type": "string",
      "enum": [
        "hr",
        "s",
        "hjres",
        "sjres",
        "hconres",
        "sconres",
        "hres",
        "sres"
      ]
    },
    "from_datetime": {
      "type": "string",
      "maxLength": 40
    },
    "to_datetime": {
      "type": "string",
      "maxLength": 40
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000
    }
  }
}
```

| `list-congress-hearings` | 读取 Congress.gov v3 听证会列表。 | `congress, chamber, limit, offset` |

`list-congress-hearings` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "congress": {
      "type": "integer",
      "minimum": 1,
      "maximum": 200
    },
    "chamber": {
      "type": "string",
      "enum": [
        "house",
        "senate"
      ]
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000
    }
  }
}
```

| `get-congress-crs-report` | 按 CRS 报告编号读取 Congress.gov 官方国会研究处报告元数据。 | `report_number` |

`get-congress-crs-report` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "report_number"
  ],
  "properties": {
    "report_number": {
      "type": "string",
      "pattern": "^[A-Za-z]{1,4}[0-9-]{1,20}$"
    }
  }
}
```

| `search-courtlistener` | 通过 CourtListener v4 搜索判例、案卷、法官和口头辩论资料。 | `query, type, order_by, page` |

`search-courtlistener` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "query"
  ],
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    },
    "type": {
      "type": "string",
      "enum": [
        "o",
        "r",
        "p",
        "oa"
      ]
    },
    "order_by": {
      "type": "string",
      "enum": [
        "score desc",
        "dateFiled desc",
        "dateFiled asc"
      ]
    },
    "page": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    }
  }
}
```

| `get-courtlistener-opinion` | 按数字 ID 读取 CourtListener v4 单份公开司法意见。 | `opinion_id` |

`get-courtlistener-opinion` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "opinion_id"
  ],
  "properties": {
    "opinion_id": {
      "type": "integer",
      "minimum": 1,
      "maximum": 999999999
    }
  }
}
```

| `search-nasdaq-data-link` | 搜索 Nasdaq Data Link 数据集目录。 | `query, page, per_page` |

`search-nasdaq-data-link` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "query"
  ],
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 300
    },
    "page": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    },
    "per_page": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    }
  }
}
```

| `get-nasdaq-dataset` | 按数据库代码和数据集代码读取 Nasdaq Data Link 时间序列数据。 | `database_code, dataset_code, start_date, end_date, rows, order, collapse, transform` |

`get-nasdaq-dataset` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "database_code",
    "dataset_code"
  ],
  "properties": {
    "database_code": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_-]{1,30}$"
    },
    "dataset_code": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_.-]{1,80}$"
    },
    "start_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "end_date": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "rows": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10000
    },
    "order": {
      "type": "string",
      "enum": [
        "asc",
        "desc"
      ]
    },
    "collapse": {
      "type": "string",
      "enum": [
        "none",
        "daily",
        "weekly",
        "monthly",
        "quarterly",
        "annual"
      ]
    },
    "transform": {
      "type": "string",
      "enum": [
        "none",
        "diff",
        "rdiff",
        "rdiff_from",
        "cumul",
        "normalize"
      ]
    }
  }
}
```

| `finnhub-company-news` | 按股票代码和日期范围读取 Finnhub 公司新闻。 | `symbol, from, to` |

`finnhub-company-news` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "symbol",
    "from",
    "to"
  ],
  "properties": {
    "symbol": {
      "type": "string",
      "pattern": "^[A-Za-z0-9.:-]{1,30}$"
    },
    "from": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    },
    "to": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  }
}
```

| `finnhub-transcripts-list` | 读取公司财报电话会议文本目录。 | `symbol` |

`finnhub-transcripts-list` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "symbol"
  ],
  "properties": {
    "symbol": {
      "type": "string",
      "pattern": "^[A-Za-z0-9.:-]{1,30}$"
    }
  }
}
```

| `finnhub-transcript` | 按文本 ID 读取财报电话会议原文。 | `transcript_id` |

`finnhub-transcript` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "transcript_id"
  ],
  "properties": {
    "transcript_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._:-]{1,120}$"
    }
  }
}
```

| `scopus-search` | 通过 Elsevier Scopus Search API 检索论文、作者、机构和主题元数据。 | `query, start, count, sort, view` |

`scopus-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "query"
  ],
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 1000
    },
    "start": {
      "type": "integer",
      "minimum": 0,
      "maximum": 5000
    },
    "count": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    },
    "sort": {
      "type": "string",
      "enum": [
        "-coverDate",
        "coverDate",
        "relevancy",
        "-citedby-count"
      ]
    },
    "view": {
      "type": "string",
      "enum": [
        "STANDARD",
        "COMPLETE"
      ]
    }
  }
}
```

| `scopus-abstract` | 按 Scopus EID 读取论文摘要与书目信息。 | `eid, view` |

`scopus-abstract` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "eid"
  ],
  "properties": {
    "eid": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._:-]{3,80}$"
    },
    "view": {
      "type": "string",
      "enum": [
        "META",
        "META_ABS",
        "FULL"
      ]
    }
  }
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "provider_concurrency_max": 1,
  "records_per_ticket_max": 100,
  "timeout_seconds_max": 120,
  "max_response_bytes": 20000000,
  "fixed_api_hosts": [
    "export.arxiv.org",
    "digitallibrary.un.org",
    "data.sec.gov",
    "api.congress.gov",
    "www.courtlistener.com",
    "data.nasdaq.com",
    "finnhub.io",
    "api.elsevier.com"
  ],
  "credential_environment_variables": {
    "sec": "SEC_USER_AGENT",
    "congress": "CONGRESS_API_KEY",
    "courtlistener": "COURTLISTENER_API_TOKEN",
    "nasdaq": "NASDAQ_DATA_LINK_API_KEY",
    "finnhub": "FINNHUB_API_KEY",
    "scopus": "SCOPUS_API_KEY",
    "scopus_insttoken_optional": "SCOPUS_INST_TOKEN"
  },
  "automatic_retry_allowed": false,
  "automatic_pagination_allowed": false,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "document_body_bulk_download_allowed": false,
  "write_operations_allowed": false,
  "trading_or_order_execution_allowed": false,
  "personal_data_targeting_allowed": false,
  "secret_values_exposed": false
}
```

## OpenBB 免费官方数据补充层 (`openbb-free`)

- 状态：`启用`
- 说明：通过模块化 OpenBB Core 与免 Key Provider 读取 ECB 汇率、纽约联储有效联邦基金利率、SOFR 和 Fama-French 因子；同时公开安装包与免费/Key/付费分类。不会安装 openbb[all]，不会启用交易、付费订阅或任意 Provider。
- 目录策略：仅安装锁定版本的 openbb-core、openbb-ecb、openbb-federal-reserve、openbb-famafrench。开放7项固定只读能力；禁止任意模型、任意 Provider、任意 URL、客户端密钥、交易、写入、自动翻页、自动重试和付费数据调用。
- 执行策略：每张票据执行一个固定操作。远程操作只调用 OpenBB 官方扩展中明确免 Key的 Fetcher；ECB 汇率一次请求，纽约联储利率一次请求，Fama-French 因子一次受限下载。超时与输出体积受票据限制。
- 票据前缀：`[intel-openbb-free]`
- Secret环境变量名：`无`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`3f8b099f7c1556b5df44c13f39398a5be0cda460066afd7d8f73f277a907a68c`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地 OpenBB 免费层安全能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "maxProperties": 0
}
```

| `provider-access-matrix` | 读取 OpenBB Provider 的免 Key、免费 Key、付费和未启用分类，不访问上游。 | `无` |

`provider-access-matrix` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "maxProperties": 0
}
```

| `package-manifest` | 读取当前锁定的 OpenBB 包、版本、许可证和启用模块，不访问上游。 | `无` |

`package-manifest` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "maxProperties": 0
}
```

| `ecb-currency-reference-rates` | 通过 OpenBB ECB Fetcher 读取欧洲央行最新欧元参考汇率。 | `无` |

`ecb-currency-reference-rates` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "maxProperties": 0
}
```

| `federal-reserve-federal-funds-rate` | 通过 OpenBB Federal Reserve Fetcher 读取指定日期范围的有效联邦基金利率。 | `start_date, end_date` |

`federal-reserve-federal-funds-rate` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "start_date",
    "end_date"
  ],
  "properties": {
    "start_date": {
      "type": "string",
      "format": "date"
    },
    "end_date": {
      "type": "string",
      "format": "date"
    }
  }
}
```

| `federal-reserve-sofr` | 通过 OpenBB Federal Reserve Fetcher 读取指定日期范围的 SOFR。 | `start_date, end_date` |

`federal-reserve-sofr` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "start_date",
    "end_date"
  ],
  "properties": {
    "start_date": {
      "type": "string",
      "format": "date"
    },
    "end_date": {
      "type": "string",
      "format": "date"
    }
  }
}
```

| `fama-french-factors` | 通过 OpenBB Fama-French Fetcher 读取受限日期范围的研究因子数据。 | `region, factor, frequency, start_date, end_date` |

`fama-french-factors` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "region",
    "factor",
    "frequency",
    "start_date",
    "end_date"
  ],
  "properties": {
    "region": {
      "type": "string",
      "enum": [
        "america",
        "north_america",
        "europe",
        "japan",
        "asia_pacific_ex_japan",
        "developed",
        "developed_ex_us",
        "emerging"
      ]
    },
    "factor": {
      "type": "string",
      "enum": [
        "5_factors",
        "3_factors",
        "momentum",
        "st_reversal",
        "lt_reversal"
      ]
    },
    "frequency": {
      "type": "string",
      "enum": [
        "daily",
        "weekly",
        "monthly",
        "annual"
      ]
    },
    "start_date": {
      "type": "string",
      "format": "date"
    },
    "end_date": {
      "type": "string",
      "format": "date"
    }
  }
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "transient_retry_max": 0,
  "provider_concurrency_max": 1,
  "timeout_seconds_max": 120,
  "max_response_bytes": 10000000,
  "rows_per_response_max": 10000,
  "automatic_retry_allowed": false,
  "automatic_pagination_allowed": false,
  "arbitrary_provider_allowed": false,
  "arbitrary_model_allowed": false,
  "arbitrary_urls_allowed": false,
  "arbitrary_headers_allowed": false,
  "client_supplied_credentials_allowed": false,
  "paid_provider_calls_allowed": false,
  "trading_or_order_execution_allowed": false,
  "write_operations_allowed": false,
  "secret_values_exposed": false,
  "authentication_required": false,
  "fixed_hosts": [
    "www.ecb.europa.eu",
    "markets.newyorkfed.org",
    "mba.tuck.dartmouth.edu"
  ]
}
```

## 全球开放聚合数据层 (`open-data-aggregators`)

- 状态：`启用`
- 说明：固定接入GLEIF、GDELT、Eurostat SDMX、Mobility Database、OpenAlex、DataCite、OpenCitations、Unpaywall、USAspending、Transitland和China Data Portal。
- 目录策略：仅开放13项固定只读操作；禁止任意URL、主机、路径、Header、客户端Key、自动翻页、重试、写入、交易、个人画像和实时人员/车辆追踪。
- 执行策略：每票最多一次上游调用；固定端点、超时和响应上限；Key仅后端注入；China Data Portal强制标记二级聚合源。
- 票据前缀：`[intel-open-data]`
- Secret环境变量名：`无`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`451b944b19cbecff679199bd6a0a7768860edd12e285d9c86a67718ae0b713a5`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地能力目录。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `source-access-matrix` | 读取来源费用、Key和许可证矩阵。 | `无` |

`source-access-matrix` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `gleif-search` | 搜索全球法律实体。 | `query, limit` |

`gleif-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50
    }
  },
  "required": [
    "query"
  ]
}
```

| `gdelt-search` | 搜索全球新闻事件。 | `query, limit, timespan` |

`gdelt-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 250
    },
    "timespan": {
      "type": "string",
      "pattern": "^[0-9]{1,4}(min|h|d|w|m)$"
    }
  },
  "required": [
    "query"
  ]
}
```

| `sdmx-eurostat-data` | 读取固定Eurostat SDMX数据集。 | `dataflow, key, start_period, end_period` |

`sdmx-eurostat-data` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "dataflow": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_.-]{1,80}$"
    },
    "key": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_.+-]{1,300}$"
    },
    "start_period": {
      "type": "string",
      "maxLength": 20
    },
    "end_period": {
      "type": "string",
      "maxLength": 20
    }
  },
  "required": [
    "dataflow",
    "key"
  ]
}
```

| `mobility-search` | 搜索全球GTFS/GTFS-RT/GBFS Feed。 | `query, limit` |

`mobility-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50
    }
  },
  "required": [
    "query"
  ]
}
```

| `openalex-search` | 搜索开放学术知识图谱。 | `query, limit` |

`openalex-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 300
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50
    }
  },
  "required": [
    "query"
  ]
}
```

| `datacite-search` | 搜索DOI和研究数据元数据。 | `query, limit` |

`datacite-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 300
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    }
  },
  "required": [
    "query"
  ]
}
```

| `opencitations-citations` | 读取DOI引用关系。 | `doi` |

`opencitations-citations` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "doi": {
      "type": "string",
      "pattern": "^10\\.[0-9]{4,9}/\\S{1,240}$"
    }
  },
  "required": [
    "doi"
  ]
}
```

| `unpaywall-get` | 读取合法开放获取位置。 | `doi` |

`unpaywall-get` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "doi": {
      "type": "string",
      "pattern": "^10\\.[0-9]{4,9}/\\S{1,240}$"
    }
  },
  "required": [
    "doi"
  ]
}
```

| `usaspending-search` | 搜索美国联邦合同、补助和支出。 | `keyword, start_date, end_date, limit` |

`usaspending-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "keyword": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100
    },
    "start_date": {
      "type": "string",
      "format": "date"
    },
    "end_date": {
      "type": "string",
      "format": "date"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    }
  },
  "required": [
    "keyword",
    "start_date",
    "end_date"
  ]
}
```

| `transitland-search` | 搜索Transitland交通Feed。 | `query, spec, limit` |

`transitland-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "spec": {
      "type": "string",
      "enum": [
        "gtfs",
        "gtfs-rt",
        "gbfs",
        "mds"
      ]
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50
    }
  },
  "required": [
    "query"
  ]
}
```

| `china-data-get` | 读取China Data Portal固定slug数据集。 | `dataset, format` |

`china-data-get` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "dataset": {
      "type": "string",
      "pattern": "^[a-z0-9][a-z0-9-]{1,100}$"
    },
    "format": {
      "type": "string",
      "enum": [
        "json",
        "csv"
      ]
    }
  },
  "required": [
    "dataset"
  ]
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "timeout_seconds_max": 90,
  "max_response_bytes": 5000000,
  "automatic_pagination_allowed": false,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "client_supplied_credentials_allowed": false,
  "redirects_allowed": false,
  "write_operations_allowed": false,
  "trading_allowed": false,
  "personal_profiling_allowed": false,
  "real_time_tracking_allowed": false,
  "secret_values_exposed": false
}
```

## NIH/NCBI/FDA 公共卫生与生物医学数据 (`nih-public-health`)

- 状态：`启用`
- 说明：统一接入 PubMed（NCBI E-utilities）、openFDA、MedlinePlus 与 NIH Clinical Tables 的公开只读检索能力。
- 目录策略：开放6项固定只读操作。NCBI与openFDA默认免Key，Key仅用于官方额度提升；MedlinePlus与Clinical Tables免Key。禁止任意URL、端点、数据库、请求头和写操作。
- 执行策略：每张票据最多一次固定HTTPS请求；不跟随重定向，不自动翻页，不自动重试。PubMed Fetch最多50个PMID，所有结果受超时和响应体积限制。
- 票据前缀：`[intel-nih-health]`
- Secret环境变量名：`无`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`77e5e508c1ac47de47a58b3a9efee04a4e84c3cbbc5bb8a1d939175c0a2d0f97`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地公共卫生与生物医学能力目录，不访问上游. | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `pubmed-search` | 通过 NCBI E-utilities 的 PubMed ESearch 搜索 PMID。 | `query, retmax, retstart, sort, datetype, mindate, maxdate` |

`pubmed-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    },
    "retmax": {
      "type": "integer",
      "minimum": 1,
      "maximum": 200,
      "default": 20
    },
    "retstart": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100000,
      "default": 0
    },
    "sort": {
      "type": "string",
      "enum": [
        "relevance",
        "pub_date",
        "first_author",
        "journal"
      ],
      "default": "relevance"
    },
    "datetype": {
      "type": "string",
      "enum": [
        "pdat",
        "edat",
        "mdat"
      ]
    },
    "mindate": {
      "type": "string",
      "pattern": "^[0-9]{4}(/[0-9]{2}(/[0-9]{2})?)?$"
    },
    "maxdate": {
      "type": "string",
      "pattern": "^[0-9]{4}(/[0-9]{2}(/[0-9]{2})?)?$"
    }
  },
  "required": [
    "query"
  ]
}
```

| `pubmed-fetch` | 通过 NCBI E-utilities 的 PubMed EFetch 按 PMID 获取 MEDLINE/PubMed XML。 | `pmids, rettype` |

`pubmed-fetch` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "pmids": {
      "type": "array",
      "minItems": 1,
      "maxItems": 50,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "pattern": "^[0-9]{1,12}$"
      }
    },
    "rettype": {
      "type": "string",
      "enum": [
        "abstract",
        "medline"
      ],
      "default": "abstract"
    }
  },
  "required": [
    "pmids"
  ]
}
```

| `openfda-query` | 查询 openFDA 固定数据集；不接受任意端点或任意查询参数。 | `dataset, search, limit, skip, count` |

`openfda-query` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "dataset": {
      "type": "string",
      "enum": [
        "drug-event",
        "drug-label",
        "drug-enforcement",
        "device-event",
        "device-recall",
        "food-enforcement"
      ]
    },
    "search": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 20
    },
    "skip": {
      "type": "integer",
      "minimum": 0,
      "maximum": 25000,
      "default": 0
    },
    "count": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200,
      "pattern": "^[A-Za-z0-9_.]+$"
    }
  },
  "required": [
    "dataset"
  ]
}
```

| `medlineplus-search` | 搜索 MedlinePlus 健康主题、疾病、药物和健康教育内容。 | `query, retmax, retstart, language` |

`medlineplus-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 300
    },
    "retmax": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50,
      "default": 10
    },
    "retstart": {
      "type": "integer",
      "minimum": 0,
      "maximum": 1000,
      "default": 0
    },
    "language": {
      "type": "string",
      "enum": [
        "en",
        "es"
      ],
      "default": "en"
    }
  },
  "required": [
    "query"
  ]
}
```

| `clinical-tables-search` | 搜索 NIH Clinical Tables 固定临床术语表。 | `dataset, terms, max_list, offset` |

`clinical-tables-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "dataset": {
      "type": "string",
      "enum": [
        "conditions",
        "icd10cm",
        "rxterms",
        "loinc"
      ]
    },
    "terms": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "max_list": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 20
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "maximum": 7500,
      "default": 0
    }
  },
  "required": [
    "dataset",
    "terms"
  ]
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "timeout_seconds_max": 120,
  "max_response_bytes": 20000000,
  "provider_concurrency_max": 1,
  "transient_retry_max": 0,
  "fixed_api_hosts": [
    "eutils.ncbi.nlm.nih.gov",
    "api.fda.gov",
    "wsearch.nlm.nih.gov",
    "clinicaltables.nlm.nih.gov"
  ],
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "redirects_allowed": false,
  "write_operations_allowed": false,
  "personal_data_allowed": false,
  "secret_values_exposed": false,
  "authentication_required": false,
  "optional_api_keys": [
    "NCBI_API_KEY",
    "OPENFDA_API_KEY"
  ],
  "automatic_pagination_allowed": false,
  "whole_database_download_allowed": false,
  "pubmed_pmids_per_fetch_max": 50,
  "openfda_records_per_request_max": 100
}
```

## OpenStreetMap / Overpass / Nominatim (`openstreetmap`)

- 状态：`启用`
- 说明：统一接入 OSM 对象读取、Nominatim 单次地理编码与受控模板化 Overpass 空间查询。
- 目录策略：开放6项固定免密只读操作；禁止任意URL、任意主机、原始Overpass QL、批量Nominatim、自动补全、爬取和写入。
- 执行策略：每张票据最多一次固定HTTPS请求，Provider全局并发1。Nominatim使用明确User-Agent并限制每票最多10条；Overpass只由白名单字段生成QL，半径和边界框严格受限。
- 票据前缀：`[intel-osm]`
- Secret环境变量名：`无`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`098b5b9562d9a0cf2901c212d739727b87cf08aa25a32a601bae5a5ae246a12b`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地 OpenStreetMap 能力与使用政策，不访问上游. | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `osm-object` | 按固定对象类型和ID读取一个 OSM node、way 或 relation。 | `object_type, object_id` |

`osm-object` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "object_type": {
      "type": "string",
      "enum": [
        "node",
        "way",
        "relation"
      ]
    },
    "object_id": {
      "type": "integer",
      "minimum": 1,
      "maximum": 999999999999
    }
  },
  "required": [
    "object_type",
    "object_id"
  ]
}
```

| `nominatim-search` | 使用 Nominatim 对单个自然语言地点进行地理编码；禁止自动补全和批量地理编码。 | `query, limit, countrycodes, language, addressdetails, extratags, namedetails` |

`nominatim-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string",
      "minLength": 2,
      "maxLength": 300
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10,
      "default": 5
    },
    "countrycodes": {
      "type": "string",
      "pattern": "^[a-z]{2}(,[a-z]{2}){0,9}$"
    },
    "language": {
      "type": "string",
      "minLength": 2,
      "maxLength": 40,
      "pattern": "^[A-Za-z-]+(,[A-Za-z-]+)*$"
    },
    "addressdetails": {
      "type": "boolean",
      "default": true
    },
    "extratags": {
      "type": "boolean",
      "default": false
    },
    "namedetails": {
      "type": "boolean",
      "default": false
    }
  },
  "required": [
    "query"
  ]
}
```

| `nominatim-reverse` | 使用 Nominatim 对单个坐标进行反向地理编码。 | `lat, lon, zoom, language, addressdetails, extratags, namedetails` |

`nominatim-reverse` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
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
      "minimum": 3,
      "maximum": 18,
      "default": 18
    },
    "language": {
      "type": "string",
      "minLength": 2,
      "maxLength": 40,
      "pattern": "^[A-Za-z-]+(,[A-Za-z-]+)*$"
    },
    "addressdetails": {
      "type": "boolean",
      "default": true
    },
    "extratags": {
      "type": "boolean",
      "default": false
    },
    "namedetails": {
      "type": "boolean",
      "default": false
    }
  },
  "required": [
    "lat",
    "lon"
  ]
}
```

| `overpass-nearby` | 使用模板化 Overpass QL 查询坐标附近的 OSM 要素；不接受原始QL。 | `lat, lon, radius_m, tag_key, tag_value, element_type, limit` |

`overpass-nearby` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
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
    "radius_m": {
      "type": "integer",
      "minimum": 1,
      "maximum": 5000,
      "default": 500
    },
    "tag_key": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_:.-]{1,64}$"
    },
    "tag_value": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100,
      "pattern": "^[A-Za-z0-9_ :./()&+,'-]+$"
    },
    "element_type": {
      "type": "string",
      "enum": [
        "node",
        "way",
        "relation",
        "all"
      ],
      "default": "all"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 200,
      "default": 100
    }
  },
  "required": [
    "lat",
    "lon",
    "tag_key"
  ]
}
```

| `overpass-bbox` | 使用模板化 Overpass QL 查询小范围边界框内的 OSM 要素；不接受原始QL。 | `south, west, north, east, tag_key, tag_value, element_type, limit` |

`overpass-bbox` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "south": {
      "type": "number",
      "minimum": -90,
      "maximum": 90
    },
    "west": {
      "type": "number",
      "minimum": -180,
      "maximum": 180
    },
    "north": {
      "type": "number",
      "minimum": -90,
      "maximum": 90
    },
    "east": {
      "type": "number",
      "minimum": -180,
      "maximum": 180
    },
    "tag_key": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_:.-]{1,64}$"
    },
    "tag_value": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100,
      "pattern": "^[A-Za-z0-9_ :./()&+,'-]+$"
    },
    "element_type": {
      "type": "string",
      "enum": [
        "node",
        "way",
        "relation",
        "all"
      ],
      "default": "all"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 200,
      "default": 100
    }
  },
  "required": [
    "south",
    "west",
    "north",
    "east",
    "tag_key"
  ]
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "timeout_seconds_max": 120,
  "max_response_bytes": 20000000,
  "provider_concurrency_max": 1,
  "transient_retry_max": 0,
  "fixed_api_hosts": [
    "api.openstreetmap.org",
    "nominatim.openstreetmap.org",
    "overpass-api.de"
  ],
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "raw_overpass_ql_allowed": false,
  "nominatim_autocomplete_allowed": false,
  "nominatim_bulk_geocoding_allowed": false,
  "redirects_allowed": false,
  "write_operations_allowed": false,
  "personal_data_allowed": false,
  "secret_values_exposed": false,
  "authentication_required": false,
  "automatic_pagination_allowed": false,
  "whole_database_download_allowed": false,
  "nominatim_results_per_ticket_max": 10,
  "overpass_result_elements_max": 200,
  "overpass_radius_m_max": 5000,
  "overpass_bbox_span_degrees_max": 2.0
}
```

## GNews 全球新闻情报 (`gnews`)

- 状态：`启用`
- 说明：通过 GNews 官方 REST API读取全球新闻搜索结果和基于 Google News 排名的头条；固定只读、单请求、受限分页，不抓取文章正文。
- 目录策略：固定开放3项能力：本地目录、关键词新闻检索、分类头条。API Key仅后端注入X-Api-Key；免费套餐按100次/日、每次最多10篇、12小时延迟、30天历史和仅开发测试用途建模。
- 执行策略：每张票据最多一次固定HTTPS GET；不接受客户端凭据、任意URL、任意路径、任意请求头、自动翻页、自动重试、后台轮询、写操作或文章正文二次抓取。
- 票据前缀：`[intel-gnews]`
- Secret环境变量名：`GNEWS_API_KEY`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`f0a2f1ec6641043689fb10cfefdfe8d042e1a49983ec5714cdbea4a2a4702d07`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地 GNews 安全能力目录，不访问上游。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "maxProperties": 0
}
```

| `search-news` | 按关键词检索全球新闻，支持语言、国家、字段、日期、排序和单页过滤。 | `q, lang, country, max, in, nullable, from, to, sortby, page, truncate` |

`search-news` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "q": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "lang": {
      "type": "string",
      "pattern": "^[a-z]{2}$"
    },
    "country": {
      "type": "string",
      "pattern": "^[a-z]{2}$"
    },
    "max": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10,
      "default": 10
    },
    "in": {
      "type": "array",
      "minItems": 1,
      "maxItems": 3,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "enum": [
          "title",
          "description",
          "content"
        ]
      }
    },
    "nullable": {
      "type": "array",
      "minItems": 1,
      "maxItems": 3,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "enum": [
          "description",
          "content",
          "image"
        ]
      }
    },
    "from": {
      "type": "string",
      "format": "date-time"
    },
    "to": {
      "type": "string",
      "format": "date-time"
    },
    "sortby": {
      "type": "string",
      "enum": [
        "publishedAt",
        "relevance"
      ],
      "default": "publishedAt"
    },
    "page": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 1
    },
    "truncate": {
      "const": "content"
    }
  },
  "required": [
    "q"
  ],
  "maxProperties": 11
}
```

| `top-headlines` | 读取基于 Google News 排名的头条，可按分类、关键词、语言、国家和日期过滤。 | `category, q, lang, country, max, nullable, from, to, page, truncate` |

`top-headlines` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "category": {
      "type": "string",
      "enum": [
        "general",
        "world",
        "nation",
        "business",
        "technology",
        "entertainment",
        "sports",
        "science",
        "health"
      ],
      "default": "general"
    },
    "q": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "lang": {
      "type": "string",
      "pattern": "^[a-z]{2}$"
    },
    "country": {
      "type": "string",
      "pattern": "^[a-z]{2}$"
    },
    "max": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10,
      "default": 10
    },
    "nullable": {
      "type": "array",
      "minItems": 1,
      "maxItems": 3,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "enum": [
          "description",
          "content",
          "image"
        ]
      }
    },
    "from": {
      "type": "string",
      "format": "date-time"
    },
    "to": {
      "type": "string",
      "format": "date-time"
    },
    "page": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 1
    },
    "truncate": {
      "const": "content"
    }
  },
  "maxProperties": 10
}
```

限制：

```json
{
  "requests_per_ticket_max": 1,
  "provider_concurrency_max": 1,
  "transient_retry_max": 0,
  "timeout_seconds_max": 90,
  "max_response_bytes": 10000000,
  "max_articles_per_request": 10,
  "max_page": 100,
  "max_date_range_days": 30,
  "free_plan_requests_per_day": 100,
  "free_plan_delay_hours": 12,
  "free_plan_historical_days": 30,
  "free_plan_noncommercial_development_testing_only": true,
  "commercial_use_requires_paid_plan": true,
  "full_content_plan_dependent": true,
  "fixed_api_host": "gnews.io",
  "fixed_paths": [
    "/api/v4/search",
    "/api/v4/top-headlines"
  ],
  "arbitrary_urls_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "client_supplied_credentials_allowed": false,
  "redirects_allowed": false,
  "automatic_pagination_allowed": false,
  "background_monitoring_allowed": false,
  "article_body_fetching_allowed": false,
  "write_operations_allowed": false,
  "secret_values_exposed": false
}
```

## 全球开放文献与资料库 (`global-literature-libraries`)

- 状态：`启用`
- 说明：固定接入全球学术聚合、经济政策灰色文献、研究仓储、医学工程资料、预印本、国家图书馆、文化遗产与欧洲专利公开文献。
- 目录策略：仅开放10项固定只读操作和25个固定HTTPS来源；禁止任意URL、主机、路径、Header、客户端Key、动态Provider、付费墙绕过和未授权全文复制。
- 执行策略：每票最多一次上游请求；只取首批结果；不自动追随分页或resumptionToken；Key仅后端注入；保留来源权利字段与响应哈希。
- 票据前缀：`[intel-literature]`
- Secret环境变量名：`无`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`0aa88d2bb597e7fee8012bb93bd3ad0f0dafe597927525b89f6c692ca0b3fc21`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地全球文献能力目录。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "maxProperties": 0
}
```

| `source-access-matrix` | 读取来源、费用、Key、权利和禁用原因矩阵。 | `无` |

`source-access-matrix` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "maxProperties": 0
}
```

| `literature-search` | 在一个固定 REST/OpenSearch/SRU 来源执行单页文献或资料检索。 | `source_id, query, limit` |

`literature-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "type": "string",
      "enum": [
        "core",
        "openaire",
        "semantic-scholar",
        "europe-pmc",
        "zenodo",
        "osf",
        "figshare",
        "dryad",
        "econbiz",
        "osti",
        "nasa-ads",
        "library-of-congress",
        "open-library",
        "europeana",
        "dpla",
        "cinii",
        "gallica"
      ]
    },
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50,
      "default": 20
    }
  },
  "required": [
    "source_id",
    "query"
  ]
}
```

| `literature-record` | 从一个固定来源读取单条公开元数据记录。 | `source_id, record_id` |

`literature-record` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "type": "string",
      "enum": [
        "core",
        "openaire",
        "semantic-scholar",
        "europe-pmc",
        "zenodo",
        "osf",
        "figshare",
        "econbiz",
        "osti",
        "nasa-ads",
        "library-of-congress",
        "open-library",
        "europeana",
        "dpla"
      ]
    },
    "record_id": {
      "type": "string",
      "minLength": 1,
      "maxLength": 300,
      "pattern": "^[A-Za-z0-9._:/-]+$"
    }
  },
  "required": [
    "source_id",
    "record_id"
  ]
}
```

| `preprint-feed` | 读取 bioRxiv 或 medRxiv 固定日期范围的一页预印本元数据。 | `source_id, from_date, until_date, cursor` |

`preprint-feed` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "type": "string",
      "enum": [
        "biorxiv",
        "medrxiv"
      ]
    },
    "from_date": {
      "type": "string",
      "format": "date"
    },
    "until_date": {
      "type": "string",
      "format": "date"
    },
    "cursor": {
      "type": "integer",
      "minimum": 0,
      "maximum": 9999,
      "default": 0
    }
  },
  "required": [
    "source_id",
    "from_date",
    "until_date"
  ]
}
```

| `oai-identify` | 对固定 OAI-PMH 仓储执行 Identify。 | `source_id` |

`oai-identify` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "type": "string",
      "enum": [
        "doaj-oai",
        "econstor-oai",
        "erara-oai",
        "texas-history-oai"
      ]
    }
  },
  "required": [
    "source_id"
  ]
}
```

| `oai-list-records` | 从固定 OAI-PMH 仓储读取首批记录；不接受或追随 resumptionToken。 | `source_id, metadata_prefix, from_date, until_date, set` |

`oai-list-records` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "type": "string",
      "enum": [
        "doaj-oai",
        "econstor-oai",
        "erara-oai",
        "texas-history-oai"
      ]
    },
    "metadata_prefix": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_.-]{1,64}$",
      "default": "oai_dc"
    },
    "from_date": {
      "type": "string",
      "format": "date"
    },
    "until_date": {
      "type": "string",
      "format": "date"
    },
    "set": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_.:/-]{1,200}$"
    }
  },
  "required": [
    "source_id",
    "metadata_prefix"
  ]
}
```

| `oai-get-record` | 从固定 OAI-PMH 仓储读取单条记录。 | `source_id, identifier, metadata_prefix` |

`oai-get-record` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "type": "string",
      "enum": [
        "doaj-oai",
        "econstor-oai",
        "erara-oai",
        "texas-history-oai"
      ]
    },
    "identifier": {
      "type": "string",
      "minLength": 1,
      "maxLength": 300
    },
    "metadata_prefix": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_.-]{1,64}$",
      "default": "oai_dc"
    }
  },
  "required": [
    "source_id",
    "identifier",
    "metadata_prefix"
  ]
}
```

| `sru-search` | 在日本国立国会图书馆固定 SRU 端点执行首批检索。 | `source_id, query, limit, record_schema` |

`sru-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "type": "string",
      "enum": [
        "ndl-sru"
      ]
    },
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50,
      "default": 20
    },
    "record_schema": {
      "type": "string",
      "enum": [
        "dc",
        "dcndl"
      ],
      "default": "dc"
    }
  },
  "required": [
    "source_id",
    "query"
  ]
}
```

| `patent-publication-get` | 从 EPO 权威发布服务器读取固定欧洲专利文献的格式列表或公开文档。 | `source_id, publication_number, format` |

`patent-publication-get` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "type": "string",
      "enum": [
        "epo-publication-server"
      ]
    },
    "publication_number": {
      "type": "string",
      "pattern": "^EP[0-9]{6,10}N[A-Z]{1,3}[0-9]$"
    },
    "format": {
      "type": "string",
      "enum": [
        "formats",
        "xml",
        "html",
        "pdf"
      ],
      "default": "formats"
    }
  },
  "required": [
    "source_id",
    "publication_number",
    "format"
  ]
}
```

限制：

```json
{
  "source_count": 25,
  "requests_per_ticket_max": 1,
  "timeout_seconds_max": 90,
  "max_response_bytes": 15000000,
  "automatic_pagination_allowed": false,
  "automatic_retry_allowed": false,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "client_supplied_credentials_allowed": false,
  "dynamic_providers_allowed": false,
  "redirects_allowed": false,
  "write_operations_allowed": false,
  "paywall_bypass_allowed": false,
  "unauthorized_full_text_copying_allowed": false,
  "personal_profiling_allowed": false,
  "real_time_tracking_allowed": false,
  "secret_values_exposed": false
}
```

## 全球文献档案资料库第二波 (`global-knowledge-archives`)

- 状态：`启用`
- 说明：固定接入学位论文、教育研究、开放专著、国家目录、档案馆、博物馆、政府出版物、科研资助、临床试验、地学报告、监管文件和经济工作论文元数据。
- 目录策略：仅开放9项固定只读操作和20个固定HTTPS来源；禁止任意URL、主机、路径、Header、客户端Key、动态Provider、付费墙绕过和未授权全文复制。
- 执行策略：每票最多一次上游请求；只取首批结果；不自动翻页、不追随OAI resumptionToken、不自动重试、不跟随重定向；Key仅后端注入；保留权利字段与响应哈希。
- 票据前缀：`[intel-knowledge]`
- Secret环境变量名：`无`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`e65f7c045c71588225b75e83c060e6ad45829f1e9e6496e7d13b2c82ba987a58`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取本地第二波全球资料库能力目录。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "maxProperties": 0
}
```

| `source-access-matrix` | 读取来源、Key、费用、权利和暂缓原因矩阵。 | `无` |

`source-access-matrix` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "maxProperties": 0
}
```

| `knowledge-search` | 在一个固定REST来源执行一页文献、档案、研究项目或馆藏检索。 | `source_id, query, limit` |

`knowledge-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "type": "string",
      "enum": [
        "eric",
        "ukri-gtr",
        "nih-reporter",
        "clinicaltrials-gov",
        "usgs-publications",
        "federal-register",
        "met-museum",
        "art-institute-chicago",
        "digitalnz",
        "trove",
        "google-books",
        "bhl",
        "nara",
        "smithsonian"
      ]
    },
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50,
      "default": 20
    }
  },
  "required": [
    "source_id",
    "query"
  ]
}
```

| `knowledge-record` | 从一个固定来源读取单条公开元数据记录或GovInfo包摘要。 | `source_id, record_id` |

`knowledge-record` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "type": "string",
      "enum": [
        "ukri-gtr",
        "clinicaltrials-gov",
        "federal-register",
        "met-museum",
        "art-institute-chicago",
        "digitalnz",
        "google-books",
        "bhl",
        "govinfo"
      ]
    },
    "record_id": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200,
      "pattern": "^[A-Za-z0-9._:/-]+$"
    }
  },
  "required": [
    "source_id",
    "record_id"
  ]
}
```

| `oai-identify` | 对固定开放仓储或博物馆OAI-PMH端点执行Identify。 | `source_id` |

`oai-identify` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "type": "string",
      "enum": [
        "hal-oai",
        "doab-oai",
        "rijksmuseum-oai"
      ]
    }
  },
  "required": [
    "source_id"
  ]
}
```

| `oai-list-records` | 从固定OAI-PMH来源读取首批记录；不接受或追随resumptionToken。 | `source_id, metadata_prefix, from_date, until_date, set` |

`oai-list-records` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "type": "string",
      "enum": [
        "hal-oai",
        "doab-oai",
        "rijksmuseum-oai"
      ]
    },
    "metadata_prefix": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_.-]{1,64}$",
      "default": "oai_dc"
    },
    "from_date": {
      "type": "string",
      "format": "date"
    },
    "until_date": {
      "type": "string",
      "format": "date"
    },
    "set": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_.:/-]{1,200}$"
    }
  },
  "required": [
    "source_id",
    "metadata_prefix"
  ]
}
```

| `oai-get-record` | 从固定OAI-PMH来源读取单条元数据记录。 | `source_id, identifier, metadata_prefix` |

`oai-get-record` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "type": "string",
      "enum": [
        "hal-oai",
        "doab-oai",
        "rijksmuseum-oai"
      ]
    },
    "identifier": {
      "type": "string",
      "minLength": 1,
      "maxLength": 300
    },
    "metadata_prefix": {
      "type": "string",
      "pattern": "^[A-Za-z0-9_.-]{1,64}$",
      "default": "oai_dc"
    }
  },
  "required": [
    "source_id",
    "identifier",
    "metadata_prefix"
  ]
}
```

| `sru-search` | 在德国国家图书馆固定SRU端点执行首批书目检索。 | `source_id, query, limit, record_schema` |

`sru-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "type": "string",
      "enum": [
        "dnb-sru"
      ]
    },
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50,
      "default": 20
    },
    "record_schema": {
      "type": "string",
      "enum": [
        "MARC21-xml",
        "RDFxml",
        "oai_dc"
      ],
      "default": "MARC21-xml"
    }
  },
  "required": [
    "source_id",
    "query"
  ]
}
```

| `metadata-file-get` | 读取一个固定NBER工作论文元数据TSV文件；不读取受限全文。 | `source_id, dataset` |

`metadata-file-get` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "type": "string",
      "enum": [
        "nber-metadata"
      ]
    },
    "dataset": {
      "type": "string",
      "enum": [
        "reference",
        "titles",
        "abstracts",
        "authors",
        "dates",
        "jel",
        "programs",
        "projects",
        "published"
      ]
    }
  },
  "required": [
    "source_id",
    "dataset"
  ]
}
```

限制：

```json
{
  "source_count": 20,
  "requests_per_ticket_max": 1,
  "timeout_seconds_max": 90,
  "max_response_bytes": 15000000,
  "automatic_pagination_allowed": false,
  "automatic_retry_allowed": false,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "client_supplied_credentials_allowed": false,
  "dynamic_providers_allowed": false,
  "redirects_allowed": false,
  "write_operations_allowed": false,
  "paywall_bypass_allowed": false,
  "unauthorized_full_text_copying_allowed": false,
  "personal_profiling_allowed": false,
  "patient_level_data_allowed": false,
  "real_time_tracking_allowed": false,
  "secret_values_exposed": false
}
```

## 全球知识织网第三波 (`global-knowledge-fabric`)

- 状态：`启用`
- 说明：固定接入科研机构与作者标识、计算机科学书目、研究对象关系、科研数据集、政府资助与法规、欧盟出版物、生命科学知识和技术标准。
- 目录策略：仅开放9项固定只读操作和15个固定HTTPS来源；禁止任意URL、主机、路径、Header、客户端凭证、任意SPARQL、动态Provider、写入和付费墙绕过。
- 执行策略：每票最多一次上游请求；只取首批结果；不自动翻页、不使用cursor、不自动重试、不跟随重定向；凭证仅后端注入；保留来源权利和响应哈希。
- 票据前缀：`[intel-knowledge-fabric]`
- Secret环境变量名：`无`（仅名称）
- Repository Variable名：`无`（仅名称）
- 提供方SHA-256：`f237e8794b12cf3aa8ccc907e0a190e6528565273dddb308fac8ecf38228282c`

| 操作 | 说明 | 参数 |
|---|---|---|
| `catalog-capabilities` | 读取第三波全球知识织网能力目录。 | `无` |

`catalog-capabilities` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `source-access-matrix` | 读取来源、凭证、费用、权利和暂缓原因矩阵。 | `无` |

`source-access-matrix` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

| `entity-search` | 检索科研机构、研究者或作者实体。 | `source_id, query, limit` |

`entity-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "type": "string",
      "enum": [
        "ror",
        "orcid",
        "dblp-author"
      ]
    },
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50,
      "default": 20
    }
  },
  "required": [
    "source_id",
    "query"
  ]
}
```

| `scholarly-search` | 检索计算机科学文献或学术场馆。 | `source_id, query, limit` |

`scholarly-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "type": "string",
      "enum": [
        "dblp-publication",
        "dblp-venue"
      ]
    },
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50,
      "default": 20
    }
  },
  "required": [
    "source_id",
    "query"
  ]
}
```

| `dataset-search` | 检索公开科研数据集或机器学习数据集。 | `source_id, query, limit` |

`dataset-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "type": "string",
      "enum": [
        "harvard-dataverse",
        "openml"
      ]
    },
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50,
      "default": 20
    }
  },
  "required": [
    "source_id",
    "query"
  ]
}
```

| `government-search` | 检索政府资助、法规、数据目录或欧盟出版物。 | `source_id, query, limit` |

`government-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "type": "string",
      "enum": [
        "grants-gov",
        "regulations-gov",
        "data-gov",
        "eu-cellar"
      ]
    },
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50,
      "default": 20
    }
  },
  "required": [
    "source_id",
    "query"
  ]
}
```

| `science-search` | 检索结构生物学、蛋白质或药物发现知识。 | `source_id, query, limit` |

`science-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "type": "string",
      "enum": [
        "rcsb-pdb",
        "uniprot",
        "chembl"
      ]
    },
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50,
      "default": 20
    }
  },
  "required": [
    "source_id",
    "query"
  ]
}
```

| `record-get` | 读取一个固定来源的单条公开记录。 | `source_id, record_id` |

`record-get` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "type": "string",
      "enum": [
        "ror",
        "orcid",
        "harvard-dataverse",
        "openml",
        "grants-gov",
        "regulations-gov",
        "data-gov",
        "rcsb-pdb",
        "uniprot",
        "chembl"
      ]
    },
    "record_id": {
      "type": "string",
      "minLength": 1,
      "maxLength": 240
    }
  },
  "required": [
    "source_id",
    "record_id"
  ]
}
```

| `standards-search` | 检索IETF标准、RFC和Internet-Draft过程元数据。 | `source_id, query, limit` |

`standards-search` 参数Schema：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source_id": {
      "type": "string",
      "enum": [
        "ietf-datatracker"
      ]
    },
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50,
      "default": 20
    }
  },
  "required": [
    "source_id",
    "query"
  ]
}
```

限制：

```json
{
  "source_count": 15,
  "requests_per_ticket_max": 1,
  "timeout_seconds_max": 75,
  "max_response_bytes": 5000000,
  "automatic_pagination_allowed": false,
  "automatic_retry_allowed": false,
  "arbitrary_urls_allowed": false,
  "arbitrary_hosts_allowed": false,
  "arbitrary_paths_allowed": false,
  "arbitrary_headers_allowed": false,
  "client_supplied_credentials_allowed": false,
  "dynamic_providers_allowed": false,
  "arbitrary_sparql_allowed": false,
  "redirects_allowed": false,
  "write_operations_allowed": false,
  "paywall_bypass_allowed": false,
  "unauthorized_full_text_copying_allowed": false,
  "personal_profiling_allowed": false,
  "patient_level_data_allowed": false,
  "real_time_tracking_allowed": false,
  "secret_values_exposed": false
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
