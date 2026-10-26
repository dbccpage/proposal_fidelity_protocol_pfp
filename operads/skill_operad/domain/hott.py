"""Homotopy Type Theory (HoTT) Path Groupoids, Fibrational Transport, and 2-Cell Homotopies.

AuthorityEffect: None.
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

from .antibodies import AntiMorphism
from .evidence import (
    HallucinationWitness,
    PathObstructionWitness,
    Residual,
    Witness,
    EMPTY,
)

T = TypeVar("T")


@dataclass(frozen=True)
class Path(Generic[T]):
    """A 1-cell / Path p : source = target in the space of code states or signatures."""
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
        return self.concat(other)


def refl(x: T) -> Path[T]:
    return Path(
        source=x,
        target=x,
        steps=(f"refl({x})",),
        antibodies_passed=(),
        witness=None,
        residual=EMPTY,
    )


def identity_path(candidate: T) -> Path[T]:
    return refl(candidate)


def transport_along_path(
    path: Path[T],
    predicate_fibration: Callable[[T], Tuple[bool, Optional[Witness]]],
    fibration_name: str = "InvariantFibration",
) -> Tuple[bool, Optional[Witness], Residual]:
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
    passed: List[str] = []
    current_residual = EMPTY

    for antibody in battery:
        witness, r = antibody.apply(candidate, context)
        current_residual = current_residual.absorb(r)
        if witness is not None:
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


@dataclass(frozen=True)
class Homotopy2Cell(Generic[T]):
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
        if self.target_path != other.source_path:
            raise ValueError("Vertical composition target-source path mismatch")
        return Homotopy2Cell(
            name=f"({other.name} \u2218_v {self.name})",
            source_path=self.source_path,
            target_path=other.target_path,
            residual=self.residual.absorb(other.residual),
        )

    def compose_horizontal(self, other: Homotopy2Cell[T]) -> Homotopy2Cell[T]:
        p_comp = self.source_path.concat(other.source_path)
        q_comp = self.target_path.concat(other.target_path)
        return Homotopy2Cell(
            name=f"({self.name} \u2218_h {other.name})",
            source_path=p_comp,
            target_path=q_comp,
            residual=self.residual.absorb(other.residual),
        )
