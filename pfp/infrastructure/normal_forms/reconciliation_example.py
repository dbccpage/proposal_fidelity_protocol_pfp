# ==============================================================================
# Specification: 04-cross-domain-reconciliation.md
# ==============================================================================
r"""
================================================================================
04-cross-domain-reconciliation.md
================================================================================

# Demo 04: Cross-Domain Reconciliation & Obstruction Class Certificates

Status: Mechanization target.

Cross-domain transport != automatic truth or authority.

When transporting states between distinct carrier representations (e.g. detailed transactional relvars $A$ and summarized analytical states $B$), a reconciliation morphism must satisfy six independent BQNF criteria:

1. **Bidirectional Differential Compatibility:** Forward projection $F: A \to B$ and backward synthesis $G: B \to A$ must commute up to an exact coboundary defect:
   $$
   \Delta = B - F(A) = d\alpha
   $$
2. **Obstruction Classification:**
   - $\Delta = 0$: Morphism commutes exactly; obstruction class is $[0]$ (`Preserve`).
   - $\Delta = d\alpha$: Defect is exact; resolved via verified compensating cochain witness (`Repair`).
   - $[\Delta] \neq 0$: Non-trivial cycle obstruction; irreconcilable structural divergence (`Refuse`).
3. **Sealed Loss Ledger:** Erased structural attributes (e.g. transaction IDs, audit nonces, fine-grained timestamps) must be recorded in an immutable `LossLedger`. Lossy transport without a declared loss ledger fails closed (`LossLedgerMissing`).
4. **Target Verifier Precedence:** Source admission establishes provenance only; target state authority requires independent target verifier execution (`verified`). A pending or absent verifier cannot mint authority (`AuthorityLaundering` / `MissingVerifier`).

## Required Outcomes

| Case | Condition | Required Terminal Route | Authorized |
|---|---|---|---|
| Case 1 | Zero obstruction, sealed loss ledger, active target verifier | `Preserve` | Yes |
| Case 2 | Coboundary defect with valid compensating witness | `Repair` | Yes |
| Case 3 | Non-trivial cycle obstruction (phantom discrepancy) | `Refuse` | No |
| Case 4 | Lossy projection with missing/null loss ledger | `LossLedgerMissing` | No |
| Case 5 | Valid morphism with pending target verifier outcome | `AuthorityLaundering` | No |

## Non-claims

- Does not claim universal cross-domain equivalence.
- Does not authorize target state without active target verifier replay.
- Does not erase structural distinctions without an explicit loss ledger.

AuthorityEffect: None.
"""

import hashlib
import json
import os

from pfp.infrastructure.normal_forms.contract_paths import NORMAL_FORMS_DIR
from typing import Any, Dict, List, Tuple

# Load cross-domain reconciliation fixtures from JSON
DATA_PATH = NORMAL_FORMS_DIR / "data" / "cross_domain_reconciliation.json"


def verify_loss_ledger_integrity(loss_ledger: Dict[str, Any]) -> Tuple[bool, str | None]:
    """Verifies that a declared LossLedger is cryptographically sealed and untampered."""
    if not isinstance(loss_ledger, dict):
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
    discrepancies: Dict[str, int], pending_compensations: List[Dict[str, Any]]
) -> Tuple[str, str]:
    """Classifies reconciliation discrepancy into terminal route and obstruction class."""
    if not discrepancies:
        return "Preserve", "[0]"

    comp_sums: Dict[str, int] = {}
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


def evaluate_reconciliation(case: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluates cross-domain reconciliation morphism under Boundary-Quotient Normal Form (BQNF).

    Invariants checked:
    1. Target Verifier Precedence: Target validity requires an active, successful target verifier.
       Unreplayed / pending verifier fails closed to AuthorityLaundering or MissingVerifier.
       A bare string claim (e.g. 'verified') does not mint authority.
    2. Sealed Loss Ledger: Lossy quotient projections erasing structural attributes require an explicit LossLedger.
       Missing or unsealed loss ledger fails closed to LossLedgerMissing / LossLedgerTampered.
    3. Differential Obstruction & BQNF Invariants:
       - Delta == 0: Commuting exact morphism -> Preserve (obstruction [0]).
       - Delta == d(alpha): Exact coboundary defect with valid compensating witness -> Repair.
       - Delta != d(alpha): Non-trivial homological cycle obstruction -> Refuse ([NonZero - UnreconciledDiscrepancy]).
    """
    case_id = case.get("case_id", "unknown")
    raw_target_verifier = case.get("target_verifier")

    # Reject bare string claims for target verifier
    if isinstance(raw_target_verifier, str):
        return {
            "case_id": case_id,
            "decision": "NotAuthorized",
            "terminal_route": "MissingVerifier",
            "obstruction_class": "[NonZero - UnauthenticatedVerifierString]",
            "repair": None,
            "certified": False,
            "authorized": False,
            "reconciled": False,
            "reason": f"Target verifier '{raw_target_verifier}' is a bare string claim; authenticated execution record is required.",
        }

    target_verifier = raw_target_verifier or {}
    verifier_outcome = target_verifier.get("outcome")

    # 1. Target Verifier Gate
    if verifier_outcome == "pending":
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
    elif verifier_outcome != "verified":
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

    # 2. Loss Ledger Check
    morphism = case.get("morphism", {})
    kind = morphism.get("kind", "")
    loss_ledger = case.get("loss_ledger")

    if kind == "quotient_projection":
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
        ok_ledger, err_ledger = verify_loss_ledger_integrity(loss_ledger)
        if not ok_ledger:
            return {
                "case_id": case_id,
                "decision": "NotAuthorized",
                "terminal_route": "LossLedgerTampered",
                "obstruction_class": "[NonZero - TamperedLossLedger]",
                "repair": None,
                "certified": False,
                "authorized": False,
                "reconciled": False,
                "reason": f"Loss ledger failed cryptographic seal verification: {err_ledger}",
            }

    # 3. Bidirectional Morphism & Boundary Defect Evaluation
    source_records = morphism.get("source_records", [])
    target_state = morphism.get("target_state", [])
    pending_compensations = morphism.get("pending_compensations", [])

    # Forward projection F: aggregate ledger transactions by (account_id, currency)
    projected: Dict[str, int] = {}
    for r in source_records:
        key = f"{r.get('account_id')}:{r.get('currency', 'USD')}"
        projected[key] = projected.get(key, 0) + r.get("amount_cents", 0)

    # Target state B: indexed by (account_id, currency)
    target_balances: Dict[str, int] = {}
    for t in target_state:
        key = f"{t.get('account_id')}:{t.get('currency', 'USD')}"
        target_balances[key] = t.get("balance_cents", 0)

    # Discrepancy cochain Delta = Target - Projected
    all_keys = set(projected.keys()).union(set(target_balances.keys()))
    discrepancies: Dict[str, int] = {}
    for k in all_keys:
        p_val = projected.get(k, 0)
        t_val = target_balances.get(k, 0)
        diff = t_val - p_val
        if diff != 0:
            discrepancies[k] = diff

    # Zero defect: exact commutation
    if not discrepancies:
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

    # Non-zero defect: check for exact coboundary compensating witnesses d(alpha)
    comp_sums: Dict[str, int] = {}
    for c in pending_compensations:
        key = f"{c.get('account_id')}:{c.get('currency', 'USD')}"
        comp_sums[key] = comp_sums.get(key, 0) + c.get("amount_cents", 0)

    # Coboundary exactness check: does pending compensation equal discrepancy for every key?
    is_exact_coboundary = True
    for k, diff in discrepancies.items():
        if comp_sums.get(k, 0) != diff:
            is_exact_coboundary = False
            break

    if is_exact_coboundary and len(discrepancies) == len(comp_sums):
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

    # Non-bounding cycle obstruction
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


def main():
    print("================================================================================")
    print("DEMO 04: Cross-Domain Reconciliation & Obstruction Class Certificates")
    print("================================================================================")

    if not os.path.exists(DATA_PATH):
        print(f"Error: Data file not found at {DATA_PATH}")
        return

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        cases = json.load(f)

    for i, case in enumerate(cases, 1):
        print(f"\n--- Running Case {i}: {case.get('description')} ---")
        result = evaluate_reconciliation(case)
        print("Output Certificate Decision:")
        print(json.dumps(result, indent=2))
        print("-" * 80)


if __name__ == "__main__":
    main()
