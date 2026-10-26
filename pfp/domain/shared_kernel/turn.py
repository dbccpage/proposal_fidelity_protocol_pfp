"""Shared Kernel: Turn Value Objects and Enumerations (Role, Kind, Modality)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, Self

from ..exceptions import InvariantViolationError
from .kind import Kind, Role, RoleKind


@dataclass(frozen=True, slots=True, eq=False)
class TurnRole(Role):
    """Enriched Value Object representing a turn's participant role."""


class TurnModality(str, Enum):
    """Standard turn execution modalities."""

    SYMBOL_GAME_TURN = "symbol_game_turn"
    PROSE = "prose"
    MACHINE_BLOCK = "machine_block"
    CODE_PATCH = "code_patch"
    CODE_CHANGE = "code_change"
    CLAIMED_RESULT = "claimed_result"
    TOOL_RESULT = "tool_result"
    STATUS = "status"
    TOOL_USE = "tool_use"
    REPAIR_CANDIDATE = "repair_candidate"
    ELIMINATION_PROPOSAL = "elimination_proposal"
    COT_UNTRUSTED = "cot_untrusted"
    RESEARCH_INTAKE = "research_intake"


@dataclass(frozen=True, slots=True, eq=False)
class TurnKind(Kind):
    """Enriched Value Object representing a turn execution modality (subtyping Kind)."""

    @classmethod
    def symbol_game(cls) -> TurnKind:
        return cls(TurnModality.SYMBOL_GAME_TURN.value)

    @classmethod
    def prose(cls) -> TurnKind:
        return cls(TurnModality.PROSE.value)

    @classmethod
    def code_change(cls) -> TurnKind:
        return cls(TurnModality.CODE_CHANGE.value)

    @classmethod
    def claimed_result(cls) -> TurnKind:
        return cls(TurnModality.CLAIMED_RESULT.value)

    @classmethod
    def code_patch(cls) -> TurnKind:
        return cls(TurnModality.CODE_PATCH.value)

    @classmethod
    def research_intake(cls) -> TurnKind:
        return cls(TurnModality.RESEARCH_INTAKE.value)

    @classmethod
    def from_str(cls: type[Self], val: str | Self | TurnModality) -> Self:
        if isinstance(val, cls):
            return val
        if isinstance(val, TurnModality):
            return cls(val.value)
        if type(val) is not str:
            raise InvariantViolationError(
                f"TurnKind.from_str requires an exact str or TurnModality, got {type(val).__name__}"
            )
        return cls(val)
