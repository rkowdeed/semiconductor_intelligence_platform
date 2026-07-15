"""Dependency-injection wiring for the ingestion service.

Centralizing construction here keeps FastAPI route handlers thin and makes
the components easy to swap out in tests (e.g. via FastAPI's
``dependency_overrides``).
"""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy.orm import Session

from common.aws.kinesis_publisher import KinesisPublisher
from common.aws.s3_client import S3Client
from common.config.metadata_registry import MetadataRegistry, metadata_registry
from common.models.base import get_session
from common.storage.raw_payload_store import RawPayloadStore
from common.validation.validator import SchemaValidator, schema_validator
from publisher.event_publisher import EventPublisherService
from services.ingestion_service import IngestionService
from storage.raw_storage_service import RawStorageService
from validators.payload_validator import PayloadValidatorService


@lru_cache
def get_s3_client() -> S3Client:
    return S3Client()


@lru_cache
def get_kinesis_publisher() -> KinesisPublisher:
    return KinesisPublisher()


def get_metadata_registry() -> MetadataRegistry:
    return metadata_registry


def get_schema_validator() -> SchemaValidator:
    return schema_validator


def get_ingestion_service() -> IngestionService:
    registry = get_metadata_registry()
    validator_service = PayloadValidatorService(registry, get_schema_validator())
    storage_service = RawStorageService(registry, RawPayloadStore(get_s3_client()))
    publisher_service = EventPublisherService(registry, get_kinesis_publisher())
    return IngestionService(registry, validator_service, storage_service, publisher_service)


def get_db_session() -> Session:
    yield from get_session()
