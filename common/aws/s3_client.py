"""Thin, reusable wrapper around boto3 S3 for storing raw payloads."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.client import Config as BotoConfig
from botocore.exceptions import BotoCoreError, ClientError

from common.exceptions.exceptions import StorageException
from common.logger.logger import get_logger

logger = get_logger(__name__)


class S3Client:
    """Wraps boto3 S3 operations needed by the ingestion framework."""

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
            "s3",
            endpoint_url=self._endpoint_url,
            region_name=self._region_name,
            aws_access_key_id=access_key_id or os.environ.get("AWS_ACCESS_KEY_ID", "test"),
            aws_secret_access_key=secret_access_key
            or os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
            config=BotoConfig(s3={"addressing_style": "path"}),
        )

    def ensure_bucket(self, bucket_name: str) -> None:
        try:
            self._client.head_bucket(Bucket=bucket_name)
        except ClientError:
            try:
                self._client.create_bucket(Bucket=bucket_name)
            except (ClientError, BotoCoreError) as exc:
                raise StorageException(f"Failed to create bucket {bucket_name}: {exc}") from exc

    def put_raw_payload(
        self,
        bucket: str,
        prefix: str,
        source: str,
        payload: dict[str, Any],
        request_id: str,
    ) -> str:
        """Persist a raw JSON payload to S3 and return the object key."""
        now = datetime.now(timezone.utc)
        key = (
            f"{prefix}/{now:%Y/%m/%d}/{source}-{request_id}.json"
            if prefix
            else f"{source}/{now:%Y/%m/%d}/{source}-{request_id}.json"
        )
        try:
            self._client.put_object(
                Bucket=bucket,
                Key=key,
                Body=json.dumps(payload).encode("utf-8"),
                ContentType="application/json",
            )
        except (ClientError, BotoCoreError) as exc:
            raise StorageException(f"Failed to upload payload to s3://{bucket}/{key}: {exc}") from exc

        logger.info("s3_upload_success", bucket=bucket, key=key)
        return key

    def object_exists(self, bucket: str, key: str) -> bool:
        try:
            self._client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False

    def healthcheck(self) -> bool:
        try:
            self._client.list_buckets()
            return True
        except (ClientError, BotoCoreError):
            return False
