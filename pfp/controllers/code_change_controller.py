"""Code Change Controller coordinating code proposals and patch gate evaluation."""

from __future__ import annotations

from ..domain import CodeChangeRunRootV1, GateReceiptV1
from ..domain.ports import ICodeChangeRepository
from ..use_cases import (
    BoundCandidate,
    CodeChangeSession,
    CreateCodeChangeProposalUseCase,
    EvaluatePatchGatesUseCase,
    FinalizeCodeChangeRunUseCase,
    SubmitPatchCandidateUseCase,
)


class CodeChangeController:
    """Application controller orchestrating code change proposal use cases.

    The four methods mirror the canonical domain lifecycle. Note where
    persistence happens: a ``CodeChangeRunRootV1`` only exists after
    ``finalize_run`` calls the evaluator, so that is the only place one can be
    saved. The previous controller saved a run root at proposal time, which
    persisted a record of an evaluation that had not occurred -- carrying a
    ``terminal_status`` no evaluator had assigned.
    """

    def __init__(
        self,
        repository: ICodeChangeRepository | None = None,
        create_use_case: CreateCodeChangeProposalUseCase | None = None,
        submit_use_case: SubmitPatchCandidateUseCase | None = None,
        evaluate_use_case: EvaluatePatchGatesUseCase | None = None,
        finalize_use_case: FinalizeCodeChangeRunUseCase | None = None,
    ) -> None:
        self.repo = repository
        self.create_uc = create_use_case or CreateCodeChangeProposalUseCase()
        self.submit_uc = submit_use_case or SubmitPatchCandidateUseCase()
        self.evaluate_uc = evaluate_use_case or EvaluatePatchGatesUseCase()
        self.finalize_uc = finalize_use_case or FinalizeCodeChangeRunUseCase()

    def create_proposal(
        self,
        *,
        task_id: str,
        objective: str,
        base_revision: str,
        owned_paths: tuple[str, ...],
        protected_paths: tuple[str, ...],
        path_manifest_root: str | None = None,
        candidate_budget: int = 4,
        operation_budget: int = 16,
        required_gates: tuple[str, ...] = ("gate_syntax", "gate_ownership", "gate_contract"),
    ) -> CodeChangeSession:
        return self.create_uc.execute(
            task_id=task_id,
            objective=objective,
            base_revision=base_revision,
            owned_paths=owned_paths,
            protected_paths=protected_paths,
            path_manifest_root=path_manifest_root,
            candidate_budget=candidate_budget,
            operation_budget=operation_budget,
            required_gates=required_gates,
        )

    def submit_patch(
        self,
        *,
        session: CodeChangeSession,
        producer_id: str,
        patch_text: str,
    ) -> tuple[CodeChangeSession, BoundCandidate]:
        updated, bound = self.submit_uc.execute(
            session=session,
            producer_id=producer_id,
            patch_text=patch_text,
        )
        if self.repo is not None:
            self.repo.save_patch_artifact(bound.patch)
        return updated, bound

    def evaluate_patch_gates(
        self,
        *,
        session: CodeChangeSession,
        bound: BoundCandidate,
    ) -> tuple[GateReceiptV1, ...]:
        receipts = self.evaluate_uc.execute(session=session, bound=bound)
        if self.repo is not None:
            for receipt in receipts:
                self.repo.save_gate_receipt(receipt)
        return receipts

    def finalize_run(
        self,
        *,
        session: CodeChangeSession,
        bound: BoundCandidate,
        gate_receipts: tuple[GateReceiptV1, ...],
        prior_candidate_count: int = 0,
        operation_count: int = 1,
    ) -> CodeChangeRunRootV1:
        run_root = self.finalize_uc.execute(
            session=session,
            bound=bound,
            gate_receipts=gate_receipts,
            prior_candidate_count=prior_candidate_count,
            operation_count=operation_count,
        )
        if self.repo is not None:
            self.repo.save_run_root(run_root)
        return run_root
