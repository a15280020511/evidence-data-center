# BIS SDMX API

固定访问国际清算银行官方 `https://stats.bis.org/api/v2`，无需 API Key。票据前缀为 `[intel-bis]`。

开放 8 项只读能力：能力目录、数据流、数据流定义、数据结构、代码表、概念表、数据读取和数据可用性。每票据最多一次 GET，不自动翻页、重试或批量下载。引用 BIS 数据时必须注明 BIS 为来源。

诊断与 Snapshot 中的 `row_count` 按实际 SDMX 数据流、结构集合、序列或观测集合计数，不将外层消息容器误计为一条数据。
