from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence


class ConflictAdmissionStatus(str, Enum):
    ADMITTED = "ADMITTED"
    REFUSED_CAPACITY_CEILING = "REFUSED_CAPACITY_CEILING"
    REFUSED_WRITE_CONFLICT = "REFUSED_WRITE_CONFLICT"


@dataclass(frozen=True, slots=True)
class ConflictEdge:
    packet_a: str
    packet_b: str
    conflicting_paths: tuple[str, ...]

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ConflictEdge)
        return (
            self.packet_a == other.packet_a
            and self.packet_b == other.packet_b
            and self.conflicting_paths == other.conflicting_paths
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "packet_a": self.packet_a,
            "packet_b": self.packet_b,
            "conflicting_paths": list(self.conflicting_paths),
        }


@dataclass(frozen=True, slots=True)
class ConflictAdmissionDecision:
    candidate_id: str
    status: ConflictAdmissionStatus
    active_count: int
    n_ceiling: int
    conflict_edges: tuple[ConflictEdge, ...]
    reason: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ConflictAdmissionDecision)
        return (
            self.candidate_id == other.candidate_id
            and self.status == other.status
            and self.active_count == other.active_count
            and self.n_ceiling == other.n_ceiling
            and self.conflict_edges == other.conflict_edges
            and self.reason == other.reason
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "status": self.status.value,
            "active_count": self.active_count,
            "n_ceiling": self.n_ceiling,
            "conflict_edges": [e.to_dict() for e in self.conflict_edges],
            "reason": self.reason,
        }


def evaluate_conflict_graph_admission(
    active_write_sets: Mapping[str, Sequence[str]],
    candidate_id: str,
    candidate_write_set: Sequence[str],
    *,
    n_ceiling: int = 10,
) -> ConflictAdmissionDecision:
    """Evaluates conflict graph admission against active write-sets and N ceiling.
    
    Guarantees N is enforced as a safety ceiling, and overlapping write paths are refused fail-closed.
    """
    active_count = len(active_write_sets)

    # 1. Capacity Ceiling Check
    if active_count >= n_ceiling:
        return ConflictAdmissionDecision(
            candidate_id=candidate_id,
            status=ConflictAdmissionStatus.REFUSED_CAPACITY_CEILING,
            active_count=active_count,
            n_ceiling=n_ceiling,
            conflict_edges=(),
            reason=f"Active packet count ({active_count}) reached or exceeded concurrency ceiling N={n_ceiling}",
        )

    # 2. Write-Set Overlap Check
    candidate_paths_set = set(candidate_write_set)
    conflict_edges: list[ConflictEdge] = []

    for active_id, active_paths in active_write_sets.items():
        overlap = sorted(candidate_paths_set & set(active_paths), key=lambda s: s.encode("utf-8"))
        if overlap:
            conflict_edges.append(
                ConflictEdge(
                    packet_a=candidate_id,
                    packet_b=active_id,
                    conflicting_paths=tuple(overlap),
                )
            )

    if conflict_edges:
        sorted_edges = tuple(sorted(conflict_edges, key=lambda e: (e.packet_b.encode("utf-8"))))
        return ConflictAdmissionDecision(
            candidate_id=candidate_id,
            status=ConflictAdmissionStatus.REFUSED_WRITE_CONFLICT,
            active_count=active_count,
            n_ceiling=n_ceiling,
            conflict_edges=sorted_edges,
            reason=f"Candidate overlaps with {len(sorted_edges)} active write set(s): "
                   f"{', '.join(e.packet_b for e in sorted_edges)}",
        )

    # 3. Admitted
    return ConflictAdmissionDecision(
        candidate_id=candidate_id,
        status=ConflictAdmissionStatus.ADMITTED,
        active_count=active_count,
        n_ceiling=n_ceiling,
        conflict_edges=(),
        reason=f"Candidate write set disjoint with all {active_count} active packet(s); under ceiling N={n_ceiling}",
    )
