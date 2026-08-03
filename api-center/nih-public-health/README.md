# NIH Public Health Provider

统一接入以下公开只读服务：

- PubMed：NCBI E-utilities `ESearch` 与 `EFetch`
- openFDA：固定的药品、器械和食品数据集
- MedlinePlus：健康主题搜索
- NIH Clinical Tables：疾病、ICD-10-CM、RxTerms、LOINC 术语搜索

## 票据入口

Issue 标题前缀：`[intel-nih-health]`

每张票据只允许一个操作、一次上游请求。`NCBI_API_KEY`、`OPENFDA_API_KEY` 为可选提额密钥；未配置时仍可使用官方免密额度。密钥只从 Actions Secret 注入，不写入票据、日志、快照或目录。

## 安全边界

固定 HTTPS 主机、固定路径映射、禁止任意 URL、禁止任意请求头、禁止写操作、禁止自动翻页和自动重试。PubMed EFetch 每次最多 50 个 PMID，openFDA 每次最多 100 条。
