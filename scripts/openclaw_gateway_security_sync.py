#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import shutil
import socket
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path("~/.openclaw/openclaw.json").expanduser()
DEFAULT_CREDENTIALS_DIR = Path("~/.openclaw/credentials").expanduser()
DEFAULT_PORT = 18789
DEFAULT_PATH = "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
DEFAULT_RATE_LIMIT = {
    "maxAttempts": 10,
    "windowMs": 60_000,
    "lockoutMs": 300_000,
}
RFC1918_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
]


def now_local() -> datetime:
    return datetime.now().astimezone()


def run_command(args: list[str]) -> str:
    env = dict(os.environ)
    env.setdefault("HOME", str(Path.home()))
    env.setdefault("PATH", DEFAULT_PATH)
    try:
        completed = subprocess.run(args, check=False, text=True, capture_output=True, env=env)
    except FileNotFoundError:
        return ""
    return ((completed.stdout or "") + (completed.stderr or "")).strip()


def collect_hostnames(extra_hostnames: list[str]) -> list[str]:
    hostnames = {
        "localhost",
        socket.gethostname().strip(),
        socket.getfqdn().strip(),
    }
    for value in extra_hostnames:
        value = value.strip()
        if value:
            hostnames.add(value)
    cleaned: list[str] = []
    for name in sorted(hostnames):
        if not name or name == "localhost.localdomain":
            continue
        lowered = name.lower()
        if lowered.endswith(".ip6.arpa") or lowered.endswith(".in-addr.arpa"):
            continue
        try:
            ipaddress.ip_address(name)
            continue
        except ValueError:
            pass
        cleaned.append(name)
    return cleaned


def collect_ipv4_addresses() -> list[str]:
    ips: set[str] = set()

    for hostname in {socket.gethostname().strip(), socket.getfqdn().strip()}:
        if not hostname:
            continue
        try:
            for item in socket.getaddrinfo(hostname, None, socket.AF_INET, 0, socket.IPPROTO_TCP):
                ip = item[4][0]
                _maybe_add_private_ip(ip, ips)
        except socket.gaierror:
            continue

    for args in (["hostname", "-I"], ["ip", "-4", "addr"], ["ifconfig"]):
        output = run_command(args)
        for match in re.finditer(r"\b([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)\b", output):
            _maybe_add_private_ip(match.group(1), ips)

    return sorted(ips)


def _maybe_add_private_ip(ip: str, bucket: set[str]) -> None:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return
    if addr.is_loopback:
        return
    if isinstance(addr, ipaddress.IPv4Address):
        last_octet = int(ip.split(".")[-1])
        if last_octet in {0, 255}:
            return
    if any(addr in network for network in RFC1918_NETWORKS):
        bucket.add(ip)


def desired_allowed_origins(port: int, extra_hostnames: list[str], extra_origins: list[str]) -> list[str]:
    origins = {
        f"http://localhost:{port}",
        f"http://127.0.0.1:{port}",
    }
    for hostname in collect_hostnames(extra_hostnames):
        origins.add(f"http://{hostname}:{port}")
    for ip in collect_ipv4_addresses():
        origins.add(f"http://{ip}:{port}")
    for origin in extra_origins:
        origin = origin.strip()
        if origin:
            origins.add(origin)
    return sorted(origins)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def chmod_mode(path: Path) -> str:
    return oct(path.stat().st_mode & 0o777)


def build_updated_config(
    config: dict[str, Any],
    preserve_insecure_auth: bool,
    extra_hostnames: list[str],
    extra_origins: list[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    gateway = dict(config.get("gateway") or {})
    control_ui = dict(gateway.get("controlUi") or {})
    auth = dict(gateway.get("auth") or {})

    port = gateway.get("port")
    if not isinstance(port, int) or port <= 0:
        port = DEFAULT_PORT

    before = {
        "allowedOrigins": list(control_ui.get("allowedOrigins") or []),
        "dangerouslyAllowHostHeaderOriginFallback": control_ui.get("dangerouslyAllowHostHeaderOriginFallback"),
        "dangerouslyDisableDeviceAuth": control_ui.get("dangerouslyDisableDeviceAuth"),
        "allowInsecureAuth": control_ui.get("allowInsecureAuth"),
        "rateLimit": auth.get("rateLimit"),
    }

    control_ui["allowedOrigins"] = desired_allowed_origins(port, extra_hostnames, extra_origins)
    control_ui["dangerouslyAllowHostHeaderOriginFallback"] = False
    control_ui["dangerouslyDisableDeviceAuth"] = False
    if not preserve_insecure_auth:
        control_ui["allowInsecureAuth"] = False
    elif "allowInsecureAuth" not in control_ui:
        control_ui["allowInsecureAuth"] = True

    if not isinstance(auth.get("rateLimit"), dict):
        auth["rateLimit"] = dict(DEFAULT_RATE_LIMIT)

    gateway["controlUi"] = control_ui
    gateway["auth"] = auth

    updated = dict(config)
    updated["gateway"] = gateway

    after = {
        "allowedOrigins": list(control_ui.get("allowedOrigins") or []),
        "dangerouslyAllowHostHeaderOriginFallback": control_ui.get("dangerouslyAllowHostHeaderOriginFallback"),
        "dangerouslyDisableDeviceAuth": control_ui.get("dangerouslyDisableDeviceAuth"),
        "allowInsecureAuth": control_ui.get("allowInsecureAuth"),
        "rateLimit": auth.get("rateLimit"),
    }
    return updated, {"before": before, "after": after}


def write_config(path: Path, payload: dict[str, Any]) -> Path:
    stamp = now_local().strftime("%Y%m%d-%H%M%S")
    backup_path = path.with_name(f"{path.name}.security-sync.{stamp}.bak")
    shutil.copy2(path, backup_path)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return backup_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync safer OpenClaw gateway Control UI config")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to openclaw.json")
    parser.add_argument(
        "--credentials-dir",
        default=str(DEFAULT_CREDENTIALS_DIR),
        help="Credentials directory to chmod 700 when applying",
    )
    parser.add_argument(
        "--disable-insecure-auth",
        action="store_true",
        help="Also disable gateway.controlUi.allowInsecureAuth",
    )
    parser.add_argument("--extra-hostname", action="append", default=[], help="Additional hostname to include")
    parser.add_argument("--extra-origin", action="append", default=[], help="Additional origin to include as-is")
    parser.add_argument("--apply", action="store_true", help="Write changes and chmod credentials dir")
    args = parser.parse_args()

    config_path = Path(args.config).expanduser()
    credentials_dir = Path(args.credentials_dir).expanduser()
    config = load_json(config_path)
    updated, diff = build_updated_config(
        config,
        preserve_insecure_auth=not args.disable_insecure_auth,
        extra_hostnames=list(args.extra_hostname),
        extra_origins=list(args.extra_origin),
    )

    changed = updated != config
    backup_path = ""
    credentials_mode_before = chmod_mode(credentials_dir) if credentials_dir.exists() else ""
    credentials_mode_after = credentials_mode_before
    if args.apply and changed:
        backup_path = str(write_config(config_path, updated))
    if args.apply and credentials_dir.exists():
        os.chmod(credentials_dir, 0o700)
        credentials_mode_after = chmod_mode(credentials_dir)

    payload = {
        "kind": "openclaw-gateway-security-sync",
        "checkedAt": now_local().strftime("%Y-%m-%d %H:%M:%S %Z"),
        "configPath": str(config_path),
        "changed": changed,
        "applied": bool(args.apply),
        "backupPath": backup_path,
        "preservedAllowInsecureAuth": not args.disable_insecure_auth,
        "controlUi": diff,
        "credentialsDir": str(credentials_dir),
        "credentialsModeBefore": credentials_mode_before,
        "credentialsModeAfter": credentials_mode_after,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
