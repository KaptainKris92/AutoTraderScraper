import os

FLASK_SECRET_KEY = os.getenv("SECRET_KEY", "abcdefg")
PORT = int(os.getenv("PORT", "8080"))  # Railway sets PORT
DATA_DIR = os.getenv("DATA_DIR", "/data")  # Volume mount path
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(DATA_DIR, "images"))
THUMBNAIL_DIR = os.getenv(
    "THUMBNAIL_DIR", os.path.join(DATA_DIR, "thumbnails"))
DATABASE_URL = os.getenv(
    "DATABASE_URL", f"sqlite:///{os.path.join(DATA_DIR, 'app.db')}")
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN")  # ADD NETLIFY URL ONCE CREATED
