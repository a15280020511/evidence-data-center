# 情报中心：全源公开情报能力实施方案

治理权威：`decision-system-governance/PUBLIC_INTELLIGENCE_AND_THINK_TANK_BLUEPRINT.json`。

## 目标

把情报中心从“外部 API 连接器集合”升级为“全球公开信息、工具和方法的发现与证据工程中心”。范围包括 API、MCP、搜索、浏览器、爬虫、文档、多媒体、NLP、实体消歧、知识图谱、地理、公开网络威胁情报、来源治理和工程安全。

## 六个独立机器目录

```text
registries/data_sources.jsonl
registries/intelligence_tools.jsonl
registries/mcp_candidates.jsonl
registries/models_and_datasets.jsonl
registries/reference_methods.jsonl
registries/standards_and_protocols.jsonl
```

不得把工具仓库或 MCP Manifest 当成数据端点。每个目录使用独立 Schema、状态和去重键。

## 第一阶段：结构化注册表扫描

优先实现无需通用网页搜索的确定性发现器：

- APIs.guru 与 OpenAPI 目录；
- PyPI、conda-forge、CRAN/R-universe、Julia General；
- npm、Maven、NuGet、RubyGems、crates.io、Go modules；
- GitHub/GitLab 官方仓库与 Releases；
- MCP 注册表、官方 MCP 仓库和 Manifest；
- Hugging Face 模型、数据集和 Spaces；
- OpenML、Zenodo、Software Heritage；
- OpenAlex、Crossref、DataCite、re3data、OpenAIRE；
- CKAN、Socrata、ArcGIS Hub、STAC；
- OSV、deps.dev、NVD、CISA KEV、OpenSSF、SPDX、CycloneDX、Sigstore。

每个发现器只读元数据，不安装、不执行、不授权、不提交密钥。

## 第二阶段：多语言全球补漏

按能力族而不是单一“API”关键词轮换：

1. 搜索、元搜索、语义搜索、新闻、论文、专利、法律、公司、代码、数据集、模型和图片搜索；
2. 浏览器、远程浏览器、无头浏览器、JavaScript 渲染、截图和网络记录；
3. 爬虫、抓取、RSS、Sitemap、变化检测、网页归档和附件发现；
4. HTML、PDF、表格、OCR、Office、邮件、图片、音频和视频解析；
5. 翻译、语音转写、实体、关系、事件、时间、地点、引文和主张抽取；
6. ETL、Schema、校验、字段映射、单位、时间和格式转换；
7. 实体消歧、记录链接、公司/机构/地址标准化和标识符映射；
8. RDF、知识图谱、证据图、引文图、时间图、全文/向量/地理索引；
9. GIS、遥感、STAC、COG、NetCDF、HDF5、WMS/WFS/WMTS；
10. STIX/TAXII、MISP/OpenCTI 连接器、CVE/CWE/CPE/ATT&CK 等公开防御性情报；
11. OpenLineage、来源、快照、哈希、版本、许可证、额度和证据包；
12. SBOM、漏洞、依赖、Secret、静态分析、许可证和供应链安全；
13. 测试、HTTP 回放、契约、负载、日志、指标、追踪和 Artifact；
14. 官方方法、协议标准、数据字典、分类法、OSINT 和分析培训资料。

每个国家至少维护英文、本国语言和当地政府域名三组搜索面；欠覆盖地区单独轮换。

## 第三阶段：候选元数据和评分

每个候选至少记录：

```text
candidate_id
name
surface_type
capability_families
official_owner
official_url
repository
registry
latest_version
release_date
license
free_model
key_required
card_required
auto_overage_risk
quota
rate_limit
runtime_platform
network_requirement
offline_support
dependencies
sbom
vulnerabilities
maintenance_status
documentation_status
test_signal
resource_requirements
existing_overlap
center_fit
security_risks
status
rejection_reasons
evidence_urls
checked_at
```

星标数只能作为弱信号，不能决定晋级。

## 第四阶段：情报工作流

```text
需求/PIR
→ 采集计划
→ 多源发现
→ 只读采集
→ 文档与媒体解析
→ 实体、关系、事件、主张抽取
→ 去重与实体消歧
→ 来源评级
→ 交叉验证、矛盾和缺口
→ 证据图与时间线
→ 弱信号和预警
→ 证据包
```

来源评级必须分别记录：官方性、原始性、采集方式、可靠性、可信度、时效、覆盖、偏差、局限和不确定性。

## 第五阶段：自动化边界

允许自动：

- 查询公开注册表；
- 读取固定官方文档和只读端点；
- 下载有界文本元数据和小样本；
- 检查 Manifest、锁文件、许可证、SBOM 和漏洞；
- 登记候选、生成覆盖缺口和创建评审 Issue；
- 对高价值免费 Key 候选发送 Server酱通知。

禁止自动：

- 安装新包；
- 执行未知代码、容器、二进制或本地 MCP；
- 安装浏览器扩展；
- 进行 OAuth 授权；
- 提交或读取 Secret 值；
- 开启写 API、交易或付费计费；
- 绕过访问控制、付费墙、robots 或速率限制；
- 采集私人数据、隐蔽监控或个人目标跟踪。

## 调度

- 每日：变更、漏洞、停用、关键数据更新、弱信号、到期健康检查；
- 每周：全能力族、全软件生态、全来源类型和多语言平衡轮换；
- 每月：免费、绑卡、超额、许可、维护、安全和重复审计；
- 每季度：前沿工具评审、欠覆盖地区专项补漏和架构淘汰。

## 验收指标

- 国家、语言、行业、来源类型、协议、工具表面和能力族覆盖率；
- 新增官方高价值来源数；
- 新增可用免费工具候选数；
- 重复率、误报率、失效率和安全淘汰率；
- 每个搜索引擎每信用点的有效候选产出；
- 关键变更发现延迟；
- 来源证据完整率；
- 未覆盖能力和地区清单。
