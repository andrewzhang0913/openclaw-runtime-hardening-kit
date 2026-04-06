# Quickstart

## 1. Requirements

- Python 3.10+
- a local OpenClaw source tree with `dist/`
- a reachable gateway health endpoint

## 2. Run the doctor

macOS + launchd:

```bash
python3 scripts/openclaw_gateway_doctor.py \
  --source-root ~/OpenClaw \
  --service-manager launchd \
  --launchd-label ai.openclaw.gateway
```

Linux + systemd:

```bash
python3 scripts/openclaw_gateway_doctor.py \
  --source-root ~/OpenClaw \
  --service-manager systemd \
  --systemd-unit openclaw-gateway.service
```

## 3. Run security sync as a dry-run

```bash
python3 scripts/openclaw_gateway_security_sync.py \
  --config ~/.openclaw/openclaw.json
```

## 4. Run the combined verify entrypoint

```bash
python3 scripts/openclaw_runtime_verify.py \
  --source-root ~/OpenClaw \
  --service-manager launchd \
  --launchd-label ai.openclaw.gateway
```

## 5. Apply only after review

For any write action:

1. inspect the JSON diff
2. confirm the target path
3. only then use `--apply`

