import json
import os
from pathlib import Path
from cryptography.fernet import Fernet

CONFIG_DIR = Path.home() / ".scptool"
CONFIG_FILE = CONFIG_DIR / "servers.json"
KEY_FILE = CONFIG_DIR / ".key"


def _ensure_config_dir():
    CONFIG_DIR.mkdir(exist_ok=True)
    if os.name == "nt":
        # Windows: make directory accessible only to current user
        import subprocess
        subprocess.run(
            ["icacls", str(CONFIG_DIR), "/inheritance:r",
             "/grant:r", f"{os.getlogin()}:(OI)(CI)F"],
            capture_output=True,
        )
    else:
        CONFIG_DIR.chmod(0o700)


def _get_key() -> bytes:
    _ensure_config_dir()
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()
    key = Fernet.generate_key()
    KEY_FILE.write_bytes(key)
    _lock_file(KEY_FILE)
    return key


def _lock_file(path: Path):
    """Restrict file permissions to current user only."""
    if os.name == "nt":
        import subprocess
        subprocess.run(
            ["icacls", str(path), "/inheritance:r",
             "/grant:r", f"{os.getlogin()}:F"],
            capture_output=True,
        )
    else:
        path.chmod(0o600)


def _cipher() -> Fernet:
    return Fernet(_get_key())


def encrypt(value: str) -> str:
    return _cipher().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    return _cipher().decrypt(value.encode()).decode()


def load_servers() -> list[dict]:
    _ensure_config_dir()
    if not CONFIG_FILE.exists():
        return []
    data = json.loads(CONFIG_FILE.read_text())
    return data


def save_servers(servers: list[dict]):
    _ensure_config_dir()
    CONFIG_FILE.write_text(json.dumps(servers, indent=2))
    _lock_file(CONFIG_FILE)
