"""Metadata-driven payload validation for the ingestion service."""

from __future__ import annotations

from typing import Any

from common.config.metadata_registry import MetadataRegistry
from common.validation.validator import SchemaValidator


class PayloadValidatorService:
    """Resolves the correct JSON Schema for a source via metadata, then
    validates. No source-specific validation code is ever required."""

    def __init__(self, registry: MetadataRegistry, validator: SchemaValidator) -> None:
        self._registry = registry
        self._validator = validator

    def validate(self, source_name: str, payload: dict[str, Any]) -> None:
        source = self._registry.get_source(source_name)
        self._validator.validate(payload, source.schema)
