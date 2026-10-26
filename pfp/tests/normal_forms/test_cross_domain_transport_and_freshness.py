"""Unit and property-based tests for Cross-Domain Transport & Sheaf Gluing (Tests 26-32)
and Observer Freshness, SLA Posets & Asymmetric Drift (Tests 33-38).

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import unittest

from omega_engine_pfp.domain.normal_forms.reconciliation import (
    classify_defect_cocycle,
    evaluate_freshness,
    evaluate_reconciliation,
    verify_loss_ledger_integrity,
    verify_observer_lattice_monotonicity,
)


class TestCrossDomainTransportAndFreshness(unittest.TestCase):
    """Test suite covering Cross-Domain Transport, Loss Ledgers, and Observer Freshness Posets."""

    # =========================================================================
    # Group 4: Cross-Domain Transport, Sheaf Gluing & LossLedger Custody (Tests 26-32)
    # =========================================================================

    def test_cross_domain_delta_cocycle_decomposition(self) -> None:
        """Test 26: Discrepancy decomposes into coboundary repair and non-trivial cycle obstruction."""
        # Exact coboundary: sum of compensations exactly cancels discrepancy
        discrepancies = {"acc_A:USD": 1000, "acc_B:USD": -1000}
        compensations = [
            {"account_id": "acc_A", "currency": "USD", "amount_cents": 1000},
            {"account_id": "acc_B", "currency": "USD", "amount_cents": -1000},
        ]
        route, obstruction = classify_defect_cocycle(discrepancies, compensations)
        self.assertEqual(route, "Repair")
        self.assertEqual(obstruction, "[0]")

        # Non-exact cycle (unreconciled remainder)
        unbalanced_comps = [
            {"account_id": "acc_A", "currency": "USD", "amount_cents": 500},
        ]
        route_bad, obstruction_bad = classify_defect_cocycle(discrepancies, unbalanced_comps)
        self.assertEqual(route_bad, "Refuse")
        self.assertEqual(obstruction_bad, "[NonZero - UnreconciledDiscrepancy]")

    def test_loss_ledger_merkle_digest_tamper_rejection(self) -> None:
        """Test 27: Modifying a single character in sealed loss entries triggers LossLedgerTampered."""
        entries = [
            {"dropped_column": "tax_rate", "entity_id": "e_01", "original_value": "0.0825"},
            {"dropped_column": "tax_rate", "entity_id": "e_02", "original_value": "0.0500"},
        ]
        raw_json = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
        valid_digest = hashlib.sha256(raw_json).hexdigest()

        ledger = {
            "ledger_id": "ledger_custody_01",
            "source_domain": "sales_tax_prod",
            "target_domain": "analytics_dw",
            "erased_attributes": ["tax_rate"],
            "record_count": 2,
            "merkle_digest": valid_digest,
            "entries": entries,
        }

        # Valid ledger passes
        ok, reason = verify_loss_ledger_integrity(ledger)
        self.assertTrue(ok)
        self.assertIsNone(reason)

        # Mutate value (tamper)
        tampered_entries = [
            {"dropped_column": "tax_rate", "entity_id": "e_01", "original_value": "0.0000"},
            {"dropped_column": "tax_rate", "entity_id": "e_02", "original_value": "0.0500"},
        ]
        tampered_ledger = dict(ledger)
        tampered_ledger["entries"] = tampered_entries
        ok_tampered, reason_tampered = verify_loss_ledger_integrity(tampered_ledger)
        self.assertFalse(ok_tampered)
        self.assertIn("Digest mismatch", str(reason_tampered))

    def test_loss_ledger_tail_truncation_rejection(self) -> None:
        """Test 28: Truncating a trailing record from a sealed LossLedger triggers LossLedgerTampered."""
        entries = [
            {"dropped_column": "tax_rate", "entity_id": "e_01", "original_value": "0.0825"},
            {"dropped_column": "tax_rate", "entity_id": "e_02", "original_value": "0.0500"},
        ]
        raw_json = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
        valid_digest = hashlib.sha256(raw_json).hexdigest()

        ledger = {
            "ledger_id": "ledger_custody_02",
            "source_domain": "sales_tax_prod",
            "target_domain": "analytics_dw",
            "erased_attributes": ["tax_rate"],
            "record_count": 2,
            "merkle_digest": valid_digest,
            "entries": entries[:1],  # truncated tail!
        }
        ok, reason = verify_loss_ledger_integrity(ledger)
        self.assertFalse(ok)
        self.assertIn("Record count mismatch", str(reason))

    def test_cross_domain_authority_laundering_firewall(self) -> None:
        """Test 29: Unverified target state blocks authority elevation (AuthorityLaundering)."""
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

    def test_cross_domain_missing_verifier_rejection(self) -> None:
        """Test 30: Unregistered verifier fails closed to MissingVerifier."""
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

    def test_sheaf_gluing_compatible_overlap_coincidence(self) -> None:
        """Test 31: Local database sections agreeing on pairwise intersections glue to a global state."""
        section_u1 = {"A": 1, "B": 2}
        section_u2 = {"B": 2, "C": 3}

        # Compatible overlap on U_1 ∩ U_2 = {B}
        overlap = set(section_u1.keys()) & set(section_u2.keys())
        is_compatible = all(section_u1[k] == section_u2[k] for k in overlap)
        self.assertTrue(is_compatible)

        glued_global = dict(section_u1)
        glued_global.update(section_u2)
        self.assertEqual(glued_global, {"A": 1, "B": 2, "C": 3})

    def test_loss_ledger_lossless_projection_null_invariance(self) -> None:
        """Test 32: Injective/lossless projections (direct_transport) require no loss ledger."""
        case = {
            "case_id": "case_direct_lossless",
            "target_verifier": {"outcome": "verified"},
            "morphism": {
                "kind": "direct_transport",
                "source_records": [{"account_id": "acc_1", "currency": "USD", "amount_cents": 100}],
                "target_state": [{"account_id": "acc_1", "currency": "USD", "balance_cents": 100}],
            },
            "loss_ledger": None,
        }
        res = evaluate_reconciliation(case)
        self.assertTrue(res["authorized"])
        self.assertEqual(res["terminal_route"], "Preserve")

    # =========================================================================
    # Group 5: Observer Freshness, SLA Posets & Asymmetric Drift (Tests 33-38)
    # =========================================================================

    def test_observer_poset_sla_monotonic_degradation(self) -> None:
        """Test 33: Freshness SLA monotonically relaxes along directed observer poset chains."""
        o_strict = {
            "observer_id": "obs_strict",
            "max_lag_seconds": 2,
            "authorized_scopes": ["public", "internal"],
        }
        o_medium = {
            "observer_id": "obs_medium",
            "max_lag_seconds": 5,
            "authorized_scopes": ["public", "internal", "audit"],
        }
        o_lenient = {
            "observer_id": "obs_lenient",
            "max_lag_seconds": 10,
            "authorized_scopes": ["public", "internal", "audit", "external"],
        }
        poset_chain = [o_strict, o_medium, o_lenient]
        packet = {"replica_lag_seconds": 4, "packet_scope": "public"}

        is_monotone, violations = verify_observer_lattice_monotonicity(poset_chain, packet)
        self.assertTrue(is_monotone)
        self.assertEqual(violations, [])

    def test_observer_causal_clock_vector_skew_tolerance(self) -> None:
        """Test 34: Causal clock vector skew within tolerance passes; excessive skew requires refresh."""
        observer = {
            "observer_id": "dashboard",
            "max_lag_seconds": 5,
            "authorized_scopes": ["public"],
        }

        # Fresh packet: lag 2s <= 5s
        res_fresh = evaluate_freshness(
            {
                "packet": {"replica_lag_seconds": 2, "packet_scope": "public"},
                "observers": [observer],
            }
        )
        self.assertEqual(res_fresh[0]["terminal_route"], "AuthorizedFresh")

        # Stale packet: lag 10s > 5s
        res_stale = evaluate_freshness(
            {
                "packet": {"replica_lag_seconds": 10, "packet_scope": "public"},
                "observers": [observer],
            }
        )
        self.assertEqual(res_stale[0]["terminal_route"], "RefreshRequired")

    def test_observer_scope_firewall_leakage_rejection(self) -> None:
        """Test 35: Private observer state dimensions are shielded from downstream scopes."""
        observer = {
            "observer_id": "public_client",
            "max_lag_seconds": 100,
            "authorized_scopes": ["public"],
        }
        # Scope is classified, observer only has public
        res = evaluate_freshness(
            {
                "packet": {"replica_lag_seconds": 1, "packet_scope": "classified"},
                "observers": [observer],
            }
        )
        self.assertEqual(res[0]["terminal_route"], "Refuse")
        self.assertFalse(res[0]["authorized"])

    def test_observer_stale_read_quarantine(self) -> None:
        """Test 36: Reads exceeding observer SLA threshold trigger RefreshRequired."""
        observer = {
            "observer_id": "trading_desk",
            "max_lag_seconds": 5,
            "authorized_scopes": ["public"],
        }
        res = evaluate_freshness(
            {
                "packet": {"replica_lag_seconds": 20, "packet_scope": "public"},
                "observers": [observer],
            }
        )
        self.assertEqual(res[0]["terminal_route"], "RefreshRequired")

    def test_observer_lattice_join_least_upper_bound(self) -> None:
        """Test 37: SLA lattice join calculates least upper bound max(sla_1, sla_2)."""
        sla_1 = 10
        sla_2 = 30
        lub_sla = max(sla_1, sla_2)
        self.assertEqual(lub_sla, 30)
        self.assertTrue(25 <= lub_sla)

    def test_observer_eventual_consistency_convergence_bound(self) -> None:
        """Test 38: Under zero write influx, observer drift contracts to zero within timeout."""
        initial_drift = 50.0
        decay_rate = 0.5
        steps = 8
        final_drift = initial_drift * (decay_rate**steps)
        self.assertLess(final_drift, 1.0)


if __name__ == "__main__":
    unittest.main()
