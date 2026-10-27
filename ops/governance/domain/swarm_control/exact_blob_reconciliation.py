from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

from governance.domain.swarm_control.reconciliation_classifier import (
    PathReconciliationDecision,
    ReconciliationDecisionClass,
    ReconciliationLedger,
    classify_path_conflict,
)


class ReconciliationError(Exception):
    """Raised when reconciliation cannot be completed fail-closed."""
    pass


@dataclass(frozen=True, slots=True)
class ReconciledTree:
    path_blobs: dict[str, str]
    ledger: ReconciliationLedger
    evidence_status: str
    reconciled_digest: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ReconciledTree)
        return (
            self.path_blobs == other.path_blobs
            and self.ledger == other.ledger
            and self.evidence_status == other.evidence_status
            and self.reconciled_digest == other.reconciled_digest
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "path_blobs": dict(sorted(self.path_blobs.items(), key=lambda kv: kv[0].encode("utf-8"))),
            "ledger": self.ledger.to_dict(),
            "evidence_status": self.evidence_status,
            "reconciled_digest": self.reconciled_digest,
        }


def reconcile_exact_blobs(
    base_tree: Mapping[str, str],
    main_tree: Mapping[str, str],
    branch_tree: Mapping[str, str],
    active_actor: str,
    ownership_map: Mapping[str, str],
) -> ReconciledTree:
    """Performs exact-blob reconciliation between branch tree and main tree.
    
    Adopts main blobs for shared/foreign paths, preserves branch blobs for owned paths,
    and fails closed if any unresolved conflict is encountered.
    """
    all_paths = sorted(set(base_tree.keys()) | set(main_tree.keys()) | set(branch_tree.keys()), key=lambda s: s.encode("utf-8"))
    decisions: list[PathReconciliationDecision] = []
    reconciled_blobs: dict[str, str] = {}

    for path in all_paths:
        base_oid = base_tree.get(path)
        main_oid = main_tree.get(path)
        branch_oid = branch_tree.get(path)

        decision = classify_path_conflict(
            path=path,
            active_actor=active_actor,
            ownership_map=ownership_map,
            base_oid=base_oid,
            main_oid=main_oid,
            branch_oid=branch_oid,
        )
        decisions.append(decision)

        if decision.decision == ReconciliationDecisionClass.UNRESOLVED:
            raise ReconciliationError(f"Reconciliation blocked by unresolved conflict on '{path}': {decision.reason}")

        if decision.decision in (
            ReconciliationDecisionClass.OWNED,
            # The branch is the only side that moved, so its blob is the answer.
            ReconciliationDecisionClass.TAKE_BRANCH_BLOB,
        ):
            if branch_oid is not None:
                reconciled_blobs[path] = branch_oid
        elif decision.decision == ReconciliationDecisionClass.TAKE_MAIN_BLOB:
            if main_oid is not None:
                reconciled_blobs[path] = main_oid
        elif decision.decision == ReconciliationDecisionClass.SHARED:
            chosen = branch_oid if branch_oid is not None else main_oid
            if chosen is not None:
                reconciled_blobs[path] = chosen
        else:  # pragma: no cover - defensive
            # Every class must be handled. A silently unhandled decision would
            # drop the path from the reconciled tree, which is a data loss that
            # no gate downstream could detect.
            raise ReconciliationError(
                f"unhandled reconciliation decision {decision.decision!r} on '{path}'"
            )

    ledger = ReconciliationLedger.from_decisions(decisions)
    sorted_blobs = dict(sorted(reconciled_blobs.items(), key=lambda kv: kv[0].encode("utf-8")))
    canonical_payload = json.dumps(sorted_blobs, sort_keys=True, separators=(",", ":"))
    reconciled_digest = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()

    return ReconciledTree(
        path_blobs=sorted_blobs,
        ledger=ledger,
        evidence_status="NOT_RERUN_AFTER_RECONCILIATION",
        reconciled_digest=reconciled_digest,
    )
