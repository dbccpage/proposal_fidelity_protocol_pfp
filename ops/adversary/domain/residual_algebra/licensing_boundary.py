"""
licensing_boundary.py
=====================

Licensing Boundary & Valuation Receipts (Role B and Stage 5/6 Gate).

Residual Honesty Invariants:
1. Φ₁ = 0 does NOT imply token without an ExactnessWitnessPackage.
2. Flow/framing/concession metrics are Observables only.
3. AuthorityEffect remains strictly "None" on all emitted tokens.
4. Float residual mass cannot be promoted to exact rational certificates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from pfp.functional_boundary import require_rust_functional

from .residual_sorts import R_EXACTNESS_WITNESS, Residual1Cochain, ResidualSort


@dataclass(frozen=True)
class ValuationReceipt:
    """
    Role B Valuation Receipt emitted by ObstructionValuator.
    Pure evaluation of observed residual cochains.
    """

    residual_sort: ResidualSort
    phi_1: float | None
    gamma_2: float | None = 0.0
    phi_ret: float | None = 0.0
    phi_claim: float | None = 0.0
    is_exact_rational: bool = False
    evidence_sha256: Optional[str] = None
    diagnostics: Dict[str, Any] = field(default_factory=dict)
    authority_effect: str = "None"

    @property
    def residual_norm_phi_1(self) -> float | None:
        return self.phi_1

    @property
    def is_measured(self) -> bool:
        return all(value is not None for value in (
            self.phi_1, self.gamma_2, self.phi_ret, self.phi_claim,
        ))

    @classmethod
    def not_measured(cls, residual_sort: ResidualSort, *, code: str, reason: str) -> "ValuationReceipt":
        return cls(residual_sort, None, gamma_2=None, phi_ret=None, phi_claim=None,
            diagnostics={"refusal_code": code, "reason": reason})

    @property
    def is_exact_coboundary(self) -> bool:
        return self.is_measured and self.phi_1 == 0.0 and self.gamma_2 == 0.0 and self.phi_ret == 0.0

    def has_defects(self) -> bool:
        return self.is_measured and not self.is_exact_coboundary

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if not isinstance(other, ValuationReceipt):
            return False
        return (
            self.residual_sort == other.residual_sort
            and self.phi_1 == other.phi_1
            and self.gamma_2 == other.gamma_2
            and self.phi_ret == other.phi_ret
            and self.phi_claim == other.phi_claim
            and self.is_exact_rational == other.is_exact_rational
            and self.evidence_sha256 == other.evidence_sha256
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash(
            (
                type(self),
                self.residual_sort,
                self.phi_1,
                self.gamma_2,
                self.phi_ret,
                self.phi_claim,
                self.is_exact_rational,
                self.evidence_sha256,
                self.authority_effect,
            )
        )


class ObstructionValuator:
    """
    Role B Obstruction Valuator. Pure Functional:
    Evaluates Residual1Cochain into a ValuationReceipt. Never decides or commits.
    """

    @staticmethod
    def value_cochain(
        cochain: Residual1Cochain,
        *,
        gamma_2: float = 0.0,
        phi_ret: float = 0.0,
        phi_claim: float = 0.0,
        is_exact_rational: bool = False,
    ) -> ValuationReceipt:
        require_rust_functional("ObstructionValuator.value_cochain")

    @staticmethod
    def value_cochains(
        cochains: Tuple[Residual1Cochain, ...] | List[Residual1Cochain],
    ) -> ValuationReceipt:
        require_rust_functional("ObstructionValuator.value_cochains")


class LicensingBoundary:
    """
    Licensing Boundary Gate (Stage 5–6 Waist).
    Enforces residual honesty before proposing transition tokens.
    """

    @staticmethod
    def propose_token(
        *,
        target_receipt: ValuationReceipt,
        witness_cochain: Optional[Residual1Cochain],
        expected_sha256: Optional[str] = None,
        authority_effect_ceiling: str = "None",
    ) -> Tuple[bool, Optional[str], Tuple[str, ...]]:
        """
        Proposes a residual_admissible_transition_token.

        Conditions for proposal:
          1. Target valuation Φ₁ == 0.0
          2. ExactnessWitnessPackage is present and confirmed exact (mass == 0.0 and no defects)
          3. When expected_sha256 is supplied, witness evidence_sha256 must match exactly.
          4. AuthorityEffect is strictly "None".

        Returns: (is_admissible, token_proposal_or_none, refusal_reasons)
        """
        reasons: list[str] = []

        if authority_effect_ceiling != "None":
            reasons.append("authority_effect_ceiling_exceeded")

        if not target_receipt.is_measured:
            reasons.append("target_valuation_not_measured")
        elif target_receipt.phi_1 > 0.0:
            reasons.append("target_residual_mass_nonzero")

        if witness_cochain is None:
            reasons.append("missing_exactness_witness_package")
        else:
            if witness_cochain.residual_sort != R_EXACTNESS_WITNESS:
                reasons.append("witness_cochain_sort_mismatch")
            if not witness_cochain.is_exact():
                reasons.append("exactness_witness_rejected")

            if expected_sha256 is not None:
                witness_sha = None
                for item in witness_cochain.witness_data:
                    if isinstance(item, str) and len(item) == 64:
                        witness_sha = item
                        break
                if witness_sha != expected_sha256:
                    reasons.append("evidence_sha256_mismatch")

        if reasons:
            return False, None, tuple(reasons)

        token = "proposal:residual_admissible_transition_token:authority_effect_none"
        return True, token, ()
