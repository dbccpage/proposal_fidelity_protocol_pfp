"""models.py
=========

Domain models for the 10 PFP Intergate transition dynamics, curvature obstructions,
and cognitive defense verdicts.

Governing Epic: EPIC-OE-ADVERSARY-002
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal, Tuple


@dataclass(frozen=True)
class CurvatureObstruction:
    """Represents anholonomy or non-integrable curvature (Omega = d(omega) != 0).

    Occurs when a sequence of cognitive or debate transitions cycles back to an
    earlier state without net residual descent or state progress.
    """

    detected: bool
    loop_edges: Tuple[str, ...] = ()
    holonomy_norm: float = 0.0
    reason: str = ""


@dataclass(frozen=True)
class IntergateSpec:
    """Declarative specification of an intergate loaded from YAML."""

    intergate_id: str
    name: str
    transition_from: str
    transition_to: str
    cognitive_vector: str
    authority_effect: str
    version: str
    doctrine: str
    objective: str
    fences: Tuple[str, ...]
    input_schema: Dict[str, str]
    transition_rules: str
    narrowest_defensible_claim: str
    next_test_needed: str
    source_file: str = ""
    source_sha256: str = ""

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if not isinstance(other, IntergateSpec):
            return False
        return (
            self.intergate_id == other.intergate_id
            and self.name == other.name
            and self.transition_from == other.transition_from
            and self.transition_to == other.transition_to
            and self.cognitive_vector == other.cognitive_vector
            and self.authority_effect == other.authority_effect
            and self.version == other.version
            and self.doctrine == other.doctrine
            and self.objective == other.objective
            and self.fences == other.fences
            and self.input_schema == other.input_schema
            and self.transition_rules == other.transition_rules
            and self.narrowest_defensible_claim == other.narrowest_defensible_claim
            and self.next_test_needed == other.next_test_needed
            and self.source_file == other.source_file
            and self.source_sha256 == other.source_sha256
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.intergate_id,
            self.name,
            self.transition_from,
            self.transition_to,
            self.cognitive_vector,
            self.authority_effect,
            self.version,
            self.doctrine,
            self.objective,
            self.fences,
            tuple(sorted(self.input_schema.items())),
            self.transition_rules,
            self.narrowest_defensible_claim,
            self.next_test_needed,
            self.source_file,
            self.source_sha256,
        ))


@dataclass(frozen=True)
class IntergateEvaluationResult:
    """Outcome of evaluating an intergate transition dynamic."""

    intergate_id: str
    status: Literal["PASS", "HOLD", "BLOCKED", "DIVERTED"]
    transition_from: str
    transition_to: str
    cognitive_vector: str
    curvature_obstruction: CurvatureObstruction
    refusal_code: str | None
    diagnostics: str
    witness: str
    authority_effect: Literal["None"] = "None"
