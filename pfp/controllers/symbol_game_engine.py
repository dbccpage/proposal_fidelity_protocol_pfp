"""
symbol_game_engine.py
======================

Unified Deep Facade Seam for the Symbol Game Bounded Context.
Integrates Clean Architecture Use Cases, Railway-Oriented Programming (ROP), and Event-Driven Architecture.

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, Dict, Literal, Mapping, Optional, Sequence, Tuple, Type

from ..domain.evaluator import ProposalEvaluationResult, ProposalEvaluator
from ..domain.events import (
    DomainEvent,
    ProposalEvaluatedEvent,
    TurnExecutedEvent,
)
from ..domain.exceptions import DomainError, TypedRefusalError
from ..domain.models import (
    ObstructionScore,
    SymbolGameEnvelope,
    SymbolGameStepOutcome,
)
from ..domain.packet_codec import PacketCodec
from ..domain.shared_kernel.result import Result, err, ok
from ..domain.solvers import (
    CochainCarrier,
    CochainGradientInjectionHook,
    Delta,
    RegimeK,
    RetractionLoopResult,
    RetractionTurnOutcome,
    SimplicialRetractionReceipt,
    Stage,
    compute_obstruction_score,
    execute_retraction_turn,
    run_retraction_loop,
    run_simplicial_retraction_loop,
)
from ..infrastructure.adapters.research_solvers import build_airy_problem, build_coda_problem
from ..infrastructure.events import InMemoryEventBus, TransactionalOutbox
from ..use_cases.problem_runner import ProblemRunnerUseCase
from ..use_cases.symbol_turn_service import SymbolGameExecutionService


def _typed_failure(ex: Exception) -> Result[Any, DomainError]:
    """Keep a typed refusal's code and cause on the failure track; re-raise the rest.

    An exception that carries a string ``code`` is a refusal and travels as
    ``TypedRefusalError`` with that code. Anything else is a defect, not a
    refusal, and is re-raised rather than flattened into ``DomainError(str(ex))``.
    """
    code = getattr(ex, "code", None)
    if type(code) is str and code:
        return err(TypedRefusalError(ex))
    raise ex


class SymbolGameEngine:
    """Unified deep facade seam providing high-leverage entry points for callers and tests."""

    def __init__(
        self,
        target_dir: Optional[Path] = None,
        event_bus: Optional[InMemoryEventBus] = None,
    ) -> None:
        self.target_dir = target_dir or Path.cwd()
        self.event_bus = event_bus or InMemoryEventBus()
        self.outbox = TransactionalOutbox(self.event_bus)
        self.turn_service = SymbolGameExecutionService()
        self.problem_runner = ProblemRunnerUseCase(
            turn_service=self.turn_service, target_dir=self.target_dir
        )
        self.evaluator = ProposalEvaluator()
        self.codec = PacketCodec()

    def execute_turn(self, task_id: str, prompt: str) -> SymbolGameStepOutcome:
        """Executes a single sparse manifold retraction turn."""
        envelope = SymbolGameEnvelope(task_id=task_id, initial_input=prompt)
        outcome = self.turn_service.execute_symbol_turn(envelope)

        # Raise TurnExecutedEvent
        self.event_bus.publish(
            TurnExecutedEvent(
                aggregate_id=task_id,
                task_id=task_id,
                step_id=outcome.step_id,
                purity=outcome.purity,
                l1_obstruction=outcome.l1_obstruction,
                is_exact=outcome.is_exact,
                verdict=outcome.verdict,
            )
        )
        return outcome

    def execute_turn_result(self, task_id: str, prompt: str) -> Result[SymbolGameStepOutcome, DomainError]:
        """ROP track: Executes turn returning Success[Outcome] or Failure[DomainError]."""
        try:
            outcome = self.execute_turn(task_id, prompt)
            return ok(outcome)
        except DomainError as ex:
            return err(ex)

    def compute_obstruction_score(self, state: RegimeK) -> ObstructionScore:
        """Computes exact obstruction score (Gamma_2, Phi_1, defect_count) via sovereign Rust ports."""
        return compute_obstruction_score(state)

    def execute_retraction_turn(
        self,
        *,
        task_id: str,
        state: RegimeK,
        candidate_delta: Delta,
        stage: Stage,
        turn_index: int = 0,
        prior_score: Optional[ObstructionScore] = None,
    ) -> RetractionTurnOutcome:
        """Executes a discrete retraction turn verifying strict descent on (Gamma_2, Phi_1, defect_count)."""
        outcome = execute_retraction_turn(
            task_id=task_id,
            turn_index=turn_index,
            state=state,
            candidate_delta=candidate_delta,
            stage=stage,
            prior_score=prior_score,
        )
        self.event_bus.publish(
            TurnExecutedEvent(
                aggregate_id=task_id,
                task_id=task_id,
                step_id=f"retraction_step_{turn_index}",
                purity=1.0 if outcome.is_exact else 0.5,
                l1_obstruction=outcome.new_score.phi_1 + outcome.new_score.gamma_2,
                is_exact=outcome.is_exact,
                verdict=outcome.verdict.value,
            )
        )
        return outcome

    def solve_retraction_loop(
        self,
        *,
        task_id: str,
        initial_state: RegimeK,
        stage: Stage,
        candidate_deltas: Sequence[Delta],
    ) -> RetractionLoopResult:
        """Runs a multi-turn retraction loop over candidate deltas, verifying strict descent."""
        return run_retraction_loop(
            task_id=task_id,
            initial_state=initial_state,
            stage=stage,
            candidate_deltas=candidate_deltas,
        )

    def run_simplicial_retraction(
        self,
        *,
        task_id: str,
        complex_obj: CochainCarrier,
        initial_claims: dict[tuple[str, str], Fraction],
        mode: Literal["unhinted", "hinted"] = "hinted",
        max_turns: int = 15,
        hook: Optional[CochainGradientInjectionHook] = None,
    ) -> SimplicialRetractionReceipt:
        """Runs a multi-turn retraction loop on a higher-order simplicial complex with cochain gradient injection."""
        receipt = run_simplicial_retraction_loop(
            task_id=task_id,
            complex_obj=complex_obj,
            initial_claims=initial_claims,
            mode=mode,
            max_turns=max_turns,
            hook=hook,
        )
        self.event_bus.publish(
            TurnExecutedEvent(
                aggregate_id=task_id,
                task_id=task_id,
                step_id=f"simplicial_{complex_obj.complex_id}_{mode}",
                purity=1.0 if receipt.loop_prevented else 0.0,
                # The basis-dependent holonomy sum is not an L1 obstruction:
                # it is published exactly under its own name.
                holonomy_sum=receipt.final_holonomy_sum,
                is_exact=(receipt.final_holonomy_sum == 0),
                verdict=receipt.terminal_verdict,
            )
        )
        return receipt

    def solve_problem(
        self,
        problem_input: str | Dict[str, Any],
        task_id: Optional[str] = None,
        max_steps: int = 4,
    ) -> Dict[str, Any]:
        """Runs a multi-step problem reduction."""
        return self.problem_runner.run_problem(
            problem_input=problem_input,
            task_id=task_id,
            max_steps=max_steps,
        )

    def solve_problem_result(
        self,
        problem_input: str | Dict[str, Any],
        task_id: Optional[str] = None,
        max_steps: int = 4,
    ) -> Result[Dict[str, Any], DomainError]:
        """ROP track: Runs multi-step reduction returning Result."""
        try:
            res = self.solve_problem(problem_input=problem_input, task_id=task_id, max_steps=max_steps)
            return ok(res)
        except DomainError as ex:
            return err(ex)
        except Exception as ex:
            return _typed_failure(ex)

    def evaluate_proposal(
        self,
        proposal_id: str,
        initial_mass: float,
        final_mass: float,
        effort: float = 1.0,
        metadata: Mapping[str, Any] | None = None,
    ) -> ProposalEvaluationResult:
        """Scores candidate proposal contractiveness and kill rules."""
        result = self.evaluator.evaluate_proposal(
            proposal_id=proposal_id,
            initial_mass=initial_mass,
            final_mass=final_mass,
            effort=effort,
            metadata=metadata,
        )
        self.event_bus.publish(
            ProposalEvaluatedEvent(
                aggregate_id=proposal_id,
                proposal_id=proposal_id,
                is_admissible=result.is_admissible,
                efficiency=result.efficiency,
                kill_reason=result.kill_reason.value if hasattr(result.kill_reason, "value") else str(result.kill_reason),
            )
        )
        return result

    def evaluate_proposal_result(
        self,
        proposal_id: str,
        initial_mass: float,
        final_mass: float,
        effort: float = 1.0,
        metadata: Mapping[str, Any] | None = None,
    ) -> Result[ProposalEvaluationResult, DomainError]:
        """ROP track: Scores candidate proposal returning Result."""
        try:
            res = self.evaluate_proposal(
                proposal_id=proposal_id,
                initial_mass=initial_mass,
                final_mass=final_mass,
                effort=effort,
                metadata=metadata,
            )
            return ok(res)
        except DomainError as ex:
            return err(ex)
        except Exception as ex:
            return _typed_failure(ex)

    def subscribe(self, event_type: Type[DomainEvent], handler: Callable[[DomainEvent], None]) -> None:
        """Subscribes an event listener to the internal event bus."""
        self.event_bus.subscribe(event_type, handler)

    def seal_packet(
        self,
        payload: Mapping[str, Any],
        packet_family: str,
        *,
        payload_schema: str | None = None,
        parent_id: str | None = None,
        carrier_id: str | None = None,
    ) -> dict[str, Any]:
        """Seals an arbitrary payload into a validated PacketEnvelopeV2 structure."""
        return self.codec.seal(
            payload,
            packet_family,
            payload_schema=payload_schema,
            parent_id=parent_id,
            carrier_id=carrier_id,
        )

    def verify_packet(self, envelope: Mapping[str, Any]) -> Tuple[bool, str, str]:
        """Verifies packet payload hash and authority invariants."""
        return self.codec.verify(envelope)

    # Problem Builder Shortcuts
    @staticmethod
    def build_airy_problem(*args: Any, **kwargs: Any) -> Any:
        return build_airy_problem(*args, **kwargs)

    @staticmethod
    def build_coda_problem(*args: Any, **kwargs: Any) -> Any:
        return build_coda_problem(*args, **kwargs)


__all__ = [
    "SymbolGameEngine",
]
