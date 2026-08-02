# Asian Development Bank KIDB SDMX

通过亚洲开发银行官方 Key Indicators Database（KIDB）SDMX API v4 读取亚洲及太平洋宏观、金融、社会、环境与可持续发展统计。

- 票据前缀：`[intel-adb]`
- 固定主机：`kidb.adb.org`
- 公开接口，无需账户凭据
- 官方限速：每分钟最多 20 次查询
- 每张票据最多一次 GET，不自动重试或翻页
- 数据查询最多 20 个指标、20 个经济体、25 年
- 禁止空维度全库请求、任意 URL、任意请求头和写操作

主要能力：数据流目录、数据流定义、数据结构、代码表、概念表、指标目录，以及有界 SDMX JSON/CSV 数据读取。
