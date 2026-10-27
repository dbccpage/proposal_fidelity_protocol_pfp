from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Mapping, Sequence


class ReconciliationDecisionClass(str, Enum):
    OWNED = "OWNED"
    SHARED = "SHARED"
    TAKE_MAIN_BLOB = "TAKE_MAIN_BLOB"
    #: The branch changed this path and main did not, so there is nothing to
    #: reconcile against. Added because the classifier had no branch for the
    #: ordinary case and fell through to UNRESOLVED, which meant every added
    #: file and every edit to an unregistered path blocked the whole landing.
    TAKE_BRANCH_BLOB = "TAKE_BRANCH_BLOB"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True, slots=True)
class PathReconciliationDecision:
    path: str
    decision: ReconciliationDecisionClass
    owner: str | None = None
    base_oid: str | None = None
    main_oid: str | None = None
    branch_oid: str | None = None
    reason: str = ""

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, PathReconciliationDecision)
        return (
            self.path == other.path
            and self.decision == other.decision
            and self.owner == other.owner
            and self.base_oid == other.base_oid
            and self.main_oid == other.main_oid
            and self.branch_oid == other.branch_oid
            and self.reason == other.reason
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "decision": self.decision.value,
            "owner": self.owner,
            "base_oid": self.base_oid,
            "main_oid": self.main_oid,
            "branch_oid": self.branch_oid,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class ReconciliationLedger:
    decisions: tuple[PathReconciliationDecision, ...]
    ledger_digest: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ReconciliationLedger)
        return self.decisions == other.decisions and self.ledger_digest == other.ledger_digest

    @classmethod
    def from_decisions(cls, decisions: Sequence[PathReconciliationDecision]) -> ReconciliationLedger:
        sorted_decisions = tuple(sorted(decisions, key=lambda d: d.path.encode("utf-8")))
        canonical_payload = json.dumps(
            [d.to_dict() for d in sorted_decisions],
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
        return cls(decisions=sorted_decisions, ledger_digest=digest)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decisions": [d.to_dict() for d in self.decisions],
            "ledger_digest": self.ledger_digest,
            "count": len(self.decisions),
        }


def classify_path_conflict(
    path: str,
    active_actor: str,
    ownership_map: Mapping[str, str],
    base_oid: str | None,
    main_oid: str | None,
    branch_oid: str | None,
) -> PathReconciliationDecision:
    """Classifies a path conflict between main and candidate branch.
    
    Fails closed to UNRESOLVED for unknown or ambiguous concurrent edits.
    """
    owner = ownership_map.get(path)

    # Identical state - no reconciliation needed
    if branch_oid == main_oid:
        return PathReconciliationDecision(
            path=path,
            decision=ReconciliationDecisionClass.OWNED if owner == active_actor else ReconciliationDecisionClass.SHARED,
            owner=owner,
            base_oid=base_oid,
            main_oid=main_oid,
            branch_oid=branch_oid,
            reason="Path identical between branch and main",
        )

    # 1. Owned by current actor
    if owner == active_actor:
        return PathReconciliationDecision(
            path=path,
            decision=ReconciliationDecisionClass.OWNED,
            owner=owner,
            base_oid=base_oid,
            main_oid=main_oid,
            branch_oid=branch_oid,
            reason=f"Path owned exclusively by active actor '{active_actor}'",
        )

    # 2. Owned by another actor
    if owner is not None and owner != active_actor:
        return PathReconciliationDecision(
            path=path,
            decision=ReconciliationDecisionClass.TAKE_MAIN_BLOB,
            owner=owner,
            base_oid=base_oid,
            main_oid=main_oid,
            branch_oid=branch_oid,
            reason=f"Path owned by foreign actor '{owner}', adopting main blob",
        )

    # 3. Unowned / Shared: Branch has no changes from base, main moved -> take main
    if branch_oid == base_oid and main_oid != base_oid:
        return PathReconciliationDecision(
            path=path,
            decision=ReconciliationDecisionClass.TAKE_MAIN_BLOB,
            owner=None,
            base_oid=base_oid,
            main_oid=main_oid,
            branch_oid=branch_oid,
            reason="Unowned path unmodified on branch, adopting new main blob",
        )

    # 4. Unowned / Shared: branch moved, main did not -> take the branch blob.
    #
    # The ordinary case, and it was missing. Every branch-local edit and every
    # newly added file (base_oid is None, main_oid is None, branch_oid set) fell
    # past this point into UNRESOLVED, so `reconcile_exact_blobs` raised for
    # essentially any real candidate. Fail-closed is correct for a genuine
    # concurrent edit; it is not correct for "nobody else touched this".
    if main_oid == base_oid and branch_oid != base_oid:
        return PathReconciliationDecision(
            path=path,
            decision=ReconciliationDecisionClass.TAKE_BRANCH_BLOB,
            owner=None,
            base_oid=base_oid,
            main_oid=main_oid,
            branch_oid=branch_oid,
            reason="Unowned path modified on branch only, main unchanged since base",
        )

    # 5. Unowned / Shared: Both modified from base -> fail-closed UNRESOLVED
    return PathReconciliationDecision(
        path=path,
        decision=ReconciliationDecisionClass.UNRESOLVED,
        owner=None,
        base_oid=base_oid,
        main_oid=main_oid,
        branch_oid=branch_oid,
        reason="Unowned path concurrently modified on both branch and main with no registered owner",
    )
