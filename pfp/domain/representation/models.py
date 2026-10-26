"""Domain models for TurnView and Representation Ablation (U25).

Defines the canonical information-complete TurnView representation.
Zero outward dependencies. Zero floating-point arithmetic.
AuthorityEffect: None.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence, Tuple


@dataclass(frozen=True, slots=True)
class TurnView:
    """Canonical representation of an active Symbol Game turn state."""

    round_seq: int
    phi1: int
    gamma2: int
    open_constraints: Tuple[Tuple[str, str], ...]
    decided_values: Tuple[Tuple[str, int], ...]
    refused_moves: Tuple[Tuple[str, str], ...]
    prompt_regime: str
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if not isinstance(self.round_seq, int) or isinstance(self.round_seq, bool) or self.round_seq < 0:
            raise ValueError(f"round_seq must be non-negative int, got {self.round_seq}")
        if not isinstance(self.phi1, int) or isinstance(self.phi1, bool) or self.phi1 < 0:
            raise ValueError(f"phi1 must be non-negative int, got {self.phi1}")
        if not isinstance(self.gamma2, int) or isinstance(self.gamma2, bool) or self.gamma2 < 0:
            raise ValueError(f"gamma2 must be non-negative int, got {self.gamma2}")
        if not isinstance(self.open_constraints, tuple):
            object.__setattr__(self, "open_constraints", tuple((str(k), str(v)) for k, v in self.open_constraints))
        if not isinstance(self.decided_values, tuple):
            object.__setattr__(self, "decided_values", tuple((str(k), int(v)) for k, v in self.decided_values))
        if not isinstance(self.refused_moves, tuple):
            object.__setattr__(self, "refused_moves", tuple((str(k), str(v)) for k, v in self.refused_moves))
        if not isinstance(self.prompt_regime, str):
            raise TypeError("prompt_regime must be a str")
        if self.authority_effect != "None":
            raise ValueError(f"authority_effect must be 'None', got {self.authority_effect}")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, TurnView)
        return (
            self.round_seq == other.round_seq
            and self.phi1 == other.phi1
            and self.gamma2 == other.gamma2
            and self.open_constraints == other.open_constraints
            and self.decided_values == other.decided_values
            and self.refused_moves == other.refused_moves
            and self.prompt_regime == other.prompt_regime
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.round_seq,
            self.phi1,
            self.gamma2,
            self.open_constraints,
            self.decided_values,
            self.refused_moves,
            self.prompt_regime,
            self.authority_effect,
        ))


ARM_A_CONFIG: dict[str, Any] = {
    "representation": "GLYPH_PACKET",
    "controller": "STANDARD_ROP",
    "prompt_regime": "STANDARD",
    "grammar_strength": "EXACT",
    "carrier_mask": True,
    "authority_effect": "None",
}

ARM_C_CONFIG: dict[str, Any] = {
    "representation": "PLAIN_TEXT",
    "controller": "STANDARD_ROP",
    "prompt_regime": "STANDARD",
    "grammar_strength": "EXACT",
    "carrier_mask": True,
    "authority_effect": "None",
}


def get_arm_config(arm_id: str) -> dict[str, Any]:
    """Retrieve frozen copy of arm execution config."""
    if arm_id.upper() in ("ARM_A", "A"):
        return dict(ARM_A_CONFIG)
    if arm_id.upper() in ("ARM_C", "C"):
        return dict(ARM_C_CONFIG)
    raise KeyError(f"Unknown arm_id: {arm_id}. Valid arms: ARM_A, ARM_C")

