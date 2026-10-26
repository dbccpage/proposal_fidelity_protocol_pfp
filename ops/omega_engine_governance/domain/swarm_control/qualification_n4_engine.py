from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence

from omega_engine_governance.domain.swarm_control.conflict_graph_admission import (
    ConflictAdmissionStatus,
    evaluate_conflict_graph_admission,
)


@dataclass(frozen=True, slots=True)
class N4QualificationResult:
    admitted_count: int
    refused_collision_count: int
    duplicate_patch_detected: bool
    receipt_digest: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, N4QualificationResult)
        return (
            self.admitted_count == other.admitted_count
            and self.refused_collision_count == other.refused_collision_count
            and self.duplicate_patch_detected == other.duplicate_patch_detected
            and self.receipt_digest == other.receipt_digest
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "admitted_count": self.admitted_count,
            "refused_collision_count": self.refused_collision_count,
            "duplicate_patch_detected": self.duplicate_patch_detected,
            "receipt_digest": self.receipt_digest,
        }


def run_n4_qualification_pipeline(
    packet1_id: str,
    packet1_paths: Sequence[str],
    packet2_id: str,
    packet2_paths: Sequence[str],
    packet3_id: str,
    packet3_collision_paths: Sequence[str],
    packet4_id: str,
    packet4_dup_paths: Sequence[str],
    patch_digests: Mapping[str, str],
) -> N4QualificationResult:
    """Executes N=4 qualification scenario verifying write collision refusal and duplicate patch detection."""
    active_write_sets: dict[str, Sequence[str]] = {}
    admitted = 0
    refused_collisions = 0
    dup_patch_found = False

    # 1. Admit Packet 1
    res1 = evaluate_conflict_graph_admission(active_write_sets, packet1_id, packet1_paths, n_ceiling=10)
    if res1.status == ConflictAdmissionStatus.ADMITTED:
        active_write_sets[packet1_id] = packet1_paths
        admitted += 1

    # 2. Admit Packet 2 (disjoint paths from Packet 1)
    res2 = evaluate_conflict_graph_admission(active_write_sets, packet2_id, packet2_paths, n_ceiling=10)
    if res2.status == ConflictAdmissionStatus.ADMITTED:
        active_write_sets[packet2_id] = packet2_paths
        admitted += 1

    # 3. Attempt Packet 3 (collides with Packet 1 write set) -> Refused
    res3 = evaluate_conflict_graph_admission(active_write_sets, packet3_id, packet3_collision_paths, n_ceiling=10)
    if res3.status == ConflictAdmissionStatus.REFUSED_WRITE_CONFLICT:
        refused_collisions += 1

    # 4. Attempt Packet 4 (duplicate patch of Packet 2) -> Refused & Flagged
    res4 = evaluate_conflict_graph_admission(active_write_sets, packet4_id, packet4_dup_paths, n_ceiling=10)
    if res4.status == ConflictAdmissionStatus.REFUSED_WRITE_CONFLICT:
        refused_collisions += 1

    # Check duplicate patch digest equivalence
    if patch_digests.get(packet2_id) == patch_digests.get(packet4_id) and patch_digests.get(packet2_id) is not None:
        dup_patch_found = True

    raw_payload = json.dumps(
        {
            "admitted": admitted,
            "refused_collisions": refused_collisions,
            "dup_patch_found": dup_patch_found,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()

    return N4QualificationResult(
        admitted_count=admitted,
        refused_collision_count=refused_collisions,
        duplicate_patch_detected=dup_patch_found,
        receipt_digest=digest,
    )
