"""PFP Infrastructure - Verification Statuses Taxonomy.

AuthorityEffect: None.
Canonical specification of dual verification statuses (UNVERIFIED / VERIFIED).
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from pfp.infrastructure.yaml_loading import strict_yaml_load
from pydantic import BaseModel, ConfigDict, Field


def _load_verification_status_enum_members() -> dict[str, str]:
    """Load canonical verification status category identifiers directly from YAML."""
    for candidate_root in [
        Path(__file__).parent.parent / "yaml" / "taxonomy",
    ]:
        reg_file = candidate_root / "verification_statuses.yaml"
        if reg_file.is_file():
            try:
                data = strict_yaml_load(reg_file.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "categories" in data:
                    members = {
                        str(item["id"]): str(item["id"])
                        for item in data["categories"]
                        if isinstance(item, dict) and "id" in item
                    }
                    if members:
                        return members
            except Exception:
                pass
    return {
        "UNVERIFIED": "UNVERIFIED",
        "VERIFIED": "VERIFIED",
    }


VerificationStatusEnum: type[Enum] = Enum(
    "VerificationStatusEnum",
    _load_verification_status_enum_members(),
    type=str,
    module=__name__,
)
VerificationStatusEnum.__doc__ = (
    "Canonical enum of proposal certification statuses loaded directly from YAML."
)


class VerificationStatusDefinition(BaseModel):
    """Strongly typed specification of a verification status."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    id: str = Field(description="Status token (e.g. 'VERIFIED')")
    is_certified: bool = Field(
        default=False, description="Whether proposal is certified by gate receipt"
    )
    description: str = Field(default="", description="Semantic status explanation")


class VerificationStatusRegistry:
    """Catalog of verification statuses loaded from canonical YAML with dynamic extension."""

    _instance: VerificationStatusRegistry | None = None

    def __init__(self) -> None:
        self._statuses: dict[str, VerificationStatusDefinition] = {}
        self._load_canonical()

    @classmethod
    def get_instance(cls) -> VerificationStatusRegistry:
        if cls._instance is None:
            cls._instance = VerificationStatusRegistry()
        return cls._instance

    def _load_canonical(self) -> None:
        for candidate_root in [
            Path(__file__).parent.parent / "yaml" / "taxonomy",
        ]:
            reg_file = candidate_root / "verification_statuses.yaml"
            if reg_file.is_file():
                data = strict_yaml_load(reg_file.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "categories" in data:
                    for item in data["categories"]:
                        try:
                            defn = VerificationStatusDefinition.model_validate(item)
                            self._statuses[defn.id] = defn
                        except Exception:
                            pass
                    break

        if not self._statuses:
            for vs_val in VerificationStatusEnum:
                self._statuses[vs_val.value] = VerificationStatusDefinition(
                    id=vs_val.value,
                    is_certified=vs_val.value == "VERIFIED",
                )

    def register(self, defn: VerificationStatusDefinition) -> None:
        self._statuses[defn.id] = defn

    def is_valid(self, status_id: str) -> bool:
        return status_id in self._statuses

    def all_ids(self) -> frozenset[str]:
        return frozenset(self._statuses.keys())

    def get(self, status_id: str) -> VerificationStatusDefinition | None:
        return self._statuses.get(status_id)


# Pre-resolved constants
VALID_VERIFICATION_STATUSES = VerificationStatusRegistry.get_instance().all_ids()


def get_valid_verification_statuses() -> frozenset[str]:
    return VerificationStatusRegistry.get_instance().all_ids()
