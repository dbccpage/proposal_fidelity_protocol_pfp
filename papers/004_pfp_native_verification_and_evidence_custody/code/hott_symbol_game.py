"""
Homotopy Type Theory (HoTT) Identity Types and Primitive Difference Kernel for Paper 032.

This module formalizes:
1. Intensional identity types a =_A b and constructive path operations (refl, sym, trans, ap).
2. The nullary Primitive Difference delta : A -> A -> B with Zero predicate and Residual Quotient.
3. Contrast between constructive HoTT path equivalence and continuous embedding cancellation laundering.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, Optional, TypeVar

T = TypeVar("T")
U = TypeVar("U")
CarrierT = TypeVar("CarrierT")
DiffT = TypeVar("DiffT")


@dataclass(frozen=True)
class IdentityPath(Generic[T]):
    """Intensional Identity Path p : source_a =_type_A target_b in HoTT."""
    type_name: str
    source_a: T
    target_b: T
    is_refl: bool = False
    witness: Optional[str] = None

    def __post_init__(self) -> None:
        if self.is_refl and self.source_a != self.target_b:
            raise ValueError(f"Reflexivity path requires equal endpoints: {self.source_a!r} != {self.target_b!r}")


def refl(type_name: str, a: T) -> IdentityPath[T]:
    """Reflexivity path refl_a : a =_A a."""
    return IdentityPath(type_name=type_name, source_a=a, target_b=a, is_refl=True, witness=f"refl_{a}")


def sym(p: IdentityPath[T]) -> IdentityPath[T]:
    """Symmetry (path inversion) p^{-1} : b =_A a."""
    return IdentityPath(
        type_name=p.type_name,
        source_a=p.target_b,
        target_b=p.source_a,
        is_refl=p.is_refl,
        witness=f"sym({p.witness})" if p.witness else None,
    )


def trans(p: IdentityPath[T], q: IdentityPath[T]) -> IdentityPath[T]:
    """Transitivity (path concatenation) p * q : a =_A c."""
    if p.type_name != q.type_name:
        raise TypeError(f"Type mismatch in path composition: {p.type_name} != {q.type_name}")
    if p.target_b != q.source_a:
        raise ValueError(f"Path composition endpoint mismatch: {p.target_b!r} != {q.source_a!r}")
    return IdentityPath(
        type_name=p.type_name,
        source_a=p.source_a,
        target_b=q.target_b,
        is_refl=p.is_refl and q.is_refl,
        witness=f"trans({p.witness}, {q.witness})" if (p.witness and q.witness) else None,
    )


def ap(f: Callable[[T], U], p: IdentityPath[T], target_type_name: str) -> IdentityPath[U]:
    """Application of function to path (action on paths): ap_f(p) : f(a) =_B f(b)."""
    fa = f(p.source_a)
    fb = f(p.target_b)
    return IdentityPath(
        type_name=target_type_name,
        source_a=fa,
        target_b=fb,
        is_refl=p.is_refl and (fa == fb),
        witness=f"ap({f.__name__ if hasattr(f, '__name__') else 'f'}, {p.witness})" if p.witness else None,
    )


class PrimitiveDifference(Generic[CarrierT, DiffT]):
    """
    The nullary Primitive Difference delta : A -> A -> B with Zero predicate.
    ZeroRel x y := Zero(delta x y).
    """

    def __init__(
        self,
        carrier_type: str,
        delta_func: Callable[[CarrierT, CarrierT], DiffT],
        zero_pred: Callable[[DiffT], bool],
    ):
        self.carrier_type = carrier_type
        self.delta_func = delta_func
        self.zero_pred = zero_pred

    def delta(self, x: CarrierT, y: CarrierT) -> DiffT:
        """Computes difference between two elements of the carrier."""
        return self.delta_func(x, y)

    def zero(self, d: DiffT) -> bool:
        """Determines if a difference value counts as zero difference."""
        return self.zero_pred(d)

    def zero_rel(self, x: CarrierT, y: CarrierT) -> bool:
        """Equivalence relation: ZeroRel x y := Zero(delta x y)."""
        return self.zero(self.delta(x, y))

    def certificate_of_identity(self, x: CarrierT, y: CarrierT) -> Optional[IdentityPath[CarrierT]]:
        """
        If ZeroRel x y holds, constructs an IdentityPath in the residual quotient.
        Otherwise returns None (obstruction persists).
        """
        if self.zero_rel(x, y):
            return IdentityPath(
                type_name=f"Quotient({self.carrier_type})",
                source_a=x,
                target_b=y,
                is_refl=(x == y),
                witness=f"zero_diff_witness({x!r}, {y!r})",
            )
        return None


class ContinuousCancellationDetector:
    """
    Analyzes whether continuous latent vectors create cancellation laundering,
    and contrasts that with discrete HoTT path obstructions.
    """

    @staticmethod
    def is_cancellation_laundering(
        v1: list[float],
        v2: list[float],
        alpha1: float = 0.5,
        alpha2: float = 0.5,
        threshold: float = 1e-4,
    ) -> dict[str, Any]:
        """
        Checks if opposing vectors v1, v2 cancel under convex combination
        alpha1 * v1 + alpha2 * v2, masking a contradiction.
        """
        if len(v1) != len(v2):
            raise ValueError("Vectors must have identical dimensions.")

        mixed = [alpha1 * x1 + alpha2 * x2 for x1, x2 in zip(v1, v2)]
        norm_sq = sum(m * m for m in mixed)
        norm = norm_sq ** 0.5
        norm_v1 = (sum(x * x for x in v1)) ** 0.5
        norm_v2 = (sum(x * x for x in v2)) ** 0.5

        is_laundering = (norm < threshold) and (norm_v1 > threshold) and (norm_v2 > threshold)

        return {
            "is_laundering": is_laundering,
            "mixed_norm": norm,
            "v1_norm": norm_v1,
            "v2_norm": norm_v2,
            "hott_path_exists": False,  # Constructive identity path REFUSED
            "refusal_reason": (
                "Continuous cancellation laundering detected: convex combination "
                "vanishes in R^d without a discrete HoTT identity certificate."
                if is_laundering
                else None
            ),
        }
