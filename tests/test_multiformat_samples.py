"""Tests for sample-data multi-format payloads."""

from __future__ import annotations

import json
from pathlib import Path

from common.validation.validator import SchemaValidator


def test_all_multiformat_sample_files_validate(repo_root: Path) -> None:
    validator = SchemaValidator()
    sample_dir = repo_root / "sample-data" / "files" / "multiformat"
    sample_files = sorted(sample_dir.glob("*_sample.json"))

    assert sample_files, "No sample files found in sample-data/files/multiformat"

    for sample_file in sample_files:
        payload = json.loads(sample_file.read_text(encoding="utf-8"))
        validator.validate(payload, "schemas/files/file_multiformat_event.json")


def test_multiformat_samples_cover_all_categories(repo_root: Path) -> None:
    sample_dir = repo_root / "sample-data" / "files" / "multiformat"
    sample_files = sorted(sample_dir.glob("*_sample.json"))

    categories = set()
    for sample_file in sample_files:
        payload = json.loads(sample_file.read_text(encoding="utf-8"))
        categories.add(payload["metadata"]["category"])

    expected_categories = {
        "telemetry",
        "system_health",
        "logs",
        "events",
        "configuration",
        "performance",
        "validation",
        "environmental",
        "design",
        "manufacturing",
    }

    assert categories == expected_categories
