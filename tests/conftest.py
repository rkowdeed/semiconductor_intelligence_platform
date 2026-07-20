"""Shared pytest fixtures.

Tests run entirely offline: AWS services are mocked via `moto`, and the
repository/API tests use an in-memory SQLite database instead of requiring a
live PostgreSQL instance. This lets `pytest` run without `docker compose up`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVICE_ROOT = REPO_ROOT / "ingestion-service"

for path in (str(REPO_ROOT), str(SERVICE_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.pop("AWS_ENDPOINT_URL", None)
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def sample_mes_payload() -> dict:
    return {
        "eventType": "LOT_COMPLETED",
        "lotId": "LOT10001",
        "recipeId": "REC100",
        "equipmentId": "ETCH001",
        "waferCount": 25,
        "temperature": 47.8,
        "timestamp": "2026-07-15T10:30:00Z",
    }


@pytest.fixture
def invalid_mes_payload() -> dict:
    return {
        "eventType": "LOT_COMPLETED",
        "lotId": "LOT10002",
        "recipeId": "REC100",
        "waferCount": "twenty-five",
        "timestamp": "not-a-timestamp",
    }


@pytest.fixture
def sample_erp_payload() -> dict:
    return {
        "eventType": "WORK_ORDER_CREATED",
        "workOrderId": "WO-2026-1001",
        "plant": "FAB-01",
        "priority": "HIGH",
        "timestamp": "2026-07-15T10:30:00Z",
    }


@pytest.fixture
def sample_equipment_payload() -> dict:
    return {
        "eventType": "TOOL_STATUS_CHANGED",
        "equipmentId": "ETCH-TOOL-01",
        "status": "IDLE",
        "chamber": "CH-2",
        "timestamp": "2026-07-15T10:35:00Z",
    }


@pytest.fixture
def sample_plm_payload() -> dict:
    return {
        "eventType": "ECO_RELEASED",
        "changeOrderId": "ECO-2026-0042",
        "partNumber": "PN-AX12-9001",
        "lifecycleState": "RELEASED",
        "owner": "eng_lead",
        "timestamp": "2026-07-15T10:40:00Z",
    }


@pytest.fixture
def sample_file_json_payload() -> dict:
    return {
        "eventType": "FILE_INGESTED",
        "timestamp": "2026-07-20T08:00:00Z",
        "metadata": {
            "sourceSystem": "supplier_portal",
            "fileName": "supplier_orders.json",
            "fileType": "JSON",
            "structure": "ARRAY",
            "contentVersion": "v1.0",
        },
        "file": {
            "content": [
                {"orderId": "SO-100", "quantity": 25, "priority": "HIGH"},
                {"orderId": "SO-101", "quantity": 10, "priority": "LOW"},
            ]
        },
    }


@pytest.fixture
def sample_file_csv_payload() -> dict:
    return {
        "eventType": "FILE_INGESTED",
        "timestamp": "2026-07-20T08:05:00Z",
        "metadata": {
            "sourceSystem": "erp_bulk",
            "fileName": "work_orders.csv",
            "fileType": "CSV",
            "structure": "ROW_BASED",
            "contentVersion": "v2.1",
        },
        "file": {
            "delimiter": ",",
            "hasHeader": True,
            "columns": ["workOrderId", "plant", "priority"],
            "rows": [
                ["WO-1", "FAB-01", "HIGH"],
                ["WO-2", "FAB-02", "MEDIUM"],
            ],
        },
    }


@pytest.fixture
def sample_file_xml_payload() -> dict:
    return {
        "eventType": "FILE_INGESTED",
        "timestamp": "2026-07-20T08:10:00Z",
        "metadata": {
            "sourceSystem": "quality_gateway",
            "fileName": "tool_events.xml",
            "fileType": "XML",
            "structure": "DOCUMENT",
            "contentVersion": "v3",
        },
        "file": {
            "rootTag": "ToolEvents",
            "namespaces": {
                "q": "https://example.org/quality"
            },
            "records": [
                {"toolId": "ETCH-1", "status": "IDLE"},
                {"toolId": "ETCH-2", "status": "RUNNING"},
            ],
        },
    }


@pytest.fixture
def invalid_file_csv_payload() -> dict:
    return {
        "eventType": "FILE_INGESTED",
        "timestamp": "2026-07-20T08:05:00Z",
        "metadata": {
            "sourceSystem": "erp_bulk",
            "fileName": "work_orders.txt",
            "fileType": "CSV",
            "structure": "ROW_BASED",
            "contentVersion": "1.0",
        },
        "file": {
            "delimiter": ",",
            "hasHeader": True,
            "columns": [],
            "rows": [],
        },
    }


@pytest.fixture
def sample_file_multiformat_payload() -> dict:
    return {
        "eventType": "FILE_INGESTED",
        "timestamp": "2026-07-20T09:00:00Z",
        "metadata": {
            "sourceSystem": "fab_gateway",
            "fileName": "fab_equipment.stdf",
            "category": "manufacturing",
            "format": "STDF",
            "contentVersion": "v1.0",
        },
        "file": {
            "contentEncoding": "BASE64",
            "content": "U1RERl9EQVRBX1NBUkxJTkVfMQ==",
        },
    }


@pytest.fixture
def invalid_file_multiformat_payload() -> dict:
    return {
        "eventType": "FILE_INGESTED",
        "timestamp": "2026-07-20T09:00:00Z",
        "metadata": {
            "sourceSystem": "fab_gateway",
            "fileName": "fab_equipment.stdf",
            "category": "manufacturing",
            "format": "Kafka",
            "contentVersion": "v1.0",
        },
        "file": {
            "contentEncoding": "BASE64",
            "content": "U1RERl9EQVRBX1NBUkxJTkVfMQ==",
        },
    }
