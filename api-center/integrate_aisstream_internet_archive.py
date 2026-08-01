#!/usr/bin/env python3
"""One-shot deterministic registration for AISstream and Internet Archive."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def save(path: str, text: str) -> None:
    (ROOT / path).write_text(text.rstrip() + "\n", encoding="utf-8")


path = "api-center/tests/test_api_catalog.py"
text = load(path)
if '    "aisstream": 4,\n' not in text:
    text = text.replace(
        '    "statistics-of-the-world": 11,\n',
        '    "statistics-of-the-world": 11,\n    "aisstream": 4,\n    "internet-archive": 6,\n',
    )
text = text.replace('catalog["managed_provider_count"], 32', 'catalog["managed_provider_count"], 34')
text = text.replace('catalog["enabled_managed_provider_count"], 32', 'catalog["enabled_managed_provider_count"], 34')
text = text.replace('catalog["managed_operation_count"], 363', 'catalog["managed_operation_count"], 373')
if '            "aisstream": "AISSTREAM_API_KEY",\n' not in text:
    text = text.replace(
        '            "mediastack": "MEDIASTACK_API_KEY",\n',
        '            "mediastack": "MEDIASTACK_API_KEY",\n            "aisstream": "AISSTREAM_API_KEY",\n',
    )
marker = '        who = providers["who-gho-odata"]\n'
block = '''        aisstream = providers["aisstream"]
        self.assertEqual(aisstream["ticket_prefix"], "[intel-aisstream]")
        self.assertEqual(
            aisstream["required_secret_environment_variable_name"],
            "AISSTREAM_API_KEY",
        )
        self.assertEqual(len(aisstream["operations"]), 4)
        self.assertFalse(aisstream["limits"]["worldwide_subscription_allowed"])
        self.assertFalse(aisstream["limits"]["background_streaming_allowed"])
        self.assertFalse(aisstream["limits"]["write_operations_allowed"])

        internet_archive = providers["internet-archive"]
        self.assertEqual(
            internet_archive["ticket_prefix"],
            "[intel-internet-archive]",
        )
        self.assertEqual(
            internet_archive["required_secret_environment_variable_name"],
            "",
        )
        self.assertEqual(len(internet_archive["operations"]), 6)
        self.assertFalse(internet_archive["limits"]["file_downloads_allowed"])
        self.assertFalse(internet_archive["limits"]["uploads_allowed"])
        self.assertFalse(internet_archive["limits"]["write_operations_allowed"])

'''
if '        aisstream = providers["aisstream"]\n' not in text:
    if marker not in text:
        raise RuntimeError("test_api_catalog insertion marker missing")
    text = text.replace(marker, block + marker, 1)
save(path, text)

path = "api-center/tests/test_capability_maximization.py"
text = load(path)
text = text.replace('            363,\n', '            373,\n', 1)
if '            "aisstream": 4,\n' not in text:
    text = text.replace(
        '            "statistics-of-the-world": 11,\n',
        '            "statistics-of-the-world": 11,\n            "aisstream": 4,\n            "internet-archive": 6,\n',
        1,
    )
save(path, text)

path = "api-center/README.md"
text = load(path)
if "## AISstream 全球船舶实时AIS" not in text:
    text += '''

## AISstream 全球船舶实时AIS

```text
Provider: aisstream
Ticket prefix: [intel-aisstream]
Repository Secret: AISSTREAM_API_KEY
Operations: 4
Fixed endpoint: wss://stream.aisstream.io/v0/stream
```

只允许短时、有限区域、有限消息数的只读AIS采集。禁止全球无限订阅、后台常驻、流转发、任意WSS端点、客户端密钥、写操作和交易执行。

## 互联网档案馆 Internet Archive

```text
Provider: internet-archive
Ticket prefix: [intel-internet-archive]
Secret: none
Operations: 6
Fixed hosts: archive.org, web.archive.org
```

支持受控馆藏搜索、项目元数据、文件目录、Wayback可用性和有限CDX捕获记录。禁止上传、删除、登录、借阅、文件内容下载、网页正文回放抓取和批量镜像。
'''
save(path, text)

path = "api-center/SECRET_ISOLATION_POLICY.md"
text = load(path)
if "## AISstream" not in text:
    text += '''

## AISstream

```text
Repository Secret: AISSTREAM_API_KEY
```

该Key只允许在专用GitHub Actions后端写入AISstream订阅消息并发送至`wss://stream.aisstream.io/v0/stream`。客户端不得提交或覆盖Key；Key不得进入Issue、目录、日志、诊断或Artifact。

## Internet Archive

Internet Archive Provider不使用Secret，只访问`archive.org`与`web.archive.org`的固定公开只读端点。
'''
save(path, text)
