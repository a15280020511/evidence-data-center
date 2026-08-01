# Overture Maps 全球开放地图数据

正式票据前缀：

```text
[api-overture]
```

无需 Repository Secret。Provider 仅通过 Overture 官方 `overturemaps==1.0.1` 客户端访问官方 STAC 目录和匿名只读对象存储。

固定开放 7 项操作：

- `catalog-capabilities`
- `list-feature-types`
- `list-releases`
- `latest-release`
- `count-features`
- `query-features`
- `lookup-gers`

`count-features` 和 `query-features` 必须提供合法经纬度边界框，面积不得超过 4 平方度；单票据最多提取 1,000 条 GeoJSON 要素。禁止全量全球下载、任意 S3 路径、任意 URL、写入和个人数据。
