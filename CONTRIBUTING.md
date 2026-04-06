# Contributing

This repository is intended to stay small, explicit, and operations-focused.

## Rules

1. Keep scripts parameterized. Do not hardcode personal paths.
2. Prefer Python standard library. Avoid new dependencies unless they remove real operator pain.
3. Every behavior change should include a verification command in docs.
4. Do not mix personal memory, notification, or private network logic into this repo.
5. If a feature is specific to one environment, document it as an example instead of making it a default.

## Pull request checklist

1. Explain the operator problem being solved.
2. State the platform scope: `launchd`, `systemd`, or both.
3. Include a dry-run or verification example.
4. Confirm no secrets, tokens, or personal paths are present.

