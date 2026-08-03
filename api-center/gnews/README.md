# GNews Provider

受治理的 GNews 官方 REST API 只读 Provider。

## 操作

- `catalog-capabilities`
- `search-news`
- `top-headlines`

## 凭据

Repository Secret：`GNEWS_API_KEY`。

凭据仅通过 `X-Api-Key` 请求头在后端注入，不接受票据携带的 Key，也不会写入日志、快照或 Artifact。

## 套餐边界

免费套餐仅用于非商业开发与测试：100 次/日、每次最多 10 篇、约 12 小时延迟、最多 30 天历史。生产或商业用途需要符合 GNews 的付费套餐与服务条款。

## 治理边界

固定主机 `gnews.io`，固定路径 `/api/v4/search` 和 `/api/v4/top-headlines`。每票据单请求，无自动翻页、自动重试、后台轮询、写操作或文章正文二次抓取。
