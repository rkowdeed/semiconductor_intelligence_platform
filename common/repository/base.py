"""Generic repository base class implementing the Repository Pattern."""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from common.exceptions.exceptions import DatabaseException
from common.logger.logger import get_logger

logger = get_logger(__name__)

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """Base repository providing common CRUD operations for a single model.

    Concrete repositories (LotRepository, RawEventRepository, ...) subclass
    this and add domain-specific query methods.
    """

    model: type[ModelType]

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, entity: ModelType) -> ModelType:
        try:
            self.session.add(entity)
            self.session.commit()
            self.session.refresh(entity)
            return entity
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseException(f"Failed to persist {self.model.__name__}: {exc}") from exc

    def get_by_id(self, entity_id) -> ModelType | None:
        try:
            return self.session.get(self.model, entity_id)
        except SQLAlchemyError as exc:
            raise DatabaseException(f"Failed to fetch {self.model.__name__}: {exc}") from exc

    def list(self, limit: int = 100, offset: int = 0) -> list[ModelType]:
        try:
            return (
                self.session.query(self.model)
                .order_by(self.model.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as exc:
            raise DatabaseException(f"Failed to list {self.model.__name__}: {exc}") from exc
