"""The Seven Halt Guards of Finite Descent Authority (FDA).

Enforces the 7 invariant guards required before descent promotion.
Guard 7 enforces strict immutable role split: proposer != authorizer.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import List, Tuple


@dataclass(frozen=True)
class HaltGuardResult:
    """Result of evaluating the Seven Halt Guards."""

    guard_1_valid_carrier: bool
    guard_2_nonempty_evidence: bool
    guard_3_verified_dual_witness: bool
    guard_4_audited_loss_ledger: bool
    guard_5_licensed_lift: bool
    guard_6_budget_available: bool
    guard_7_role_split: bool  # proposer != authorizer
    all_passed: bool
    refusal_reasons: Tuple[str, ...]

    def is_authorized(self) -> bool:
        return self.all_passed


class SevenHaltGuards:
    """Evaluates the Seven Halt Guards of FDA."""

    @staticmethod
    def evaluate(
        carrier_id: str,
        evidence_cochain_size: int,
        has_dual_witness: bool,
        loss_ledger_audited: bool,
        has_licensed_lift: bool,
        remaining_budget: Fraction,
        proposer_id: str,
        authorizer_id: str,
    ) -> HaltGuardResult:
        reasons: List[str] = []

        g1 = bool(carrier_id and carrier_id.strip())
        if not g1:
            reasons.append("Guard 1 Failed: Invalid or empty carrier.")

        g2 = evidence_cochain_size > 0
        if not g2:
            reasons.append("Guard 2 Failed: Empty evidence cochain.")

        g3 = has_dual_witness
        if not g3:
            reasons.append("Guard 3 Failed: Unverified dual witness.")

        g4 = loss_ledger_audited
        if not g4:
            reasons.append("Guard 4 Failed: Loss ledger is not audited.")

        g5 = has_licensed_lift
        if not g5:
            reasons.append("Guard 5 Failed: Missing licensed context extension / lift.")

        g6 = remaining_budget > Fraction(0, 1)
        if not g6:
            reasons.append("Guard 6 Failed: Zero or negative computational budget remaining.")

        g7 = (proposer_id != authorizer_id) and bool(proposer_id) and bool(authorizer_id)
        if not g7:
            reasons.append("Guard 7 Failed: Proposer and Authorizer roles must be strictly distinct.")

        all_passed = g1 and g2 and g3 and g4 and g5 and g6 and g7

        return HaltGuardResult(
            guard_1_valid_carrier=g1,
            guard_2_nonempty_evidence=g2,
            guard_3_verified_dual_witness=g3,
            guard_4_audited_loss_ledger=g4,
            guard_5_licensed_lift=g5,
            guard_6_budget_available=g6,
            guard_7_role_split=g7,
            all_passed=all_passed,
            refusal_reasons=tuple(reasons),
        )
