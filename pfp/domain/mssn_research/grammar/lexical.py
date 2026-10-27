"""Value Objects for the Grammar Bounded Context.

Enforces:
- Exact-Type Equality (RULE_VO_EXACT_TYPE_EQUALITY_001)
- Immutability and Pure Python language types
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from pfp.domain.mssn_research.shared_kernel.value_objects import (
    Rational,
    StageLevel,
)


@dataclass(frozen=True)
class Alphabet:
    """Admitted glyph vocabulary for a discrete stage level."""
    allowed_glyphs: frozenset[str]
    stage_level: StageLevel

    def __post_init__(self) -> None:
        if not isinstance(self.allowed_glyphs, frozenset):
            object.__setattr__(self, "allowed_glyphs", frozenset(self.allowed_glyphs))
        if not isinstance(self.stage_level, StageLevel):
            raise TypeError("stage_level must be a StageLevel Value Object")

    @classmethod
    def level_0(cls) -> Alphabet:
        """Level 0: empty alphabet; only primitive delimiters < and > admit <>."""
        return cls(allowed_glyphs=frozenset(), stage_level=StageLevel(0))

    @classmethod
    def level_1(cls) -> Alphabet:
        """Level 1: binary data mode Sigma_2 = {0, 1}."""
        return cls(allowed_glyphs=frozenset("01"), stage_level=StageLevel(1))

    @classmethod
    def level_2_plus(cls, stage: StageLevel) -> Alphabet:
        """Level 2+: alphanumeric alphabet Sigma_36 = {0..9, a..z}."""
        glyphs = frozenset("0123456789abcdefghijklmnopqrstuvwxyz")
        return cls(allowed_glyphs=glyphs, stage_level=stage)

    @classmethod
    def for_stage(cls, stage: StageLevel, strict_two_glyph: bool = False) -> Alphabet:
        """Construct stage alphabet following §12.1 literal schedule or §12.2 general tower."""
        if stage.level == 0:
            return cls.level_0()
        if stage.level == 1:
            return cls.level_1()
        if strict_two_glyph:
            pairs = [
                "01", "23", "45", "67", "89", "ab", "cd", "ef",
                "gh", "ij", "kl", "mn", "op", "qr", "st", "uv", "wx", "yz"
            ]
            accum: set[str] = set()
            for i in range(min(stage.level, len(pairs))):
                accum.update(pairs[i])
            return cls(allowed_glyphs=frozenset(accum), stage_level=stage)
        return cls.level_2_plus(stage)

    def contains(self, char: str) -> bool:
        return char in self.allowed_glyphs

    def contains_all(self, s: str) -> bool:
        return all(c in self.allowed_glyphs for c in s)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, Alphabet)
        return self.allowed_glyphs == other.allowed_glyphs and self.stage_level == other.stage_level

    def __hash__(self) -> int:
        return hash((type(self), self.allowed_glyphs, self.stage_level))

    def __repr__(self) -> str:
        return f"Alphabet(stage={self.stage_level.level}, size={len(self.allowed_glyphs)})"


@dataclass(frozen=True)
class ParserStateId:
    """Discrete state identifier in the incremental grammar parser."""
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("ParserStateId value must be a str")
        if not self.value:
            raise ValueError("ParserStateId cannot be empty")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ParserStateId)
        return self.value == other.value

    def __hash__(self) -> int:
        return hash((type(self), self.value))

    def __repr__(self) -> str:
        return f"ParserStateId({self.value!r})"


@dataclass(frozen=True)
class ProbabilityMass:
    """Exact rational probability mass in [0, 1]."""
    mass: Rational

    def __post_init__(self) -> None:
        if not isinstance(self.mass, Rational):
            raise TypeError("mass must be a Rational Value Object")
        if self.mass.numerator < 0:
            raise ValueError(f"Probability mass cannot be negative, got {self.mass}")
        if self.mass.numerator > self.mass.denominator:
            raise ValueError(f"Probability mass cannot exceed 1, got {self.mass}")

    def is_zero(self) -> bool:
        return self.mass.numerator == 0

    def is_one(self) -> bool:
        return self.mass.numerator == self.mass.denominator

    @classmethod
    def zero(cls) -> ProbabilityMass:
        return cls(Rational(0, 1))

    @classmethod
    def one(cls) -> ProbabilityMass:
        return cls(Rational(1, 1))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ProbabilityMass)
        return self.mass == other.mass

    def __hash__(self) -> int:
        return hash((type(self), self.mass))

    def __repr__(self) -> str:
        return f"ProbabilityMass({self.mass.to_wire()})"


@dataclass(frozen=True)
class FrontierCandidate:
    """Individual candidate token proposal at an incremental grammar frontier."""
    token_id: int
    emitted_bytes: bytes
    parser_state_after: ParserStateId
    base_probability: Rational
    constrained_probability: Rational

    def __post_init__(self) -> None:
        if not isinstance(self.token_id, int) or isinstance(self.token_id, bool) or self.token_id < 0:
            raise ValueError("token_id must be a non-negative int")
        if not isinstance(self.emitted_bytes, bytes):
            raise TypeError("emitted_bytes must be bytes")
        if not isinstance(self.parser_state_after, ParserStateId):
            raise TypeError("parser_state_after must be a ParserStateId")
        if not isinstance(self.base_probability, Rational):
            raise TypeError("base_probability must be a Rational")
        if self.base_probability.numerator < 0 or self.base_probability.numerator > self.base_probability.denominator:
            raise ValueError(f"base_probability must be in [0, 1], got {self.base_probability}")
        if not isinstance(self.constrained_probability, Rational):
            raise TypeError("constrained_probability must be a Rational")
        if self.constrained_probability.numerator < 0 or self.constrained_probability.numerator > self.constrained_probability.denominator:
            raise ValueError(f"constrained_probability must be in [0, 1], got {self.constrained_probability}")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, FrontierCandidate)
        return (
            self.token_id == other.token_id
            and self.emitted_bytes == other.emitted_bytes
            and self.parser_state_after == other.parser_state_after
            and self.base_probability == other.base_probability
            and self.constrained_probability == other.constrained_probability
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.token_id,
            self.emitted_bytes,
            self.parser_state_after,
            self.base_probability,
            self.constrained_probability
        ))


@dataclass(frozen=True)
class QuantifierMask:
    """Quantifier alternation block mask (e.g. '010' for forall-exists-forall)."""
    mask: str

    def __post_init__(self) -> None:
        if not isinstance(self.mask, str):
            raise TypeError("mask must be a str")
        if not re.fullmatch(r"^[01]+$", self.mask):
            raise ValueError(f"QuantifierMask must contain only binary digits, got {self.mask!r}")

    @property
    def switch_count(self) -> int:
        """Count the number of alternation switches between adjacent bits (per Level 14 paper)."""
        if not self.mask:
            return 0
        switches = 0
        for i in range(1, len(self.mask)):
            if self.mask[i] != self.mask[i - 1]:
                switches += 1
        return switches

    @property
    def switches(self) -> int:
        """Alias for switch_count."""
        return self.switch_count

    @property
    def block_count(self) -> int:
        """Count the number of contiguous quantifier blocks."""
        if not self.mask:
            return 0
        return self.switch_count + 1

    @property
    def alternation_depth(self) -> int:
        """Count the number of contiguous quantifier blocks (alternations + 1)."""
        return self.block_count

    def to_binary_atom(self) -> str:
        """Serialize mask as wire binary atom."""
        return f"<{self.mask}>"

    def is_within_stage_budget(self, stage: StageLevel) -> bool:
        """Check if alternation depth is bounded by stage level ceiling."""
        return self.alternation_depth <= stage.level

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, QuantifierMask)
        return self.mask == other.mask

    def __hash__(self) -> int:
        return hash((type(self), self.mask))

    def __repr__(self) -> str:
        return f"QuantifierMask({self.mask!r}, depth={self.alternation_depth})"
