"""Transform survivor deduplication domain logic."""
from __future__ import annotations

from typing import Any, List, Optional
from .exceptions import DomainError
from .shared_kernel.result import Failure, Result, Success, err, ok


def dedup_transform_survivors(
    survivors: List[Any], query: Optional[str]
) -> List[Any]:
    """Drop separator-operation-map survivors duplicated by a non-op-map survivor."""
    if query is None:
        raise ValueError("Query cannot be None for survivor deduplication")
    if len(survivors) <= 1:
        return survivors
    non_opmap_q = {r.apply(query) for r in survivors if getattr(r, "op_id", "") != "separator_operation_map"}
    return [
        r
        for r in survivors
        if getattr(r, "op_id", "") != "separator_operation_map" or r.apply(query) not in non_opmap_q
    ]


def dedup_transform_survivors_safe(
    survivors: List[Any], query: Optional[str]
) -> Result[List[Any], DomainError]:
    """Railway boundary for transform survivor deduplication."""
    if query is None:
        return err(DomainError("Query cannot be None for survivor deduplication."))
    try:
        return ok(dedup_transform_survivors(survivors, query))
    except Exception as exc:
        return err(DomainError(f"Transform survivor deduplication failed: {exc}"))


__all__ = ["dedup_transform_survivors", "dedup_transform_survivors_safe"]
