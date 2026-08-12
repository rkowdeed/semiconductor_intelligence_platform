"""Thin, reusable wrapper around boto3 Secrets Manager."""

from __future__ import annotations

import json
import os
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from common.exceptions.exceptions import ConfigurationException
from common.logger.logger import get_logger

logger = get_logger(__name__)


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


class SecretsManager:
    """Wraps boto3 Secrets Manager operations."""

    def __init__(
        self,
        endpoint_url: str | None = None,
        region_name: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
    ) -> None:
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
            "secretsmanager",
            **client_kwargs,
        )

    def get_secret(self, secret_name: str) -> dict[str, Any] | str:
        try:
            response = self._client.get_secret_value(SecretId=secret_name)
        except (ClientError, BotoCoreError) as exc:
            raise ConfigurationException(f"Failed to fetch secret {secret_name}: {exc}") from exc

        raw = response.get("SecretString", "{}")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw

    def put_secret(self, secret_name: str, value: dict[str, Any] | str) -> None:
        body = value if isinstance(value, str) else json.dumps(value)
        try:
            try:
                self._client.put_secret_value(SecretId=secret_name, SecretString=body)
            except ClientError:
                self._client.create_secret(Name=secret_name, SecretString=body)
        except (ClientError, BotoCoreError) as exc:
            raise ConfigurationException(f"Failed to write secret {secret_name}: {exc}") from exc
        logger.info("secret_write_success", secret_name=secret_name)
