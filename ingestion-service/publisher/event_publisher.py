"""Metadata-driven event publishing to Kinesis."""

from __future__ import annotations

from typing import Any

from common.aws.kinesis_publisher import KinesisPublisher
from common.config.metadata_registry import MetadataRegistry


class EventPublisherService:
    """Resolves the correct stream for a source via metadata, then
    publishes. No source-specific publishing code is ever required."""

    def __init__(self, registry: MetadataRegistry, publisher: KinesisPublisher) -> None:
        self._registry = registry
        self._publisher = publisher

    def publish(
        self, source_name: str, payload: dict[str, Any], partition_key: str
    ) -> tuple[str, dict[str, Any]]:
        source = self._registry.get_source(source_name)
        physical_stream = self._registry.resolve_stream_name(source.stream)
        response = self._publisher.publish(physical_stream, partition_key, payload)
        return physical_stream, response
