"""Tests for the FastAPI REST API surface: MES ingestion, health, config."""

from __future__ import annotations

import json

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from common.models.base import Base


@pytest.fixture
def client():
    with mock_aws():
        # Bootstrap the mocked AWS resources the ingestion flow expects.
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="semiconductor-landing")

        kinesis = boto3.client("kinesis", region_name="us-east-1")
        for stream in ("mes-events", "metadata-events", "quality-events", "plm-events"):
            kinesis.create_stream(StreamName=stream, ShardCount=1)
            kinesis.get_waiter("stream_exists").wait(StreamName=stream)

        # In-memory SQLite standing in for PostgreSQL.
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        @event.listens_for(engine, "connect")
        def _attach_schemas(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            for schema in ("mdm", "metadata", "quality"):
                cursor.execute(f"ATTACH DATABASE ':memory:' AS {schema}")
            cursor.close()

        Base.metadata.create_all(engine)
        TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

        from api.dependencies import get_db_session, get_kinesis_publisher, get_s3_client
        from common.aws.kinesis_publisher import KinesisPublisher
        from common.aws.s3_client import S3Client
        from main import app

        def override_get_db_session():
            db = TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db_session] = override_get_db_session
        app.dependency_overrides[get_s3_client] = lambda: S3Client(
            endpoint_url=None, region_name="us-east-1"
        )
        app.dependency_overrides[get_kinesis_publisher] = lambda: KinesisPublisher(
            endpoint_url=None, region_name="us-east-1"
        )

        with TestClient(app) as test_client:
            yield test_client

        app.dependency_overrides.clear()


def test_health_endpoint_returns_ok(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "UP"
    for component in ("database", "aws", "kinesis", "s3", "application"):
        assert body["components"][component]["status"] == "UP"


def test_ready_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "READY"}


def test_swagger_docs_available(client: TestClient) -> None:
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema_available(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "paths" in response.json()


def test_config_sources_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/config/sources")
    assert response.status_code == 200
    names = [s["name"] for s in response.json()]
    assert "mes" in names


def test_validation_ui_page_is_available(client: TestClient) -> None:
    response = client.get("/ui/validate")
    assert response.status_code == 200
    assert "Validate ingestion output" in response.text


def test_validation_ui_submit_returns_pipeline_evidence(client: TestClient, sample_mes_payload: dict) -> None:
    response = client.post(
        "/api/v1/ui/validate",
        json={
            "source": "mes",
            "content_type": "application/json",
            "payload": sample_mes_payload,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ingestion"]["source"] == "mes"
    assert body["ingestion"]["status"] == "ACCEPTED"
    assert body["postgresql"]["table"] in {"mdm.lot_master", "metadata.raw_events"}
    assert body["kinesis"]["stream"] == "mes-events"


def test_config_streams_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/config/streams")
    assert response.status_code == 200
    names = [s["logical_name"] for s in response.json()]
    assert "mes" in names


def test_config_data_categories_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/config/data-categories")
    assert response.status_code == 200
    categories = {item["category"]: item for item in response.json()}
    assert "manufacturing" in categories
    assert "STDF" in categories["manufacturing"]["formats"]
    assert "telemetry" in categories
    assert "Protobuf" in categories["telemetry"]["formats"]


def test_post_valid_mes_event_returns_202(client: TestClient, sample_mes_payload: dict) -> None:
    response = client.post("/api/v1/mes/events", json=sample_mes_payload)
    assert response.status_code == 202
    body = response.json()
    assert body["source"] == "mes"
    assert body["status"] == "ACCEPTED"
    assert body["s3_key"].startswith("mes/")
    assert body["stream"] == "mes-events"
    assert body["curated_record_id"] is not None


def test_post_valid_erp_event_returns_202(client: TestClient, sample_erp_payload: dict) -> None:
    response = client.post("/api/v1/erp/events", json=sample_erp_payload)
    assert response.status_code == 202
    body = response.json()
    assert body["source"] == "erp"
    assert body["status"] == "ACCEPTED"
    assert body["s3_key"].startswith("erp/")
    assert body["stream"] == "metadata-events"
    assert body["curated_record_id"] is not None


def test_post_valid_equipment_event_returns_202(
    client: TestClient, sample_equipment_payload: dict
) -> None:
    response = client.post("/api/v1/equipment/events", json=sample_equipment_payload)
    assert response.status_code == 202
    body = response.json()
    assert body["source"] == "equipment"
    assert body["status"] == "ACCEPTED"
    assert body["s3_key"].startswith("equipment/")
    assert body["stream"] == "quality-events"
    assert body["curated_record_id"] is not None


def test_post_valid_plm_event_returns_202(client: TestClient, sample_plm_payload: dict) -> None:
    response = client.post("/api/v1/plm/events", json=sample_plm_payload)
    assert response.status_code == 202
    body = response.json()
    assert body["source"] == "plm"
    assert body["status"] == "ACCEPTED"
    assert body["s3_key"].startswith("plm/")
    assert body["stream"] == "plm-events"
    assert body["curated_record_id"] is not None


def test_post_valid_multiformat_event_returns_202(
    client: TestClient, sample_file_multiformat_payload: dict
) -> None:
    response = client.post("/api/v1/files/multiformat/events", json=sample_file_multiformat_payload)
    assert response.status_code == 202
    body = response.json()
    assert body["source"] == "file_multiformat"
    assert body["status"] == "ACCEPTED"
    assert body["s3_key"].startswith("files/multiformat/")
    assert body["stream"] == "metadata-events"
    assert body["curated_record_id"] is not None


def test_post_invalid_mes_event_returns_400(client: TestClient, invalid_mes_payload: dict) -> None:
    response = client.post("/api/v1/mes/events", json=invalid_mes_payload)
    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "ValidationException"


def test_post_malformed_json_returns_400(client: TestClient) -> None:
    response = client.post(
        "/api/v1/mes/events",
        content=b"{not valid json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400


def test_post_xml_body_is_converted_before_ingestion(client: TestClient) -> None:
    from api.dependencies import get_ingestion_service
    from main import app

    captured: dict[str, object] = {}

    class _FakeResult:
        request_id = "req-xml"
        source = "mes"
        s3_key = "mes/2026/07/20/mes-req-xml.json"
        stream = "mes-events"
        sequence_number = "1"
        curated_record_id = "1"

    class _FakeIngestionService:
        def ingest(self, source_name, raw_body, session):
            captured["source_name"] = source_name
            captured["raw_body"] = raw_body
            return _FakeResult()

    app.dependency_overrides[get_ingestion_service] = lambda: _FakeIngestionService()
    try:
        xml_payload = b"<mes><eventType>LOT_COMPLETED</eventType><lotId>LOT10001</lotId></mes>"
        response = client.post(
            "/api/v1/mes/events",
            content=xml_payload,
            headers={"Content-Type": "application/xml"},
        )
        assert response.status_code == 202
        assert captured["source_name"] == "mes"
        assert isinstance(captured["raw_body"], dict)
        assert "mes" in captured["raw_body"]
    finally:
        app.dependency_overrides.pop(get_ingestion_service, None)
