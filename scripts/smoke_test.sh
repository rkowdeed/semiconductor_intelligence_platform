#!/usr/bin/env bash
# Quick smoke test against a running stack (docker compose up).
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000/api/v1}"
AWS_ENDPOINT_URL="${AWS_ENDPOINT_URL:-}"
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_PROFILE="${AWS_PROFILE:-default}"
NORMALIZE_BUCKET="${NORMALIZE_BUCKET:-semiconductor-landing}"

export AWS_REGION
export AWS_PROFILE

AWS_CLI=(aws --region "${AWS_REGION}" --profile "${AWS_PROFILE}")
if [[ -n "${AWS_ENDPOINT_URL}" ]]; then
  AWS_CLI+=(--endpoint-url "${AWS_ENDPOINT_URL}")
fi

echo "==> Health check"
curl -sf "${BASE_URL}/health" | python3 -m json.tool

echo "==> Data categories check"
curl -sf "${BASE_URL}/config/data-categories" | python3 -m json.tool

echo "==> Posting sample MES event"
curl -sf -X POST "${BASE_URL}/mes/events" \
  -H "Content-Type: application/json" \
  -d @sample-data/mes/lot_completed_sample.json | python3 -m json.tool

echo "==> Posting sample ERP event"
curl -sf -X POST "${BASE_URL}/erp/events" \
  -H "Content-Type: application/json" \
  -d @sample-data/erp/work_order_sample.json | python3 -m json.tool

echo "==> Posting sample equipment event"
curl -sf -X POST "${BASE_URL}/equipment/events" \
  -H "Content-Type: application/json" \
  -d @sample-data/equipment/equipment_event_sample.json | python3 -m json.tool

echo "==> Posting sample PLM event"
curl -sf -X POST "${BASE_URL}/plm/events" \
  -H "Content-Type: application/json" \
  -d @sample-data/plm/product_lifecycle_event_sample.json | python3 -m json.tool

echo "==> Posting telemetry sample event"
curl -sf -X POST "${BASE_URL}/telemetry/events" \
  -H "Content-Type: application/json" \
  -d @sample-data/telemetry/telemetry_sample.json | python3 -m json.tool

echo "==> Posting yield sample event"
curl -sf -X POST "${BASE_URL}/yield/events" \
  -H "Content-Type: text/csv" \
  -d @sample-data/yield/yield_sample.csv | python3 -m json.tool

echo "==> Posting multiformat sample events"
for sample_file in sample-data/files/multiformat/*_sample.json; do
  echo "   -> ${sample_file}"
  curl -sf -X POST "${BASE_URL}/files/multiformat/events" \
    -H "Content-Type: application/json" \
    -d @"${sample_file}" | python3 -m json.tool
done

echo "==> Uploading native sample files for normalization test"
for native_file in sample-data/files/native/*.{xml,csv,txt,parquet}; do
  [[ -e "${native_file}" ]] || continue
  key="files/native/$(basename "${native_file}")"
  echo "   -> s3://${NORMALIZE_BUCKET}/${key}"
  "${AWS_CLI[@]}" s3 cp "${native_file}" "s3://${NORMALIZE_BUCKET}/${key}" >/dev/null
done

echo "==> Running normalization script"
python3 scripts/normalize_s3_files.py \
  --source file_multiformat \
  --bucket "${NORMALIZE_BUCKET}" \
  --source-prefix "files/native" \
  --normalized-prefix "files/native/normalized" \
  --format AUTO

echo "==> Listing normalized JSON objects"
"${AWS_CLI[@]}" s3 ls "s3://${NORMALIZE_BUCKET}/files/native/normalized/" --recursive

echo "==> Posting invalid MES event (expect 400)"
curl -s -o /dev/stderr -w "HTTP %{http_code}\n" -X POST "${BASE_URL}/mes/events" \
  -H "Content-Type: application/json" \
  -d @sample-data/mes/lot_completed_invalid_sample.json || true

echo "==> Posting invalid ERP event (expect 400)"
curl -s -o /dev/stderr -w "HTTP %{http_code}\n" -X POST "${BASE_URL}/erp/events" \
  -H "Content-Type: application/json" \
  -d @sample-data/erp/work_order_invalid_sample.json || true

echo "==> Posting invalid equipment event (expect 400)"
curl -s -o /dev/stderr -w "HTTP %{http_code}\n" -X POST "${BASE_URL}/equipment/events" \
  -H "Content-Type: application/json" \
  -d @sample-data/equipment/equipment_event_invalid_sample.json || true

echo "==> Posting invalid PLM event (expect 400)"
curl -s -o /dev/stderr -w "HTTP %{http_code}\n" -X POST "${BASE_URL}/plm/events" \
  -H "Content-Type: application/json" \
  -d @sample-data/plm/product_lifecycle_event_invalid_sample.json || true

echo "==> Done"
