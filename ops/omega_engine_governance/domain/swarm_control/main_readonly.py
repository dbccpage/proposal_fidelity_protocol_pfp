"""Read-only main enforcement for agent edits (STORY-033-002).

Main prohibition is checked before lease membership. Lease roots nested under
primary main are rejected (MAIN_IS_LEDGER / LEASE_NESTED_IN_MAIN).
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass

from .path_canon import path_is_under


@dataclass(frozen=True)
class WriteGuardResult:
    allowed: bool
    residual: str | None


def guard_write(
    target_path: str,
    *,
    primary_main_path: str,
    under_lease_worktree: str | None = None,
) -> WriteGuardResult:
    # Invalid configuration: lease nested inside main cannot authorize writes.
    if under_lease_worktree and path_is_under(under_lease_worktree, primary_main_path):
        return WriteGuardResult(False, "LEASE_NESTED_IN_MAIN")

    # Main ledger first â€” never allow writes under main even if also under a lease.
    if path_is_under(target_path, primary_main_path):
        return WriteGuardResult(False, "MAIN_IS_LEDGER")

    if under_lease_worktree:
        if path_is_under(target_path, under_lease_worktree):
            return WriteGuardResult(True, None)
        return WriteGuardResult(False, "OUTSIDE_LEASE")
    return WriteGuardResult(True, None)
