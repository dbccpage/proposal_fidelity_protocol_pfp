"""Typed evidence the Adversary terminal gate may rely on.

Three kinds of evidence reach Act VII, and each one is a value object here so
that no act can pass a float, a keyword, or a narrative in its place:

* ``ObstructionMeasurementV1`` -- the exact carrier measurement. Either
  ``MEASURED`` (exact rational Phi1 and Gamma2 behind a verified certificate)
  or ``NOT_MEASURED`` (no scorer, no carrier, no host, or an unverified
  certificate). ``NOT_MEASURED`` can never authorize.
* ``CandidateCheckV1`` -- the challenge checker's verdict on one candidate,
  bound to the candidate's content digest and to the SHA-256 of the checker
  receipt bytes. Only ``ACCEPTED`` can authorize.
* ``StructuredCritiqueV1`` -- a critic seat's reply parsed from one fenced
  ``critique`` JSON block. A reply that does not parse is ``MALFORMED`` and
  blocks its candidate.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Any

from adversary.stage.domain.packets import CHALLENGE_KINDS

from .native import NativeOperationPort
from .native import value as native_value

_SHA256_REF = re.compile(r"sha256:[0-9a-f]{64}\Z")
_RATIONAL_TEXT = re.compile(r"-?(0|[1-9][0-9]*)(/[1-9][0-9]*)?\Z")


def sha256_ref(data: bytes) -> str:
    """``sha256:<hex>`` of exact bytes."""
    return "sha256:" + hashlib.sha256(data).hexdigest()


def is_sha256_ref(value: Any) -> bool:
    return type(value) is str and _SHA256_REF.fullmatch(value) is not None


def parse_exact_rational(value: Any) -> Fraction:
    """Admit an exact rational: an ``int``, a ``Fraction``, or ``"p"`` / ``"p/q"`` text.

    ``float`` and ``bool`` are refused, never converted: a float cannot carry
    an exact value, and ``True`` is not the integer one in a cochain.
    """
    if type(value) is int:
        return Fraction(value)
    if type(value) is Fraction:
        return value
    if type(value) is str:
        text = value.strip()
        if _RATIONAL_TEXT.fullmatch(text) is None:
            raise ValueError(f"not an exact rational literal: {value!r}")
        return Fraction(text)
    raise TypeError(
        f"exact rational required (int, Fraction or 'p/q' text), got {type(value).__name__}"
    )


def canonical_rational(value: Fraction) -> str:
    """Wire form: ``"n"`` for integers, ``"n/d"`` otherwise (never ``"n/1"``)."""
    if type(value) is not Fraction:
        raise TypeError("canonical_rational requires a Fraction")
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


class MeasurementStatus(str, Enum):
    MEASURED = "MEASURED"
    NOT_MEASURED = "NOT_MEASURED"


@dataclass(frozen=True)
class ObstructionMeasurementV1:
    """Exact carrier measurement, or an explicit statement that none exists."""

    status: MeasurementStatus
    backend: str
    phi1: Fraction | None = None
    gamma2: Fraction | None = None
    defect_count: int = 0
    active_obstructions: tuple[str, ...] = ()
    certificate_verified: bool = False
    dual_witness: tuple[tuple[str, Fraction], ...] = ()
    reason: str = ""

    def __post_init__(self) -> None:
        if type(self.status) is not MeasurementStatus:
            raise TypeError("status must be a MeasurementStatus")
        if type(self.backend) is not str or not self.backend.strip():
            raise ValueError("backend must be a nonempty string")
        if type(self.certificate_verified) is not bool:
            raise TypeError("certificate_verified must be an exact bool")
        if type(self.defect_count) is not int or self.defect_count < 0:
            raise TypeError("defect_count must be a non-negative exact int")
        object.__setattr__(self, "active_obstructions", tuple(self.active_obstructions))
        if any(type(item) is not str for item in self.active_obstructions):
            raise TypeError("active_obstructions must be strings")
        object.__setattr__(self, "dual_witness", tuple(tuple(pair) for pair in self.dual_witness))
        for pair in self.dual_witness:
            if len(pair) != 2 or type(pair[0]) is not str or type(pair[1]) is not Fraction:
                raise TypeError("dual_witness entries must be (edge label, Fraction)")
        if type(self.reason) is not str:
            raise TypeError("reason must be a string")
        if self.status is MeasurementStatus.MEASURED:
            for name in ("phi1", "gamma2"):
                value = getattr(self, name)
                if type(value) is not Fraction or value < 0:
                    raise TypeError(f"a MEASURED {name} must be a non-negative Fraction")
            if not self.certificate_verified:
                raise ValueError(
                    "a measurement without a verified certificate is NOT_MEASURED, not MEASURED"
                )
            if self.defect_count != len(self.active_obstructions):
                raise ValueError("defect_count must equal the number of active obstructions")
        else:
            if self.phi1 is not None or self.gamma2 is not None:
                raise ValueError("a NOT_MEASURED result carries no Phi1 or Gamma2 value")
            if self.certificate_verified or self.dual_witness:
                raise ValueError("a NOT_MEASURED result carries no certificate")
            if not self.reason.strip():
                raise ValueError("a NOT_MEASURED result must state why")

    @classmethod
    def not_measured(cls, reason: str, *, backend: str) -> ObstructionMeasurementV1:
        return cls(status=MeasurementStatus.NOT_MEASURED, backend=backend, reason=reason)

    @property
    def is_measured(self) -> bool:
        return self.status is MeasurementStatus.MEASURED

    def is_exact_joint_zero(self) -> bool:
        """Exact ``Phi1 == 0 and Gamma2 == 0`` behind a verified certificate; no tolerance."""
        return (
            self.status is MeasurementStatus.MEASURED
            and self.certificate_verified is True
            and self.phi1 == 0
            and self.gamma2 == 0
        )

    def has_open_obstruction(self) -> bool:
        return self.is_measured and (self.phi1 != 0 or self.gamma2 != 0)

    def phi1_text(self) -> str | None:
        return None if self.phi1 is None else canonical_rational(self.phi1)

    def gamma2_text(self) -> str | None:
        return None if self.gamma2 is None else canonical_rational(self.gamma2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_obstructions": list(self.active_obstructions),
            "backend": self.backend,
            "certificate_verified": self.certificate_verified,
            "defect_count": self.defect_count,
            "dual_witness": [
                [edge, canonical_rational(value)] for edge, value in self.dual_witness
            ],
            "gamma2": self.gamma2_text(),
            "phi1": self.phi1_text(),
            "reason": self.reason,
            "status": self.status.value,
        }

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.to_dict() == other.to_dict()

    def __hash__(self) -> int:
        return hash((type(self), json.dumps(self.to_dict(), sort_keys=True)))


class CheckerVerdict(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    NOT_MEASURED = "NOT_MEASURED"


@dataclass(frozen=True)
class CandidateCheckV1:
    """A challenge checker's verdict on one candidate, bound by digests.

    ``checker_receipt_sha256`` must be the SHA-256 of ``checker_receipt_bytes``,
    so the verdict can be replayed from the persisted receipt. A
    ``NOT_MEASURED`` check has no receipt and can never authorize.
    """

    verdict: CheckerVerdict
    candidate_id: str
    candidate_content_sha256: str
    checker_id: str
    checker_receipt_sha256: str | None = None
    checker_receipt_bytes: bytes = b""
    reason: str = ""

    def __post_init__(self) -> None:
        if type(self.verdict) is not CheckerVerdict:
            raise TypeError("verdict must be a CheckerVerdict")
        for name in ("candidate_id", "checker_id"):
            value = getattr(self, name)
            if type(value) is not str or not value.strip():
                raise ValueError(f"{name} must be a nonempty string")
        if not is_sha256_ref(self.candidate_content_sha256):
            raise ValueError("candidate_content_sha256 must be a sha256:<hex> reference")
        if type(self.checker_receipt_bytes) is not bytes:
            raise TypeError("checker_receipt_bytes must be bytes")
        if type(self.reason) is not str:
            raise TypeError("reason must be a string")
        if self.verdict is CheckerVerdict.NOT_MEASURED:
            if self.checker_receipt_sha256 is not None or self.checker_receipt_bytes:
                raise ValueError("a NOT_MEASURED check carries no checker receipt")
            if not self.reason.strip():
                raise ValueError("a NOT_MEASURED check must state why")
        else:
            if not self.checker_receipt_bytes:
                raise ValueError(f"a {self.verdict.value} check requires the checker receipt bytes")
            if self.checker_receipt_sha256 != sha256_ref(self.checker_receipt_bytes):
                raise ValueError("checker_receipt_sha256 is not the digest of the receipt bytes")

    def binds(self, candidate_id: str, artifact_refs: tuple[str, ...]) -> bool:
        """True when this check names exactly this candidate and its content bytes."""
        return self.candidate_id == candidate_id and self.candidate_content_sha256 in tuple(
            artifact_refs
        )

    @property
    def can_authorize(self) -> bool:
        return self.verdict is CheckerVerdict.ACCEPTED

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_content_sha256": self.candidate_content_sha256,
            "candidate_id": self.candidate_id,
            "checker_id": self.checker_id,
            "checker_receipt_hex": self.checker_receipt_bytes.hex(),
            "checker_receipt_sha256": self.checker_receipt_sha256,
            "reason": self.reason,
            "verdict": self.verdict.value,
        }

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.to_dict() == other.to_dict()

    def __hash__(self) -> int:
        return hash((type(self), json.dumps(self.to_dict(), sort_keys=True)))


@dataclass(frozen=True)
class CheckerReceiptRecordV1:
    """The fields a checker receipt must state before it can back a verdict.

    Parsed from the receipt bytes themselves (a JSON object). It is the
    ``CandidateCheckV1`` shape minus what only the bout knows: ``verdict``,
    ``candidate_content_sha256`` (the digest of the answer bytes the checker
    judged) and ``checker_id``; ``candidate_id`` is optional.
    """

    verdict: CheckerVerdict
    candidate_content_sha256: str
    checker_id: str
    candidate_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_content_sha256": self.candidate_content_sha256,
            "candidate_id": self.candidate_id,
            "checker_id": self.checker_id,
            "verdict": self.verdict.value,
        }


def parse_checker_receipt(receipt_bytes: bytes, *, native_support: NativeOperationPort) -> CheckerReceiptRecordV1:
    """Parse checker receipt bytes; raise ``ValueError`` naming the first defect.

    A digest alone is not evidence: the bytes must say who checked what and
    with which verdict.
    """
    if type(receipt_bytes) is not bytes or not receipt_bytes:
        raise ValueError("the checker receipt is empty")
    record = native_value(native_support, "checker_receipt", receipt_hex=receipt_bytes.hex())
    record["verdict"] = CheckerVerdict(record["verdict"])
    return CheckerReceiptRecordV1(**record)


class CritiqueStatus(str, Enum):
    STRUCTURED = "STRUCTURED"
    MALFORMED = "MALFORMED"


#: The reply contract a critic seat is asked to follow, quoted in its prompt.
CRITIQUE_REPLY_CONTRACT = (
    "End your reply with exactly one fenced block tagged `critique` holding a JSON "
    'object: {"blocking": true or false, "counterexample": "<a concrete input or '
    'witness that breaks the candidate>" or null, "kind": optional, one of '
    + ", ".join(sorted(CHALLENGE_KINDS))
    + "}. A blocking critique must give a nonempty counterexample."
)


@dataclass(frozen=True)
class StructuredCritiqueV1:
    """A critic's typed finding. ``MALFORMED`` always blocks its candidate."""

    status: CritiqueStatus
    blocking: bool
    counterexample: str
    challenge_kind: str
    parse_error: str = ""

    def __post_init__(self) -> None:
        if type(self.status) is not CritiqueStatus:
            raise TypeError("status must be a CritiqueStatus")
        if type(self.blocking) is not bool:
            raise TypeError("blocking must be an exact bool")
        if self.challenge_kind not in CHALLENGE_KINDS:
            raise ValueError("challenge_kind is not closed")
        if self.status is CritiqueStatus.MALFORMED and not self.blocking:
            raise ValueError("a MALFORMED critique must block (fail closed)")

    def to_dict(self) -> dict[str, Any]:
        return {
            "blocking": self.blocking,
            "challenge_kind": self.challenge_kind,
            "counterexample": self.counterexample,
            "parse_error": self.parse_error,
            "status": self.status.value,
        }


def parse_structured_critique(reply_text: Any, *, native_support: NativeOperationPort) -> StructuredCritiqueV1:
    """Parse the typed critic block in Rust, preserving malformed findings."""
    record = native_value(native_support, "critique", reply=reply_text)
    record["status"] = CritiqueStatus(record["status"])
    return StructuredCritiqueV1(**record)


@dataclass(frozen=True)
class PrimeDescentReceiptV1:
    """Exact operational receipt emitted by the prime descent coordinator.

    AuthorityEffect: None.
    """

    status: MeasurementStatus
    backend: str
    run_id: str
    letters: str = ""
    terminal_status: str = "Pending"
    phi1: Fraction | None = None
    gamma2: Fraction | None = None
    b1_over_q: int = 0
    laws_passed: bool = False
    authority_effect: str = "None"
    reason: str = ""

    def __post_init__(self) -> None:
        if type(self.status) is not MeasurementStatus:
            raise TypeError("status must be a MeasurementStatus")
        if type(self.backend) is not str or not self.backend.strip():
            raise ValueError("backend must be a nonempty string")
        if type(self.run_id) is not str or not self.run_id.strip():
            raise ValueError("run_id must be a nonempty string")
        if type(self.letters) is not str:
            raise TypeError("letters must be a string")
        if type(self.terminal_status) is not str:
            raise TypeError("terminal_status must be a string")
        if type(self.b1_over_q) is not int or self.b1_over_q < 0:
            raise TypeError("b1_over_q must be a non-negative int")
        if type(self.laws_passed) is not bool:
            raise TypeError("laws_passed must be a bool")
        if type(self.authority_effect) is not str:
            raise TypeError("authority_effect must be a string")
        if type(self.reason) is not str:
            raise TypeError("reason must be a string")
        if self.status is MeasurementStatus.MEASURED:
            if type(self.phi1) is not Fraction or self.phi1 < 0:
                raise TypeError("a MEASURED phi1 must be a non-negative Fraction")
            if type(self.gamma2) is not Fraction or self.gamma2 < 0:
                raise TypeError("a MEASURED gamma2 must be a non-negative Fraction")
        else:
            if self.phi1 is not None or self.gamma2 is not None:
                raise ValueError("a NOT_MEASURED result carries no Phi1 or Gamma2 value")
            if not self.reason.strip():
                raise ValueError("a NOT_MEASURED result must state why")

    @classmethod
    def not_measured(
        cls, reason: str, *, backend: str, run_id: str = "not_measured"
    ) -> PrimeDescentReceiptV1:
        return cls(
            status=MeasurementStatus.NOT_MEASURED,
            backend=backend,
            run_id=run_id,
            reason=reason,
        )

    @property
    def is_measured(self) -> bool:
        return self.status is MeasurementStatus.MEASURED

    def is_terminalized(self) -> bool:
        return (
            self.is_measured
            and self.terminal_status in ("Terminalized", "CLOSED_RESIDUAL", "AUTHORIZED")
            and self.laws_passed
        )


__all__ = [
    "CRITIQUE_REPLY_CONTRACT",
    "CandidateCheckV1",
    "CheckerReceiptRecordV1",
    "CheckerVerdict",
    "CritiqueStatus",
    "MeasurementStatus",
    "ObstructionMeasurementV1",
    "PrimeDescentReceiptV1",
    "StructuredCritiqueV1",
    "canonical_rational",
    "is_sha256_ref",
    "parse_checker_receipt",
    "parse_exact_rational",
    "parse_structured_critique",
    "sha256_ref",
]
