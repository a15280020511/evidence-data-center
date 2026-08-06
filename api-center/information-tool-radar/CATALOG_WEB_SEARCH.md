# 受控网页书目搜索

该能力由情报中心自己维护，只读取公开搜索结果页中的可见书名，不依赖任何第三方 Anna’s Archive Python API、SDK、CLI 或下载器。

## 固定边界

- 仅使用 Python 标准库。
- 仅访问 `catalog-domains.json` 中启用且批准的 HTTPS 域名。
- 仅请求 `/search?q=...`。
- 只保存可见书名、数量、HTTP 状态和诊断信息。
- 不进入书籍详情页，不保存结果链接，不下载文件，不读取正文。
- 不安装或执行第三方封装。
- 不绕过验证码、反自动化、访问控制、限流或付费墙。

## 域名变化处理

1. 主域名失败时，只尝试清单中已经批准的备用域名。
2. 批准域名出现跨域跳转时，不跟随跳转，只把目标主机记录为候选。
3. 所有批准域名不可用时立即失败关闭，并在 Actions 中留下证据。
4. 新域名必须通过独立 PR 加入清单，并完成 TLS、HTTP、搜索结果结构、来源和安全复核。
5. 搜索引擎、论坛、社交媒体或未知镜像发现的域名不得自动启用。

这种设计不能保证域名永远不变，但能防止系统在域名变化时自动连接钓鱼镜像或恶意站点。

## 使用

```bash
python api-center/information-tool-radar/catalog_web_search.py \
  --registry api-center/information-tool-radar/catalog-domains.json \
  --query "孙子兵法" \
  --output catalog-search-report.json \
  --enforce
```

GitHub Actions 的手动运行支持传入 `catalog_query`；定时健康检查默认使用“孙子兵法”作为无害书目合同测试词。
