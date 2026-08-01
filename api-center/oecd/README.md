# OECD Data Explorer SDMX

正式票据前缀：

```text
[api-oecd]
```

无需 Repository Secret。Provider 固定访问：

```text
https://sdmx.oecd.org/public/rest/v1
```

固定开放 6 项操作：本地能力目录、数据流目录、数据流定义、数据结构、代码表和统计数据查询。每张票据最多一次 HTTPS GET；Agency、Flow、Version、维度 Key、时间范围、格式和响应体积均受 Schema 限制。禁止任意 URL、批量下载逃逸、请求头覆盖和写操作。
