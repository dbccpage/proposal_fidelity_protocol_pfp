"""Pure domain models for Lean 4 Formal Kernel Bridge (Prompt 43).

AuthorityEffect: None.
ZERO-FLOAT Law: Exact rational witness translations in Fraction.
Clean Architecture: Zero outward dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Tuple

STANDARD_LEAN_AXIOMS: Tuple[str, ...] = ("propext", "Quot.sound", "Classical.choice")


@dataclass(frozen=True)
class LeanProofWitness:
    """Formal proof witness translating between Python solvers and Lean 4 kernel terms."""

    theorem_id: str
    carrier_domain: str
    obstruction_code: str
    witness_repr: str
    exact_rational_gap: Fraction

    def __post_init__(self) -> None:
        if isinstance(self.exact_rational_gap, float):
            raise TypeError("ZERO-FLOAT Law: exact_rational_gap must be Fraction, not float")
        if not isinstance(self.exact_rational_gap, Fraction):
            raise TypeError("ZERO-FLOAT Law: exact_rational_gap must be Fraction instance")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.theorem_id,
            self.carrier_domain,
            self.obstruction_code,
            self.witness_repr,
            self.exact_rational_gap,
        ) == (
            other.theorem_id,
            other.carrier_domain,
            other.obstruction_code,
            other.witness_repr,
            other.exact_rational_gap,
        )


@dataclass(frozen=True)
class FormalCertificateBridge:
    """Cryptographic certificate bridge linking on-disk Lean module bytes with theorem verdicts."""

    lean_module: str
    source_sha256: str
    theorems_verified: Tuple[str, ...]
    status: str  # e.g. "PASS", "ABSTAIN", "REFUSED"
    authority_effect: str = "None"

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.lean_module,
            self.source_sha256,
            self.theorems_verified,
            self.status,
            self.authority_effect,
        ) == (
            other.lean_module,
            other.source_sha256,
            other.theorems_verified,
            other.status,
            other.authority_effect,
        )


@dataclass(frozen=True)
class LeanVerificationRequest:
    """Request specification for verifying a Lean 4 submission."""

    package_digest: str
    toolchain_pin: str
    required_declarations: Tuple[Tuple[str, str], ...]  # (claimed_name, hidden_statement)
    axiom_policy: Tuple[str, ...] = STANDARD_LEAN_AXIOMS
    forbidden_set: Tuple[str, ...] = (
        "sorry",
        "admit",
        "axiom",
        "unsafe",
        "partial",
        "implemented_by",
        "extern",
        "debug.skipKernelTC",
    )


@dataclass(frozen=True)
class LeanVerificationReceipt:
    """Receipt emitted after sandboxed build, harness elaboration, and axiom audit."""

    status: str  # "PASS", "FAIL"
    build_success: bool
    harness_elaborated: bool
    axioms_by_declaration: tuple[tuple[str, tuple[str, ...]], ...]
    forbidden_findings: tuple[dict[str, Any], ...] = ()
    refusal_code: str | None = None
    details: str | None = None
    authority_effect: str = "None"
    schema_version: str = "omega.symbol_game.lean_verification_receipt.v1"

