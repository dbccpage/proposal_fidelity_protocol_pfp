"""Discrete Deformation Calculus (DDC) 8-letter operational tracer for C036.

Traces transitions over alphabet A_DDC = {E, R, C, I, Lambda, D, M, T}.
Maintains SHA-256 chained step receipts for deterministic reproduction.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

VALID_DDC_LETTERS = frozenset({"E", "R", "C", "I", "Lambda", "D", "M", "T"})


class DDCTracer:
    """Records operational steps with SHA-256 hash chaining."""

    def __init__(self, challenge_id: str = "c036_quintic_gromov_witten_mirror") -> None:
        self.challenge_id = challenge_id
        self.steps: list[dict[str, Any]] = []
        self._last_digest = hashlib.sha256(challenge_id.encode("utf-8")).hexdigest()

    def record_step(self, letter: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Appends an operational step and updates running SHA-256 digest."""
        if letter not in VALID_DDC_LETTERS:
            raise ValueError(f"Invalid DDC letter: {letter}")

        step_idx = len(self.steps)
        canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        step_data = f"{step_idx}:{letter}:{canonical_payload}:{self._last_digest}".encode("utf-8")
        step_digest = hashlib.sha256(step_data).hexdigest()
        self._last_digest = step_digest

        entry = {
            "step": step_idx,
            "letter": letter,
            "payload": payload,
            "digest": step_digest,
        }
        self.steps.append(entry)
        return entry

    def export_trace(self) -> dict[str, Any]:
        """Exports the full operational trace with summary metrics."""
        letters = [s["letter"] for s in self.steps]
        return {
            "challenge_id": self.challenge_id,
            "step_count": len(self.steps),
            "letters": letters,
            "final_digest": self._last_digest,
            "steps": self.steps,
        }
