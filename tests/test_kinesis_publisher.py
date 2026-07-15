"""Tests for the KinesisPublisher wrapper, mocked via moto."""

from __future__ import annotations

import pytest
from moto import mock_aws

from common.aws.kinesis_publisher import KinesisPublisher


@pytest.fixture
def kinesis_publisher():
    with mock_aws():
        publisher = KinesisPublisher(endpoint_url=None, region_name="us-east-1")
        publisher.ensure_stream("mes-events", shard_count=1)
        yield publisher


def test_ensure_stream_is_idempotent(kinesis_publisher: KinesisPublisher) -> None:
    kinesis_publisher.ensure_stream("mes-events", shard_count=1)


def test_publish_returns_sequence_number(
    kinesis_publisher: KinesisPublisher, sample_mes_payload: dict
) -> None:
    response = kinesis_publisher.publish("mes-events", "partition-1", sample_mes_payload)
    assert "SequenceNumber" in response
    assert "ShardId" in response


def test_healthcheck_true_when_reachable(kinesis_publisher: KinesisPublisher) -> None:
    assert kinesis_publisher.healthcheck() is True


def test_publish_to_missing_stream_raises(kinesis_publisher: KinesisPublisher, sample_mes_payload: dict) -> None:
    from common.exceptions.exceptions import KinesisException

    with pytest.raises(KinesisException):
        kinesis_publisher.publish("does-not-exist", "partition-1", sample_mes_payload)
