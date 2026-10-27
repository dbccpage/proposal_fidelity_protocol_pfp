"""PFP Infrastructure - Evaluation Statuses Taxonomy.

AuthorityEffect: None.
Canonical specification of candidate evaluation outcomes.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from pfp.infrastructure.yaml_loading import strict_yaml_load
from pydantic import BaseModel, ConfigDict, Field


def _load_evaluation_status_enum_members() -> dict[str, str]:
    """Load canonical evaluation status category identifiers directly from YAML."""
    for candidate_root in [
        Path(__file__).parent.parent / "yaml" / "taxonomy",
    ]:
        reg_file = candidate_root / "evaluation_statuses.yaml"
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
        "ACCEPTED": "ACCEPTED",
        "WRONG_ANSWER": "WRONG_ANSWER",
        "FALSE_CERTAINTY": "FALSE_CERTAINTY",
        "MALFORMED": "MALFORMED",
        "NOT_RUN": "NOT_RUN",
        "REFUSED": "REFUSED",
    }


EvaluationStatusEnum: type[Enum] = Enum(
    "EvaluationStatusEnum",
    _load_evaluation_status_enum_members(),
    type=str,
    module=__name__,
)
EvaluationStatusEnum.__doc__ = (
    "Canonical enum of gate evaluation outcomes loaded directly from YAML."
)


class EvaluationStatusDefinition(BaseModel):
    """Strongly typed specification of an evaluation outcome status."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    id: str = Field(description="Evaluation outcome token (e.g. 'ACCEPTED')")
    display_name: str = Field(description="Human-readable title")
    is_terminal: bool = Field(default=True, description="Whether status halts pipeline evaluation")
    is_valid_proposal: bool = Field(
        default=False, description="Whether proposal was correct or validly refused"
    )
    description: str = Field(default="", description="Detailed semantic explanation")


class EvaluationStatusRegistry:
    """Catalog of evaluation statuses loaded from canonical YAML with dynamic extension."""

    _instance: EvaluationStatusRegistry | None = None

    def __init__(self) -> None:
        self._statuses: dict[str, EvaluationStatusDefinition] = {}
        self._load_canonical()

    @classmethod
    def get_instance(cls) -> EvaluationStatusRegistry:
        if cls._instance is None:
            cls._instance = EvaluationStatusRegistry()
        return cls._instance

    def _load_canonical(self) -> None:
        for candidate_root in [
            Path(__file__).parent.parent / "yaml" / "taxonomy",
        ]:
            reg_file = candidate_root / "evaluation_statuses.yaml"
            if reg_file.is_file():
                data = strict_yaml_load(reg_file.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "categories" in data:
                    for item in data["categories"]:
                        try:
                            defn = EvaluationStatusDefinition.model_validate(item)
                            self._statuses[defn.id] = defn
                        except Exception:
                            pass
                    break

        if not self._statuses:
            for s_val in EvaluationStatusEnum:
                self._statuses[s_val.value] = EvaluationStatusDefinition(
                    id=s_val.value,
                    display_name=s_val.value.replace("_", " ").title(),
                )

    def register(self, defn: EvaluationStatusDefinition) -> None:
        self._statuses[defn.id] = defn

    def is_valid(self, status_id: str) -> bool:
        return status_id in self._statuses

    def all_ids(self) -> frozenset[str]:
        return frozenset(self._statuses.keys())

    def get(self, status_id: str) -> EvaluationStatusDefinition | None:
        return self._statuses.get(status_id)


# Pre-resolved constants
VALID_EVALUATION_STATUSES = EvaluationStatusRegistry.get_instance().all_ids()


def get_valid_evaluation_statuses() -> frozenset[str]:
    return EvaluationStatusRegistry.get_instance().all_ids()
