"""Domain models and value objects for cohomology challenge operations.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
import json
from typing import Any, Mapping


@dataclass(frozen=True)
class CohomologyCase:
    """Immutable domain representation of a cohomology challenge input case."""

    case_id: str
    challenge_id: str
    payload: dict[str, Any]

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, CohomologyCase)
        return self.case_id == other.case_id and self.challenge_id == other.challenge_id and self.payload == other.payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CohomologyCase:
        cid = str(data.get("challenge") or data.get("challenge_id") or "c011").lower()
        case_id = str(data.get("case_id") or data.get("id") or "unnamed")
        return cls(case_id=case_id, challenge_id=cid, payload=dict(data))


@dataclass(frozen=True)
class CohomologyResult:
    """Immutable domain representation of a certified solver outcome."""

    case_id: str
    challenge_id: str
    status: str
    data: dict[str, Any] = field(default_factory=dict)
    witness: dict[str, Any] = field(default_factory=dict)
    native_attestation: str | None = None

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, CohomologyResult)
        return (
            self.case_id == other.case_id
            and self.challenge_id == other.challenge_id
            and self.status == other.status
            and self.data == other.data
            and self.witness == other.witness
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"status": self.status}
        if self.status == "OUT_OF_SCOPE":
            out["witness"] = self.witness
        elif self.status == "UNKNOWN":
            out["refusal"] = self.witness.get("refusal", "BUDGET_EXHAUSTED")
        else:
            out.update(self.data)
        return out


@dataclass(frozen=True)
class CertificateCheckResult:
    """Immutable verdict emitted by the independent certificate checker."""

    case_id: str
    challenge_id: str
    passed: bool
    status: str
    error: str | None = None
    telemetry: dict[str, Any] = field(default_factory=dict)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, CertificateCheckResult)
        return (
            self.case_id == other.case_id
            and self.challenge_id == other.challenge_id
            and self.passed == other.passed
            and self.status == other.status
            and self.error == other.error
        )
