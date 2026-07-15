"""Thin, reusable wrapper around boto3 Kinesis for event publishing."""

from __future__ import annotations

import json
import os
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from common.exceptions.exceptions import KinesisException
from common.logger.logger import get_logger

logger = get_logger(__name__)


class KinesisPublisher:
    """Wraps boto3 Kinesis operations needed by the ingestion framework."""

    def __init__(
        self,
        endpoint_url: str | None = None,
        region_name: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
    ) -> None:
        self._endpoint_url = (
            endpoint_url if endpoint_url is not None else os.environ.get("AWS_ENDPOINT_URL")
        )
        self._region_name = region_name or os.environ.get("AWS_REGION", "us-east-1")
        self._client = boto3.client(
            "kinesis",
            endpoint_url=self._endpoint_url,
            region_name=self._region_name,
            aws_access_key_id=access_key_id or os.environ.get("AWS_ACCESS_KEY_ID", "test"),
            aws_secret_access_key=secret_access_key
            or os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
        )

    def ensure_stream(self, stream_name: str, shard_count: int = 1) -> None:
        try:
            self._client.describe_stream(StreamName=stream_name)
        except ClientError:
            try:
                self._client.create_stream(StreamName=stream_name, ShardCount=shard_count)
                waiter = self._client.get_waiter("stream_exists")
                waiter.wait(StreamName=stream_name)
            except (ClientError, BotoCoreError) as exc:
                raise KinesisException(f"Failed to create stream {stream_name}: {exc}") from exc

    def publish(
        self,
        stream_name: str,
        partition_key: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            response = self._client.put_record(
                StreamName=stream_name,
                Data=json.dumps(payload).encode("utf-8"),
                PartitionKey=partition_key,
            )
        except (ClientError, BotoCoreError) as exc:
            raise KinesisException(
                f"Failed to publish event to stream {stream_name}: {exc}"
            ) from exc

        logger.info(
            "kinesis_publish_success",
            stream=stream_name,
            shard_id=response.get("ShardId"),
            sequence_number=response.get("SequenceNumber"),
        )
        return response

    def healthcheck(self) -> bool:
        try:
            self._client.list_streams(Limit=1)
            return True
        except (ClientError, BotoCoreError):
            return False
