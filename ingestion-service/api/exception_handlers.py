"""Global FastAPI exception handlers mapping custom exceptions to HTTP
responses with a consistent error envelope."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from common.exceptions.exceptions import (
    ConfigurationException,
    DatabaseException,
    KinesisException,
    SAPBaseException,
    SourceNotFoundException,
    StorageException,
    ValidationException,
)
from common.logger.logger import get_logger

logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(SAPBaseException)
    async def handle_sap_exception(request: Request, exc: SAPBaseException) -> JSONResponse:
        logger.warning(
            "request_failed",
            path=str(request.url.path),
            error=exc.__class__.__name__,
            message=exc.message,
        )
        return JSONResponse(status_code=exc.default_status_code, content=exc.to_dict())

    # Explicit registrations kept for clarity / documentation purposes even
    # though they are covered by the SAPBaseException handler above.
    for exc_type in (
        ValidationException,
        StorageException,
        KinesisException,
        ConfigurationException,
        DatabaseException,
        SourceNotFoundException,
    ):
        app.exception_handler(exc_type)(handle_sap_exception)

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_exception", path=str(request.url.path), error=str(exc))
        return JSONResponse(
            status_code=500,
            content={"error": "InternalServerError", "message": "An unexpected error occurred.", "details": {}},
        )
