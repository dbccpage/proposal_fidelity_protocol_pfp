"""Colour Value Objects and Type Predicates.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Iterable, Sequence

from operads.canon import OPERAD_COLOUR

from .errors import InvalidColourError

ADMITTED_FINITE_COLOURS: FrozenSet[str] = frozenset(OPERAD_COLOUR)


@dataclass(frozen=True)
class Colour:
    """A single object colour in a multi-coloured symmetric operad."""
    name: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise InvalidColourError("Colour name must be a non-empty string.")
        if self.name not in ADMITTED_FINITE_COLOURS:
            raise InvalidColourError(
                f"Colour '{self.name}' is not in admitted finite colours: {sorted(list(ADMITTED_FINITE_COLOURS))}"
            )

    def is_admitted(self, vocabulary: FrozenSet[str] = ADMITTED_FINITE_COLOURS) -> bool:
        return self.name in vocabulary

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class ColourSignature:
    """The source colour sequence and target colour for an operation."""
    source: tuple[Colour, ...]
    target: Colour

    @property
    def arity(self) -> int:
        return len(self.source)

    @classmethod
    def from_strings(cls, source: Sequence[str], target: str) -> ColourSignature:
        return cls(
            source=tuple(Colour(s) for s in source),
            target=Colour(target),
        )

    def to_tuple(self) -> tuple[tuple[str, ...], str]:
        return (tuple(c.name for c in self.source), self.target.name)

    def validate_admitted(self, vocabulary: FrozenSet[str] = ADMITTED_FINITE_COLOURS) -> None:
        for c in self.source:
            if not c.is_admitted(vocabulary):
                raise InvalidColourError(f"Unadmitted source colour: {c.name}")
        if not self.target.is_admitted(vocabulary):
            raise InvalidColourError(f"Unadmitted target colour: {self.target.name}")
