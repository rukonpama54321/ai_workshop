"""Start the API from the project root.

Usage (from E:\\AI Workshop 2026):
    backend\\.venv\\Scripts\\python serve.py

Or:
    .\\run-backend.ps1
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"

os.chdir(BACKEND)
sys.path.insert(0, str(BACKEND))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=[str(BACKEND / "app")],
    )
