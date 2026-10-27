"""Discrete Deformation Calculus (DDC) 8-Letter Operational Trace for C032.

Implements the DDC operational trace alphabet:
  A_DDC = {E, R, C, I, Lambda, D, M, T}
with SHA-256 chained step receipts and machine-verifiable transitions.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

ALLOWED_DDC_LETTERS = frozenset({"E", "R", "C", "I", "Lambda", "D", "M", "T"})


@dataclass(frozen=True)
class DdcStepReceipt:
    step_index: int
    operation: str
    letter: str
    payload_hash: str
    prev_receipt_hash: str
    receipt_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DdcTracer:
    """Records and cryptographically seals DDC operational transitions."""

    def __init__(self, challenge_id: str = "c032_six_d_sugra_anomaly_cancellation") -> None:
        self.challenge_id = challenge_id
        self.steps: list[DdcStepReceipt] = []
        self._prev_hash: str = "0" * 64

    def emit_step(self, operation: str, letter: str, payload: Any = None) -> DdcStepReceipt:
        if letter not in ALLOWED_DDC_LETTERS:
            raise ValueError(
                f"Illegal DDC letter: {letter!r}. Allowed: {sorted(ALLOWED_DDC_LETTERS)}"
            )

        payload_bytes = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")
        payload_hash = hashlib.sha256(payload_bytes).hexdigest()

        step_idx = len(self.steps)
        content_to_hash = (
            f"{step_idx}:{operation}:{letter}:{payload_hash}:{self._prev_hash}".encode("utf-8")
        )
        receipt_hash = hashlib.sha256(content_to_hash).hexdigest()

        receipt = DdcStepReceipt(
            step_index=step_idx,
            operation=operation,
            letter=letter,
            payload_hash=payload_hash,
            prev_receipt_hash=self._prev_hash,
            receipt_hash=receipt_hash,
        )
        self.steps.append(receipt)
        self._prev_hash = receipt_hash
        return receipt

    def verify_integrity(self) -> tuple[bool, str]:
        prev = "0" * 64
        for idx, s in enumerate(self.steps):
            if s.step_index != idx:
                return False, f"Step index gap at {idx}: found {s.step_index}"
            if s.prev_receipt_hash != prev:
                return False, f"Broken cryptographic link at step {idx}"
            expected_content = f"{idx}:{s.operation}:{s.letter}:{s.payload_hash}:{prev}".encode(
                "utf-8"
            )
            expected_hash = hashlib.sha256(expected_content).hexdigest()
            if s.receipt_hash != expected_hash:
                return False, f"Corrupted receipt hash at step {idx}"
            prev = s.receipt_hash
        return True, "VALID_CHAIN"

    def export_trace(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self.steps]
