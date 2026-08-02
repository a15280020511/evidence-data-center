# World Bank Documents & Reports API

固定访问世界银行官方公开检索端点 `https://search.worldbank.org/api/v3/wds`，无需 API Key。

票据前缀：`[intel-worldbank-docs]`。

开放 7 项只读能力：本地目录、综合检索、按文档 ID、按项目 ID、按报告编号、按日期范围及 Facet 查询。覆盖世界银行公开报告、项目周期文件、研究论文、出版物和董事会文件元数据。

每张票据最多一次 GET，不自动翻页或重试，每次最多 50 条。仅保存公开元数据和官方文档链接，不批量下载 PDF/TXT 正文，不接受任意 URL、主机、路径或请求头。
