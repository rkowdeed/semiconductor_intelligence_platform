#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Executed automatically by LocalStack on container startup (mounted into
# /etc/localstack/init/ready.d/). Provisions the S3 bucket and Kinesis
# streams the ingestion service expects to find, per metadata/*.yaml.
# ---------------------------------------------------------------------------
set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
ENDPOINT="http://localhost:4566"

echo "[localstack-init] Creating S3 bucket: semiconductor-landing"
awslocal s3api create-bucket \
  --bucket semiconductor-landing \
  --region "${REGION}" \
  || echo "[localstack-init] Bucket may already exist, continuing."

echo "[localstack-init] Creating Kinesis stream: mes-events"
awslocal kinesis create-stream --stream-name mes-events --shard-count 1 \
  || echo "[localstack-init] Stream mes-events may already exist, continuing."

echo "[localstack-init] Creating Kinesis stream: metadata-events"
awslocal kinesis create-stream --stream-name metadata-events --shard-count 1 \
  || echo "[localstack-init] Stream metadata-events may already exist, continuing."

echo "[localstack-init] Creating Kinesis stream: quality-events"
awslocal kinesis create-stream --stream-name quality-events --shard-count 1 \
  || echo "[localstack-init] Stream quality-events may already exist, continuing."

echo "[localstack-init] Creating Kinesis stream: plm-events"
awslocal kinesis create-stream --stream-name plm-events --shard-count 1 \
  || echo "[localstack-init] Stream plm-events may already exist, continuing."

echo "[localstack-init] Waiting for Kinesis streams to become ACTIVE"
for stream in mes-events metadata-events quality-events plm-events; do
  awslocal kinesis wait stream-exists --stream-name "${stream}"
done

echo "[localstack-init] Bootstrap complete."
