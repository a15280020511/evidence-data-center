# HexDB 航空器元数据补全

该 Provider 用于补全 OpenSky 状态向量不包含的静态航空器和航线信息，固定访问：

```text
https://hexdb.io/api/v1
```

无需 API Key，票据前缀：

```text
[intel-hexdb]
```

## 能力

- `aircraft-by-icao24`：注册号、制造商、ICAO 机型代码、具体机型、登记所有人、运营方代码；
- `route-by-icao-callsign`：ICAO 呼号对应的推定航线；
- `route-by-iata-callsign`：IATA 呼号对应的推定航线；
- `airport-by-icao`：ICAO 机场代码对应的机场名称、IATA、国家、地区和坐标；
- `airport-by-iata`：IATA 机场代码对应的机场名称、ICAO、国家、地区和坐标；
- `catalog-capabilities`：本地能力目录。

## 与 OpenSky 的组合

OpenSky 提供实时经纬度、高度、速度、航迹角、垂直速度和 ICAO24。将 OpenSky 返回的 `icao24` 传给 `aircraft-by-icao24`，即可补全飞机注册号、制造商和具体型号；将呼号传给航线操作，可补全推定起讫机场。

## 固定边界

- 每张票据只查询一个标识符，并只发送一次 GET；
- 不自动重试、不自动翻页、不批量抓取、不获取图片；
- 固定主机 `hexdb.io`，禁止任意 URL、主机、请求头和写操作；
- 上游公开说明为每 5 分钟不超过 1000 次请求，情报中心进一步限制并发为 1；
- 数据来自第三方和众包来源，可能缺失、陈旧或有误，不替代民航主管机关登记或适航资料。
