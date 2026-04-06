# Upgrade Checklist

Run this after rebuilding or upgrading OpenClaw:

1. confirm `dist/build-info.json` exists
2. check the gateway health endpoint
3. run `openclaw_gateway_doctor.py`
4. if config changed, run `openclaw_gateway_security_sync.py` in dry-run mode
5. if you changed service env, reload the supervisor correctly
6. only then restart
7. run the full verify entrypoint

Suggested command chain:

```bash
curl --noproxy '*' http://127.0.0.1:18789/health
python3 scripts/openclaw_gateway_doctor.py --source-root ~/OpenClaw
python3 scripts/openclaw_gateway_security_sync.py --config ~/.openclaw/openclaw.json
python3 scripts/openclaw_runtime_verify.py --source-root ~/OpenClaw
```

