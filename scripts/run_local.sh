#!/usr/bin/env bash
# Run the ingestion-service directly on the host (outside Docker), useful
# for fast iteration. Requires a reachable PostgreSQL and LocalStack -
# typically started via: docker compose up postgres localstack
set -euo pipefail

cd "$(dirname "$0")/.."

export PYTHONPATH="$(pwd):$(pwd)/ingestion-service"
export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg2://sap_user:sap_password@localhost:5432/semiconductor}"
export AWS_ENDPOINT_URL="${AWS_ENDPOINT_URL:-http://localhost:4566}"
export AWS_REGION="${AWS_REGION:-us-east-1}"
export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-test}"
export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-test}"

cd ingestion-service
exec uvicorn main:app --reload --host 0.0.0.0 --port 8000
