"""Normalize raw non-JSON files in S3 into JSON objects for downstream use."""

from __future__ import annotations

from pathlib import Path

from common.aws.s3_client import S3Client
from parser.format_parser_registry import format_parser_registry


_EXTENSION_TO_FORMAT = {
    ".json": "JSON",
    ".xml": "XML",
    ".csv": "CSV",
    ".txt": "TEXT",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".parquet": "PARQUET",
    ".h5": "HDF5",
    ".hdf5": "HDF5",
}


class S3NormalizationService:
    def __init__(self, s3_client: S3Client) -> None:
        self._s3_client = s3_client

    @staticmethod
    def _infer_format_from_key(key: str, fallback_format: str | None) -> str:
        suffix = Path(key).suffix.lower()
        if suffix in _EXTENSION_TO_FORMAT:
            return _EXTENSION_TO_FORMAT[suffix]
        return fallback_format or "JSON"

    def normalize_prefix(
        self,
        *,
        bucket: str,
        source_prefix: str,
        normalized_prefix: str,
        source_format: str | None = None,
        limit: int | None = None,
    ) -> list[str]:
        keys = self._s3_client.list_object_keys(bucket, source_prefix)
        normalized_keys: list[str] = []

        for key in keys:
            if key.endswith("/"):
                continue
            if key.startswith(f"{normalized_prefix.rstrip('/')}/"):
                continue

            effective_format = self._infer_format_from_key(key, source_format)
            raw_bytes = self._s3_client.get_object_bytes(bucket, key)
            payload = format_parser_registry.parse(raw_bytes, source_format=effective_format)

            normalized_name = f"{Path(key).stem}.json"
            output_key = f"{normalized_prefix.rstrip('/')}/{normalized_name}"
            self._s3_client.put_json_payload(bucket, output_key, payload)
            normalized_keys.append(output_key)

            if limit is not None and len(normalized_keys) >= limit:
                break

        return normalized_keys
