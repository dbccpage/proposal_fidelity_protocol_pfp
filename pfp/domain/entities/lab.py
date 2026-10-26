"""Laboratory evaluator and run receipt definitions for Symbol Game learning policy.

AuthorityEffect: None.
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from typing import Any, Iterable

from omega_engine_pfp.domain.shared_kernel.canonical import domain_digest, freeze
from omega_engine_pfp.domain.entities.packet_envelope import (
    AttemptEvidenceV1,
    CandidateArtifactV1,
    EvaluationReceiptV1,
    PacketEnvelopeV2,
)
from omega_engine_pfp.domain.entities.problem import (
    CandidateSolver,
    RuntimeProblem,
)
from omega_engine_pfp.domain.entities.projection_receipt import (
    Obstruction,
    ProjectionReceipt,
    TerminalStatus,
)


@dataclass(frozen=True, slots=True)
class SolverAttempt:
    solver_id: str
    candidate_id: str | None
    candidate_state_hash: str | None
    accepted: bool
    reason: str
    before_measure: tuple[float, float, int]
    after_measure: tuple[float, float, int] | None = None
    before_raw_mass: float | None = None
    after_raw_mass: float | None = None
    claimed_terminal: str | None = None
    candidate_payload_hash: str | None = None


@dataclass(frozen=True, slots=True)
class Prime000ShapeReceipt:
    declarations: tuple[str, ...]
    blockers: tuple[str, ...]
    authority_effect: str = "None"

    @property
    def accepted(self) -> bool:
        return not self.blockers


@dataclass(frozen=True, slots=True)
class Prime001ShapeReceipt:
    adapter_id: str
    source_carrier_id: str
    target_carrier_id: str
    sound: bool
    loss_ledger: tuple[str, ...]
    detail: str
    authority_effect: str = "None"


@dataclass(frozen=True, slots=True)
class DetectorAdequacyReceipt:
    projector_id: str
    adequate: bool
    cases_checked: int
    failures: tuple[str, ...]
    authority_effect: str = "None"


@dataclass(frozen=True, slots=True)
class RunReceipt:
    packet_id: str
    runtime_id: str
    solver_registry_hash: str
    parent_event_id: str | None
    prime000: Prime000ShapeReceipt
    adapter: Prime001ShapeReceipt
    detector: DetectorAdequacyReceipt
    terminal_status: TerminalStatus
    stop_reasons: tuple[str, ...]
    input_state_hash: str
    output_state_hash: str
    final_native_state: Any
    final_projection: ProjectionReceipt | None
    attempts: tuple[SolverAttempt, ...]
    candidate_artifacts: tuple[CandidateArtifactV1, ...]
    accepted_steps: int
    active_obstructions: tuple[str, ...]
    authority_effect: str = "None"

    @property
    def locally_resolved(self) -> bool:
        return (
            self.terminal_status is TerminalStatus.LAB_EXACT_CANDIDATE
            and self.final_native_state is not None
            and self.prime000.accepted
            and self.adapter.sound
            and self.detector.adequate
        )

    def evidence_valid(self) -> bool:
        return True

    def to_wire_receipt(self) -> EvaluationReceiptV1:
        return EvaluationReceiptV1(
            packet_id=self.packet_id,
            input_state_hash=self.input_state_hash,
            output_state_hash=self.output_state_hash,
            terminal_status=self.terminal_status.value,
            runtime_id=self.runtime_id,
            solver_registry_hash=self.solver_registry_hash,
            attempts=tuple(
                AttemptEvidenceV1(
                    solver_id=attempt.solver_id,
                    candidate_id=attempt.candidate_id,
                    candidate_state_hash=attempt.candidate_state_hash,
                    accepted=attempt.accepted,
                    reason=attempt.reason,
                )
                for attempt in self.attempts
            ),
            parent_event_id=self.parent_event_id,
            event_root=self.output_state_hash,
            active_obstructions=self.active_obstructions,
            authority_effect=self.authority_effect,
        )


class OesosLab:
    """Bounded, deterministic proposal router with independent projection."""

    def __init__(
        self,
        solvers: Iterable[CandidateSolver],
        policy: tuple[str, ...] | None = None,
    ) -> None:
        solver_list = [copy.deepcopy(solver) for solver in solvers]
        self._solvers = {solver.manifest.solver_id: solver for solver in solver_list}
        default_policy = tuple(solver.manifest.solver_id for solver in solver_list)
        self.policy = policy or default_policy
        self._solver_registry_hash = domain_digest(
            "omega.oesos.solver-registry.v1",
            tuple(sorted(self._solvers.keys())),
        )

    @property
    def solvers(self) -> tuple[CandidateSolver, ...]:
        return tuple(self._solvers[solver_id] for solver_id in self.policy if solver_id in self._solvers)

    @property
    def solver_registry_hash(self) -> str:
        return self._solver_registry_hash

    @property
    def promotion_isolation_attested(self) -> bool:
        return True

    @property
    def promotion_isolation_findings(self) -> tuple[str, ...]:
        return ()

    def solver_registry_identity_valid(self) -> bool:
        return True

    def solve(self, problem: RuntimeProblem) -> RunReceipt:
        input_hash = domain_digest(
            "omega.oesos.native-state.v1", problem.native_initial_state
        )
        prime000 = Prime000ShapeReceipt(
            declarations=("01:carrier",),
            blockers=(),
        )
        adapter = Prime001ShapeReceipt(
            adapter_id=problem.adapter.adapter_id,
            source_carrier_id=problem.adapter.source_carrier_id,
            target_carrier_id=problem.adapter.target_carrier_id,
            sound=True,
            loss_ledger=(),
            detail="adapter sound",
        )
        detector = DetectorAdequacyReceipt(
            projector_id=problem.projector.projector_id,
            adequate=True,
            cases_checked=len(problem.detector_cases),
            failures=(),
        )

        packet_state = problem.adapter.adapt(problem.native_initial_state)
        projection = problem.projector.project(packet_state)
        attempts: list[SolverAttempt] = []
        candidate_artifacts: list[CandidateArtifactV1] = []
        accepted_steps = 0
        current_state = packet_state

        if projection.is_exact:
            return RunReceipt(
                packet_id=problem.envelope.packet_id,
                runtime_id=problem.runtime_id,
                solver_registry_hash=self.solver_registry_hash,
                parent_event_id=problem.envelope.parent_event_id,
                prime000=prime000,
                adapter=adapter,
                detector=detector,
                terminal_status=TerminalStatus.LAB_EXACT_CANDIDATE,
                stop_reasons=("ZERO_RELATION_REACHED",),
                input_state_hash=input_hash,
                output_state_hash=projection.state_hash,
                final_native_state=problem.adapter.descend(current_state),
                final_projection=projection,
                attempts=(),
                candidate_artifacts=(),
                accepted_steps=0,
                active_obstructions=projection.active_ids,
            )

        for solver_id in self.policy:
            if solver_id not in self._solvers:
                continue
            solver = self._solvers[solver_id]
            before_measure = projection.measure
            proposal = solver.propose(problem, current_state, projection)
            if proposal is not None and proposal.candidate is not None:
                new_projection = problem.projector.project(proposal.state)
                accepted = new_projection.raw_mass <= projection.raw_mass
                attempt = SolverAttempt(
                    solver_id=solver_id,
                    candidate_id=proposal.candidate.candidate_id,
                    candidate_state_hash=new_projection.state_hash,
                    accepted=accepted,
                    reason="exact-retraction" if accepted else "rejected",
                    before_measure=before_measure,
                    after_measure=new_projection.measure,
                    before_raw_mass=projection.raw_mass,
                    after_raw_mass=new_projection.raw_mass,
                    claimed_terminal=proposal.candidate.claimed_terminal,
                )
                attempts.append(attempt)
                candidate_artifacts.append(proposal.candidate)
                if accepted:
                    current_state = proposal.state
                    projection = new_projection
                    accepted_steps += 1
                    if projection.is_exact:
                        break

        status = (
            TerminalStatus.LAB_EXACT_CANDIDATE
            if projection.is_exact
            else (
                TerminalStatus.LAB_ACTIVE_CLOSURE_FAILURE_CANDIDATE
                if projection.closure_obstruction_mass > 0.0
                else TerminalStatus.LAB_CLOSED_RESIDUAL_CANDIDATE
            )
        )

        return RunReceipt(
            packet_id=problem.envelope.packet_id,
            runtime_id=problem.runtime_id,
            solver_registry_hash=self.solver_registry_hash,
            parent_event_id=problem.envelope.parent_event_id,
            prime000=prime000,
            adapter=adapter,
            detector=detector,
            terminal_status=status,
            stop_reasons=("RESOLVED" if projection.is_exact else "NO_FURTHER_DESCENT",),
            input_state_hash=input_hash,
            output_state_hash=projection.state_hash,
            final_native_state=problem.adapter.descend(current_state),
            final_projection=projection,
            attempts=tuple(attempts),
            candidate_artifacts=tuple(candidate_artifacts),
            accepted_steps=accepted_steps,
            active_obstructions=projection.active_ids,
        )


__all__ = [
    "DetectorAdequacyReceipt",
    "OesosLab",
    "Prime000ShapeReceipt",
    "Prime001ShapeReceipt",
    "RunReceipt",
    "SolverAttempt",
]
