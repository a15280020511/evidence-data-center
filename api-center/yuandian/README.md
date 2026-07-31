# 元典法律智能托管 Provider

正式票据前缀：`[api-yuandian]`。认证 Secret：`YUANDIAN_API_KEY`（兼容读取 `YD_API_KEY`，也可作为同名键放入 `API_CENTER_SECRETS_JSON`）。

能力分三层：

1. `catalog-capabilities`：读取仓库冻结的 37 项只读 API 快照；
2. `catalog-live`：读取元典官方公开 JSON 目录和完整请求/响应参数元数据；
3. 37 个固定操作与 `invoke-readonly-api`：固定操作映射冻结 routeKey；通用操作仅允许官方实时目录当前登记的 GET/POST routeKey。

所有业务请求固定发送到 `https://open.chineselaw.com/open/{routeKey}`，密钥只通过后端 `X-API-Key` 注入。禁止任意 URL、任意请求头、写入、代码执行和 Secret 回显。响应会递归过滤密钥、令牌、身份证号、手机号和邮箱等直接标识字段。

元典按积分计费。适配器每张票据只执行一次业务调用，不自动展开多接口链；组合查询应由 GPTs 拆成多个明确票据并控制预算。
