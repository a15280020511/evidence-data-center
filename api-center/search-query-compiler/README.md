# 搜索查询编译器

Tavily、Exa、SerpAPI/Google和百度的查询语法与排序机制不同，不能把同一个长查询原样发送给所有Provider。本模块把统一搜索目标编译为各Provider适合的受限查询包。

## 输入

```json
{
  "objective": "寻找官方公共采购API",
  "concepts": ["public procurement", "contracts", "API documentation"],
  "official_domains": ["open-contracting.org", "europa.eu"],
  "language": "en"
}
```

## 输出

- `tavily`：自然语言查询加 `include_domains`；
- `exa`：语义完整的自然语言查询，不使用Google操作符；
- `serpapi-google`：受限 `site:` 域名表达式、短关键词和文档类型；
- `baidu`：中文机构/主题词组合，删除 `site:`、`OR`、`filetype:` 等Google专用表达式。

该模块只生成查询，不直接访问网络，不持有密钥，也不执行自动多轮Agent循环。
