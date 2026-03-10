#!/bin/bash
# Start both backend and frontend dev servers

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Detect venv python directly (no need to source activate)
if [ -f "$SCRIPT_DIR/backend/venv/bin/python" ]; then
    VENV_PYTHON="$SCRIPT_DIR/backend/venv/bin/python"
elif [ -f "$SCRIPT_DIR/backend/venv/Scripts/python.exe" ]; then
    VENV_PYTHON="$SCRIPT_DIR/backend/venv/Scripts/python.exe"
else
    echo "Error: Python virtual environment not found in backend/venv/"
    echo "Run: bash setup.sh"
    exit 1
fi

echo "Starting SCP Tool..."
echo ""

# Start backend
echo "[Backend] Starting FastAPI on http://127.0.0.1:8000"
"$VENV_PYTHON" "$SCRIPT_DIR/backend/main.py" &
BACKEND_PID=$!

# Start frontend
echo "[Frontend] Starting Vite on http://localhost:5173"
cd "$SCRIPT_DIR/frontend"
npx vite --host 127.0.0.1 &
FRONTEND_PID=$!

echo ""
echo "Open http://localhost:5173 in your browser"
echo "Press Ctrl+C to stop both servers"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
