"""Rewriting and Span Partition Aggregate Root.

AuthorityEffect: None.
Governing standard: Proposal Fidelity Protocol (PFP v0.2).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple

from omega_engine_pfp.domain.value_objects.topology import ByteSpanVO
from omega_engine_pfp.domain.value_objects.taxonomy import SpanRoleVO
from .base import AggregateRoot


@dataclass
class SpanPartitionAggregate(AggregateRoot):
    """Aggregate Root enforcing continuous, non-overlapping span partitioning of text.

    Invariants:
    1. Spans must be ordered: span[i].end == span[i+1].start.
    2. First span starts at 0.
    3. Last span ends at total_length.
    """

    partitions: Tuple[Tuple[ByteSpanVO, SpanRoleVO], ...]
    total_length: int

    def __post_init__(self) -> None:
        self.validate_invariants()

    def validate_invariants(self) -> None:
        if self.total_length < 0:
            raise ValueError(f"total_length cannot be negative, got {self.total_length}")
        if not self.partitions:
            if self.total_length != 0:
                raise ValueError("Empty partitions only valid for zero-length text")
            return

        first_span, _ = self.partitions[0]
        if first_span.start != 0:
            raise ValueError(f"First span must start at 0, got {first_span.start}")

        for i in range(len(self.partitions) - 1):
            curr_span, _ = self.partitions[i]
            next_span, _ = self.partitions[i + 1]
            if curr_span.end != next_span.start:
                raise ValueError(
                    f"Discontinuous partition at index {i}: "
                    f"span[{i}].end ({curr_span.end}) != span[{i+1}].start ({next_span.start})"
                )

        last_span, _ = self.partitions[-1]
        if last_span.end != self.total_length:
            raise ValueError(
                f"Partition does not cover entire text: last end {last_span.end} != {self.total_length}"
            )

    @classmethod
    def from_pairs(
        cls,
        pairs: Sequence[Tuple[ByteSpanVO, SpanRoleVO]],
        total_length: int,
    ) -> SpanPartitionAggregate:
        return cls(partitions=tuple(pairs), total_length=total_length)
