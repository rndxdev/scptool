#!/bin/bash
# Cross-platform silent launcher for SCP Tool (macOS / Linux)
# Equivalent of launch.pyw but launched via shell for Unix systems.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
# Detect venv python (Windows/Git Bash uses Scripts/, Unix uses bin/)
if [ -f "$BACKEND_DIR/venv/bin/python" ]; then
    VENV_PYTHON="$BACKEND_DIR/venv/bin/python"
elif [ -f "$BACKEND_DIR/venv/Scripts/python.exe" ]; then
    VENV_PYTHON="$BACKEND_DIR/venv/Scripts/python.exe"
else
    echo "Error: Python virtual environment not found in backend/venv/"
    echo "Create one with:"
    echo "  cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Launch via the cross-platform .pyw script
exec "$VENV_PYTHON" "$SCRIPT_DIR/launch.pyw"
