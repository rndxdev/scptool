"""Detect SSH config hosts and available keys from ~/.ssh."""

import os
import re
from pathlib import Path


def detect_ssh_config() -> dict:
    ssh_dir = Path.home() / ".ssh"
    result = {
        "hosts": [],
        "keys": [],
        "ssh_dir": str(ssh_dir),
    }

    if not ssh_dir.is_dir():
        return result

    # --- Find available SSH keys ---
    key_names = [
        "id_rsa", "id_ed25519", "id_ecdsa", "id_dsa", "id_ed25519_sk", "id_ecdsa_sk",
    ]
    for name in key_names:
        key_path = ssh_dir / name
        if key_path.is_file():
            has_pub = (ssh_dir / f"{name}.pub").is_file()
            result["keys"].append({
                "name": name,
                "path": str(key_path),
                "has_pub": has_pub,
                "type": _key_type(name),
            })

    # Also find any custom-named keys (files without extensions that have a .pub pair)
    for f in ssh_dir.iterdir():
        if (
            f.is_file()
            and not f.suffix
            and f.name not in key_names
            and f.name not in ("config", "known_hosts", "authorized_keys", "environment")
            and not f.name.startswith(".")
            and (ssh_dir / f"{f.name}.pub").is_file()
        ):
            result["keys"].append({
                "name": f.name,
                "path": str(f),
                "has_pub": True,
                "type": "custom",
            })

    # --- Parse ~/.ssh/config ---
    config_file = ssh_dir / "config"
    if config_file.is_file():
        result["hosts"] = _parse_ssh_config(config_file, result["keys"])

    return result


def _parse_ssh_config(config_path: Path, available_keys: list[dict]) -> list[dict]:
    """Parse SSH config file into a list of host entries."""
    hosts = []
    current = None

    text = config_path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Match "Key Value" or "Key=Value"
        m = re.match(r"^(\w+)\s*[=\s]\s*(.+)$", line)
        if not m:
            continue

        key = m.group(1).lower()
        value = m.group(2).strip()

        if key == "host":
            # Skip wildcard-only entries
            if "*" in value and value.strip() == "*":
                current = None
                continue
            current = {
                "alias": value,
                "hostname": "",
                "port": 22,
                "user": "",
                "identity_file": "",
            }
            hosts.append(current)
        elif current is not None:
            if key == "hostname":
                current["hostname"] = value
            elif key == "port":
                try:
                    current["port"] = int(value)
                except ValueError:
                    pass
            elif key == "user":
                current["user"] = value
            elif key == "identityfile":
                # Expand ~ to home dir
                expanded = value.replace("~", str(Path.home()))
                current["identity_file"] = expanded

    # For hosts without an explicit identity file, pick the best available key
    default_key = ""
    if available_keys:
        # Prefer ed25519 > ecdsa > rsa
        pref = {"id_ed25519": 0, "id_ecdsa": 1, "id_rsa": 2}
        sorted_keys = sorted(available_keys, key=lambda k: pref.get(k["name"], 99))
        default_key = sorted_keys[0]["path"]

    for h in hosts:
        if not h["identity_file"] and default_key:
            h["identity_file"] = default_key
        # If hostname is missing, use alias
        if not h["hostname"]:
            h["hostname"] = h["alias"]

    return hosts


def _key_type(name: str) -> str:
    if "ed25519" in name:
        return "ed25519"
    if "ecdsa" in name:
        return "ecdsa"
    if "rsa" in name:
        return "rsa"
    if "dsa" in name:
        return "dsa"
    return "unknown"
