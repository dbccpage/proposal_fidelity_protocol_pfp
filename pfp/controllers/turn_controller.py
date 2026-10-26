"""Turn Controller coordinating LLM turn lifecycle and candidate evaluation."""

from __future__ import annotations

from typing import Any

from ..domain import (
    CandidateArtifactV1,
    LlmTurnContentArtifactV1,
    LlmTurnRunRootV1,
)
from ..domain.ports import ITurnRepository
from ..use_cases import (
    CreateTurnUseCase,
    EvaluateCandidateUseCase,
    SubmitCandidateUseCase,
)


class TurnController:
    """Application controller orchestrating LLM turn use cases."""

    def __init__(
        self,
        repository: ITurnRepository | None = None,
        create_use_case: CreateTurnUseCase | None = None,
        submit_use_case: SubmitCandidateUseCase | None = None,
        evaluate_use_case: EvaluateCandidateUseCase | None = None,
    ) -> None:
        self.repo = repository
        self.create_uc = create_use_case or CreateTurnUseCase()
        self.submit_uc = submit_use_case or SubmitCandidateUseCase()
        self.evaluate_uc = evaluate_use_case or EvaluateCandidateUseCase()

    def create_turn(
        self,
        *,
        task_id: str,
        objective: str,
        role: str = "assistant",
        turn_kind: str = "prose",
        candidate_budget: int = 4,
        operation_budget: int = 16,
        prompt_artifact_id: str | None = None,
        prompt_body: str | None = None,
        required_reply_fields: tuple[str, ...] = ("status", "step_claims", "obstruction_receipts"),
        kill_conditions: tuple[str, ...] = ("F-01_inherited_meaning",),
    ) -> LlmTurnRunRootV1:
        run_root = self.create_uc.execute(
            task_id=task_id,
            objective=objective,
            role=role,
            turn_kind=turn_kind,
            candidate_budget=candidate_budget,
            operation_budget=operation_budget,
            prompt_artifact_id=prompt_artifact_id,
            prompt_body=prompt_body,
            required_reply_fields=required_reply_fields,
            kill_conditions=kill_conditions,
        )
        if self.repo is not None:
            self.repo.save_run_root(run_root)
        return run_root

    def submit_candidate(
        self,
        *,
        run_root: LlmTurnRunRootV1,
        candidate_id: str,
        producer_id: str,
        reply_text: str,
        parent_packet_id: str | None = None,
        dual_witness_ref: str | None = None,
    ) -> tuple[LlmTurnRunRootV1, CandidateArtifactV1, LlmTurnContentArtifactV1]:
        updated_root, cand, content = self.submit_uc.execute(
            run_root=run_root,
            candidate_id=candidate_id,
            producer_id=producer_id,
            reply_text=reply_text,
            parent_packet_id=parent_packet_id,
            dual_witness_ref=dual_witness_ref,
        )
        if self.repo is not None:
            self.repo.save_run_root(updated_root)
            self.repo.save_candidate_artifact(cand)
            self.repo.save_content_artifact(content)
        return updated_root, cand, content

    def evaluate_candidate(
        self,
        *,
        run_root: LlmTurnRunRootV1,
        candidate: CandidateArtifactV1,
        content: LlmTurnContentArtifactV1,
    ) -> dict[str, Any]:
        return self.evaluate_uc.execute(
            run_root=run_root,
            candidate=candidate,
            content=content,
        )
