# 和风天气 QWeather

- Provider：`qweather`
- 票据前缀：`[api-qweather]`
- Repository Secret：`QWEATHER_API_KEY`
- 固定 API Host：`ka6r72kcc3.re.qweatherapi.com`
- 鉴权：后端请求头 `X-QW-Api-Key`
- 当前开放：18 项固定只读操作

覆盖 GeoAPI、城市天气、格点天气、分钟级降水、空气质量、天气生活指数、最近 10 天历史天气和太阳辐射预报。

禁止任意 URL、任意 Host、任意路径、任意请求头、客户端提交密钥、重定向、写入和个人数据。每张正式票据生成 Snapshot、Diagnostics、Manifest、摘要和 GitHub Actions Artifact。
