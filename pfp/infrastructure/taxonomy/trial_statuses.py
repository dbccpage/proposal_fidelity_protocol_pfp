"""PFP Infrastructure - Trial Statuses Taxonomy.

AuthorityEffect: None.
Canonical specification of trial execution lifecycle states.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from pfp.infrastructure.yaml_loading import strict_yaml_load
from pydantic import BaseModel, ConfigDict, Field


def _load_trial_status_enum_members() -> dict[str, str]:
    """Load canonical trial status category identifiers directly from YAML."""
    for candidate_root in [
        Path(__file__).parent.parent / "yaml" / "taxonomy",
    ]:
        reg_file = candidate_root / "trial_statuses.yaml"
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
        "NOT_RUN": "NOT_RUN",
        "RUNNING": "RUNNING",
        "COMPLETED": "COMPLETED",
        "FAILED": "FAILED",
        "REFUSED": "REFUSED",
        "PASS": "PASS",
        "FAIL": "FAIL",
    }


TrialStatusEnum: type[Enum] = Enum(
    "TrialStatusEnum",
    _load_trial_status_enum_members(),
    type=str,
    module=__name__,
)
TrialStatusEnum.__doc__ = (
    "Canonical enum of trial execution lifecycle states loaded directly from YAML."
)


class TrialStatusDefinition(BaseModel):
    """Strongly typed specification of a trial execution status."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    id: str = Field(description="Trial status token (e.g. 'RUNNING')")
    is_terminal: bool = Field(
        default=False, description="Whether status marks completion of the trial"
    )
    description: str = Field(default="", description="Semantic meaning of this lifecycle stage")


class TrialStatusRegistry:
    """Catalog of trial lifecycle statuses loaded from canonical YAML with dynamic extension."""

    _instance: TrialStatusRegistry | None = None

    def __init__(self) -> None:
        self._statuses: dict[str, TrialStatusDefinition] = {}
        self._load_canonical()

    @classmethod
    def get_instance(cls) -> TrialStatusRegistry:
        if cls._instance is None:
            cls._instance = TrialStatusRegistry()
        return cls._instance

    def _load_canonical(self) -> None:
        for candidate_root in [
            Path(__file__).parent.parent / "yaml" / "taxonomy",
        ]:
            reg_file = candidate_root / "trial_statuses.yaml"
            if reg_file.is_file():
                data = strict_yaml_load(reg_file.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "categories" in data:
                    for item in data["categories"]:
                        try:
                            defn = TrialStatusDefinition.model_validate(item)
                            self._statuses[defn.id] = defn
                        except Exception:
                            pass
                    break

        if not self._statuses:
            for t_val in TrialStatusEnum:
                self._statuses[t_val.value] = TrialStatusDefinition(
                    id=t_val.value,
                    is_terminal=t_val.value in {"COMPLETED", "FAILED", "REFUSED", "PASS", "FAIL"},
                )

    def register(self, defn: TrialStatusDefinition) -> None:
        self._statuses[defn.id] = defn

    def is_valid(self, status_id: str) -> bool:
        return status_id in self._statuses

    def all_ids(self) -> frozenset[str]:
        return frozenset(self._statuses.keys())

    def get(self, status_id: str) -> TrialStatusDefinition | None:
        return self._statuses.get(status_id)


# Pre-resolved constants
VALID_TRIAL_STATUSES = TrialStatusRegistry.get_instance().all_ids()


def get_valid_trial_statuses() -> frozenset[str]:
    return TrialStatusRegistry.get_instance().all_ids()
