"""Tests for data category to format mapping metadata."""

from __future__ import annotations

from common.config.metadata_registry import MetadataRegistry


def test_data_categories_metadata_contains_all_required_categories() -> None:
    registry = MetadataRegistry()
    categories = registry.get_data_categories()

    expected = {
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

    assert expected.issubset(set(categories.keys()))


def test_data_categories_formats_match_expected_matrix() -> None:
    registry = MetadataRegistry()
    categories = registry.get_data_categories()

    expected_formats = {
        "telemetry": {"Protobuf", "MQTT", "Avro", "gRPC"},
        "system_health": {"JSON", "REST", "XML"},
        "logs": {"Syslog", "JSON Logs", "Text"},
        "events": {"JSON", "Kafka", "MQTT"},
        "configuration": {"YAML", "JSON", "XML"},
        "performance": {"Parquet", "CSV"},
        "validation": {"CSV", "HDF5", "XML"},
        "environmental": {"MQTT", "JSON"},
        "design": {"Verilog", "GDSII", "LEF/DEF"},
        "manufacturing": {"STDF", "SECS/GEM", "OPC-UA"},
    }

    for category, formats in expected_formats.items():
        assert category in categories
        assert set(categories[category]["formats"]) == formats


def test_telemetry_and_yield_sources_are_registered() -> None:
    registry = MetadataRegistry()
    sources = registry.get_sources()

    telemetry_source = sources["telemetry"]
    yield_source = sources["yield"]

    assert telemetry_source.input_format == "JSON"
    assert telemetry_source.schema.endswith("telemetry/telemetry_event.json")
    assert yield_source.input_format == "CSV"
    assert yield_source.schema.endswith("yield/yield_event.json")
