"""Tests for the reusable configuration loader."""

from __future__ import annotations

import os

import pytest

from common.config.loader import ConfigLoader
from common.exceptions.exceptions import ConfigurationException


@pytest.fixture
def loader() -> ConfigLoader:
    return ConfigLoader()


def test_loads_yaml_file(loader: ConfigLoader) -> None:
    data = loader.load("config/application.yaml")
    assert data["app"]["name"] == "Semiconductor_Operations_Data_Platform"


def test_loads_json_schema_file(loader: ConfigLoader) -> None:
    data = loader.load("schemas/mes/lot_completed.json")
    assert data["title"] == "MES Lot Completed Event"


def test_missing_file_raises(loader: ConfigLoader) -> None:
    with pytest.raises(ConfigurationException):
        loader.load("config/does_not_exist.yaml")


def test_env_var_interpolation_with_default(loader: ConfigLoader) -> None:
    os.environ.pop("AWS_REGION", None)
    data = loader.load("config/aws.yaml", use_cache=False)
    assert data["aws"]["region"] == "us-east-1"


def test_env_var_interpolation_with_override(loader: ConfigLoader) -> None:
    os.environ["AWS_REGION"] = "eu-west-1"
    try:
        data = loader.load("config/aws.yaml", use_cache=False)
        assert data["aws"]["region"] == "eu-west-1"
    finally:
        os.environ["AWS_REGION"] = "us-east-1"


def test_caching_returns_same_object(loader: ConfigLoader) -> None:
    first = loader.load("config/database.yaml")
    second = loader.load("config/database.yaml")
    assert first is second


def test_clear_cache_forces_reload(loader: ConfigLoader) -> None:
    first = loader.load("config/database.yaml")
    loader.clear_cache()
    second = loader.load("config/database.yaml")
    assert first is not second
    assert first == second
