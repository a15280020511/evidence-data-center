# 战略情报固定数据源

该模块补充通用宏观和搜索连接器无法替代的结构化情报数据，包括灾害、互联网路由、网络互联设施和攻击技战术目录。

## 已实现、待真实验收的操作

```text
catalog-capabilities
source-access-matrix
openfema-disaster-declarations
ripestat-network-info
ripestat-prefix-overview
ripestat-as-overview
ripestat-bgp-state
peeringdb-search
peeringdb-object
mitre-attack-index
```

除两个本地目录操作外，其余操作必须在代码合并、CI通过后，再由GitHub Actions真实票据完成上游验收。未取得真实成功回执前，不标记为生产来源。

所有上游操作均设计为免 Key、固定 HTTPS 主机、单次只读请求。禁止任意 URL、任意请求头、自动翻页、自动重试、持续流、个人画像和写操作。

## 候选来源

OCDS、联合国/OFAC/英国制裁清单、WITS、EITI、UCDP、Global Fishing Watch、OpenSanctions 和 BODS 已进入 `source-access-matrix.json`。只有在端点、许可、免费条件和GitHub Actions出口真实验收全部通过后，才能升级为生产操作。

## 票据

Issue标题必须以：

```text
[intel-strategic-source]
```

开头。Issue正文必须是符合 `ticket.schema.json` 的单个JSON对象。每张票据最多调用一次上游。
