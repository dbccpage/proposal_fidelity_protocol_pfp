"""Turn Driver Controller with strict descent gating and cemetery routing (U05).

Coordinates:
- Prompt artifact rendering (turn_driver_next_prompt)
- Candidate step execution against strict descent invariant (turn_driver_step)
- Writing accepted moves to ddc_trace.jsonl
- Writing rejected/non-descending moves to cemetery.jsonl
AuthorityEffect: None.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Sequence

from operations.domain.rop.result import Err, Ok, Refusal, Result
from pfp.domain.immune.danger_gate import (
    Signal1AstMatch,
    Signal2DangerState,
)
from pfp.domain.immune.turn_loop_wiring import (
    TurnLoopImmuneCoordinator,
)


@dataclass
class EngineTurnStateV1:
    round_seq: int
    specification_digest: str
    current_phi1: int
    current_gamma2: int
    open_defect_count: int
    previous_code: str | None = None
    previous_diff: str | None = None
    open_obligations: list[str] = field(default_factory=list)
    promoted_operands: list[str] = field(default_factory=list)
    cemetery_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PromptPolicyV1:
    regime_id: str
    regime_kind: str
    admitted_constructors: list[str] = field(default_factory=list)
    kill_conditions: list[str] = field(default_factory=list)
    required_reply_fields: list[str] = field(default_factory=list)
    max_tokens: int = 4096

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DriverMovePacket:
    candidate_id: str
    proposed_diff: str
    declared_phi1: int
    declared_gamma2: int
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TurnDriverController:
    """Orchestrates turn driving against the sovereign native Rust driver."""

    def __init__(
        self,
        trace_dir: Path,
        state: EngineTurnStateV1,
        policy: PromptPolicyV1,
        host: Any | None = None,
        immune_coordinator: TurnLoopImmuneCoordinator | None = None,
    ) -> None:
        self.trace_dir = trace_dir
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self.state = state
        self.policy = policy
        if host is not None:
            self.host = host
        else:
            import importlib
            _ffi = importlib.import_module("pfp.ffi")
            self.host = _ffi.get_default_host()
        self.immune_coordinator = immune_coordinator or TurnLoopImmuneCoordinator()
        self.ddc_trace_path = self.trace_dir / "ddc_trace.jsonl"
        self.cemetery_path = self.trace_dir / "cemetery.jsonl"

    def next_prompt(self) -> Result[dict[str, Any], Refusal]:
        """Compile the native driver prompt; retain native refusal evidence."""
        payload = {
            "state": self.state.to_dict(),
            "policy": self.policy.to_dict(),
        }
        res = self.host.invoke("turn_driver_next_prompt", payload)
        if res.is_err:
            return Err(res.unwrap_err())
        outcome = res.unwrap()
        details = (("native_outcome", json.dumps(outcome, sort_keys=True)),)
        if outcome.get("success") is not True:
            message = outcome.get("error") or "Native prompt compilation refused"
            code = (
                "TURN_DRIVER_PROMPT_INVALID"
                if message.startswith("TURN_DRIVER_PROMPT_INVALID:")
                else "TURN_DRIVER_PROMPT_REFUSED"
            )
            return Err(Refusal(code=code, message=message, details=details))
        artifact = outcome.get("result")
        if type(artifact) is not dict:
            return Err(Refusal(
                code="TURN_DRIVER_PROMPT_OUTCOME_INVALID",
                message="Native prompt success must carry an artifact object",
                details=details,
            ))
        return Ok(artifact)

    def step(
        self,
        candidate: DriverMovePacket,
        signal1_matches: Sequence[Signal1AstMatch] = (),
        signal2_danger: Signal2DangerState | None = None,
        detector_votes: int = 1,
    ) -> Result[EngineTurnStateV1, Refusal]:
        """Evaluates candidate move against immune checkpoints and strict descent invariant.

        On immune quarantine: logs to cemetery.jsonl and refuses.
        On success: advances state and logs to ddc_trace.jsonl.
        On non-descent or malformed: logs to cemetery.jsonl and returns Refusal.
        """
        # Point 1-7: OEEIS Turn-Loop Immune Evaluation
        immune_verdict = self.immune_coordinator.evaluate_candidate_move(
            current_phi1=self.state.current_phi1,
            proposed_diff=candidate.proposed_diff,
            signal1_matches=signal1_matches,
            signal2_danger=signal2_danger,
            detector_votes=detector_votes,
        )
        if immune_verdict.quarantined:
            cemetery_row = {
                "candidate_id": candidate.candidate_id,
                "reason": "QUARANTINED",
                "rationale": immune_verdict.rationale,
                "complement_effectors": immune_verdict.complement_effectors,
            }
            with open(self.cemetery_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(cemetery_row, sort_keys=True) + "\n")
            self.state.cemetery_count += 1
            return Err(Refusal(code="QUARANTINED", message=immune_verdict.rationale))

        payload = {
            "state": self.state.to_dict(),
            "candidate": candidate.to_dict(),
        }
        res = self.host.invoke("turn_driver_step", payload)
        if res.is_err:
            return Err(res.unwrap_err())

        outcome = res.unwrap().get("result", {})
        status = outcome.get("status")
        detail = outcome.get("detail", {})

        if status == "Accepted":
            new_state_dict = detail.get("new_state", {})
            step_row = detail.get("step_row", {})

            # Record step row in ddc_trace.jsonl
            with open(self.ddc_trace_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(step_row, sort_keys=True) + "\n")

            # Update local state
            self.state = EngineTurnStateV1(
                round_seq=new_state_dict["round_seq"],
                specification_digest=new_state_dict["specification_digest"],
                current_phi1=new_state_dict["current_phi1"],
                current_gamma2=new_state_dict["current_gamma2"],
                open_defect_count=new_state_dict["open_defect_count"],
                previous_code=new_state_dict.get("previous_code"),
                previous_diff=new_state_dict.get("previous_diff"),
                open_obligations=new_state_dict.get("open_obligations", []),
                promoted_operands=new_state_dict.get("promoted_operands", []),
                cemetery_count=self.state.cemetery_count,
            )
            return Ok(self.state)

        elif status in ("RejectedNonDescent", "RejectedMalformed"):
            cemetery_row = detail.get("cemetery_row", {})
            refusal_reason = detail.get("refusal_reason", status)

            # Record rejection to cemetery.jsonl
            with open(self.cemetery_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(cemetery_row, sort_keys=True) + "\n")

            self.state.cemetery_count += 1
            return Err(Refusal(code=status, message=refusal_reason))

        return Err(Refusal(code="UNEXPECTED_DRIVER_OUTCOME", message=f"Unknown status {status}"))
