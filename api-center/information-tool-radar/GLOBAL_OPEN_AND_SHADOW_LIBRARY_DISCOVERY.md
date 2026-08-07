# 全球开放图书馆与影子图书馆发现层

## 目标

情报中心不再试图用一个静态网址清单代表“全球所有图书馆”。生产结构改为：

```text
全球父级发现器
→ 国家馆 / 联合目录 / 大学与科研机构仓储
→ 候选接口核验
→ 治理审批
→ 生产搜索适配器
```

开放图书馆父级发现器包括 IFLA Library Map of the World、IFLA National Libraries、OpenAlex Institutions/Sources、OpenDOAR、OpenAIRE、BASE、WorldCat、Internet Archive、Open Library、Europeana、DPLA、Trove、NDL Search 和 Wikidata。

`global-open-library-discovery-sources.json` 只负责发现骨架。新发现的子站点不能自动晋升生产，必须重新核验 HTTPS、访问合同、Key、费用、许可、限流和全文权利。

## 影子图书馆

所有影子图书馆统一执行：

```text
名称 / 别名
→ Wikipedia 页面
→ Wikipedia pageprops 获取 Wikidata 实体
→ Wikidata P856 临时解析当前网站候选
→ 只在当前进程中交给批准的书目元数据适配器
→ 任务结束立即丢弃
```

仓库禁止保存影子图书馆固定域名、镜像域名、Onion 地址、IPFS、magnet、MD5 下载定位符和直接下载链接。

种子注册表：`shadow-library-wikimedia-sources.json`。

当前种子覆盖 Anna's Archive、Library Genesis、Sci-Hub、Z-Library、UbuWeb、Flibusta、Library.nu/Gigapedia、Monoskop、Textz.org、Librusec、Nexus/STC、OceanofPDF、MagzDB、Pirate Library Mirror、Scorser。种子不是“世界上永远只有这些”，后续通过 Wikipedia/Wikidata 文档继续扩展。

## 运行时隐私与可维护性

`shadow_library_wikimedia_discovery.py` 可以在内存中解析 Wikidata P856，但 CLI 报告只保留候选数量和 SHA-256 指纹，不输出实际域名，也不写入注册表。这样域名变化时无需维护仓库，同时避免把临时镜像变成持久配置。

## 内容边界

开放、公版、开放许可和来源明确声明可公开读取的内容，可以进入已有全文读取器。

影子图书馆只进入书目/元数据层，不进入详情下载链，不解析或生成下载直链，不获取版权文件，不绕过验证码、403/429、登录、付费墙、WAF 或其他访问控制。
