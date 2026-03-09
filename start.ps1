# Start both backend and frontend dev servers
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Starting SCP Tool..." -ForegroundColor Cyan
Write-Host ""

# Start backend
Write-Host "[Backend] Starting FastAPI on http://127.0.0.1:8000" -ForegroundColor Green
$backend = Start-Process -NoNewWindow -PassThru -FilePath "$scriptDir\backend\venv\Scripts\python.exe" -ArgumentList "$scriptDir\backend\main.py" -WorkingDirectory "$scriptDir\backend"

# Start frontend
Write-Host "[Frontend] Starting Vite on http://localhost:5173" -ForegroundColor Green
$frontend = Start-Process -NoNewWindow -PassThru -FilePath "npx" -ArgumentList "vite --host 127.0.0.1" -WorkingDirectory "$scriptDir\frontend"

Write-Host ""
Write-Host "Open http://localhost:5173 in your browser" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop both servers" -ForegroundColor Yellow

try {
    Wait-Process -Id $backend.Id, $frontend.Id
} finally {
    Stop-Process -Id $backend.Id -ErrorAction SilentlyContinue
    Stop-Process -Id $frontend.Id -ErrorAction SilentlyContinue
}
