"""hott.py
=======

Homotopy Type Theory (HoTT) Path Groupoids, Fibrational Transport,
2-Cell Homotopies, and Hallucination Obstructions for Colored Operads.

Mathematical Foundations:
-------------------------
1. Identity Types as Groupoids:
   For a space of code states or morphisms X:
   - Reflexivity: refl(x) : x =_X x
   - Inversion (Symmetry): inv(p) : y =_X x for p : x =_X y
   - Concatenation (Transitivity): concat(p, q) : x =_X z for p : x =_X y, q : y =_X z
   - Groupoid laws (associator, left unitor, right unitor) hold up to 2-cell homotopy.

2. Fibrational Transport:
   Given a predicate / type family P : X -> Type (e.g. an antibody or contract suite),
   transport(p, P, u) lifts evidence u in P(x) along path p : x = y to transport(p, P, u) in P(y).
   If P(y) fails, transport generates a PathObstructionWitness / HallucinationWitness.

3. 2-Cell Homotopies:
   A 2-cell alpha : p => q relates two parallel 1-cell paths p, q : x = y, witnessing
   that both execution trajectories achieve equivalent contract satisfaction.

4. Authority Invariant:
   AuthorityEffect: None. Path equivalence supports local test and antibody survival,
   never global mathematical proof or promotion authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Generic,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
)

try:
    from .coloured_operad import AntiMorphism, Residual, Witness, EMPTY
except (ImportError, ValueError):
    from coloured_operad import AntiMorphism, Residual, Witness, EMPTY


T = TypeVar("T")
U = TypeVar("U")

__all__ = [
    "HallucinationWitness", "Homotopy2Cell", "Path", "PathObstructionWitness",
    "identity_path", "refl", "transport", "transport_along_path",
]


# ---------------------------------------------------------------------------
# Obstruction & Hallucination Witnesses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HallucinationWitness:
    """Witness that kills a claimed path or implementation equivalence."""
    claimed_source: str
    claimed_target: str
    antibody_name: str
    inner_witness: Witness

    def kills(self, candidate: object) -> bool:
        return True

    def describe(self) -> str:
        return (
            f"Hallucination detected by {self.antibody_name}: "
            f"claimed Path({self.claimed_source} ≡ {self.claimed_target}) falsified: "
            f"{self.inner_witness.describe()}"
        )


@dataclass(frozen=True)
class PathObstructionWitness:
    """Witness produced when transport across a path fails to preserve a fibration invariant."""
    path_source: str
    path_target: str
    fibration_name: str
    detail: str

    def kills(self, candidate: object) -> bool:
        return True

    def describe(self) -> str:
        return (
            f"Path obstruction in fibration '{self.fibration_name}' "
            f"along Path({self.path_source} -> {self.path_target}): {self.detail}"
        )


# ---------------------------------------------------------------------------
# 1-Cell: Path (Identity Type in HoTT)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Path(Generic[T]):
    """
    A 1-cell / Path p : source = target in the space of code states or signatures.
    Satisfies 1-groupoid operations: refl, inv, concat.
    """
    source: T
    target: T
    steps: Tuple[str, ...] = ()
    antibodies_passed: Tuple[str, ...] = ()
    witness: Optional[Witness] = None
    residual: Residual = field(default_factory=lambda: EMPTY)

    @property
    def is_valid(self) -> bool:
        return self.witness is None

    def inv(self) -> Path[T]:
        """Invert the path: inv(p) : target = source."""
        inv_steps = tuple(f"inv({s})" for s in reversed(self.steps))
        return Path(
            source=self.target,
            target=self.source,
            steps=inv_steps,
            antibodies_passed=self.antibodies_passed,
            witness=self.witness,
            residual=self.residual,
        )

    def concat(self, other: Path[T]) -> Path[T]:
        """
        Transitive composition of paths (path concatenation):
        If self : x = y and other : y = z, then self.concat(other) : x = z.
        """
        if self.target != other.source and str(self.target) != str(other.source):
            return Path(
                source=self.source,
                target=other.target,
                steps=self.steps + ("MISMATCH_BOUNDARY",) + other.steps,
                antibodies_passed=(),
                witness=PathObstructionWitness(
                    path_source=str(self.source),
                    path_target=str(other.target),
                    fibration_name="EndpointMatching",
                    detail=f"Target endpoint {self.target!r} does not match source endpoint {other.source!r}",
                ),
                residual=self.residual.absorb(other.residual).absorb(
                    Residual(obligations=("path_endpoint_mismatch",), risk=1.0)
                ),
            )

        failing_witness = self.witness or other.witness
        return Path(
            source=self.source,
            target=other.target,
            steps=self.steps + other.steps,
            antibodies_passed=self.antibodies_passed + other.antibodies_passed,
            witness=failing_witness,
            residual=self.residual.absorb(other.residual),
        )

    def __matmul__(self, other: Path[T]) -> Path[T]:
        """Infix operator for path concatenation: p @ q."""
        return self.concat(other)


def refl(x: T) -> Path[T]:
    """Identity path (Reflexivity): refl(x) : x = x."""
    return Path(
        source=x,
        target=x,
        steps=(f"refl({x})",),
        antibodies_passed=(),
        witness=None,
        residual=EMPTY,
    )


def identity_path(candidate: T) -> Path[T]:
    """Alias for refl(candidate)."""
    return refl(candidate)


# ---------------------------------------------------------------------------
# Fibrational Transport
# ---------------------------------------------------------------------------

def transport_along_path(
    path: Path[T],
    predicate_fibration: Callable[[T], Tuple[bool, Optional[Witness]]],
    fibration_name: str = "InvariantFibration",
) -> Tuple[bool, Optional[Witness], Residual]:
    """
    Transports an invariant property across path p : source = target.
    Verifies that the target satisfies the invariant predicate.
    """
    if not path.is_valid:
        return False, path.witness, path.residual

    ok, witness = predicate_fibration(path.target)
    if not ok:
        obstr = PathObstructionWitness(
            path_source=str(path.source),
            path_target=str(path.target),
            fibration_name=fibration_name,
            detail=witness.describe() if witness else "Invariant failed at target",
        )
        return False, obstr, path.residual.absorb(Residual(obligations=(obstr.describe(),), risk=1.0))

    return True, None, path.residual


def transport(
    candidate: T,
    battery: Sequence[AntiMorphism],
    source_reference: Optional[T] = None,
    context: object = None,
) -> Path[T]:
    """
    Transports candidate along the antibody battery.
    If any antibody kills the candidate, produces a Path with a distinguishing HallucinationWitness.
    Otherwise produces a valid Path with accumulated survival residual.
    """
    passed: List[str] = []
    current_residual = EMPTY

    for antibody in battery:
        witness, r = antibody.apply(candidate, context)
        current_residual = current_residual.absorb(r)
        if witness is not None:
            # Falsified path
            hw = HallucinationWitness(
                claimed_source=str(source_reference) if source_reference is not None else "contract",
                claimed_target=str(candidate),
                antibody_name=antibody.name,
                inner_witness=witness,
            )
            return Path(
                source=source_reference if source_reference is not None else candidate,
                target=candidate,
                steps=("transport", f"killed_by_{antibody.name}"),
                antibodies_passed=tuple(passed),
                witness=hw,
                residual=current_residual,
            )
        passed.append(antibody.name)

    return Path(
        source=source_reference if source_reference is not None else candidate,
        target=candidate,
        steps=("transport", "all_antibodies_passed"),
        antibodies_passed=tuple(passed),
        witness=None,
        residual=current_residual,
    )


# ---------------------------------------------------------------------------
# 2-Cells: Homotopies between Paths
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Homotopy2Cell(Generic[T]):
    """
    A 2-cell alpha : p => q between two parallel 1-cells p, q : source = target.
    Witnesses that path p and path q are homotopic (both valid and agree on boundary).
    """
    name: str
    source_path: Path[T]
    target_path: Path[T]
    residual: Residual = field(default_factory=lambda: EMPTY)

    def __post_init__(self) -> None:
        if self.source_path.source != self.target_path.source or self.source_path.target != self.target_path.target:
            raise ValueError(
                f"Boundary mismatch for 2-cell {self.name!r}: "
                f"p: {self.source_path.source} -> {self.source_path.target} vs "
                f"q: {self.target_path.source} -> {self.target_path.target}"
            )

    @property
    def is_valid(self) -> bool:
        return self.source_path.is_valid and self.target_path.is_valid

    def compose_vertical(self, other: Homotopy2Cell[T]) -> Homotopy2Cell[T]:
        """
        Vertical composition of 2-cells:
        If self : p => q and other : q => r, then self.compose_vertical(other) : p => r.
        """
        if self.target_path != other.source_path:
            raise ValueError("Vertical composition target-source path mismatch")
        return Homotopy2Cell(
            name=f"({other.name} ∘_v {self.name})",
            source_path=self.source_path,
            target_path=other.target_path,
            residual=self.residual.absorb(other.residual),
        )

    def compose_horizontal(self, other: Homotopy2Cell[T]) -> Homotopy2Cell[T]:
        """
        Horizontal composition (whisker / tensor) of 2-cells:
        If self : p1 => q1 and other : p2 => q2 with p1.target == p2.source,
        then self.compose_horizontal(other) : (p1 @ p2) => (q1 @ q2).
        """
        p_comp = self.source_path.concat(other.source_path)
        q_comp = self.target_path.concat(other.target_path)
        return Homotopy2Cell(
            name=f"({self.name} ∘_h {other.name})",
            source_path=p_comp,
            target_path=q_comp,
            residual=self.residual.absorb(other.residual),
        )
