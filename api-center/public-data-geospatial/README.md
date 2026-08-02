# 全球公共数据、空间地理与中国数据

票据前缀：`[intel-public-data]`。当前开放 **39** 项固定只读能力，覆盖国际统计、人道主义、企业主体、人口、生物多样性、空气质量、地震、道路路网、路线/矩阵/等时圈、地理编码、高程、行政区边界、土壤、海洋船舶、充电设施、公共交通，以及中国国家统计局和中国科学数据中心目录。

## 安全边界

- 每张票据最多一次上游请求，不自动翻页、不重试、不批量镜像。
- 仅访问代码内固定官方主机；禁止任意 URL、请求头和写操作。
- 所有 Key/Token/用户名只从 Actions Secrets 注入，Artifact 和评论不暴露凭据。
- `global-fishing-watch-vessels` 仅限其条款允许的非商业用途。
- SoilGrids 使用 WCS 能力接口，不依赖暂停的 REST beta。
- 国家统计局接口属于其公开网站使用的查询接口，但缺少正式外部 API SLA；生产使用保留来源和抓取时间，并允许结构化失败。

## 可选 Secrets

`OPENROUTESERVICE_API_KEY`、`GEONAMES_USERNAME`、`OPENAQ_API_KEY`、`OPENFDA_API_KEY`、`RELIEFWEB_APPNAME`、`HDX_HAPI_APP_IDENTIFIER`、`IATI_API_KEY`、`COMPANIES_HOUSE_API_KEY`、`SAM_GOV_API_KEY`、`OPENTOPOGRAPHY_API_KEY`、`GLOBAL_FISHING_WATCH_API_TOKEN`、`OPENCHARGEMAP_API_KEY`、`TRANSITLAND_API_KEY`。
