# Google公开情报 Provider

该 Provider 使用统一 Repository Secret：

```text
GOOGLE_PUBLIC_INTELLIGENCE_API_KEY
```

服务范围：

| Google API | 生产能力 | 典型用途 |
|---|---|---|
| YouTube Data API v3 | 视频检索、视频详情、频道详情 | 视频舆情、传播时间线、频道画像、公开统计 |
| Google Books API | 由 `global-knowledge-archives` 提供图书检索和单卷详情 | ISBN、作者、出版社、版本和主题核验 |
| Fact Check Tools API | 事实核查搜索 | 谣言、争议信息和核查来源发现 |
| PageSpeed Insights API v5 | 公开HTTPS页面的Lighthouse审计 | 网站性能、SEO、无障碍和最佳实践分析 |
| Chrome UX Report API | 当前及历史真实用户体验 | LCP、INP、CLS及网站性能趋势 |

## 本 Provider 操作

```text
catalog-capabilities
quota-policy
youtube-search-videos
youtube-video
youtube-channel
factcheck-search
pagespeed-analyze
crux-query
crux-history-query
```

Google Books 保留在全球资料库 Provider 中，避免重复目录；其凭据由旧的 `GOOGLE_API_KEY` 迁移为同一把 `GOOGLE_PUBLIC_INTELLIGENCE_API_KEY`。

## 安全边界

- 每张票据一个操作，最多一次上游请求；
- 禁止自动翻页、自动重试和重定向；
- 只允许四个固定Google官方API主机；
- YouTube只读取公开资源，不启用OAuth，不访问私人账户数据；
- PageSpeed和CrUX仅接受公开HTTPS网址或来源；拒绝localhost、私有后缀、IP字面量和URL凭据；
- 禁止写入、上传、评论、订阅、ClaimReview修改和任何用户账户操作；
- API Key只由GitHub Actions后端注入，不进入票据、日志或Artifact；
- 不存在付费兜底，配额耗尽立即失败。

## 生命周期原则

这五项服务当前均真实调用通过，但任何第三方API都不能获得“永久不停止”的保证。仓库按以下原则管理：

1. 只使用当前官方版本和固定端点；
2. 定期检查官方修订历史、弃用通知和控制台配额；
3. 版本或字段变化时显式失败，不静默生成错误数据；
4. 不使用即将停止的 Google Custom Search API；
5. 服务退役时删除或替换对应能力，不使用非官方抓取规避平台规则。

详细免费额度、使用场景和稳定性评级见 `quota-policy.json`。
