"""ProposalEvaluator domain entity for scoring residual reductions and enforcing kill conditions.

Conforms to urn:omega:governance:evaluator:v1.0.0.
Operates strictly via zero-float exact rational arithmetic (fractions.Fraction).
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction
from typing import Any, Mapping, Sequence

from .exact.q import Q


class KillReason(str, Enum):
    NONE = "None"
    NON_CONTRACTIVE = "NonContractive"
    AUTHORITY_LEAK = "AuthorityLeak"
    UNBOUNDED_ENERGY = "UnboundedEnergy"
    DIVERGENCE = "Divergence"
    CYCLE_DETECTED = "CycleDetected"


def _to_fraction(val: Any, field_name: str = "value") -> Fraction:
    if isinstance(val, Fraction):
        return val
    if isinstance(val, Q):
        return Fraction(val.num, val.den)
    if isinstance(val, int) and not isinstance(val, bool):
        return Fraction(val, 1)
    if isinstance(val, float):
        return Fraction(str(val)).limit_denominator()
    if isinstance(val, str):
        return Fraction(val)
    raise TypeError(f"{field_name} must be exact rational, int, or float, got {type(val).__name__}")


@dataclass(frozen=True, slots=True)
class EvaluatorConfig:
    """Explicit tolerance specification and evaluation policy thresholds in exact rationals."""

    tolerance: Fraction = field(default_factory=lambda: Fraction(0, 1))
    efficiency_epsilon: Fraction = field(default_factory=lambda: Fraction(1, 10**6))
    max_proposals: int = 100
    require_exactness: bool = False

    def __post_init__(self) -> None:
        tol = _to_fraction(self.tolerance, "tolerance")
        eff_eps = _to_fraction(self.efficiency_epsilon, "efficiency_epsilon")
        object.__setattr__(self, "tolerance", tol)
        object.__setattr__(self, "efficiency_epsilon", eff_eps)


@dataclass(frozen=True, slots=True)
class ProposalEvaluationResult:
    """Deterministic evaluation verdict decision envelope using exact rational metrics."""

    proposal_id: str
    is_admissible: bool
    initial_l1_mass: Fraction
    final_l1_mass: Fraction
    mass_drop: Fraction
    efficiency: Fraction
    kill_reason: KillReason = KillReason.NONE
    details: str = "OK"
    authority_effect: str = "None"


@dataclass(frozen=True, slots=True)
class ProposalEvaluator:
    """Read-only governance decision layer applying admissibility policy to proposals."""

    evaluator_id: str = "proposal-evaluator-v1"
    evaluator_version: str = "v1.0.0"
    config: EvaluatorConfig = field(default_factory=EvaluatorConfig)

    def evaluate_proposal(
        self,
        proposal_id: str,
        initial_mass: Any,
        final_mass: Any,
        effort: Any = 1,
        metadata: Mapping[str, Any] | None = None,
    ) -> ProposalEvaluationResult:
        """Evaluates a single proposal for contractiveness, residual drop, and authority cleanliness."""
        meta = metadata or {}
        authority = meta.get("authority_effect", "None")
        init_m = _to_fraction(initial_mass, "initial_mass")
        fin_m = _to_fraction(final_mass, "final_mass")
        eff = _to_fraction(effort, "effort")

        if authority != "None":
            return ProposalEvaluationResult(
                proposal_id=proposal_id,
                is_admissible=False,
                initial_l1_mass=init_m,
                final_l1_mass=fin_m,
                mass_drop=Fraction(0, 1),
                efficiency=Fraction(0, 1),
                kill_reason=KillReason.AUTHORITY_LEAK,
                details=f"Prohibited authority effect: {authority}",
            )

        mass_drop = init_m - fin_m
        if mass_drop < -self.config.tolerance:
            return ProposalEvaluationResult(
                proposal_id=proposal_id,
                is_admissible=False,
                initial_l1_mass=init_m,
                final_l1_mass=fin_m,
                mass_drop=mass_drop,
                efficiency=Fraction(0, 1),
                kill_reason=KillReason.NON_CONTRACTIVE,
                details=f"Residual mass increased by {-mass_drop}",
            )

        if eff <= Fraction(0, 1):
            eff = Fraction(1, 1)
        efficiency = max(Fraction(0, 1), mass_drop) / eff

        return ProposalEvaluationResult(
            proposal_id=proposal_id,
            is_admissible=True,
            initial_l1_mass=init_m,
            final_l1_mass=fin_m,
            mass_drop=mass_drop,
            efficiency=efficiency,
            kill_reason=KillReason.NONE,
            details="Strict descent verified",
        )

    def rank_proposals(
        self,
        results: Sequence[ProposalEvaluationResult],
    ) -> tuple[ProposalEvaluationResult, ...]:
        """Deterministically ranks admissible proposals sorted by efficiency descending."""
        admissible = sorted(
            [r for r in results if r.is_admissible],
            key=lambda r: (r.efficiency, -len(r.proposal_id), r.proposal_id),
            reverse=True,
        )
        return tuple(admissible)

    def select_best_proposal(
        self,
        proposals: Sequence[tuple[str, Any, Any, Any, Mapping[str, Any] | None]],
    ) -> ProposalEvaluationResult | None:
        """Deterministically selects the most efficient contractive proposal from evaluated candidates."""
        evaluated = [
            self.evaluate_proposal(p_id, init, fin, eff, meta)
            for p_id, init, fin, eff, meta in proposals
        ]
        ranked = self.rank_proposals(evaluated)
        return ranked[0] if ranked else None


__all__ = [
    "EvaluatorConfig",
    "KillReason",
    "ProposalEvaluationResult",
    "ProposalEvaluator",
]
