#!/usr/bin/env bash
# Quick smoke test against a running stack (docker compose up).
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000/api/v1}"

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

echo "==> Posting multiformat sample events"
for sample_file in sample-data/files/multiformat/*_sample.json; do
  echo "   -> ${sample_file}"
  curl -sf -X POST "${BASE_URL}/files/multiformat/events" \
    -H "Content-Type: application/json" \
    -d @"${sample_file}" | python3 -m json.tool
done

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
