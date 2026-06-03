@echo off
cd /d "%~dp0"
if not exist "backend\.venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv backend\.venv
  backend\.venv\Scripts\pip install -r backend\requirements.txt
)
set DATABASE_URL=postgresql://medclaim:medclaim@localhost:5432/medclaim
set UPLOAD_DIR=uploads
set LLM_BASE_URL=http://localhost:11434
echo Starting backend at http://127.0.0.1:8000
backend\.venv\Scripts\python.exe serve.py
