# openclaw-runtime-hardening-kit

Small external tooling for keeping a local OpenClaw runtime explainable, recoverable, and easier to upgrade.

## Scope

This kit focuses on the local hardening layer around OpenClaw. It does not replace official OpenClaw docs or modify OpenClaw core code.

Current draft scope:

- gateway build/runtime drift detection
- control-ui security baseline sync
- upgrade verification commands
- launchd/systemd examples
- env-based secrets examples

## Non-goals

- personal memory systems
- multi-agent identity contracts
- Discord bot automation
- private notification chains
- private HomeNet topology or personal paths

See [docs/non-goals.md](docs/non-goals.md) and [docs/boundary.md](docs/boundary.md).

## Repository layout

```text
.
├── docs/
├── examples/
├── scripts/
└── templates/
```

## Quick start

1. Point the doctor at your OpenClaw source tree.
2. Run it without restart first.
3. Review the JSON result.
4. Only then decide whether to restart the gateway service.

Example:

```bash
python3 scripts/openclaw_gateway_doctor.py \
  --source-root ~/OpenClaw \
  --service-manager launchd \
  --launchd-label ai.openclaw.gateway
```

Security sync dry-run:

```bash
python3 scripts/openclaw_gateway_security_sync.py \
  --config ~/.openclaw/openclaw.json
```

Combined verification:

```bash
python3 scripts/openclaw_runtime_verify.py \
  --source-root ~/OpenClaw \
  --service-manager launchd \
  --launchd-label ai.openclaw.gateway
```

## Status

This is a draft public repo scaffold extracted from a private HomeNet lab.

- verified today on macOS + launchd
- systemd docs are included as a public-facing baseline
- more sanitization and packaging work is still required before a public push

## Next steps

- validate the scripts in a non-HomeNet directory layout
- create the external standalone git repository
- push the first draft release candidate

