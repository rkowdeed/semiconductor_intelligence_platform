"""Tests for the Repository Pattern implementations against an in-memory
SQLite database (schemas are simulated as SQLite doesn't support them
natively, so we patch table args for the test run)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from common.models.base import Base
from common.models.tables import IngestionLog, LotMaster, RawEvent
from common.repository.repositories import IngestionLogRepository, LotRepository, RawEventRepository


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # SQLite has no schema concept - attach each configured schema as an
    # in-memory database alias so `schema.table` references resolve.
    @event.listens_for(engine, "connect")
    def _attach_schemas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        for schema in ("mdm", "metadata", "quality"):
            cursor.execute(f"ATTACH DATABASE ':memory:' AS {schema}")
        cursor.close()

    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


def test_lot_repository_add_and_get(session) -> None:
    repo = LotRepository(session)
    entity = LotMaster(
        lot_id="LOT1",
        recipe_id="REC1",
        equipment_id="EQ1",
        wafer_count=25,
        temperature=45.0,
        event_type="LOT_COMPLETED",
        event_timestamp=datetime.now(timezone.utc),
    )
    saved = repo.add(entity)
    assert saved.id is not None

    fetched = repo.get_by_lot_id("LOT1")
    assert fetched is not None
    assert fetched.lot_id == "LOT1"


def test_raw_event_repository_list_by_source(session) -> None:
    repo = RawEventRepository(session)
    repo.add(RawEvent(source="erp", event_type="WORK_ORDER", payload={"a": 1}))
    repo.add(RawEvent(source="erp", event_type="WORK_ORDER", payload={"a": 2}))
    repo.add(RawEvent(source="equipment", event_type="ALARM", payload={"a": 3}))

    erp_events = repo.list_by_source("erp")
    assert len(erp_events) == 2


def test_ingestion_log_repository_list_by_request_id(session) -> None:
    repo = IngestionLogRepository(session)
    repo.add(IngestionLog(request_id="req-1", source="mes", stream="mes-events", status="SUCCESS"))
    repo.add(IngestionLog(request_id="req-1", source="mes", stream="mes-events", status="SUCCESS"))
    repo.add(IngestionLog(request_id="req-2", source="mes", stream="mes-events", status="FAILED"))

    entries = repo.list_by_request_id("req-1")
    assert len(entries) == 2


def test_base_repository_list_orders_by_created_at(session) -> None:
    repo = RawEventRepository(session)
    for i in range(3):
        repo.add(RawEvent(source="mes", event_type="LOT_COMPLETED", payload={"i": i}))

    results = repo.list(limit=10)
    assert len(results) == 3
