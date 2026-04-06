# systemd

## Typical usage

Use `systemd --user` when OpenClaw runs as a user service on Linux.

Common unit example:

```text
openclaw-gateway.service
```

## Verify state

```bash
systemctl --user status openclaw-gateway.service
curl http://127.0.0.1:18789/health
python3 scripts/openclaw_gateway_doctor.py \
  --source-root ~/OpenClaw \
  --service-manager systemd \
  --systemd-unit openclaw-gateway.service
```

## Environment updates

If environment files changed, reload user units before restart:

```bash
systemctl --user daemon-reload
systemctl --user restart openclaw-gateway.service
```

Treat this document as an operator baseline. Validate it on your own layout before calling it production-ready.

