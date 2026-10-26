"""
Planar Trees and Operadic Associativity Witnesses.
==================================================

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass

from .colours import ColourSignature
from .errors import Err, Ok, OperadAssociativityError, Result
from .operation import OperationSignature


@dataclass(frozen=True)
class PlanarTree:
    """Planar rooted tree representing a composite operadic computation."""
    root_op: OperationSignature
    children: tuple[PlanarTree | None, ...] = ()

    @property
    def arity(self) -> int:
        count = 0
        for i, child in enumerate(self.children):
            if child is None:
                count += 1
            else:
                count += child.arity
        return count


def compose_colour_signatures(
    f: ColourSignature,
    g: ColourSignature,
    index: int,
) -> Result[ColourSignature, OperadAssociativityError]:
    """The colour signature of ``f o_index g``, or a typed refusal.

    Admissible exactly when ``0 <= index < arity(f)`` and ``g``'s target is the
    colour ``f`` expects at ``index``. The composite consumes ``f``'s inputs with
    position ``index`` replaced, in place, by all of ``g``'s inputs, and produces
    ``f``'s target.
    """
    if type(index) is not int:
        return Err(OperadAssociativityError(f"index must be an exact int, got {type(index).__name__}"))
    if not 0 <= index < f.arity:
        return Err(OperadAssociativityError(f"index {index} out of bounds for arity {f.arity}"))
    if g.target != f.source[index]:
        return Err(
            OperadAssociativityError(
                f"composition ill-typed at {index}: expected {f.source[index]}, got {g.target}"
            )
        )
    return Ok(
        ColourSignature(
            source=f.source[:index] + g.source + f.source[index + 1 :],
            target=f.target,
        )
    )


def _left_bracketing(
    f: ColourSignature, g: ColourSignature, h: ColourSignature, i: int, j: int
) -> Result[ColourSignature, OperadAssociativityError]:
    """``(f o_i g) o_{i+j} h``: after ``g`` is spliced in at ``i``, ``g``'s
    input ``j`` sits at position ``i + j`` of the composite."""
    return compose_colour_signatures(f, g, i).bind(
        lambda fg: compose_colour_signatures(fg, h, i + j)
    )


def _right_bracketing(
    f: ColourSignature, g: ColourSignature, h: ColourSignature, i: int, j: int
) -> Result[ColourSignature, OperadAssociativityError]:
    """``f o_i (g o_j h)``."""
    return compose_colour_signatures(g, h, j).bind(
        lambda gh: compose_colour_signatures(f, gh, i)
    )


@dataclass(frozen=True)
class TreeCompositionWitness:
    """Record that both bracketings of one sequential insertion were composed.

    Sequential associativity is the statement

        (f o_i g) o_{i + j} h == f o_i (g o_j h)

    for ``0 <= i < arity(f)`` and ``0 <= j < arity(g)``. The witness carries the
    two composite signatures that were actually computed. It certifies this one
    instance at the level of colour signatures; it is not a proof of the axiom
    in general and says nothing about the operations' behaviour.
    """
    left_path: str
    right_path: str
    is_associative: bool
    details: str
    left_composite: ColourSignature | None = None
    right_composite: ColourSignature | None = None

    @classmethod
    def verify_sequential_associativity(
        cls,
        f: OperationSignature,
        g: OperationSignature,
        h: OperationSignature,
        i: int,
        j: int,
    ) -> Result[TreeCompositionWitness, OperadAssociativityError]:
        left = _left_bracketing(f.signature, g.signature, h.signature, i, j)
        if left.is_err:
            return Err(OperadAssociativityError(f"left bracketing refused: {left.error.message}"))
        right = _right_bracketing(f.signature, g.signature, h.signature, i, j)
        if right.is_err:
            return Err(OperadAssociativityError(f"right bracketing refused: {right.error.message}"))

        left_sig = left.unwrap()
        right_sig = right.unwrap()
        left_path = f"({f.op_id} o_{i} {g.op_id}) o_{i + j} {h.op_id}"
        right_path = f"{f.op_id} o_{i} ({g.op_id} o_{j} {h.op_id})"
        if left_sig != right_sig:
            return Err(
                OperadAssociativityError(
                    f"bracketings disagree: {left_path} = {left_sig} but {right_path} = {right_sig}"
                )
            )
        return Ok(
            cls(
                left_path=left_path,
                right_path=right_path,
                is_associative=True,
                details=f"both bracketings composed to {left_sig}",
                left_composite=left_sig,
                right_composite=right_sig,
            )
        )
