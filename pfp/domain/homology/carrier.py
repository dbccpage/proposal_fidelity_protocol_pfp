"""Pure carrier sets, proto-support obligations, and discrete cell bounds.

Zero host I/O, zero external framework imports.
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ProtoSupport:
    """Pre-carrier ontological support obligations defining whether difference is typeable."""

    has_support: bool = True
    has_addressability: bool = True
    has_distinguishability: bool = True
    has_orientation: bool = True
    has_boundary_capacity: bool = True
    has_witnessability: bool = True
    has_markability: bool = True

    def __post_init__(self) -> None:
        if any(type(value) is not bool for value in vars(self).values()):
            raise TypeError("ProtoSupport declarations must be booleans")

    def is_fully_supported(self) -> bool:
        return (
            self.has_support
            and self.has_addressability
            and self.has_distinguishability
            and self.has_orientation
            and self.has_boundary_capacity
            and self.has_witnessability
            and self.has_markability
        )


@dataclass(frozen=True)
class Edge:
    """Directed edge between integer vertex indices."""

    src: int
    tgt: int

    def __post_init__(self) -> None:
        if type(self.src) is not int or type(self.tgt) is not int:
            raise TypeError("Edge vertices must be integers")


@dataclass(frozen=True)
class StaticCellBounds:
    """Rigid static cell bounds ensuring finite memory and time budgets."""

    max_vertices: int = 1024
    max_edges: int = 4096
    max_cells: int = 16384
    max_budget: int = 65536

    def check_bounds(self, num_vertices: int, num_edges: int, num_cells: int = 0) -> bool:
        return (
            num_vertices <= self.max_vertices
            and num_edges <= self.max_edges
            and num_cells <= self.max_cells
        )


@dataclass(frozen=True)
class Carrier:
    """Finite discrete simplicial carrier state."""

    vertices: Tuple[int, ...]
    edges: Tuple[Edge, ...]
    support: ProtoSupport = ProtoSupport()
    bounds: StaticCellBounds = StaticCellBounds()

    def __post_init__(self) -> None:
        if not self.bounds.check_bounds(len(self.vertices), len(self.edges)):
            raise ValueError("Carrier exceeds static cell bounds")
        v_set = set(self.vertices)
        for e in self.edges:
            if e.src not in v_set or e.tgt not in v_set:
                raise ValueError(f"Edge ({e.src}, {e.tgt}) references vertex outside carrier")
