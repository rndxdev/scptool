"""
Silent launcher for SCP Tool.
.pyw = runs with pythonw.exe = no console window.
Starts the backend, opens the browser, shows a tray icon to quit.
"""
import subprocess
import threading
import time
import os
import webbrowser
import urllib.request

import pystray
from PIL import Image

PORT = 8000
URL = f"http://127.0.0.1:{PORT}"

# Paths
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(script_dir, "backend")
icon_path = os.path.join(script_dir, "icon.ico")
venv_python = os.path.join(backend_dir, "venv", "Scripts", "pythonw.exe")

if not os.path.isfile(venv_python):
    venv_python = os.path.join(backend_dir, "venv", "Scripts", "python.exe")

# Start the backend server (hidden)
server_process = subprocess.Popen(
    [venv_python, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(PORT)],
    cwd=backend_dir,
    creationflags=subprocess.CREATE_NO_WINDOW,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
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
    server_process.wait(timeout=5)
    icon.stop()

tray_image = Image.open(icon_path)
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
