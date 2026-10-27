"""Domain-level dependency-inversion ports and protocols for the Adversary stage.

Defines pure abstract interfaces for external storage, runtime telemetry/event sinks,
and execution adapters without framework or outer-layer dependencies.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Any, Protocol, runtime_checkable

from operations.domain.rop.result import Refusal, Result
from pfp.domain.value_objects.seat_turn import SeatTurnReplyV1, SeatTurnRequestV1

from .canonical import AUTHORITY_EFFECT_NONE
from .ddc import DdaStepV1, DdcStepV1
from .evaluation import EvaluatorEpochV1, ProgressMeasureV1, ValuationReceiptV1
from .genealogy import AntibodyEntryV1, CemeteryHeadstoneV1, GenealogyEntryV1
from .packets import AgentResultV1, CandidateProposalV1, WorkPacketV1
from .run import SwarmRunStateV1


class ContinueDecisionKindV1(str, Enum):
    """Decision kind for Prime-002 continuation gate."""

    CONTINUE = "CONTINUE"
    HALT = "HALT"


@dataclass(frozen=True)
class ContinueDecisionV1:
    """Continuation gate decision with remaining budget bounds."""

    kind: ContinueDecisionKindV1
    reason: str = ""
    remaining_budget: int = 0


# ============================================================================
# External Storage Ports
# ============================================================================


@runtime_checkable
class CemeterySink(Protocol):
    """Lossless storage for dead candidates and their cause of death."""

    def record_headstone(
        self, headstone: CemeteryHeadstoneV1
    ) -> Result[Any, Refusal]: ...


@runtime_checkable
class AntibodyStorePort(Protocol):
    """Immune antibody memory: loads past constraints and accumulates failures."""

    def load_antibodies(
        self, objective: str
    ) -> Result[tuple[AntibodyEntryV1, ...], Refusal]: ...

    def record_failure(
        self, failure_pattern: str, constraint_rule: str
    ) -> Result[Any, Refusal]: ...


@runtime_checkable
class GenealogyStorePort(Protocol):
    """Parent-to-child lineage tracking for front-door re-entries."""

    def record_lineage(
        self, entry: GenealogyEntryV1
    ) -> Result[Any, Refusal]: ...

    def get_lineage(
        self, child_run_key: str
    ) -> Result[GenealogyEntryV1 | None, Refusal]: ...


@runtime_checkable
class MemoryPortV1(Protocol):
    """General memory port for recalling context and appending receipts."""

    def recall(
        self, run_key: str, subject_ids: tuple[str, ...]
    ) -> Result[tuple[bytes, ...], Refusal]: ...

    def append_receipt(self, receipt_bytes: bytes) -> Result[None, Refusal]: ...


@runtime_checkable
class RunStateStorePort(Protocol):
    """Storage port for persisting and restoring swarm run states."""

    def save_state(
        self, run_key: str, state: SwarmRunStateV1
    ) -> Result[None, Refusal]: ...

    def load_state(
        self, run_key: str
    ) -> Result[SwarmRunStateV1 | None, Refusal]: ...


# ============================================================================
# Runtime Sinks
# ============================================================================


@runtime_checkable
class UtsSink(Protocol):
    """Universal Trace Stream (UTS): per-event superset source of truth."""

    def record_event(
        self, event: Any, payload: bytes | str
    ) -> Result[str, Refusal]: ...


@runtime_checkable
class DdcSink(Protocol):
    """Discrete Deformation Calculus (DDC) sink: strict-purity actions only."""

    def record_step(self, step: DdcStepV1 | DdaStepV1) -> Result[str, Refusal]: ...


DdaSink = DdcSink


@runtime_checkable
class UnsSink(Protocol):
    """Universal Narrative Stream (UNS): derived novella for humans."""

    def record_narrative(
        self, session_id: str, turn_md: str
    ) -> Result[str, Refusal]: ...


@runtime_checkable
class SgtSink(Protocol):
    """Symbol Game Trace (SGT) sink: typed turn packets."""

    def record_turn(
        self, session_id: str, turn_payload: dict[str, Any]
    ) -> Result[str, Refusal]: ...


@runtime_checkable
class EventPortV1(Protocol):
    """Domain event publication port."""

    def publish_observation(self, event_bytes: bytes) -> Result[None, Refusal]: ...


# ============================================================================
# Execution & Model Ports
# ============================================================================


@runtime_checkable
class ModelPortV1(Protocol):
    def propose(
        self, packet: WorkPacketV1, context_bytes: bytes
    ) -> Result[CandidateProposalV1, Refusal]: ...


@runtime_checkable
class SeatPortV1(Protocol):
    """Per-seat model execution port for turn-by-turn swarm interactions."""

    def execute_turn(
        self, request: SeatTurnRequestV1
    ) -> Result[SeatTurnReplyV1, Refusal]: ...


@runtime_checkable
class ToolPortV1(Protocol):
    def invoke(
        self, operation_id: str, input_artifact_refs: tuple[str, ...]
    ) -> Result[tuple[str, ...], Refusal]: ...


@runtime_checkable
class SkillPortV1(Protocol):
    """Invoke a dev/math/physics/other skill as a scene aside."""

    def invoke_aside(
        self, skill_id: str, context_bytes: bytes
    ) -> Result[AgentResultV1, Refusal]: ...


@runtime_checkable
class HostPortV1(Protocol):
    def execute_host_request(self, request_bytes: bytes) -> Result[bytes, Refusal]: ...


@runtime_checkable
class ValuatorPortV1(Protocol):
    def evaluate(
        self,
        epoch: EvaluatorEpochV1,
        candidate: CandidateProposalV1,
    ) -> Result[ValuationReceiptV1, Refusal]: ...


@runtime_checkable
class ContinuationPortV1(Protocol):
    """Prime-002 CanContinue_n gate + budget bound."""

    def can_continue(
        self, state: SwarmRunStateV1
    ) -> Result[ContinueDecisionV1, Refusal]: ...


@runtime_checkable
class SchedulerPortV1(Protocol):
    def start(self, run_key: str, packet: WorkPacketV1) -> SwarmRunStateV1: ...

    def advance(
        self,
        state: SwarmRunStateV1,
        result: AgentResultV1,
        progress: ProgressMeasureV1,
    ) -> Result[SwarmRunStateV1, Refusal]: ...


# ============================================================================
# Cochain & Theory Evaluator Ports
# ============================================================================


@dataclass(frozen=True)
class FunctionalEvaluationReceiptV1:
    """Receipt for discrete defect functional evaluation."""

    phi1: Fraction
    gamma2: Fraction
    diagnostic_class: str
    input_digest: str = ""
    dual_witness: tuple[Fraction, ...] = ()
    primal_residual: tuple[Fraction, ...] = ()
    success: bool = True
    authority_effect: str = AUTHORITY_EFFECT_NONE


@runtime_checkable
class FunctionalEvaluatorPort(Protocol):
    """Domain port for defect functionals Phi_1, Gamma_2, and Xi."""

    def evaluate_functional(
        self,
        d0: Sequence[Sequence[Fraction]],
        d1: Sequence[Sequence[Fraction]],
        residual: Sequence[Fraction],
    ) -> FunctionalEvaluationReceiptV1:
        """Evaluate d0, d1, residual to compute obstruction metrics."""
        ...


_GLOBAL_FUNCTIONAL_EVALUATOR_PORT: FunctionalEvaluatorPort | None = None


def set_functional_evaluator_port(port: FunctionalEvaluatorPort | None) -> None:
    """Register the global functional evaluator port at composition root."""
    global _GLOBAL_FUNCTIONAL_EVALUATOR_PORT
    _GLOBAL_FUNCTIONAL_EVALUATOR_PORT = port


def get_functional_evaluator_port() -> FunctionalEvaluatorPort | None:
    """Retrieve the global functional evaluator port, if configured."""
    return _GLOBAL_FUNCTIONAL_EVALUATOR_PORT


__all__ = [
    "AntibodyStorePort",
    "CemeterySink",
    "ContinuationPortV1",
    "ContinueDecisionKindV1",
    "ContinueDecisionV1",
    "DdaSink",
    "DdcSink",
    "EventPortV1",
    "FunctionalEvaluationReceiptV1",
    "FunctionalEvaluatorPort",
    "GenealogyStorePort",
    "HostPortV1",
    "MemoryPortV1",
    "ModelPortV1",
    "RunStateStorePort",
    "SchedulerPortV1",
    "SeatPortV1",
    "SgtSink",
    "SkillPortV1",
    "ToolPortV1",
    "UnsSink",
    "UtsSink",
    "ValuatorPortV1",
    "get_functional_evaluator_port",
    "set_functional_evaluator_port",
]
