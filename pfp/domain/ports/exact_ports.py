"""Domain protocols for exact arithmetic, linear algebra, and digest operations.

Enforces Clean Architecture inward dependency by defining domain ports that can
be backed either by pure Python domain kernels or native Rust crates (engine/crates_rs).

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol, runtime_checkable

from fractions import Fraction

from ..exact.poly import Poly
from ..exact.q import Q
from ..value_objects.functional_receipt import FunctionalReceipt

Matrix = Sequence[Sequence[Q]]


@runtime_checkable
class ExactLinearAlgebraPort(Protocol):
    """Protocol for exact linear algebra operations over Q."""

    def determinant(self, matrix: Matrix) -> Q: ...

    def characteristic_polynomial(self, matrix: Matrix) -> Poly: ...

    def rank(self, matrix: Matrix) -> int: ...

    def is_positive_definite(self, matrix: Matrix) -> bool: ...

    def leading_minors(self, matrix: Matrix) -> tuple[Q, ...]: ...


@runtime_checkable
class ExactHomologyPort(Protocol):
    """Protocol for simplicial complexes, chain complexes, and homology (core_homology)."""

    def compute_betti_numbers(self, complex_descriptor: object) -> list[int]: ...

    def verify_boundary_law(self, complex_descriptor: object) -> bool: ...

    def verify_boundary_closed(self, faces: Sequence[Sequence[tuple[int, int, int]]]) -> bool: ...

    def verify_simplicial_boundary_law(
        self, simplices: Sequence[Sequence[int]]
    ) -> Mapping[str, Any]: ...


@runtime_checkable
class ExactHolonomyPort(Protocol):
    """Protocol for discrete connection, holonomy, and curvature (core_holonomy)."""

    def path_holonomy(self, connection: object, path: Sequence[str]) -> object: ...

    def loop_curvature(self, connection: object, loop: Sequence[str]) -> object: ...

    def ordered_loop_product(
        self,
        tables: Sequence[Sequence[Sequence[Q]]],
        word: Sequence[tuple[int, bool]],
    ) -> Sequence[Sequence[Q]]: ...

    def is_ordered_closure(
        self,
        tables: Sequence[Sequence[Sequence[Q]]],
        word: Sequence[tuple[int, bool]],
    ) -> bool: ...


@runtime_checkable
class ExactFunctionalPort(Protocol):
    """Protocol for defect functionals Phi_1, Gamma_2, and Xi (core_functional)."""

    def evaluate(
        self,
        d0: Sequence[Sequence[Fraction]],
        d1: Sequence[Sequence[Fraction]],
        residual: Sequence[Fraction],
    ) -> FunctionalReceipt:
        """Phi1, Gamma2 and the diagnostic class of ``residual`` over ``d1 d0 = 0``."""
        ...

    def verify_phi1_certificate(self, certificate: object) -> bool: ...

    def verify_gamma2_certificate(self, certificate: object) -> bool: ...


@runtime_checkable
class ExactPharmacyPort(Protocol):
    """Protocol for pharmacy defect and failure-class detection (core_prompt_civilization)."""

    def pharmacy_detect(
        self, candidate_json: str, context: str = ""
    ) -> Mapping[str, Any]:
        """Runs the 12 failure-class detector battery on a candidate turn."""
        ...


@runtime_checkable
class ExactDigestPort(Protocol):
    """Protocol for deterministic content-addressed JSON serialization and hashing."""

    def canonical_json(self, value: object) -> bytes: ...

    def sha256(self, data: bytes) -> bytes: ...

    def digest_of(self, value: object) -> bytes: ...


@runtime_checkable
class RetractionEnginePort(Protocol):
    """Protocol for retraction turn and loop descent validation (core_symbol_game::epics)."""

    def retraction_turn(
        self,
        before: Mapping[str, int],
        after: Mapping[str, int],
        candidate: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        """Verify retraction turn candidate descent."""
        ...

    def retraction_loop(
        self,
        intake: Mapping[str, int],
        candidates: Sequence[Mapping[str, Any]],
        open_obligations: int = 0,
    ) -> Mapping[str, Any]:
        """Verify multi-turn retraction loop."""
        ...


_GLOBAL_RETRACTION_PORT: RetractionEnginePort | None = None


def set_retraction_port(port: RetractionEnginePort | None) -> None:
    """Register the active retraction engine adapter at composition root."""
    global _GLOBAL_RETRACTION_PORT
    _GLOBAL_RETRACTION_PORT = port


def get_retraction_port() -> RetractionEnginePort | None:
    """Retrieve the registered retraction engine port, falling back to homology port if compatible."""
    if _GLOBAL_RETRACTION_PORT is not None:
        return _GLOBAL_RETRACTION_PORT
    try:
        from ..solvers.kinds import get_homology_port

        hom_port = get_homology_port()
        if hom_port is not None and hasattr(hom_port, "retraction_turn"):
            return hom_port  # type: ignore[return-value]
    except Exception:
        pass
    return None


__all__ = [
    "ExactDigestPort",
    "ExactFunctionalPort",
    "ExactHolonomyPort",
    "ExactHomologyPort",
    "ExactLinearAlgebraPort",
    "ExactPharmacyPort",
    "RetractionEnginePort",
    "get_retraction_port",
    "set_retraction_port",
]
