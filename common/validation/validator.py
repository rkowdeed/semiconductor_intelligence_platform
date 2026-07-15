"""JSON Schema payload validation."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema.validators import validator_for

from common.config.loader import config_loader
from common.exceptions.exceptions import ValidationException


class SchemaValidator:
    """Validates payloads against JSON Schema files, with schema caching."""

    def __init__(self) -> None:
        self._schema_cache: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def _load_schema(self, schema_path: str) -> dict[str, Any]:
        if schema_path in self._schema_cache:
            return self._schema_cache[schema_path]

        with self._lock:
            if schema_path in self._schema_cache:
                return self._schema_cache[schema_path]

            full_path = config_loader.resolve_path(schema_path)
            if not full_path.exists():
                raise ValidationException(f"Schema file not found: {full_path}")

            try:
                schema = json.loads(Path(full_path).read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ValidationException(f"Invalid JSON schema at {full_path}: {exc}") from exc

            self._schema_cache[schema_path] = schema
            return schema

    def validate(self, payload: dict[str, Any], schema_path: str) -> None:
        """Validate a payload; raises ValidationException with all errors
        collected if the payload does not conform to the schema."""
        schema = self._load_schema(schema_path)
        validator_cls = validator_for(schema)
        validator_cls.check_schema(schema)
        validator = validator_cls(schema)

        errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
        if errors:
            error_details = [
                {
                    "path": ".".join(str(p) for p in error.path) or "<root>",
                    "message": error.message,
                }
                for error in errors
            ]
            raise ValidationException(
                "Payload failed schema validation",
                details={"errors": error_details, "schema": schema_path},
            )


schema_validator = SchemaValidator()
