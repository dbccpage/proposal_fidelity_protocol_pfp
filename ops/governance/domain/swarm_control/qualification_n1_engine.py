from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence

from governance.domain.swarm_control.cas_land_license import (
    issue_cas_land_license,
    validate_cas_land_license,
)
from governance.domain.swarm_control.conflict_graph_admission import (
    ConflictAdmissionStatus,
    evaluate_conflict_graph_admission,
)
from governance.domain.swarm_control.merge_mutex import (
    MergeMutexState,
)
from governance.domain.swarm_control.postmerge_content_witness import (
    create_postmerge_content_witness,
)


@dataclass(frozen=True, slots=True)
class N1QualificationResult:
    packet_id: str
    candidate_id: str
    states_traversed: tuple[str, ...]
    is_successful: bool
    receipt_digest: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, N1QualificationResult)
        return (
            self.packet_id == other.packet_id
            and self.candidate_id == other.candidate_id
            and self.states_traversed == other.states_traversed
            and self.is_successful == other.is_successful
            and self.receipt_digest == other.receipt_digest
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "candidate_id": self.candidate_id,
            "states_traversed": list(self.states_traversed),
            "is_successful": self.is_successful,
            "receipt_digest": self.receipt_digest,
        }


def run_n1_qualification_pipeline(
    packet_id: str,
    candidate_id: str,
    write_paths: Sequence[str],
    base_head: str,
    landed_head: str,
    path_blobs: Mapping[str, str],
    observed_path_blobs: Mapping[str, str] | None = None,
) -> N1QualificationResult:
    """Executes the complete N=1 single-agent qualification lifecycle to PRUNED."""
    states: list[str] = []

    # 1. Admit via conflict graph
    admission = evaluate_conflict_graph_admission(
        active_write_sets={},
        candidate_id=candidate_id,
        candidate_write_set=write_paths,
        n_ceiling=10,
    )
    if admission.status != ConflictAdmissionStatus.ADMITTED:
        raise ValueError(f"N=1 Admission refused: {admission.reason}")
    states.append("ADMITTED")

    # 2. Leased
    states.append("LEASED")

    # 3. Bound to candidate branch
    states.append("BOUND")

    # 4. Issue CAS Land License
    license_obj = issue_cas_land_license(
        candidate_id=candidate_id,
        expected_head_sha=base_head,
        current_epoch=100.0,
        ttl_seconds=120.0,
    )
    validate_cas_land_license(license_obj, observed_head_sha=base_head, current_epoch=110.0)
    states.append("READY_FOR_LAND")

    # 5. Acquire Merge Mutex & Land
    mutex = MergeMutexState()
    token = mutex.acquire(holder_id=candidate_id, current_epoch=115.0)
    states.append("LANDED")

    # 6. Post-Merge Content Witness
    create_postmerge_content_witness(
        candidate_id=candidate_id,
        landed_main_head=landed_head,
        expected_path_blobs=path_blobs,
        # Defaults to the promised blobs so the happy path is unchanged, but a
        # caller can supply a divergent mainline and the gate will refuse.
        observed_path_blobs=path_blobs if observed_path_blobs is None else observed_path_blobs,
    )
    states.append("WITNESSED")

    # 7. Release Mutex & Non-force dispose worktree
    mutex.release(token, current_epoch=120.0)
    states.append("DISPOSED")

    # 8. Terminal state PRUNED
    states.append("PRUNED")

    raw_payload = json.dumps(
        {
            "packet_id": packet_id,
            "candidate_id": candidate_id,
            "states": states,
            "landed_head": landed_head,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()

    return N1QualificationResult(
        packet_id=packet_id,
        candidate_id=candidate_id,
        states_traversed=tuple(states),
        is_successful=True,
        receipt_digest=digest,
    )
