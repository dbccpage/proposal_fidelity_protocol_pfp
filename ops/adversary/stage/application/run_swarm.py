"""Execution loop for the Adversary stage: Generic Swarm Circuit Runner.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from operations.domain.rop.result import Err, Ok, Refusal, Result

from ..domain import (
    EvaluatorEpochV1,
    SwarmDefinitionV1,
    SwarmProfileV1,
    SwarmRunReceiptV1,
    WorkPacketV1,
)
from .emission import EmitterSuiteV1
from .oscillation_detector import OscillationDetectorV1
from .ports import (
    ContinuationPortV1,
    EventPortV1,
    HostPortV1,
    MemoryPortV1,
    ModelPortV1,
    SchedulerPortV1,
    SeatPortV1,
    SkillPortV1,
    ToolPortV1,
    ValuatorPortV1,
)

HOST_OPERATION_ID = "execute_host_request"


def dispatch_host_request(
    runtime: SwarmRuntimeV1,
    operation_ids: tuple[str, ...],
    request: bytes | None,
) -> Result[bytes | None, Refusal]:
    """Run one host request when the scene assignment names the host operation.

    A missing host port refuses. The circuit does not touch the filesystem itself.
    """
    if HOST_OPERATION_ID not in operation_ids:
        return Ok(None)
    if runtime.host is None:
        return Err(
            Refusal(
                code="HOST_PORT_MISSING",
                message="The scene asks for a host request and no HostPortV1 is bound",
                locus="adversary.stage.application.run_swarm",
            )
        )
    if type(request) is not bytes:
        return Err(
            Refusal(
                code="HOST_REQUEST_MISSING",
                message="The host operation requires request bytes",
                locus="adversary.stage.application.run_swarm",
            )
        )
    host_result = runtime.host.execute_host_request(request)
    if host_result.is_err:
        return Err(host_result.unwrap_err())
    reply = host_result.unwrap()
    if type(reply) is not bytes:
        return Err(
            Refusal(
                code="HOST_REPLY_TYPE_MISMATCH",
                message="HostPortV1 must return exact reply bytes",
                locus="adversary.stage.application.run_swarm",
            )
        )
    return Ok(reply)


def _scene_operation_ids(runtime: SwarmRuntimeV1, scene_id: str) -> tuple[str, ...]:
    plan = getattr(runtime.scheduler, "plan", None)
    if plan is None:
        return ()
    return tuple(
        operation_id
        for assignment in plan.assignments
        if assignment.scene_id == scene_id
        for operation_id in assignment.operation_ids
    )


@dataclass(frozen=True)
class SwarmRuntimeV1:
    """Runtime dependencies for executing a base Swarm circuit."""

    model: ModelPortV1 | None = None
    scheduler: SchedulerPortV1 | None = None
    valuator: ValuatorPortV1 | None = None
    cont: ContinuationPortV1 | None = None
    emitters: EmitterSuiteV1 | None = None
    epoch: EvaluatorEpochV1 | None = None
    profile: SwarmProfileV1 | None = None
    seat_port: SeatPortV1 | None = None
    continuation: ContinuationPortV1 | None = None
    tools: ToolPortV1 | None = None
    memory: MemoryPortV1 | None = None
    events: EventPortV1 | None = None
    host: HostPortV1 | None = None
    skills: SkillPortV1 | None = None
    circuit: Any = None
    request_external_admission: bool = False
    max_candidate_budget: int = 3
    max_critique_rounds: int = 10
    operational_output_dir: str | None = None
    rollback_on_refusal: bool = False
    oscillation_detector: OscillationDetectorV1 | None = None
    host_request: bytes | None = None

    def __post_init__(self) -> None:
        if self.cont is not None and self.continuation is None:
            object.__setattr__(self, "continuation", self.cont)
        elif self.continuation is not None and self.cont is None:
            object.__setattr__(self, "cont", self.continuation)


def run_swarm(
    defn: SwarmDefinitionV1,
    profile: SwarmProfileV1,
    rt: SwarmRuntimeV1,
    initial_packet: WorkPacketV1,
    *,
    run_key: str = "run_001",
    host_request: bytes | None = None,
) -> Result[SwarmRunReceiptV1, Refusal]:
    """Run a generic Adversary stage circuit without inventing evaluation or DDA evidence."""
    if rt.epoch and rt.epoch.epoch_id != initial_packet.evaluator_epoch_id:
        return Err(
            Refusal(
                code="EVALUATOR_EPOCH_BINDING_MISMATCH",
                message="Runtime evaluator epoch does not match the work packet binding",
                locus="adversary.stage.application.run_swarm",
            )
        )

    if rt.scheduler is None:
        return Err(
            Refusal(
                code="OEAS_SCHEDULER_MISSING",
                message="Runtime scheduler is required to execute circuit",
                locus="adversary.stage.application.run_swarm",
            )
        )

    try:
        current_state = rt.scheduler.start(run_key, initial_packet)
    except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
        return Err(
            Refusal(
                code="OEAS_SCHEDULER_START_REFUSED",
                message=str(exc),
                locus="adversary.stage.application.run_swarm",
            )
        )

    if rt.oscillation_detector is not None:
        rt.oscillation_detector.reset()


    from .orchestration_owner import advance_owned_run

    effective_host_request = host_request if host_request is not None else rt.host_request
    return advance_owned_run(
        defn=defn,
        profile=profile,
        rt=rt,
        initial_packet=initial_packet,
        run_key=run_key,
        host_request=effective_host_request,
        current_state=current_state,
    )


__all__ = [
    "HOST_OPERATION_ID",
    "OscillationDetectorV1",
    "SwarmRuntimeV1",
    "dispatch_host_request",
    "run_swarm",
]
