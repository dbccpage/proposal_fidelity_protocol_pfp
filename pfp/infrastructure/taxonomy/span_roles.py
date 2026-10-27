"""PFP Infrastructure - Byte Span Roles Taxonomy.

AuthorityEffect: None.
Canonical specification of byte span and prompt segment functional roles under SPK-001.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from pfp.infrastructure.yaml_loading import strict_yaml_load
from pydantic import BaseModel, ConfigDict, Field


def _load_span_role_enum_members() -> dict[str, str]:
    """Load canonical span role category identifiers directly from YAML."""
    for candidate_root in [
        Path(__file__).parent.parent / "yaml" / "taxonomy",
    ]:
        reg_file = candidate_root / "span_roles.yaml"
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
        "PREAMBLE": "PREAMBLE",
        "GROUND_TRUTH": "GROUND_TRUTH",
        "STIMULUS": "STIMULUS",
        "PROMPT_BODY": "PROMPT_BODY",
        "FENCE": "FENCE",
        "EPILOGUE": "EPILOGUE",
    }


SpanRoleEnum: type[Enum] = Enum(
    "SpanRoleEnum",
    _load_span_role_enum_members(),
    type=str,
    module=__name__,
)
SpanRoleEnum.__doc__ = "Canonical enum of byte span functional roles loaded directly from YAML."


class SpanRoleDefinition(BaseModel):
    """Strongly typed specification of a byte span functional role."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    id: str = Field(description="Span role token (e.g. 'STIMULUS')")
    is_protected: bool = Field(
        default=False, description="Whether span contains withheld truth or fence boundaries"
    )
    description: str = Field(default="", description="Functional purpose of this segment")


class SpanRoleRegistry:
    """Catalog of byte span functional roles loaded from canonical YAML with dynamic extension."""

    _instance: SpanRoleRegistry | None = None

    def __init__(self) -> None:
        self._roles: dict[str, SpanRoleDefinition] = {}
        self._load_canonical()

    @classmethod
    def get_instance(cls) -> SpanRoleRegistry:
        if cls._instance is None:
            cls._instance = SpanRoleRegistry()
        return cls._instance

    def _load_canonical(self) -> None:
        for candidate_root in [
            Path(__file__).parent.parent / "yaml" / "taxonomy",
        ]:
            reg_file = candidate_root / "span_roles.yaml"
            if reg_file.is_file():
                data = strict_yaml_load(reg_file.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "categories" in data:
                    for item in data["categories"]:
                        try:
                            defn = SpanRoleDefinition.model_validate(item)
                            self._roles[defn.id] = defn
                        except Exception:
                            pass
                    break

        if not self._roles:
            for r_val in SpanRoleEnum:
                self._roles[r_val.value] = SpanRoleDefinition(
                    id=r_val.value,
                    is_protected=r_val.value in {"PREAMBLE", "GROUND_TRUTH", "FENCE", "EPILOGUE"},
                )

    def register(self, defn: SpanRoleDefinition) -> None:
        self._roles[defn.id] = defn

    def is_valid(self, role_id: str) -> bool:
        return role_id in self._roles

    def all_ids(self) -> frozenset[str]:
        return frozenset(self._roles.keys())

    def get(self, role_id: str) -> SpanRoleDefinition | None:
        return self._roles.get(role_id)


# Pre-resolved constants
VALID_SPAN_ROLES = SpanRoleRegistry.get_instance().all_ids()


def get_valid_span_roles() -> frozenset[str]:
    return SpanRoleRegistry.get_instance().all_ids()
