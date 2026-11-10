"""Discrete Deformation Calculus (DDC) 8-Letter Operational Tracer for C022.

Tracks operational transitions in A_DDC = {E, R, C, I, Lambda, D, M, T}
with machine-verifiable SHA-256 chained step receipts.

Alphabet:
- E: Exact Repair (basis extraction, minimization)
- R: Residual Projection (commutation evaluation)
- C: Context Exposure (case intake and bound validation)
- I: Integration (certificate synthesis)
- Lambda: Structural Lift
- D: Scale Descent
- M: Typed Refusal (malformed or out-of-scope halt)
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

    def __init__(self, run_id: str = "c022_run") -> None:
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
            "action": action_name,
            "prev_step_hash": self.prev_step_hash,
            "payload": step_payload,
            "refusal_reason": refusal_reason,
        }

        step_hash = hashlib.sha256(canonical_json_bytes(pre_image)).hexdigest()
        receipt = {**pre_image, "step_hash": step_hash}
        self.steps.append(receipt)
        self.prev_step_hash = step_hash
        return receipt

    def verify_integrity(self) -> bool:
        """Verifies full cryptographic chain integrity from root step."""
        expected_prev = "0" * 64
        for step in self.steps:
            if step["prev_step_hash"] != expected_prev:
                return False
            recomputed = hashlib.sha256(
                canonical_json_bytes({k: v for k, v in step.items() if k != "step_hash"})
            ).hexdigest()
            if recomputed != step["step_hash"]:
                return False
            expected_prev = step["step_hash"]
        return True

    def export_trace(self) -> list[dict[str, Any]]:
        return list(self.steps)
