"""Discrete Deformation Calculus (DDC) 8-Letter Operational Tracer for C031.

Tracks operational transitions in A_DDC = {E, R, C, I, Lambda, D, M, T}
with machine-verifiable SHA-256 chained step receipts for Anomaly-Free
Chiral U(1) Charge Assignments.

Alphabet:
- E: Exact Solution / Repair (chiral primitive anomaly cancellation admitted)
- R: Residual Projection (evaluation of Phi1 = |sum q|, Gamma2 = |sum q^3|)
- C: Context Exposure (case intake, schema and bound validation)
- I: Integration (fixed charges accumulation and target deficits)
- Lambda: Structural Lift (canonical representative quotient, MITM table lift)
- D: Scale Descent (branch-and-bound dimension reduction)
- M: Typed Refusal (vector-like rejection, non-primitive rejection, malformed halt)
- T: Terminalization (final verdict emission and hash sealing)

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

    def __init__(self, run_id: str = "default_run") -> None:
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
            "authority_effect": "None",
            "prev_step_hash": self.prev_step_hash,
        }

        step_bytes = canonical_json_bytes(pre_image)
        step_hash = hashlib.sha256(step_bytes).hexdigest()

        receipt = dict(pre_image)
        receipt["step_hash"] = step_hash

        self.steps.append(receipt)
        self.prev_step_hash = step_hash
        return receipt

    def to_list(self) -> list[dict[str, Any]]:
        return list(self.steps)

    def to_jsonl(self) -> str:
        return "\n".join(json.dumps(s, sort_keys=True) for s in self.steps) + "\n"

    def verify_integrity(self) -> tuple[bool, str]:
        """Verifies cryptographic hash chain integrity."""
        expected_prev = "0" * 64
        for idx, step in enumerate(self.steps):
            if step["step_id"] != idx:
                return False, f"Step ID mismatch at index {idx}: got {step['step_id']}"
            if step["letter"] not in VALID_DDC_LETTERS:
                return False, f"Invalid letter {step['letter']} at step {idx}"
            if step["prev_step_hash"] != expected_prev:
                return (
                    False,
                    f"Chain break at step {idx}: prev_hash {step['prev_step_hash']} != {expected_prev}",
                )

            recomputed_data = {
                "step_id": step["step_id"],
                "run_id": step["run_id"],
                "timestamp_utc": step["timestamp_utc"],
                "letter": step["letter"],
                "action_name": step["action_name"],
                "payload": step["payload"],
                "refusal_reason": step.get("refusal_reason"),
                "authority_effect": "None",
                "prev_step_hash": step["prev_step_hash"],
            }
            computed_hash = hashlib.sha256(canonical_json_bytes(recomputed_data)).hexdigest()
            if computed_hash != step["step_hash"]:
                return (
                    False,
                    f"Hash verification failed at step {idx}: {step['step_hash']} != {computed_hash}",
                )
            expected_prev = step["step_hash"]

        return True, "VALID_CHAIN"
