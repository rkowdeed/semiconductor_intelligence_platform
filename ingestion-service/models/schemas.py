"""Pydantic (v2) request/response models for the ingestion API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IngestionAcceptedResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    source: str
    status: str = "ACCEPTED"
    s3_key: str
    stream: str
    sequence_number: str | None = None
    curated_record_id: str | None = None


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class HealthComponent(BaseModel):
    status: str
    detail: str | None = None


class HealthResponse(BaseModel):
    status: str
    components: dict[str, HealthComponent]


class SourceInfo(BaseModel):
    name: str
    display_name: str
    endpoint: str
    method: str
    type: str
    schema_path: str = Field(alias="schema")
    target_table: str
    target_schema: str
    stream: str
    enabled: bool

    model_config = ConfigDict(populate_by_name=True)


class StreamInfo(BaseModel):
    logical_name: str
    physical_name: str
    shard_count: int
