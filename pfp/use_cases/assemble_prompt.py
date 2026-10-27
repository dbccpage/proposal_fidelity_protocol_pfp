"""Prompt assembly use case for PFP stages and demos.

Education storage and aggregate adapter for runtime-owned prompt assembly.
AuthorityEffect: None.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Union

from pfp.domain.contracts.pfp_runtime import PfpStagePromptInput
from pfp.use_cases.pfp_prompt import AssemblePfpStagePromptUseCase

from ..domain.aggregates.pilot_aggregate import PilotAggregate
from ..domain.kernel.ports import PfpStoragePort
from ..domain.kernel.result import DomainError, RefusalCode, Result
from ..domain.prompts.prompts import PromptPacket
from ..domain.stages.stages import HOST_STAGES, STAGE_COUNT
from ..domain.value_objects.identifiers import PilotId, Sha256Digest
from ..domain.value_objects.numerics import StageNumber


class AssemblePromptUseCase:
    """Compiles prompt templates, seed values, and response schemas into PromptPacket."""

    def __init__(self, storage: PfpStoragePort) -> None:
        self.storage = storage

    def assemble(
        self,
        demo_id: Union[str, PilotId],
        stage: Union[int, StageNumber],
        seed_data: Dict[str, Any],
        template_id: str = "default_template",
    ) -> Result[PromptPacket, DomainError]:
        """Assemble PromptPacket accepting string/int or typed PilotId/StageNumber value objects."""
        try:
            d_id = str(demo_id.value if isinstance(demo_id, PilotId) else demo_id)
            st_num = int(stage.value if isinstance(stage, StageNumber) else stage)

            if st_num < 0 or st_num > STAGE_COUNT:
                return Result.err(
                    DomainError(
                        code=RefusalCode.UNKNOWN_STAGE,
                        message=f"Invalid stage index: {st_num}",
                        stage=st_num,
                    )
                )

            # Load the model schema of a model stage; stage 1 has one for its repair turn.
            response_schema: Dict[str, Any] = {}
            if st_num > 0 and (st_num not in HOST_STAGES or st_num == 1):
                stage_file = self.storage.load_stage_file(st_num)
                response_schema = deepcopy(stage_file.response_schema or {})
                if response_schema:
                    response_schema["properties"]["demo_id"]["const"] = d_id

            template = self.storage.load_prompt_template(template_id)
            assembled = AssemblePfpStagePromptUseCase().execute(
                PfpStagePromptInput(
                    template.system_format,
                    template.user_format,
                    seed_data,
                    response_schema,
                )
            )
            system_text, user_text = assembled.system, assembled.user
            response_schema = assembled.response_schema

            sys_sha = Sha256Digest.compute(system_text.encode("utf-8")).value
            user_sha = Sha256Digest.compute(user_text.encode("utf-8")).value
            schema_sha = Sha256Digest.compute(str(response_schema).encode("utf-8")).value

            packet = PromptPacket(
                demo_id=d_id,
                stage=st_num,
                system=system_text,
                user=user_text,
                response_schema=response_schema,
                system_sha256=sys_sha,
                user_sha256=user_sha,
                schema_sha256=schema_sha,
                derived_under_policy="SPK-001",
                authority_effect="None",
            )
            return Result.ok(packet)

        except Exception as exc:
            st = (
                int(stage.value if isinstance(stage, StageNumber) else stage)
                if isinstance(stage, (int, StageNumber))
                else None
            )
            return Result.err(
                DomainError(
                    code=RefusalCode.PARSER_ERROR,
                    message=f"Failed to assemble prompt packet: {str(exc)}",
                    stage=st,
                )
            )

    def assemble_pilot(
        self,
        pilot: PilotAggregate,
        stage: Union[int, StageNumber] = 1,
        template_id: str = "default_template",
    ) -> Result[PromptPacket, DomainError]:
        """Assemble a PromptPacket directly from a typed PilotAggregate."""
        if not isinstance(pilot, PilotAggregate):
            return Result.err(
                DomainError(
                    code=RefusalCode.TYPING_VIOLATION,
                    message=f"Expected PilotAggregate, received {type(pilot).__name__}",
                )
            )
        demo_id = getattr(pilot, "target", "") or pilot.pilot_id.value
        seed_prompt = getattr(pilot, "seed_prompt", "") or (
            pilot.ingress.prompt_text if hasattr(pilot, "ingress") else ""
        )
        seed_data = {"user_prompt": seed_prompt}
        return self.assemble(
            demo_id=demo_id,
            stage=stage,
            seed_data=seed_data,
            template_id=template_id,
        )

    assemble_for_pilot = assemble_pilot
