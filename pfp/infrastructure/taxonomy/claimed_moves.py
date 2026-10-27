"""PFP Infrastructure - Claimed Topological Moves Taxonomy.

AuthorityEffect: None.
Canonical specification of candidate moves and topological state transitions in Symbol Game complexes.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from pfp.infrastructure.yaml_loading import strict_yaml_load
from pydantic import BaseModel, ConfigDict, Field


def _load_claimed_move_enum_members() -> dict[str, str]:
    """Load canonical claimed move category identifiers directly from YAML."""
    for candidate_root in [
        Path(__file__).parent.parent / "yaml" / "taxonomy",
    ]:
        reg_file = candidate_root / "claimed_moves.yaml"
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
        "ATTACH_2CELL": "ATTACH_2CELL",
        "REMOVE_1CELL": "REMOVE_1CELL",
        "CONTRACT_EDGE": "CONTRACT_EDGE",
        "GAUGE_TRANSFORM": "GAUGE_TRANSFORM",
        "LIFT_CARRIER": "LIFT_CARRIER",
        "REFUSE_DESCENT": "REFUSE_DESCENT",
        "REWRITE_EXPRESSION": "REWRITE_EXPRESSION",
    }


ClaimedMoveEnum: type[Enum] = Enum(
    "ClaimedMoveEnum",
    _load_claimed_move_enum_members(),
    type=str,
    module=__name__,
)
ClaimedMoveEnum.__doc__ = (
    "Canonical enum of admitted topological modification moves loaded directly from YAML."
)


class ClaimedMoveDefinition(BaseModel):
    """Strongly typed specification of a candidate topological move."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    id: str = Field(description="Move identifier token (e.g. 'ATTACH_2CELL')")
    preserves_homology: bool = Field(
        default=False, description="Whether move is a homotopy or gauge equivalence"
    )
    description: str = Field(default="", description="Topological specification of the operation")


class ClaimedMoveRegistry:
    """Catalog of topological moves loaded from canonical YAML with dynamic extension."""

    _instance: ClaimedMoveRegistry | None = None

    def __init__(self) -> None:
        self._moves: dict[str, ClaimedMoveDefinition] = {}
        self._load_canonical()

    @classmethod
    def get_instance(cls) -> ClaimedMoveRegistry:
        if cls._instance is None:
            cls._instance = ClaimedMoveRegistry()
        return cls._instance

    def _load_canonical(self) -> None:
        for candidate_root in [
            Path(__file__).parent.parent / "yaml" / "taxonomy",
        ]:
            reg_file = candidate_root / "claimed_moves.yaml"
            if reg_file.is_file():
                data = strict_yaml_load(reg_file.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "categories" in data:
                    for item in data["categories"]:
                        try:
                            defn = ClaimedMoveDefinition.model_validate(item)
                            self._moves[defn.id] = defn
                        except Exception:
                            pass
                    break

        if not self._moves:
            for cm_val in ClaimedMoveEnum:
                self._moves[cm_val.value] = ClaimedMoveDefinition(
                    id=cm_val.value,
                    preserves_homology=cm_val.value
                    in {"CONTRACT_EDGE", "GAUGE_TRANSFORM", "REFUSE_DESCENT", "REWRITE_EXPRESSION"},
                )

    def register(self, defn: ClaimedMoveDefinition) -> None:
        self._moves[defn.id] = defn

    def is_valid(self, move_id: str) -> bool:
        return move_id in self._moves

    def all_ids(self) -> frozenset[str]:
        return frozenset(self._moves.keys())

    def get(self, move_id: str) -> ClaimedMoveDefinition | None:
        return self._moves.get(move_id)


# Pre-resolved constants
VALID_CLAIMED_MOVES = ClaimedMoveRegistry.get_instance().all_ids()


def get_valid_claimed_moves() -> frozenset[str]:
    return ClaimedMoveRegistry.get_instance().all_ids()
