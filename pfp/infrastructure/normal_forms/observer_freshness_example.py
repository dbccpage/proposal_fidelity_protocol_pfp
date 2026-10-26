# ==============================================================================
# Specification: 03-observer-relative-freshness.md
# ==============================================================================
"""
================================================================================
03-observer-relative-freshness.md
================================================================================

# Demo 03: Observer-Relative Freshness

Status: Mechanization target.

Freshness timestamp != freshness authority.

Example packet:

```yaml
value_ref: paid_revenue_by_customer:customer_42
observer: dashboard_region_us_east
read_timestamp: "2026-05-19T12:00:00Z"
source_epoch: cdc_lsn_10042
replica_lag_ms: 250
cache_age_ms: 1000
invalidation_status: fresh
freshness_sla_ms: 5000
terminal_route: Preserve
authorization_status: certified_not_authorized
```

Required outcomes:

| Case | Required terminal |
|---|---|
| timestamp present but invalidation status unknown | `BudgetUnknown` or `ConservativeInvalidate` |
| cache age exceeds SLA | `Invalidate` |
| observer reads outside declared replica scope | `Refuse` |
| freshness packet verifies but policy verifier absent | certified, not authorized |

Non-claims:

* Does not prove the value is correct.
* Does not authorize action.
* Does not replace BQNF repair.

AuthorityEffect: None.
"""

import json
import os

from omega_engine_pfp.infrastructure.normal_forms.contract_paths import NORMAL_FORMS_DIR
from typing import Any, Dict, List

# Load the observers configuration from JSON
DATA_PATH = NORMAL_FORMS_DIR / "data" / "observers.json"


def evaluate_freshness(scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
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

    results = []

    # Check 1: Explicit Packet Scope requirement (Fail closed, no defaulting to public)
    if packet_scope is None or not isinstance(packet_scope, str) or not packet_scope.strip():
        for observer in observers:
            observer_id = observer.get("observer_id", "unknown")
            results.append(
                {
                    "observer_id": observer_id,
                    "terminal_route": "Refuse",
                    "authorized": False,
                    "reason": "Packet scope is missing or malformed; freshness evaluation fails closed without explicit scope.",
                }
            )
        return results

    # Check 2: Explicit Replica Lag requirement (Fail closed, no defaulting)
    if lag is None or not isinstance(lag, (int, float)) or lag < 0:
        for observer in observers:
            observer_id = observer.get("observer_id", "unknown")
            results.append(
                {
                    "observer_id": observer_id,
                    "terminal_route": "ConservativeInvalidate",
                    "authorized": False,
                    "reason": "Replica lag is missing or null or malformed; unable to verify SLA budget.",
                }
            )
        return results

    for observer in observers:
        observer_id = observer.get("observer_id", "unknown")
        max_lag = observer.get("max_lag_seconds")
        auth_scopes = observer.get("authorized_scopes")

        # Check 3: Explicit Observer Scopes requirement
        if auth_scopes is None or not isinstance(auth_scopes, (list, tuple, set)):
            results.append(
                {
                    "observer_id": observer_id,
                    "terminal_route": "Refuse",
                    "authorized": False,
                    "reason": f"Observer '{observer_id}' has missing or malformed authorized_scopes.",
                }
            )
            continue

        # Check 4: Observer max_lag requirement
        if max_lag is None or not isinstance(max_lag, (int, float)) or max_lag < 0:
            results.append(
                {
                    "observer_id": observer_id,
                    "terminal_route": "ConservativeInvalidate",
                    "authorized": False,
                    "reason": f"Observer '{observer_id}' has missing or invalid max_lag_seconds ({max_lag}).",
                }
            )
            continue

        # Check 5: Scope Authorization Check
        if packet_scope not in auth_scopes:
            results.append(
                {
                    "observer_id": observer_id,
                    "terminal_route": "Refuse",
                    "authorized": False,
                    "reason": f"Observer is not authorized for packet scope: '{packet_scope}'.",
                }
            )
            continue

        # Check 6: SLA Budget Check
        if lag <= max_lag:
            results.append(
                {
                    "observer_id": observer_id,
                    "terminal_route": "AuthorizedFresh",
                    "authorized": True,
                    "reason": f"Replica lag ({lag}s) is within the observer's max limit ({max_lag}s).",
                }
            )
        else:
            results.append(
                {
                    "observer_id": observer_id,
                    "terminal_route": "RefreshRequired",
                    "authorized": False,
                    "reason": f"Replica lag ({lag}s) exceeds the observer's max limit ({max_lag}s).",
                }
            )

    return results


from dataclasses import dataclass
from typing import Sequence


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


def verify_observer_lattice_monotonicity(
    poset_chain: Sequence[Dict[str, Any]], packet: Dict[str, Any]
) -> tuple[bool, List[str]]:
    """Verifies that freshness authorization is a monotonic functor over an observer poset chain.
    If observer O_i authorizes the packet as AuthorizedFresh, then any O_{i+1} with O_i <= O_{i+1}
    must also authorize the packet as AuthorizedFresh.
    """
    scenario = {"packet": packet, "observers": list(poset_chain)}
    eval_results = evaluate_freshness(scenario)
    auth_flags = [r["authorized"] for r in eval_results]

    violations = []
    for i in range(len(auth_flags) - 1):
        if auth_flags[i] and not auth_flags[i + 1]:
            obs_curr = poset_chain[i].get("observer_id")
            obs_next = poset_chain[i + 1].get("observer_id")
            violations.append(
                f"Monotonicity violation: {obs_curr} authorized packet but less stringent observer {obs_next} refused"
            )

    return (len(violations) == 0, violations)


def main():
    print("================================================================================")
    print("DEMO 03: Observer-Relative Freshness SLA Bounds")
    print("================================================================================")

    if not os.path.exists(DATA_PATH):
        print(f"Error: Data file not found at {DATA_PATH}")
        return

    with open(DATA_PATH, "r") as f:
        scenarios = json.load(f)

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n--- Running Scenario {i}: {scenario.get('description')} ---")
        print("Input Packet Metadata:")
        print(json.dumps(scenario.get("packet"), indent=2))

        results = evaluate_freshness(scenario)

        print("\nObserver Resolutions:")
        print(json.dumps(results, indent=2))
        print("-" * 80)


if __name__ == "__main__":
    main()
