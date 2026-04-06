# Release Notes - v0.1.0

## Summary

`v0.1.0` is the first public cut of `openclaw-runtime-hardening-kit`.

This release turns a private HomeNet maintenance extraction into a standalone public repository with:

- a reusable gateway drift doctor
- a safer Control UI baseline sync helper
- a small runtime verification entrypoint
- launchd/systemd operator docs
- examples and templates for env/config-driven setups

## What is included

### Scripts

- `scripts/openclaw_gateway_doctor.py`
- `scripts/openclaw_gateway_security_sync.py`
- `scripts/openclaw_runtime_verify.py`

### Docs

- quickstart
- launchd notes
- systemd notes
- security baseline
- upgrade checklist
- boundary and non-goals

### Examples and templates

- `openclaw.json` patch example
- env examples for launchd/systemd/general use
- service template fragments

## Why this release matters

This release is useful if you run OpenClaw locally and want a cleaner external maintenance layer without pushing private operator logic back into OpenClaw core.

It is especially aimed at operators who need:

- a clear explanation of whether a running gateway is actually serving the current build
- a repeatable way to sync safer Control UI defaults
- a small verification chain after upgrades or rebuilds

## Platform status

Current validation:

- macOS + launchd: validated
- Linux + systemd: documented baseline, more live validation still needed

## Known limits

- this is still an early release
- the repo does not attempt to cover every OpenClaw deployment shape
- systemd paths and unit conventions may still need adaptation per environment
- some security decisions, such as `allowInsecureAuth`, still depend on each operator's local context

## Explicit non-goals

`v0.1.0` does not include:

- memory systems
- multi-agent identity contracts
- Discord bot automation
- private black-box protocols
- personal HomeNet topology or secrets

## Suggested next steps after v0.1.0

1. validate on a non-HomeNet macOS setup
2. validate on a real Linux + systemd setup
3. add a small test/fixture layer
4. refine docs based on first outside users

