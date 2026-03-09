"""
Silent launcher for SCP Tool.
.pyw = runs with pythonw.exe = no console window on Windows.
Starts the backend, opens the browser, shows a tray icon to quit.

Cross-platform: Windows, macOS, Linux (Ubuntu).
"""
import subprocess
import threading
import time
import os
import sys
import platform
import webbrowser
import urllib.request

import pystray
from PIL import Image

PORT = 8000
URL = f"http://127.0.0.1:{PORT}"

# Paths
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(script_dir, "backend")

# Find the venv python executable (cross-platform)
if sys.platform == "win32":
    # Windows: prefer pythonw.exe (no console), fall back to python.exe
    venv_python = os.path.join(backend_dir, "venv", "Scripts", "pythonw.exe")
    if not os.path.isfile(venv_python):
        venv_python = os.path.join(backend_dir, "venv", "Scripts", "python.exe")
else:
    # macOS / Linux
    venv_python = os.path.join(backend_dir, "venv", "bin", "python")

# Build platform-specific subprocess kwargs
popen_kwargs = dict(
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

if sys.platform == "win32":
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0  # SW_HIDE
    popen_kwargs["startupinfo"] = startupinfo
    popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
else:
    # On Unix, start in its own process group so we can clean up child processes
    popen_kwargs["start_new_session"] = True

server_process = subprocess.Popen(
    [venv_python, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(PORT)],
    cwd=backend_dir,
    **popen_kwargs,
)


# Wait for server to be ready, then open browser
def open_when_ready():
    for _ in range(30):
        try:
            urllib.request.urlopen(URL, timeout=1)
            break
        except Exception:
            time.sleep(0.5)
    webbrowser.open(URL)


threading.Thread(target=open_when_ready, daemon=True).start()

# --- System tray icon ---

def on_open(icon, item):
    webbrowser.open(URL)


def on_quit(icon, item):
    server_process.terminate()
    try:
        server_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server_process.kill()
    icon.stop()


# Load icon: use .ico on Windows, convert SVG->PNG or use PNG on Unix
icon_ico = os.path.join(script_dir, "icon.ico")
icon_png = os.path.join(script_dir, "icon.png")
icon_svg = os.path.join(script_dir, "icon.svg")

if sys.platform == "win32" and os.path.isfile(icon_ico):
    tray_image = Image.open(icon_ico)
elif os.path.isfile(icon_png):
    tray_image = Image.open(icon_png)
else:
    # Fallback: generate a simple 64x64 blue square with an arrow
    tray_image = Image.new("RGBA", (64, 64), (37, 99, 235, 255))

tray_icon = pystray.Icon(
    "scptool",
    tray_image,
    "SCP Tool",
    menu=pystray.Menu(
        pystray.MenuItem("Open SCP Tool", on_open, default=True),
        pystray.MenuItem("Quit", on_quit),
    ),
)

# This blocks until Quit is clicked
tray_icon.run()
