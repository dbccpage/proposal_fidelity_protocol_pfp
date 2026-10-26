"""Shared Kernel: Coboundary scoring, candidate proposal, and residual drop Value Objects.

AuthorityEffect: None.
Operates strictly via zero-float exact rational arithmetic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from .authority_effect import AuthorityEffect
from .exact import Exact, coerce_exact, to_canonical_string
from .residual_colour import ResidualColour
from .residual_drop import ResidualDropV1


def _coerce_score_val(val: Any, field_name: str) -> Exact:
    if isinstance(val, Fraction):
        return val
    if hasattr(val, "num") and hasattr(val, "den"):
        return Fraction(val.num, val.den)
    if isinstance(val, int) and not isinstance(val, bool):
        return Fraction(val, 1)
    if isinstance(val, float):
        return Fraction(str(val)).limit_denominator()
    if isinstance(val, str):
        return coerce_exact(val, field=field_name)
    raise TypeError(f"{field_name} must be exact rational, int, or float, got {type(val).__name__}")


@dataclass(frozen=True, slots=True)
class CoboundaryScoreResult:
    """Result of evaluating discrete coboundary scoring vector for a candidate proposal."""

    phi1: Exact
    gamma2: Exact
    xi: Exact
    combined_score: Exact
    is_exact: bool
    refusals: tuple[str, ...] = field(default_factory=tuple)
    residual_colour: str = ResidualColour.OPEN.value

    def __post_init__(self) -> None:
        p1 = _coerce_score_val(self.phi1, "phi1")
        g2 = _coerce_score_val(self.gamma2, "gamma2")
        x = _coerce_score_val(self.xi, "xi")
        comb = _coerce_score_val(self.combined_score, "combined_score")
        object.__setattr__(self, "phi1", p1)
        object.__setattr__(self, "gamma2", g2)
        object.__setattr__(self, "xi", x)
        object.__setattr__(self, "combined_score", comb)

    def to_dict(self) -> dict[str, object]:
        return {
            "phi1": to_canonical_string(self.phi1),
            "gamma2": to_canonical_string(self.gamma2),
            "xi": to_canonical_string(self.xi),
            "combined_score": to_canonical_string(self.combined_score),
            "is_exact": self.is_exact,
            "refusals": list(self.refusals),
            "residual_colour": self.residual_colour,
            "authority_effect": AuthorityEffect.NONE.value,
        }


@dataclass(frozen=True, slots=True)
class CandidateProposal:
    """Value object representing a candidate proposal with payload, patch, and target demands."""

    proposal_id: str
    target_obstruction_ids: tuple[str, ...]
    eliminated_demand_ids: tuple[str, ...]
    patch_bytes_digest: str | None = None
    dual_witness_digest: str | None = None
    carrier_hash: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "target_obstruction_ids", tuple(sorted(set(self.target_obstruction_ids))))
        object.__setattr__(self, "eliminated_demand_ids", tuple(sorted(set(self.eliminated_demand_ids))))


__all__ = [
    "CandidateProposal",
    "CoboundaryScoreResult",
    "ResidualDropV1",
]
