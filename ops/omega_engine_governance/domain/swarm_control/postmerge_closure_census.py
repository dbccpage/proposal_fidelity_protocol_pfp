from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Sequence


class PrNotClosedError(Exception):
    """Raised when a supposedly merged PR is still observed in the active open list."""
    pass


@dataclass(frozen=True, slots=True)
class PostmergeClosureCensus:
    merged_pr_id: int
    observed_open_pr_ids: tuple[int, ...]
    is_closed: bool
    census_digest: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, PostmergeClosureCensus)
        return (
            self.merged_pr_id == other.merged_pr_id
            and self.observed_open_pr_ids == other.observed_open_pr_ids
            and self.is_closed == other.is_closed
            and self.census_digest == other.census_digest
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "merged_pr_id": self.merged_pr_id,
            "observed_open_pr_ids": list(self.observed_open_pr_ids),
            "is_closed": self.is_closed,
            "census_digest": self.census_digest,
        }


def verify_postmerge_pr_closure(
    merged_pr_id: int,
    observed_open_pr_ids: Sequence[int],
) -> PostmergeClosureCensus:
    """Verifies that merged PR has been closed and removed from the active PR census."""
    open_tuple = tuple(sorted(set(observed_open_pr_ids)))
    if merged_pr_id in open_tuple:
        raise PrNotClosedError(
            f"Direct census failed: PR #{merged_pr_id} was declared merged but remains in open PR census: {open_tuple}"
        )

    raw_payload = json.dumps(
        {
            "merged_pr_id": merged_pr_id,
            "open_pr_ids": list(open_tuple),
            "closed": True,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()

    return PostmergeClosureCensus(
        merged_pr_id=merged_pr_id,
        observed_open_pr_ids=open_tuple,
        is_closed=True,
        census_digest=digest,
    )
