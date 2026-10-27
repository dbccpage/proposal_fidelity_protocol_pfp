"""Targeted property tests for Boundary-Quotient Normal Form (BQNF) invariants.

Tests exact coboundary repairs, zero-defect preservation, compensating cochains,
customer partition conservation, and fail-closed missing evidence guards across
synthetic CDC event streams.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib.util
import json
import random
import unittest
from pathlib import Path
from typing import Any, Dict

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
_EVALUATOR_PATH = _NORMAL_FORMS_DIR / "01-bqnf-orders-paid-revenue.py"
if not _EVALUATOR_PATH.is_file():
    _fallback_eval = (
        _NORMAL_FORMS_DIR.parent.parent
        / "normal_forms"
        / "examples"
        / "01-bqnf-orders-paid-revenue.py"
    )
    if _fallback_eval.is_file():
        _EVALUATOR_PATH = _fallback_eval

_DATA_PATH = _NORMAL_FORMS_DIR / "data" / "cdc_events.json"
if not _DATA_PATH.is_file():
    _fallback_data = (
        _NORMAL_FORMS_DIR.parent.parent / "normal_forms" / "examples" / "data" / "cdc_events.json"
    )
    if _fallback_data.is_file():
        _DATA_PATH = _fallback_data


def _load_bqnf_evaluator():
    spec = importlib.util.spec_from_file_location("bqnf_orders_module", _EVALUATOR_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load evaluator from {_EVALUATOR_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.evaluate_bqnf


evaluate_bqnf = _load_bqnf_evaluator()


class TestBqnfCdcProperties(unittest.TestCase):
    """Property test suite asserting BQNF invariants on CDC event streams."""

    def setUp(self) -> None:
        self.boundary = {
            "relations": ["Orders"],
            "attributes": ["customer_id", "amount", "status"],
            "predicates": ["status = paid"],
            "groups": ["customer_id"],
            "aggregates": ["SUM(amount)"],
        }

    def test_canonical_fixtures_pass(self) -> None:
        """Verify all 6 canonical fixtures from data/cdc_events.json."""
        self.assertTrue(_DATA_PATH.is_file(), f"Missing {_DATA_PATH}")
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            cases = json.load(f)

        self.assertEqual(len(cases), 6)
        outcomes = [evaluate_bqnf(case) for case in cases]

        # Case 1: pending -> paid => Repair (+120)
        self.assertEqual(outcomes[0]["decision"], "Repair")
        self.assertEqual(outcomes[0]["repair"]["delta_revenue"], 120)
        self.assertTrue(outcomes[0]["certified"])

        # Case 2: paid -> paid (amount 100 -> 120) => Repair (+20)
        self.assertEqual(outcomes[1]["decision"], "Repair")
        self.assertEqual(outcomes[1]["repair"]["delta_revenue"], 20)
        self.assertTrue(outcomes[1]["certified"])

        # Case 3: paid -> pending (100 -> 100) => Repair (-100)
        self.assertEqual(outcomes[2]["decision"], "Repair")
        self.assertEqual(outcomes[2]["repair"]["delta_revenue"], -100)
        self.assertTrue(outcomes[2]["certified"])

        # Case 4: updated_at only change => Preserve (0)
        self.assertEqual(outcomes[3]["decision"], "Preserve")
        self.assertIsNone(outcomes[3]["repair"])
        self.assertTrue(outcomes[3]["certified"])

        # Case 5: Missing status and amount => Invalidate
        self.assertEqual(outcomes[4]["decision"], "Invalidate")
        self.assertFalse(outcomes[4]["evidence_sufficient"])
        self.assertFalse(outcomes[4]["certified"])

        # Case 6: Unsupported aggregate MAX => Unsupported
        self.assertEqual(outcomes[5]["decision"], "Unsupported")
        self.assertFalse(outcomes[5]["certified"])

    def test_zero_defect_preservation_property(self) -> None:
        """Property: If no boundary attribute changes, defect is zero and routes to Preserve."""
        rng = random.Random(42)
        for _ in range(50):
            customer_id = rng.randint(1, 100)
            amount = rng.randint(10, 1000)
            status = rng.choice(["pending", "paid", "cancelled", "refunded"])

            # Non-boundary modification (e.g., notes, updated_at, shipping_address)
            old_rec = {
                "order_id": 99,
                "customer_id": customer_id,
                "amount": amount,
                "status": status,
                "note": "v1",
            }
            new_rec = {
                "order_id": 99,
                "customer_id": customer_id,
                "amount": amount,
                "status": status,
                "note": "v2",
            }

            case = {
                "boundary": self.boundary,
                "event": {"op": "UPDATE", "relation": "Orders", "old": old_rec, "new": new_rec},
            }
            res = evaluate_bqnf(case)
            self.assertEqual(res["decision"], "Preserve")
            self.assertEqual(res["terminal_route"], "Preserve")
            self.assertEqual(res["obstruction_class"], "[0]")
            self.assertIsNone(res["repair"])
            self.assertTrue(res["certified"])

    def test_compensating_cochain_reversibility_property(self) -> None:
        """Property: For any forward transition e, the reversed transition -e has delta = -delta."""
        rng = random.Random(1337)
        statuses = ["pending", "paid"]
        for _ in range(50):
            customer_id = rng.randint(1, 50)
            amt_old = rng.randint(10, 500)
            amt_new = rng.randint(10, 500)
            st_old = rng.choice(statuses)
            st_new = rng.choice(statuses)

            forward_old = {
                "order_id": 1,
                "customer_id": customer_id,
                "amount": amt_old,
                "status": st_old,
            }
            forward_new = {
                "order_id": 1,
                "customer_id": customer_id,
                "amount": amt_new,
                "status": st_new,
            }

            forward_case = {
                "boundary": self.boundary,
                "event": {
                    "op": "UPDATE",
                    "relation": "Orders",
                    "old": forward_old,
                    "new": forward_new,
                },
            }
            reverse_case = {
                "boundary": self.boundary,
                "event": {
                    "op": "UPDATE",
                    "relation": "Orders",
                    "old": forward_new,
                    "new": forward_old,
                },
            }

            f_res = evaluate_bqnf(forward_case)
            r_res = evaluate_bqnf(reverse_case)

            f_delta = f_res["repair"]["delta_revenue"] if f_res["decision"] == "Repair" else 0
            r_delta = r_res["repair"]["delta_revenue"] if r_res["decision"] == "Repair" else 0

            # Net cycle cochain sum must equal zero: d(forward) + d(reverse) = 0
            self.assertEqual(
                f_delta + r_delta, 0, f"Cycle defect not zero for {st_old} -> {st_new}"
            )

    def test_multi_event_stream_convergence_property(self) -> None:
        """Property: Accumulating incremental BQNF deltas strictly matches full recomputation."""
        rng = random.Random(2026)
        customers = [1, 2, 3, 4, 5]
        # Active order table state: order_id -> dict
        orders: Dict[int, Dict[str, Any]] = {
            i: {
                "order_id": i,
                "customer_id": rng.choice(customers),
                "amount": rng.randint(50, 200),
                "status": "pending",
            }
            for i in range(1, 21)
        }

        # BQNF incremental view cache: customer_id -> accumulated revenue
        cached_view: Dict[int, int] = {c: 0 for c in customers}

        # Stream 100 random CDC updates
        for step in range(100):
            order_id = rng.choice(list(orders.keys()))
            old_order = dict(orders[order_id])

            new_amount = rng.randint(20, 300)
            new_status = rng.choice(["pending", "paid"])
            new_order = dict(old_order)
            new_order["amount"] = new_amount
            new_order["status"] = new_status

            case = {
                "boundary": self.boundary,
                "event": {"op": "UPDATE", "relation": "Orders", "old": old_order, "new": new_order},
            }
            res = evaluate_bqnf(case)
            self.assertIn(res["decision"], ("Repair", "Preserve"))

            if res["decision"] == "Repair":
                cid = res["repair"]["customer_id"]
                delta = res["repair"]["delta_revenue"]
                cached_view[cid] += delta

            # Commit the update to the base state
            orders[order_id] = new_order

            # Ground truth recomputation: sum(amount) where status == 'paid' grouped by customer_id
            ground_truth: Dict[int, int] = {c: 0 for c in customers}
            for o in orders.values():
                if o["status"] == "paid":
                    ground_truth[o["customer_id"]] += o["amount"]

            # BQNF invariant: incremental cache matches ground truth at EVERY turn
            self.assertEqual(cached_view, ground_truth, f"Drift detected at stream step {step}")

    def test_missing_evidence_fail_closed_property(self) -> None:
        """Property: Any omission of boundary attributes must fail closed to Invalidate."""
        rng = random.Random(999)
        required_attrs = ["customer_id", "amount", "status"]
        for _ in range(30):
            # Drop at least one required attribute from old or new
            dropped_attr = rng.choice(required_attrs)
            old_rec = {"order_id": 1, "customer_id": 10, "amount": 100, "status": "paid"}
            new_rec = {"order_id": 1, "customer_id": 10, "amount": 120, "status": "paid"}

            # Randomly remove from old or new
            if rng.choice([True, False]):
                del old_rec[dropped_attr]
            else:
                del new_rec[dropped_attr]

            case = {
                "boundary": self.boundary,
                "event": {"op": "UPDATE", "relation": "Orders", "old": old_rec, "new": new_rec},
            }
            res = evaluate_bqnf(case)
            self.assertEqual(res["decision"], "Invalidate")
            self.assertEqual(res["terminal_route"], "Invalidate")
            self.assertFalse(res["evidence_sufficient"])
            self.assertFalse(res["certified"])
            self.assertIn("MissingEvidence", res["obstruction_class"])

    def test_average_maintenance_fixture_and_property_integration(self) -> None:
        """Integration: Execute the BQNF average maintenance fixture suite."""
        from pfp.tests.normal_forms.test_bqnf_average_maintenance_integration import (
            TestBqnfAverageMaintenanceIntegration,
        )

        suite = unittest.defaultTestLoader.loadTestsFromTestCase(
            TestBqnfAverageMaintenanceIntegration
        )
        runner = unittest.TextTestRunner(stream=None, verbosity=0)
        res = runner.run(suite)
        self.assertTrue(res.wasSuccessful())
        self.assertEqual(res.testsRun, 5)


if __name__ == "__main__":
    unittest.main()
