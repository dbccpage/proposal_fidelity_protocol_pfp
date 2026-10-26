"""Evidence Status Domain Enumeration and Aggregation.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import Enum
from .aggregate_error import AggregateError


class EvidenceStatus(str, Enum):
    PASS = "PASS"
    SKIP = "SKIP"
    BYPASS = "BYPASS"
    MISSING = "MISSING"
    UNKNOWN = "UNKNOWN"
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    STALE_AFTER_REBASE = "STALE_AFTER_REBASE"
    NOT_RERUN_AFTER_RECONCILIATION = "NOT_RERUN_AFTER_RECONCILIATION"


def aggregate_required(statuses: Sequence[EvidenceStatus]) -> EvidenceStatus:
    """Refuse overall PASS when any required item is non-PASS."""
    if type(statuses) not in {list, tuple}:
        raise AggregateError("INVALID_EVIDENCE_STATUS_CONTAINER")
    if not statuses:
        raise AggregateError("NO_REQUIRED_ITEMS")
    if len(statuses) > 10_000:
        raise AggregateError("TOO_MANY_REQUIRED_ITEMS")
    for s in statuses:
        if type(s) is not EvidenceStatus:
            raise AggregateError("INVALID_EVIDENCE_STATUS_TYPE")
        if s is not EvidenceStatus.PASS:
            raise AggregateError(f"AGGREGATE_BLOCKED_BY:{s.value}")
    return EvidenceStatus.PASS
