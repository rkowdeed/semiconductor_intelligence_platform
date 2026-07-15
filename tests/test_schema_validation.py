"""Tests for JSON Schema payload validation."""

from __future__ import annotations

import pytest

from common.exceptions.exceptions import ValidationException
from common.validation.validator import SchemaValidator


@pytest.fixture
def validator() -> SchemaValidator:
    return SchemaValidator()


def test_valid_payload_passes(validator: SchemaValidator, sample_mes_payload: dict) -> None:
    validator.validate(sample_mes_payload, "schemas/mes/lot_completed.json")


def test_valid_erp_payload_passes(validator: SchemaValidator, sample_erp_payload: dict) -> None:
    validator.validate(sample_erp_payload, "schemas/erp/work_order.json")


def test_valid_equipment_payload_passes(
    validator: SchemaValidator, sample_equipment_payload: dict
) -> None:
    validator.validate(sample_equipment_payload, "schemas/equipment/equipment_event.json")


def test_valid_plm_payload_passes(validator: SchemaValidator, sample_plm_payload: dict) -> None:
    validator.validate(sample_plm_payload, "schemas/plm/product_lifecycle_event.json")


def test_invalid_payload_raises(validator: SchemaValidator, invalid_mes_payload: dict) -> None:
    with pytest.raises(ValidationException) as exc_info:
        validator.validate(invalid_mes_payload, "schemas/mes/lot_completed.json")
    assert "errors" in exc_info.value.details


def test_missing_required_field_raises(validator: SchemaValidator, sample_mes_payload: dict) -> None:
    payload = dict(sample_mes_payload)
    del payload["lotId"]
    with pytest.raises(ValidationException):
        validator.validate(payload, "schemas/mes/lot_completed.json")


def test_wrong_event_type_raises(validator: SchemaValidator, sample_mes_payload: dict) -> None:
    payload = dict(sample_mes_payload)
    payload["eventType"] = "LOT_STARTED"
    with pytest.raises(ValidationException):
        validator.validate(payload, "schemas/mes/lot_completed.json")


def test_schema_is_cached(validator: SchemaValidator, sample_mes_payload: dict) -> None:
    validator.validate(sample_mes_payload, "schemas/mes/lot_completed.json")
    assert "schemas/mes/lot_completed.json" in validator._schema_cache


def test_missing_schema_file_raises(validator: SchemaValidator, sample_mes_payload: dict) -> None:
    with pytest.raises(ValidationException):
        validator.validate(sample_mes_payload, "schemas/does_not_exist.json")
