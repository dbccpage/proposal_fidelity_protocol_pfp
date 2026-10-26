"""CompositionV3 Entity in OEWAS V3."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from ..value_objects.identifier import OperationId


@dataclass(frozen=True, slots=True)
class CompositionV3:
    composition_id: str
    term_kind: str  # "unit", "primitive", "substitute"
    root_operation_id: OperationId
    child_operation_ids: Tuple[OperationId, ...] = ()
    slot_bindings: Tuple[Tuple[int, OperationId], ...] = ()
    expected_boundary: str = ""

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.composition_id == other.composition_id
            and self.term_kind == other.term_kind
            and self.root_operation_id == other.root_operation_id
            and self.child_operation_ids == other.child_operation_ids
            and self.slot_bindings == other.slot_bindings
            and self.expected_boundary == other.expected_boundary
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.composition_id,
            self.term_kind,
            self.root_operation_id,
            self.child_operation_ids,
            self.slot_bindings,
            self.expected_boundary,
        ))
