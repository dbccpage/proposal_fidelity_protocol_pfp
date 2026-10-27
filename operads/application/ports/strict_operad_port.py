"""Anti-corruption port translating WAS operations to higher_operad kernel."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Tuple

from operations.domain.rop.result import Result
from ...domain.entities.operation_v3 import OperationV3
from ...domain.errors.domain_errors import OeopDomainError


class StrictOperadPort(ABC):
    @abstractmethod
    def verify_composition(
        self,
        root_op: OperationV3,
        child_ops: Tuple[OperationV3, ...],
        slot_bindings: Tuple[Tuple[int, OperationV3], ...],
    ) -> Result[bool, OeopDomainError]:
        """Verify strict operadic substitution and colour/schema agreement."""
        pass

    @abstractmethod
    def authorize_term(
        self,
        agent_id: str,
        term_expr: str,
    ) -> Result[str, OeopDomainError]:
        """Authorize term against agent license and return normalized term digest."""
        pass
