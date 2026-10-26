"""Core computational engine for Epistemic Immune System (EIS).

AuthorityEffect: None.

Formalizes operations across Levels 00–10:
- Level 00: Innate Pharmacy Barriers (InnateBarrier)
- Level 01: Component Role Partitioning (RolePartition)
- Level 02: Fixture Polarity & Near-Misses (FixtureGate)
- Level 03: Central Tolerance & Thymus Gate (ThymusGate)
- Level 04: Learned Guard Two-Signal Activation (TwoSignalGuard)
- Level 05: Independent Observation Support Policy (SupportPolicy)
- Level 06: Provisional Custody & Review Queue (ProvisionalCustody)
- Level 07: Clonal Selection & Affinity Maturation (ClonalSelectionEngine)
- Level 08: Regulatory Supervision & Anergy (TregSupervisor)
- Level 09: External Admission Boundary (ExternalAdmissionBoundary)
- Level 10: Antimorphism Polarity & Bounded Telemetry (AntimorphismEmitter)
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


class Role(str, Enum):
    PROPOSER = "PROPOSER"
    REVIEWER = "REVIEWER"
    VERIFIER = "VERIFIER"


@dataclass(frozen=True)
class Antigen:
    """Untrusted candidate stimulus, proposal, or payload."""

    id: int
    payload: str
    claims: Tuple[str, ...]
    source: str
    byte_length: int = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "byte_length", len(self.payload.encode("utf-8")))


@dataclass(frozen=True)
class SelfSpec:
    """Protected core baseline specification invariant."""

    spec_id: int
    name: str
    invariant_pattern: str


@dataclass(frozen=True)
class Antibody:
    """Learned detector guard targeting failure modes or hallucination patterns."""

    id: int
    target_pattern: str
    affinity_threshold: float
    is_anergic: bool = False

    def digest(self) -> str:
        s = f"{self.id}:{self.target_pattern}:{self.affinity_threshold}:{self.is_anergic}"
        return hashlib.sha256(s.encode("utf-8")).hexdigest()


class InnateBarrier:
    """Level 00: Innate Pharmacy Barriers enforcing size limits and schema validation."""

    def __init__(self, max_bytes: int = 10000, forbidden_terms: Optional[List[str]] = None) -> None:
        self.max_bytes = max_bytes
        self.forbidden_terms = forbidden_terms or [
            "weaponized",
            "safe ASI",
            "true intelligence",
            "flawless",
        ]

    def validate_payload(self, antigen: Antigen) -> Tuple[bool, Optional[str]]:
        if antigen.byte_length > self.max_bytes:
            return False, f"Payload size {antigen.byte_length} exceeds limit {self.max_bytes}"
        for term in self.forbidden_terms:
            if term.lower() in antigen.payload.lower():
                return False, f"Forbidden non-claim-hygiene token detected: '{term}'"
        return True, None


class RolePartition:
    """Level 01: Component Role Partitioning enforcing triad separation."""

    def __init__(self) -> None:
        pass

    @staticmethod
    def verify_triad_separation(proposer_id: str, reviewer_id: str, verifier_id: str) -> bool:
        """Verifies Proposer != Reviewer, Reviewer != Verifier, and Proposer != Verifier."""
        actors = {proposer_id, reviewer_id, verifier_id}
        return len(actors) == 3


class FixtureGate:
    """Level 02: Fixture Polarity & Near-Misses verifying positive and negative fixtures."""

    def __init__(self) -> None:
        self.positive_fixtures: List[Tuple[str, bool]] = []
        self.negative_fixtures: List[Tuple[str, bool]] = []

    def add_positive_fixture(self, input_text: str) -> None:
        self.positive_fixtures.append((input_text, True))

    def add_negative_fixture(self, near_miss_text: str) -> None:
        self.negative_fixtures.append((near_miss_text, False))

    def evaluate_detector(self, detector_fn: Callable[[str], bool]) -> Tuple[bool, float]:
        """Evaluates detector: must return True on positive fixtures and False on negative near-misses."""
        if not self.positive_fixtures or not self.negative_fixtures:
            return False, 0.0
        passed = 0
        total = len(self.positive_fixtures) + len(self.negative_fixtures)
        for text, expected in self.positive_fixtures:
            if detector_fn(text) == expected:
                passed += 1
        for text, expected in self.negative_fixtures:
            if detector_fn(text) == expected:
                passed += 1
        accuracy = passed / total
        return accuracy == 1.0, accuracy


class ThymusGate:
    """Level 03: Central Tolerance & Thymus Gate performing negative selection against self-specs."""

    def __init__(self, protected_specs: List[SelfSpec]) -> None:
        self.protected_specs = protected_specs

    def test_negative_selection(
        self, candidate_antibody: Antibody
    ) -> Tuple[bool, Optional[SelfSpec]]:
        """If candidate antibody matches any protected self-specification, it is destroyed (autoimmune)."""
        for spec in self.protected_specs:
            if (
                candidate_antibody.target_pattern.lower() in spec.invariant_pattern.lower()
                or spec.invariant_pattern.lower() in candidate_antibody.target_pattern.lower()
            ):
                return False, spec  # Destroyed by central tolerance
        return True, None  # Admitted to peripheral circulation


class TwoSignalGuard:
    """Level 04: Learned Guard Two-Signal Activation requiring co-stimulatory danger signal."""

    def __init__(self, antibody: Antibody) -> None:
        self.antibody = antibody

    def evaluate(self, payload: str, danger_signal_present: bool) -> str:
        """Signal 1: Pattern match. Signal 2: Co-stimulatory danger signal."""
        if self.antibody.is_anergic:
            return "SUPPRESSED_BY_TREG"
        signal1 = self.antibody.target_pattern.lower() in payload.lower()
        if signal1 and danger_signal_present:
            return "ACTIVATED_IMMUNE_RESPONSE"
        elif signal1 and not danger_signal_present:
            return "SIGNAL1_ONLY_QUIESCENT"
        return "QUIESCENT"


class SupportPolicy:
    """Level 05: Independent Observation Support Policy requiring k independent witnesses."""

    def __init__(self, required_k: int = 3) -> None:
        self.required_k = required_k

    def check_consensus(self, witnesses: List[Tuple[str, bool]]) -> bool:
        """Verifies at least k distinct witness channels agree."""
        unique_approvers = {ch for ch, approved in witnesses if approved}
        return len(unique_approvers) >= self.required_k


class ProvisionalCustody:
    """Level 06: Provisional Custody & Review Queue managing probationary antibodies."""

    def __init__(self, probation_evaluations: int = 5) -> None:
        self.probation_limit = probation_evaluations
        self.queue: Dict[int, Dict[str, Any]] = {}

    def admit_provisional(self, ab: Antibody) -> None:
        self.queue[ab.id] = {
            "antibody": ab,
            "eval_count": 0,
            "false_alarms": 0,
            "promoted": False,
        }

    def record_evaluation(self, ab_id: int, was_false_alarm: bool) -> bool:
        if ab_id not in self.queue:
            return False
        entry = self.queue[ab_id]
        entry["eval_count"] += 1
        if was_false_alarm:
            entry["false_alarms"] += 1
        if entry["eval_count"] >= self.probation_limit and entry["false_alarms"] == 0:
            entry["promoted"] = True
            return True
        return False

    def is_promoted(self, ab_id: int) -> bool:
        return self.queue.get(ab_id, {}).get("promoted", False)


class ClonalSelectionEngine:
    """Level 07: Clonal Selection & Affinity Maturation optimizing detector sensitivity."""

    def __init__(self) -> None:
        self._next_id = 9000

    def compute_affinity(self, antibody: Antibody, target: str) -> float:
        """Calculates binding affinity as token overlap ratio."""
        ab_tokens = set(antibody.target_pattern.lower().split())
        target_tokens = set(target.lower().split())
        if not ab_tokens or not target_tokens:
            return 0.0
        intersection = ab_tokens.intersection(target_tokens)
        return len(intersection) / len(ab_tokens)

    def somatic_hypermutation(self, parent_ab: Antibody, refine_token: str) -> Antibody:
        self._next_id += 1
        new_pattern = f"{parent_ab.target_pattern} {refine_token}"
        return Antibody(
            id=self._next_id,
            target_pattern=new_pattern,
            affinity_threshold=min(1.0, parent_ab.affinity_threshold + 0.05),
            is_anergic=False,
        )


class TregSupervisor:
    """Level 08: Regulatory Supervision & Anergy suppressing hyperactive antibodies."""

    def __init__(self, false_positive_threshold: float = 0.20) -> None:
        self.fp_threshold = false_positive_threshold

    def evaluate_regulatory_status(self, total_triggers: int, false_positives: int) -> bool:
        """Returns True if antibody must be forced into anergy due to excessive false positives."""
        if total_triggers < 5:
            return False
        fp_rate = false_positives / total_triggers
        return fp_rate >= self.fp_threshold

    def induce_anergy(self, ab: Antibody) -> Antibody:
        return Antibody(
            id=ab.id,
            target_pattern=ab.target_pattern,
            affinity_threshold=ab.affinity_threshold,
            is_anergic=True,
        )


class ExternalAdmissionBoundary:
    """Level 09: External Admission Boundary enforcing fail-closed intake."""

    def __init__(self, innate: InnateBarrier, thymus: ThymusGate) -> None:
        self.innate = innate
        self.thymus = thymus

    def filter_antigen(self, antigen: Antigen) -> Tuple[bool, Dict[str, Any]]:
        passed_innate, reason = self.innate.validate_payload(antigen)
        if not passed_innate:
            receipt = {
                "antigen_id": antigen.id,
                "admitted": False,
                "refusal_reason": reason,
                "stage": "INNATE_BARRIER",
                "authority_effect": "None",
            }
            return False, receipt
        return True, {
            "antigen_id": antigen.id,
            "admitted": True,
            "stage": "ADMITTED_PERIPHERAL",
            "authority_effect": "None",
        }


class AntimorphismEmitter:
    """Level 10: Antimorphism Polarity & Bounded Telemetry producing typed receipts."""

    def __init__(self) -> None:
        self.receipts: List[Dict[str, Any]] = []

    def emit_receipt(
        self,
        event_name: str,
        subject_id: int,
        details: Dict[str, Any],
        is_success: bool = True,
    ) -> Dict[str, Any]:
        receipt = {
            "receipt_id": len(self.receipts) + 1,
            "event_name": event_name,
            "subject_id": subject_id,
            "is_success": is_success,
            "details": details,
            "authority_effect": "None",
        }
        serialized = json.dumps(receipt, sort_keys=True)
        receipt["digest"] = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        self.receipts.append(receipt)
        return receipt
