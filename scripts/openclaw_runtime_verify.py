#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_GATEWAY_URL = "http://127.0.0.1:18789/health"


def now_local() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def fetch_health(url: str) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            body = response.read().decode("utf-8", errors="ignore")
            return {"ok": '"ok":true' in body, "statusCode": response.status, "body": body}
    except Exception as exc:
        return {"ok": False, "statusCode": None, "body": "", "error": str(exc)}


def run_json_command(args: list[str]) -> dict[str, Any]:
    completed = subprocess.run(args, check=False, text=True, capture_output=True)
    output = (completed.stdout or completed.stderr or "").strip()
    payload: dict[str, Any]
    try:
        payload = json.loads(output) if output else {}
    except json.JSONDecodeError:
        payload = {"rawOutput": output}
    payload.setdefault("returncode", completed.returncode)
    return payload


def run_optional_command(command: str) -> dict[str, Any]:
    args = shlex.split(command)
    completed = subprocess.run(args, check=False, text=True, capture_output=True)
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": (completed.stdout or "").strip(),
        "stderr": (completed.stderr or "").strip(),
        "ok": completed.returncode == 0,
    }


def main() -> int:
    script_root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Run a small OpenClaw runtime verification chain")
    parser.add_argument("--source-root", default="~/OpenClaw", help="OpenClaw source root for the doctor")
    parser.add_argument("--gateway-url", default=DEFAULT_GATEWAY_URL, help="Gateway health URL")
    parser.add_argument(
        "--service-manager",
        choices=["launchd", "systemd"],
        default="launchd" if sys.platform == "darwin" else "systemd",
        help="Supervisor used by the gateway service",
    )
    parser.add_argument("--launchd-label", default="ai.openclaw.gateway", help="launchd label for the doctor")
    parser.add_argument("--systemd-unit", default="openclaw-gateway.service", help="systemd unit for the doctor")
    parser.add_argument("--skip-doctor", action="store_true", help="Skip the doctor subprocess")
    parser.add_argument(
        "--security-audit-command",
        help="Optional command to run after doctor, for example 'openclaw security audit'",
    )
    args = parser.parse_args()

    health = fetch_health(args.gateway_url)
    doctor_payload: dict[str, Any] = {}
    if not args.skip_doctor:
        doctor_args = [
            sys.executable,
            str(script_root / "openclaw_gateway_doctor.py"),
            "--source-root",
            args.source_root,
            "--gateway-url",
            args.gateway_url,
            "--service-manager",
            args.service_manager,
            "--launchd-label",
            args.launchd_label,
            "--systemd-unit",
            args.systemd_unit,
        ]
        doctor_payload = run_json_command(doctor_args)

    security_payload: dict[str, Any] = {}
    if args.security_audit_command:
        security_payload = run_optional_command(args.security_audit_command)

    overall = "PASS"
    reasons: list[str] = []
    if not health.get("ok"):
        overall = "FAIL"
        reasons.append("gateway health check failed")
    doctor_status = str(doctor_payload.get("status") or "").upper()
    if doctor_status == "FAIL":
        overall = "FAIL"
        reasons.append("gateway doctor reported FAIL")
    elif doctor_status == "WARN" and overall == "PASS":
        overall = "WARN"
        reasons.append("gateway doctor reported WARN")
    if security_payload and not security_payload.get("ok", False):
        overall = "FAIL"
        reasons.append("security audit command failed")
    if not reasons:
        reasons.append("health and verification chain look good")

    payload = {
        "kind": "openclaw-runtime-verify",
        "checkedAt": now_local(),
        "status": overall,
        "reasons": reasons,
        "health": health,
        "doctor": doctor_payload,
        "securityAudit": security_payload,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if overall == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
