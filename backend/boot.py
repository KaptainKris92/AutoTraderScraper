import os
import sys
from gunicorn.app.wsgiapp import run

port = os.environ.get("PORT", "8000")
sys.argv = [
    "gunicorn", "server:app",
    "--bind", f"0.0.0.0:{port}",
    "--workers", "2",
    "--timeout", "120",
]
run()
