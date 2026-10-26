"""Finite occurrence graph declarations; no execution or admission authority."""

from __future__ import annotations

import re
from dataclasses import dataclass, fields

from ..value_objects.identifier import OperationId

_ID = re.compile(r"[a-z][a-z0-9-]{0,63}\Z")
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")


class WorkflowShapeError(ValueError):
    """A malformed finite graph declaration at the domain seam."""

    code = "WORKFLOW_SHAPE_INVALID"


def _identifier(value: object) -> None:
    if type(value) is not str or _ID.fullmatch(value) is None:
        raise WorkflowShapeError("workflow identifiers must be bounded lowercase names")


def _slot(value: object) -> None:
    if type(value) is not int or not 0 <= value < 128:
        raise WorkflowShapeError("slot must be an exact integer in [0,128)")


def _collection(value: object, kind: type, minimum: int, maximum: int) -> None:
    if (
        type(value) is not tuple
        or not minimum <= len(value) <= maximum
        or any(type(item) is not kind for item in value)
    ):
        raise WorkflowShapeError(f"expected bounded tuple of {kind.__name__}")


class _ExactValue:
    __slots__ = ()

    def _parts(self) -> tuple:
        return tuple(getattr(self, field.name) for field in fields(self))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self._parts() == other._parts()

    def __hash__(self) -> int:
        return hash((type(self), self._parts()))


@dataclass(frozen=True, slots=True, eq=False)
class WorkflowNodeV1(_ExactValue):
    node_id: str
    operation_id: str
    source_digest: str
    operation_digest: str

    def __post_init__(self) -> None:
        _identifier(self.node_id)
        if (
            type(self.operation_id) is not str
            or str(OperationId(self.operation_id)) != self.operation_id
        ):
            raise WorkflowShapeError(
                "operation IDs use the existing exact bounded declaration carrier"
            )
        for digest in (self.source_digest, self.operation_digest):
            if type(digest) is not str or _DIGEST.fullmatch(digest) is None:
                raise WorkflowShapeError("node pins must be sha256: plus 64 lowercase hex digits")


@dataclass(frozen=True, slots=True, eq=False)
class WorkflowBindingV1(_ExactValue):
    source_node_id: str
    target_node_id: str
    target_slot: int

    def __post_init__(self) -> None:
        _identifier(self.source_node_id)
        _identifier(self.target_node_id)
        _slot(self.target_slot)


@dataclass(frozen=True, slots=True, eq=False)
class WorkflowInputV1(_ExactValue):
    node_id: str
    slot: int

    def __post_init__(self) -> None:
        _identifier(self.node_id)
        _slot(self.slot)


@dataclass(frozen=True, slots=True, eq=False)
class TypedWorkflowV1(_ExactValue):
    workflow_id: str
    root_node_id: str
    nodes: tuple[WorkflowNodeV1, ...]
    bindings: tuple[WorkflowBindingV1, ...]
    inputs: tuple[WorkflowInputV1, ...]

    def __post_init__(self) -> None:
        _identifier(self.workflow_id)
        _identifier(self.root_node_id)
        _collection(self.nodes, WorkflowNodeV1, 1, 128)
        _collection(self.bindings, WorkflowBindingV1, 0, 127)
        _collection(self.inputs, WorkflowInputV1, 0, 1024)
