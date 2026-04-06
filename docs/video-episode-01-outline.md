# Video Episode 01 Outline

Related file:

- `video-episode-01-script-zh.md`

## Working title

From Private Lab to Public Tooling: Hardening a Local OpenClaw Runtime

## Audience

- OpenClaw local operators
- AI tinkerers running private desktop gateways
- developers who want a maintainable hardening layer outside core code

## Core message

This video is not about building a giant private lab.

It is about taking one narrow, high-value slice from a private lab and turning it into a small public repository that other operators can actually reuse.

## Episode structure

### 1. Hook

Suggested opening:

"Your OpenClaw gateway can look alive while still serving the wrong build. That is the kind of operator problem this repo was built to solve."

### 2. Problem statement

Show three concrete maintenance failures:

1. gateway process is alive, but build drift already happened
2. Control UI works, but config drift is accumulating
3. upgrade notes exist only in logs, not in reusable tooling

### 3. Why not open-source the whole private lab

Explain the boundary:

- a private lab contains too much personal structure
- public users do not need journals, memory systems, or personal routing rules
- the reusable layer is the external hardening layer

### 4. What the repo contains

Walk through:

- `openclaw_gateway_doctor.py`
- `openclaw_gateway_security_sync.py`
- `openclaw_runtime_verify.py`
- `docs/`
- `examples/`

### 5. Demo flow

Recommended live demo sequence:

1. run `openclaw_gateway_doctor.py`
2. explain drift detection output
3. run `openclaw_gateway_security_sync.py` in dry-run mode
4. run `openclaw_runtime_verify.py`
5. show the repo structure and docs

### 6. Engineering principles

Key points to say explicitly:

1. keep hardening outside core code when possible
2. keep paths parameterized
3. keep secrets out of the repo
4. make every important operator action verifiable

### 7. What this repo does not do

Say this clearly in the video:

- it is not a memory system
- it is not a full HomeNet release
- it is not a Discord automation pack
- it is not an official OpenClaw replacement

### 8. Closing

Suggested close:

"If you are running OpenClaw locally, you do not need a giant private framework. You need a small layer that helps you see drift, verify changes, and recover cleanly. That is what this repository is for."

## Suggested visuals

1. local gateway health terminal
2. doctor JSON output
3. security sync dry-run diff
4. repo tree on GitHub
5. README and release notes

## Suggested recording length

- short version: 6 to 8 minutes
- fuller version: 10 to 14 minutes

## Suggested follow-up episodes

1. how to validate a local gateway upgrade safely
2. when to keep logic outside OpenClaw core
3. how to extract a public tool from a private AI lab without leaking private structure
