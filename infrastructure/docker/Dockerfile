FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full repository so that both `common/` (shared code) and
# `ingestion-service/` (the service) are available.
COPY common /app/common
COPY config /app/config
COPY metadata /app/metadata
COPY schemas /app/schemas
COPY ingestion-service /app/ingestion-service

# Repository root (for `common.*` imports) AND the service directory
# (for `api`, `services`, `parser`, etc. imports) both need to be on the
# Python path, since "ingestion-service" is not a valid package name.
ENV PYTHONPATH=/app:/app/ingestion-service

WORKDIR /app/ingestion-service

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
    CMD curl -f http://localhost:8000/api/v1/ready || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
