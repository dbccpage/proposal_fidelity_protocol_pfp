"""
Coloured Symmetric Operad Aggregate Root.
=========================================

Enforces multi-coloured operad axioms, unit laws, type-safe composition,
symmetric permutation actions, and agent capability slices.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from .colours import ADMITTED_FINITE_COLOURS, Colour, ColourSignature
from .errors import (
    ArityMismatchError,
    DomainError,
    Err,
    IllTypedCompositionError,
    InvalidColourError,
    MissingUnitError,
    Ok,
    Result,
    SliceViolationError,
)
from .operation import OperationId, OperationSignature


@dataclass
class AgentSlice:
    """A capability slice restricting an agent to a typed subset of operad operations."""
    agent_id: str
    licensed_operations: set[str]
    allowed_sources: set[str] = field(default_factory=set)
    allowed_targets: set[str] = field(default_factory=set)


class ColouredOperad:
    """The formal multi-coloured symmetric operad aggregate root."""

    def __init__(self, colours: Sequence[str] | None = None) -> None:
        self._colours: set[str] = set(colours) if colours is not None else set(ADMITTED_FINITE_COLOURS)
        self._operations: dict[str, OperationSignature] = {}

    @property
    def colours(self) -> set[str]:
        return set(self._colours)

    @property
    def operations(self) -> dict[str, OperationSignature]:
        return dict(self._operations)

    def add_colour(self, colour: Colour | str) -> None:
        c_name = colour.name if isinstance(colour, Colour) else str(colour)
        if c_name not in ADMITTED_FINITE_COLOURS:
            raise InvalidColourError(f"Colour '{c_name}' not in admitted finite colours")
        self._colours.add(c_name)

    def add_operation(self, op: OperationSignature) -> None:
        for c in op.source:
            if c.name not in self._colours:
                raise InvalidColourError(f"Operation '{op.op_id}' has un-admitted source colour: {c.name}")
        if op.target.name not in self._colours:
            raise InvalidColourError(f"Operation '{op.op_id}' has un-admitted target colour: {op.target.name}")
        existing=self._operations.get(op.op_id.value)
        if existing is not None and existing != op:
            raise ValueError(f"conflicting operation {op.op_id}")
        self._operations[op.op_id.value] = op

    def ensure_units(self) -> list[str]:
        """Ensures that every admitted colour C has an identity operation id_C: C -> C."""
        added = []
        for c_name in sorted(self._colours):
            unit_op = OperationSignature.unit(c_name)
            existing=self._operations.get(unit_op.op_id.value)
            if existing is not None and not existing.is_unit:
                raise MissingUnitError(f"unit name occupied by nonidentity: {unit_op.op_id}")
            if unit_op.op_id.value not in self._operations:
                self._operations[unit_op.op_id.value] = unit_op
                added.append(unit_op.op_id.value)
        return added

    def partial_compose(
        self,
        f: OperationSignature,
        g: OperationSignature,
        i: int,
    ) -> Result[OperationSignature, IllTypedCompositionError | ArityMismatchError]:
        """Calculates the partial operadic composition f circle_i g.

        Domain Axioms:
          1. 0 <= i < arity(f)
          2. target(g) == source(f)[i]
          3. Result signature: (s_0, ..., s_{i-1}, g_0, ..., g_{m-1}, s_{i+1}, ...) -> target(f)
        """
        if i < 0 or i >= f.arity:
            return Err(
                ArityMismatchError(
                    f"Invalid insertion index i={i} for operation {f.op_id} of arity {f.arity}"
                )
            )

        target_source_colour = f.source[i]
        if g.target != target_source_colour:
            return Err(
                IllTypedCompositionError(
                    f"Type mismatch in composition: {f.op_id} expects {target_source_colour} at position {i}, "
                    f"but {g.op_id} outputs {g.target}"
                )
            )

        new_source = f.source[:i] + g.source + f.source[i + 1 :]
        new_target = f.target
        new_op_id = OperationId(f"({f.op_id.value}_o_{i}_{g.op_id.value})")

        composite_sig = OperationSignature(
            op_id=new_op_id,
            signature=ColourSignature(source=new_source, target=new_target),
            equivariant=f.equivariant and g.equivariant,
            residual_effect=f"composite({f.residual_effect}, {g.residual_effect})",
        )
        return Ok(composite_sig)

    def verify_agent_permission(self, agent_slice: AgentSlice, op_id: str) -> Result[bool, SliceViolationError]:
        """Enforces that an agent invocation stays strictly within its capability slice."""
        if op_id not in self._operations:
            return Err(SliceViolationError(f"Operation '{op_id}' does not exist in operad"))

        op = self._operations[op_id]
        if op.is_unit:
            return Ok(True)

        if op_id not in agent_slice.licensed_operations:
            return Err(
                SliceViolationError(
                    f"Agent '{agent_slice.agent_id}' is not licensed to execute operation '{op_id}'"
                )
            )

        if agent_slice.allowed_sources:
            for s in op.source_colours:
                if s not in agent_slice.allowed_sources:
                    return Err(
                        SliceViolationError(
                            f"Agent '{agent_slice.agent_id}' cannot use input colour '{s}' for operation '{op_id}'"
                        )
                    )

        if agent_slice.allowed_targets:
            if op.target_colour not in agent_slice.allowed_targets:
                return Err(
                    SliceViolationError(
                        f"Agent '{agent_slice.agent_id}' cannot produce output colour '{op.target_colour}'"
                    )
                )

        return Ok(True)

    def validate_types(self):
        for op in self._operations.values():
            if any(c.name not in self._colours for c in (*op.source,op.target)):
                raise InvalidColourError(str(op.op_id))

    def compose(self, outer_id, slot, inner_id, composite_id=None):
        outer=self._operations.get(str(outer_id)); inner=self._operations.get(str(inner_id))
        if outer is None or inner is None:
            return Err(IllTypedCompositionError("unknown operation"))
        result=self.partial_compose(outer,inner,slot)
        if result.is_err or composite_id is None:
            return result
        from dataclasses import replace
        return Ok(replace(result.value,op_id=OperationId(str(composite_id))))

    def slice(self,agent_id,licensed_operations):
        names=set(licensed_operations)
        if names-self._operations.keys():
            raise SliceViolationError("unknown licensed operation")
        return AgentSlice(agent_id,names,{c for name in names for c in self._operations[name].source_colours},{self._operations[name].target_colour for name in names})
