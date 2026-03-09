import os
import stat
import paramiko
from pathlib import Path, PurePosixPath


def _connect(server: dict) -> paramiko.SSHClient:
    client = paramiko.SSHClient()

    # Load system known_hosts for host key verification
    known_hosts = Path.home() / ".ssh" / "known_hosts"
    if known_hosts.is_file():
        client.load_host_keys(str(known_hosts))
    # Reject unknown hosts instead of blindly trusting (prevents MITM)
    client.set_missing_host_key_policy(paramiko.RejectPolicy())

    connect_kwargs = {
        "hostname": server["host"],
        "port": server.get("port", 22),
        "username": server["username"],
        "timeout": 10,
    }

    # Prefer key-based auth
    key_path = server.get("key_path", "").strip()
    if key_path and os.path.isfile(key_path):
        passphrase = server.get("key_passphrase") or None
        connect_kwargs["key_filename"] = key_path
        if passphrase:
            connect_kwargs["passphrase"] = passphrase
    elif server.get("password"):
        connect_kwargs["password"] = server["password"]
    else:
        # Fall back to default SSH agent / keys
        connect_kwargs["allow_agent"] = True
        connect_kwargs["look_for_keys"] = True

    client.connect(**connect_kwargs)
    return client


def upload_file(
    server: dict,
    local_path: str,
    remote_dir: str,
    progress_callback=None,
) -> dict:
    """Upload a single file via SFTP (SCP protocol over SSH)."""
    local = Path(local_path)
    if not local.is_file():
        raise FileNotFoundError(f"Local file not found: {local_path}")

    file_size = local.stat().st_size
    remote_path = str(PurePosixPath(remote_dir) / local.name)

    client = _connect(server)
    try:
        sftp = client.open_sftp()
        # Ensure remote directory exists
        _mkdir_p(sftp, remote_dir)

        transferred = [0]

        def _progress(sent, total):
            transferred[0] = sent
            if progress_callback:
                progress_callback(sent, total)

        sftp.put(local_path, remote_path, callback=_progress)
        sftp.close()
    finally:
        client.close()

    return {
        "local_path": local_path,
        "remote_path": remote_path,
        "size": file_size,
        "status": "success",
    }


def test_connection(server: dict) -> dict:
    """Test SSH connection to a server."""
    try:
        client = _connect(server)
        client.close()
        return {"status": "ok", "message": "Connection successful"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def list_remote_dir(server: dict, remote_path: str) -> tuple[str, list[dict]]:
    """List files in a remote directory. Returns (resolved_path, entries)."""
    client = _connect(server)
    try:
        sftp = client.open_sftp()
        # Resolve ~ and relative paths to absolute
        if remote_path in ("~", ".", ""):
            remote_path = sftp.normalize(".")
        elif remote_path.startswith("~/"):
            home = sftp.normalize(".")
            remote_path = home + remote_path[1:]
        else:
            remote_path = sftp.normalize(remote_path)

        entries = []
        for attr in sftp.listdir_attr(remote_path):
            entries.append({
                "name": attr.filename,
                "size": attr.st_size,
                "is_dir": stat.S_ISDIR(attr.st_mode) if attr.st_mode else False,
                "modified": attr.st_mtime,
            })
        sftp.close()
    finally:
        client.close()
    sorted_entries = sorted(entries, key=lambda e: (not e["is_dir"], e["name"].lower()))
    return remote_path, sorted_entries


def _mkdir_p(sftp: paramiko.SFTPClient, remote_dir: str):
    """Recursively create remote directories."""
    dirs_to_create = []
    current = remote_dir
    while True:
        try:
            sftp.stat(current)
            break
        except FileNotFoundError:
            dirs_to_create.append(current)
            parent = str(PurePosixPath(current).parent)
            if parent == current:
                break
            current = parent

    for d in reversed(dirs_to_create):
        try:
            sftp.mkdir(d)
        except OSError:
            pass  # already exists
