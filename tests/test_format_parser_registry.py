"""Tests for format parser registry conversions."""

from __future__ import annotations

from parser.format_parser_registry import format_parser_registry


def test_parse_xml_to_dict() -> None:
    raw = b"<health><status>UP</status><host>node-1</host></health>"
    parsed = format_parser_registry.parse(raw, content_type="application/xml", source_format="AUTO")

    assert "health" in parsed
    assert parsed["health"]["status"] == "UP"
    assert parsed["health"]["host"] == "node-1"


def test_parse_csv_to_rows() -> None:
    raw = b"workOrderId,priority\nWO-1,HIGH\nWO-2,LOW\n"
    parsed = format_parser_registry.parse(raw, content_type="text/csv", source_format="AUTO")

    assert parsed["columns"] == ["workOrderId", "priority"]
    assert parsed["row_count"] == 2
    assert parsed["rows"][0]["workOrderId"] == "WO-1"


def test_parse_plain_text() -> None:
    raw = b"driver started"
    parsed = format_parser_registry.parse(raw, content_type="text/plain", source_format="AUTO")

    assert parsed == {"text": "driver started"}


def test_parse_binary_passthrough_for_protobuf() -> None:
    raw = b"\x08\x96\x01"
    parsed = format_parser_registry.parse(raw, source_format="PROTOBUF")

    assert "content_base64" in parsed
