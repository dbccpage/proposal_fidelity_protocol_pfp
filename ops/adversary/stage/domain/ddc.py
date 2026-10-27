"""Discrete Deformation Calculus (DDC) domain actions and purity validators.

The operational alphabet is extracted dynamically from the operad canon:
`code/rust/core_operad_canon/src/lib.rs` (`DdcOp::letter`).
Letters and operations are never hardcoded here.

AuthorityEffect: strictly None.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Any

from operations.domain.rop.result import Err, Ok, Refusal, Result

from .canonical import AUTHORITY_EFFECT_NONE, identifier, text


def _format_exact(frac: Fraction) -> str:
    """Format exact BigRational wire representation."""
    if frac.denominator == 1:
        return str(frac.numerator)
    return f"{frac.numerator}/{frac.denominator}"


def parse_ddc_alphabet(source_text: str) -> tuple[tuple[str, ...], dict[str, str]]:
    """Parse DDC letters from source text. This module does not read the disk."""
    if type(source_text) is not str or not source_text:
        raise ValueError("DDC alphabet source text is required")
    pairs = re.findall(r"Dd[ac]Op::(\w+)\s*=>\s*\"([^\"]+)\"", source_text)
    if not pairs:
        raise ValueError("Could not parse DdcOp/DdaOp letters from the supplied source")
    canonical_letters = tuple(letter for _, letter in pairs)
    members: dict[str, str] = {}
    for variant, letter in pairs:
        if letter.isascii() and letter.isalnum():
            members[letter] = letter
        elif letter == "Λ":
            members["LAMBDA"] = letter
    for variant, letter in pairs:
        members[variant] = letter
        if letter == "Λ":
            members["Lambda"] = letter
            members["L"] = letter
    return canonical_letters, members


def bind_ddc_alphabet(source_text: str) -> Any:
    """Install ``DdcLetter`` from caller-supplied source text."""
    global DdcLetter, DdaLetter
    canonical_letters, members = parse_ddc_alphabet(source_text)
    letter_enum: Any = Enum("DdcLetter", members, type=str, module=__name__)
    letter_enum.CANONICAL_ALPHABET = canonical_letters
    letter_enum.from_letter = classmethod(_from_letter)
    DdcLetter = letter_enum
    DdaLetter = letter_enum
    return letter_enum


DdcLetter: Any = None
DdaLetter: Any = DdcLetter


def _from_letter(cls: type[DdcLetter], s: str) -> DdcLetter:
    if s in ("L", "Lambda", "\\Lambda", "Meta"):
        s = "Λ"
    try:
        return cls(s)
    except ValueError:
        try:
            return cls[s]
        except KeyError:
            raise ValueError(f"Unknown DDC letter or op: {s!r}")


@dataclass(frozen=True)
class DdcStepV1:
    """One obstruction-removal / structure-building action in the DDC stream.

    Carries zero narrative, zero perception metrics, zero bookkeeping.
    AuthorityEffect is strictly invariant at None.
    """

    letter: DdcLetter | str
    before_class: str
    after_class: str
    carrier_hash: str
    witness_hash: str | None
    receipt_sha256: str
    authority_effect: str = AUTHORITY_EFFECT_NONE
    timestamp: str | None = None
    phi_1: Fraction | None = None
    gamma_2: Fraction | None = None

    def __post_init__(self) -> None:
        if isinstance(self.letter, str):
            val = self.letter
            if val in ("L", "Lambda", "\\Lambda", "Meta"):
                val = "Λ"
            try:
                object.__setattr__(self, "letter", DdcLetter(val))
            except ValueError:
                try:
                    object.__setattr__(self, "letter", DdcLetter[val])
                except KeyError:
                    raise TypeError(f"letter must be a valid DdcLetter, got {self.letter!r}")
        elif not isinstance(self.letter, DdcLetter):
            raise TypeError(f"letter must be a valid DdcLetter, got {self.letter!r}")
        object.__setattr__(
            self, "before_class", identifier(self.before_class, "before_class")
        )
        object.__setattr__(
            self, "after_class", identifier(self.after_class, "after_class")
        )
        object.__setattr__(
            self, "carrier_hash", text(self.carrier_hash, "carrier_hash")
        )
        if self.witness_hash is not None:
            object.__setattr__(
                self, "witness_hash", text(self.witness_hash, "witness_hash")
            )
        object.__setattr__(
            self, "receipt_sha256", text(self.receipt_sha256, "receipt_sha256")
        )
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError(f"authority_effect must be '{AUTHORITY_EFFECT_NONE}'")
        if self.timestamp is not None:
            object.__setattr__(self, "timestamp", str(self.timestamp))
        if self.phi_1 is not None:
            if not isinstance(self.phi_1, Fraction):
                object.__setattr__(self, "phi_1", Fraction(self.phi_1))
        if self.gamma_2 is not None:
            if not isinstance(self.gamma_2, Fraction):
                object.__setattr__(self, "gamma_2", Fraction(self.gamma_2))

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "after_class": self.after_class,
            "authority_effect": self.authority_effect,
            "before_class": self.before_class,
            "carrier_hash": self.carrier_hash,
            "letter": self.letter.value,
            "receipt_sha256": self.receipt_sha256,
            "witness_hash": self.witness_hash,
        }
        if self.timestamp is not None:
            data["timestamp"] = self.timestamp
        if self.phi_1 is not None:
            data["phi_1"] = _format_exact(self.phi_1) if isinstance(self.phi_1, Fraction) else self.phi_1
        if self.gamma_2 is not None:
            data["gamma_2"] = _format_exact(self.gamma_2) if isinstance(self.gamma_2, Fraction) else self.gamma_2
        return data

    @classmethod
    def from_dict(cls, value: Any) -> "DdcStepV1":
        if not isinstance(value, dict):
            raise TypeError("DdcStepV1 wire representation must be an exact dict")
        letter_val = value.get("letter")
        if letter_val is None:
            raise ValueError("DdcStepV1 missing 'letter'")
        letter = DdcLetter.from_letter(letter_val) if isinstance(letter_val, str) else letter_val
        phi_1_raw = value.get("phi_1")
        gamma_2_raw = value.get("gamma_2")
        return cls(
            letter=letter,
            before_class=identifier(value["before_class"], "before_class"),
            after_class=identifier(value["after_class"], "after_class"),
            carrier_hash=text(value["carrier_hash"], "carrier_hash"),
            witness_hash=text(value["witness_hash"], "witness_hash") if value.get("witness_hash") is not None else None,
            receipt_sha256=text(value["receipt_sha256"], "receipt_sha256"),
            authority_effect=value.get("authority_effect", AUTHORITY_EFFECT_NONE),
            timestamp=value.get("timestamp"),
            phi_1=Fraction(phi_1_raw) if phi_1_raw is not None else None,
            gamma_2=Fraction(gamma_2_raw) if gamma_2_raw is not None else None,
        )

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.letter == other.letter
            and self.before_class == other.before_class
            and self.after_class == other.after_class
            and self.carrier_hash == other.carrier_hash
            and self.witness_hash == other.witness_hash
            and self.receipt_sha256 == other.receipt_sha256
            and self.authority_effect == other.authority_effect
            and self.timestamp == other.timestamp
            and self.phi_1 == other.phi_1
            and self.gamma_2 == other.gamma_2
        )

    def __hash__(self) -> int:
        return hash(
            (
                type(self),
                self.letter,
                self.before_class,
                self.after_class,
                self.carrier_hash,
                self.witness_hash,
                self.receipt_sha256,
                self.authority_effect,
                self.timestamp,
                self.phi_1,
                self.gamma_2,
            )
        )


# Backward-compatibility alias
DdaStepV1 = DdcStepV1


def validate_ddc_purity(record: Any) -> Result[DdcStepV1, Refusal]:
    """Validate that a record is a strictly pure DdcStepV1 action."""
    if not isinstance(record, DdcStepV1):
        return Err(
            Refusal(
                code="DDA_IMPURE_RECORD",
                message="Record must be an exact DdcStepV1 instance",
                locus="adversary.stage.domain.ddc",
                details=(("received_type", type(record).__name__),),
            )
        )
    if not isinstance(record.letter, DdcLetter):
        return Err(
            Refusal(
                code="DDA_IMPURE_RECORD",
                message=f"Invalid DDC letter: {record.letter}",
                locus="adversary.stage.domain.ddc",
            )
        )
    if record.authority_effect != AUTHORITY_EFFECT_NONE:
        return Err(
            Refusal(
                code="DDA_IMPURE_RECORD",
                message=f"Authority effect must be {AUTHORITY_EFFECT_NONE}",
                locus="adversary.stage.domain.ddc",
            )
        )
    return Ok(record)


# Backward-compatibility alias
validate_dda_purity = validate_ddc_purity


@dataclass(frozen=True)
class DdcStepReceipt:
    """Canonical receipt for an executed DDC step."""

    step_id: str
    letter: DdcLetter
    input_state_hash: str
    output_state_hash: str
    carrier_hash: str
    diagnostic_before: str
    diagnostic_after: str
    required_witness: str
    witness_hash: str
    refusal_reason: str | None = None
    authority_effect: str = "None"

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.step_id == other.step_id
            and self.letter == other.letter
            and self.input_state_hash == other.input_state_hash
            and self.output_state_hash == other.output_state_hash
            and self.carrier_hash == other.carrier_hash
            and self.diagnostic_before == other.diagnostic_before
            and self.diagnostic_after == other.diagnostic_after
            and self.required_witness == other.required_witness
            and self.witness_hash == other.witness_hash
            and self.refusal_reason == other.refusal_reason
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash(
            (
                type(self),
                self.step_id,
                self.letter,
                self.input_state_hash,
                self.output_state_hash,
                self.carrier_hash,
                self.diagnostic_before,
                self.diagnostic_after,
                self.required_witness,
                self.witness_hash,
                self.refusal_reason,
                self.authority_effect,
            )
        )


# Backward-compatibility alias
DdaStepReceipt = DdcStepReceipt

__all__ = [
    "DdcLetter",
    "DdcStepReceipt",
    "DdcStepV1",
    "validate_ddc_purity",
    "DdaLetter",
    "DdaStepReceipt",
    "DdaStepV1",
    "validate_dda_purity",
]
