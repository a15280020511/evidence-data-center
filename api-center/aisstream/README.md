# AISstream Provider

Ticket prefix: `[intel-aisstream]`

Repository Secret:

```text
AISSTREAM_API_KEY
```

固定上游：`wss://stream.aisstream.io/v0/stream`

能力：

- `catalog-capabilities`
- `collect-messages`
- `collect-vessel-positions`
- `collect-vessel-static`

每张票据只允许一次短时 WSS 连接；最长 30 秒、最多 4 个有限区域、20 个 MMSI、8 种消息类型和 200 条消息。禁止全球无限订阅、后台常驻、转发、写入和交易。
