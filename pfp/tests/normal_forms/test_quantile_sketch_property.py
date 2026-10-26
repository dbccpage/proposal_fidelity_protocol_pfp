"""Targeted property tests for higher-order non-linear aggregate projection models (epsilon-BQNF).

Verifies:
1. Dynamic streaming insertions and deletions conserve quantile sketch bucket counts.
2. Piecewise-linear quantile interpolation error bound |q_est - q_true| <= bucket_width.
3. Epsilon-BQNF routing exactness:
   - Error <= tolerance -> Repair (within quotient tolerance ball B_eps(0))
   - Error > tolerance -> Recompute (fallback bounded partition recomputation)
4. Empty quantile sketch cochain fails closed to Recompute.
5. Missing quantile sketch cochain fails closed to Recompute.
6. Full CDC integration with SQLite NormalFormsEvaluator and quantile_repair_log audit trail.

AuthorityEffect: None.
"""

from __future__ import annotations

import random
import unittest
from typing import List

from omega_engine_pfp.domain.normal_forms.quantum_forms import (
    QuantileSketchCochain,
    verify_quantile_sketch_repair,
)
from omega_engine_pfp.infrastructure.normal_forms.evaluator import NormalFormsEvaluator


class TestQuantileSketchCochainProperties(unittest.TestCase):
    """Property tests asserting epsilon-BQNF quantile sketch cochain invariants."""

    def test_streaming_insert_delete_conservation(self) -> None:
        """Property: Total count equals sum of bucket counts and matches active elements."""
        for seed in range(30):
            rng = random.Random(seed + 1000)
            sketch = QuantileSketchCochain(bucket_width=5.0)
            active_elements: List[float] = []

            # 1. Dynamic streaming insertions
            for _ in range(rng.randint(30, 80)):
                val = round(rng.uniform(0.0, 100.0), 2)
                sketch.add(val)
                active_elements.append(val)

            self.assertEqual(sketch.total_count, len(active_elements))
            self.assertEqual(sum(sketch.buckets.values()), len(active_elements))

            # 2. Dynamic streaming deletions (random subset)
            rng.shuffle(active_elements)
            num_deletions = rng.randint(10, len(active_elements) - 5)
            deleted = active_elements[:num_deletions]
            surviving = active_elements[num_deletions:]

            for val in deleted:
                sketch.remove(val)

            # Invariant: Conservation of sketch counts
            self.assertEqual(sketch.total_count, len(surviving))
            self.assertEqual(sum(sketch.buckets.values()), len(surviving))
            for cnt in sketch.buckets.values():
                self.assertGreater(cnt, 0, "Empty buckets must be pruned from sketch dictionary")

    def test_piecewise_linear_median_bounded_error(self) -> None:
        """Property: Piecewise-linear quantile estimate error is bounded by bucket width."""
        bucket_width = 10.0
        for seed in range(30):
            rng = random.Random(seed + 2000)
            sketch = QuantileSketchCochain(bucket_width=bucket_width)
            values = [rng.uniform(10.0, 200.0) for _ in range(100)]
            for v in values:
                sketch.add(v)

            est_median = sketch.estimate_quantile(q=0.5)
            self.assertIsNotNone(est_median)

            sorted_vals = sorted(values)
            n = len(sorted_vals)
            true_median = (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2.0

            # Approximation error bound
            error = abs(est_median - true_median)
            self.assertLessEqual(
                error,
                bucket_width,
                f"Interpolation error {error} must be bounded by bucket width {bucket_width}",
            )

    def test_epsilon_bqnf_tolerance_routing_property(self) -> None:
        """Property: Error <= tolerance routes strictly to Repair; error > tolerance routes to Recompute."""
        bucket_width = 10.0
        rng = random.Random(42)
        sketch = QuantileSketchCochain(bucket_width=bucket_width)
        values = [rng.uniform(0.0, 100.0) for _ in range(60)]
        for v in values:
            sketch.add(v)

        est = sketch.estimate_quantile(0.5)
        sorted_vals = sorted(values)
        true_q = (sorted_vals[29] + sorted_vals[30]) / 2.0
        actual_error = abs(est - true_q)

        # 1. Tolerance above error -> Repair
        res_repair = verify_quantile_sketch_repair(
            sketch, values, q=0.5, tolerance=actual_error + 0.1
        )
        self.assertEqual(res_repair.terminal, "Repair")
        self.assertTrue(res_repair.within_tolerance)

        # 2. Tolerance below error -> Recompute
        if actual_error > 0.05:
            res_recompute = verify_quantile_sketch_repair(
                sketch, values, q=0.5, tolerance=actual_error - 0.05
            )
            self.assertEqual(res_recompute.terminal, "Recompute")
            self.assertFalse(res_recompute.within_tolerance)

    def test_empty_and_missing_sketch_fail_closed(self) -> None:
        """Property: Empty or None sketch forces Recompute under BQNF fail-closed policy."""
        values = [10.0, 20.0, 30.0]

        # Case A: Missing sketch (None)
        res_none = verify_quantile_sketch_repair(None, values, q=0.5, tolerance=15.0)
        self.assertEqual(res_none.terminal, "Recompute")
        self.assertFalse(res_none.within_tolerance)
        self.assertEqual(res_none.reason, "MissingQuantileSketch")

        # Case B: Empty sketch (total_count == 0)
        empty_sketch = QuantileSketchCochain(bucket_width=10.0)
        res_empty = verify_quantile_sketch_repair(empty_sketch, values, q=0.5, tolerance=15.0)
        self.assertEqual(res_empty.terminal, "Recompute")
        self.assertFalse(res_empty.within_tolerance)
        self.assertEqual(res_empty.reason, "EmptyQuantileSketch")

    def test_sqlite_evaluator_dynamic_cdc_quantile_repair(self) -> None:
        """Integration Property: Evaluates dynamic streaming insertions and deletions in SQLite NormalFormsEvaluator."""
        evaluator = NormalFormsEvaluator(in_memory=True)
        rng = random.Random(999)

        # 1. Insert 40 sales in region 'West'
        sale_amounts = []
        for i in range(1, 41):
            amt = round(rng.uniform(10.0, 150.0), 2)
            sale_amounts.append((i, amt))
            evaluator.apply_sales_cdc(
                op_type="INSERT",
                sale_id=i,
                new_region="West",
                new_amount=amt,
                maintain_cochain=True,
            )

        res1 = evaluator.process_bqnf_incremental_repair(
            use_cochain=True, track_quantiles=True, quantile_tolerance=15.0
        )
        self.assertEqual(res1["terminal"], "Repair")
        self.assertEqual(res1["quantile_repairs"], 1)
        self.assertEqual(res1["quantile_fallback_recomputations"], 0)

        # Check cached median is within tolerance of true median
        c = evaluator.conn.cursor()
        c.execute("SELECT median_amount FROM region_sales_cache WHERE region = 'West';")
        cached_med = c.fetchone()["median_amount"]
        true_med_before = evaluator.compute_true_median("West")
        self.assertIsNotNone(cached_med)
        self.assertIsNotNone(true_med_before)
        self.assertLessEqual(abs(cached_med - true_med_before), 15.0)

        # 2. Dynamic streaming deletions: delete 15 sales (both extrema and interior)
        to_delete = sale_amounts[:15]
        for sid, amt in to_delete:
            evaluator.apply_sales_cdc(
                op_type="DELETE",
                sale_id=sid,
                old_region="West",
                old_amount=amt,
                maintain_cochain=True,
            )

        res2 = evaluator.process_bqnf_incremental_repair(
            use_cochain=True, track_quantiles=True, quantile_tolerance=15.0
        )
        self.assertEqual(res2["terminal"], "Repair")
        self.assertEqual(res2["quantile_repairs"], 1)

        # Verify quantile repair log table reflects Repair
        c.execute(
            "SELECT terminal_route, within_tolerance FROM quantile_repair_log ORDER BY repair_id DESC LIMIT 1;"
        )
        log_entry = c.fetchone()
        self.assertEqual(log_entry["terminal_route"], "Repair")
        self.assertEqual(log_entry["within_tolerance"], 1)

        # 3. Test tolerance breach: set ultra-tight tolerance of 0.0001
        evaluator.apply_sales_cdc(
            op_type="INSERT",
            sale_id=999,
            new_region="West",
            new_amount=50.0,
            maintain_cochain=True,
        )
        res_breach = evaluator.process_bqnf_incremental_repair(
            use_cochain=True, track_quantiles=True, quantile_tolerance=0.0001
        )
        self.assertEqual(res_breach["terminal"], "Recompute")
        self.assertEqual(res_breach["quantile_fallback_recomputations"], 1)

        c.execute(
            "SELECT terminal_route, recomputation_fallback_executed FROM quantile_repair_log ORDER BY repair_id DESC LIMIT 1;"
        )
        log_breach = c.fetchone()
        self.assertEqual(log_breach["terminal_route"], "Recompute")
        self.assertEqual(log_breach["recomputation_fallback_executed"], 1)


if __name__ == "__main__":
    unittest.main()
