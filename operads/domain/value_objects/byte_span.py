"""Exact half-open byte range and line/column source provenance."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceByteSpan:
    start_byte: int
    end_byte: int
    start_line: int
    start_col: int
    end_line: int
    end_col: int

    def __post_init__(self) -> None:
        for name, val in (
            ("start_byte", self.start_byte),
            ("end_byte", self.end_byte),
            ("start_line", self.start_line),
            ("start_col", self.start_col),
            ("end_line", self.end_line),
            ("end_col", self.end_col),
        ):
            if not isinstance(val, int) or isinstance(val, bool):
                raise TypeError(f"{name} must be an integer, got {type(val).__name__}")
        if self.start_byte < 0 or self.end_byte < self.start_byte:
            raise ValueError(f"invalid byte span: [{self.start_byte}, {self.end_byte})")
        if self.start_line < 1 or self.end_line < self.start_line:
            raise ValueError(f"invalid line span: lines {self.start_line}..{self.end_line}")
        if self.start_col < 0 or (self.start_line == self.end_line and self.end_col < self.start_col):
            raise ValueError(f"invalid column span: cols {self.start_col}..{self.end_col}")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.start_byte == other.start_byte
            and self.end_byte == other.end_byte
            and self.start_line == other.start_line
            and self.start_col == other.start_col
            and self.end_line == other.end_line
            and self.end_col == other.end_col
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.start_byte,
            self.end_byte,
            self.start_line,
            self.start_col,
            self.end_line,
            self.end_col,
        ))

    @property
    def byte_length(self) -> int:
        return self.end_byte - self.start_byte
