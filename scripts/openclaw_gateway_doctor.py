#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_SOURCE_ROOT = Path("~/OpenClaw").expanduser()
DEFAULT_GATEWAY_URL = "http://127.0.0.1:18789/health"
DEFAULT_LAUNCHD_LABEL = "ai.openclaw.gateway"
DEFAULT_SYSTEMD_UNIT = "openclaw-gateway.service"
DEFAULT_PATH = "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
DEFAULT_TIMEOUT_SECONDS = 15
RESTART_WAIT_SECONDS = 60
DRIFT_TOLERANCE_SECONDS = 2
STARTUP_GRACE_SECONDS = 120


@dataclass(frozen=True)
class ServiceSnapshot:
    manager: str
    target: str
    state: str
    pid: int | None
    service_version: str
    process_started_at: datetime | None
    process_started_at_raw: str
    process_started_epoch: float | None


def now_local() -> datetime:
    return datetime.now().astimezone()


def default_service_manager() -> str:
    return "launchd" if platform.system() == "Darwin" else "systemd"


def clean_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")
    return value


def run_command(args: list[str], timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> tuple[int, str]:
    env = dict(os.environ)
    env.setdefault("HOME", str(Path.home()))
    env.setdefault("PATH", DEFAULT_PATH)
    try:
        completed = subprocess.run(
            args,
            check=False,
            text=True,
            capture_output=True,
            env=env,
            timeout=timeout_seconds,
        )
        return completed.returncode, ((completed.stdout or "") + (completed.stderr or "")).strip()
    except subprocess.TimeoutExpired as exc:
        output = (clean_output(exc.stdout) + clean_output(exc.stderr)).strip()
        return -1, f"{output}\nTIMEOUT after {timeout_seconds}s".strip()


def fetch_gateway_health(url: str) -> str:
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            return response.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""


def parse_iso_datetime(raw: str) -> datetime | None:
    text = str(raw).strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).astimezone()
    except ValueError:
        return None


def parse_ps_datetime(raw: str) -> datetime | None:
    text = str(raw).strip()
    if not text:
        return None
    for fmt in ("%a %b %d %H:%M:%S %Y", "%a %b %e %H:%M:%S %Y"):
        try:
            return datetime.strptime(text, fmt).astimezone()
        except ValueError:
            continue
    return None


def read_build_metadata(source_root: Path) -> dict[str, Any]:
    dist_root = source_root / "dist"
    build_info_path = dist_root / "build-info.json"
    index_path = dist_root / "index.js"
    payload: dict[str, Any] = {
        "sourceRoot": str(source_root),
        "distRoot": str(dist_root),
        "buildInfoPath": str(build_info_path),
        "indexPath": str(index_path),
        "version": "",
        "commit": "",
        "builtAt": "",
        "artifactTimestamp": "",
        "artifactEpoch": None,
    }
    build_info: dict[str, Any] = {}
    if build_info_path.exists():
        try:
            build_info = json.loads(build_info_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            build_info = {}
    payload["version"] = str(build_info.get("version") or "").strip()
    payload["commit"] = str(build_info.get("commit") or "").strip()
    payload["builtAt"] = str(build_info.get("builtAt") or "").strip()

    candidates: list[datetime] = []
    built_at_dt = parse_iso_datetime(payload["builtAt"])
    if built_at_dt:
        candidates.append(built_at_dt)
    if index_path.exists():
        candidates.append(datetime.fromtimestamp(index_path.stat().st_mtime).astimezone())
    if candidates:
        artifact_dt = max(candidates)
        payload["artifactTimestamp"] = artifact_dt.isoformat()
        payload["artifactEpoch"] = artifact_dt.timestamp()
    return payload


def read_process_started_at(pid: int | None) -> tuple[datetime | None, str]:
    if pid is None:
        return None, ""
    _, output = run_command(["ps", "-p", str(pid), "-o", "lstart="], timeout_seconds=10)
    return parse_ps_datetime(output), output.strip()


def inspect_launchd_service(label: str, service_version_env: str) -> ServiceSnapshot:
    uid = str(os.getuid())
    target = f"gui/{uid}/{label}"
    returncode, dump = run_command(["launchctl", "print", target], timeout_seconds=10)
    if returncode != 0:
        return ServiceSnapshot("launchd", target, "not-found", None, "", None, "", None)

    state_match = re.search(r"^\s*state = ([^\n]+)$", dump, flags=re.MULTILINE)
    pid_match = re.search(r"^\s*pid = ([0-9]+)$", dump, flags=re.MULTILINE)
    version_match = re.search(rf"{re.escape(service_version_env)} => ([^\n]+)", dump)
    pid = int(pid_match.group(1)) if pid_match else None
    started_at, started_raw = read_process_started_at(pid)
    return ServiceSnapshot(
        manager="launchd",
        target=target,
        state=(state_match.group(1).strip() if state_match else "unknown"),
        pid=pid,
        service_version=(version_match.group(1).strip() if version_match else ""),
        process_started_at=started_at,
        process_started_at_raw=started_raw,
        process_started_epoch=(started_at.timestamp() if started_at else None),
    )


def inspect_systemd_service(unit: str, service_version_env: str) -> ServiceSnapshot:
    returncode, dump = run_command(
        [
            "systemctl",
            "--user",
            "show",
            unit,
            "--property=ActiveState",
            "--property=SubState",
            "--property=MainPID",
            "--property=Environment",
        ],
        timeout_seconds=10,
    )
    if returncode != 0:
        return ServiceSnapshot("systemd", unit, "not-found", None, "", None, "", None)

    properties: dict[str, str] = {}
    for line in dump.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        properties[key.strip()] = value.strip()

    state = properties.get("SubState") or properties.get("ActiveState") or "unknown"
    pid_raw = properties.get("MainPID", "0")
    pid = int(pid_raw) if pid_raw.isdigit() and int(pid_raw) > 0 else None
    env_line = properties.get("Environment", "")
    version_match = re.search(rf"(?:^|\s){re.escape(service_version_env)}=([^\s]+)", env_line)
    started_at, started_raw = read_process_started_at(pid)
    return ServiceSnapshot(
        manager="systemd",
        target=unit,
        state=state,
        pid=pid,
        service_version=(version_match.group(1).strip() if version_match else ""),
        process_started_at=started_at,
        process_started_at_raw=started_raw,
        process_started_epoch=(started_at.timestamp() if started_at else None),
    )


def inspect_service(service_manager: str, launchd_label: str, systemd_unit: str, service_version_env: str) -> ServiceSnapshot:
    if service_manager == "launchd":
        return inspect_launchd_service(launchd_label, service_version_env)
    if service_manager == "systemd":
        return inspect_systemd_service(systemd_unit, service_version_env)
    return ServiceSnapshot(service_manager, "", "unsupported", None, "", None, "", None)


def wait_for_health(url: str, timeout_seconds: int) -> str:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        health = fetch_gateway_health(url)
        if '"ok":true' in health:
            return health
        time.sleep(2)
    return fetch_gateway_health(url)


def restart_service(service_manager: str, snapshot: ServiceSnapshot, gateway_url: str) -> dict[str, Any]:
    if service_manager == "launchd":
        args = ["launchctl", "kickstart", "-k", snapshot.target]
    elif service_manager == "systemd":
        args = ["systemctl", "--user", "restart", snapshot.target]
    else:
        return {
            "attempted": False,
            "target": snapshot.target,
            "returncode": None,
            "output": f"restart unsupported for service manager {service_manager}",
            "healthAfterRestart": "",
            "ok": False,
        }

    returncode, output = run_command(args, timeout_seconds=20)
    health = wait_for_health(gateway_url, RESTART_WAIT_SECONDS) if returncode == 0 else ""
    return {
        "attempted": True,
        "target": snapshot.target,
        "returncode": returncode,
        "output": output,
        "healthAfterRestart": health,
        "ok": returncode == 0 and '"ok":true' in health,
    }


def assess_gateway(
    source_root: Path,
    service_manager: str,
    launchd_label: str,
    systemd_unit: str,
    service_version_env: str,
    gateway_url: str,
    restart_if_drift: bool,
    startup_grace_seconds: int,
) -> dict[str, Any]:
    checked = now_local()
    build = read_build_metadata(source_root)
    snapshot = inspect_service(service_manager, launchd_label, systemd_unit, service_version_env)
    gateway_health = fetch_gateway_health(gateway_url)

    reasons: list[str] = []
    actions: list[str] = []
    status = "PASS"
    drift_detected = False
    restart_result: dict[str, Any] = {
        "attempted": False,
        "target": snapshot.target,
        "returncode": None,
        "output": "",
        "healthAfterRestart": "",
        "ok": False,
    }

    artifact_epoch = build.get("artifactEpoch")
    process_epoch = snapshot.process_started_epoch
    version = str(build.get("version") or "").strip()
    process_age_seconds = None
    if snapshot.process_started_at:
        process_age_seconds = max((checked - snapshot.process_started_at).total_seconds(), 0)

    running_states = {"launchd": {"running"}, "systemd": {"running", "active"}}
    expected_states = running_states.get(service_manager, {"running"})

    if snapshot.state not in expected_states:
        status = "FAIL"
        reasons.append(f"{service_manager} state is {snapshot.state}")
        actions.append("Inspect the service state and restore the gateway process.")
    if snapshot.pid is None:
        status = "FAIL"
        reasons.append("service did not expose a gateway pid")
        actions.append("Inspect service logs and startup configuration.")
    if '"ok":true' not in gateway_health:
        if process_age_seconds is not None and process_age_seconds <= startup_grace_seconds and status == "PASS":
            status = "WARN"
            reasons.append(
                f"gateway health is not live yet, but process is within startup grace ({int(process_age_seconds)}s <= {startup_grace_seconds}s)"
            )
            actions.append("Wait for the current restart to finish before treating health as failed.")
        else:
            status = "FAIL"
            reasons.append("gateway health endpoint is not live")
            actions.append("Check gateway logs and confirm the process can bind the gateway port.")

    if artifact_epoch is not None and process_epoch is not None:
        if process_epoch + DRIFT_TOLERANCE_SECONDS < float(artifact_epoch):
            drift_detected = True
            status = "FAIL"
            reasons.append("gateway process started before current dist artifact timestamp")
            actions.append("Restart the gateway service so the running process reloads the current build.")
    elif artifact_epoch is None:
        if status == "PASS":
            status = "WARN"
        reasons.append("dist build timestamp unavailable")
        actions.append("Ensure dist/build-info.json exists and the build completed cleanly.")
    elif process_epoch is None:
        if status == "PASS":
            status = "WARN"
        reasons.append("unable to parse gateway process start time")

    if snapshot.service_version and version and snapshot.service_version != version:
        if status == "PASS":
            status = "WARN"
        reasons.append(
            f"service {service_version_env}={snapshot.service_version} differs from dist version {version}"
        )
        actions.append("Refresh the service metadata so the service version matches the current build.")

    if restart_if_drift and drift_detected:
        restart_result = restart_service(service_manager, snapshot, gateway_url)
        if restart_result.get("ok"):
            snapshot = inspect_service(service_manager, launchd_label, systemd_unit, service_version_env)
            gateway_health = restart_result.get("healthAfterRestart", "") or fetch_gateway_health(gateway_url)
            if (
                snapshot.process_started_epoch is not None
                and artifact_epoch is not None
                and snapshot.process_started_epoch + DRIFT_TOLERANCE_SECONDS >= float(artifact_epoch)
                and '"ok":true' in gateway_health
            ):
                status = "PASS" if not (snapshot.service_version and version and snapshot.service_version != version) else "WARN"
                drift_detected = False
                reasons.append("restart cleared gateway/dist drift")
            else:
                status = "FAIL"
                reasons.append("restart completed but drift verification still failed")
        else:
            status = "FAIL"
            reasons.append("restart attempt failed")

    if not reasons:
        reasons.append("gateway process matches current dist build")

    return {
        "kind": "openclaw-gateway-doctor",
        "checkedAt": checked.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "status": status,
        "reasons": reasons,
        "actions": actions,
        "gatewayUrl": gateway_url,
        "gatewayHealth": gateway_health,
        "driftDetected": drift_detected,
        "restart": restart_result,
        "service": {
            "manager": snapshot.manager,
            "target": snapshot.target,
            "state": snapshot.state,
            "pid": snapshot.pid,
            "serviceVersion": snapshot.service_version,
        },
        "process": {
            "startedAt": snapshot.process_started_at.isoformat() if snapshot.process_started_at else "",
            "startedAtRaw": snapshot.process_started_at_raw,
            "startedEpoch": snapshot.process_started_epoch,
            "ageSeconds": process_age_seconds,
        },
        "build": build,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="External doctor for OpenClaw gateway build/runtime drift")
    parser.add_argument("--source-root", default=str(DEFAULT_SOURCE_ROOT), help="OpenClaw source root")
    parser.add_argument(
        "--service-manager",
        choices=["launchd", "systemd"],
        default=default_service_manager(),
        help="Supervisor used to run the gateway process",
    )
    parser.add_argument("--launchd-label", default=DEFAULT_LAUNCHD_LABEL, help="launchd label")
    parser.add_argument("--systemd-unit", default=DEFAULT_SYSTEMD_UNIT, help="systemd user unit name")
    parser.add_argument("--service-version-env", default="OPENCLAW_SERVICE_VERSION", help="Service version env key")
    parser.add_argument("--gateway-url", default=DEFAULT_GATEWAY_URL, help="Gateway health URL")
    parser.add_argument(
        "--restart-if-drift",
        action="store_true",
        help="Restart the service when process/build drift is detected",
    )
    parser.add_argument(
        "--startup-grace-seconds",
        type=int,
        default=STARTUP_GRACE_SECONDS,
        help="Grace window during which a fresh process may be WARN instead of FAIL before health is live",
    )
    args = parser.parse_args()

    payload = assess_gateway(
        source_root=Path(args.source_root).expanduser(),
        service_manager=args.service_manager,
        launchd_label=args.launchd_label.strip(),
        systemd_unit=args.systemd_unit.strip(),
        service_version_env=args.service_version_env.strip(),
        gateway_url=args.gateway_url.strip(),
        restart_if_drift=args.restart_if_drift,
        startup_grace_seconds=max(args.startup_grace_seconds, 0),
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if payload.get("status") == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())

