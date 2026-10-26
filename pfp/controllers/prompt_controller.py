"""Prompt Controller coordinating prompt compilation and residual validation."""

from __future__ import annotations

from typing import Any, Mapping

from ..domain import (
    DemandItemV1,
    EliminationReceiptV1,
    ObjectiveTypedV1,
    ObstructionHintV1,
    PromptArtifactV1,
    ResidualColour,
)
from ..domain.ports import IPromptRepository
from ..use_cases import (
    CompilePromptUseCase,
    EliminateObstructionUseCase,
    ValidateReplyResidualUseCase,
)


class PromptController:
    """Application controller orchestrating prompt compilation use cases."""

    def __init__(
        self,
        repository: IPromptRepository | None = None,
        compile_use_case: CompilePromptUseCase | None = None,
        validate_use_case: ValidateReplyResidualUseCase | None = None,
        eliminate_use_case: EliminateObstructionUseCase | None = None,
    ) -> None:
        self.repo = repository
        self.compile_uc = compile_use_case or CompilePromptUseCase()
        self.validate_uc = validate_use_case or ValidateReplyResidualUseCase()
        self.eliminate_uc = eliminate_use_case or EliminateObstructionUseCase()

    def compile_prompt(
        self,
        *,
        prompt_artifact_id: str,
        regime_kind: str,
        prompt_body: str,
        regime_metadata: Mapping[str, Any] | None = None,
        admitted_constructors: tuple[str, ...] = (),
        open_obstructions: tuple[ObstructionHintV1, ...] = (),
        demand_set: tuple[DemandItemV1, ...] = (),
        kill_conditions: tuple[str, ...] = (),
        required_reply_fields: tuple[str, ...] = (),
        objective: ObjectiveTypedV1 | None = None,
        residual_colour: str = ResidualColour.OPEN.value,
        dual_witness_required: bool = False,
        dual_witness_ref: str | None = None,
        parent_packet_id: str | None = None,
        conversation_root_id: str | None = None,
    ) -> PromptArtifactV1:
        artifact = self.compile_uc.execute(
            prompt_artifact_id=prompt_artifact_id,
            regime_kind=regime_kind,
            prompt_body=prompt_body,
            regime_metadata=regime_metadata,
            admitted_constructors=admitted_constructors,
            open_obstructions=open_obstructions,
            demand_set=demand_set,
            kill_conditions=kill_conditions,
            required_reply_fields=required_reply_fields,
            objective=objective,
            residual_colour=residual_colour,
            dual_witness_required=dual_witness_required,
            dual_witness_ref=dual_witness_ref,
            parent_packet_id=parent_packet_id,
            conversation_root_id=conversation_root_id,
        )
        if self.repo is not None:
            self.repo.save_prompt_artifact(artifact)
        return artifact

    def validate_reply(self, artifact: PromptArtifactV1, reply_content: str) -> bool:
        return self.validate_uc.execute(artifact=artifact, reply_content=reply_content)

    def eliminate_obstruction(
        self,
        *,
        packet_id: str,
        prior_residual_colour: str,
        new_residual_colour: str,
        evidence_root: str,
        eliminated_obstruction_ids: tuple[str, ...] = (),
        dual_witness_ref: str | None = None,
    ) -> EliminationReceiptV1:
        receipt = self.eliminate_uc.execute(
            packet_id=packet_id,
            prior_residual_colour=prior_residual_colour,
            new_residual_colour=new_residual_colour,
            evidence_root=evidence_root,
            eliminated_obstruction_ids=eliminated_obstruction_ids,
            dual_witness_ref=dual_witness_ref,
        )
        if self.repo is not None:
            self.repo.save_elimination_receipt(receipt)
        return receipt
