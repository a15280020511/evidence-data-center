# 百度AI网页搜索 Provider

该 Provider 只保留当前 `BAIDU_AI_CLOUD_API_KEY` 已真实调用验证通过、免费且对情报中心价值最高的百度公开网页搜索。

## 操作

| 操作 | 上游调用 | 用途 |
|---|---:|---|
| `catalog-capabilities` | 否 | 查看当前保留能力和安全边界 |
| `quota-policy` | 否 | 查看免费额度与零付费策略 |
| `web-search` | 是 | 检索中国大陆公开网页，返回标题、摘要、网址和引用 |

当前上游业务能力只有 `web-search`。它已使用现有统一 Key 完成 HTTP 200 真实验收。

## 凭据

Repository Secret：

```text
BAIDU_AI_CLOUD_API_KEY
```

只在 GitHub Actions 后端通过 Bearer Header 使用，不进入票据、日志或 Artifact。

## 已删除

以下能力不再登记、路由或维护：

- 智能搜索生成、深度搜索、网页总结、深度研究 Agent；
- NLP；
- OCR；
- 图像识别；
- 百度通用模型；
- 人脸、语音、生成式图像视频及云资源管理。

删除原因：

- 当前 Key 未完成可用且免费的真实验收；或
- 当前 Key 已明确返回 IAM 权限错误；或
- 存在模型、按次或后付费风险；或
- 对当前情报中心价值不足。

## 运行边界

- 每张票据只允许一个操作；
- 每张票据最多一次上游请求；
- 只允许 `qianfan.baidubce.com/v2/ai_search/web_search`；
- 禁止任意 URL、请求头、重试、翻页、重定向、后台任务和写操作；
- 模型调用固定为 0；
- 付费兜底固定为关闭；
- 免费额度耗尽时立即失败。

严格零费用仍要求百度控制台不启用按量后付费。
