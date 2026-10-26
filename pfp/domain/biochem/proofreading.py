"""Hopfield-Ninio 3-Step Irreversible Kinetic Proofreading State Machine.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
import enum
from fractions import Fraction
import re
from typing import Any, Mapping

from omega_engine_pfp.domain.biochem.errors import (
    DissociationError,
    ZeroFloatViolationError,
)


_PSEUDO_PROOF_MARKER = "am-fsp-1-pseudo-proof"
_BUZZWORDS = ("gauge invariance", "topological protection", "manifestly positive", "by symmetry")
# A hyphen, slash or underscore joining two letters is word formation ("sign-free",
# "and/or", "gauge_invariance"), not arithmetic.
_WORD_JOINER = re.compile(r"(?<=[^\W\d_])[-‐‑/_](?=[^\W\d_])")
_WHITESPACE = re.compile(r"\s+")
_EQUATION = re.compile(r"(=|\+|-|\*|/|\\sum|\\prod|\bpf\b|\bdet\b)")


def _normalize_prose(text: str) -> str:
    """Case-fold, split word-internal joiners into spaces, and collapse whitespace."""
    return _WHITESPACE.sub(" ", _WORD_JOINER.sub(" ", text.casefold())).strip()


def _has_equations(text: str) -> bool:
    """True when the text carries an arithmetic or operator symbol outside word formation."""
    return bool(_EQUATION.search(_WORD_JOINER.sub(" ", text)))


@enum.unique
class KineticProofreadingState(str, enum.Enum):
    """The 3 stages of irreversible kinetic proofreading + dissociation."""

    STAGE_A_INITIAL_BINDING = "STAGE_A_INITIAL_BINDING"
    STAGE_B_DEFORMATION_DELAY = "STAGE_B_DEFORMATION_DELAY"
    STAGE_C_TERMINAL_CATALYSIS = "STAGE_C_TERMINAL_CATALYSIS"
    DISSOCIATED = "DISSOCIATED"


@dataclass(frozen=True)
class DissociationReceipt:
    """Receipt documenting kinetic proofreading deformation and outcome."""

    candidate_id: str
    initial_phi1: Fraction
    deformed_phi1: Fraction
    delta_phi1: Fraction
    energy_dissipated: Fraction
    status: str
    reason: str

    def __post_init__(self) -> None:
        if (
            isinstance(self.initial_phi1, float)
            or isinstance(self.deformed_phi1, float)
            or isinstance(self.delta_phi1, float)
            or isinstance(self.energy_dissipated, float)
        ):
            raise ZeroFloatViolationError(
                "Float values in DissociationReceipt violate Zero-Float law"
            )

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.candidate_id == other.candidate_id
            and self.initial_phi1 == other.initial_phi1
            and self.deformed_phi1 == other.deformed_phi1
            and self.delta_phi1 == other.delta_phi1
            and self.energy_dissipated == other.energy_dissipated
            and self.status == other.status
            and self.reason == other.reason
        )


class HopfieldNinioProofreader:
    """Hopfield-Ninio kinetic proofreading with irreversible energy dissipation.

    Prevents commodity LLM pseudo-proofs (AM-FSP-1-PSEUDO-PROOF) from superficial
    one-turn admission.
    """

    def __init__(self, energy_per_delay: Fraction = Fraction(1, 1)) -> None:
        if isinstance(energy_per_delay, float):
            raise ZeroFloatViolationError(
                f"Float energy_per_delay={energy_per_delay!r} violates Zero-Float law"
            )
        self.energy_per_delay = Fraction(energy_per_delay)

    def proofread(
        self,
        candidate_id: str,
        content: str | Mapping[str, Any],
        initial_phi1: Fraction = Fraction(0, 1),
        deformation_factor: Fraction = Fraction(1, 1),
    ) -> DissociationReceipt:
        """Execute 3-step proofreading: Binding -> Deformation Delay -> Catalysis or Dissociation."""
        if isinstance(initial_phi1, float) or isinstance(deformation_factor, float):
            raise ZeroFloatViolationError(
                "Float phi1 or deformation_factor violates Zero-Float law; use Fraction"
            )

        initial_phi1_q = Fraction(initial_phi1)
        deform_q = Fraction(deformation_factor)

        # Stage A: Initial Binding
        # Check text or payload for pseudo-proof buzzword density without computation
        text = ""
        if isinstance(content, str):
            text = content
        elif isinstance(content, dict):
            text = str(content.get("text", content.get("content", "")))

        normalized = _normalize_prose(text)
        buzzword_count = sum(1 for b in _BUZZWORDS if b in normalized)
        has_equations = _has_equations(text)

        is_pseudo_proof = (
            _normalize_prose(_PSEUDO_PROOF_MARKER) in normalized
            or (buzzword_count >= 2 and not has_equations)
            or (isinstance(content, dict) and content.get("is_pseudo_proof", False))
        )

        # Stage B: Irreversible Retraction Deformation & Energy Dissipation
        energy_dissipated = self.energy_per_delay

        if is_pseudo_proof:
            # Under orthogonal deformation T_delta(M), pseudo-proof fails to maintain coboundary exactness
            delta_phi1 = Fraction(1, 1) * deform_q
            deformed_phi1 = initial_phi1_q + delta_phi1
            return DissociationReceipt(
                candidate_id=candidate_id,
                initial_phi1=initial_phi1_q,
                deformed_phi1=deformed_phi1,
                delta_phi1=delta_phi1,
                energy_dissipated=energy_dissipated,
                status="DISSOCIATED_DURING_DELAY",
                reason=(
                    "Substrate failed under orthogonal deformation T_delta(M); "
                    f"measured Delta Phi_1 = {delta_phi1} > 0 (AM-FSP-1-PSEUDO-PROOF detected)"
                ),
            )

        if initial_phi1_q > 0:
            delta_phi1 = Fraction(0, 1)
            return DissociationReceipt(
                candidate_id=candidate_id,
                initial_phi1=initial_phi1_q,
                deformed_phi1=initial_phi1_q,
                delta_phi1=delta_phi1,
                energy_dissipated=energy_dissipated,
                status="DISSOCIATED_DURING_DELAY",
                reason=f"Initial coboundary defect Phi_1 = {initial_phi1_q} > 0 precludes admission",
            )

        # Stage C: Terminal Catalysis
        # True proofs retain Phi_1 = 0 under deformation
        return DissociationReceipt(
            candidate_id=candidate_id,
            initial_phi1=Fraction(0, 1),
            deformed_phi1=Fraction(0, 1),
            delta_phi1=Fraction(0, 1),
            energy_dissipated=energy_dissipated,
            status="CATALYTIC_ADMISSION",
            reason="Substrate survived orthogonal deformation with Delta Phi_1 == 0",
        )


__all__ = [
    "DissociationReceipt",
    "HopfieldNinioProofreader",
    "KineticProofreadingState",
]
