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
        version=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
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

# Check that venv module is available
if ! "$PYTHON" -m venv --help &>/dev/null; then
    echo ""
    echo "Error: Python venv module is not installed."
    echo "Install it with:"
    echo "  Ubuntu: sudo apt install python3-venv"
    echo "  macOS:  (included with python3 from brew)"
    exit 1
fi

# Remove broken venv if activate is missing
if [ -d "$BACKEND_DIR/venv" ] && [ ! -f "$BACKEND_DIR/venv/bin/activate" ] && [ ! -f "$BACKEND_DIR/venv/Scripts/activate" ]; then
    echo "  Removing broken virtual environment..."
    rm -rf "$BACKEND_DIR/venv"
fi

if [ ! -d "$BACKEND_DIR/venv" ]; then
    "$PYTHON" -m venv "$BACKEND_DIR/venv"
    echo "  Virtual environment created."
else
    echo "  Virtual environment already exists."
fi

# Use venv pip directly instead of sourcing activate
if [ -f "$BACKEND_DIR/venv/bin/pip" ]; then
    PIP="$BACKEND_DIR/venv/bin/pip"
elif [ -f "$BACKEND_DIR/venv/Scripts/pip.exe" ]; then
    PIP="$BACKEND_DIR/venv/Scripts/pip.exe"
else
    echo "Error: pip not found in venv."
    echo "Try deleting backend/venv and running this script again."
    exit 1
fi

"$PIP" install --upgrade pip -q
"$PIP" install -r "$BACKEND_DIR/requirements.txt" -q
"$PIP" install pystray Pillow -q

echo "  Python dependencies installed."

# --- Frontend ---
echo ""
echo "[2/3] Setting up frontend..."

if [ -d "$FRONTEND_DIR" ]; then
    cd "$FRONTEND_DIR"
    if command -v npm &>/dev/null; then
        npm install --silent
        npm run build --silent 2>/dev/null || echo "  (Frontend build skipped - may need dev server instead)"
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
