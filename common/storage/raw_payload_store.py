"""Storage service responsible for persisting raw payloads to S3."""

from __future__ import annotations

from typing import Any

from common.aws.s3_client import S3Client


class RawPayloadStore:
    """Thin façade over S3Client used by the ingestion service."""

    def __init__(self, s3_client: S3Client) -> None:
        self._s3_client = s3_client

    def persist(
        self,
        *,
        bucket: str,
        prefix: str,
        source: str,
        payload: dict[str, Any],
        request_id: str,
    ) -> str:
        return self._s3_client.put_raw_payload(
            bucket=bucket,
            prefix=prefix,
            source=source,
            payload=payload,
            request_id=request_id,
        )
