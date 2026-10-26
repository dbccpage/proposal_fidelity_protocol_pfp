from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any

from omega_engine_governance.domain.swarm_control.swarm_status_reconciliation import (
    SwarmDriftKind,
    SwarmStatusSnapshot,
)


class RecoveryActionType(str, Enum):
    RECOVER_STALE_MUTEX = "RECOVER_STALE_MUTEX"
    PRUNE_DIRTY_WORKTREE = "PRUNE_DIRTY_WORKTREE"
    RELEASE_ORPHAN_LEASE = "RELEASE_ORPHAN_LEASE"
    REBIND_HEAD_DRIFT = "REBIND_HEAD_DRIFT"


@dataclass(frozen=True, slots=True)
class RecoveryAction:
    action_type: RecoveryActionType
    target_id: str
    is_dry_run: bool
    description: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, RecoveryAction)
        return (
            self.action_type == other.action_type
            and self.target_id == other.target_id
            and self.is_dry_run == other.is_dry_run
            and self.description == other.description
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_type": self.action_type.value,
            "target_id": self.target_id,
            "is_dry_run": self.is_dry_run,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class RecoveryPlan:
    plan_id: str
    actions: tuple[RecoveryAction, ...]
    is_dry_run: bool
    plan_digest: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, RecoveryPlan)
        return (
            self.plan_id == other.plan_id
            and self.actions == other.actions
            and self.is_dry_run == other.is_dry_run
            and self.plan_digest == other.plan_digest
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "actions": [a.to_dict() for a in self.actions],
            "is_dry_run": self.is_dry_run,
            "plan_digest": self.plan_digest,
            "action_count": len(self.actions),
        }


def plan_recovery_from_snapshot(
    snapshot: SwarmStatusSnapshot,
    *,
    dry_run: bool = True,
) -> RecoveryPlan:
    """Derives deterministic, fail-closed recovery actions from a reconciled swarm snapshot."""
    actions: list[RecoveryAction] = []

    for residual in snapshot.drift_residuals:
        if residual.kind == SwarmDriftKind.ORPHAN_LEASE:
            actions.append(
                RecoveryAction(
                    action_type=RecoveryActionType.RELEASE_ORPHAN_LEASE,
                    target_id=residual.subject_id,
                    is_dry_run=dry_run,
                    description=f"Release orphaned lease '{residual.subject_id}' safely without forcing",
                )
            )
        elif residual.kind == SwarmDriftKind.DETACHED_WORKTREE:
            actions.append(
                RecoveryAction(
                    action_type=RecoveryActionType.PRUNE_DIRTY_WORKTREE,
                    target_id=residual.subject_id,
                    is_dry_run=dry_run,
                    description=f"Prune detached/unreferenced worktree '{residual.subject_id}'",
                )
            )
        elif residual.kind == SwarmDriftKind.HEAD_DRIFT:
            actions.append(
                RecoveryAction(
                    action_type=RecoveryActionType.REBIND_HEAD_DRIFT,
                    target_id=residual.subject_id,
                    is_dry_run=dry_run,
                    description=f"Rebind candidate '{residual.subject_id}' to latest epoch head",
                )
            )
        elif residual.kind == SwarmDriftKind.UNBACKED_PR:
            # Was silently dropped. A snapshot carrying only UNBACKED_PR
            # residuals produced a plan with zero actions, so an operator
            # following the playbook read "nothing to recover" while an orphaned
            # PR sat open against a dead packet.
            actions.append(
                RecoveryAction(
                    action_type=RecoveryActionType.RELEASE_ORPHAN_LEASE,
                    target_id=residual.subject_id,
                    is_dry_run=dry_run,
                    description=(
                        f"Close or re-bind PR '{residual.subject_id}', which is open against a "
                        f"packet no longer active"
                    ),
                )
            )
        else:
            # No silent fall-through. A drift kind added later must fail loudly
            # here rather than vanish from the plan the way UNBACKED_PR did.
            raise ValueError(
                f"no recovery action defined for drift kind {residual.kind!r} "
                f"(subject {residual.subject_id!r})"
            )

    sorted_actions = tuple(sorted(actions, key=lambda a: (a.action_type.value, a.target_id.encode("utf-8"))))
    raw_payload = json.dumps(
        {
            "actions": [a.to_dict() for a in sorted_actions],
            "is_dry_run": dry_run,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()
    plan_id = f"plan:recovery:{digest[:16]}"

    return RecoveryPlan(
        plan_id=plan_id,
        actions=sorted_actions,
        is_dry_run=dry_run,
        plan_digest=digest,
    )
