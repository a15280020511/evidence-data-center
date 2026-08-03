# OpenStreetMap Provider

统一接入以下公开只读服务：

- OpenStreetMap API 0.6：单个 node、way、relation 对象读取
- Nominatim：单次地理编码与反向地理编码
- Overpass API：附近或小型边界框的模板化空间查询

## 票据入口

Issue 标题前缀：`[intel-osm]`

每张票据只允许一个操作、一次上游请求，Provider 全局并发为 1。

## 使用政策与安全边界

Nominatim 固定使用可识别的 User-Agent，最多返回 10 条，禁止自动补全、批量地理编码和系统性爬取。Overpass 不接受原始 QL，只允许从受 Schema 约束的坐标、半径、边界框和标签字段生成查询；半径上限 5 公里，边界框经纬跨度上限 2 度，结果上限 200 个元素。
