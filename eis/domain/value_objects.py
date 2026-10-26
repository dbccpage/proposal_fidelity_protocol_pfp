"""Value objects for the Epistemic Immune System (EIS).

Enforces exact-type equality guards and immutable domain value semantics.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Any

# The matcher id of the content-regex matcher. Other matchers declare their own.
REGEX_MATCHER_ID = "regex"


class DangerDecision(str, Enum):
    """Four-way disposition of the Two-Signal Danger Gate."""
    TOLERATED = "TOLERATED"
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"
    DEFENSIVE_LOCKDOWN = "DEFENSIVE_LOCKDOWN"
    QUARANTINED = "QUARANTINED"


class DangerSeverity(str, Enum):
    """Categorical severity scale for Signal 2 danger indications."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True, slots=True)
class Signal1Match:
    """Epitope / syntactic pattern match (Signal 1)."""
    epitope_name: str = ""
    pattern_matched: str = ""
    confidence: float = 1.0
    offset: int = 0
    detector_id: str = ""
    matched_locus: str = ""
    match_signature: str = ""

    def __post_init__(self) -> None:
        if self.detector_id and not self.epitope_name:
            object.__setattr__(self, "epitope_name", self.detector_id)
        if not self.detector_id and self.epitope_name:
            object.__setattr__(self, "detector_id", self.epitope_name)
        if self.matched_locus and not self.pattern_matched:
            object.__setattr__(self, "pattern_matched", self.matched_locus)
        if not self.matched_locus and self.pattern_matched:
            object.__setattr__(self, "matched_locus", self.pattern_matched)
        if self.match_signature and not self.pattern_matched:
            object.__setattr__(self, "pattern_matched", self.match_signature)

        if not isinstance(self.epitope_name, str) or isinstance(self.epitope_name, bool):
            raise TypeError(f"epitope_name must be a str, got {type(self.epitope_name).__name__}")
        if not isinstance(self.pattern_matched, str) or isinstance(self.pattern_matched, bool):
            raise TypeError(f"pattern_matched must be a str, got {type(self.pattern_matched).__name__}")
        if not isinstance(self.confidence, (int, float)) or isinstance(self.confidence, bool):
            raise TypeError(f"confidence must be numeric, got {type(self.confidence).__name__}")
        if not (0.0 <= float(self.confidence) <= 1.0):
            raise ValueError(f"confidence must be in [0.0, 1.0], got {self.confidence}")
        if not isinstance(self.offset, int) or isinstance(self.offset, bool) or self.offset < 0:
            raise ValueError(f"offset must be non-negative int, got {self.offset}")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.epitope_name == other.epitope_name
            and self.pattern_matched == other.pattern_matched
            and abs(self.confidence - other.confidence) < 1e-9
            and self.offset == other.offset
            and self.detector_id == other.detector_id
            and self.matched_locus == other.matched_locus
            and self.match_signature == other.match_signature
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.epitope_name,
            self.pattern_matched,
            round(self.confidence, 6),
            self.offset,
            self.detector_id,
            self.matched_locus,
            self.match_signature,
        ))


@dataclass(frozen=True, slots=True)
class Signal2Danger:
    """Structural / authority / integrity damage indicator (Signal 2 - Danger/Alarmin)."""
    danger_type: str = "danger"
    severity: DangerSeverity = DangerSeverity.MEDIUM
    defect_count: int = 1
    evidence_digest: str = "sha256:0000000000000000000000000000000000000000000000000000000000000000"
    observer_id: str = ""
    evidence_spans: tuple[tuple[int, int], ...] = ()
    source: str = ""
    danger_kind: str = ""
    witness_digest: str = ""
    is_derived: bool = False
    derived_from: Any = None

    def __post_init__(self) -> None:
        if self.source and not self.observer_id:
            object.__setattr__(self, "observer_id", self.source)
        if not self.source and self.observer_id:
            object.__setattr__(self, "source", self.observer_id)
        if self.danger_kind and self.danger_type == "danger":
            object.__setattr__(self, "danger_type", self.danger_kind)
        if not self.danger_kind and self.danger_type != "danger":
            object.__setattr__(self, "danger_kind", self.danger_type)
        if self.witness_digest and self.evidence_digest == "sha256:0000000000000000000000000000000000000000000000000000000000000000":
            object.__setattr__(self, "evidence_digest", self.witness_digest)
        if not self.witness_digest and self.evidence_digest:
            object.__setattr__(self, "witness_digest", self.evidence_digest)

        if not isinstance(self.danger_type, str) or isinstance(self.danger_type, bool):
            raise TypeError(f"danger_type must be a str, got {type(self.danger_type).__name__}")
        if not isinstance(self.severity, DangerSeverity):
            raise TypeError(f"severity must be a DangerSeverity enum, got {type(self.severity).__name__}")
        if not isinstance(self.defect_count, int) or isinstance(self.defect_count, bool) or self.defect_count < 0:
            raise ValueError(f"defect_count must be non-negative int, got {self.defect_count}")
        if not isinstance(self.evidence_digest, str) or isinstance(self.evidence_digest, bool):
            raise TypeError(f"evidence_digest must be a str, got {type(self.evidence_digest).__name__}")
        if type(self.observer_id) is not str:
            raise TypeError(f"observer_id must be a str, got {type(self.observer_id).__name__}")
        if type(self.evidence_spans) is not tuple:
            raise TypeError("evidence_spans must be a tuple of (start, end) int pairs")
        for span in self.evidence_spans:
            if (
                type(span) is not tuple
                or len(span) != 2
                or type(span[0]) is not int
                or type(span[1]) is not int
                or not 0 <= span[0] < span[1]
            ):
                raise ValueError(f"evidence span must be (start, end) ints with 0 <= start < end, got {span!r}")

    @classmethod
    def derive_from_signal1_match(cls, s1: Any) -> "Signal2Danger":
        sig = getattr(s1, "match_signature", "") or getattr(s1, "pattern_matched", "")
        return cls(
            source="derived_from_signal1",
            danger_kind="TWO_SIGNAL_COLLAPSE",
            witness_digest=sig or "collapsed_signature",
            is_derived=True,
            derived_from=s1,
        )

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.danger_type == other.danger_type
            and self.severity == other.severity
            and self.defect_count == other.defect_count
            and self.evidence_digest == other.evidence_digest
            and self.observer_id == other.observer_id
            and self.evidence_spans == other.evidence_spans
            and self.source == other.source
            and self.danger_kind == other.danger_kind
            and self.witness_digest == other.witness_digest
            and self.is_derived is other.is_derived
            and self.derived_from == other.derived_from
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.danger_type,
            self.severity,
            self.defect_count,
            self.evidence_digest,
            self.observer_id,
            self.evidence_spans,
            self.source,
            self.danger_kind,
            self.witness_digest,
            self.is_derived,
        ))


class AllosteryRefusal(ValueError):
    """A typed refusal from the allosteric gate or its Hill parameters."""

    CODES = frozenset(
        {
            "NOT_EXACT",
            "HILL_COEFFICIENT_OUT_OF_RANGE",
            "HALF_MAXIMAL_CONSTANT_OUT_OF_RANGE",
            "SIGNAL_OUT_OF_RANGE",
            "SIGNAL_ABOVE_SENSOR_CAP",
            "THRESHOLD_OUT_OF_RANGE",
            "SENSOR_CAP_OUT_OF_RANGE",
            "SIGNALS_NOT_KEYED",
            "BAD_SENSOR_ID",
            "DUPLICATE_SENSOR",
        }
    )

    def __init__(self, code: str, detail: str = "") -> None:
        if code not in self.CODES:
            raise ValueError(f"unknown allostery refusal code: {code}")
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}" if detail else code)


# Exact inputs are bounded so that a caller cannot make the gate compute with
# arbitrarily large integers. The bound replaces the float `OverflowError` the
# old implementation raised on large inputs with a typed refusal.
MAX_HILL_COEFFICIENT = 16
MAX_EXACT_BITS = 256


def exact_rational(value: object, label: str) -> Fraction:
    """`value` as a Fraction if it is an exact int or Fraction; refuse otherwise.

    Floats and booleans are refused, never converted: a float is already an
    approximation, and `True` is not a signal strength.
    """
    if type(value) is int:
        result = Fraction(value)
    elif type(value) is Fraction:
        result = value
    else:
        raise AllosteryRefusal(
            "NOT_EXACT", f"{label} must be int or Fraction, got {type(value).__name__}"
        )
    if (
        result.numerator.bit_length() > MAX_EXACT_BITS
        or result.denominator.bit_length() > MAX_EXACT_BITS
    ):
        raise AllosteryRefusal("SIGNAL_OUT_OF_RANGE", f"{label} exceeds {MAX_EXACT_BITS} bits")
    return result


@dataclass(frozen=True, slots=True)
class HillParameters:
    """Exact Hill-curve parameters: an integer coefficient n and a constant K > 0.

    The response is H(S) = S**n / (K**n + S**n), computed with Fractions.
    """
    hill_coefficient: int
    half_maximal_constant: Fraction

    def __post_init__(self) -> None:
        if type(self.hill_coefficient) is not int:
            raise AllosteryRefusal(
                "NOT_EXACT",
                f"hill_coefficient must be an int, got {type(self.hill_coefficient).__name__}",
            )
        if not 1 <= self.hill_coefficient <= MAX_HILL_COEFFICIENT:
            raise AllosteryRefusal(
                "HILL_COEFFICIENT_OUT_OF_RANGE",
                f"hill_coefficient must be in [1, {MAX_HILL_COEFFICIENT}], got {self.hill_coefficient}",
            )
        constant = exact_rational(self.half_maximal_constant, "half_maximal_constant")
        if constant <= 0:
            raise AllosteryRefusal(
                "HALF_MAXIMAL_CONSTANT_OUT_OF_RANGE", "half_maximal_constant must be > 0"
            )
        object.__setattr__(self, "half_maximal_constant", constant)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.hill_coefficient == other.hill_coefficient
            and self.half_maximal_constant == other.half_maximal_constant
        )

    def __hash__(self) -> int:
        return hash((type(self), self.hill_coefficient, self.half_maximal_constant))

    def calculate_cooperativity(self, signal_strength: object) -> Fraction:
        """Exact Hill response H(S) = S**n / (K**n + S**n) for an exact S >= 0."""
        signal = exact_rational(signal_strength, "signal_strength")
        if signal < 0:
            raise AllosteryRefusal("SIGNAL_OUT_OF_RANGE", "signal_strength must be >= 0")
        if signal == 0:
            return Fraction(0)
        n = self.hill_coefficient
        signal_pow = signal ** n
        return signal_pow / (self.half_maximal_constant ** n + signal_pow)


@dataclass(frozen=True, slots=True)
class DetectorRule:
    """A detector rule, bound to the matcher that executes it.

    `matcher_id` names the matcher that runs `match_pattern`. For the regex
    matcher (`REGEX_MATCHER_ID`) the pattern is a regular expression in the
    admitted subset of `safe_pattern`; for a host-check matcher it is the exact
    finding code the rule selects. A matcher refuses a rule bound to a different
    matcher, and the thymus screens a rule with the matcher that will run it, so
    the predicate that is screened is the predicate that executes.

    `half_life_runs` is an idle limit: the number of consecutive unmatched
    screening runs after which the rule is deactivated. The decay is linear
    (a counter), not exponential. `affinity_score` is a caller-maintained tally;
    no code in this package selects rules by it. It stays a finite non-negative
    int or float (not a Fraction) because existing callers, including Symbol
    Game tests, pass float tallies and boosts; booleans, NaN and infinities are
    refused.
    """
    rule_id: str
    target_epitope: str
    match_pattern: str
    generation: int = 1
    affinity_score: float = 1.0
    half_life_runs: int = 10
    runs_idle: int = 0
    is_active: bool = True
    matcher_id: str = REGEX_MATCHER_ID

    def __post_init__(self) -> None:
        if type(self.matcher_id) is not str or not self.matcher_id.strip():
            raise ValueError("matcher_id must be a non-empty string naming the matcher that runs the rule")
        if not isinstance(self.rule_id, str) or not self.rule_id.strip():
            raise ValueError("rule_id must be a non-empty string")
        if not isinstance(self.target_epitope, str) or not self.target_epitope.strip():
            raise ValueError("target_epitope must be a non-empty string")
        if not isinstance(self.match_pattern, str) or not self.match_pattern.strip():
            raise ValueError("match_pattern must be a non-empty string")
        if type(self.generation) is not int or self.generation < 1:
            raise ValueError("generation must be an exact int >= 1")
        if type(self.affinity_score) not in (int, float) or not math.isfinite(self.affinity_score):
            raise ValueError("affinity_score must be a finite int or float (not bool, NaN or infinity)")
        if self.affinity_score < 0:
            raise ValueError("affinity_score must be non-negative")
        if type(self.half_life_runs) is not int or self.half_life_runs < 1:
            raise ValueError("half_life_runs must be an exact int >= 1")
        if type(self.runs_idle) is not int or self.runs_idle < 0:
            raise ValueError("runs_idle must be an exact int >= 0")
        if type(self.is_active) is not bool:
            raise TypeError("is_active must be a boolean")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.rule_id == other.rule_id
            and self.target_epitope == other.target_epitope
            and self.match_pattern == other.match_pattern
            and self.generation == other.generation
            and abs(self.affinity_score - other.affinity_score) < 1e-9
            and self.half_life_runs == other.half_life_runs
            and self.runs_idle == other.runs_idle
            and self.is_active is other.is_active
            and self.matcher_id == other.matcher_id
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.rule_id,
            self.target_epitope,
            self.match_pattern,
            self.generation,
            round(self.affinity_score, 6),
            self.half_life_runs,
            self.runs_idle,
            self.is_active,
            self.matcher_id,
        ))
