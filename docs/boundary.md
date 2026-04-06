# Boundary

This repository is an external hardening layer around OpenClaw.

## It is for

- local operator maintenance
- upgrade regression checks
- safer control-ui baseline sync
- macOS `launchd` and Linux `systemd` examples

## It is not for

- replacing OpenClaw core
- becoming a private runtime state dump
- shipping user-specific secrets or machine-specific paths
- carrying personal memory systems

## Design boundary

1. Keep logic outside OpenClaw core whenever possible.
2. Prefer wrappers, scripts, docs, and examples.
3. Make paths configurable.
4. Make every important action verifiable.

