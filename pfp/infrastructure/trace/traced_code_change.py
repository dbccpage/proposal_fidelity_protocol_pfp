"""Trace recording over the deterministic code-change path.

P1a is P0's regression instrumented. That is the point of doing it first: the
very first execution the harness records needs no model at all, so any
disagreement between two runs is a defect in the harness rather than sampling
noise from a provider.

What is recorded per stage is the *derived identity* of what the stage produced
-- packet id, candidate id, patch digest, gate dispositions -- and never the
patch bytes themselves. A trace is read far more often than an execution is run,
and a file that carries payloads invites being treated as the artifact store.
The digests are enough to re-look-up anything real, and a digest cannot be
quietly edited into something plausible.

Failures are recorded before they are raised. A refusal that escapes without a
record makes the trace say a stage never happened, when what happened is that it
refused -- the two are not the same and the harness must not confuse them.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any

from ...controllers.code_change_controller import CodeChangeController
from ...use_cases.code_change import BoundCandidate, CodeChangeSession
from .execution_trace import ExecutionTrace
from .trace_schema import (
    EVENT_CANDIDATE_SUBMITTED,
    EVENT_GATES_EVALUATED,
    EVENT_PROPOSAL_CREATED,
    EVENT_RUN_FINALIZED,
    EVENT_STAGE_REFUSED,
)

# The five code-change event names are declared by ``trace_schema`` and
# re-exported here. Defining them beside their writer made a reader's idea of
# which events exist depend on which modules it had imported.

TERMINAL_PATH_COMPLETE = "CODE_CHANGE_PATH_COMPLETE"


class TracedCodeChangeController:
    """Wraps `CodeChangeController`, recording each stage to an execution trace.

    A wrapper rather than instrumentation inside the controller: the controller
    is the thing under measurement, and a measured object that carries its own
    recorder can no longer be run unmeasured for comparison.
    """

    def __init__(self, trace: ExecutionTrace, controller: CodeChangeController | None = None) -> None:
        self.trace = trace
        self.controller = controller or CodeChangeController()

    def _refuse(self, stage: str, exc: BaseException) -> None:
        self.trace.record(
            EVENT_STAGE_REFUSED,
            stage=stage,
            refusal_type=type(exc).__name__,
            # The message, not the traceback: a refusal code is the governed
            # part and a traceback is host detail that would differ per machine.
            refusal=str(exc)[:512],
        )

    def create_proposal(self, **kwargs: Any) -> CodeChangeSession:
        try:
            session = self.controller.create_proposal(**kwargs)
        except BaseException as exc:
            self._refuse("create_proposal", exc)
            raise
        self.trace.record(
            EVENT_PROPOSAL_CREATED,
            packet_id=session.packet_id,
            task_id=session.task_id,
            source_revision=session.payload.source_revision,
            owned_paths=list(session.payload.owned_paths),
            protected_paths=list(session.payload.protected_paths),
            required_gates=list(session.payload.required_gates),
            candidate_budget=int(session.payload.candidate_budget),
            operation_budget=int(session.payload.operation_budget),
        )
        return session

    def submit_patch(self, **kwargs: Any) -> tuple[CodeChangeSession, BoundCandidate]:
        try:
            session, bound = self.controller.submit_patch(**kwargs)
        except BaseException as exc:
            self._refuse("submit_patch", exc)
            raise
        self.trace.record(
            EVENT_CANDIDATE_SUBMITTED,
            packet_id=session.packet_id,
            candidate_id=bound.candidate.candidate_id,
            patch_id=bound.patch.patch_id,
            patch_sha256=bound.patch.patch_sha256,
            patch_byte_count=bound.patch.patch_byte_count,
            touched_paths=list(bound.patch.touched_paths),
            producer_id=bound.candidate.producer_id,
            # Recorded as the producer's claim, which on this path is always
            # absent. When typed claims land, this is where provenance attaches.
            model_claimed_valid=bound.candidate.claimed_valid,
            ledger_candidate_count=len(session.candidate_ids),
        )
        return session, bound

    def evaluate_patch_gates(self, **kwargs: Any) -> tuple[Any, ...]:
        try:
            receipts = self.controller.evaluate_patch_gates(**kwargs)
        except BaseException as exc:
            self._refuse("evaluate_patch_gates", exc)
            raise
        self.trace.record(
            EVENT_GATES_EVALUATED,
            gates=[
                {
                    "gate_id": r.gate_id,
                    "disposition": r.disposition,
                    "candidate_id": r.candidate_id,
                    "evaluator_id": r.evaluator_id,
                    "evidence_sha256": r.evidence_sha256,
                    "refusal_codes": list(r.refusal_codes),
                    "model_claimed_passed": r.model_claimed_passed,
                }
                for r in receipts
            ],
        )
        return receipts

    def finalize_run(self, **kwargs: Any) -> Any:
        try:
            run_root = self.controller.finalize_run(**kwargs)
        except BaseException as exc:
            self._refuse("finalize_run", exc)
            raise
        self.trace.record(
            EVENT_RUN_FINALIZED,
            packet_id=run_root.task_packet_id,
            terminal_status=run_root.terminal_status,
            refusals=list(run_root.refusals),
            open_obstruction_ids=list(run_root.open_obstruction_ids),
            candidate_ids=list(run_root.candidate_ids),
            patch_ids=list(run_root.patch_ids),
        )
        return run_root
