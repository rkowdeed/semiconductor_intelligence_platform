"""Lakehouse catalog scaffolding for landing raw assets in S3 and tracking metadata."""

from __future__ import annotations

from typing import Any


class LakehouseCatalogService:
    """Maintains a simple metadata catalog for lakehouse assets in S3."""

    def __init__(self) -> None:
        self._assets: list[dict[str, Any]] = []

    def register_asset(self, *, asset_class: str, s3_path: str, source_name: str) -> dict[str, Any]:
        asset = {
            "asset_class": asset_class,
            "s3_path": s3_path,
            "source_name": source_name,
            "registered": True,
        }
        self._assets.append(asset)
        return asset

    def list_assets(self, asset_class: str | None = None) -> list[dict[str, Any]]:
        if asset_class is None:
            return list(self._assets)
        return [asset for asset in self._assets if asset["asset_class"] == asset_class]
