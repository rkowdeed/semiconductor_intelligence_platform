from __future__ import annotations

from common.ai.intelligence_service import IntelligenceService
from common.governance.governance_service import DataGovernanceService
from common.orchestration.agent_service import AgentOrchestrationService
from common.storage.lakehouse_service import LakehouseCatalogService
from common.traceability.traceability_service import TraceabilityService


def test_governance_service_enforces_access_policy() -> None:
    service = DataGovernanceService()

    policy = service.create_policy(
        asset_class="telemetry",
        subject="analyst",
        operation="read",
        classification="restricted",
    )

    assert policy["subject"] == "analyst"
    assert service.is_allowed("analyst", "telemetry", "read") is True
    assert service.is_allowed("viewer", "telemetry", "read") is False


def test_lakehouse_catalog_registers_asset_metadata() -> None:
    service = LakehouseCatalogService()

    asset = service.register_asset(
        asset_class="telemetry",
        s3_path="s3://semiconductor-lakehouse/raw/telemetry/2026-08-10/part-0001.json",
        source_name="telemetry",
    )

    assert asset["asset_class"] == "telemetry"
    assert asset["source_name"] == "telemetry"
    assert service.list_assets("telemetry")[0]["s3_path"].endswith("part-0001.json")


def test_intelligence_service_indexes_and_searches_documents() -> None:
    service = IntelligenceService()

    document = service.index_document(
        title="Yield review",
        content="Yield improved after tool calibration and recipe tuning.",
        metadata={"source": "yield"},
    )

    results = service.search("tool calibration", limit=3)

    assert document["title"] == "Yield review"
    assert results[0]["document"]["title"] == "Yield review"


def test_traceability_service_registers_lineage() -> None:
    service = TraceabilityService()

    lineage = service.register_lineage(
        lot_id="LOT-1001",
        wafer_id="WAFER-9001",
        process_step_id="STEP-01",
        tool_id="ETCH-01",
        design_version="REV-5",
    )

    assert lineage["lot_id"] == "LOT-1001"
    assert service.get_lineage("LOT-1001")[0]["wafer_id"] == "WAFER-9001"


def test_agent_orchestration_service_tracks_heartbeats() -> None:
    service = AgentOrchestrationService()

    heartbeat = service.record_heartbeat(agent_id="agent-001", status="active")

    assert heartbeat["status"] == "active"
    assert service.list_heartbeats()[0]["agent_id"] == "agent-001"
