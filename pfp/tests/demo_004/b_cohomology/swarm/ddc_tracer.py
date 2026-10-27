"""DDC (Discrete Deformation Calculus) Operational Trace Recorder & Tape Verifier.

Records transitions in the 8-letter DDC alphabet:
    A_DDC = {C, R, E, I, Λ, D, M, T}

Connects directly to the native sovereign Rust host via:
    RustSymbolGameHost.invoke("ddc_verify_tape", payload)
verifying tape legality, step laws, and cryptographic hash chaining.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Sequence

from pfp.ffi import RustSymbolGameHost, get_default_host
from adversary.infrastructure.cochain_adapter import to_canonical_rational_str


@dataclass
class DdcStepRecord:
    """A single step in the DDC operational trace."""

    letter: str
    carrier: str
    residual: list[Fraction]
    phi: Fraction
    gamma: Fraction
    adequate: bool = True
    receipt: bool = False
    loss_ledger: bool = False
    lift_licence: bool = False
    reason: str | None = None


class DdcTracer:
    """Records DDC transitions and validates tapes with sovereign Rust crates."""

    def __init__(
        self,
        task_id: str,
        initial_carrier: str = "carrier_0",
        host: RustSymbolGameHost | None = None,
    ) -> None:
        self.task_id = task_id
        self.initial_carrier = initial_carrier
        self._host = host
        self.steps: list[DdcStepRecord] = []
        self._initial_state = {
            "carrier": initial_carrier,
            "residual": ["0"],
            "phi": "0",
            "gamma": "0",
            "adequate": True,
        }

    def get_host(self) -> RustSymbolGameHost:
        if self._host is not None:
            return self._host
        return get_default_host()

    def set_initial_state(
        self,
        carrier: str,
        residual: Sequence[Fraction],
        phi: Fraction,
        gamma: Fraction,
        adequate: bool = True,
    ) -> None:
        self._initial_state = {
            "carrier": carrier,
            "residual": [to_canonical_rational_str(r) for r in residual] or ["0"],
            "phi": to_canonical_rational_str(phi),
            "gamma": to_canonical_rational_str(gamma),
            "adequate": adequate,
        }

    def record_step(
        self,
        letter: str,
        carrier: str,
        residual: Sequence[Fraction],
        phi: Fraction,
        gamma: Fraction,
        adequate: bool = True,
        receipt: bool = False,
        loss_ledger: bool = False,
        lift_licence: bool = False,
        reason: str | None = None,
    ) -> None:
        """Record an operational transition."""
        self.steps.append(
            DdcStepRecord(
                letter=letter,
                carrier=carrier,
                residual=list(residual),
                phi=phi,
                gamma=gamma,
                adequate=adequate,
                receipt=receipt,
                loss_ledger=loss_ledger,
                lift_licence=lift_licence,
                reason=reason,
            )
        )

    def to_rust_verify_payload(self) -> dict[str, Any]:
        """Format request payload matching Rust DdcVerifyTapeRequestV1."""
        wire_steps = []
        for s in self.steps:
            wire_steps.append(
                {
                    "letter": s.letter,
                    "after": {
                        "carrier": s.carrier,
                        "residual": [to_canonical_rational_str(r) for r in s.residual] or ["0"],
                        "phi": to_canonical_rational_str(s.phi),
                        "gamma": to_canonical_rational_str(s.gamma),
                        "adequate": s.adequate,
                    },
                    "witness": {
                        "receipt": s.receipt,
                        "loss_ledger": s.loss_ledger,
                        "lift_licence": s.lift_licence,
                        "reason": s.reason,
                    },
                }
            )
        return {
            "initial_state": self._initial_state,
            "steps": wire_steps,
        }

    def verify_tape_with_native_host(self) -> dict[str, Any]:
        """Verify tape automaton laws in sovereign Rust host."""
        host = self.get_host()
        payload = self.to_rust_verify_payload()
        res = host.invoke("ddc_verify_tape", payload)
        if not res.is_ok:
            return {"lawful": False, "violations": [f"FFI_ERROR: {res.unwrap_err()}"]}
        data = res.unwrap().get("result", {})
        return data

    def write_jsonl(self, output_path: Path) -> Path:
        """Write canonical RFC 8785 JSON-L tape actions."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        lines = []
        for i, s in enumerate(self.steps):
            rec = {
                "step_index": i,
                "task_id": self.task_id,
                "letter": s.letter,
                "carrier": s.carrier,
                "phi": to_canonical_rational_str(s.phi),
                "gamma": to_canonical_rational_str(s.gamma),
                "adequate": s.adequate,
                "witness": {
                    "receipt": s.receipt,
                    "loss_ledger": s.loss_ledger,
                    "lift_licence": s.lift_licence,
                    "reason": s.reason,
                },
            }
            line = json.dumps(rec, sort_keys=True)
            lines.append(line)

        output_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        return output_path
