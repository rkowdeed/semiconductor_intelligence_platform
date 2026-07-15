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
