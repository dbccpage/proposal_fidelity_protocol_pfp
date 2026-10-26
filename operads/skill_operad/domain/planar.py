"""Executable coloured planar multicategory (ordered operad fragment).

Strict colour matching, multi-ary substitution, residual absorption, free Term
trees. Not a symmetric operad — Sn action lives on the registry aggregate when
an operation is declared equivariant.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

from .errors import DomainError
from .evidence import EMPTY, Residual

Color = str


class OperadError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__("OPERAD_ERROR", message)


class ArityMismatch(OperadError, ValueError):
    def __init__(self, expected: int, got: int, context: str):
        super().__init__(f"Arity mismatch in {context}: expected {expected}, got {got}")
        self.expected = expected
        self.got = got


class ColorMismatch(OperadError, TypeError):
    def __init__(self, slot: int, expected: str, got: str, outer: str, inner: str):
        super().__init__(
            f"Color mismatch at slot {slot} of {outer!r}: "
            f"expected {expected!r}, got {got!r} from {inner!r}"
        )
        self.slot = slot
        self.expected = expected
        self.got = got


class ArgumentCountError(OperadError, ValueError):
    pass


@dataclass(frozen=True)
class ColoredOp:
    """An operation of a coloured planar multicategory."""

    name: str
    source_colors: Tuple[Color, ...]
    target_color: Color
    body: Callable[..., Tuple[object, Residual]] = field(repr=False, compare=False)
    residual: Residual = EMPTY
    _identity: bool = field(default=False, init=False, repr=False)

    @property
    def arity(self) -> int:
        return len(self.source_colors)

    def __call__(self, *args: object) -> Tuple[object, Residual]:
        if len(args) != self.arity:
            raise ArityMismatch(self.arity, len(args), self.name)
        result, dyn = self.body(*args)
        return result, self.residual + dyn

    def compose(self, *inners: "ColoredOp") -> "ColoredOp":
        if len(inners) != self.arity:
            raise ArityMismatch(self.arity, len(inners), self.name)

        for i, (inner, expected) in enumerate(zip(inners, self.source_colors)):
            if inner.target_color != expected:
                raise ColorMismatch(i, expected, inner.target_color, self.name, inner.name)

        if self.arity > 0 and all(
            _is_pure_identity(op, col) for op, col in zip(inners, self.source_colors)
        ):
            return self

        new_residual = EMPTY
        new_sources = tuple(c for op in inners for c in op.source_colors)
        outer = self

        def composed_body(*flat_args_input: object) -> Tuple[object, Residual]:
            flat_args = flat_args_input

            parts: List[Tuple[object, ...]] = []
            idx = 0
            for op in inners:
                n = op.arity
                parts.append(flat_args[idx : idx + n])
                idx += n
            if idx != len(flat_args):
                raise ArityMismatch(idx, len(flat_args), "composed_body")

            inter: List[object] = []
            total_dyn = EMPTY
            for op, part in zip(inners, parts):
                val, dyn = op(*part)
                inter.append(val)
                total_dyn = total_dyn + dyn

            final, dyn_outer = outer(*inter)
            return final, total_dyn + dyn_outer

        if self.arity == 1 and len(inners) == 1:
            name = f"{self.name}\u2218{inners[0].name}"
        else:
            name = f"({self.name} \u2218 {', '.join(op.name for op in inners)})"

        return ColoredOp(
            name=name,
            source_colors=new_sources,
            target_color=self.target_color,
            residual=new_residual,
            body=composed_body,
        )

    def __repr__(self) -> str:
        src = ", ".join(self.source_colors)
        return f"ColoredOp({self.name!r}: ({src}) \u2192 {self.target_color})"


def _is_pure_identity(op: ColoredOp, color: Color) -> bool:
    return (
        op.arity == 1
        and op.source_colors[0] == color
        and op.target_color == color
        and op.residual.is_empty
        and op._identity
    )


def identity(color: Color, name: Optional[str] = None) -> ColoredOp:
    def id_body(value: object) -> Tuple[object, Residual]:
        return value, EMPTY

    result = ColoredOp(
        name=name or f"id_{color}",
        source_colors=(color,),
        target_color=color,
        residual=EMPTY,
        body=id_body,
    )
    object.__setattr__(result, "_identity", True)
    return result


def nullary(color: Color, value: object, name: Optional[str] = None) -> ColoredOp:
    def const_body() -> Tuple[object, Residual]:
        return value, EMPTY

    return ColoredOp(
        name=name or f"const_{color}",
        source_colors=(),
        target_color=color,
        residual=EMPTY,
        body=const_body,
    )


@dataclass(frozen=True)
class Term:
    op: ColoredOp
    children: Tuple["Term", ...] = ()

    def __post_init__(self) -> None:
        if len(self.children) != self.op.arity:
            raise ArityMismatch(self.op.arity, len(self.children), self.op.name)
        for i, (child, expected) in enumerate(zip(self.children, self.op.source_colors)):
            if child.op.target_color != expected:
                raise ColorMismatch(
                    i, expected, child.op.target_color, self.op.name, child.op.name
                )

    @property
    def color(self) -> Color:
        return self.op.target_color

    def evaluate(self) -> Tuple[object, Residual]:
        if self.op.arity == 0:
            return self.op()
        child_vals = []
        total = EMPTY
        for ch in self.children:
            v, r = ch.evaluate()
            child_vals.append(v)
            total = total + r
        result, op_residual = self.op(*child_vals)
        return result, total + op_residual


def formal_compose(outer: ColoredOp, *children: Term) -> Term:
    return Term(op=outer, children=children)


def receipt_to_residual(receipt: object) -> Residual:
    residual_strs = tuple(getattr(receipt, "residual", ()) or ())
    unverified = tuple(getattr(receipt, "unverified_claims", ()) or ())
    witnesses = tuple(getattr(receipt, "witnesses_found", ()) or ())
    if witnesses:
        risk = 1.0
    elif residual_strs or unverified:
        risk = 0.7
    else:
        risk = 0.0
    return Residual(obligations=residual_strs + unverified, risk=risk)
