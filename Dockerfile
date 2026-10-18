
# syntax=docker/dockerfile:1

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_DATA_DIR=/data \
    APP_CONFIG_DIR=/config \
    OAUTH_PORT=8765

WORKDIR /app

RUN groupadd --system app \
    && useradd --system --gid app --create-home --home-dir /home/app app \
    && mkdir -p /data/incoming /data/uploaded /config \
    && chown -R app:app /app /data /config /home/app
    
COPY requirements.txt .

RUN python -m pip install --no-cache-dir \
    -r requirements.txt

COPY --chown=app:app main.py .

USER app

EXPOSE 8765

ENTRYPOINT ["python", "/app/main.py"]
