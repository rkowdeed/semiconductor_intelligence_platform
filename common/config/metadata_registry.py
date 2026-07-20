"""Metadata registry: the runtime view of metadata/*.yaml.

This is what makes the framework metadata-driven - onboarding a new source
is a matter of adding entries to these YAML files, not writing new code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from common.config.loader import ConfigLoader, config_loader
from common.exceptions.exceptions import ConfigurationException, SourceNotFoundException


@dataclass(frozen=True)
class SourceDefinition:
    name: str
    display_name: str
    endpoint: str
    method: str
    type: str
    input_format: str
    schema: str
    target_table: str
    target_schema: str
    stream: str
    raw_bucket: str
    raw_prefix: str
    enabled: bool


class MetadataRegistry:
    """Loads and exposes source/mapping/routing/validation/stream metadata."""

    def __init__(self, loader: ConfigLoader | None = None) -> None:
        self._loader = loader or config_loader
        self._app_config = self._loader.load("config/application.yaml")

    def _metadata_files(self) -> dict[str, str]:
        return self._app_config["metadata"]

    def get_sources(self) -> dict[str, SourceDefinition]:
        files = self._metadata_files()
        raw = self._loader.load(files["sources_file"])
        sources = raw.get("sources", {})
        result: dict[str, SourceDefinition] = {}
        for name, cfg in sources.items():
            try:
                result[name] = SourceDefinition(
                    name=name,
                    display_name=cfg.get("display_name", name),
                    endpoint=cfg["endpoint"],
                    method=cfg.get("method", "POST"),
                    type=cfg.get("type", "REST"),
                    input_format=cfg.get("input_format", "AUTO"),
                    schema=cfg["schema"],
                    target_table=cfg["target_table"],
                    target_schema=cfg.get("target_schema", "metadata"),
                    stream=cfg["stream"],
                    raw_bucket=cfg["raw_bucket"],
                    raw_prefix=cfg.get("raw_prefix", name),
                    enabled=cfg.get("enabled", True),
                )
            except KeyError as exc:
                raise ConfigurationException(
                    f"Source '{name}' is missing required metadata field: {exc}"
                ) from exc
        return result

    def get_source(self, name: str) -> SourceDefinition:
        sources = self.get_sources()
        if name not in sources:
            raise SourceNotFoundException(f"Unknown source: {name}")
        return sources[name]

    def get_mapping(self, source_name: str) -> dict[str, Any]:
        files = self._metadata_files()
        raw = self._loader.load(files["mappings_file"])
        mappings = raw.get("mappings", {})
        return mappings.get(source_name, {})

    def get_routing(self, source_name: str) -> dict[str, Any]:
        files = self._metadata_files()
        raw = self._loader.load(files["routing_file"])
        routing = raw.get("routing", {})
        return routing.get(source_name, {})

    def get_validation(self, source_name: str) -> dict[str, Any]:
        files = self._metadata_files()
        raw = self._loader.load(files["validation_file"])
        validation = raw.get("validation", {})
        return validation.get(source_name, {})

    def get_streams(self) -> dict[str, Any]:
        files = self._metadata_files()
        raw = self._loader.load(files["streams_file"])
        return raw.get("streams", {})

    def get_data_categories(self) -> dict[str, Any]:
        files = self._metadata_files()
        raw = self._loader.load(files["data_categories_file"])
        return raw.get("data_categories", {})

    def resolve_stream_name(self, logical_name: str) -> str:
        streams = self.get_streams()
        if logical_name not in streams:
            raise ConfigurationException(f"Unknown logical stream: {logical_name}")
        return streams[logical_name]["name"]


metadata_registry = MetadataRegistry()
