# Mediastack 全球新闻情报

正式票据前缀：

```text
[intel-mediastack]
```

独立 Repository Secret：

```text
MEDIASTACK_API_KEY
```

固定官方主机：

```text
https://api.mediastack.com
```

## 固定开放能力

```text
catalog-capabilities
latest-news
search-news
historical-news
list-sources
```

安全边界：

- 每张票据最多一次固定 GET；
- 仅允许 `/v1/news` 和 `/v1/sources`；
- `limit` 最大 100，`offset` 最大 10000；
- 历史日期区间最长 366 天；
- 不自动翻页，不后台轮询，不创建监控任务；
- 不抓取新闻文章正文，只返回 Mediastack 标准化元数据；
- 不接受客户端 API Key、任意 URL、任意路径、任意请求头或写操作；
- API Key 仅由 GitHub Repository Secret 注入为 `access_key` 查询参数，日志和 Artifact 不保存其值。

## 套餐边界

Mediastack 官方当前标示免费层为每月 100 次请求，免费层使用延迟新闻数据；历史数据和商业使用取决于付费套餐。实际权限、延迟、额度和超额费用以上游账户实时返回为准。

中国新闻可使用国家代码：

```text
cn
```

示例票据：

```json
{
  "task_id": "mediastack-yonghui-001",
  "provider": "mediastack",
  "operation": "search-news",
  "objective": "检索永辉超市公开新闻",
  "parameters": {
    "keywords": "永辉超市",
    "countries": ["cn"],
    "languages": ["zh"],
    "categories": ["business"],
    "sort": "published_desc",
    "limit": 25,
    "offset": 0
  },
  "data_policy": {
    "classification": "public",
    "contains_personal_data": false,
    "contains_confidential_data": false
  },
  "acceptance": {
    "timeout_seconds": 45,
    "max_response_bytes": 5000000,
    "max_rows": 100
  }
}
```
