# openclaw-runtime-hardening-kit

一套面向本地 OpenClaw runtime 的外置维护工具，用来让运行状态更容易解释、回退和升级。

[English README](README.md)

## 这个项目是做什么的

很多本地 OpenClaw 部署的痛点其实很相似：

- gateway 进程还活着，但实际已经跑在旧的构建产物上
- Control UI 看起来还能用，但配置漂移已经发生
- 升级后 service env 重载方式容易搞错
- 维护经验散落在工程日志里，缺少可重复执行的验证链

这个仓库的目的，就是把这些“本机硬化层”抽成一套小而明确的外置脚本和文档，而不是把逻辑继续塞回私有实验室笔记里。

## 当前功能范围

- 检查 gateway 构建物与运行进程是否漂移
- 同步更安全的 Control UI 配置基线
- 提供一个最小 runtime verify 入口
- 提供 `launchd` / `systemd` 的运维说明
- 提供 env/config 示例模板

## 明确不做的内容

这个仓库不是 HomeNet 私有实验室的镜像，因此不会包含：

- 个人记忆系统
- 多智能体身份合同
- Discord bot 自动化
- 私人通知链
- 家庭网络路由或代理治理
- HomeNet 私有数据、日记、黑匣子和 secret

详见：

- [docs/non-goals.md](docs/non-goals.md)
- [docs/boundary.md](docs/boundary.md)

## 仓库结构

```text
.
├── docs/
├── examples/
├── scripts/
└── templates/
```

## 核心脚本

### `openclaw_gateway_doctor.py`

用于检查当前运行中的 gateway 进程，是否早于当前 `dist/` 构建产物。

它还可以比对 service 元数据，例如 `OPENCLAW_SERVICE_VERSION` 是否和 `dist/build-info.json` 一致。

示例：

```bash
python3 scripts/openclaw_gateway_doctor.py \
  --source-root ~/OpenClaw \
  --service-manager launchd \
  --launchd-label ai.openclaw.gateway
```

### `openclaw_gateway_security_sync.py`

用于同步更安全的 `gateway.controlUi` 基线，包括：

- 生成明确的 `allowedOrigins`
- 关闭危险 fallback 开关
- 确保 `gateway.auth.rateLimit` 存在
- 在 apply 时可同步收紧 credentials 目录权限

dry-run 示例：

```bash
python3 scripts/openclaw_gateway_security_sync.py \
  --config ~/.openclaw/openclaw.json
```

### `openclaw_runtime_verify.py`

用于执行一个小型验证链，覆盖：

- gateway health
- gateway doctor
- 可选的额外审计命令

示例：

```bash
python3 scripts/openclaw_runtime_verify.py \
  --source-root ~/OpenClaw \
  --service-manager launchd \
  --launchd-label ai.openclaw.gateway
```

## 快速开始

### macOS + launchd

```bash
python3 scripts/openclaw_gateway_doctor.py \
  --source-root ~/OpenClaw \
  --service-manager launchd \
  --launchd-label ai.openclaw.gateway

python3 scripts/openclaw_gateway_security_sync.py \
  --config ~/.openclaw/openclaw.json

python3 scripts/openclaw_runtime_verify.py \
  --source-root ~/OpenClaw \
  --service-manager launchd \
  --launchd-label ai.openclaw.gateway
```

### Linux + systemd

```bash
python3 scripts/openclaw_gateway_doctor.py \
  --source-root ~/OpenClaw \
  --service-manager systemd \
  --systemd-unit openclaw-gateway.service
```

## 设计原则

这个仓库遵守以下原则：

1. 硬化层尽量放在 OpenClaw core 之外
2. 优先使用脚本、wrapper、文档和示例
3. 每个关键动作都应该能验证
4. 路径必须参数化
5. secret 不进仓库

## 当前状态

当前是第一版公开骨架：

- 公共仓已建立
- 已在 macOS + `launchd` 下完成验证
- 已提供 Linux + `systemd` 的文档基线
- 在宣称 production-ready 之前，还需要更多外部环境验证

## 建议下一步

如果你要试用这个项目，顺序建议是：

1. 先在非 HomeNet 目录结构下测试
2. 确认你本机的 service manager 假设成立
3. 按自己的路径改 example
4. 最后才使用 `--apply`

## 相关文档

- [docs/quickstart.md](docs/quickstart.md)
- [docs/security-baseline.md](docs/security-baseline.md)
- [docs/upgrade-checklist.md](docs/upgrade-checklist.md)
- [docs/launchd.md](docs/launchd.md)
- [docs/systemd.md](docs/systemd.md)
- [docs/design-notes/runtime-hardening-origin.md](docs/design-notes/runtime-hardening-origin.md)
