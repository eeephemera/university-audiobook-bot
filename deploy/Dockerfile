# syntax=docker/dockerfile:1
# 3.13-slim: stable, broad wheel coverage, close to the 3.14 dev runtime.
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code.
COPY app ./app
COPY scripts ./scripts
COPY data ./data

# SQLite DB lives here; mount as a volume to persist across restarts.
VOLUME ["/app/data"]

CMD ["python", "-m", "app"]
