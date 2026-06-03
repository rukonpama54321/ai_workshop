# Start FastAPI backend (run from project root)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path "backend\.venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..."
    python -m venv backend\.venv
    & backend\.venv\Scripts\pip install -r backend\requirements.txt
}

$env:DATABASE_URL = "postgresql://medclaim:medclaim@localhost:5432/medclaim"
$env:UPLOAD_DIR = "uploads"
$env:LLM_BASE_URL = "http://localhost:11434"

Write-Host "Starting backend at http://127.0.0.1:8000"
& backend\.venv\Scripts\python.exe serve.py
