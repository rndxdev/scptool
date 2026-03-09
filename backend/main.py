import os
import time
import uuid
import asyncio
import tempfile
import shutil
from pathlib import Path, PurePosixPath
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import load_servers, save_servers, encrypt, decrypt
from transfer import upload_file, test_connection, list_remote_dir
from ssh_detect import detect_ssh_config

# Track upload progress in memory (auto-cleaned after 10 min)
upload_progress: dict[str, dict] = {}

MAX_UPLOAD_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB per request (adjust as needed)
PROGRESS_TTL = 600  # seconds


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Cleanup temp files on shutdown
    pass


app = FastAPI(title="SCP Tool", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    """Reject uploads that exceed MAX_UPLOAD_SIZE before body is fully read."""
    if request.method in ("POST", "PUT"):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_UPLOAD_SIZE:
            return JSONResponse(
                status_code=413,
                content={"detail": f"File too large. Max {MAX_UPLOAD_SIZE // (1024**3)} GB."},
            )
    return await call_next(request)


# --- Models ---

class ServerCreate(BaseModel):
    name: str
    host: str
    port: int = 22
    username: str
    auth_type: str = "key"  # "key" or "password"
    key_path: str = ""
    key_passphrase: str = ""
    password: str = ""
    default_remote_dir: str = "~"


class ServerUpdate(ServerCreate):
    pass


# --- Server CRUD ---

@app.get("/api/servers")
def get_servers():
    servers = load_servers()
    # Strip sensitive fields for listing
    safe = []
    for s in servers:
        safe.append({
            "id": s["id"],
            "name": s["name"],
            "host": s["host"],
            "port": s["port"],
            "username": s["username"],
            "auth_type": s.get("auth_type", "key"),
            "key_path": s.get("key_path", ""),
            "default_remote_dir": s.get("default_remote_dir", "~"),
            "has_password": bool(s.get("password_enc")),
            "has_passphrase": bool(s.get("key_passphrase_enc")),
        })
    return safe


@app.post("/api/servers")
def create_server(server: ServerCreate):
    servers = load_servers()
    entry = {
        "id": str(uuid.uuid4())[:8],
        "name": server.name,
        "host": server.host,
        "port": server.port,
        "username": server.username,
        "auth_type": server.auth_type,
        "key_path": server.key_path,
        "default_remote_dir": server.default_remote_dir,
    }
    if server.password:
        entry["password_enc"] = encrypt(server.password)
    if server.key_passphrase:
        entry["key_passphrase_enc"] = encrypt(server.key_passphrase)
    servers.append(entry)
    save_servers(servers)
    return {"id": entry["id"], "message": "Server added"}


@app.put("/api/servers/{server_id}")
def update_server(server_id: str, server: ServerUpdate):
    servers = load_servers()
    for i, s in enumerate(servers):
        if s["id"] == server_id:
            s["name"] = server.name
            s["host"] = server.host
            s["port"] = server.port
            s["username"] = server.username
            s["auth_type"] = server.auth_type
            s["key_path"] = server.key_path
            s["default_remote_dir"] = server.default_remote_dir
            if server.password:
                s["password_enc"] = encrypt(server.password)
            if server.key_passphrase:
                s["key_passphrase_enc"] = encrypt(server.key_passphrase)
            servers[i] = s
            save_servers(servers)
            return {"message": "Server updated"}
    raise HTTPException(404, "Server not found")


@app.delete("/api/servers/{server_id}")
def delete_server(server_id: str):
    servers = load_servers()
    servers = [s for s in servers if s["id"] != server_id]
    save_servers(servers)
    return {"message": "Server deleted"}


# --- SSH Auto-Detection ---

@app.get("/api/ssh/detect")
def detect_ssh():
    """Scan ~/.ssh for config entries and available keys."""
    return detect_ssh_config()


# --- Connection Test ---

@app.post("/api/servers/{server_id}/test")
def test_server_connection(server_id: str):
    server = _get_server(server_id)
    result = test_connection(server)
    return result


# --- File Upload ---

@app.post("/api/upload")
async def upload_files(
    server_id: str = Form(...),
    remote_dir: str = Form(...),
    files: list[UploadFile] = File(...),
):
    server = _get_server(server_id)
    transfer_id = str(uuid.uuid4())[:8]
    results = []

    upload_progress[transfer_id] = {
        "total_files": len(files),
        "completed": 0,
        "current_file": "",
        "status": "uploading",
        "results": [],
        "_created": time.time(),
    }

    # Clean up stale progress entries
    _cleanup_progress()

    tmp_dir = tempfile.mkdtemp(prefix="scptool_")
    try:
        for f in files:
            # Sanitize filename — strip path components to prevent traversal
            safe_name = PurePosixPath(f.filename).name
            safe_name = Path(safe_name).name  # also handle backslash paths
            if not safe_name or safe_name in (".", ".."):
                results.append({
                    "local_path": f.filename,
                    "status": "error",
                    "error": "Invalid filename",
                })
                continue

            upload_progress[transfer_id]["current_file"] = safe_name

            # Save to temp file — stream in chunks to avoid buffering huge files
            tmp_path = os.path.join(tmp_dir, safe_name)
            size = 0
            too_large = False
            with open(tmp_path, "wb") as out:
                while chunk := await f.read(8 * 1024 * 1024):  # 8 MB chunks
                    size += len(chunk)
                    if size > MAX_UPLOAD_SIZE:
                        too_large = True
                        break
                    out.write(chunk)

            if too_large:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                # Drain remaining data so connection doesn't hang
                while await f.read(1024 * 1024):
                    pass
                results.append({
                    "local_path": safe_name,
                    "status": "error",
                    "error": f"File exceeds {MAX_UPLOAD_SIZE // (1024**3)} GB limit",
                })
                continue

            # Upload via SFTP
            try:
                result = await asyncio.to_thread(
                    upload_file, server, tmp_path, remote_dir
                )
                results.append(result)
            except Exception as e:
                results.append({
                    "local_path": f.filename,
                    "status": "error",
                    "error": str(e),
                })

            upload_progress[transfer_id]["completed"] += 1
            upload_progress[transfer_id]["results"] = results
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    upload_progress[transfer_id]["status"] = "done"
    return {"transfer_id": transfer_id, "results": results}


@app.get("/api/upload/{transfer_id}/progress")
def get_upload_progress(transfer_id: str):
    if transfer_id not in upload_progress:
        raise HTTPException(404, "Transfer not found")
    return upload_progress[transfer_id]


# --- Remote Directory Browsing ---

@app.get("/api/servers/{server_id}/browse")
def browse_remote(server_id: str, path: str = "~"):
    server = _get_server(server_id)
    try:
        resolved_path, entries = list_remote_dir(server, path)
        return {"path": resolved_path, "entries": entries}
    except Exception as e:
        raise HTTPException(400, str(e))


# --- Helpers ---

def _cleanup_progress():
    """Remove progress entries older than PROGRESS_TTL."""
    now = time.time()
    stale = [k for k, v in upload_progress.items()
             if now - v.get("_created", 0) > PROGRESS_TTL]
    for k in stale:
        del upload_progress[k]


def _get_server(server_id: str) -> dict:
    servers = load_servers()
    for s in servers:
        if s["id"] == server_id:
            # Decrypt sensitive fields
            result = dict(s)
            if "password_enc" in result:
                result["password"] = decrypt(result.pop("password_enc"))
            if "key_passphrase_enc" in result:
                result["key_passphrase"] = decrypt(result.pop("key_passphrase_enc"))
            return result
    raise HTTPException(404, "Server not found")


# Serve frontend static files in production
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
