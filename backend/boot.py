# backend/boot.py
import os
import subprocess
import sys

port = os.environ.get("PORT", "8000")
cmd = [
    "gunicorn", "server:app",
    "--bind", f"0.0.0.0:{port}",
    "--workers", "2",
    "--timeout", "120",
]
sys.exit(subprocess.call(cmd))
