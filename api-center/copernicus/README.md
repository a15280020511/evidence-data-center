# Copernicus Data Space Ecosystem

受控、只读的哥白尼 Sentinel 卫星数据提供方。

- 票据前缀：`[intel-copernicus]`
- 公开 STAC 目录：免密
- Sentinel Hub PNG 渲染：需要 Repository Variable `COPERNICUS_CLIENT_ID` 和 Repository Secret `COPERNICUS_CLIENT_SECRET`
- 固定主机：`stac.dataspace.copernicus.eu`、`sh.dataspace.copernicus.eu`、`identity.dataspace.copernicus.eu`
- 能力：集合目录、区域/时间/云量产品搜索、单产品元数据、Sentinel-2 L2A 真彩色/假彩色/NDVI PNG
- 约束：每票据最多一次目录请求，或一次 OAuth 令牌请求加一次处理请求；不重试、不翻页、不批量下载、不接受任意 evalscript、不持久化令牌、不写入上游
- 许可与署名：按 Copernicus Sentinel 数据使用条款注明 `European Union, Copernicus Sentinel data`
