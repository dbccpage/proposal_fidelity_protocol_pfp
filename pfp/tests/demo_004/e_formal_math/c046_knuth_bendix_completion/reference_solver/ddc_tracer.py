# AuthorityEffect: None.
"""
DDC Operational Tracer for C046 (Knuth-Bendix Completion).
Emits deterministic operational traces typed in the 8-letter DDC alphabet:
A_DDC = {E, R, C, I, Lambda, D, M, T}.
"""

from typing import Any, Dict, List


class DDCTracer:
    """Collects deterministic DDC operational steps."""

    def __init__(self, case_id: str):
        self.case_id = case_id
        self.trace: List[Dict[str, Any]] = []

    def record_step(self, op: str, detail: str, meta: Dict[str, Any] = None):
        assert op in {"E", "R", "C", "I", "Lambda", "D", "M", "T"}, f"Invalid DDC op: {op}"
        self.trace.append(
            {"step_index": len(self.trace), "op": op, "detail": detail, "meta": meta or {}}
        )

    def get_summary(self) -> Dict[str, Any]:
        letters = "".join(step["op"] for step in self.trace)
        return {
            "case_id": self.case_id,
            "trace_string": letters,
            "step_count": len(self.trace),
            "steps": self.trace,
        }
