# Xweather 全球专业天气数据

正式票据前缀：

```text
[api-xweather]
```

Xweather Weather API 每次调用需要两项配置：

```text
Repository Variable: XWEATHER_CLIENT_ID
Repository Secret:   XWEATHER_CLIENT_SECRET
```

Client ID 不是写入仓库的常量；Client Secret 只由 GitHub Actions 后端注入。Provider 固定访问：

```text
https://data.api.xweather.com
```

固定开放 10 项核心只读能力：地点解析、实时观测、插值条件、15 日预报、官方预警、空气质量、日月数据、月相和历史观测日汇总。部分端点可能受套餐、区域或调用倍率约束；权限不足会输出结构化失败，不会伪造数据。

禁止任意 URL、任意主机、任意查询参数、路线批量、客户端凭据、Webhook 和写操作。
