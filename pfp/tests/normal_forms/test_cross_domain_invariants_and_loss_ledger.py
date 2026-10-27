"""Targeted unit and property tests for Cross-Domain Reconciliation Invariants, Sealed Loss Ledgers, and Target Verifier Precedence.

AuthorityEffect: None.

Tests:
1. Bidirectional Defect Cocycle Classification:
   - Delta == 0 -> Preserve ([0])
   - Delta == d(alpha) -> Repair ([0])
   - Delta != d(alpha) -> Refuse ([NonZero - UnreconciledDiscrepancy])
2. Sealed Loss Ledger Cryptographic Verification:
   - Untampered ledger with valid SHA-256 digest is admitted.
   - Missing or empty loss ledger on quotient projection fails closed to LossLedgerMissing.
   - Mutated payload entry trips SHA-256 digest mismatch -> LossLedgerTampered.
   - Truncated tail entry trips record count mismatch -> LossLedgerTampered.
3. Target Verifier Precedence:
   - Pending verifier blocks authority -> AuthorityLaundering.
   - Missing/unregistered verifier blocks authority -> MissingVerifier.
   - Verified target state grants active authorization.
"""

from __future__ import annotations

import hashlib
import json
import unittest
from typing import Any, Dict

from pfp.domain.normal_forms.reconciliation import (
    classify_defect_cocycle,
    evaluate_reconciliation,
    verify_loss_ledger_integrity,
)


class TestCrossDomainDefectCocycle(unittest.TestCase):
    """Verifies homological classification of reconciliation discrepancies (Demo 04)."""

    def test_zero_defect_preserves(self) -> None:
        """When discrepancy is empty, classify_defect_cocycle returns Preserve with [0]."""
        route, obstruction = classify_defect_cocycle({}, [])
        self.assertEqual(route, "Preserve")
        self.assertEqual(obstruction, "[0]")

    def test_exact_coboundary_repair(self) -> None:
        """When discrepancies match pending compensating cochains exactly, returns Repair with [0]."""
        discrepancies = {
            "acc_101:USD": 5000,
            "acc_102:USD": -5000,
        }
        compensations = [
            {"account_id": "acc_101", "currency": "USD", "amount_cents": 5000},
            {"account_id": "acc_102", "currency": "USD", "amount_cents": -5000},
        ]
        route, obstruction = classify_defect_cocycle(discrepancies, compensations)
        self.assertEqual(route, "Repair")
        self.assertEqual(obstruction, "[0]")

    def test_unreconciled_cycle_obstruction_refusal(self) -> None:
        """When discrepancy does not match compensations, returns Refuse with non-zero obstruction."""
        discrepancies = {
            "acc_101:USD": 5000,
            "acc_102:USD": -3000,  # 2000 cents phantom imbalance
        }
        compensations = [
            {"account_id": "acc_101", "currency": "USD", "amount_cents": 5000},
            {"account_id": "acc_102", "currency": "USD", "amount_cents": -5000},
        ]
        route, obstruction = classify_defect_cocycle(discrepancies, compensations)
        self.assertEqual(route, "Refuse")
        self.assertEqual(obstruction, "[NonZero - UnreconciledDiscrepancy]")


class TestSealedLossLedgerTamperFalsification(unittest.TestCase):
    """Verifies cryptographic integrity and tamper/truncation detection for LossLedger."""

    def _make_valid_loss_ledger(self) -> Dict[str, Any]:
        entries = [
            {"tx_id": "tx_001", "nonce": 1001, "audit_tag": "tag_a"},
            {"tx_id": "tx_002", "nonce": 1002, "audit_tag": "tag_b"},
            {"tx_id": "tx_003", "nonce": 1003, "audit_tag": "tag_c"},
        ]
        canonical_bytes = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
        digest = hashlib.sha256(canonical_bytes).hexdigest()
        return {
            "ledger_id": "ledger_custody_001",
            "source_domain": "tx_ledger_prod",
            "target_domain": "analytics_daily",
            "erased_attributes": ["tx_id", "nonce", "audit_tag"],
            "record_count": 3,
            "merkle_digest": digest,
            "entries": entries,
        }

    def test_valid_loss_ledger_integrity(self) -> None:
        ledger = self._make_valid_loss_ledger()
        ok, err = verify_loss_ledger_integrity(ledger)
        self.assertTrue(ok)
        self.assertIsNone(err)

    def test_missing_erased_attributes_fails_closed(self) -> None:
        ledger = self._make_valid_loss_ledger()
        ledger["erased_attributes"] = []
        ok, err = verify_loss_ledger_integrity(ledger)
        self.assertFalse(ok)
        self.assertIn("no declared erased attributes", str(err))

    def test_payload_tampering_trips_digest_mismatch(self) -> None:
        ledger = self._make_valid_loss_ledger()
        # Mutate one entry
        ledger["entries"][0]["nonce"] = 9999
        ok, err = verify_loss_ledger_integrity(ledger)
        self.assertFalse(ok)
        self.assertIn("Digest mismatch", str(err))

    def test_tail_truncation_trips_record_count_mismatch(self) -> None:
        ledger = self._make_valid_loss_ledger()
        # Truncate one entry without updating record_count
        ledger["entries"].pop()
        ok, err = verify_loss_ledger_integrity(ledger)
        self.assertFalse(ok)
        self.assertIn("Record count mismatch", str(err))

    def test_evaluate_reconciliation_tampered_ledger_fails_closed(self) -> None:
        ledger = self._make_valid_loss_ledger()
        ledger["entries"][1]["tx_id"] = "tampered_id"

        case = {
            "case_id": "case_tampered_ledger",
            "target_verifier": {"outcome": "verified"},
            "morphism": {
                "kind": "quotient_projection",
                "source_records": [{"account_id": "acc_1", "currency": "USD", "amount_cents": 100}],
                "target_state": [{"account_id": "acc_1", "currency": "USD", "balance_cents": 100}],
            },
            "loss_ledger": ledger,
        }
        res = evaluate_reconciliation(case)
        self.assertFalse(res["authorized"])
        self.assertEqual(res["terminal_route"], "LossLedgerTampered")
        self.assertEqual(res["obstruction_class"], "[NonZero - TamperedLossLedger]")


class TestTargetVerifierPrecedenceAndAuthorityLaundering(unittest.TestCase):
    """Verifies that target domain authority strictly requires an independent, verified target verifier."""

    def test_pending_target_verifier_triggers_authority_laundering(self) -> None:
        case = {
            "case_id": "case_pending_verifier",
            "target_verifier": {"outcome": "pending"},
            "morphism": {
                "kind": "direct_transport",
                "source_records": [{"account_id": "acc_1", "currency": "USD", "amount_cents": 100}],
                "target_state": [{"account_id": "acc_1", "currency": "USD", "balance_cents": 100}],
            },
        }
        res = evaluate_reconciliation(case)
        self.assertFalse(res["authorized"])
        self.assertEqual(res["terminal_route"], "AuthorityLaundering")
        self.assertEqual(res["decision"], "NotAuthorized")

    def test_missing_target_verifier_triggers_missing_verifier(self) -> None:
        case = {
            "case_id": "case_missing_verifier",
            "target_verifier": {"outcome": "absent"},
            "morphism": {
                "kind": "direct_transport",
                "source_records": [{"account_id": "acc_1", "currency": "USD", "amount_cents": 100}],
                "target_state": [{"account_id": "acc_1", "currency": "USD", "balance_cents": 100}],
            },
        }
        res = evaluate_reconciliation(case)
        self.assertFalse(res["authorized"])
        self.assertEqual(res["terminal_route"], "MissingVerifier")
        self.assertEqual(res["decision"], "NotAuthorized")

    def test_verified_target_verifier_grants_authorization(self) -> None:
        case = {
            "case_id": "case_verified_verifier",
            "target_verifier": {"outcome": "verified"},
            "morphism": {
                "kind": "direct_transport",
                "source_records": [{"account_id": "acc_1", "currency": "USD", "amount_cents": 100}],
                "target_state": [{"account_id": "acc_1", "currency": "USD", "balance_cents": 100}],
            },
        }
        res = evaluate_reconciliation(case)
        self.assertTrue(res["authorized"])
        self.assertEqual(res["terminal_route"], "Preserve")
        self.assertEqual(res["decision"], "Authorized")


if __name__ == "__main__":
    unittest.main()
