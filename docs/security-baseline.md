# Security Baseline

Recommended baseline for a local OpenClaw gateway:

1. generate explicit `allowedOrigins`
2. set `dangerouslyAllowHostHeaderOriginFallback=false`
3. set `dangerouslyDisableDeviceAuth=false`
4. keep a rate limit block in `gateway.auth.rateLimit`
5. keep secrets outside the main config file when possible
6. tighten runtime credential directory permissions

## Notes

- `allowInsecureAuth=true` may still be needed for localhost-only HTTP control-ui setups.
- Do not disable it blindly unless you already moved to a safer browser context.

## Verify after changes

```bash
python3 scripts/openclaw_gateway_security_sync.py --config ~/.openclaw/openclaw.json
python3 scripts/openclaw_runtime_verify.py --source-root ~/OpenClaw
```

