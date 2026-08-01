# Alpha Vantage 托管 Provider

固定官方端点：

```text
GET https://www.alphavantage.co/query
```

正式票据前缀与独立 Repository Secret：

```text
[api-alpha-vantage]
ALPHA_VANTAGE_API_KEY
```

该 Provider 固定开放 66 项只读操作（含 1 项本地能力目录），覆盖：

- 全球股票、指数、期权和市场状态；
- 公司基本面、财务报表、公司行动、持仓和 ETF；
- 新闻情绪、涨跌榜；
- 外汇、数字资产、商品；
- 美国宏观经济指标；
- 常用技术指标。

安全边界：

- 不允许票据传入 `apikey`、任意 `function`、任意 URL、任意请求头或 CSV；
- API Key 仅在后端查询参数中注入，不进入 Issue、日志或 Artifact；
- 每张票据最多一次上游调用，不做自动重试；
- 全 Provider 使用串行并发组，降低免费额度被并发耗尽的风险；
- 免费密钥官方标准额度为每日 25 次请求；部分函数、实时/延迟行情和完整历史数据需要付费权限；
- 不开放交易、下单、账户修改或写入。

## 示例票据

Issue 标题：

```text
[api-alpha-vantage] IBM daily
```

Issue 正文：

```json
{
  "task_id": "av-ibm-daily-001",
  "provider": "alpha-vantage",
  "operation": "stock-daily",
  "parameters": {
    "symbol": "IBM",
    "outputsize": "compact"
  },
  "acceptance": {
    "timeout_seconds": 30,
    "max_response_bytes": 5000000
  },
  "data_policy": {
    "public_data_only": true,
    "no_personal_data": true,
    "no_secret_values": true
  }
}
```
