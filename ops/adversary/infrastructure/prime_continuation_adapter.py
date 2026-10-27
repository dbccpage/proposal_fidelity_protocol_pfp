"""Prime continuation adapter for Adversary Swarm.

Enforces Prime-002 CanContinue_n rules and budget bounds over the OEOS seam.
AuthorityEffect: None.
"""

from __future__ import annotations

from operations.domain.rop.result import Ok, Refusal, Result
from pfp.ffi import RustSymbolGameHost, get_default_host
from adversary.stage.application.ports import (
    ContinuationPortV1,
    ContinueDecisionKindV1,
    ContinueDecisionV1,
)
from adversary.stage.domain import SwarmRunStateV1


class PrimeContinuationAdapter(ContinuationPortV1):
    """Prime-002 CanContinue_n continuation adapter calling native host or budget bounds."""

    def __init__(
        self,
        host: RustSymbolGameHost | None = None,
        max_ops: int = 64,
    ) -> None:
        self.host = host
        self.max_ops = max_ops

    def get_host(self) -> RustSymbolGameHost | None:
        if self.host is not None:
            return self.host
        try:
            return get_default_host()
        except Exception:
            return None

    def can_continue(
        self, state: SwarmRunStateV1
    ) -> Result[ContinueDecisionV1, Refusal]:
        # 1. Terminal check: once terminalized, state cannot continue (AntiCheatLaw: TerminalAbsorbing)
        terminal_status = getattr(state, "terminal_status", "RUNNING")
        if terminal_status != "RUNNING":
            return Ok(
                ContinueDecisionV1(
                    kind=ContinueDecisionKindV1.HALT,
                    reason=f"Run reached terminal status: {terminal_status}",
                    remaining_budget=0,
                )
            )

        # 2. Budget finite check
        remaining_budget = getattr(state, "remaining_budget", 0)
        if remaining_budget <= 0:
            return Ok(
                ContinueDecisionV1(
                    kind=ContinueDecisionKindV1.HALT,
                    reason=f"Budget exhausted (remaining={remaining_budget})",
                    remaining_budget=0,
                )
            )

        # 3. Scene step / operation bound check (AntiCheatLaw: BoundedStopping)
        scene_steps = getattr(state, "scene_steps", 0)
        if scene_steps >= self.max_ops:
            return Ok(
                ContinueDecisionV1(
                    kind=ContinueDecisionKindV1.HALT,
                    reason=f"Maximum allowed steps reached ({self.max_ops})",
                    remaining_budget=0,
                )
            )

        circuit_count = getattr(state, "circuit_count", 0)
        if circuit_count >= self.max_ops:
            return Ok(
                ContinueDecisionV1(
                    kind=ContinueDecisionKindV1.HALT,
                    reason=f"Circuit count reached maximum allowed limit ({self.max_ops})",
                    remaining_budget=0,
                )
            )

        effective_remaining = min(remaining_budget, self.max_ops - scene_steps)
        return Ok(
            ContinueDecisionV1(
                kind=ContinueDecisionKindV1.CONTINUE,
                reason="Prime-002 continuation licensed; budget available",
                remaining_budget=effective_remaining,
            )
        )


__all__ = ["PrimeContinuationAdapter"]
