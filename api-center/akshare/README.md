
# AKShare 托管适配器

正式票据前缀：`[api-akshare]`。

该适配器直接在隔离的 GitHub Actions 任务中安装固定版本 AKShare，并只暴露
`provider-catalog.json` 中列出的固定只读函数。它不开放任意函数名、任意 URL、
Python 代码、券商登录或交易执行。

AKShare 上游网页接口可能变化，因此所有结果必须保留版本、时间和 Artifact 证据；
关键投资决定还应与交易所公告、上市公司公告和持牌金融机构数据交叉核验。

## Ashare 轻量行情提供方

同一受控工作流还接受 `[api-ashare]` 票据。该提供方兼容 `get_price` 的核心语义，
只开放固定 `ashare-get-price` 操作，使用腾讯固定端点作为主源、Sina固定端点作为备用。
它不复制上游项目代码，不允许任意URL、任意函数、券商连接、下单或自动交易。
