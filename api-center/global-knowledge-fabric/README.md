# Global Knowledge Fabric

第三波全球知识织网 Provider，固定接入16个免费或具有免费公共访问合同的来源，覆盖：

- ROR、ORCID、dblp：科研机构、研究者、作者、文献和场馆标识；
- Crossref Event Data：研究对象之间的公开关系事件；
- Harvard Dataverse、OpenML：公开科研和机器学习数据集；
- Grants.gov、Regulations.gov、Data.gov、EU CELLAR：政府资助、法规、数据目录和欧盟出版物；
- RCSB PDB、UniProt、ChEMBL：结构生物学、蛋白质和药物发现知识；
- IETF Datatracker：RFC、Internet-Draft 和标准过程元数据。

## 固定操作

`catalog-capabilities`、`source-access-matrix`、`entity-search`、`scholarly-search`、
`dataset-search`、`government-search`、`science-search`、`record-get`、`standards-search`。

## 凭证

- `ORCID_PUBLIC_API_TOKEN`：ORCID Public API 的长期 `/read-public` Token。
- `REGULATIONS_GOV_API_KEY`、`DATA_GOV_API_KEY`：免费 api.data.gov Key。
- `ROR_CLIENT_ID`：可选客户端标识，不是授权凭证；未配置时仍允许低频访问。

## 安全合同

固定 HTTPS 主机、路径和参数；每票最多一次上游请求；禁止任意 URL、任意 SPARQL、
自动分页、自动重试、重定向、写入、评论提交、付费墙绕过、患者级数据和个人画像。
