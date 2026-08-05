# 全球专业细分开放 API

第二批专业来源覆盖五个现有聚合层不能完全替代的行业面：

- 自然历史和馆藏研究数据：Natural History Museum Data Portal；
- 材料科学和晶体结构：Materials Cloud OPTIMADE；
- 政府政策、法规说明和出版物：GOV.UK Search API；
- 博物馆艺术与文化遗产：Rijksmuseum Search API；
- 地质、地震、滑坡、钻孔和传感器集合：BGS OpenGeoscience OGC API。

所有操作均固定主机、固定路径、单请求、只读、无重试、无翻页、无重定向。OPTIMADE只允许固定数据库和经过验证的元素列表，禁止客户端提供任意过滤表达式。

来源只有在独立GitHub Actions真实票据通过后才能进入生产矩阵。
