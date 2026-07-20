"""Tests for S3 raw file normalization service."""

from __future__ import annotations

import json
from pathlib import Path

import boto3
from moto import mock_aws

from common.aws.s3_client import S3Client
from services.s3_normalization_service import S3NormalizationService


def test_normalize_prefix_converts_xml_csv_and_text_files() -> None:
    with mock_aws():
        bucket = "semiconductor-landing"
        raw = boto3.client("s3", region_name="us-east-1")
        raw.create_bucket(Bucket=bucket)

        raw.put_object(
            Bucket=bucket,
            Key="incoming/health.xml",
            Body=b"<health><status>UP</status></health>",
            ContentType="application/xml",
        )
        raw.put_object(
            Bucket=bucket,
            Key="incoming/work_orders.csv",
            Body=b"id,priority\\nWO-1,HIGH\\n",
            ContentType="text/csv",
        )
        raw.put_object(
            Bucket=bucket,
            Key="incoming/driver.txt",
            Body=b"driver started",
            ContentType="text/plain",
        )

        service = S3NormalizationService(S3Client(endpoint_url=None, region_name="us-east-1"))
        normalized = service.normalize_prefix(
            bucket=bucket,
            source_prefix="incoming/",
            normalized_prefix="normalized/",
            source_format="AUTO",
        )

        assert len(normalized) == 3
        assert "normalized/health.json" in normalized
        assert "normalized/work_orders.json" in normalized
        assert "normalized/driver.json" in normalized

        body = raw.get_object(Bucket=bucket, Key="normalized/health.json")["Body"].read()
        parsed = json.loads(body)
        assert parsed["health"]["status"] == "UP"


def test_normalize_native_sample_files_from_repo(repo_root: Path) -> None:
    with mock_aws():
        bucket = "semiconductor-landing"
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=bucket)

        native_dir = repo_root / "sample-data" / "files" / "native"
        files_to_upload = {
            "incoming/system_health_sample.xml": native_dir / "system_health_sample.xml",
            "incoming/work_orders_sample.csv": native_dir / "work_orders_sample.csv",
            "incoming/driver_logs_sample.txt": native_dir / "driver_logs_sample.txt",
            "incoming/benchmark_sample.parquet": native_dir / "benchmark_sample.parquet",
        }

        for key, file_path in files_to_upload.items():
            s3.put_object(Bucket=bucket, Key=key, Body=file_path.read_bytes())

        service = S3NormalizationService(S3Client(endpoint_url=None, region_name="us-east-1"))
        normalized_keys = service.normalize_prefix(
            bucket=bucket,
            source_prefix="incoming/",
            normalized_prefix="normalized/",
            source_format="AUTO",
        )

        assert len(normalized_keys) == 4

        xml_payload = json.loads(
            s3.get_object(Bucket=bucket, Key="normalized/system_health_sample.json")["Body"].read()
        )
        assert xml_payload["health"]["status"] == "UP"

        csv_payload = json.loads(
            s3.get_object(Bucket=bucket, Key="normalized/work_orders_sample.json")["Body"].read()
        )
        assert csv_payload["row_count"] == 2

        txt_payload = json.loads(
            s3.get_object(Bucket=bucket, Key="normalized/driver_logs_sample.json")["Body"].read()
        )
        assert "driver initialized" in txt_payload["text"]

        parquet_payload = json.loads(
            s3.get_object(Bucket=bucket, Key="normalized/benchmark_sample.json")["Body"].read()
        )
        assert "content_base64" in parquet_payload
