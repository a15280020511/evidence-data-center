# AKShare / Ashare 托管适配器

正式票据前缀：AKShare 使用 `[api-akshare]`，Ashare 使用 `[api-ashare]`。

AKShare 开放模式为 **maximum-safe-readonly**：

- 保留 A 股行情、历史、公司资料和财务指标快捷操作；
- `catalog-readonly-functions` 枚举固定安装版本中通过安全校验的全部公共只读函数、签名、参数和说明；
- `invoke-readonly-function` 只调用实时发现、无可变参数、无副作用关键词、无 URL/文件/代码参数的函数；
- 参数必须是受限 JSON，并与函数签名一致；结果受超时、行数和体积限制。

禁止券商连接、交易、下单、账户操作、任意 URL、脚本和文件写入。Ashare 仍只暴露固定的只读行情入口。
