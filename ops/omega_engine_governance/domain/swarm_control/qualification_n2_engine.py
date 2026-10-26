from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence

from omega_engine_governance.domain.swarm_control.cas_land_license import (
    CasHeadDriftError,
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
from omega_engine_governance.domain.swarm_control.rebind_after_merge import (
    rebind_candidate_to_main_epoch,
)


@dataclass(frozen=True, slots=True)
class N2QualificationResult:
    cand1_landed_head: str
    cand2_stale_assessment_state: str
    cand2_landed_head: str
    is_successful: bool
    receipt_digest: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, N2QualificationResult)
        return (
            self.cand1_landed_head == other.cand1_landed_head
            and self.cand2_stale_assessment_state == other.cand2_stale_assessment_state
            and self.cand2_landed_head == other.cand2_landed_head
            and self.is_successful == other.is_successful
            and self.receipt_digest == other.receipt_digest
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "cand1_landed_head": self.cand1_landed_head,
            "cand2_stale_assessment_state": self.cand2_stale_assessment_state,
            "cand2_landed_head": self.cand2_landed_head,
            "is_successful": self.is_successful,
            "receipt_digest": self.receipt_digest,
        }


def run_n2_qualification_pipeline(
    base_head: str,
    cand1_id: str,
    cand1_paths: Sequence[str],
    cand1_blobs: Mapping[str, str],
    cand1_landed_head: str,
    cand2_id: str,
    cand2_paths: Sequence[str],
    cand2_blobs: Mapping[str, str],
    cand2_landed_head: str,
    cand1_observed_blobs: Mapping[str, str] | None = None,
    cand2_observed_blobs: Mapping[str, str] | None = None,
) -> N2QualificationResult:
    """Executes the complete N=2 dual-agent qualification proving serial landing and rebind invalidation."""
    mutex = MergeMutexState()

    # 1. Admit Candidate 1 and Candidate 2 concurrently (disjoint write paths)
    admit_c1 = evaluate_conflict_graph_admission({}, cand1_id, cand1_paths, n_ceiling=10)
    admit_c2 = evaluate_conflict_graph_admission({cand1_id: cand1_paths}, cand2_id, cand2_paths, n_ceiling=10)
    if admit_c1.status != ConflictAdmissionStatus.ADMITTED or admit_c2.status != ConflictAdmissionStatus.ADMITTED:
        raise ValueError("N=2 Admission failed")

    # 2. Candidate 1 obtains license for base_head and lands
    lic_c1 = issue_cas_land_license(cand1_id, base_head, current_epoch=100.0)
    validate_cas_land_license(lic_c1, base_head, current_epoch=105.0)

    token_c1 = mutex.acquire(cand1_id, current_epoch=110.0)
    create_postmerge_content_witness(
        cand1_id,
        cand1_landed_head,
        cand1_blobs,
        cand1_blobs if cand1_observed_blobs is None else cand1_observed_blobs,
    )
    mutex.release(token_c1, current_epoch=115.0)

    # 3. Mainline has now advanced to cand1_landed_head. Candidate 2 attempts land on stale base_head -> fails
    lic_c2_stale = issue_cas_land_license(cand2_id, base_head, current_epoch=100.0)
    try:
        validate_cas_land_license(lic_c2_stale, observed_head_sha=cand1_landed_head, current_epoch=120.0)
        raise AssertionError("Expected CasHeadDriftError was not raised")
    except CasHeadDriftError:
        pass

    # 4. Candidate 2 rebinds to new epoch head (cand1_landed_head)
    rebind_res = rebind_candidate_to_main_epoch(
        candidate_id=cand2_id,
        previous_epoch_head=base_head,
        new_epoch_head=cand1_landed_head,
        active_obligation_ids={"unit_test_suite": base_head},
    )
    stale_state = rebind_res.invalidated_assessments[0].state.value

    # 5. Candidate 2 gathers fresh evidence, obtains fresh license for cand1_landed_head, and lands
    lic_c2_fresh = issue_cas_land_license(cand2_id, cand1_landed_head, current_epoch=130.0)
    validate_cas_land_license(lic_c2_fresh, observed_head_sha=cand1_landed_head, current_epoch=135.0)

    token_c2 = mutex.acquire(cand2_id, current_epoch=140.0)
    create_postmerge_content_witness(
        cand2_id,
        cand2_landed_head,
        cand2_blobs,
        cand2_blobs if cand2_observed_blobs is None else cand2_observed_blobs,
    )
    mutex.release(token_c2, current_epoch=145.0)

    raw_payload = json.dumps(
        {
            "cand1_head": cand1_landed_head,
            "cand2_head": cand2_landed_head,
            "stale_state": stale_state,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()

    return N2QualificationResult(
        cand1_landed_head=cand1_landed_head,
        cand2_stale_assessment_state=stale_state,
        cand2_landed_head=cand2_landed_head,
        is_successful=True,
        receipt_digest=digest,
    )
