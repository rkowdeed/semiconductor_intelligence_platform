"""Metadata-driven raw payload storage to S3."""

from __future__ import annotations

from typing import Any

from common.config.metadata_registry import MetadataRegistry
from common.storage.raw_payload_store import RawPayloadStore


class RawStorageService:
    """Resolves the correct bucket/prefix for a source via metadata, then
    persists the raw payload. No source-specific storage code is required."""

    def __init__(self, registry: MetadataRegistry, store: RawPayloadStore) -> None:
        self._registry = registry
        self._store = store

    def persist(self, source_name: str, payload: dict[str, Any], request_id: str) -> str:
        source = self._registry.get_source(source_name)
        return self._store.persist(
            bucket=source.raw_bucket,
            prefix=source.raw_prefix,
            source=source_name,
            payload=payload,
            request_id=request_id,
        )
