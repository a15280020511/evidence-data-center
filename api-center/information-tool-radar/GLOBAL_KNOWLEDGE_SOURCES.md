# 全球图书馆、资料库、文献库与影子库目录

## 目标

情报中心采用“全球聚合层优先、国家馆/专业库补充、影子库严格元数据隔离”的方式扩大知识覆盖。静态枚举不可能永久覆盖全球所有图书馆和数据库，因此生产设计不是维护一个宣称“全世界全部网站”的脆弱清单，而是优先接入能聚合成千上万机构的上层目录，再持续扩展国家级、学科级和地区级来源。

主注册表：`global-knowledge-sources.json`

治理/路由器：`global_knowledge_registry.py`

## 当前首批覆盖

注册表首批包含 53 个入口，覆盖：

- 图书与联合目录：Project Gutenberg、Standard Ebooks、Wikisource、Open Library、Internet Archive、Google Books、WorldCat、HathiTrust。
- 国家图书馆与文化遗产：Library of Congress、Europeana、DPLA、日本国立国会图书馆 NDL、法国 BnF/Gallica、德国 DNB、澳大利亚 Trove、中国国家图书馆。
- 全球学术元数据：Crossref、DataCite、OpenAlex、Semantic Scholar。
- 开放获取：DOAJ、DOAB、OAPEN、CORE、Unpaywall、OpenCitations、OpenAIRE、BASE。
- 医学与生命科学：PubMed、PubMed Central、Europe PMC、bioRxiv、medRxiv。
- 预印本与科研仓储：arXiv、Zenodo、Figshare、OSF、HAL。
- 专业文献：dblp、RePEc、ERIC、NASA ADS、INSPIRE HEP。
- 中国大陆文献入口：国家哲学社会科学文献中心、国家科技报告服务系统、CADAL。
- 影子库风险/书目目录：Anna's Archive、Library Genesis、Sci-Hub、Z-Library、Nexus/STC、OceanofPDF、MagzDB。

这里的“加入”分为三种状态：

1. `active-existing-adapter`：仓库已经有正式适配器，例如 Crossref、DataCite、Project Gutenberg、Wikisource、Anna 元数据搜索。
2. `ready` / `registered-key-required`：官方接口已经登记，控制器可以据此创建/启用相应只读适配器；需要 Key 的源在 Key 缺失时不会被标记为运行可用。
3. `catalog-only` / `registered`：先作为稳定目录和路由候选保留，后续在接口条款和机器接口确认后再升级，避免用网页抓取代替官方 API。

## 聚合层为什么优先

单独维护全球每一所图书馆并不稳定。更高覆盖的做法是先利用聚合源：

- OpenAlex：全球研究系统目录，覆盖海量论文、作者、机构、期刊等；当前官方 API 需要免费 Key，并提供免费额度及数据库快照。
- Crossref：全球 DOI/学术出版元数据，公共 REST API 无需注册即可使用。
- Open Library：免费公开的图书与作者目录 API，并可返回 Internet Archive 可用性信息。
- Europeana：聚合欧洲约 4,000 家文化机构，提供 Search、Record、Entity、IIIF、SPARQL、OAI-PMH 等接口；API 使用需要 Key。
- NDL Search：提供 SRU、OpenSearch、OpenURL、OAI-PMH，覆盖日本国立国会图书馆以及其联接的数据提供方。
- Europe PMC / PubMed：覆盖生命科学和医学文献；PMC 同时提供开放全文服务。

## 权利与全文读取

“出现在目录里”不等于“允许下载全文”。注册表把 `metadata`、`open-access discovery` 和 `fulltext-when-rights-open` 分开。

只有以下情况可以进入全文读取器：

- 来源自身明确声明 public domain；
- 条目具有开放许可；
- 平台明确提供 Full View / Open Access 文件；
- 用户提供自己有权访问的文件。

读取器仍应检查来源域名、HTTPS、条目权利、文件格式、重定向和文件大小。任何聚合源返回的外部链接都不能自动视为授权。

## 影子图书馆处理

影子库也登记，但属于完全不同的安全类别。生产规则固定为：

```text
影子库名称/公开书目线索
        ↓
metadata-only
        ↓
可用于判断“某书/论文是否有记录”
        ↓
禁止详情下载链、禁止文件获取、禁止绕过访问控制
```

注册表对所有 `category=shadow-library` 条目强制：

- `mode=metadata-only`；
- 不保存实际站点 endpoint；
- `network_access_allowed=false`；
- 不解析下载链接、IPFS、magnet、MD5 下载节点；
- 不绕过验证码、403、429、WAF、登录或付费墙。

Anna's Archive 是一个例外的“已有元数据适配器”：其当前域名仍按现有设计从 Wikimedia 临时发现，仅访问公开搜索结果中的可见书名，运行后丢弃域名。

## 使用

验证并生成全量路由报告：

```bash
python api-center/information-tool-radar/global_knowledge_registry.py \
  --registry api-center/information-tool-radar/global-knowledge-sources.json \
  --output global-knowledge-report.json \
  --enforce
```

只看开放获取类：

```bash
python api-center/information-tool-radar/global_knowledge_registry.py \
  --registry api-center/information-tool-radar/global-knowledge-sources.json \
  --category open-access-index \
  --available-only
```

排除所有影子库：

```bash
python api-center/information-tool-radar/global_knowledge_registry.py \
  --registry api-center/information-tool-radar/global-knowledge-sources.json \
  --exclude-shadow
```

## Key 管理

当前路由器已经为以下常见 Key 预留环境变量门禁：

- `OPENALEX_API_KEY`
- `EUROPEANA_API_KEY`
- `DPLA_API_KEY`
- `TROVE_API_KEY`
- `CORE_API_KEY`
- `NASA_ADS_API_TOKEN`

Key 缺失时来源仍留在知识源目录，但 `runtime_available=false`，不会伪装成已可调用。

## CI 门禁

`.github/workflows/global-knowledge-registry-quality.yml` 会验证：

- 注册表至少 50 个入口、至少 12 个类别；
- ID 唯一、字段完整、endpoint 必须 HTTPS；
- Key 来源在无 Key 环境中正确降为不可用；
- 影子库至少 7 个元数据登记项；
- 影子库运行网络访问数必须严格为 0；
- 人为给影子库加入 endpoint 或全文模式时测试必须拒绝。

## 后续扩展原则

新增来源时优先顺序：官方 API > OAI-PMH/SRU/OPDS/IIIF > 官方数据快照 > 官方网页目录。只有没有机器接口时才保留 `catalog-only`，不以高维护网页抓取冒充 API。

该结构允许继续加入更多国家图书馆、大学机构库、档案馆、博物馆、智库、学科数据库和地方数字馆藏，而不会把每一个来源都硬编码进主搜索程序。
