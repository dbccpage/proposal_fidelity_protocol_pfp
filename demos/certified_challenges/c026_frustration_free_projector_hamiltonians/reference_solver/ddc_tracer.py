# AuthorityEffect: None.
"""Discrete Deformation Calculus (DDC) 8-Letter Operational Tracer for C026.

Tracks operational transitions in A_DDC = {E, R, C, I, Lambda, D, M, T}
with machine-verifiable SHA-256 chained step receipts.

Alphabet:
- E: Exact Verification (testing annihilation P_i v = 0, independence, rank identity)
- R: Residual Evaluation (evaluating <psi|H|psi>)
- C: Context Exposure (intake sites, local dims, terms)
- I: Initial Integration (kernel of initial terms)
- Lambda: Structural Lift (Kronecker extension to full D x D space)
- D: Scale Descent (shrinking running common kernel as terms intersect)
- M: Typed Refusal (malformed projector, invalid site, dimension out of bounds)
- T: Terminalization (verdict: SOLVED with basis or left inverse, OUT_OF_SCOPE, UNKNOWN)
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

VALID_DDC_LETTERS = frozenset({"E", "R", "C", "I", "Lambda", "D", "M", "T"})


def canonical_json_bytes(obj: Any) -> bytes:
    """Serializes obj to canonical RFC 8785 JSON bytes."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


class DDCTracer:
    """Deterministic chained step receipt tracer for DDC execution."""

    def __init__(self, run_id: str = "c026_run") -> None:
        self.run_id = run_id
        self.steps: List[Dict[str, Any]] = []
        self.prev_step_hash = "0" * 64

    def record_step(
        self,
        letter: str,
        action_name: str,
        payload: Optional[Dict[str, Any]] = None,
        refusal_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
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
            "prev_step_hash": self.prev_step_hash,
        }
        if refusal_reason:
            pre_image["refusal_reason"] = refusal_reason

        step_bytes = canonical_json_bytes(pre_image)
        step_hash = hashlib.sha256(step_bytes).hexdigest()

        receipt = {
            **pre_image,
            "step_hash": step_hash,
        }
        self.steps.append(receipt)
        self.prev_step_hash = step_hash
        return receipt

    def get_trace_sequence(self) -> str:
        """Returns the concatenated string of DDC letters recorded so far."""
        return "".join(step["letter"] for step in self.steps)

    def verify_integrity(self) -> bool:
        """Verifies hash-chain integrity of the recorded trace."""
        expected_prev = "0" * 64
        for step in self.steps:
            if step["prev_step_hash"] != expected_prev:
                return False
            check_obj = {k: v for k, v in step.items() if k != "step_hash"}
            check_bytes = canonical_json_bytes(check_obj)
            computed_hash = hashlib.sha256(check_bytes).hexdigest()
            if computed_hash != step["step_hash"]:
                return False
            expected_prev = step["step_hash"]
        return True
