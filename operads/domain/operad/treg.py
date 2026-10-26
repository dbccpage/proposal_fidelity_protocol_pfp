"""Regulatory T-Cell (Treg) Supervisor for Operad Compositions.

Monitors anti-skill operations during planar substitution and operadic evaluation.
If an operation's independently checked false-suppression rate
exceeds the tolerance threshold tau (default 2/5 = 40%) once at least
``min_suppressions`` suppressions have been observed (default 3), the supervisor
synthesizes a RegulatoryAntibody record and downgrades the operation to
DIAGNOSTIC_ONLY. The sample floor prevents a single checked false positive
from downgrading a learned blocking gate. Missing evidence never counts.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import re


@dataclass(frozen=True, slots=True)
class CheckedFalsePositive:
    """Trusted host witness; construct only after executing an independent check.

    This internal value is not an LLM payload admission boundary. The OEEIS
    RegulatedGuardState adapter executes the checker before constructing it.
    """

    target_operation: str
    subject_sha256: str
    checker_id: str
    evidence_sha256: str

    def __post_init__(self):
        if not self.target_operation or not self.checker_id or self.checker_id == self.target_operation:
            raise ValueError('INDEPENDENT_CHECKER_REQUIRED')
        if any(re.fullmatch(r'[0-9a-f]{64}', value) is None
               for value in (self.subject_sha256, self.evidence_sha256)):
            raise ValueError('CHECKED_EVIDENCE_REQUIRED')


@dataclass(frozen=True, slots=True)
class OperadTregReceipt:
    """Receipt emitted when an operadic anti-skill is downgraded."""

    treg_id: str
    target_operation: str
    downgraded_authority: str
    toxicity_index: Fraction
    tau_threshold: Fraction
    reason: str
    receipt_hash: str
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if not isinstance(self.treg_id, str) or not self.treg_id.strip():
            raise ValueError("treg_id must be non-empty string")
        if not isinstance(self.target_operation, str) or not self.target_operation.strip():
            raise ValueError("target_operation must be non-empty string")
        if not isinstance(self.toxicity_index, Fraction):
            raise TypeError("toxicity_index must be Fraction")
        if not isinstance(self.tau_threshold, Fraction):
            raise TypeError("tau_threshold must be Fraction")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.treg_id == other.treg_id
            and self.target_operation == other.target_operation
            and self.downgraded_authority == other.downgraded_authority
            and self.toxicity_index == other.toxicity_index
            and self.tau_threshold == other.tau_threshold
            and self.receipt_hash == other.receipt_hash
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.treg_id,
            self.target_operation,
            self.downgraded_authority,
            self.toxicity_index,
            self.tau_threshold,
            self.receipt_hash,
            self.authority_effect,
        ))


class OperadTregSupervisor:
    """Supervises operadic anti-skill operations to prevent autoimmune execution lock."""

    def __init__(
        self,
        tau_threshold: Fraction = Fraction(2, 5),
        min_suppressions: int = 3,
    ) -> None:
        if not isinstance(tau_threshold, Fraction):
            raise TypeError("tau_threshold must be Fraction")
        if not 0 <= tau_threshold <= 1:
            raise ValueError('tau_threshold must lie in [0,1]')
        if type(min_suppressions) is not int or min_suppressions < 1:
            raise ValueError("min_suppressions must be a positive int")
        self.tau_threshold = tau_threshold
        self.min_suppressions = min_suppressions
        self._suppressed_counts: dict[str, int] = {}
        self._danger_counts: dict[str, int] = {}
        self._false_positive_counts: dict[str, int] = {}
        self._seen_subjects: set[tuple[str, str]] = set()
        self._downgraded_operations: set[str] = set()

    def record_operation_step(
        self,
        operation_name: str,
        suppressed: bool,
        danger_confirmed: bool,
        *,
        false_positive: CheckedFalsePositive | None = None,
        learned_detector: bool = False,
        protected: bool = False,
    ) -> OperadTregReceipt | None:
        """Record an operation step and check whether autoimmune toxicity threshold is exceeded."""
        if protected:
            if false_positive is not None:
                raise ValueError('PROTECTED_GATE: mandatory controls cannot be regulated')
            return None
        if false_positive is not None:
            if not learned_detector or type(false_positive) is not CheckedFalsePositive:
                raise ValueError('LEARNED_CHECKED_DETECTOR_REQUIRED')
            if false_positive.target_operation != operation_name:
                raise ValueError('FALSE_POSITIVE_TARGET_MISMATCH')
            if not suppressed or danger_confirmed:
                raise ValueError('CONTRADICTORY_FALSE_POSITIVE')
            identity = (operation_name, false_positive.subject_sha256)
            if identity in self._seen_subjects:
                return None
            self._seen_subjects.add(identity)
        # Unknown/uncorroborated observations do not enter a false-positive rate.
        if not suppressed or (not danger_confirmed and false_positive is None):
            return None
        self._suppressed_counts[operation_name] = self._suppressed_counts.get(operation_name, 0) + 1
        self._danger_counts[operation_name] = self._danger_counts.get(operation_name, 0) + (1 if (suppressed and danger_confirmed) else 0)
        self._false_positive_counts[operation_name] = self._false_positive_counts.get(operation_name, 0) + int(false_positive is not None)

        total_suppressed = self._suppressed_counts[operation_name]
        if total_suppressed < self.min_suppressions:
            return None

        toxicity = Fraction(self._false_positive_counts[operation_name], total_suppressed)

        if learned_detector and toxicity > self.tau_threshold and operation_name not in self._downgraded_operations:
            self._downgraded_operations.add(operation_name)
            treg_id = f"TREG-OP-{hashlib.sha256(f'{operation_name}:{toxicity}'.encode()).hexdigest()[:12]}"
            reason = (
                f"Operad anti-skill {operation_name} toxicity {toxicity} strictly exceeds threshold {self.tau_threshold}. "
                "Authority downgraded from BLOCKING_GATE to DIAGNOSTIC_ONLY."
            )
            receipt_body = {
                "authority_effect": "None",
                "downgraded_authority": "DIAGNOSTIC_ONLY",
                "reason": reason,
                "target_operation": operation_name,
                "tau_threshold": str(self.tau_threshold),
                "toxicity_index": str(toxicity),
                "treg_id": treg_id,
            }
            canonical_bytes = json.dumps(receipt_body, sort_keys=True, separators=(",", ":")).encode("utf-8")
            receipt_hash = hashlib.sha256(canonical_bytes).hexdigest()
            return OperadTregReceipt(
                treg_id=treg_id,
                target_operation=operation_name,
                downgraded_authority="DIAGNOSTIC_ONLY",
                toxicity_index=toxicity,
                tau_threshold=self.tau_threshold,
                reason=reason,
                receipt_hash=receipt_hash,
            )
        return None

    def is_downgraded(self, operation_name: str) -> bool:
        """Check if an operation has been downgraded to DIAGNOSTIC_ONLY."""
        return operation_name in self._downgraded_operations


__all__ = [
    "CheckedFalsePositive",
    "OperadTregReceipt",
    "OperadTregSupervisor",
]
