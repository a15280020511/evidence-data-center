# 天地图中国大陆固定公网出口运行手册

## 目标状态

天地图生产票据只能在以下执行环境运行：

```text
中国大陆云服务器
Linux x64
GitHub self-hosted runner
独立固定公网 IPv4 / EIP
自定义 Runner 标签：tianditu-mainland-egress
```

工作流不再回退到 GitHub 托管 Runner。Runner 离线、出口 IP 改变或仓库变量未配置时，天地图请求会被拒绝，不会从其他出口继续调用。

## 1. 准备服务器

建议使用中国大陆地域的轻量云服务器或云主机：

```text
系统：Ubuntu 22.04 LTS 或 Ubuntu 24.04 LTS
架构：x86_64
最低配置：1 vCPU / 2 GB RAM / 20 GB 磁盘
公网：绑定独立固定公网 IPv4 或弹性公网 IP
出站：允许 HTTPS 443
入站：仅保留管理所需 SSH；不需要为 GitHub Runner 开放业务端口
```

不要使用会自动变化的共享 NAT 出口。服务器重启、更换实例或扩缩容后，公网出口必须保持不变。

## 2. 创建专用系统用户

```bash
sudo useradd --create-home --shell /bin/bash github-runner
sudo install -d -o github-runner -g github-runner /opt/actions-runner
```

Runner 不得以 root 身份长期运行，不要在该服务器部署其他公开 Web 服务。

## 3. 注册 Repository self-hosted runner

在 GitHub 仓库中打开：

```text
Settings
→ Actions
→ Runners
→ New self-hosted runner
→ Linux
→ x64
```

以 `github-runner` 用户执行页面实时生成的下载与注册命令。注册时增加专用标签：

```bash
./config.sh \
  --url https://github.com/a15280020511/evidence-data-center \
  --token <GitHub 页面生成的一次性注册令牌> \
  --name tianditu-mainland-01 \
  --labels tianditu-mainland-egress \
  --unattended \
  --replace
```

注册令牌短期有效，必须从 GitHub Runner 设置页面实时取得，禁止写入仓库、Issue、日志或长期 Secret。

## 4. 安装为系统服务

在 Runner 安装目录执行：

```bash
sudo ./svc.sh install github-runner
sudo ./svc.sh start
sudo ./svc.sh status
```

确认 GitHub Runner 页面显示：

```text
Status: Idle 或 Active
Labels:
- self-hosted
- Linux
- X64
- tianditu-mainland-egress
```

## 5. 配置仓库变量

在仓库中打开：

```text
Settings
→ Secrets and variables
→ Actions
→ Variables
```

新增两个 Repository variables：

```text
TIANDITU_RUNNER_LABEL=tianditu-mainland-egress
TIANDITU_EXPECTED_EGRESS_IP=<服务器固定公网 IPv4>
```

现有 Repository secret 保持：

```text
TIANDITU_API_KEY=<天地图控制台 Key>
```

公网 IP 不写入 Artifact。预检只记录其 SHA-256，用于证明每次任务使用的是登记出口。

## 6. 天地图控制台配置

若天地图控制台支持 IP 白名单或来源限制，将以下地址加入允许范围：

```text
TIANDITU_EXPECTED_EGRESS_IP 对应的固定公网 IPv4
```

不要配置 `0.0.0.0/0`，不要使用动态住宅代理、公共代理或轮换代理池。

## 7. 生产验证

创建最小只读票据：

```json
{
  "task_id": "tianditu-mainland-egress-smoke",
  "provider": "tianditu",
  "operation": "administrative-search",
  "objective": "验证中国大陆固定公网出口和天地图 API",
  "parameters": {
    "keyword": "小学",
    "specify": "福州市",
    "start": 0,
    "count": 1,
    "show": 1
  },
  "data_policy": {
    "classification": "public",
    "contains_personal_data": false
  },
  "acceptance": {
    "timeout_seconds": 45,
    "max_response_bytes": 1000000
  }
}
```

Issue 标题必须以以下前缀开始：

```text
[api-tianditu]
```

成功标准：

```text
Fixed mainland egress verified: true
Upstream called: true
HTTP status: 200
Business status: 1000
WAF blocked: false
API_TIANDITU_COMPLETED
```

## 8. 故障判定

### 工作流长期 queued

专用 Runner 离线，或 Runner 没有 `tianditu-mainland-egress` 标签。工作流不会回退到 GitHub 托管出口。

### TIANDITU_FIXED_EGRESS_REJECTED

可能原因：

```text
TIANDITU_EXPECTED_EGRESS_IP 未配置
实际公网 IP 与登记 IP 不一致
Runner 不是 self-hosted
Runner 不是 Linux x64
公网 IP 检测端点均不可达
```

### TIANDITU_WAF_BLOCKED

固定大陆出口仍被天地图拦截。检查天地图控制台白名单、Key 权限、服务器 EIP 是否已变更，并携带 Artifact 中的 HTTP/WAF 证据联系天地图支持。

## 安全边界

- 该 Runner 只服务天地图专用标签，不承载普通 PR 或任意代码工作流。
- 仓库是公开仓库，因此不得给来自 fork、pull_request 或非仓库所有者的事件分配此 Runner。
- 不保存天地图 Key、GitHub 注册令牌或原始公网 IP。
- 禁止任意代理 URL、动态代理、请求头注入和任意 Shell 参数。
- 服务器应及时安装安全更新，并限制 SSH 来源。
