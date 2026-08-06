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
- 拒绝JavaScript、OpenAction、Launch、远程跳转、XFA和其他主动内容；
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

- Anna's Archive：公开书目元数据；
- Open Library、Internet Archive、Google Books、Library of Congress、Gallica、日本国会图书馆、德国国家图书馆等：书目或馆藏查询；
- Project Gutenberg、Standard Ebooks、英文/中文Wikisource和Wikimedia：公版或开放许可全文读取；
- Europeana和DPLA：已接入，但需要各自的API Key。

这些能力不是一个“全网书籍API”。Gutenberg、Standard Ebooks和Wikisource当前能读取已知合法URL的全文，但尚未统一成一个专用书目搜索适配器。

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
