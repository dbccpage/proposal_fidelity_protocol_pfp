# AuthorityEffect: None.
"""
DDC (Discrete Deformation Calculus) 8-Letter Operational Tracer for C042.

Alphabet:
  A_DDC = {E, R, C, I, Λ, D, M, T}
"""

from __future__ import annotations

import time
from typing import Any, Dict, List


class DDCTracer:
    """Records deterministic operational transitions under A_DDC."""

    VALID_ALPHABET = {"E", "R", "C", "I", "Λ", "D", "M", "T"}

    def __init__(self, case_id: str):
        self.case_id = case_id
        self.trace: List[Dict[str, Any]] = []

    def record(self, letter: str, payload: str, metadata: Dict[str, Any] | None = None) -> None:
        if letter not in self.VALID_ALPHABET:
            raise ValueError(f"Invalid DDC transition letter: {letter}")
        step = {
            "step": len(self.trace) + 1,
            "letter": letter,
            "payload": payload,
            "metadata": metadata or {},
            "timestamp": time.time(),
        }
        self.trace.append(step)

    def trace_letters(self) -> str:
        return "".join(step["letter"] for step in self.trace)
