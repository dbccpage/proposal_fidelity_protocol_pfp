# AuthorityEffect: None.
"""
DDC Tracer for C041: Discrete Deformation Calculus on Lean 4 Proof Search.

Alphabet:
  A_DDC = {E, R, C, I, Λ, D, M, T}
  C: Context initialization (lemma statement, prelude, toolchain pinned)
  I: Initial candidate proof proposal
  R: Residual evaluation (compiler errors and open goals measured)
  Λ: Lift / transformation (range split, auxiliary lemma, tactic switch)
  D: Descent step (strict reduction in open goals / errors)
  E: Exact closure (proof kernel-verified, zero errors, clean axioms)
  M: Typed refusal or budget limit
  T: Terminal commitment
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

VALID_DDC_LETTERS = {"E", "R", "C", "I", "Λ", "D", "M", "T"}


@dataclass
class DdcStepRecord:
    letter: str
    action: str
    phi1: int  # Obstruction: open goals + compiler errors
    active_count: int  # Banned constructs / unwhitelisted axioms
    gamma2: int = 0  # Cycle obstruction (must remain 0)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "letter": self.letter,
            "action": self.action,
            "phi1": self.phi1,
            "active_count": self.active_count,
            "gamma2": self.gamma2,
            "details": self.details,
        }


class LeanProofDdcTracer:
    """
    Maintains a deterministic DDC trace for Lean 4 proof exploration.
    """

    def __init__(self, case_id: str):
        self.case_id = case_id
        self.steps: List[DdcStepRecord] = []

    def record(
        self,
        letter: str,
        action: str,
        phi1: int = 0,
        active_count: int = 0,
        gamma2: int = 0,
        details: Dict[str, Any] = None,
    ) -> DdcStepRecord:
        if letter not in VALID_DDC_LETTERS:
            raise ValueError(f"Invalid DDC letter: {letter}")
        step = DdcStepRecord(
            letter=letter,
            action=action,
            phi1=phi1,
            active_count=active_count,
            gamma2=gamma2,
            details=details or {},
        )
        self.steps.append(step)
        return step

    def get_trace_string(self) -> str:
        return "".join(step.letter for step in self.steps)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "trace_string": self.get_trace_string(),
            "step_count": len(self.steps),
            "steps": [s.to_dict() for s in self.steps],
        }
