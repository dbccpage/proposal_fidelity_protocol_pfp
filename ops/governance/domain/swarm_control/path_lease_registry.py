"""Path Lease Registry for Swarm Write Set Exclusivity.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Sequence

from .active_lease_state import ActiveLeaseState
from .lease_denied import LeaseDenied
from .lease_grant import LeaseGrant
from .path_canon import canonicalize_path


def _paths_overlap(p1: str, p2: str) -> bool:
    c1 = canonicalize_path(p1)
    c2 = canonicalize_path(p2)
    if c1 == c2:
        return True
    if c1.startswith(c2 + "/"):
        return True
    if c2.startswith(c1 + "/"):
        return True
    return False


class PathLeaseRegistry:
    def __init__(self) -> None:
        self._active: dict[str, ActiveLeaseState] = {}

    def grant(
        self,
        packet_id: str,
        paths: Sequence[str] | None = None,
        exclusive_resources: Sequence[str] | None = None,
        stacked_under: str | None = None,
        write_paths: Sequence[str] | None = None,
    ) -> LeaseGrant | LeaseDenied:
        target_paths = paths if paths is not None else (write_paths or ())
        p_tuple = tuple(target_paths)
        res_tuple = tuple(exclusive_resources or ())

        for existing_id, existing in self._active.items():
            if stacked_under is not None and existing_id == stacked_under:
                continue

            conflict_paths = [p for p in p_tuple if any(_paths_overlap(p, ep) for ep in existing.paths)]
            conflict_resources = [r for r in res_tuple if r in existing.exclusive_resources]

            if conflict_paths or conflict_resources:
                return LeaseDenied(
                    residual="SHARED_RESOURCE_REQUIRED",
                    holder=existing_id,
                    conflict_paths=tuple(conflict_paths),
                    conflict_resources=tuple(conflict_resources),
                )

        self._active[packet_id] = ActiveLeaseState(
            packet_id=packet_id,
            paths=p_tuple,
            exclusive_resources=res_tuple,
            stacked_under=stacked_under,
        )
        return LeaseGrant(
            packet_id=packet_id,
            paths=p_tuple,
            exclusive_resources=res_tuple,
        )

    def list_active(self) -> tuple[str, ...]:
        return tuple(self._active.keys())

    def revoke(self, packet_id: str) -> bool:
        if packet_id in self._active:
            del self._active[packet_id]
            return True
        return False
