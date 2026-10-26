"""Clonal Selection with Parent-Child Kill Condition and Exponential Half-Life Decay.

Models Darwinian clonal selection and affinity maturation with strict central tolerance safety.
Parent-Child Kill Condition:
If any mutated clone matches a sample in the sealed Self Panel, both clone AND parent lineage
are destroyed immediately (emitting ApoptosisReceipt / KillConditionReceipt with PURGED_SELF_REACTIVE).

Exponential Half-Life Decay:
Idle rules decay exponentially towards zero activity and deactivate after tau half-life intervals.

Zero outward dependencies. Strict ZERO-FLOAT law.
Exact-type equality enforced on all Value Objects.
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import re
from typing import Any, Sequence

from .thymus import ApoptosisReceipt, SelfPanel


def _assert_zero_float(val: Any, field_name: str) -> None:
    if isinstance(val, float):
        raise TypeError(
            f"ZERO-FLOAT Invariant violated on {field_name}: float values are strictly forbidden; "
            "use fractions.Fraction or Q"
        )


@dataclass(frozen=True, slots=True)
class ClonalCandidate:
    """An antibody detector candidate undergoing clonal evolution."""

    rule_id: str
    target_epitope: str
    match_pattern: str
    parent_id: str | None = None
    generation: int = 1
    affinity_score: Fraction = Fraction(1, 1)
    half_life_runs: int = 10
    runs_idle: int = 0
    is_active: bool = True

    def __post_init__(self) -> None:
        _assert_zero_float(self.affinity_score, "affinity_score")
        if not isinstance(self.rule_id, str) or not self.rule_id.strip():
            raise ValueError("rule_id must be a non-empty string")
        if not isinstance(self.target_epitope, str) or not self.target_epitope.strip():
            raise ValueError("target_epitope must be a non-empty string")
        if not isinstance(self.match_pattern, str) or not self.match_pattern.strip():
            raise ValueError("match_pattern must be a non-empty string")
        if self.parent_id is not None and not isinstance(self.parent_id, str):
            raise TypeError("parent_id must be a string or None")
        if not isinstance(self.generation, int) or self.generation < 1:
            raise ValueError("generation must be a positive integer >= 1")
        if not isinstance(self.affinity_score, (Fraction, int)):
            if hasattr(self.affinity_score, "num") and hasattr(self.affinity_score, "den"):
                pass
            else:
                raise TypeError(f"affinity_score must be Fraction or Q, got {type(self.affinity_score).__name__}")
        if not isinstance(self.half_life_runs, int) or self.half_life_runs < 1:
            raise ValueError("half_life_runs must be >= 1")
        if not isinstance(self.runs_idle, int) or self.runs_idle < 0:
            raise ValueError("runs_idle must be non-negative")
        if not isinstance(self.is_active, bool):
            raise TypeError("is_active must be a boolean")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ClonalCandidate)
        return (
            self.rule_id == other.rule_id
            and self.target_epitope == other.target_epitope
            and self.match_pattern == other.match_pattern
            and self.parent_id == other.parent_id
            and self.generation == other.generation
            and self.affinity_score == other.affinity_score
            and self.half_life_runs == other.half_life_runs
            and self.runs_idle == other.runs_idle
            and self.is_active is other.is_active
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.rule_id,
            self.target_epitope,
            self.match_pattern,
            self.parent_id,
            self.generation,
            self.affinity_score,
            self.half_life_runs,
            self.runs_idle,
            self.is_active,
        ))


# Compatibility alias
DetectorRule = ClonalCandidate


@dataclass(frozen=True, slots=True)
class KillConditionReceipt:
    """Cryptographic evidence receipt sealing a parent-child lineage purge."""

    receipt_id: str
    clone_id: str
    parent_id: str
    violating_sample_id: str
    violating_sample_digest: str
    status: str = "PURGED_SELF_REACTIVE"
    canonical_hash: str = ""
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if not isinstance(self.receipt_id, str) or not self.receipt_id.strip():
            raise ValueError("receipt_id must be a non-empty string")
        if not isinstance(self.clone_id, str) or not self.clone_id.strip():
            raise ValueError("clone_id must be a non-empty string")
        if not isinstance(self.parent_id, str) or not self.parent_id.strip():
            raise ValueError("parent_id must be a non-empty string")
        if self.status != "PURGED_SELF_REACTIVE":
            raise ValueError("status must be 'PURGED_SELF_REACTIVE'")
        if self.authority_effect != "None":
            raise ValueError("authority_effect must be 'None'")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, KillConditionReceipt)
        return (
            self.receipt_id == other.receipt_id
            and self.clone_id == other.clone_id
            and self.parent_id == other.parent_id
            and self.violating_sample_id == other.violating_sample_id
            and self.violating_sample_digest == other.violating_sample_digest
            and self.status == other.status
            and self.canonical_hash == other.canonical_hash
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.receipt_id,
            self.clone_id,
            self.parent_id,
            self.violating_sample_id,
            self.violating_sample_digest,
            self.status,
            self.canonical_hash,
            self.authority_effect,
        ))

    @classmethod
    def create(
        cls,
        clone_id: str,
        parent_id: str,
        violating_sample_id: str,
        violating_sample_digest: str,
        receipt_id: str = "",
    ) -> KillConditionReceipt:
        """Create a sealed KillConditionReceipt."""
        if not receipt_id:
            h_seed = hashlib.sha256(f"KILL:{clone_id}:{parent_id}:{violating_sample_id}".encode("utf-8")).hexdigest()
            receipt_id = f"KILL-{h_seed[:12]}"

        body = {
            "authority_effect": "None",
            "clone_id": clone_id,
            "parent_id": parent_id,
            "receipt_id": receipt_id,
            "status": "PURGED_SELF_REACTIVE",
            "violating_sample_digest": violating_sample_digest,
            "violating_sample_id": violating_sample_id,
        }
        canonical_bytes = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
        canonical_hash = hashlib.sha256(canonical_bytes).hexdigest()

        return cls(
            receipt_id=receipt_id,
            clone_id=clone_id,
            parent_id=parent_id,
            violating_sample_id=violating_sample_id,
            violating_sample_digest=violating_sample_digest,
            status="PURGED_SELF_REACTIVE",
            canonical_hash=canonical_hash,
            authority_effect="None",
        )


@dataclass(frozen=True, slots=True)
class KillConditionRefusal:
    """Typed refusal for a clone whose match pattern cannot be compiled.

    The clone cannot cross-react with the self panel, so the parent is spared,
    but the clone is not admissible and must not enter the repertoire.
    """

    clone_id: str
    parent_id: str
    match_pattern: str
    reason: str
    code: str = "INVALID_MATCH_PATTERN"
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if not isinstance(self.clone_id, str) or not self.clone_id.strip():
            raise ValueError("clone_id must be a non-empty string")
        if not isinstance(self.parent_id, str) or not self.parent_id.strip():
            raise ValueError("parent_id must be a non-empty string")
        if self.code != "INVALID_MATCH_PATTERN":
            raise ValueError("code must be 'INVALID_MATCH_PATTERN'")
        if self.authority_effect != "None":
            raise ValueError("authority_effect must be 'None'")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, KillConditionRefusal)
        return (
            self.clone_id == other.clone_id
            and self.parent_id == other.parent_id
            and self.match_pattern == other.match_pattern
            and self.reason == other.reason
            and self.code == other.code
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.clone_id,
            self.parent_id,
            self.match_pattern,
            self.reason,
            self.code,
            self.authority_effect,
        ))


class ClonalSelectionEngine:
    """Clonal selection engine with central tolerance kill condition and exponential decay."""

    @staticmethod
    def mutate_rule(
        parent: ClonalCandidate,
        new_epitope: str | None = None,
        new_pattern: str | None = None,
        clone_id: str | None = None,
    ) -> ClonalCandidate:
        """Generate a mutated child clone from parent detector rule."""
        if clone_id is None:
            clone_id = f"{parent.rule_id}-MUT-{parent.generation + 1}"
        return ClonalCandidate(
            rule_id=clone_id,
            target_epitope=new_epitope or parent.target_epitope,
            match_pattern=new_pattern or parent.match_pattern,
            parent_id=parent.rule_id,
            generation=parent.generation + 1,
            affinity_score=parent.affinity_score,
            half_life_runs=parent.half_life_runs,
            runs_idle=0,
            is_active=True,
        )

    @staticmethod
    def check_kill_condition(
        clone: ClonalCandidate,
        parent: ClonalCandidate,
        self_panel: SelfPanel | Sequence[Any],
    ) -> tuple[bool, KillConditionReceipt | KillConditionRefusal | None]:
        """Parent-Child Kill Condition: If clone cross-reacts with SelfPanel, both clone and parent are purged.

        Returns ``(True, KillConditionReceipt)`` on a self-panel match, ``(False, None)`` for a
        clean clone, and ``(False, KillConditionRefusal)`` when the clone's pattern does not compile.
        """
        try:
            pattern = re.compile(clone.match_pattern, re.IGNORECASE)
        except re.error as err:
            return False, KillConditionRefusal(
                clone_id=clone.rule_id,
                parent_id=parent.rule_id,
                match_pattern=clone.match_pattern,
                reason=f"Invalid regular expression syntax: {err}",
            )

        for entry in self_panel:
            content = getattr(entry, "content", str(entry))
            sample_id = getattr(entry, "entry_id", "SELF_FIXTURE")
            sample_digest = getattr(entry, "content_sha256", hashlib.sha256(content.encode("utf-8")).hexdigest())

            if pattern.search(content):
                # Trigger parent-child kill condition
                receipt = KillConditionReceipt.create(
                    clone_id=clone.rule_id,
                    parent_id=parent.rule_id,
                    violating_sample_id=sample_id,
                    violating_sample_digest=sample_digest,
                )
                return True, receipt

        return False, None

    @staticmethod
    def stimulate_rule(
        rule: ClonalCandidate,
        boost: Fraction = Fraction(1, 5),
    ) -> ClonalCandidate:
        """Stimulate an antibody on pathogen match, resetting idle count and boosting affinity."""
        _assert_zero_float(boost, "boost")
        if not isinstance(boost, (Fraction, int)):
            if hasattr(boost, "num") and hasattr(boost, "den"):
                boost = Fraction(boost.num, boost.den)
            else:
                raise TypeError(f"boost must be Fraction, int, or Q, got {type(boost).__name__}")
        new_affinity = rule.affinity_score + boost
        return ClonalCandidate(
            rule_id=rule.rule_id,
            target_epitope=rule.target_epitope,
            match_pattern=rule.match_pattern,
            parent_id=rule.parent_id,
            generation=rule.generation,
            affinity_score=new_affinity,
            half_life_runs=rule.half_life_runs,
            runs_idle=0,
            is_active=True,
        )

    @staticmethod
    def apply_half_life_decay(
        rule: ClonalCandidate,
        elapsed_runs: int = 1,
        tau: int | None = None,
    ) -> ClonalCandidate:
        """Apply exponential half-life decay timer. Deactivates rule when idle >= half_life_runs."""
        if type(elapsed_runs) is not int or elapsed_runs < 1:
            raise ValueError("elapsed_runs must be a positive integer >= 1")

        tau_effective = tau if tau is not None else rule.half_life_runs
        if type(tau_effective) is not int or tau_effective < 1:
            raise ValueError("tau must be a positive integer >= 1")
        new_runs_idle = rule.runs_idle + elapsed_runs

        # Exponential step decay w(t) = w0 * (1/2)^floor(t / tau), where t counts idle runs.
        # Halve once for each tau interval this call completes, so repeated calls
        # telescope to the same result as one call covering the same idle runs.
        completed_intervals = new_runs_idle // tau_effective - rule.runs_idle // tau_effective
        decay_factor = Fraction(1, 2**completed_intervals)
        new_affinity = max(Fraction(0, 1), rule.affinity_score * decay_factor)

        # Deactivate when idle intervals reached or exceeded half_life_runs
        is_active = new_runs_idle < rule.half_life_runs

        return ClonalCandidate(
            rule_id=rule.rule_id,
            target_epitope=rule.target_epitope,
            match_pattern=rule.match_pattern,
            parent_id=rule.parent_id,
            generation=rule.generation,
            affinity_score=new_affinity,
            half_life_runs=rule.half_life_runs,
            runs_idle=new_runs_idle,
            is_active=is_active,
        )
