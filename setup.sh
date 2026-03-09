#!/bin/bash
# One-time setup for SCP Tool on macOS / Linux.
# Creates the Python venv, installs dependencies, and builds the frontend.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

echo "=== SCP Tool Setup ==="
echo ""

# --- Python venv ---
echo "[1/3] Setting up Python virtual environment..."

# Find python3
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        version=$("$cmd" --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
        major=$(echo "$version" | cut -d. -f1)
        if [ "$major" = "3" ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "Error: Python 3 is required but not found."
    echo "Install it with:"
    echo "  macOS:  brew install python3"
    echo "  Ubuntu: sudo apt install python3 python3-venv python3-pip"
    exit 1
fi

echo "  Using: $PYTHON ($($PYTHON --version))"

if [ ! -d "$BACKEND_DIR/venv" ]; then
    "$PYTHON" -m venv "$BACKEND_DIR/venv"
    echo "  Virtual environment created."
else
    echo "  Virtual environment already exists."
fi

source "$BACKEND_DIR/venv/bin/activate"
pip install --upgrade pip -q
pip install -r "$BACKEND_DIR/requirements.txt" -q

# Install tray icon dependencies
pip install pystray Pillow -q

echo "  Python dependencies installed."

# --- Frontend ---
echo ""
echo "[2/3] Setting up frontend..."

if [ -d "$FRONTEND_DIR" ]; then
    cd "$FRONTEND_DIR"
    if command -v npm &>/dev/null; then
        npm install --silent
        npm run build --silent 2>/dev/null || echo "  (Frontend build skipped — may need dev server instead)"
    else
        echo "  Warning: npm not found. Install Node.js to build the frontend."
        echo "    macOS:  brew install node"
        echo "    Ubuntu: sudo apt install nodejs npm"
    fi
fi

# --- Desktop shortcut ---
echo ""
echo "[3/3] Creating desktop shortcut..."
bash "$SCRIPT_DIR/create-shortcut.sh"

echo ""
echo "=== Setup complete! ==="
echo ""
echo "To launch SCP Tool:"
echo "  bash $SCRIPT_DIR/launch.sh"
echo ""
echo "Or use the desktop shortcut / app that was just created."
