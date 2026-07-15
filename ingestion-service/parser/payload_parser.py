"""Generic payload parsing for incoming ingestion requests."""

from __future__ import annotations

import json
from typing import Any

from common.exceptions.exceptions import ValidationException


class PayloadParser:
    """Parses raw request bodies into plain dictionaries.

    Kept generic (source-agnostic) so new sources never require a new
    parser implementation - only new metadata/schema entries.
    """

    @staticmethod
    def parse(raw_body: bytes | str | dict[str, Any]) -> dict[str, Any]:
        if isinstance(raw_body, dict):
            return raw_body
        try:
            if isinstance(raw_body, bytes):
                raw_body = raw_body.decode("utf-8")
            return json.loads(raw_body)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValidationException(f"Request body is not valid JSON: {exc}") from exc
