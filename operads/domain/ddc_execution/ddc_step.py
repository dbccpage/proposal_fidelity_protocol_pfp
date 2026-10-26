#!/usr/bin/env python3
"""DEPRECATED: Operations math shim for DDC action records and runtime laws.

AuthorityEffect: None.

Milestone M1 Deprecation Notice (gemini_001.md §2.2 G1-OPS.4):
Direct DDC runtime law checking and tape verification in operations are deprecated
in favor of the DDC module omega_wdp::ddc (op_verification.rs, parser.rs)
and workflow operad parsers (DdcOperadParser).

Canonical Destinations:
- Rust Crate: omega_engine/crates_rs/omega_wdp/src/ddc/
  - src/op_verification.rs (The 8 candidate runtime laws verification)
  - src/dda_alphabet.rs (DdaOp and 8-rune alphabet)
  - src/dda_trace.rs (Merkle row hash chaining)
  - src/parser.rs (DdcTapeParser)
- Workflows Parser: omega_engine_operads.skill_operad.ddc_operad_parser.DdcOperadParser
- CLI Binary: omega_ddc_parse
"""

from __future__ import annotations

import hashlib
import json
import warnings
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Any, Sequence

from .errors import Refusal

DDC_SHIM_DEPRECATED_REFUSAL = Refusal(
    code="DDC_OPERATIONS_SHIM_DEPRECATED",
    message=(
        "Direct DDC runtime law checking in operations is deprecated; "
        "delegate to omega_wdp::ddc or DdcOperadParser."
    ),
    locus="omega_engine_operads.domain.ddc_execution.ddc_step",
)


def emit_ddc_shim_deprecation_warning(subject: str) -> None:
    warnings.warn(
        f"{subject} in omega_engine_operads.domain.ddc_execution.ddc_step is deprecated. "
        "Delegate DDC parsing and runtime laws to omega_wdp::ddc.",
        category=DeprecationWarning,
        stacklevel=3,
    )


class DdcRune(str, Enum):
    """The 8 canonical runes of the Discrete Deformation Calculus operational alphabet."""

    C = "C"  # Context Exposure
    R = "R"  # Residual Projection
    E = "E"  # Exact Repair
    I = "I"  # noqa: E741 — canonical rune name

    LAMBDA = "Λ"  # Structural Lift
    D = "D"  # Scale Descent
    M = "M"  # Typed Refusal
    T = "T"  # Terminalization


CANONICAL_RUNES: tuple[str, ...] = ("C", "R", "E", "I", "Λ", "D", "M", "T")

RUNE_SYNONYMS: dict[str, str] = {
    "L": "Λ",
    "Lambda": "Λ",
    "\\Lambda": "Λ",
    "Meta": "Λ",
}


def normalize_rune(rune: str) -> str:
    cleaned = rune.strip()
    return RUNE_SYNONYMS.get(cleaned, cleaned)


@dataclass(frozen=True)
class DdcRecord:
    """Immutable value object representing one verified transition on a DDC tape."""

    sequence: int
    letter: str
    parent_sha256: str | None
    record_sha256: str
    carrier_hash: str
    phi_1: Fraction | None
    gamma_2: Fraction | None
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        emit_ddc_shim_deprecation_warning("DdcRecord")
        norm_letter = normalize_rune(self.letter)
        if norm_letter not in CANONICAL_RUNES:
            raise ValueError(f"Unknown DDC rune: {self.letter!r}")
        object.__setattr__(self, "letter", norm_letter)

    @property
    def total_residual(self) -> Fraction | None:
        if self.phi_1 is None and self.gamma_2 is None:
            return None
        return (self.phi_1 or Fraction(0)) + (self.gamma_2 or Fraction(0))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, DdcRecord)
        return (
            self.sequence == other.sequence
            and self.letter == other.letter
            and self.parent_sha256 == other.parent_sha256
            and self.record_sha256 == other.record_sha256
            and self.carrier_hash == other.carrier_hash
            and self.phi_1 == other.phi_1
            and self.gamma_2 == other.gamma_2
            and self.payload == other.payload
        )

    def __hash__(self) -> int:
        return hash(
            (
                type(self),
                self.sequence,
                self.letter,
                self.parent_sha256,
                self.record_sha256,
                self.carrier_hash,
                self.phi_1,
                self.gamma_2,
            )
        )


def verify_merkle_chain(records: Sequence[DdcRecord]) -> tuple[bool, list[str]]:
    """Verifies that each step hashes its contents and links to parent_sha256."""
    emit_ddc_shim_deprecation_warning("verify_merkle_chain")
    violations: list[str] = []
    expected_parent: str | None = None

    for idx, rec in enumerate(records):
        if rec.sequence != idx:
            violations.append(
                f"Step {idx}: sequence number mismatch (got {rec.sequence}, expected {idx})"
            )

        if rec.parent_sha256 != expected_parent:
            violations.append(
                f"Step {idx} ({rec.letter}): broken parent hash link (expected {expected_parent}, got {rec.parent_sha256})"
            )

        sorted_payload = {
            k: rec.payload[k] for k in sorted(rec.payload.keys(), key=lambda s: s.encode("utf-8"))
        }
        material = json.dumps(
            {
                "sequence": rec.sequence,
                "parent_sha256": rec.parent_sha256,
                "payload": sorted_payload,
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        computed_hash = hashlib.sha256(material).hexdigest()

        if computed_hash != rec.record_sha256:
            violations.append(
                f"Step {idx} ({rec.letter}): record hash mismatch (expected {computed_hash}, got {rec.record_sha256})"
            )

        expected_parent = rec.record_sha256

    return len(violations) == 0, violations


def verify_ddc_candidate_laws(records: Sequence[DdcRecord]) -> tuple[bool, list[str]]:
    """Verifies the 8 candidate runtime laws over a sequence of DdcRecords."""
    emit_ddc_shim_deprecation_warning("verify_ddc_candidate_laws")
    violations: list[str] = []
    terminal_seen = False
    refusal_active = False

    for idx, step in enumerate(records):
        letter = step.letter

        # Law 2: Terminal Absorption
        if terminal_seen:
            violations.append(
                f"Law 2 Violation (TerminalAbsorbing): step {idx} ({letter}) occurred after terminalization"
            )

        if letter == "T":
            terminal_seen = True
            gamma2 = step.gamma_2 or Fraction(0)
            if gamma2 > 0:
                violations.append(
                    f"Law 2 Violation (TerminalizedOpenResidual): step {idx} terminalized with closure defect Gamma_2={gamma2} > 0"
                )

        # Law 3: Refusal Absorption
        if refusal_active and letter not in ("C", "Λ", "T"):
            violations.append(
                f"Law 3 Violation (RefusalAbsorbing): step {idx} ({letter}) attempted during active refusal"
            )

        if letter == "M":
            refusal_active = True
            reason = step.payload.get("refusal_reason") or step.payload.get("reason")
            if not reason:
                violations.append(
                    f"Law 3 Violation (MissingRefusalReason): step {idx} (M) missing refusal reason"
                )

        if letter in ("C", "Λ"):
            refusal_active = False

        # Law 4: Lift Trigger
        if letter == "Λ":
            has_trigger = step.payload.get("lift_trigger") is True or step.payload.get(
                "before_class"
            ) in ("ClosedResidual", "StabilizedSurvivor", "DetectorInadequate")
            has_licence = (
                step.payload.get("licence_verified") is True
                or step.payload.get("has_licence") is True
            )
            if not has_trigger:
                violations.append(
                    f"Law 4 Violation (LiftWithoutTrigger): step {idx} (Λ) proposed without trigger"
                )
            if not has_licence:
                violations.append(
                    f"Law 4 Violation (UnlicensedLift): step {idx} (Λ) proposed without verified licence"
                )

        # Law 5: Integration Requires Receipt
        if letter == "I":
            has_receipt = (
                step.payload.get("has_receipt") is True
                or step.payload.get("receipt_sha256") is not None
            )
            if not has_receipt:
                violations.append(
                    f"Law 5 Violation (MissingReceipt): step {idx} (I) integration lacking receipt"
                )

        # Law 6: Descent Requires Loss Ledger
        if letter == "D":
            has_loss_ledger = (
                step.payload.get("has_loss_ledger") is True
                or step.payload.get("loss_ledger_id") is not None
                or "loss_ledger" in step.payload
            )
            if not has_loss_ledger:
                violations.append(
                    f"Law 6 Violation (MissingLossLedger): step {idx} (D) descent lacking loss ledger"
                )

        # Law 7: Exact Repair Monotonicity
        if letter == "E" and idx > 0:
            prev = records[idx - 1]
            if step.phi_1 is not None and prev.phi_1 is not None and step.phi_1 > prev.phi_1:
                violations.append(
                    f"Law 7 Violation (ExactRepairIncreasedPhi1): step {idx} (E) increased Phi_1 from {prev.phi_1} to {step.phi_1}"
                )
            if (
                step.gamma_2 is not None
                and prev.gamma_2 is not None
                and step.gamma_2 > prev.gamma_2
            ):
                violations.append(
                    f"Law 7 Violation (ExactRepairIncreasedGamma2): step {idx} (E) increased Gamma_2 from {prev.gamma_2} to {step.gamma_2}"
                )

        # Law 8: Context Exposure Monotonicity
        if letter == "C" and idx > 0:
            prev = records[idx - 1]
            if step.phi_1 is not None and prev.phi_1 is not None and step.phi_1 < prev.phi_1:
                violations.append(
                    f"Law 8 Violation (ContextExposureLoweredPhi1): step {idx} (C) lowered Phi_1 from {prev.phi_1} to {step.phi_1}"
                )

    return len(violations) == 0, violations
