"""Core ingestion orchestration service.

Implements the processing flow defined in the spec:

    Incoming REST Request
      -> Load metadata
      -> Load schema
      -> Validate payload
      -> Persist raw payload to S3
      -> Publish event to Kinesis
      -> Insert curated record into PostgreSQL
      -> Return HTTP 202

Every step is fully metadata-driven: the source name is the only thing that
varies, and it is resolved once via MetadataRegistry.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from common.config.metadata_registry import MetadataRegistry
from common.exceptions.exceptions import DatabaseException
from common.logger.logger import get_logger
from common.models.tables import IngestionLog
from common.repository.repositories import IngestionLogRepository
from common.utils.request_utils import new_request_id, timer
from parser.payload_parser import PayloadParser
from publisher.event_publisher import EventPublisherService
from repository.curation_service import CurationService
from storage.raw_storage_service import RawStorageService
from validators.payload_validator import PayloadValidatorService

logger = get_logger(__name__)


class IngestionResult:
    def __init__(
        self,
        request_id: str,
        source: str,
        s3_key: str,
        stream: str,
        sequence_number: str | None,
        curated_record_id: str | None,
    ) -> None:
        self.request_id = request_id
        self.source = source
        self.s3_key = s3_key
        self.stream = stream
        self.sequence_number = sequence_number
        self.curated_record_id = curated_record_id


class IngestionService:
    def __init__(
        self,
        registry: MetadataRegistry,
        validator_service: PayloadValidatorService,
        storage_service: RawStorageService,
        publisher_service: EventPublisherService,
    ) -> None:
        self._registry = registry
        self._validator_service = validator_service
        self._storage_service = storage_service
        self._publisher_service = publisher_service

    def ingest(
        self,
        source_name: str,
        raw_body: bytes | str | dict[str, Any],
        session: Session,
    ) -> IngestionResult:
        request_id = new_request_id()
        status = "FAILED"
        stream_name = ""

        with timer() as elapsed:
            try:
                # Load metadata (also validates the source is known/enabled)
                source = self._registry.get_source(source_name)
                if not source.enabled:
                    from common.exceptions.exceptions import ConfigurationException

                    raise ConfigurationException(f"Source '{source_name}' is disabled")

                # Parse
                payload = PayloadParser.parse(raw_body)

                # Validate against the metadata-resolved JSON Schema
                self._validator_service.validate(source_name, payload)

                # Persist raw payload to S3
                s3_key = self._storage_service.persist(source_name, payload, request_id)

                # Publish event to Kinesis
                stream_name, _response = self._publisher_service.publish(
                    source_name, payload, partition_key=request_id
                )

                # Insert curated record into PostgreSQL
                curation_service = CurationService(self._registry, session)
                curated_record_id = curation_service.curate(source_name, payload, s3_key)

                status = "SUCCESS"
                result = IngestionResult(
                    request_id=request_id,
                    source=source_name,
                    s3_key=s3_key,
                    stream=stream_name,
                    sequence_number=_response.get("SequenceNumber"),
                    curated_record_id=curated_record_id,
                )
                return result
            finally:
                self._write_audit_log(
                    session=session,
                    request_id=request_id,
                    source=source_name,
                    stream=stream_name,
                    status=status,
                    duration_ms=elapsed.get("duration_ms"),
                )
                logger.info(
                    "ingestion_request_processed",
                    request_id=request_id,
                    source=source_name,
                    stream=stream_name,
                    status=status,
                    duration=elapsed.get("duration_ms"),
                )

    @staticmethod
    def _write_audit_log(
        *,
        session: Session,
        request_id: str,
        source: str,
        stream: str,
        status: str,
        duration_ms: float | None,
        error_message: str | None = None,
    ) -> None:
        try:
            entry = IngestionLog(
                request_id=request_id,
                source=source,
                stream=stream or None,
                status=status,
                duration_ms=duration_ms,
                error_message=error_message,
            )
            IngestionLogRepository(session).add(entry)
        except DatabaseException as exc:
            logger.warning("ingestion_audit_log_failed", request_id=request_id, error=str(exc))
