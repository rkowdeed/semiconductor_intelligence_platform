"""Simple browser-based validation UI routes for the ingestion pipeline."""

from __future__ import annotations

import json
from html import escape
from typing import Any

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from api.dependencies import get_db_session, get_ingestion_service
from common.models.tables import IngestionLog, LotMaster, RawEvent
from services.ingestion_service import IngestionService

router = APIRouter(tags=["ui"])

_HTML_TEMPLATE = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Validate ingestion output</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; background: #f4f7fb; color: #1f2937; }}
    main {{ max-width: 1100px; margin: 2rem auto; background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.08); }}
    h1, h2 {{ color: #0f172a; }}
    label {{ display: block; font-weight: bold; margin-top: 1rem; }}
    select, textarea, input, button {{ width: 100%; padding: 0.7rem; margin-top: 0.35rem; border-radius: 8px; border: 1px solid #cbd5e1; box-sizing: border-box; }}
    button {{ background: #2563eb; color: white; border: none; cursor: pointer; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
    .card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1rem; margin-top: 1rem; }}
    pre {{ white-space: pre-wrap; word-break: break-word; background: #0f172a; color: #e2e8f0; padding: 1rem; border-radius: 8px; }}
    .muted {{ color: #64748b; font-size: 0.95rem; }}
  </style>
</head>
<body>
  <main>
    <h1>Validate ingestion output</h1>
    <p class=\"muted\">Submit a sample payload to validate the end-to-end flow across the ingestion API, Kinesis topic, and PostgreSQL curated tables.</p>
    <form method=\"post\" action=\"/api/v1/ui/validate\">
      <label for=\"source\">Source</label>
      <select id=\"source\" name=\"source\">
        <option value=\"mes\">MES</option>
        <option value=\"erp\">ERP</option>
        <option value=\"equipment\">Equipment</option>
        <option value=\"plm\">PLM</option>
      </select>

      <label for=\"content_type\">Content type</label>
      <select id=\"content_type\" name=\"content_type\">
        <option value=\"application/json\">application/json</option>
        <option value=\"application/xml\">application/xml</option>
      </select>

      <label for=\"payload\">Payload JSON</label>
      <textarea id=\"payload\" name=\"payload\" rows=\"16\">{{default_payload}}</textarea>
      <button type=\"submit\">Submit</button>
    </form>

    <div class=\"card\">
      <h2>Result</h2>
      <pre>{{result_html}}</pre>
    </div>
  </main>
</body>
</html>
"""

_DEFAULT_PAYLOAD = """{
  \"eventType\": \"LOT_COMPLETED\",
  \"lotId\": \"LOT10001\",
  \"recipeId\": \"REC100\",
  \"equipmentId\": \"ETCH001\",
  \"waferCount\": 25,
  \"temperature\": 72.5,
  \"eventTimestamp\": \"2026-08-10T10:15:30Z\"
}"""


@router.get("/ui/validate", include_in_schema=False)
async def validation_ui() -> Response:
    return Response(
        content=_HTML_TEMPLATE.replace("{{default_payload}}", _DEFAULT_PAYLOAD).replace(
            "{{result_html}}", "No submission yet."
        ),
        media_type="text/html; charset=utf-8",
        status_code=status.HTTP_200_OK,
    )


@router.post("/api/v1/ui/validate", include_in_schema=False)
async def submit_validation(
    request: Request,
    ingestion_service: IngestionService = Depends(get_ingestion_service),
    session: Session = Depends(get_db_session),
) -> dict[str, Any]:
    form = await request.json()
    source = form.get("source", "mes")
    content_type = form.get("content_type", "application/json")
    payload = form.get("payload", {})

    if isinstance(payload, str):
        payload = json.loads(payload)

    result = ingestion_service.ingest(source, payload, session)

    latest_log = (
        session.query(IngestionLog)
        .filter(IngestionLog.request_id == result.request_id)
        .order_by(IngestionLog.created_at.desc())
        .first()
    )

    if source == "mes":
        curated_row = (
            session.query(LotMaster)
            .filter(LotMaster.lot_id == payload.get("lotId"))
            .order_by(LotMaster.created_at.desc())
            .first()
        )
        table_name = "mdm.lot_master"
    else:
        curated_row = (
            session.query(RawEvent)
            .filter(RawEvent.source == source)
            .order_by(RawEvent.created_at.desc())
            .first()
        )
        table_name = "metadata.raw_events"

    return {
        "ingestion": {
            "source": result.source,
            "status": "ACCEPTED",
            "request_id": result.request_id,
            "s3_key": result.s3_key,
            "stream": result.stream,
            "sequence_number": result.sequence_number,
            "curated_record_id": result.curated_record_id,
        },
        "postgresql": {
            "table": table_name,
            "record_id": str(curated_row.id) if curated_row else None,
            "event_type": (curated_row.event_type if hasattr(curated_row, "event_type") else None),
            "source": (curated_row.source if hasattr(curated_row, "source") else None),
        },
        "kinesis": {
            "stream": result.stream,
            "sequence_number": result.sequence_number,
        },
        "audit": {
            "request_id": latest_log.request_id if latest_log else None,
            "status": latest_log.status if latest_log else None,
            "duration_ms": latest_log.duration_ms if latest_log else None,
        },
        "content_type": content_type,
    }
