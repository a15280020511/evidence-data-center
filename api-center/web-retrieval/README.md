# Jina Reader 与 Exa 托管网页检索 Provider

本目录为证据数据中心提供两个独立的只读网页检索能力：

- `jina-reader`：把公开 HTTPS 网页或公开 PDF 转换为适合大模型使用的内容。
- `exa`：搜索公开网页，或对已知 URL 提取正文/高相关片段。

## Repository Secrets

### Jina Reader

```text
JINA_API_KEY
```

该 Secret 是可选的。未配置时，`read-url` 使用 Jina 官方匿名基础额度；配置后仅在后端作为 `Authorization: Bearer ...` 注入。

### Exa

```text
EXA_API_KEY
```

该 Secret 是必需的，只在后端 `x-api-key` 请求头中注入。

## 正式票据

Issue 标题必须以：

```text
[api-web]
```

开头。票据只能处理公开、非个人数据；每张票据最多执行一次上游调用。

## 安全边界

- 只允许 HTTPS。
- 禁止 URL 用户名、密码和非 443 端口。
- 禁止回环、私有、链路本地、保留、组播和云元数据地址。
- DNS 解析结果中只要出现非公网 IP 即拒绝。
- 不接受 Cookie、任意请求头、代理、脚本或登录态。
- Exa 不开放 Answer、Agent、Research、Websets 和联系人富集。
- Secret 值不进入代码、目录、Issue、日志、评论或 Artifact。
