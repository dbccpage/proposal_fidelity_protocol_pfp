"""Wire vocabulary and retained probability mass value objects for constrained decoding.

Zero outward dependencies. Zero-Float Law enforced in fractions.Fraction.
AuthorityEffect: None.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence

from .errors import ZeroFloatViolationError


@dataclass(frozen=True)
class RetainedProbabilityMass:
    """Retained probability mass over an admissible token support carrier."""

    mass: Fraction

    def __post_init__(self) -> None:
        if isinstance(self.mass, float):
            raise ZeroFloatViolationError("RetainedProbabilityMass requires Fraction, float forbidden")
        if not isinstance(self.mass, Fraction):
            if isinstance(self.mass, int):
                object.__setattr__(self, "mass", Fraction(self.mass, 1))
            else:
                raise TypeError(f"mass must be a Fraction or int, got {type(self.mass)}")
        if self.mass < Fraction(0, 1) or self.mass > Fraction(1, 1):
            raise ValueError(f"Retained probability mass must be in [0, 1], got {self.mass}")

    def is_zero(self) -> bool:
        return self.mass.numerator == 0

    def is_one(self) -> bool:
        return self.mass == Fraction(1, 1)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, RetainedProbabilityMass)
        return self.mass == other.mass

    def __hash__(self) -> int:
        return hash((type(self), self.mass))


@dataclass(frozen=True)
class WireVocabulary:
    """Discrete wire vocabulary for symbolic token generation."""

    tokens: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.tokens, tuple):
            object.__setattr__(self, "tokens", tuple(self.tokens))
        if len(set(self.tokens)) != len(self.tokens):
            raise ValueError("Duplicate tokens detected in vocabulary definition")

    @classmethod
    def toy_4(cls) -> WireVocabulary:
        """Toy vocabulary of 4 alphabetic tokens."""
        return cls(("a", "b", "c", "d"))

    @classmethod
    def toy_8(cls) -> WireVocabulary:
        """Toy vocabulary of 8 tokens (6 digits and delimiters)."""
        return cls(("0", "1", "2", "3", "4", "5", "<", ">"))

    @classmethod
    def sigma_36(cls) -> WireVocabulary:
        """Alphanumeric base alphabet Sigma_36 ([0-9a-z])."""
        return cls(tuple("0123456789abcdefghijklmnopqrstuvwxyz"))

    @classmethod
    def gamma_38(cls) -> WireVocabulary:
        """Full wire protocol vocabulary Gamma_38 (<, >, Sigma_36)."""
        return cls(("<", ">") + tuple("0123456789abcdefghijklmnopqrstuvwxyz"))

    @classmethod
    def from_iterable(cls, tokens: Sequence[str]) -> WireVocabulary:
        return cls(tuple(tokens))

    @property
    def size(self) -> int:
        return len(self.tokens)

    def token_to_id(self, token: str) -> int:
        if token not in self.tokens:
            raise KeyError(f"Token '{token}' not found in vocabulary")
        return self.tokens.index(token)

    def id_to_token(self, token_id: int) -> str:
        if not (0 <= token_id < len(self.tokens)):
            raise IndexError(f"Token ID {token_id} out of bounds for vocabulary size {len(self.tokens)}")
        return self.tokens[token_id]

    def contains(self, token: str) -> bool:
        return token in self.tokens

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, WireVocabulary)
        return self.tokens == other.tokens

    def __hash__(self) -> int:
        return hash((type(self), self.tokens))


__all__ = [
    "RetainedProbabilityMass",
    "WireVocabulary",
]
