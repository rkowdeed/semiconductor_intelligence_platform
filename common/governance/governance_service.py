"""Lightweight access-control and governance service for IP-sensitive semiconductor data."""

from __future__ import annotations

from typing import Any


class DataGovernanceService:
    """Provides role-based access checks and simple policy registration."""

    def __init__(self) -> None:
        self._policies: list[dict[str, Any]] = []
        self._default_allow = False

    def create_policy(
        self,
        *,
        asset_class: str,
        subject: str,
        operation: str,
        classification: str,
    ) -> dict[str, Any]:
        policy = {
            "asset_class": asset_class,
            "subject": subject,
            "operation": operation,
            "classification": classification,
        }
        self._policies.append(policy)
        return policy

    def is_allowed(self, subject: str, asset_class: str, operation: str) -> bool:
        for policy in self._policies:
            if (
                policy["asset_class"] == asset_class
                and policy["subject"] == subject
                and policy["operation"] == operation
            ):
                return True
        return self._default_allow

    def list_policies(self) -> list[dict[str, Any]]:
        return list(self._policies)
