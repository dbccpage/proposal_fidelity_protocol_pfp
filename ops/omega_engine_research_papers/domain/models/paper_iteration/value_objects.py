#!/usr/bin/env python3
"""Domain Value Objects for the paper_iteration Bounded Context.

Enforces exact-type equality (RULE_VO_EXACT_TYPE_EQUALITY_001) and immutability.
AuthorityEffect: None.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .enums import (
    GateVerdict,
    ResearchGate,
)
from .errors import (
    InvalidGateReceiptError,
)

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class GateReceipt:
    """Immutable evidence-bound gate evaluation receipt."""

    gate: ResearchGate
    verdict: GateVerdict
    reason_code: str
    evaluator_id: str
    evidence_sha256: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.gate, ResearchGate) or not isinstance(self.verdict, GateVerdict):
            raise TypeError("gate and verdict must be typed enums")
        if not self.reason_code.strip() or not self.evaluator_id.strip():
            raise InvalidGateReceiptError("gate receipts need a reason code and evaluator identity")
        if self.verdict is GateVerdict.PASS:
            if self.evidence_sha256 is None or _SHA256.fullmatch(self.evidence_sha256) is None:
                raise InvalidGateReceiptError("passing gates require SHA-256-bound evidence")
        elif self.evidence_sha256 is not None and _SHA256.fullmatch(self.evidence_sha256) is None:
            raise InvalidGateReceiptError("gate evidence must be a lowercase SHA-256 digest")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, GateReceipt)
        return (
            self.gate == other.gate
            and self.verdict == other.verdict
            and self.reason_code == other.reason_code
            and self.evaluator_id == other.evaluator_id
            and self.evidence_sha256 == other.evidence_sha256
        )

    def __hash__(self) -> int:
        return hash(
            (
                type(self),
                self.gate,
                self.verdict,
                self.reason_code,
                self.evaluator_id,
                self.evidence_sha256,
            )
        )

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "gate": self.gate.value,
            "verdict": self.verdict.value,
            "reason_code": self.reason_code,
            "evaluator_id": self.evaluator_id,
            "evidence_sha256": self.evidence_sha256,
        }
