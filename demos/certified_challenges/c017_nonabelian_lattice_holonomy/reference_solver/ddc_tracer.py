r"""Discrete Deformation Calculus (DDC) 8-Letter Operational Tracer for C017.

Alphabet:
- E: Evaluation / measurement of plaquette curvature and holonomy
- R: Retraction step / spanning tree gauge fixing
- C: Candidate formation / connection validation
- I: Invariance check / path independence and group associativity
- \Lambda: Lift / global torus cycle holonomy lift
- D: Defect calculation (number of non-flat plaquettes / curvature obstruction)
- M: Mitigation / gauge transformation / typed refusal
- T: Terminal reality gate admission
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


class DDCTracer:
    def __init__(self, challenge_id: str = "c017_nonabelian_lattice_holonomy") -> None:
        self.challenge_id = challenge_id
        self.trace: list[dict[str, Any]] = []
        self.step_counter = 0

    def record_step(
        self,
        letter: str,
        operation: str,
        payload: dict[str, Any] | None = None,
        defect_count: int = 0,
        refusal_reason: str | None = None,
    ) -> dict[str, Any]:
        valid_letters = {"E", "R", "C", "I", "Lambda", "\u039b", "D", "M", "T"}
        if letter not in valid_letters:
            raise ValueError(f"Invalid DDC letter: {letter}")

        step = {
            "step": self.step_counter,
            "letter": letter,
            "operation": operation,
            "defect_count": defect_count,
            "payload": payload or {},
        }
        if refusal_reason:
            step["refusal_reason"] = refusal_reason
        self.trace.append(step)
        self.step_counter += 1
        return step

    def export_receipt(self, status: str, final_result: dict[str, Any]) -> dict[str, Any]:
        trace_str = json.dumps(self.trace, sort_keys=True)
        trace_hash = hashlib.sha256(trace_str.encode("utf-8")).hexdigest()
        return {
            "challenge_id": self.challenge_id,
            "status": status,
            "step_count": len(self.trace),
            "trace_sha256": trace_hash,
            "trace": self.trace,
            "final_result": final_result,
        }
