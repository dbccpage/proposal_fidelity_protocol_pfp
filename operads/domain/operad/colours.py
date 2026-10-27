"""
Colour and ColourSignature Domain Value Objects.
================================================

Canonical finite colours for the Sentinel operadic categories:
State, Proof, Paper, Code, Contract, Receipt, Ledger, Diagram, Audit, Post.

The tuple is read from the operad canon (``code/rust/core_operad_canon``), the one
definition of the vocabulary; every other colour list imports it. It once omitted
``Contract`` and ``Diagram``, which silently changed the arity of every skill
declaring them and rewrote their target colour to ``Receipt`` -- 16 admitted
skills were affected, among them ``blackrod``, ``rip-lawyers`` and
``nomos-law-contract-manager``.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from operads.canon import OPERAD_COLOUR

ADMITTED_FINITE_COLOURS: tuple[str, ...] = OPERAD_COLOUR


@dataclass(frozen=True)
class Colour:
    """Strongly-typed colour object for the operad."""
    name: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Colour name must be a non-empty string.")
        if self.name not in ADMITTED_FINITE_COLOURS:
            raise ValueError(f"Colour '{self.name}' not in admitted finite colours: {ADMITTED_FINITE_COLOURS}")

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.name == other.name

    def __hash__(self) -> int:
        return hash((type(self), self.name))


@dataclass(frozen=True)
class ColourSignature:
    """Operadic signature specifying source colours and single target colour."""
    source: tuple[Colour, ...]
    target: Colour

    def __init__(self, source: Sequence[Colour | str], target: Colour | str) -> None:
        src_colours = tuple(c if isinstance(c, Colour) else Colour(str(c)) for c in source)
        tgt_colour = target if isinstance(target, Colour) else Colour(str(target))
        object.__setattr__(self, "source", src_colours)
        object.__setattr__(self, "target", tgt_colour)

    @property
    def arity(self) -> int:
        return len(self.source)

    @property
    def is_nullary(self) -> bool:
        return len(self.source) == 0

    def __str__(self) -> str:
        src = ", ".join(c.name for c in self.source)
        return f"({src}) -> {self.target.name}"

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.source == other.source and self.target == other.target

    def __hash__(self) -> int:
        return hash((type(self), self.source, self.target))
