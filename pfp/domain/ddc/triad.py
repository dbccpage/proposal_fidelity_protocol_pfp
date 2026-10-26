"""Legacy Python DDC triad types with a fail-closed functional boundary.

The canonical Phi1, Gamma2, and Xi calculations are owned by
``omega_engine/crates_rs/omega_functional/src``. The former Python LP,
spanning-forest, closure-norm, and lexicographic-edge implementations have
been retired. In particular, the old Python Xi formula did not match the
conditional density-distance Xi in the Rust functional crate.

These types remain importable for reading historical DDC data. Computation
requires a Rust-backed adapter, which has not yet been wired to this API.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Dict, Optional, Tuple

from .cochains import Cochain0, Cochain1
from .complex import SimplicialComplex


FUNCTIONAL_OWNER = "omega_engine/crates_rs/omega_functional/src"


class FunctionalBoundaryUnavailable(RuntimeError):
    """No Rust-backed adapter is available for a DDC functional request."""

    code = "FUNCTIONAL_BOUNDARY_UNAVAILABLE"

    def __init__(self) -> None:
        super().__init__(
            f"{self.code}: Python DDC cannot calculate Phi1, Gamma2, or Xi; "
            f"{FUNCTIONAL_OWNER} is the sole calculator and no Rust-backed "
            "DDC adapter is wired."
        )


class ObstructionTrichotomy(Enum):
    """Historical DDC classification labels, retained for receipt reading."""

    EXACT_REPAIR = "EXACT_REPAIR"
    STABILIZED_SURVIVOR = "STABILIZED_SURVIVOR"
    OPEN_OBSTRUCTION = "OPEN_OBSTRUCTION"
    REFUSAL = "REFUSAL"


@dataclass(frozen=True)
class Phi1Certificate:
    """Historical certificate data shape; constructing it does not certify it."""

    phi_1: Fraction
    optimal_potential: Cochain0
    residual: Cochain1
    dual_circulation: Cochain1
    duality_gap: Fraction
    is_certified: bool
    details: str
    authority_effect: str = "None"


@dataclass(frozen=True)
class DefectTriad:
    """Historical triad data shape; constructing it does not verify values."""

    phi_1: Fraction
    gamma_2: Fraction
    xi: Fraction
    trichotomy: ObstructionTrichotomy
    phi1_certificate: Phi1Certificate

    @property
    def is_exact_repair(self) -> bool:
        return self.trichotomy == ObstructionTrichotomy.EXACT_REPAIR

    @property
    def is_stabilized_survivor(self) -> bool:
        return self.trichotomy == ObstructionTrichotomy.STABILIZED_SURVIVOR

    @property
    def is_open_obstruction(self) -> bool:
        return self.trichotomy == ObstructionTrichotomy.OPEN_OBSTRUCTION


def compute_phi1(
    complex_: SimplicialComplex,
    x: Cochain1,
    weights: Optional[Dict[Tuple[str, str], Fraction]] = None,
) -> Phi1Certificate:
    """Refuse Python Phi1 computation until a Rust-backed adapter exists."""
    raise FunctionalBoundaryUnavailable()


def compute_gamma2(complex_: SimplicialComplex, h: Cochain1) -> Fraction:
    """Refuse Python Gamma2 computation until a Rust-backed adapter exists."""
    raise FunctionalBoundaryUnavailable()


def compute_xi(complex_: SimplicialComplex, h: Cochain1) -> Fraction:
    """Refuse Python Xi computation until a Rust-backed adapter exists."""
    raise FunctionalBoundaryUnavailable()


def evaluate_defect_triad(
    complex_: SimplicialComplex,
    x: Cochain1,
    weights: Optional[Dict[Tuple[str, str], Fraction]] = None,
) -> DefectTriad:
    """Refuse Python triad evaluation until a Rust-backed adapter exists."""
    raise FunctionalBoundaryUnavailable()
