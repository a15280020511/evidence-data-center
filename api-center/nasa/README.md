# NASA Open APIs 与 Earthdata GIBS Provider

票据前缀：

```text
[intel-nasa]
```

Repository Secret：

```text
NASA_API_KEY
```

本 Provider 只开放 NASA 官方固定只读端点：

- `api.nasa.gov`：APOD、近地小行星 NeoWs、DONKI 空间天气、EPIC 地球影像元数据；
- `images-api.nasa.gov`：NASA 图像与视频资料库检索、资产、元数据和字幕；
- `gibs.earthdata.nasa.gov`：Earthdata GIBS WMTS/WMS 能力、图层元数据和单瓦片影像。

重要迁移边界：

- 不接入已归档的旧 Earth API；地球影像改用 Earthdata GIBS。
- 不接入已归档的 Mars Rover Photos API。
- 不开放任意 URL、任意主机、任意路径、上传、写入或后台轮询。

安全边界：

- 每张票据只发送一次上游 GET，请求失败不自动重试。
- APOD 日期范围最多 31 天；NeoWs feed 最多 7 天；DONKI 范围最多 31 天。
- NASA 图像搜索只允许单页，页码最大 100。
- GIBS 每张票据最多获取一张瓦片，禁止整图层、整区域和批量下载。
- `NASA_API_KEY` 仅在 GitHub Actions 执行步骤中注入，不进入 Issue、日志、目录或 Artifact。
- GIBS 与 NASA Image Library 为免密端点；`api.nasa.gov` 操作必须使用 `NASA_API_KEY`。

NASA 官方默认开发者密钥额度通常为每小时 1,000 次；实际额度以响应头和账户状态为准。本实现不使用 `DEMO_KEY` 作为生产回退。
