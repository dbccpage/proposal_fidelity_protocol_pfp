"""Pure domain models for Discrete Manifold Tower Lift Necessity via Finite Exhaustion Search (Prompt 28).

AuthorityEffect: None.
ZERO-FLOAT Law: Discrete relation enumeration and combinatorial proofs; zero floats.
Clean Architecture: Zero outward dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import FrozenSet, Tuple


@dataclass(frozen=True)
class CarrierSet:
    """Discrete manifold carrier set at a specified tower stage."""

    stage: int
    cardinality: int
    elements: Tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.elements) != self.cardinality:
            raise ValueError(
                f"Carrier cardinality mismatch: declared {self.cardinality} != actual {len(self.elements)}"
            )

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (self.stage, self.cardinality, self.elements) == (
            other.stage,
            other.cardinality,
            other.elements,
        )


@dataclass(frozen=True)
class BinaryRelation:
    """Finite binary relation R subset of X x X over a carrier set."""

    pairs: FrozenSet[Tuple[int, int]]

    def is_irreflexive(self, carrier: CarrierSet) -> bool:
        """Returns True if for all x in carrier, (x, x) not in R."""
        return not any((x, x) in self.pairs for x in carrier.elements)

    def has_witnessed_pair(self, carrier: CarrierSet) -> bool:
        """Returns True if there exist distinct x != y such that (x, y) in R."""
        return any(
            (x, y) in self.pairs
            for x in carrier.elements
            for y in carrier.elements
            if x != y
        )

    def has_directed_path_2(self, carrier: CarrierSet) -> bool:
        """Returns True if there exist distinct x != y != z != x such that (x, y) in R and (y, z) in R."""
        return any(
            (x, y) in self.pairs and (y, z) in self.pairs
            for x in carrier.elements
            for y in carrier.elements
            for z in carrier.elements
            if len({x, y, z}) == 3
        )

    def has_directed_cycle_3(self, carrier: CarrierSet) -> bool:
        """Returns True if there exist distinct x != y != z != x such that (x,y), (y,z), (z,x) in R."""
        return any(
            (x, y) in self.pairs and (y, z) in self.pairs and (z, x) in self.pairs
            for x in carrier.elements
            for y in carrier.elements
            for z in carrier.elements
            if len({x, y, z}) == 3
        )

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.pairs == other.pairs


PINNED_EXHAUSTION_DIGESTS: dict[Tuple[int, int, str], str] = {
    (0, 1, "IRREFLEXIVE_WITNESSED_RELATION"): "5357622ee665ea7a9f8460c58bb526234290b499e9a162651a373604c71daa8d",
    (1, 2, "DIRECTED_PATH_COMPOSITION"): "d5d7c90b68bbc386a661aa1faae750ddcd99cf7638a6ed712ce9818635525e76",
    (1, 2, "DIRECTED_CYCLE_THREE"): "183d94c5100decc047ad14b0c71113935926bea96a3a73301456bf2b1a13f2fc",
}


@dataclass(frozen=True)
class LiftExhaustionReceipt:
    """Receipt proving necessity of discrete manifold tower lift via exhaustive search."""

    from_stage: int
    to_stage: int
    goal: str
    total_relations_tested: int
    valid_relations_on_source: int
    target_witness: str
    exhaustion_digest: str
    zero_float_verification: bool = True

    def matches_pinned_digest(self) -> bool:
        key = (self.from_stage, self.to_stage, self.goal)
        expected = PINNED_EXHAUSTION_DIGESTS.get(key)
        return expected is not None and self.exhaustion_digest == expected

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.from_stage,
            self.to_stage,
            self.goal,
            self.total_relations_tested,
            self.valid_relations_on_source,
            self.target_witness,
            self.exhaustion_digest,
            self.zero_float_verification,
        ) == (
            other.from_stage,
            other.to_stage,
            other.goal,
            other.total_relations_tested,
            other.valid_relations_on_source,
            other.target_witness,
            other.exhaustion_digest,
            other.zero_float_verification,
        )
