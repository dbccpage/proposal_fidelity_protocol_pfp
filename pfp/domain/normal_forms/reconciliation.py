"""Observer freshness, loss-ledger, and reconciliation normal forms.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

# =============================================================================
# Part 18: Observer Freshness & Cross-Domain Reconciliation Normal Forms
# =============================================================================


@dataclass(frozen=True)
class ObserverSpec:
    observer_id: str
    max_lag_seconds: int
    authorized_scopes: tuple[str, ...]

    def is_more_stringent_than(self, other: "ObserverSpec") -> bool:
        """Poset order A <= B: A has tighter or equal SLA budget and subset of scopes."""
        return self.max_lag_seconds <= other.max_lag_seconds and set(
            self.authorized_scopes
        ).issubset(set(other.authorized_scopes))


def evaluate_freshness(scenario: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Evaluates observer-relative freshness under SLA budgets and explicit access scopes.

    Invariants (AuthorityEffect: None):
    1. Scope must be explicit: missing or empty packet_scope fails closed (Refuse).
    2. Replica lag must be trusted and non-negative: missing or malformed lag fails closed (ConservativeInvalidate).
    3. Observer must declare explicit authorized_scopes: missing scopes fail closed (Refuse).
    4. A fresh timestamp does NOT prove correctness or grant authority.
    """
    packet = scenario.get("packet", {})
    observers = scenario.get("observers", [])

    lag = packet.get("replica_lag_seconds")
    packet_scope = packet.get("packet_scope")

    invalid_packet = _packet_freshness_failure(observers, packet_scope, lag)
    if invalid_packet is not None:
        return invalid_packet
    return [_evaluate_observer_freshness(observer, packet_scope, lag) for observer in observers]


def _freshness_result(
    observer_id: Any, terminal_route: str, authorized: bool, reason: str
) -> dict[str, Any]:
    return {
        "observer_id": observer_id,
        "terminal_route": terminal_route,
        "authorized": authorized,
        "reason": reason,
    }


def _packet_freshness_failure(
    observers: Sequence[Mapping[str, Any]], packet_scope: Any, lag: Any
) -> list[dict[str, Any]] | None:
    if packet_scope is None or not isinstance(packet_scope, str) or not packet_scope.strip():
        return [
            _freshness_result(
                observer.get("observer_id", "unknown"),
                "Refuse",
                False,
                "Packet scope is missing or malformed; freshness evaluation fails closed without explicit scope.",
            )
            for observer in observers
        ]
    if lag is None or not isinstance(lag, (int, float)) or lag < 0:
        return [
            _freshness_result(
                observer.get("observer_id", "unknown"),
                "ConservativeInvalidate",
                False,
                "Replica lag is missing or null or malformed; unable to verify SLA budget.",
            )
            for observer in observers
        ]
    return None


def _evaluate_observer_freshness(
    observer: Mapping[str, Any], packet_scope: str, lag: int | float
) -> dict[str, Any]:
    observer_id = observer.get("observer_id", "unknown")
    max_lag = observer.get("max_lag_seconds")
    auth_scopes = observer.get("authorized_scopes")
    if auth_scopes is None or not isinstance(auth_scopes, (list, tuple, set)):
        return _freshness_result(
            observer_id,
            "Refuse",
            False,
            f"Observer '{observer_id}' has missing or malformed authorized_scopes.",
        )
    if max_lag is None or not isinstance(max_lag, (int, float)) or max_lag < 0:
        return _freshness_result(
            observer_id,
            "ConservativeInvalidate",
            False,
            f"Observer '{observer_id}' has missing or invalid max_lag_seconds ({max_lag}).",
        )
    if packet_scope not in auth_scopes:
        return _freshness_result(
            observer_id,
            "Refuse",
            False,
            f"Observer is not authorized for packet scope: '{packet_scope}'.",
        )
    authorized = lag <= max_lag
    route = "AuthorizedFresh" if authorized else "RefreshRequired"
    comparison = "is within" if authorized else "exceeds"
    reason = f"Replica lag ({lag}s) {comparison} the observer's max limit ({max_lag}s)."
    return _freshness_result(observer_id, route, authorized, reason)


def verify_observer_lattice_monotonicity(
    poset_chain: Sequence[Mapping[str, Any]], packet: Mapping[str, Any]
) -> tuple[bool, list[str]]:
    """Verifies that freshness authorization is a monotonic functor over an observer poset chain.
    If observer O_i authorizes the packet as AuthorizedFresh, then any O_{i+1} with O_i <= O_{i+1}
    must also authorize the packet as AuthorizedFresh.
    """
    scenario = {"packet": packet, "observers": list(poset_chain)}
    eval_results = evaluate_freshness(scenario)
    auth_flags = [r["authorized"] for r in eval_results]

    violations: list[str] = []
    for i in range(len(auth_flags) - 1):
        if auth_flags[i] and not auth_flags[i + 1]:
            obs_curr = poset_chain[i].get("observer_id")
            obs_next = poset_chain[i + 1].get("observer_id")
            violations.append(
                f"Monotonicity violation: {obs_curr} authorized packet but less stringent observer {obs_next} refused"
            )

    return (len(violations) == 0, violations)


def verify_loss_ledger_integrity(loss_ledger: Mapping[str, Any]) -> tuple[bool, str | None]:
    """Verifies that a declared LossLedger is cryptographically sealed and untampered."""
    if not isinstance(loss_ledger, (dict, Mapping)):
        return False, "Loss ledger is not a dictionary"

    erased = loss_ledger.get("erased_attributes")
    if not erased:
        return False, "Loss ledger has no declared erased attributes"

    entries = loss_ledger.get("entries")
    is_sealed_declared = loss_ledger.get("sealed") is True or loss_ledger.get("is_sealed") is True

    if is_sealed_declared and entries is None:
        return False, "Declared sealed loss ledger is missing entries"

    if entries is not None:
        rec_count = loss_ledger.get("record_count")
        if rec_count is None:
            return False, "Loss ledger has entries but missing mandatory record_count"
        if len(entries) != rec_count:
            return False, f"Record count mismatch: declared {rec_count}, actual {len(entries)}"

        merkle_digest = loss_ledger.get("merkle_digest") or loss_ledger.get("head_digest")
        if not merkle_digest:
            return (
                False,
                "Loss ledger is unsealed (mandatory cryptographic digest merkle_digest is missing)",
            )

        canonical_bytes = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
        expected_digest = hashlib.sha256(canonical_bytes).hexdigest()
        if merkle_digest != expected_digest:
            return False, f"Digest mismatch: declared {merkle_digest}, computed {expected_digest}"

    return True, None


def classify_defect_cocycle(
    discrepancies: Mapping[str, int], pending_compensations: Sequence[Mapping[str, Any]]
) -> tuple[str, str]:
    """Classifies reconciliation discrepancy into terminal route and obstruction class."""
    if not discrepancies:
        return "Preserve", "[0]"

    comp_sums: dict[str, int] = {}
    for c in pending_compensations:
        key = f"{c.get('account_id')}:{c.get('currency', 'USD')}"
        comp_sums[key] = comp_sums.get(key, 0) + c.get("amount_cents", 0)

    is_exact_coboundary = True
    for k, diff in discrepancies.items():
        if comp_sums.get(k, 0) != diff:
            is_exact_coboundary = False
            break

    if is_exact_coboundary and len(discrepancies) == len(comp_sums):
        return "Repair", "[0]"

    return "Refuse", "[NonZero - UnreconciledDiscrepancy]"


def _target_verifier_failure(case_id: Any, verifier: Any) -> dict[str, Any] | None:
    if isinstance(verifier, str):
        return {
            "case_id": case_id,
            "decision": "NotAuthorized",
            "terminal_route": "MissingVerifier",
            "obstruction_class": "[NonZero - UnauthenticatedVerifierString]",
            "repair": None,
            "certified": False,
            "authorized": False,
            "reconciled": False,
            "reason": f"Target verifier '{verifier}' is a bare string claim; authenticated execution record is required.",
        }
    outcome = (verifier or {}).get("outcome")
    if outcome == "pending":
        return {
            "case_id": case_id,
            "decision": "NotAuthorized",
            "terminal_route": "AuthorityLaundering",
            "obstruction_class": "[0]",
            "repair": None,
            "certified": True,
            "authorized": False,
            "reconciled": False,
            "reason": "Morphism has valid structure but active target verifier has not completed verification.",
        }
    if outcome != "verified":
        return {
            "case_id": case_id,
            "decision": "NotAuthorized",
            "terminal_route": "MissingVerifier",
            "obstruction_class": "[NonZero - MissingVerifier]",
            "repair": None,
            "certified": False,
            "authorized": False,
            "reconciled": False,
            "reason": "No policy verifier is associated with target domain state.",
        }
    return None


def _loss_ledger_failure(
    case_id: Any, morphism: Mapping[str, Any], loss_ledger: Any
) -> dict[str, Any] | None:
    if morphism.get("kind", "") != "quotient_projection":
        return None
    if not loss_ledger or not loss_ledger.get("erased_attributes"):
        return {
            "case_id": case_id,
            "decision": "NotAuthorized",
            "terminal_route": "LossLedgerMissing",
            "obstruction_class": "[NonZero - MissingLossLedger]",
            "repair": None,
            "certified": False,
            "authorized": False,
            "reconciled": False,
            "reason": "Lossy quotient projection erases attributes without a declared, sealed LossLedger.",
        }
    ok, error = verify_loss_ledger_integrity(loss_ledger)
    if ok:
        return None
    return {
        "case_id": case_id,
        "decision": "NotAuthorized",
        "terminal_route": "LossLedgerTampered",
        "obstruction_class": "[NonZero - TamperedLossLedger]",
        "repair": None,
        "certified": False,
        "authorized": False,
        "reconciled": False,
        "reason": f"Loss ledger failed cryptographic seal verification: {error}",
    }


def _aggregate_amounts(records: Sequence[Mapping[str, Any]], field: str) -> dict[str, int]:
    totals: dict[str, int] = {}
    for record in records:
        key = f"{record.get('account_id')}:{record.get('currency', 'USD')}"
        totals[key] = totals.get(key, 0) + record.get(field, 0)
    return totals


def _index_balances(records: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    return {
        f"{record.get('account_id')}:{record.get('currency', 'USD')}": record.get(
            "balance_cents", 0
        )
        for record in records
    }


def _balance_discrepancies(
    projected: Mapping[str, int], target: Mapping[str, int]
) -> dict[str, int]:
    return {
        key: target.get(key, 0) - projected.get(key, 0)
        for key in set(projected).union(target)
        if target.get(key, 0) - projected.get(key, 0) != 0
    }


def evaluate_reconciliation(case: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluates cross-domain reconciliation morphism under Boundary-Quotient Normal Form (BQNF)."""
    case_id = case.get("case_id", "unknown")
    verifier_failure = _target_verifier_failure(case_id, case.get("target_verifier"))
    if verifier_failure is not None:
        return verifier_failure

    # 2. Loss Ledger Check
    morphism = case.get("morphism", {})
    ledger_failure = _loss_ledger_failure(case_id, morphism, case.get("loss_ledger"))
    if ledger_failure is not None:
        return ledger_failure

    # 3. Bidirectional Morphism & Boundary Defect Evaluation
    source_records = morphism.get("source_records", [])
    target_state = morphism.get("target_state", [])
    pending_compensations = morphism.get("pending_compensations", [])

    # Forward projection F: aggregate ledger transactions by (account_id, currency)
    projected = _aggregate_amounts(source_records, "amount_cents")

    # Target state B: indexed by (account_id, currency)
    target_balances = _index_balances(target_state)

    # Discrepancy cochain Delta = Target - Projected
    discrepancies = _balance_discrepancies(projected, target_balances)
    return _reconciliation_outcome(case_id, discrepancies, pending_compensations, target_balances)


def _reconciliation_outcome(
    case_id: Any,
    discrepancies: Mapping[str, int],
    pending_compensations: Sequence[Mapping[str, Any]],
    target_balances: Mapping[str, int],
) -> dict[str, Any]:
    if not discrepancies:
        return _exact_reconciliation(case_id)
    comp_sums = _aggregate_amounts(pending_compensations, "amount_cents")
    exact = all(comp_sums.get(key, 0) == diff for key, diff in discrepancies.items())
    if exact and len(discrepancies) == len(comp_sums):
        return _repaired_reconciliation(case_id, pending_compensations, target_balances)
    return _refused_reconciliation(case_id, discrepancies)


def _exact_reconciliation(case_id: Any) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "decision": "Authorized",
        "terminal_route": "Preserve",
        "obstruction_class": "[0]",
        "repair": None,
        "certified": True,
        "authorized": True,
        "reconciled": True,
        "reason": "Bidirectional reconciliation commute is exact with zero obstruction.",
    }


def _repaired_reconciliation(
    case_id: Any,
    pending_compensations: Sequence[Mapping[str, Any]],
    target_balances: Mapping[str, int],
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "decision": "Authorized",
        "terminal_route": "Repair",
        "obstruction_class": "[0]",
        "repair": {
            "compensating_cochains": pending_compensations,
            "reconciled_balances": target_balances,
        },
        "certified": True,
        "authorized": True,
        "reconciled": True,
        "reason": "Defect cochain is coboundary exact; resolved via verified compensating witness.",
    }


def _refused_reconciliation(case_id: Any, discrepancies: Mapping[str, int]) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "decision": "NotAuthorized",
        "terminal_route": "Refuse",
        "obstruction_class": "[NonZero - UnreconciledDiscrepancy]",
        "repair": None,
        "certified": False,
        "authorized": False,
        "reconciled": False,
        "discrepancies": discrepancies,
        "reason": f"Morphism exhibits non-trivial homological obstruction across accounts: {list(discrepancies.keys())}.",
    }
