# Dockerfile (repo root)
FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium chromium-driver \
    fonts-liberation libnss3 libxss1 libasound2 \
    libatk1.0-0 libatk-bridge2.0-0 libpangocairo-1.0-0 libcairo2 \
    libxkbcommon0 libgbm1 libpango-1.0-0 libgtk-3-0 \
 && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r /app/backend/requirements.txt \
 && python3 -c "import gunicorn,sys; print('gunicorn', gunicorn.__version__)"

COPY backend/ /app/backend/

WORKDIR /app/backend
ENTRYPOINT ["/usr/local/bin/python3", "/app/backend/boot.py"]
