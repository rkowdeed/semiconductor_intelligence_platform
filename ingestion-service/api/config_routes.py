"""Read-only endpoints exposing the currently loaded metadata."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies import get_metadata_registry
from common.config.metadata_registry import MetadataRegistry
from models.schemas import SourceInfo, StreamInfo

router = APIRouter(prefix="/config", tags=["configuration"])


@router.get("/sources", response_model=list[SourceInfo], summary="List configured sources")
def list_sources(registry: MetadataRegistry = Depends(get_metadata_registry)) -> list[SourceInfo]:
    sources = registry.get_sources()
    return [
        SourceInfo(
            name=s.name,
            display_name=s.display_name,
            endpoint=s.endpoint,
            method=s.method,
            type=s.type,
            schema=s.schema,
            target_table=s.target_table,
            target_schema=s.target_schema,
            stream=s.stream,
            enabled=s.enabled,
        )
        for s in sources.values()
    ]


@router.get("/streams", response_model=list[StreamInfo], summary="List configured Kinesis streams")
def list_streams(registry: MetadataRegistry = Depends(get_metadata_registry)) -> list[StreamInfo]:
    streams = registry.get_streams()
    return [
        StreamInfo(logical_name=name, physical_name=cfg["name"], shard_count=cfg.get("shard_count", 1))
        for name, cfg in streams.items()
    ]
