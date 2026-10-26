"""
Evidence Receipts and Residual Observations.
============================================

AuthorityEffect: None.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Sequence


class EvidenceType(str, enum.Enum):
    COMPILATION = "compilation"
    BUDGET_AUDIT = "budget_audit"
    ASSOCIATIVITY = "associativity"
    SLICE_VERIFICATION = "slice_verification"
    COCHAIN_OBSTRUCTION = "cochain_obstruction"


@dataclass(frozen=True)
class EvidenceObservation:
    """Individual observation recorded during an operad evaluation pass."""
    key: str
    value: Any
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(frozen=True)
class EvidenceReceipt:
    """Immutable evidence receipt emitted by the operad compiler and runners."""
    receipt_id: str
    evidence_type: EvidenceType
    passed: bool
    observations: tuple[EvidenceObservation, ...] = ()
    metadata: Dict[str, Any] = field(default_factory=dict)
    emitted_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "evidence_type": self.evidence_type.value,
            "passed": self.passed,
            "observations": [{"key": o.key, "value": o.value, "timestamp": o.timestamp} for o in self.observations],
            "metadata": dict(self.metadata),
            "emitted_at": self.emitted_at,
        }
