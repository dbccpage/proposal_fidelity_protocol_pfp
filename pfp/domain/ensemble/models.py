"""Domain models for Multi-Model Allosteric Ensembles (U20).

Enforces:
- <=70B total parameter ceiling for all ensemble members.
- Lineage cap to prevent redundant error correlation.
- Exact Hill cooperative quorum for non-host verifiable claims.
- Public calibration and Cohen's kappa error correlation matrix.
AuthorityEffect: None.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
import math
from typing import Mapping, Sequence

PARAM_CEILING_BILLIONS: float = 70.0


class EnsembleRole(str, Enum):
    VERIFY = "VERIFY"
    GENERATE = "GENERATE"


@dataclass(frozen=True, slots=True)
class ModelRef:
    """Reference to an admitted model from the U06 registry."""

    model_id: str
    total_params_b: float
    lineage: str

    def __post_init__(self) -> None:
        if not self.model_id:
            raise ValueError("model_id must not be empty")
        if self.total_params_b <= 0:
            raise ValueError(f"total_params_b must be positive, got {self.total_params_b}")
        if not self.lineage:
            raise ValueError("lineage must not be empty")


@dataclass(frozen=True, slots=True)
class EnsembleSpec:
    """Specification for a multi-model ensemble with parameter ceiling and lineage cap."""

    members: tuple[ModelRef, ...]
    role: EnsembleRole
    hill_n: int = 4
    hill_kd: int = 2
    max_members_per_lineage: int = 1
    quiescent_ceiling: Fraction = Fraction(1, 10)
    active_floor: Fraction = Fraction(7, 10)
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if not isinstance(self.members, tuple):
            object.__setattr__(self, "members", tuple(self.members))

        if not self.members:
            raise ValueError("Ensemble must have at least one member")

        # 1. Parameter ceiling enforcement (<= 70B)
        for m in self.members:
            if m.total_params_b > PARAM_CEILING_BILLIONS:
                raise ValueError(
                    f"Model {m.model_id} ({m.total_params_b}B) exceeds the "
                    f"{PARAM_CEILING_BILLIONS}B parameter ceiling"
                )

        # 2. Lineage cap enforcement
        lineage_counts = Counter(m.lineage.lower() for m in self.members)
        for lineage, count in lineage_counts.items():
            if count > self.max_members_per_lineage:
                raise ValueError(
                    f"Lineage '{lineage}' has {count} members, exceeding the cap of "
                    f"{self.max_members_per_lineage}"
                )

        if self.hill_n <= 0 or self.hill_kd <= 0:
            raise ValueError("hill_n and hill_kd must be positive integers")

        if self.authority_effect != "None":
            raise ValueError(f"authority_effect must be 'None', got {self.authority_effect}")

    def evaluate_quorum(self, reject_votes: int) -> tuple[str, Fraction]:
        """Exact rational allosteric quorum calculation: H(theta) = theta^n / (Kd^n + theta^n)."""
        if reject_votes < 0:
            raise ValueError("reject_votes must be non-negative")
        if reject_votes == 0:
            return "QUIESCENT", Fraction(0, 1)

        theta_n = reject_votes**self.hill_n
        kd_n = self.hill_kd**self.hill_n
        resp = Fraction(theta_n, kd_n + theta_n)

        if resp <= self.quiescent_ceiling:
            return "QUIESCENT", resp
        elif resp >= self.active_floor:
            return "ACTIVATE", resp
        else:
            return "UNKNOWN", resp


@dataclass(frozen=True, slots=True)
class PairwiseCorrelationReport:
    """Pairwise error correlation metrics between two ensemble verifiers."""

    model_a: str
    model_b: str
    joint_error_rate: float
    marginal_error_product: float
    cohens_kappa: float


def compute_ensemble_calibration(
    eval_results: Mapping[str, Sequence[bool]],
) -> tuple[list[PairwiseCorrelationReport], float]:
    """Computes pairwise error correlation and effective verifier count Neff.

    eval_results: model_id -> sequence of boolean correctness (True = correct, False = error).
    """
    models = list(eval_results.keys())
    if len(models) < 2:
        return [], float(len(models))

    num_cases = len(eval_results[models[0]])
    for m in models:
        if len(eval_results[m]) != num_cases:
            raise ValueError(f"Mismatched case count for model {m}: {len(eval_results[m])} vs {num_cases}")

    # Build error indicators: 1 if error (False), 0 if correct (True)
    error_indicators: dict[str, list[int]] = {
        m: [0 if correct else 1 for correct in eval_results[m]]
        for m in models
    }

    reports: list[PairwiseCorrelationReport] = []
    kappas: list[float] = []

    for i in range(len(models)):
        for j in range(i + 1, len(models)):
            mA, mB = models[i], models[j]
            eA, eB = error_indicators[mA], error_indicators[mB]

            pA = sum(eA) / num_cases
            pB = sum(eB) / num_cases
            joint = sum(1 for a, b in zip(eA, eB) if a == 1 and b == 1) / num_cases
            marginal_prod = pA * pB

            # Cohen's kappa on agreement of correctness
            # Po = observed agreement rate
            p_agree = sum(1 for a, b in zip(eA, eB) if a == b) / num_cases
            # Pe = expected chance agreement
            p_both_err = pA * pB
            p_both_corr = (1 - pA) * (1 - pB)
            p_exp = p_both_err + p_both_corr

            if math.isclose(p_exp, 1.0):
                kappa = 1.0
            else:
                kappa = (p_agree - p_exp) / (1.0 - p_exp)

            reports.append(
                PairwiseCorrelationReport(
                    model_a=mA,
                    model_b=mB,
                    joint_error_rate=round(joint, 4),
                    marginal_error_product=round(marginal_prod, 4),
                    cohens_kappa=round(kappa, 4),
                )
            )
            kappas.append(max(0.0, kappa))

    # Effective count of independent verifiers Neff = N / (1 + (N - 1) * mean_correlation)
    N = len(models)
    mean_kappa = sum(kappas) / len(kappas) if kappas else 0.0
    denom = 1.0 + (N - 1) * mean_kappa
    neff = N / denom if denom > 0 else 1.0

    return reports, round(neff, 2)
