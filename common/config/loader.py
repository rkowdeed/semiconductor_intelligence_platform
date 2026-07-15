"""
Configuration loader.

A single, reusable loader used across the platform to load YAML/JSON
configuration and metadata files. Supports ``${VAR:default}`` environment
variable interpolation and caches parsed results so repeated calls for the
same path are cheap.
"""

from __future__ import annotations

import json
import os
import re
import threading
from pathlib import Path
from typing import Any

import yaml

from common.exceptions.exceptions import ConfigurationException

_ENV_VAR_PATTERN = re.compile(r"\$\{([A-Za-z0-9_]+)(:([^}]*))?\}")


class ConfigLoader:
    """Loads and caches YAML/JSON configuration files.

    The loader resolves paths relative to the repository root by default,
    which lets every service reference metadata/config files using the same
    relative paths regardless of the working directory it is started from.
    """

    def __init__(self, root_dir: str | os.PathLike | None = None) -> None:
        self._root_dir = Path(root_dir) if root_dir else self._discover_root()
        self._cache: dict[str, Any] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _discover_root() -> Path:
        """Walk up from this file until a directory containing ``config/``
        and ``metadata/`` is found, falling back to the repo root."""
        current = Path(__file__).resolve()
        for parent in current.parents:
            if (parent / "config").is_dir() and (parent / "metadata").is_dir():
                return parent
        return Path.cwd()

    def resolve_path(self, relative_path: str | os.PathLike) -> Path:
        path = Path(relative_path)
        if path.is_absolute():
            return path
        return self._root_dir / path

    def load(self, relative_path: str, use_cache: bool = True) -> Any:
        """Load a YAML or JSON file, returning a plain Python object."""
        cache_key = str(relative_path)
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        with self._lock:
            if use_cache and cache_key in self._cache:
                return self._cache[cache_key]

            full_path = self.resolve_path(relative_path)
            if not full_path.exists():
                raise ConfigurationException(f"Configuration file not found: {full_path}")

            try:
                raw_text = full_path.read_text(encoding="utf-8")
                if full_path.suffix in (".yaml", ".yml"):
                    data = yaml.safe_load(raw_text)
                elif full_path.suffix == ".json":
                    data = json.loads(raw_text)
                else:
                    raise ConfigurationException(
                        f"Unsupported configuration format: {full_path.suffix}"
                    )
            except (yaml.YAMLError, json.JSONDecodeError) as exc:
                raise ConfigurationException(f"Failed to parse {full_path}: {exc}") from exc

            data = self._interpolate(data)

            if use_cache:
                self._cache[cache_key] = data
            return data

    def clear_cache(self) -> None:
        with self._lock:
            self._cache.clear()

    def _interpolate(self, value: Any) -> Any:
        """Recursively resolve ``${VAR:default}`` references against the
        process environment."""
        if isinstance(value, dict):
            return {k: self._interpolate(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._interpolate(v) for v in value]
        if isinstance(value, str):
            return self._interpolate_string(value)
        return value

    @staticmethod
    def _interpolate_string(value: str) -> Any:
        match = _ENV_VAR_PATTERN.fullmatch(value)
        if match:
            var_name, _, default = match.groups()
            return os.environ.get(var_name, default if default is not None else "")

        def _replace(m: re.Match) -> str:
            var_name, _, default = m.groups()
            return os.environ.get(var_name, default if default is not None else "")

        return _ENV_VAR_PATTERN.sub(_replace, value)


# Module-level singleton for convenient shared use across the codebase.
config_loader = ConfigLoader()
