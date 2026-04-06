# openclaw-runtime-hardening-kit

External maintenance tooling for keeping a local OpenClaw runtime explainable, recoverable, and easier to upgrade.

[中文说明](README_CN.md)

## Why this exists

Local OpenClaw deployments often fail in a predictable way:

- the gateway process is still running, but it is serving stale build artifacts
- the control UI keeps working just enough to look healthy while configuration drift is already present
- service environment changes are applied incorrectly after upgrades
- operators end up relying on scattered notes instead of a repeatable verification chain

This repository extracts a small, reusable hardening layer around OpenClaw so those problems can be checked and corrected with explicit scripts and docs.

## What this repo does

Current scope:

- detect gateway build/runtime drift
- sync a safer Control UI baseline
- provide a small runtime verification entrypoint
- document `launchd` and `systemd` operator patterns
- provide env/config examples that can live outside private lab setups

## What this repo does not do

This repository is intentionally not a dump of one private lab.

Non-goals:

- personal memory systems
- multi-agent identity contracts
- Discord bot automation
- private notification chains
- family network routing or proxy governance
- HomeNet private data, journals, black-box logs, or secrets

See [docs/non-goals.md](docs/non-goals.md) and [docs/boundary.md](docs/boundary.md).

## Repository layout

```text
.
├── docs/
│   ├── quickstart.md
│   ├── boundary.md
│   ├── non-goals.md
│   ├── launchd.md
│   ├── systemd.md
│   ├── security-baseline.md
│   └── upgrade-checklist.md
├── examples/
├── scripts/
│   ├── openclaw_gateway_doctor.py
│   ├── openclaw_gateway_security_sync.py
│   └── openclaw_runtime_verify.py
└── templates/
```

## Core scripts

### `openclaw_gateway_doctor.py`

Checks whether the currently running gateway process is older than the current `dist/` build output.

It can also compare service metadata such as `OPENCLAW_SERVICE_VERSION` against `dist/build-info.json`.

Typical use:

```bash
python3 scripts/openclaw_gateway_doctor.py \
  --source-root ~/OpenClaw \
  --service-manager launchd \
  --launchd-label ai.openclaw.gateway
```

### `openclaw_gateway_security_sync.py`

Builds a safer `gateway.controlUi` baseline by:

- generating explicit `allowedOrigins`
- forcing dangerous fallback flags off
- ensuring a `gateway.auth.rateLimit` block exists
- optionally tightening credentials directory permissions on apply

Dry-run example:

```bash
python3 scripts/openclaw_gateway_security_sync.py \
  --config ~/.openclaw/openclaw.json
```

### `openclaw_runtime_verify.py`

Runs a small verification chain around:

- gateway health
- gateway doctor
- optional extra audit command

Example:

```bash
python3 scripts/openclaw_runtime_verify.py \
  --source-root ~/OpenClaw \
  --service-manager launchd \
  --launchd-label ai.openclaw.gateway
```

## Quick start

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

## Operating model

The design principle of this repository is:

1. keep the hardening layer outside OpenClaw core
2. prefer scripts, wrappers, docs, and examples over private patch piles
3. make every important action verifiable
4. keep paths parameterized
5. keep secrets out of the repo

## Current status

Current draft status:

- public repository scaffold is live
- validated on macOS + `launchd`
- docs include a baseline for Linux + `systemd`
- more external testing is still needed before calling this production-ready

## Suggested next steps

If you are evaluating this repository, the best next move is:

1. test it against a non-HomeNet OpenClaw layout
2. verify the service manager assumptions on your machine
3. adapt the examples to your own config paths
4. only then use `--apply`

## Related docs

- [docs/quickstart.md](docs/quickstart.md)
- [docs/security-baseline.md](docs/security-baseline.md)
- [docs/upgrade-checklist.md](docs/upgrade-checklist.md)
- [docs/launchd.md](docs/launchd.md)
- [docs/systemd.md](docs/systemd.md)
- [docs/design-notes/runtime-hardening-origin.md](docs/design-notes/runtime-hardening-origin.md)

