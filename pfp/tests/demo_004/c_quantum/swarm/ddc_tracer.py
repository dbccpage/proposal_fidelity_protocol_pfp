"""DDC (Discrete Deformation Calculus) Operational Trace Recorder & Tape Verifier for C021.

Records transitions in the 8-letter DDC alphabet:
    A_DDC = {C, R, E, I, Λ, D, M, T}

Connects directly to the native sovereign Rust host via:
    RustSymbolGameHost.invoke_runtime("ddc_verify_tape", payload)
verifying tape legality, step laws, and cryptographic hash chaining.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping, Sequence

from operating_system.adapters.rust_host.ffi import RustSymbolGameHost
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
        initial_carrier: str = "carrier_q40",
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
        return RustSymbolGameHost()

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
        valid_letters = {"C", "R", "E", "I", "Λ", "D", "M", "T"}
        if letter not in valid_letters:
            raise ValueError(f"Invalid DDC letter '{letter}', must be one of {valid_letters}")

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

    def to_tape_dict(self) -> dict[str, Any]:
        """Formats the trace into the DdcVerifyTapeRequestV1 wire schema."""
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

    def verify_tape_with_rust_host(self) -> dict[str, Any]:
        """Dispatches ddc_verify_tape to sovereign RustSymbolGameHost."""
        host = self.get_host()
        tape_req = self.to_tape_dict()
        res = host.invoke_runtime("ddc_verify_tape", tape_req)
        if not res.is_ok:
            return {"lawful": False, "violations": [f"FFI_ERROR: {res.unwrap_err()}"]}
        outcome = res.unwrap()
        data = outcome.get("result", {})
        if not isinstance(data, Mapping):
            return {"lawful": False, "violations": ["MALFORMED_NATIVE_RESULT"]}
        return {**data, "native_outcome": outcome}

    def write_actions_jsonl(self, out_path: Path) -> None:
        """Writes canonical StructureBench dda_actions.jsonl output."""
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            for i, step in enumerate(self.steps):
                line = {
                    "step_index": i,
                    "letter": step.letter,
                    "carrier": step.carrier,
                    "phi": str(step.phi),
                    "gamma": str(step.gamma),
                    "adequate": step.adequate,
                    "reason": step.reason,
                }
                f.write(json.dumps(line, sort_keys=True) + "\n")
