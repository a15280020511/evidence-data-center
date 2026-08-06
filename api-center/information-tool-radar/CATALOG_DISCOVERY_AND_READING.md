# 目录域名发现与合法书籍读取

## 域名发现

`catalog_domain_discovery.py`通过Wikidata实体搜索、Wikidata `P856`网站声明和Wikipedia外部链接寻找候选域名。

发现结果只进入候选报告：

- 不修改`catalog-domains.json`；
- 不自动启用新域名；
- 不跟随旧域名跳转到未知域名；
- 每个候选保留Wikidata实体、Wikipedia页面、语言和来源链接；
- 新域名必须经过身份来源、TLS、页面结构、安全与法律复核，并通过PR更新允许名单。

Wikipedia/Wikidata可能滞后、缺失或被错误编辑，所以它们只属于线索源，不是信任根。

## 统一公版书搜索

`public_book_search.py`提供一个统一、只读、低频的公版书和开放文本搜索入口，当前固定查询：

- Project Gutenberg官方OPDS；
- Standard Ebooks公开书目搜索页；
- English Wikisource官方MediaWiki API；
- 中文维基文库官方MediaWiki API。

统一搜索规则：

- 来源、主机、路径和解析器全部由`public-book-search-sources.json`固定；
- 每个来源每次任务最多一次请求；
- 串行执行，来源之间保持10秒间隔；
- 不自动翻页，不自动重试，不跟随重定向；
- 401、403、429立即停止该来源，不换IP、账号、Cookie、User-Agent、端点或执行平台；
- 一个独立来源拒绝后，其他独立来源仍可按原定扇出计划执行，这不是对同一来源的规避或回退；
- Gutenberg只保留官方OPDS声明的可读位置；
- Standard Ebooks只返回公开落地页，不自动进入会员下载、认证Feed或合集下载；
- Wikisource返回公开页面地址，实际版本和单项权利仍需核验；
- Anna's Archive不属于该全文搜索适配器。

工作流：`.github/workflows/public-book-search.yml`。输出包括归一化书名、作者、来源、落地页、来源声明的可读格式、请求回执、硬停止状态和安全策略快照。

## 合法书籍读取

`lawful_book_reader.py`和`lawful_pdf_reader.py`共用同一套来源、权利声明、HTTPS、重定向和未知域名拒绝策略，只允许以下权利基础：

- `public-domain`：公版书；
- `open-license`：明确开放许可；
- `user-provided`：用户已合法持有并明确授权处理的本地文件。

远程下载仅限`lawful-book-sources.json`中的批准来源。目前包括Project Gutenberg、Standard Ebooks、Wikisource和经过单项权利声明的Wikimedia文件。

支持格式：

- EPUB；
- HTML/XHTML；
- TXT；
- PDF，由`lawful_pdf_reader.py`处理。

PDF读取器执行额外限制：

- 最多2,000页；
- 默认最多25 MB；
- 拒绝加密PDF；
- 允许只决定初始显示页面或执行文档内部跳转的静态目标；
- 拒绝JavaScript、启动外部程序、表单提交、外部文件跳转、媒体动作、XFA和其他主动内容；
- 拒绝内嵌文件；
- 不执行PDF中的动作、链接或脚本；
- 可要求PDF必须含可提取的文字层；
- 输出源文件和正文SHA-256。

输出包括：

- 书籍元数据；
- 目录条目；
- 章节或页级有界摘录；
- 有上限的正文文本；
- 下载字节数、页数、文字层状态、截断状态和权利依据；
- PDF安全检查结果；
- 源文件与正文哈希。

默认不保留原始书籍文件。手动工作流可对公版或开放许可来源选择将下载文件放入短期GitHub Actions Artifact。

## 公共书籍来源覆盖

`public-book-source-coverage.json`记录当前书籍查询和全文读取的实际覆盖：

- Project Gutenberg、Standard Ebooks、英文/中文Wikisource：已经进入统一公版书搜索；
- Anna's Archive：单独保留公开书目元数据检索；
- Open Library、Internet Archive、Google Books、Library of Congress、Gallica、日本国会图书馆、德国国家图书馆等：继续通过各自固定书目或馆藏Provider查询；
- Europeana和DPLA：已接入，但需要各自API Key；
- Wikimedia：用于经过单项权利确认的合法文件和PDF读取。

这些能力不是一个“全网书籍API”。统一公版书搜索不掩盖不同图书馆的Key、额度、权利字段和返回合同，因此更广泛的书目Provider仍保持独立。

## 为什么Anna只做书目元数据

Anna's Archive聚合的记录可能指向公版、开放许可、受版权保护或授权状态不清楚的文件。仅凭Anna的一条书目记录，系统无法证明具体文件已获得权利人授权，也无法把“能看到下载链接”视为下载许可。

此外，进入详情和下载链路经常涉及动态跳转、验证码、限流、登录、外部文件主机或其他访问控制。建立自动解析、重试、换域名或绕过限制的下载器，会把系统从公开书目查询变成受限文件获取工具。情报中心因此采用以下边界：

- Anna只读取公开可见书目元数据；
- 不进入书籍详情和下载链接；
- 不解析直链、镜像链或外部文件主机；
- 不绕过验证码、WAF、登录、会员、限流或其他技术措施；
- 需要全文时，优先使用公版/开放许可来源，或处理用户依法提供的本地文件。

这不是技术上“完全打不开”，而是无法对Anna所有下载结果建立统一、可靠的授权证明，也不能把规避访问限制设计成生产功能。

## 明确禁止

- 不从Anna's Archive下载书籍或PDF；
- 不进入Anna书籍详情或下载链接；
- 不解析Anna直链；
- 不绕过验证码、反自动化、访问控制、限流或付费墙；
- 不允许未知域名；
- 不允许以用户填写的声明覆盖域名允许名单；
- 不把候选域名自动提升为生产域名；
- 不处理来源或授权状态不明确的远程书籍；
- 不把书目搜索结果当作下载授权证明。
