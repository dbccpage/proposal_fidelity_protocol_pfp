"""Typed gate register for the PFP gates directory.

Models the three gate families named in ``gates/README.md``: the 13 primary
retinue gates, the 10 intergate transitions between them, and the 3 empirical
benchmark gates.  Gate bodies remain in the per-gate YAML files; this module
types the register and the identity header of each file.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictStr,
    model_validator,
)


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class ComparisonOperator(str, Enum):
    """Comparison operators used by empirical benchmark gates."""

    LT = "LT"
    GTE = "GTE"
    EQ = "EQ"


_GATE_REF_PATTERN = r"^PFP-(0[1-9]|1[0-9]|2[0-2])-[A-Z]+(-[A-Z]+)*$"


def gate_ordinal(gate_ref: str) -> int:
    """Return the two-digit ordinal of a ``PFP-NN-...`` reference."""
    return int(gate_ref.split("-")[1])


class PrimaryGate(_Frozen):
    """One of the 22 primary retinue verification gates."""

    gate_id: StrictStr = Field(pattern=_GATE_REF_PATTERN)
    name: StrictStr = Field(min_length=1)
    character: StrictStr = Field(min_length=1)
    file: StrictStr = Field(pattern=r"^\d{2}_[a-z0-9_]+\.yaml$")
    authority_effect: Literal["None"] = "None"

    @model_validator(mode="after")
    def _file_prefix_matches_id(self) -> PrimaryGate:
        if int(self.file[:2]) != gate_ordinal(self.gate_id):
            raise ValueError("file number prefix must equal gate ordinal")
        return self


class Intergate(_Frozen):
    """A transition register entry between two primary gates.

    Edge endpoints are matched by two-digit ordinal, because some endpoint
    strings abbreviate the primary gate id (for example ``PFP-07-MASTER``).
    """

    intergate_id: StrictStr = Field(pattern=r"^PFP-IG-\d{2}-[A-Z]+(-[A-Z]+)*$")
    file: StrictStr = Field(pattern=r"^intergates/\d{2}_[a-z0-9_]+\.yaml$")
    transition_from: StrictStr = Field(pattern=_GATE_REF_PATTERN)
    transition_to: StrictStr = Field(pattern=_GATE_REF_PATTERN)
    cognitive_vector: StrictStr = Field(min_length=1)
    authority_effect: Literal["None"] = "None"

    @model_validator(mode="after")
    def _edge_is_not_a_loop(self) -> Intergate:
        if gate_ordinal(self.transition_from) == gate_ordinal(self.transition_to):
            raise ValueError("an intergate must join two distinct primary gates")
        return self


class EmpiricalGate(_Frozen):
    """A quantitative empirical benchmark gate."""

    gate_id: StrictStr = Field(pattern=r"^PFP-EMP-GATE-\d{3}$")
    kind: Literal["EmpiricalBenchmarkGate"]
    suite_id: StrictStr = Field(min_length=1)
    comparison_operator: ComparisonOperator
    file: StrictStr = Field(pattern=r"^empirical/\d{2}_[a-z0-9_]+\.yaml$")
    authority_effect: Literal["None"] = "None"


class GateRegister(_Frozen):
    """Complete register: 22 primary gates, 10 intergates, 3 empirical gates."""

    primary_gates: tuple[PrimaryGate, ...]
    intergates: tuple[Intergate, ...]
    empirical_gates: tuple[EmpiricalGate, ...]
    authority_effect: Literal["None"] = "None"

    @model_validator(mode="after")
    def _counts_and_edges(self) -> GateRegister:
        ords = sorted(gate_ordinal(g.gate_id) for g in self.primary_gates)
        if ords != list(range(1, 23)):
            raise ValueError("primary gates must be ordinals 1..22 exactly once")
        if len(self.intergates) != 10:
            raise ValueError("intergate register must hold exactly 10 entries")
        if len(self.empirical_gates) != 3:
            raise ValueError("empirical register must hold exactly 3 entries")
        return self
