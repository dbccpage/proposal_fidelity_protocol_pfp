from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Mapping, Sequence


class SwarmDriftKind(str, Enum):
    ORPHAN_LEASE = "ORPHAN_LEASE"
    UNBACKED_PR = "UNBACKED_PR"
    DETACHED_WORKTREE = "DETACHED_WORKTREE"
    HEAD_DRIFT = "HEAD_DRIFT"


@dataclass(frozen=True, slots=True)
class SwarmDriftResidual:
    residual_id: str
    kind: SwarmDriftKind
    subject_id: str
    details: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, SwarmDriftResidual)
        return (
            self.residual_id == other.residual_id
            and self.kind == other.kind
            and self.subject_id == other.subject_id
            and self.details == other.details
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "residual_id": self.residual_id,
            "kind": self.kind.value,
            "subject_id": self.subject_id,
            "details": self.details,
        }


@dataclass(frozen=True, slots=True)
class SwarmStatusSnapshot:
    active_packet_ids: tuple[str, ...]
    active_lease_ids: tuple[str, ...]
    active_worktree_ids: tuple[str, ...]
    open_pr_ids: tuple[int, ...]
    epoch_head: str
    drift_residuals: tuple[SwarmDriftResidual, ...]
    snapshot_digest: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, SwarmStatusSnapshot)
        return (
            self.active_packet_ids == other.active_packet_ids
            and self.active_lease_ids == other.active_lease_ids
            and self.active_worktree_ids == other.active_worktree_ids
            and self.open_pr_ids == other.open_pr_ids
            and self.epoch_head == other.epoch_head
            and self.drift_residuals == other.drift_residuals
            and self.snapshot_digest == other.snapshot_digest
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_packet_ids": list(self.active_packet_ids),
            "active_lease_ids": list(self.active_lease_ids),
            "active_worktree_ids": list(self.active_worktree_ids),
            "open_pr_ids": list(self.open_pr_ids),
            "epoch_head": self.epoch_head,
            "drift_residuals": [r.to_dict() for r in self.drift_residuals],
            "snapshot_digest": self.snapshot_digest,
        }


def reconcile_swarm_status(
    active_packet_ids: Sequence[str],
    active_leases: Mapping[str, str],        # lease_id -> packet_id
    active_worktrees: Mapping[str, str],     # worktree_id -> packet_id
    open_prs: Mapping[int, str],             # pr_number -> candidate_packet_id
    epoch_head: str,
) -> SwarmStatusSnapshot:
    """Reconciles operator state across packets, leases, worktrees, and PRs.
    
    AuthorityEffect: None. Reconciles state and flags drift anomalies as typed residuals.
    """
    packet_set = set(active_packet_ids)
    drift: list[SwarmDriftResidual] = []

    # 1. Check Orphan Leases (lease points to unknown/unactive packet)
    for lease_id, bound_packet in active_leases.items():
        if bound_packet not in packet_set:
            drift.append(
                SwarmDriftResidual(
                    residual_id=f"drift:lease:{lease_id}",
                    kind=SwarmDriftKind.ORPHAN_LEASE,
                    subject_id=lease_id,
                    details=f"Lease '{lease_id}' bound to non-active packet '{bound_packet}'",
                )
            )

    # 2. Check Detached Worktrees (worktree points to unknown/unactive packet)
    for wt_id, bound_packet in active_worktrees.items():
        if bound_packet not in packet_set:
            drift.append(
                SwarmDriftResidual(
                    residual_id=f"drift:worktree:{wt_id}",
                    kind=SwarmDriftKind.DETACHED_WORKTREE,
                    subject_id=wt_id,
                    details=f"Worktree '{wt_id}' allocated for non-active packet '{bound_packet}'",
                )
            )

    # 3. Check Unbacked PRs (open PR references unknown candidate packet)
    for pr_num, bound_cand in open_prs.items():
        if bound_cand not in packet_set:
            drift.append(
                SwarmDriftResidual(
                    residual_id=f"drift:pr:{pr_num}",
                    kind=SwarmDriftKind.UNBACKED_PR,
                    subject_id=str(pr_num),
                    details=f"Open PR #{pr_num} references non-active packet candidate '{bound_cand}'",
                )
            )

    sorted_packets = tuple(sorted(packet_set, key=lambda s: s.encode("utf-8")))
    sorted_leases = tuple(sorted(active_leases.keys(), key=lambda s: s.encode("utf-8")))
    sorted_wts = tuple(sorted(active_worktrees.keys(), key=lambda s: s.encode("utf-8")))
    sorted_prs = tuple(sorted(open_prs.keys()))
    sorted_drift = tuple(sorted(drift, key=lambda d: d.residual_id.encode("utf-8")))

    # The digest previously carried only `drift_count` and the bare id lists, so
    # two estates with the same lease ids but different lease-to-packet bindings
    # hashed identically, as did two snapshots whose residuals were entirely
    # different kinds as long as there were the same number of them. Swapping one
    # ORPHAN_LEASE for one UNBACKED_PR left the digest unchanged, so anything
    # trusting it to pin the reconciled state could not see the substitution.
    #
    # Serialise the residual contents and the bindings, the way
    # `ReconciliationLedger.from_decisions` already does.
    raw_payload = json.dumps(
        {
            "packets": sorted_packets,
            "leases": sorted_leases,
            "worktrees": sorted_wts,
            "prs": sorted_prs,
            "epoch_head": epoch_head,
            "lease_bindings": dict(sorted(active_leases.items(), key=lambda kv: kv[0].encode("utf-8"))),
            "worktree_bindings": dict(
                sorted(active_worktrees.items(), key=lambda kv: kv[0].encode("utf-8"))
            ),
            "pr_bindings": {str(k): v for k, v in sorted(open_prs.items())},
            "drift_residuals": [d.to_dict() for d in sorted_drift],
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()

    return SwarmStatusSnapshot(
        active_packet_ids=sorted_packets,
        active_lease_ids=sorted_leases,
        active_worktree_ids=sorted_wts,
        open_pr_ids=sorted_prs,
        epoch_head=epoch_head,
        drift_residuals=sorted_drift,
        snapshot_digest=digest,
    )
