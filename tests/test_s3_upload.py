"""Tests for the S3Client wrapper, mocked via moto."""

from __future__ import annotations

import json

import boto3
import pytest
from moto import mock_aws

from common.aws.s3_client import S3Client


@pytest.fixture
def s3_client():
    with mock_aws():
        client = S3Client(endpoint_url=None, region_name="us-east-1")
        client.ensure_bucket("semiconductor-landing")
        yield client


def test_ensure_bucket_creates_bucket(s3_client: S3Client) -> None:
    assert s3_client.object_exists("semiconductor-landing", "non-existent-key") is False


def test_put_raw_payload_uploads_object(s3_client: S3Client, sample_mes_payload: dict) -> None:
    key = s3_client.put_raw_payload(
        bucket="semiconductor-landing",
        prefix="mes",
        source="mes",
        payload=sample_mes_payload,
        request_id="req-123",
    )
    assert key.startswith("mes/")
    assert key.endswith("mes-req-123.json")
    assert s3_client.object_exists("semiconductor-landing", key) is True


def test_uploaded_payload_round_trips(s3_client: S3Client, sample_mes_payload: dict) -> None:
    key = s3_client.put_raw_payload(
        bucket="semiconductor-landing",
        prefix="mes",
        source="mes",
        payload=sample_mes_payload,
        request_id="req-456",
    )
    raw_client = boto3.client("s3", region_name="us-east-1")
    obj = raw_client.get_object(Bucket="semiconductor-landing", Key=key)
    body = json.loads(obj["Body"].read())
    assert body == sample_mes_payload


def test_healthcheck_true_when_reachable(s3_client: S3Client) -> None:
    assert s3_client.healthcheck() is True
