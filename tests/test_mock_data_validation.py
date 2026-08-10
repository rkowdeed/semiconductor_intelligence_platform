from __future__ import annotations

import json
from pathlib import Path


def test_telemetry_sample_payload_matches_schema() -> None:
    sample_path = Path("sample-data/telemetry/telemetry_sample.json")
    payload = json.loads(sample_path.read_text(encoding="utf-8"))

    assert payload["eventType"] == "TELEMETRY_CAPTURED"
    assert payload["metrics"]["temperature"] > 0


def test_yield_sample_payload_is_parseable_csv() -> None:
    sample_path = Path("sample-data/yield/yield_sample.csv")
    lines = [line.strip() for line in sample_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert len(lines) == 2
    assert lines[0].startswith("eventType")
    assert lines[1].startswith("YIELD_EVENT")
