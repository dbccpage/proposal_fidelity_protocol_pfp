from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence

from omega_engine_governance.domain.swarm_control.cas_land_license import (
    issue_cas_land_license,
    validate_cas_land_license,
)
from omega_engine_governance.domain.swarm_control.conflict_graph_admission import (
    ConflictAdmissionStatus,
    evaluate_conflict_graph_admission,
)
from omega_engine_governance.domain.swarm_control.merge_mutex import (
    MergeMutexState,
)
from omega_engine_governance.domain.swarm_control.postmerge_content_witness import (
    create_postmerge_content_witness,
)


@dataclass(frozen=True, slots=True)
class N10CampaignResult:
    admitted_count: int
    landed_count: int
    is_successful: bool
    epic_dod_claimed: bool
    receipt_digest: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, N10CampaignResult)
        return (
            self.admitted_count == other.admitted_count
            and self.landed_count == other.landed_count
            and self.is_successful == other.is_successful
            and self.epic_dod_claimed == other.epic_dod_claimed
            and self.receipt_digest == other.receipt_digest
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "admitted_count": self.admitted_count,
            "landed_count": self.landed_count,
            "is_successful": self.is_successful,
            "epic_dod_claimed": self.epic_dod_claimed,
            "receipt_digest": self.receipt_digest,
        }


def run_n10_skeleton_harness(
    candidate_specs: Sequence[tuple[str, Sequence[str], Mapping[str, str]]],  # (cand_id, paths, blobs)
    initial_main_head: str,
    *,
    n_ceiling: int = 10,
    observed_blobs: Mapping[str, Mapping[str, str]] | None = None,
) -> N10CampaignResult:
    """Executes N=10 concurrency skeleton harness under serial merge mutex.
    
    AuthorityEffect: None. Does NOT claim full production multi-tenant Epic DoD.
    """
    active_write_sets: dict[str, Sequence[str]] = {}
    admitted_candidates: list[tuple[str, Sequence[str], Mapping[str, str]]] = []

    # 1. Admit up to N ceiling
    for cand_id, paths, blobs in candidate_specs:
        decision = evaluate_conflict_graph_admission(
            active_write_sets=active_write_sets,
            candidate_id=cand_id,
            candidate_write_set=paths,
            n_ceiling=n_ceiling,
        )
        if decision.status == ConflictAdmissionStatus.ADMITTED:
            active_write_sets[cand_id] = paths
            admitted_candidates.append((cand_id, paths, blobs))

    # 2. Serial landing under mutex
    mutex = MergeMutexState()
    current_head = initial_main_head
    landed_count = 0

    for idx, (cand_id, paths, blobs) in enumerate(admitted_candidates, start=1):
        epoch_time = 100.0 + (idx * 10)
        license_obj = issue_cas_land_license(cand_id, current_head, current_epoch=epoch_time)
        validate_cas_land_license(license_obj, current_head, current_epoch=epoch_time + 1.0)

        token = mutex.acquire(cand_id, current_epoch=epoch_time + 2.0)
        new_head = f"head_epoch_{idx}_{cand_id}"
        create_postmerge_content_witness(
            cand_id,
            new_head,
            blobs,
            blobs if observed_blobs is None else observed_blobs.get(cand_id, blobs),
        )
        mutex.release(token, current_epoch=epoch_time + 5.0)

        current_head = new_head
        landed_count += 1

    raw_payload = json.dumps(
        {
            "admitted": len(admitted_candidates),
            "landed": landed_count,
            "final_head": current_head,
            "epic_dod_claimed": False,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()

    return N10CampaignResult(
        admitted_count=len(admitted_candidates),
        landed_count=landed_count,
        is_successful=True,
        epic_dod_claimed=False,
        receipt_digest=digest,
    )
