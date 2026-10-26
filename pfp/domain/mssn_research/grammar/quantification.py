"""Value Objects for the Grammar Bounded Context.

Enforces:
- Exact-Type Equality (RULE_VO_EXACT_TYPE_EQUALITY_001)
- Immutability and Pure Python language types
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from omega_engine_pfp.domain.mssn_research.shared_kernel.value_objects import (
    Rational,
)

from .exact_structures import ExactRationalMatrix


class QuantifierKind(int, Enum):
    """Polarity of bounded quantifier."""
    UNIVERSAL = 0    # <0>: Bounded forall (forall x < B)
    EXISTENTIAL = 1  # <1>: Bounded exists (exists x < B)

    def to_wire_atom(self) -> str:
        return f"<{self.value}>"


@dataclass(frozen=True)
class BoundedVarDecl:
    """Bounded variable declaration with explicit finite bound limit."""
    var_id: str
    bound_limit: int

    def __post_init__(self) -> None:
        if not isinstance(self.var_id, str) or not self.var_id:
            raise ValueError("var_id must be a non-empty string")
        if not isinstance(self.bound_limit, int) or isinstance(self.bound_limit, bool) or self.bound_limit <= 0:
            raise ValueError(f"bound_limit must be a positive integer, got {self.bound_limit}")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, BoundedVarDecl)
        return self.var_id == other.var_id and self.bound_limit == other.bound_limit

    def __hash__(self) -> int:
        return hash((type(self), self.var_id, self.bound_limit))


@dataclass(frozen=True)
class QuantifierPolarityMask:
    """Ordered sequence of bounded quantifier kinds from outermost to innermost."""
    kinds: tuple[QuantifierKind, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.kinds, tuple):
            object.__setattr__(self, "kinds", tuple(self.kinds))

    @property
    def alternation_count(self) -> int:
        """Count switches between universal and existential quantifiers."""
        if len(self.kinds) <= 1:
            return 0
        switches = 0
        for i in range(1, len(self.kinds)):
            if self.kinds[i] != self.kinds[i - 1]:
                switches += 1
        return switches

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, QuantifierPolarityMask)
        return self.kinds == other.kinds

    def __hash__(self) -> int:
        return hash((type(self), self.kinds))


@dataclass(frozen=True)
class BoundedAlternationBlock:
    """Level 14: Bounded quantifier alternation evaluation block."""
    alternation_count: int
    polarity_mask: QuantifierPolarityMask
    bounded_vars: tuple[BoundedVarDecl, ...]
    step_budget: int
    total_confluence_proof: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.alternation_count, int) or isinstance(self.alternation_count, bool) or self.alternation_count < 0:
            raise ValueError("alternation_count must be non-negative integer")
        if not isinstance(self.polarity_mask, QuantifierPolarityMask):
            raise TypeError("polarity_mask must be QuantifierPolarityMask")
        if not isinstance(self.bounded_vars, tuple):
            object.__setattr__(self, "bounded_vars", tuple(self.bounded_vars))
        if not isinstance(self.step_budget, int) or isinstance(self.step_budget, bool) or self.step_budget <= 0:
            raise ValueError("step_budget must be a positive integer")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, BoundedAlternationBlock)
        return (
            self.alternation_count == other.alternation_count
            and self.polarity_mask == other.polarity_mask
            and self.bounded_vars == other.bounded_vars
            and self.step_budget == other.step_budget
            and self.total_confluence_proof == other.total_confluence_proof
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.alternation_count,
            self.polarity_mask,
            self.bounded_vars,
            self.step_budget,
            self.total_confluence_proof,
        ))


@dataclass(frozen=True)
class ExactBianchiComplex4D:
    """Higher-degree chain/cochain complex up to degree 4.

    C^4 <--d3-- C^3 <--d2-- C^2 <--d1-- C^1 <--d0-- C^0
    """
    d2: ExactRationalMatrix
    d3: ExactRationalMatrix
    d0: Optional[ExactRationalMatrix] = None
    d1: Optional[ExactRationalMatrix] = None

    def __post_init__(self) -> None:
        if not isinstance(self.d2, ExactRationalMatrix) or not isinstance(self.d3, ExactRationalMatrix):
            raise TypeError("d2 and d3 must be ExactRationalMatrix")
        if self.d0 is not None and not isinstance(self.d0, ExactRationalMatrix):
            raise TypeError("d0 must be ExactRationalMatrix")
        if self.d1 is not None and not isinstance(self.d1, ExactRationalMatrix):
            raise TypeError("d1 must be ExactRationalMatrix")

    def check_bianchi_nilpotence(self) -> bool:
        """Check discrete Bianchi coboundary nilpotence: d3 ∘ d2 = 0."""
        if self.d3.cols != self.d2.rows:
            return False
        comp = self.d3.multiply(self.d2)
        if not comp.is_zero():
            return False
        if self.d1 is not None:
            if self.d2.cols != self.d1.rows:
                return False
            comp21 = self.d2.multiply(self.d1)
            if not comp21.is_zero():
                return False
        if self.d0 is not None and self.d1 is not None:
            if self.d1.cols != self.d0.rows:
                return False
            comp10 = self.d1.multiply(self.d0)
            if not comp10.is_zero():
                return False
        return True

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ExactBianchiComplex4D)
        return (
            self.d0 == other.d0
            and self.d1 == other.d1
            and self.d2 == other.d2
            and self.d3 == other.d3
        )

    def __hash__(self) -> int:
        return hash((type(self), self.d0, self.d1, self.d2, self.d3))


@dataclass(frozen=True)
class ExactPhi4Certificate:
    """Exact rational LP weak duality certificate for degree-4 cavity cochains (Phi_4).

    Mirrors omega_engine/crates_rs/omega_functional/src/phi4.rs.
    """
    flux_g: tuple[Rational, ...]
    complex: ExactBianchiComplex4D
    weights: tuple[Rational, ...]
    potential_c: tuple[Rational, ...]
    primal_residual: tuple[Rational, ...]
    dual_witness: tuple[Rational, ...]
    reported_value: Rational

    def __post_init__(self) -> None:
        if not isinstance(self.flux_g, tuple):
            object.__setattr__(self, "flux_g", tuple(self.flux_g))
        if not isinstance(self.complex, ExactBianchiComplex4D):
            raise TypeError("complex must be ExactBianchiComplex4D")
        if not isinstance(self.weights, tuple):
            object.__setattr__(self, "weights", tuple(self.weights))
        if not isinstance(self.potential_c, tuple):
            object.__setattr__(self, "potential_c", tuple(self.potential_c))
        if not isinstance(self.primal_residual, tuple):
            object.__setattr__(self, "primal_residual", tuple(self.primal_residual))
        if not isinstance(self.dual_witness, tuple):
            object.__setattr__(self, "dual_witness", tuple(self.dual_witness))
        if not isinstance(self.reported_value, Rational):
            raise TypeError("reported_value must be Rational")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ExactPhi4Certificate)
        return (
            self.flux_g == other.flux_g
            and self.complex == other.complex
            and self.weights == other.weights
            and self.potential_c == other.potential_c
            and self.primal_residual == other.primal_residual
            and self.dual_witness == other.dual_witness
            and self.reported_value == other.reported_value
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.flux_g,
            self.complex,
            self.weights,
            self.potential_c,
            self.primal_residual,
            self.dual_witness,
            self.reported_value,
        ))
