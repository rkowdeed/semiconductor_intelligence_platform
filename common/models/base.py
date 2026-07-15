"""SQLAlchemy declarative base, engine, and session factory."""

from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


def _build_database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://sap_user:sap_password@localhost:5432/semiconductor",
    )


engine = create_engine(_build_database_url(), pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a scoped SQLAlchemy session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
