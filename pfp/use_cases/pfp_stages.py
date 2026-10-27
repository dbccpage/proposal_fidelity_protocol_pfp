"""Small-stage policy; checker defects never authorize more generation.

AuthorityEffect: None. This is a resource bound, not a convergence theorem.
"""

import time
from dataclasses import dataclass

from pfp.domain.contracts.pfp_runtime import (
    PfpPipelineFailure,
    PfpPipelinePort,
    PfpPipelineRun,
    PfpPipelineStep,
    PfpStagePort,
    PfpStageReceipt,
)
from pfp.domain.stages.host_stages import (
    challenge_replay,
    host_passed,
    receipt_terminal,
)
from pfp.domain.stages.stages import (
    HOST_STAGES,
    STAGE_COUNT,
    ChallengeReplay,
    stage_subset_problem,
)

from .pfp_proposal import ProposalCheck, repair_feedback


@dataclass(frozen=True)
class PfpStagePolicy:
    max_stages: int = 2

    def __post_init__(self):
        if type(self.max_stages) is not int or not 1 <= self.max_stages <= 2:
            raise ValueError("PFP_STAGE_BOUND")

    def feedback_after(self, stage: int, result: ProposalCheck) -> str | None:
        if type(stage) is not int or not 1 <= stage <= self.max_stages:
            raise ValueError("INVALID_STAGE")
        if stage == self.max_stages:
            return None
        if result.status != "PROVIDER_COMPLETED":
            return None
        return repair_feedback(result)


class RunPfpStagesUseCase:
    """One or two attempts; persist requests and reservations before dispatch."""

    def __init__(self, policy: PfpStagePolicy | None = None):
        self.policy = policy or PfpStagePolicy()

    def execute(
        self, port: PfpStagePort, initial_feedback: str | None = None
    ) -> list[PfpStageReceipt]:
        from .pfp_proposal import REPAIR_RULES

        if initial_feedback is not None and initial_feedback not in REPAIR_RULES.values():
            raise ValueError("UNTRUSTED_REPAIR_FEEDBACK")
        feedback = initial_feedback
        records = []
        for stage in range(1, self.policy.max_stages + 1):
            prepared = port.prepare(port.assemble(feedback))
            reserve = prepared.reserved_microusd
            port.reserve(stage, reserve)
            port.record_request(stage, prepared)
            start = time.monotonic()
            try:
                raw = port.dispatch(prepared)
            except Exception as exc:
                failure = dict(
                    status="INFRASTRUCTURE_ERROR",
                    failure_class="TRANSPORT",
                    error=type(exc).__name__,
                    reason=str(exc),
                    reserved_microusd=reserve,
                    cost_microusd=None,
                    reconciliation="REQUIRED",
                    completed_stages=len(records),
                )
                port.record_failure(stage, failure)
                port.summarize(failure)
                return records
            elapsed = time.monotonic() - start
            port.record_raw(stage, raw)
            receipt = None
            try:
                receipt = port.grade(raw)
                if receipt.data["cost_microusd"] > reserve:
                    raise ValueError("BILL_EXCEEDS_RESERVATION")
                port.record_receipt(stage, receipt, elapsed)
                port.settle(stage, receipt, reserve)
            except Exception as exc:
                # Capture first, retain the hold, and collate the real failure.
                # Preserve the existing exception API; no retry is authorized.
                code = str(exc)
                accounting = code in {
                    "MISSING_COST", "INVALID_COST", "MISSING_USAGE",
                    "BILL_EXCEEDS_RESERVATION", "DUPLICATE_GENERATION",
                }
                failure = dict(
                    status="INFRASTRUCTURE_ERROR",
                    failure_class="ACCOUNTING" if accounting else "REPLY",
                    phase="reply",
                    error=type(exc).__name__,
                    reason=code,
                    reserved_microusd=reserve,
                    cost_microusd=receipt.data["cost_microusd"] if receipt else None,
                    reconciliation="REQUIRED",
                    completed_stages=len(records),
                )
                port.record_failure(stage, failure)
                port.summarize(failure)
                raise
            records.append(receipt)
            result = receipt.data["result"]
            feedback = self.policy.feedback_after(
                stage, ProposalCheck(result["status"], result["failure_class"])
            )
            port.observe(stage, receipt)
            if feedback is None:
                break
        port.summarize(
            dict(
                status=records[-1].data["result"]["status"],
                stages=len(records),
                cost_microusd=sum(r.data["cost_microusd"] for r in records),
                transfer_benefit="UNMEASURED",
            )
        )
        return records


class RunPfpPipelineUseCase:
    """Numbered pipeline control. Host stages are supplied by the host port, never by a model."""

    @staticmethod
    def dispatch(stage: int, port: PfpPipelinePort, responses: dict) -> PfpPipelineStep:
        """Run one stage on `port`; shared by the Python runner and the native staged runner.

        Stage 11 (evidence plan) runs only when the stage 9 receipt marks the turn
        diagnostic_only; otherwise it records a skip and calls no model.
        """
        if stage in HOST_STAGES:
            return port.execute_host_stage(stage, responses)
        if stage == 11 and responses.get(9, {}).get("diagnostic_only") is False:
            data = {"stage": 11, "demo_id": responses[9]["demo_id"], "authority_effect": "None",
                    "derived_under_policy": "SPK-001", "skipped": "NOT_DIAGNOSTIC_ONLY"}
            return PfpPipelineStep(data, False)
        return port.execute_model_stage(stage, responses)

    @staticmethod
    def terminal_after(stage: int, responses: dict, should_continue: bool) -> str | None:
        """The stop rule, shared with the opt-in native staged adapter.

        A failed host check stops the run. An explicit stop before the receipt also stops it:
        STABILIZED_SURVIVOR after a stage 5 PASS, BLOCKED_BY_EVIDENCE before one. An obstruction
        found at stage 7 does not stop the run: the receipt, not the replay, names the terminal.
        """
        data = responses[stage]
        explicit_check_failed = (
            ("host_verdict" in data and data["host_verdict"] != "PASS")
            or ("exact_checks_passed" in data and data["exact_checks_passed"] is not True)
            or data.get("independent_check_passed") is False
        )
        if explicit_check_failed or (stage == 5 and not host_passed(responses)):
            return "BLOCKED_BY_EVIDENCE"
        if not should_continue and stage < 9:
            return "STABILIZED_SURVIVOR" if host_passed(responses) else "BLOCKED_BY_EVIDENCE"
        return None

    @staticmethod
    def host_replay(responses: dict) -> ChallengeReplay | None:
        """The host-written stage 7 replay record, validated again on read."""
        return challenge_replay(responses)

    # Stages a VERIFIED terminal needs: admission, the three model turns before the verdict,
    # the host verdict, the adversary and the host replay of its witnesses, and the receipt.
    ACCEPTANCE_STAGES = (1, 2, 3, 4, 5, 6, 7, 9)

    @staticmethod
    def finish(completed: tuple[int, ...], responses: dict,
               requested: tuple[int, ...] | None = None) -> PfpPipelineRun:
        """The terminal is recomputed here from host facts; no model field is read as a terminal.

        VERIFIED needs every acceptance stage, a stage 5 PASS, no open obstruction and no
        remaining obligation. Anything less after a PASS is residual. When stage 9 ran, its
        recorded terminal and obligations must equal the recomputed ones. `all_stages_passed`
        means every requested stage ran, the acceptance stages were among them, and the run
        neither stopped on evidence nor found an obstruction. `requested` defaults to all stages.
        """
        requested = tuple(range(1, STAGE_COUNT + 1)) if requested is None else requested
        terminal, codes = receipt_terminal(responses)
        if 9 in responses:
            recorded = responses[9]
            if (recorded.get("terminal") != terminal
                    or [item.get("code") for item in recorded.get("remaining_obligations", ())] != list(codes)):
                raise PfpPipelineFailure("HOST_CHECK_FAILED", "RECEIPT_DOES_NOT_MATCH_HOST_FACTS", 9)
        accepted = set(RunPfpPipelineUseCase.ACCEPTANCE_STAGES) <= set(completed)
        if terminal == "VERIFIED" and not accepted:
            terminal = "VERIFIED_WITH_RESIDUALS"
        passed = (accepted and tuple(completed) == tuple(requested)
                  and terminal not in ("OPEN_OBSTRUCTION", "BLOCKED_BY_EVIDENCE"))
        return PfpPipelineRun(completed, responses, passed, terminal)

    def execute(self, stages: tuple[int, ...], port: PfpPipelinePort,
                requires: dict[int, list[int]] | None = None) -> PfpPipelineRun:
        """Run `stages` in order. Without `requires` they must be stages 1 through N.

        With `requires` (stage number to the stages it needs) they may be any runnable
        subset: strictly increasing, starting at stage 1, closed under `requires`.
        """
        if requires is None:
            if (type(stages) is not tuple or not 1 <= len(stages) <= STAGE_COUNT
                    or any(type(s) is not int for s in stages)
                    or stages != tuple(range(1, len(stages) + 1))):
                raise PfpPipelineFailure(
                    "UNKNOWN_STAGE", f"Expected a contiguous PFP prefix, stages 1 through N (N<={STAGE_COUNT})")
        else:
            problem = (stage_subset_problem(stages, requires) if type(stages) is tuple
                       else "Stages must be a tuple of stage numbers")
            if problem is not None:
                raise PfpPipelineFailure("UNKNOWN_STAGE", problem)
        responses = {}
        completed = []
        for stage in stages:
            step = self.dispatch(stage, port, responses)
            responses[stage] = step.data
            completed.append(stage)
            terminal = self.terminal_after(stage, responses, step.should_continue)
            if terminal is not None:
                return PfpPipelineRun(tuple(completed), responses, False, terminal)
        return self.finish(tuple(completed), responses, stages)
