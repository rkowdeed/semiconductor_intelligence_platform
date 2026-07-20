"""Generic payload parsing for incoming ingestion requests."""

from __future__ import annotations

from typing import Any

from parser.format_parser_registry import format_parser_registry


class PayloadParser:
    """Parses raw request bodies into plain dictionaries.

    Kept generic (source-agnostic) so new sources never require a new
    parser implementation - only new metadata/schema entries.
    """

    @staticmethod
    def parse(raw_body: bytes | str | dict[str, Any]) -> dict[str, Any]:
        return PayloadParser.parse_with_format(raw_body)

    @staticmethod
    def parse_with_format(
        raw_body: bytes | str | dict[str, Any],
        *,
        content_type: str | None = None,
        source_format: str | None = None,
    ) -> dict[str, Any]:
        if isinstance(raw_body, dict):
            return raw_body

        # Default behavior remains JSON for backward compatibility, while
        # allowing metadata/content-type driven format conversion.
        return format_parser_registry.parse(
            raw_body,
            content_type=content_type,
            source_format=source_format,
        )
