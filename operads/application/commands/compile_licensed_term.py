"""Command Handler: Compile Licensed Term."""

from __future__ import annotations

from operations.domain.rop.result import Err, Ok, Result
from ..dtos.api_error_dto import ApiErrorDTO
from ..dtos.command_dtos import CompileLicensedTermCommand
from ..dtos.success_dtos import LicensedTermResultDTO
from ..ports.strict_operad_port import StrictOperadPort


class CompileLicensedTermHandler:
    def __init__(self, operad_port: StrictOperadPort) -> None:
        self._operad_port = operad_port

    def handle(self, command: CompileLicensedTermCommand) -> Result[LicensedTermResultDTO, ApiErrorDTO]:
        auth_res = self._operad_port.authorize_term(command.agent_id, command.term_expr)
        if auth_res.is_err:
            err = auth_res.unwrap_err()
            return Err(ApiErrorDTO(
                code=err.code,
                message=err.message,
                status_code=422,
            ))
        normalized_digest = auth_res.unwrap()
        return Ok(LicensedTermResultDTO(
            agent_id=command.agent_id,
            term_expr=command.term_expr,
            is_authorized=True,
            normalized_digest=normalized_digest,
        ))
