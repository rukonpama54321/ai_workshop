# Start React frontend (run from project root)
$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\frontend"

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing npm packages..."
    npm install
}

Write-Host "Starting frontend at http://127.0.0.1:5173"
npm run dev
