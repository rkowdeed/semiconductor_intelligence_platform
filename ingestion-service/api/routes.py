"""Dynamic, metadata-driven ingestion routes.

Endpoints are registered at startup by iterating metadata/sources.yaml -
adding a new source (e.g. "erp") only requires flipping ``enabled: true``
and providing a schema; no new route handler code is needed.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from api.dependencies import get_db_session, get_ingestion_service, get_metadata_registry
from common.config.metadata_registry import MetadataRegistry
from models.schemas import IngestionAcceptedResponse
from parser.payload_parser import PayloadParser
from services.ingestion_service import IngestionService


def build_ingestion_router() -> APIRouter:
    """Builds an APIRouter with one POST endpoint per enabled source,
    dynamically registered from metadata."""
    router = APIRouter(tags=["ingestion"])
    registry = get_metadata_registry()
    sources = registry.get_sources()

    for source_name, source in sources.items():
        if not source.enabled:
            continue
        _register_source_route(
            router,
            source_name,
            source.endpoint,
            source.method,
            source.input_format,
        )

    return router


def _register_source_route(
    router: APIRouter,
    source_name: str,
    endpoint: str,
    method: str,
    source_input_format: str,
) -> None:
    async def handler(
        request: Request,
        ingestion_service: IngestionService = Depends(get_ingestion_service),
        session: Session = Depends(get_db_session),
    ) -> IngestionAcceptedResponse:
        raw_body = await request.body()
        payload = PayloadParser.parse_with_format(
            raw_body,
            content_type=request.headers.get("content-type"),
            source_format=source_input_format,
        )
        result = ingestion_service.ingest(source_name, payload, session)
        return IngestionAcceptedResponse(
            request_id=result.request_id,
            source=result.source,
            s3_key=result.s3_key,
            stream=result.stream,
            sequence_number=result.sequence_number,
            curated_record_id=result.curated_record_id,
        )

    router.add_api_route(
        endpoint,
        handler,
        methods=[method],
        status_code=status.HTTP_202_ACCEPTED,
        response_model=IngestionAcceptedResponse,
        summary=f"Ingest a {source_name.upper()} event",
        name=f"ingest_{source_name}",
    )
