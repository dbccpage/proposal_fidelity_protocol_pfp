"""N1 Lease Domain Model.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from .lease_error import LeaseError
from .value_objects import (
    DomainInvariantError,
    Epoch,
    FenceToken,
    IdKind,
    LeaseId,
    OwnerId,
    RepoPath,
    RepoWorktreeId,
    UtcTimestamp,
)

N1_LEASE_SCHEMA_V1 = "core.n1_lease.v1"


@dataclass(frozen=True, slots=True, eq=False)
class N1Lease:
    """Immutable record of an active N=1 lease and monotonic fence token."""

    lease_id: LeaseId
    owner_id: OwnerId
    repo_worktree_id: RepoWorktreeId
    canonical_path_scope: tuple[RepoPath, ...]
    semantic_resource_scope: tuple[str, ...]
    epoch: Epoch
    fence_token: FenceToken
    issued_at_utc: UtcTimestamp
    expires_at_utc: UtcTimestamp
    is_killed: bool = False

    def __init__(
        self,
        *,
        lease_id: LeaseId | str,
        owner_id: OwnerId | str,
        repo_worktree_id: RepoWorktreeId | str,
        canonical_path_scope: Iterable[RepoPath | str],
        semantic_resource_scope: Iterable[str] = (),
        epoch: Epoch | int,
        fence_token: FenceToken | int,
        issued_at_utc: UtcTimestamp | str | datetime,
        expires_at_utc: UtcTimestamp | str | datetime,
        is_killed: bool = False,
    ) -> None:
        try:
            l_id = LeaseId.from_str(lease_id, kind=IdKind.LEASE)
            o_id = OwnerId.from_str(owner_id, kind=IdKind.OWNER)
            rw_id = RepoWorktreeId.from_str(repo_worktree_id, kind=IdKind.REPO_WORKTREE)
            paths = tuple(sorted({RepoPath.from_str(p) for p in canonical_path_scope}, key=lambda p: p.value))
            resources = tuple(sorted(set(semantic_resource_scope)))
            ep = Epoch.from_int(epoch) if isinstance(epoch, int) else epoch
            f_tok = FenceToken.from_int(fence_token) if isinstance(fence_token, int) else fence_token
            iss_ts = UtcTimestamp.from_iso(issued_at_utc)
            exp_ts = UtcTimestamp.from_iso(expires_at_utc)
        except DomainInvariantError as exc:
            raise LeaseError("INVALID_LEASE_FIELD", str(exc)) from exc

        object.__setattr__(self, "lease_id", l_id)
        object.__setattr__(self, "owner_id", o_id)
        object.__setattr__(self, "repo_worktree_id", rw_id)
        object.__setattr__(self, "canonical_path_scope", paths)
        object.__setattr__(self, "semantic_resource_scope", resources)
        object.__setattr__(self, "epoch", ep)
        object.__setattr__(self, "fence_token", f_tok)
        object.__setattr__(self, "issued_at_utc", iss_ts)
        object.__setattr__(self, "expires_at_utc", exp_ts)
        object.__setattr__(self, "is_killed", is_killed)

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.lease_id == other.lease_id

    def __hash__(self) -> int:
        return hash((type(self), self.lease_id))
