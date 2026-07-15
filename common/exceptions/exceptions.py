"""Custom exception hierarchy for Semiconductor_Operations_Data_Platform."""

from __future__ import annotations

from typing import Any


class SAPBaseException(Exception):
    """Base class for all platform-specific exceptions."""

    default_status_code: int = 500

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {"error": self.__class__.__name__, "message": self.message, "details": self.details}


class ValidationException(SAPBaseException):
    """Raised when an inbound payload fails JSON Schema validation."""

    default_status_code = 400


class StorageException(SAPBaseException):
    """Raised when persisting a raw payload to object storage fails."""

    default_status_code = 502


class KinesisException(SAPBaseException):
    """Raised when publishing an event to Kinesis fails."""

    default_status_code = 502


class ConfigurationException(SAPBaseException):
    """Raised when configuration or metadata cannot be loaded or is invalid."""

    default_status_code = 500


class DatabaseException(SAPBaseException):
    """Raised when a database operation fails."""

    default_status_code = 502


class SourceNotFoundException(SAPBaseException):
    """Raised when a request references a source not present in metadata."""

    default_status_code = 404
