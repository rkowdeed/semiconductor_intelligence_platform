"""Thin, reusable wrapper around boto3 CloudWatch Logs."""

from __future__ import annotations

import os
import time
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from common.logger.logger import get_logger

logger = get_logger(__name__)


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


class CloudWatchLogger:
    """Wraps boto3 CloudWatch Logs operations. Failures here are logged but
    never raised, since telemetry delivery should not break ingestion."""

    def __init__(
        self,
        log_group: str = "/sap/ingestion-service",
        log_stream: str = "application",
        endpoint_url: str | None = None,
        region_name: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
    ) -> None:
        self._log_group = log_group
        self._log_stream = log_stream
        self._sequence_token: str | None = None
        resolved_endpoint = (
            _clean_optional(endpoint_url)
            if endpoint_url is not None
            else _clean_optional(os.environ.get("AWS_ENDPOINT_URL"))
        )
        resolved_access_key = _clean_optional(
            access_key_id if access_key_id is not None else os.environ.get("AWS_ACCESS_KEY_ID")
        )
        resolved_secret_key = _clean_optional(
            secret_access_key
            if secret_access_key is not None
            else os.environ.get("AWS_SECRET_ACCESS_KEY")
        )
        client_kwargs: dict[str, Any] = {
            "endpoint_url": resolved_endpoint,
            "region_name": region_name or os.environ.get("AWS_REGION", "us-east-1"),
        }
        if resolved_access_key and resolved_secret_key:
            client_kwargs["aws_access_key_id"] = resolved_access_key
            client_kwargs["aws_secret_access_key"] = resolved_secret_key
        self._client = boto3.client(
            "logs",
            **client_kwargs,
        )

    def ensure_log_group(self) -> None:
        try:
            self._client.create_log_group(logGroupName=self._log_group)
        except ClientError:
            pass
        try:
            self._client.create_log_stream(
                logGroupName=self._log_group, logStreamName=self._log_stream
            )
        except ClientError:
            pass

    def log(self, message: str, extra: dict[str, Any] | None = None) -> None:
        try:
            self._client.put_log_events(
                logGroupName=self._log_group,
                logStreamName=self._log_stream,
                logEvents=[
                    {
                        "timestamp": int(time.time() * 1000),
                        "message": message if not extra else f"{message} | {extra}",
                    }
                ],
            )
        except (ClientError, BotoCoreError) as exc:
            logger.warning("cloudwatch_log_failed", error=str(exc))
