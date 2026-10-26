"""DispatchOperationUseCase: Resolves and validates operadic operation dispatch.

AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

try:
    from domain.colours import Colour
    from domain.errors import DomainError, Err, Ok, Result
    from omega_engine_operads.domain.operad.operad import ColouredOperad
    from domain.ports import OperadRepositoryPort
    from application.dto.operad_dto import DispatchResultDTO
except (ImportError, ValueError):
    from ...domain.colours import Colour
    from ...domain.errors import DomainError, Err, Ok, Result
    from omega_engine_operads.domain.operad.operad import ColouredOperad
    from ...domain.ports import OperadRepositoryPort
    from ..dto.operad_dto import DispatchResultDTO


class DispatchOperationUseCase:
    """Application use case for resolving and validating operation dispatch."""

    def __init__(self, repository: OperadRepositoryPort) -> None:
        self.repository = repository
        self._operad: Optional[ColouredOperad] = None

    def _get_operad(self) -> ColouredOperad:
        if self._operad is None:
            self._operad = self.repository.load_operad()
            self._operad.ensure_units()
        return self._operad

    def resolve_operation(self, op_id: str) -> Result[DispatchResultDTO, str]:
        operad = self._get_operad()
        if op_id not in operad.operations:
            return Err(f"Operation '{op_id}' is not registered in the operad.")

        op = operad.operations[op_id]
        dto = DispatchResultDTO(
            op_id=op.op_id.value,
            is_resolved=True,
            source_colours=tuple(c.name for c in op.source),
            target_colour=op.target.name,
            detail=f"Resolved registered operation '{op_id}' with arity {op.arity}.",
            authority_effect="None",
        )
        return Ok(dto)

    def validate_agent_dispatch(self, agent_id: str, op_id: str) -> Result[DispatchResultDTO, str]:
        operad = self._get_operad()
        slices_data = self.repository.load_agent_capability_slices()
        agents = slices_data.get("agents", {})

        if agent_id not in agents:
            return Err(f"Agent '{agent_id}' has no declared capability slice.")

        licensed = set(agents[agent_id].get("licensed_skills", []))
        if op_id not in licensed:
            return Err(f"Agent '{agent_id}' is not licensed to execute operation '{op_id}'.")

        return self.resolve_operation(op_id)
