"""Concrete repositories for the ingestion framework's curated tables."""

from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError

from common.exceptions.exceptions import DatabaseException
from common.models.tables import IngestionLog, LotMaster, RawEvent
from common.repository.base import BaseRepository


class LotRepository(BaseRepository[LotMaster]):
    model = LotMaster

    def get_by_lot_id(self, lot_id: str) -> LotMaster | None:
        try:
            return (
                self.session.query(LotMaster)
                .filter(LotMaster.lot_id == lot_id)
                .order_by(LotMaster.created_at.desc())
                .first()
            )
        except SQLAlchemyError as exc:
            raise DatabaseException(f"Failed to fetch lot {lot_id}: {exc}") from exc


class RawEventRepository(BaseRepository[RawEvent]):
    model = RawEvent

    def list_by_source(self, source: str, limit: int = 100) -> list[RawEvent]:
        try:
            return (
                self.session.query(RawEvent)
                .filter(RawEvent.source == source)
                .order_by(RawEvent.created_at.desc())
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as exc:
            raise DatabaseException(f"Failed to list raw events for {source}: {exc}") from exc


class IngestionLogRepository(BaseRepository[IngestionLog]):
    model = IngestionLog

    def list_by_request_id(self, request_id: str) -> list[IngestionLog]:
        try:
            return (
                self.session.query(IngestionLog)
                .filter(IngestionLog.request_id == request_id)
                .all()
            )
        except SQLAlchemyError as exc:
            raise DatabaseException(
                f"Failed to list ingestion log entries for {request_id}: {exc}"
            ) from exc
