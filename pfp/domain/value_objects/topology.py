"""Strongly typed Domain Topology and Spatial Value Objects.

AuthorityEffect: None.
Eliminates primitive obsession for simplicial vertices, edges, spans, and matrix shapes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .base import ValueObject


def _require_non_negative_int(name: str, value: Any) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be a strict int, got {type(value).__name__}")
    if value < 0:
        raise ValueError(f"{name} must be non-negative, got {value}")
    return value


@dataclass(frozen=True)
class VertexId(ValueObject):
    """Discrete simplicial vertex index."""

    value: int

    def __post_init__(self) -> None:
        _require_non_negative_int("VertexId", self.value)

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True)
class EdgeVO(ValueObject):
    """Directed edge between two simplicial vertices."""

    src: VertexId
    tgt: VertexId

    def __post_init__(self) -> None:
        if type(self.src) is int:
            object.__setattr__(self, "src", VertexId(self.src))
        elif type(self.src) is not VertexId:
            raise TypeError(f"EdgeVO.src must be VertexId or int, got {type(self.src).__name__}")

        if type(self.tgt) is int:
            object.__setattr__(self, "tgt", VertexId(self.tgt))
        elif type(self.tgt) is not VertexId:
            raise TypeError(f"EdgeVO.tgt must be VertexId or int, got {type(self.tgt).__name__}")


@dataclass(frozen=True)
class ByteSpanVO(ValueObject):
    """Half-open continuous byte offset span [start, end) on source text."""

    start: int
    end: int

    def __post_init__(self) -> None:
        _require_non_negative_int("ByteSpanVO.start", self.start)
        _require_non_negative_int("ByteSpanVO.end", self.end)
        if self.start > self.end:
            raise ValueError(f"ByteSpanVO start ({self.start}) cannot exceed end ({self.end})")

    @property
    def length(self) -> int:
        return self.end - self.start

    def contains(self, offset: int) -> bool:
        if type(offset) is not int:
            raise TypeError(f"Offset must be int, got {type(offset).__name__}")
        return self.start <= offset < self.end

    def overlaps(self, other: ByteSpanVO) -> bool:
        if type(other) is not ByteSpanVO:
            raise TypeError(f"Cannot test overlap with {type(other).__name__}")
        return max(self.start, other.start) < min(self.end, other.end)

    def slice(self, text: str) -> str:
        if type(text) is not str:
            raise TypeError(f"text must be str, got {type(text).__name__}")
        return text[self.start:self.end]


@dataclass(frozen=True)
class MatrixShape(ValueObject):
    """Non-negative discrete matrix dimensions (rows, cols)."""

    rows: int
    cols: int

    def __post_init__(self) -> None:
        _require_non_negative_int("MatrixShape.rows", self.rows)
        _require_non_negative_int("MatrixShape.cols", self.cols)

    @property
    def is_square(self) -> bool:
        return self.rows == self.cols

    @property
    def total_entries(self) -> int:
        return self.rows * self.cols
