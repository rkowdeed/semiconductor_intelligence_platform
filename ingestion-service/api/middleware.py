"""Request logging middleware.

Ensures every request is logged as structured JSON with request_id,
source, stream, timestamp, status, and duration - as required by the spec.
The stream field is populated by the ingestion service once known; here we
guarantee request_id/status/duration/timestamp/source are always present.
"""

from __future__ import annotations

import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from common.logger.logger import get_logger
from common.utils.request_utils import new_request_id

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        request_id = new_request_id()
        request.state.request_id = request_id
        start = time.perf_counter()

        source = self._infer_source(request.url.path)

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 3)
            logger.error(
                "request_unhandled_error",
                request_id=request_id,
                source=source,
                stream=None,
                status="ERROR",
                duration=duration_ms,
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 3)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_completed",
            request_id=request_id,
            source=source,
            stream=None,
            status=response.status_code,
            duration=duration_ms,
        )
        return response

    @staticmethod
    def _infer_source(path: str) -> str:
        parts = [p for p in path.split("/") if p]
        # /api/v1/mes/events -> "mes"
        if len(parts) >= 3 and parts[0] == "api":
            return parts[2]
        return "n/a"
