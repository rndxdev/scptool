#!/bin/bash
# Start both backend and frontend dev servers

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Starting SCP Tool..."
echo ""

# Start backend
echo "[Backend] Starting FastAPI on http://127.0.0.1:8000"
cd "$SCRIPT_DIR/backend"
source venv/Scripts/activate
python main.py &
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
