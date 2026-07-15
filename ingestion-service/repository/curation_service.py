"""Metadata-driven curation: maps a validated raw payload to a curated
ORM record using metadata/mappings.yaml, then persists it via the
Repository Pattern.

Sources with an explicit column mapping (e.g. "mes") are written to their
dedicated curated table (LotMaster). Sources without a mapping fall back to
the generic RawEvent table so the framework can accept new sources purely
through configuration before a dedicated table/mapping is authored.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from common.config.metadata_registry import MetadataRegistry
from common.exceptions.exceptions import DatabaseException
from common.models.tables import LotMaster, RawEvent
from common.repository.repositories import LotRepository, RawEventRepository

_CURATORS: dict[str, str] = {
    "lot_master": "_curate_lot_master",
}


class CurationService:
    def __init__(self, registry: MetadataRegistry, session: Session) -> None:
        self._registry = registry
        self._session = session

    def curate(self, source_name: str, payload: dict[str, Any], s3_key: str) -> str:
        source = self._registry.get_source(source_name)
        mapping = self._registry.get_mapping(source_name)

        method_name = _CURATORS.get(source.target_table)
        if method_name and mapping:
            method = getattr(self, method_name)
            record = method(mapping, payload)
            return str(record.id)

        record = self._curate_raw_event(source_name, payload, s3_key)
        return str(record.id)

    def _curate_lot_master(self, mapping: dict[str, Any], payload: dict[str, Any]) -> LotMaster:
        fields = mapping.get("fields", {})
        column_values = {
            column: payload.get(source_field) for source_field, column in fields.items()
        }
        raw_ts = column_values.get("event_timestamp")
        column_values["event_timestamp"] = self._parse_timestamp(raw_ts)

        entity = LotMaster(**column_values)
        try:
            repo = LotRepository(self._session)
            return repo.add(entity)
        except DatabaseException:
            raise

    def _curate_raw_event(self, source_name: str, payload: dict[str, Any], s3_key: str) -> RawEvent:
        entity = RawEvent(
            source=source_name,
            event_type=payload.get("eventType"),
            payload=payload,
            s3_key=s3_key,
        )
        repo = RawEventRepository(self._session)
        return repo.add(entity)

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            normalized = value.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized)
        return datetime.utcnow()
