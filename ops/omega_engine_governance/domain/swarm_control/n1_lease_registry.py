"""N1 Lease Registry Domain Model.

AuthorityEffect: None.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from .lease_error import LeaseError
from .n1_lease import N1Lease
from .value_objects import Epoch, FenceToken, RepoPath, UtcTimestamp


class N1LeaseRegistry:
    """Durable in-memory registry for N=1 lease grants, fences, and revocations."""

    def __init__(self, current_epoch: int = 1) -> None:
        self._epoch = Epoch(current_epoch)
        self._active_leases: dict[str, N1Lease] = {}
        self._killed_leases: set[str] = set()
        self._highest_fence: FenceToken = FenceToken(0)

    @property
    def current_epoch(self) -> int:
        return self._epoch.value

    def bump_epoch(self) -> int:
        self._epoch = self._epoch.bump()
        return self._epoch.value

    def grant(
        self,
        *,
        lease_id: str,
        owner_id: str,
        repo_worktree_id: str,
        path_scope: Iterable[str | RepoPath],
        resource_scope: Iterable[str] = (),
        issued_at_utc: str | datetime,
        expires_at_utc: str | datetime,
    ) -> N1Lease:
        if lease_id in self._killed_leases:
            raise LeaseError("LEASE_KILLED_OR_REVOKED", lease_id)
        if lease_id in self._active_leases:
            raise LeaseError("LEASE_ALREADY_ACTIVE", lease_id)

        canonical_paths = tuple(sorted({RepoPath.from_str(p) for p in path_scope}, key=lambda p: p.value))
        canonical_resources = tuple(sorted(set(resource_scope)))

        for active in self._active_leases.values():
            if str(active.repo_worktree_id) != repo_worktree_id:
                continue
            common_res = set(canonical_resources) & set(active.semantic_resource_scope)
            if common_res:
                raise LeaseError(
                    "RESOURCE_SCOPE_CONFLICT",
                    f"conflicts with lease {active.lease_id} on {common_res}",
                )
            for p1 in canonical_paths:
                for p2 in active.canonical_path_scope:
                    if p1.conflicts_with(p2):
                        raise LeaseError(
                            "HIERARCHICAL_PATH_CONFLICT",
                            f"path {p1} conflicts with active lease {active.lease_id} path {p2}",
                        )

        self._highest_fence = self._highest_fence.next_token()
        lease = N1Lease(
            lease_id=lease_id,
            owner_id=owner_id,
            repo_worktree_id=repo_worktree_id,
            canonical_path_scope=canonical_paths,
            semantic_resource_scope=canonical_resources,
            epoch=self._epoch,
            fence_token=self._highest_fence,
            issued_at_utc=issued_at_utc,
            expires_at_utc=expires_at_utc,
            is_killed=False,
        )
        self._active_leases[lease_id] = lease
        return lease

    def kill(self, lease_id: str) -> None:
        """Sticky revocation of a lease."""
        self._killed_leases.add(lease_id)
        if lease_id in self._active_leases:
            del self._active_leases[lease_id]

    def release(self, lease_id: str) -> None:
        """Normal release upon completed effect."""
        if lease_id in self._active_leases:
            del self._active_leases[lease_id]

    def verify_active_fence(
        self,
        lease: N1Lease,
        *,
        current_time_utc: str | datetime | None = None,
    ) -> None:
        """Assert that the lease is currently active, unrevoked, unexpired, and monotonic."""
        lease_id_str = str(lease.lease_id)
        if lease_id_str in self._killed_leases or lease.is_killed:
            raise LeaseError("LEASE_KILLED_OR_REVOKED", lease_id_str)
        if lease_id_str not in self._active_leases:
            raise LeaseError("LEASE_NOT_ACTIVE", lease_id_str)

        active = self._active_leases[lease_id_str]
        if active.owner_id != lease.owner_id:
            raise LeaseError("LEASE_OWNER_MISMATCH", f"expected {active.owner_id} got {lease.owner_id}")
        if active.epoch != self._epoch or lease.epoch != self._epoch:
            raise LeaseError("LEASE_EPOCH_MISMATCH", f"current epoch {self._epoch} lease epoch {lease.epoch}")
        if lease.fence_token.is_stale_compared_to(active.fence_token):
            raise LeaseError("STALE_FENCE_TOKEN", f"fence {lease.fence_token} < current {active.fence_token}")

        now_ts = UtcTimestamp.from_iso(current_time_utc) if current_time_utc is not None else UtcTimestamp.now()
        if not lease.expires_at_utc.is_after(now_ts):
            raise LeaseError("LEASE_EXPIRED", f"now {now_ts} >= expiry {lease.expires_at_utc}")
