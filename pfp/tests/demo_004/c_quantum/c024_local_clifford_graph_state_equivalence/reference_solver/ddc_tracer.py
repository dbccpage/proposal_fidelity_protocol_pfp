"""Discrete Deformation Calculus (DDC) 8-Letter Operational Tracer for C024.

Tracks operational transitions in A_DDC = {E, R, C, I, Lambda, D, M, T}
with machine-verifiable SHA-256 chained step receipts.

Alphabet:
- E: Exact Verification (replaying local complementation sequence on G)
- R: Residual Projection (differing cut-rank subset identification)
- C: Context Exposure (graph intake and edge validation)
- I: Integration (orbit state indexing, invariant table assembly)
- Lambda: Structural Lift (canonical graph bitmask hashing)
- D: Scale Descent (local complementation move reducing graph difference)
- M: Typed Refusal (malformed graphs, self-loops, out-of-bounds)
- T: Terminalization (final verdict emission)

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

VALID_DDC_LETTERS = frozenset({"E", "R", "C", "I", "Lambda", "D", "M", "T"})


def canonical_json_bytes(obj: Any) -> bytes:
    """Serializes obj to canonical RFC 8785 JSON bytes."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


class DDCTracer:
    """Deterministic chained step receipt tracer for DDC execution."""

    def __init__(self, run_id: str = "c024_run") -> None:
        self.run_id = run_id
        self.steps: list[dict[str, Any]] = []
        self.prev_step_hash = "0" * 64

    def record_step(
        self,
        letter: str,
        action_name: str,
        payload: dict[str, Any] | None = None,
        refusal_reason: str | None = None,
    ) -> dict[str, Any]:
        """Records an operational step and chains its SHA-256 digest."""
        if letter not in VALID_DDC_LETTERS:
            raise ValueError(
                f"Invalid DDC operational letter {letter!r}. Must be in {sorted(VALID_DDC_LETTERS)}"
            )

        step_id = len(self.steps)
        now_utc = datetime.now(timezone.utc).isoformat()
        step_payload = payload if payload is not None else {}

        pre_image = {
            "step_id": step_id,
            "run_id": self.run_id,
            "timestamp_utc": now_utc,
            "letter": letter,
            "action_name": action_name,
            "payload": step_payload,
            "refusal_reason": refusal_reason,
            "parent_step_hash": self.prev_step_hash,
        }

        step_hash = hashlib.sha256(canonical_json_bytes(pre_image)).hexdigest()
        record = {
            **pre_image,
            "step_hash": step_hash,
        }

        self.steps.append(record)
        self.prev_step_hash = step_hash
        return record

    def get_tape(self) -> list[dict[str, Any]]:
        """Returns the full sequence of hash-chained DDC steps."""
        return list(self.steps)

    @property
    def tape_head_hash(self) -> str:
        """Returns the terminal hash of the tape."""
        return self.prev_step_hash


__all__ = [
    "DDCTracer",
    "VALID_DDC_LETTERS",
    "canonical_json_bytes",
]
