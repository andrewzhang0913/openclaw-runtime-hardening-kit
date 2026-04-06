# launchd

## Typical usage

Use `launchd` when OpenClaw runs as a user service on macOS.

Common label example:

```text
ai.openclaw.gateway
```

## Verify state

```bash
launchctl print gui/$(id -u)/ai.openclaw.gateway
curl --noproxy '*' http://127.0.0.1:18789/health
python3 scripts/openclaw_gateway_doctor.py \
  --source-root ~/OpenClaw \
  --service-manager launchd \
  --launchd-label ai.openclaw.gateway
```

## Important note

If you changed `EnvironmentVariables` in the plist, `kickstart -k` is usually not enough.

Use:

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/ai.openclaw.gateway.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ai.openclaw.gateway.plist
```

