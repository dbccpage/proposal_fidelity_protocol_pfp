"""TokenFrontier entity and exact Bayes probability renormalization in Fraction.

Zero outward dependencies. Zero-Float Law strictly enforced.
AuthorityEffect: None.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence, Union

from pfp.domain.mssn_research.shared_kernel.result import Failure, Result, Success, err, ok
from .errors import (
    DecodingError,
    DecodingRefusalCode,
    RefusedZeroRetainedMassError,
    ZeroFloatViolationError,
)
from .vocabulary import RetainedProbabilityMass, WireVocabulary


@dataclass(frozen=True)
class FrontierCandidate:
    """An admissible token candidate on the decoding frontier."""

    token_id: int
    token: str
    base_probability: Fraction
    constrained_probability: Fraction
    parser_state: str = "active"

    def __post_init__(self) -> None:
        if isinstance(self.base_probability, float) or isinstance(self.constrained_probability, float):
            raise ZeroFloatViolationError("FrontierCandidate probabilities must be Fraction, float forbidden")
        if not isinstance(self.base_probability, Fraction):
            if isinstance(self.base_probability, int):
                object.__setattr__(self, "base_probability", Fraction(self.base_probability, 1))
            else:
                raise TypeError(f"base_probability must be Fraction, got {type(self.base_probability)}")
        if not isinstance(self.constrained_probability, Fraction):
            if isinstance(self.constrained_probability, int):
                object.__setattr__(self, "constrained_probability", Fraction(self.constrained_probability, 1))
            else:
                raise TypeError(f"constrained_probability must be Fraction, got {type(self.constrained_probability)}")

        if not (Fraction(0, 1) <= self.base_probability <= Fraction(1, 1)):
            raise ValueError(f"base_probability must be in [0, 1], got {self.base_probability}")
        if not (Fraction(0, 1) <= self.constrained_probability <= Fraction(1, 1)):
            raise ValueError(f"constrained_probability must be in [0, 1], got {self.constrained_probability}")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, FrontierCandidate)
        return (
            self.token_id == other.token_id
            and self.token == other.token
            and self.base_probability == other.base_probability
            and self.constrained_probability == other.constrained_probability
            and self.parser_state == other.parser_state
        )

    def __hash__(self) -> int:
        return hash((type(self), self.token_id, self.token, self.base_probability, self.constrained_probability, self.parser_state))


@dataclass(frozen=True)
class TokenFrontier:
    """Exact Bayesian conditioned token frontier with support masking."""

    vocabulary: WireVocabulary
    support_width: int
    masked_token_count: int
    retained_mass: RetainedProbabilityMass
    candidates: tuple[FrontierCandidate, ...]
    inadmissible_tokens: tuple[int, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.candidates, tuple):
            object.__setattr__(self, "candidates", tuple(self.candidates))
        if not isinstance(self.inadmissible_tokens, tuple):
            object.__setattr__(self, "inadmissible_tokens", tuple(self.inadmissible_tokens))

    @classmethod
    def compute_retained_mass(
        cls,
        vocab: WireVocabulary,
        base_weights: Sequence[Union[int, Fraction]],
        admitted_token_ids: Sequence[int],
    ) -> RetainedProbabilityMass:
        """Compute the retained probability mass under the admitted token support.

        Raises:
            DecodingError: If base_weights length != vocab size or total weight <= 0.
            ZeroFloatViolationError: If any weight is float (TypeError).
            RefusedZeroRetainedMassError: If admitted support is empty or retained mass is 0/1.
        """
        V = vocab.size
        if len(base_weights) != V:
            raise DecodingError(
                f"Base weights count ({len(base_weights)}) != vocabulary size ({V})",
                code=DecodingRefusalCode.WRONG_ARITY,
            )

        # Check for float violation
        for w in base_weights:
            if isinstance(w, float):
                raise ZeroFloatViolationError("Float weight encountered in base_weights; ZERO-FLOAT law requires int or Fraction")

        # Convert weights to Fractions
        frac_weights: list[Fraction] = []
        for w in base_weights:
            if isinstance(w, int):
                frac_weights.append(Fraction(w, 1))
            elif isinstance(w, Fraction):
                frac_weights.append(w)
            else:
                raise TypeError(f"Invalid weight type {type(w)}")

        total_weight = sum(frac_weights)
        if total_weight <= Fraction(0, 1):
            raise DecodingError(
                "Total probability weight must be strictly positive",
                code=DecodingRefusalCode.INCONSISTENT_PROBABILITY,
            )

        cand_indices = sorted(set(admitted_token_ids))
        if not cand_indices:
            raise RefusedZeroRetainedMassError(
                "Retained probability mass dropped to zero: empty support carrier S_t = empty"
            )

        p_base = [w / total_weight for w in frac_weights]
        retained_sum = sum(p_base[i] for i in cand_indices)
        if retained_sum == Fraction(0, 1):
            raise RefusedZeroRetainedMassError(
                "Retained probability mass is 0/1: all admitted tokens carry zero base probability"
            )

        return RetainedProbabilityMass(retained_sum)

    @classmethod
    def condition_probabilities(
        cls,
        vocab: WireVocabulary,
        base_weights: Sequence[Union[int, Fraction]],
        admitted_token_ids: Sequence[int],
        parser_state: str = "active",
    ) -> Sequence[FrontierCandidate]:
        """Compute conditioned probabilities over admitted support.

        Renormalizes base probabilities by dividing by the retained probability mass.
        """
        retained_mass = cls.compute_retained_mass(vocab, base_weights, admitted_token_ids)
        retained_sum = retained_mass.mass

        frac_weights: list[Fraction] = [
            Fraction(w, 1) if isinstance(w, int) else w for w in base_weights  # type: ignore
        ]
        total_weight = sum(frac_weights)
        p_base = [w / total_weight for w in frac_weights]

        cand_indices = sorted(set(admitted_token_ids))
        candidates: list[FrontierCandidate] = []
        for idx in cand_indices:
            p_c = p_base[idx] / retained_sum
            candidates.append(FrontierCandidate(
                token_id=idx,
                token=vocab.id_to_token(idx),
                base_probability=p_base[idx],
                constrained_probability=p_c,
                parser_state=parser_state,
            ))

        constrained_sum = sum(c.constrained_probability for c in candidates)
        if constrained_sum != Fraction(1, 1):
            raise DecodingError(
                f"Constrained probability sum drift: expected 1/1, got {constrained_sum}",
                code=DecodingRefusalCode.INCONSISTENT_PROBABILITY,
            )

        return tuple(candidates)

    @classmethod
    def evaluate_step(
        cls,
        vocabulary: WireVocabulary,
        base_weights: Sequence[int | Fraction | float],
        admitted_indices: Sequence[int],
        parser_state: str = "active",
    ) -> TokenFrontier:
        """Evaluate a decoding step with exact Bayes renormalization.

        Raises:
            ZeroFloatViolationError: If any weight is float.
            RefusedZeroRetainedMassError: If admitted support is empty or retained mass is 0/1.
            DecodingError: If arity or indexing is invalid.
        """
        retained_mass = cls.compute_retained_mass(vocabulary, base_weights, admitted_indices)  # type: ignore
        candidates = cls.condition_probabilities(
            vocabulary, base_weights, admitted_indices, parser_state=parser_state  # type: ignore
        )
        admitted_set = set(admitted_indices)
        inadmissible = [i for i in range(vocabulary.size) if i not in admitted_set]

        return cls(
            vocabulary=vocabulary,
            support_width=len(candidates),
            masked_token_count=len(inadmissible),
            retained_mass=retained_mass,
            candidates=tuple(candidates),
            inadmissible_tokens=tuple(inadmissible),
        )

    @classmethod
    def evaluate_step_result(
        cls,
        vocabulary: WireVocabulary,
        base_weights: Sequence[int | Fraction | float],
        admitted_indices: Sequence[int],
        parser_state: str = "active",
    ) -> Result[TokenFrontier, DecodingError]:
        """ROP Result envelope for step evaluation."""
        try:
            frontier = cls.evaluate_step(
                vocabulary=vocabulary,
                base_weights=base_weights,
                admitted_indices=admitted_indices,
                parser_state=parser_state,
            )
            return ok(frontier)
        except DecodingError as exc:
            return err(exc)

    def get_constrained_probability(self, token_id: int) -> Fraction:
        """Returns the constrained probability for token_id; inadmissible tokens receive Fraction(0, 1)."""
        for cand in self.candidates:
            if cand.token_id == token_id:
                return cand.constrained_probability
        return Fraction(0, 1)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, TokenFrontier)
        return (
            self.vocabulary == other.vocabulary
            and self.support_width == other.support_width
            and self.masked_token_count == other.masked_token_count
            and self.retained_mass == other.retained_mass
            and self.candidates == other.candidates
            and self.inadmissible_tokens == other.inadmissible_tokens
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.vocabulary,
            self.support_width,
            self.masked_token_count,
            self.retained_mass,
            self.candidates,
            self.inadmissible_tokens,
        ))


__all__ = [
    "FrontierCandidate",
    "TokenFrontier",
]
