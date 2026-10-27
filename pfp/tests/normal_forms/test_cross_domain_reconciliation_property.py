"""Targeted property tests for Cross-Domain Reconciliation and Obstruction Class Certificates (Demo 04).

Tests:
1. Canonical fixtures verification (all 5 cases in data/cross_domain_reconciliation.json)
2. Zero-obstruction exact commute property (Preserve, [0])
3. Exact coboundary defect repairability property (Repair, [0])
4. Unreconciled homological obstruction rejection property (Refuse, [NonZero - UnreconciledDiscrepancy])
5. Missing LossLedger fail-closed enforcement (LossLedgerMissing, [NonZero - MissingLossLedger])
6. Target verifier authority gate precedence (AuthorityLaundering / MissingVerifier)

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib.util
import json
import random
import unittest
from pathlib import Path
from typing import Dict

_EDU_ROOT = next(
    p / "education"
    for p in Path(__file__).resolve().parents
    if (p / "education/documentation/014_normal_forms").is_dir()
)
_CANDIDATE_DIRS = [
    _EDU_ROOT / "documentation" / "014_normal_forms" / "demos",
    _EDU_ROOT / "curriculum" / "normal_forms",
    _EDU_ROOT / "normal_forms",
]
_NORMAL_FORMS_DIR = next((d for d in _CANDIDATE_DIRS if d.is_dir()), _CANDIDATE_DIRS[0])
_RECON_SCRIPT_PATH = _NORMAL_FORMS_DIR / "04-cross-domain-reconciliation.py"
if not _RECON_SCRIPT_PATH.is_file():
    _fallback_recon = (
        _NORMAL_FORMS_DIR.parent.parent
        / "normal_forms"
        / "examples"
        / "04-cross-domain-reconciliation.py"
    )
    if _fallback_recon.is_file():
        _RECON_SCRIPT_PATH = _fallback_recon

_DATA_PATH = _NORMAL_FORMS_DIR / "data" / "cross_domain_reconciliation.json"
if not _DATA_PATH.is_file():
    _fallback_data = (
        _NORMAL_FORMS_DIR.parent.parent
        / "normal_forms"
        / "examples"
        / "data"
        / "cross_domain_reconciliation.json"
    )
    if _fallback_data.is_file():
        _DATA_PATH = _fallback_data


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


recon_mod = _load_module(_RECON_SCRIPT_PATH, "recon_eval_module")
evaluate_reconciliation = recon_mod.evaluate_reconciliation


class TestCrossDomainReconciliationProperties(unittest.TestCase):
    """Property tests asserting cross-domain transport and obstruction class certificates."""

    def test_canonical_reconciliation_fixtures(self) -> None:
        """Verify all 5 canonical fixtures in data/cross_domain_reconciliation.json."""
        self.assertTrue(_DATA_PATH.is_file())
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            cases = json.load(f)

        self.assertEqual(len(cases), 5)

        # Case 1: Exact reconciliation -> Preserve (Authorized)
        res1 = evaluate_reconciliation(cases[0])
        self.assertEqual(res1["decision"], "Authorized")
        self.assertEqual(res1["terminal_route"], "Preserve")
        self.assertEqual(res1["obstruction_class"], "[0]")
        self.assertTrue(res1["reconciled"])
        self.assertTrue(res1["authorized"])

        # Case 2: Exact coboundary defect -> Repair (Authorized)
        res2 = evaluate_reconciliation(cases[1])
        self.assertEqual(res2["decision"], "Authorized")
        self.assertEqual(res2["terminal_route"], "Repair")
        self.assertEqual(res2["obstruction_class"], "[0]")
        self.assertTrue(res2["reconciled"])
        self.assertTrue(res2["authorized"])
        self.assertIsNotNone(res2["repair"])

        # Case 3: Homological cycle obstruction -> Refuse (NotAuthorized)
        res3 = evaluate_reconciliation(cases[2])
        self.assertEqual(res3["decision"], "NotAuthorized")
        self.assertEqual(res3["terminal_route"], "Refuse")
        self.assertEqual(res3["obstruction_class"], "[NonZero - UnreconciledDiscrepancy]")
        self.assertFalse(res3["reconciled"])
        self.assertFalse(res3["authorized"])

        # Case 4: Missing Loss Ledger -> LossLedgerMissing (NotAuthorized)
        res4 = evaluate_reconciliation(cases[3])
        self.assertEqual(res4["decision"], "NotAuthorized")
        self.assertEqual(res4["terminal_route"], "LossLedgerMissing")
        self.assertEqual(res4["obstruction_class"], "[NonZero - MissingLossLedger]")
        self.assertFalse(res4["reconciled"])
        self.assertFalse(res4["authorized"])

        # Case 5: Target verifier pending -> AuthorityLaundering (NotAuthorized)
        res5 = evaluate_reconciliation(cases[4])
        self.assertEqual(res5["decision"], "NotAuthorized")
        self.assertEqual(res5["terminal_route"], "AuthorityLaundering")
        self.assertTrue(res5["certified"])
        self.assertFalse(res5["authorized"])
        self.assertFalse(res5["reconciled"])

    def test_zero_obstruction_exact_commute_property(self) -> None:
        """Property: When target balances exactly equal projected source balances, obstruction is [0] and routes to Preserve."""
        rng = random.Random(101)
        for seed in range(50):
            accounts = [f"ACC_{seed}_{i}" for i in range(4)]
            source_records = []
            target_balances: Dict[str, int] = {acc: 0 for acc in accounts}

            for acc in accounts:
                for tx_idx in range(rng.randint(1, 5)):
                    amt = rng.randint(-50000, 100000)
                    source_records.append(
                        {
                            "account_id": acc,
                            "amount_cents": amt,
                            "currency": "USD",
                            "tx_id": f"TX_{acc}_{tx_idx}",
                            "audit_nonce": f"nonce_{rng.randint(1000, 9999)}",
                        }
                    )
                    target_balances[acc] += amt

            target_state = [
                {"account_id": acc, "balance_cents": bal, "currency": "USD"}
                for acc, bal in target_balances.items()
            ]

            case = {
                "case_id": f"prop_zero_obs_{seed}",
                "source_domain": "relational_ledger",
                "target_domain": "balance_sheet_summary",
                "morphism": {
                    "morphism_id": f"morph_zero_{seed}",
                    "kind": "quotient_projection",
                    "source_records": source_records,
                    "target_state": target_state,
                },
                "loss_ledger": {
                    "ledger_id": f"loss_{seed}",
                    "erased_attributes": ["tx_id", "audit_nonce"],
                },
                "target_verifier": {"outcome": "verified"},
            }

            res = evaluate_reconciliation(case)
            self.assertEqual(res["decision"], "Authorized")
            self.assertEqual(res["terminal_route"], "Preserve")
            self.assertEqual(res["obstruction_class"], "[0]")
            self.assertTrue(res["reconciled"])
            self.assertTrue(res["authorized"])

    def test_exact_coboundary_repair_property(self) -> None:
        """Property: When target discrepancy equals pending compensating witnesses, routes to Repair with obstruction [0]."""
        rng = random.Random(202)
        for seed in range(50):
            acc = f"ACC_REP_{seed}"
            base_amt = rng.randint(10000, 50000)
            pending_amt = rng.randint(5000, 25000)

            source_records = [
                {
                    "account_id": acc,
                    "amount_cents": base_amt,
                    "currency": "USD",
                    "tx_id": "tx_base",
                    "audit_nonce": "n0",
                }
            ]
            # Target includes pending amount
            target_state = [
                {"account_id": acc, "balance_cents": base_amt + pending_amt, "currency": "USD"}
            ]
            pending_compensations = [
                {
                    "account_id": acc,
                    "amount_cents": pending_amt,
                    "currency": "USD",
                    "witness_ref": f"W_{seed}",
                }
            ]

            case = {
                "case_id": f"prop_repair_{seed}",
                "source_domain": "relational_ledger",
                "target_domain": "balance_sheet_summary",
                "morphism": {
                    "morphism_id": f"morph_rep_{seed}",
                    "kind": "quotient_projection",
                    "source_records": source_records,
                    "target_state": target_state,
                    "pending_compensations": pending_compensations,
                },
                "loss_ledger": {
                    "ledger_id": f"loss_rep_{seed}",
                    "erased_attributes": ["tx_id", "audit_nonce"],
                },
                "target_verifier": {"outcome": "verified"},
            }

            res = evaluate_reconciliation(case)
            self.assertEqual(res["decision"], "Authorized")
            self.assertEqual(res["terminal_route"], "Repair")
            self.assertEqual(res["obstruction_class"], "[0]")
            self.assertTrue(res["reconciled"])
            self.assertTrue(res["authorized"])
            self.assertIn("compensating_cochains", res["repair"])

    def test_unreconciled_homological_obstruction_property(self) -> None:
        """Property: When target discrepancy does not match compensations, fails closed to Refuse with non-zero obstruction."""
        rng = random.Random(303)
        for seed in range(50):
            acc = f"ACC_OBS_{seed}"
            base_amt = rng.randint(10000, 50000)
            target_diff = rng.randint(1000, 9999)
            comp_amt = target_diff + rng.choice([-500, 500, 1000])  # Mismatch

            case = {
                "case_id": f"prop_obs_{seed}",
                "source_domain": "relational_ledger",
                "target_domain": "balance_sheet_summary",
                "morphism": {
                    "morphism_id": f"morph_obs_{seed}",
                    "kind": "quotient_projection",
                    "source_records": [
                        {
                            "account_id": acc,
                            "amount_cents": base_amt,
                            "currency": "USD",
                            "tx_id": "tx1",
                            "audit_nonce": "n1",
                        }
                    ],
                    "target_state": [
                        {
                            "account_id": acc,
                            "balance_cents": base_amt + target_diff,
                            "currency": "USD",
                        }
                    ],
                    "pending_compensations": [
                        {"account_id": acc, "amount_cents": comp_amt, "currency": "USD"}
                    ],
                },
                "loss_ledger": {
                    "ledger_id": f"loss_{seed}",
                    "erased_attributes": ["tx_id", "audit_nonce"],
                },
                "target_verifier": {"outcome": "verified"},
            }

            res = evaluate_reconciliation(case)
            self.assertEqual(res["decision"], "NotAuthorized")
            self.assertEqual(res["terminal_route"], "Refuse")
            self.assertEqual(res["obstruction_class"], "[NonZero - UnreconciledDiscrepancy]")
            self.assertFalse(res["reconciled"])
            self.assertFalse(res["authorized"])
            self.assertIn(f"{acc}:USD", res["discrepancies"])

    def test_missing_loss_ledger_fails_closed(self) -> None:
        """Property: Omitting loss ledger from a lossy quotient projection fails closed to LossLedgerMissing."""
        bad_ledgers = [
            None,
            {},
            {"ledger_id": "incomplete", "erased_attributes": []},
        ]
        for bad_ll in bad_ledgers:
            case = {
                "case_id": "prop_bad_loss_ledger",
                "source_domain": "relational_ledger",
                "target_domain": "balance_sheet_summary",
                "morphism": {
                    "kind": "quotient_projection",
                    "source_records": [
                        {
                            "account_id": "A1",
                            "amount_cents": 100,
                            "currency": "USD",
                            "tx_id": "t1",
                            "audit_nonce": "n1",
                        }
                    ],
                    "target_state": [{"account_id": "A1", "balance_cents": 100, "currency": "USD"}],
                },
                "loss_ledger": bad_ll,
                "target_verifier": {"outcome": "verified"},
            }
            res = evaluate_reconciliation(case)
            self.assertEqual(res["decision"], "NotAuthorized")
            self.assertEqual(res["terminal_route"], "LossLedgerMissing")
            self.assertEqual(res["obstruction_class"], "[NonZero - MissingLossLedger]")
            self.assertFalse(res["reconciled"])
            self.assertFalse(res["authorized"])

    def test_target_verifier_precedence_gate(self) -> None:
        """Property: Any non-verified target verifier outcome prevents authorization."""
        outcomes = ["pending", None, "rejected", "failed", "untrusted", "unknown"]
        for outcome in outcomes:
            case = {
                "case_id": f"prop_verifier_{outcome}",
                "source_domain": "relational_ledger",
                "target_domain": "balance_sheet_summary",
                "morphism": {
                    "kind": "quotient_projection",
                    "source_records": [
                        {
                            "account_id": "A1",
                            "amount_cents": 100,
                            "currency": "USD",
                            "tx_id": "t1",
                            "audit_nonce": "n1",
                        }
                    ],
                    "target_state": [{"account_id": "A1", "balance_cents": 100, "currency": "USD"}],
                },
                "loss_ledger": {"erased_attributes": ["tx_id", "audit_nonce"]},
                "target_verifier": {"outcome": outcome},
            }
            res = evaluate_reconciliation(case)
            self.assertEqual(res["decision"], "NotAuthorized")
            self.assertFalse(res["authorized"])
            if outcome == "pending":
                self.assertEqual(res["terminal_route"], "AuthorityLaundering")
            else:
                self.assertEqual(res["terminal_route"], "MissingVerifier")


if __name__ == "__main__":
    unittest.main()
