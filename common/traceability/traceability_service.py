"""Traceability spine scaffold for linking wafers, lots, tools, and design versions."""

from __future__ import annotations

from typing import Any


class TraceabilityService:
    """Stores lightweight lineage records for semiconductor traceability."""

    def __init__(self) -> None:
        self._lineage: list[dict[str, Any]] = []

    def register_lineage(
        self,
        *,
        lot_id: str,
        wafer_id: str,
        process_step_id: str,
        tool_id: str,
        design_version: str,
    ) -> dict[str, Any]:
        record = {
            "lot_id": lot_id,
            "wafer_id": wafer_id,
            "process_step_id": process_step_id,
            "tool_id": tool_id,
            "design_version": design_version,
        }
        self._lineage.append(record)
        return record

    def get_lineage(self, lot_id: str) -> list[dict[str, Any]]:
        return [record for record in self._lineage if record["lot_id"] == lot_id]
