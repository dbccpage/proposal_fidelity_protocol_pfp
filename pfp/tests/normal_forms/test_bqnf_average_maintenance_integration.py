"""End-to-end integration tests for BQNF incremental average maintenance.

Validates report insufficiency in unextended scalar-mean regimes, exact coboundary
repairs in extended (SUM, COUNT) regimes, fixture file parsing across YAML and JSON,
and stream convergence under CDC INSERT, UPDATE, and DELETE operations.

AuthorityEffect: None.
"""

from __future__ import annotations

import random
import unittest
from pathlib import Path
from typing import Any, Dict

from pfp.domain.normal_forms.bqnf_validator import (
    BqnfBoundary,
    BqnfCdcEvent,
    BqnfValidator,
)
from pfp.infrastructure.normal_forms.bqnf_fixture_loader import (
    JsonYamlBqnfFixtureLoader,
)


def _find_repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".git").exists() or (parent / "pfp").is_dir():
            return parent
    return current.parents[3]


_REPO_ROOT = _find_repo_root()
_YAML_FIXTURE_PATH = (
    _REPO_ROOT
    / "pfp"
    / "infrastructure"
    / "yaml"
    / "fixtures"
    / "fix_bqnf_average_maintenance.yaml"
)
_JSON_FIXTURE_PATH = (
    _REPO_ROOT
    / "education"
    / "documentation"
    / "014_normal_forms"
    / "demos"
    / "data"
    / "cdc_average_maintenance.json"
)
_FIXTURE_LOADER = JsonYamlBqnfFixtureLoader()


class TestBqnfAverageMaintenanceIntegration(unittest.TestCase):
    """End-to-end integration test suite asserting BQNF average maintenance invariants."""

    def test_parse_and_evaluate_yaml_fixture_file(self) -> None:
        """Parse fix_bqnf_average_maintenance.yaml and evaluate all cases end-to-end."""
        self.assertTrue(_YAML_FIXTURE_PATH.is_file(), f"Missing YAML fixture: {_YAML_FIXTURE_PATH}")
        cases = _FIXTURE_LOADER.load(str(_YAML_FIXTURE_PATH)).unwrap()
        self.assertEqual(len(cases), 8, f"Expected 8 fixture cases, found {len(cases)}")

        for case in cases:
            fixture_id = case.get("fixture_id", "unknown")
            expected = case.get("expected", {})
            actual = BqnfValidator.evaluate_case(case)

            self.assertEqual(
                actual["decision"],
                expected["decision"],
                f"[{fixture_id}] decision mismatch",
            )
            self.assertEqual(
                actual["terminal_route"],
                expected["terminal_route"],
                f"[{fixture_id}] terminal_route mismatch",
            )
            self.assertEqual(
                actual["obstruction_class"],
                expected["obstruction_class"],
                f"[{fixture_id}] obstruction_class mismatch",
            )
            self.assertEqual(
                actual["certified"],
                expected["certified"],
                f"[{fixture_id}] certified mismatch",
            )
            self.assertEqual(
                actual["evidence_sufficient"],
                expected["evidence_sufficient"],
                f"[{fixture_id}] evidence_sufficient mismatch",
            )
            self.assertFalse(
                actual["authorized"],
                f"[{fixture_id}] Load-bearing invariant: authorized must be False",
            )

            if expected.get("repair") is not None:
                self.assertIsNotNone(actual.get("repair"), f"[{fixture_id}] missing repair")
                exp_rep = expected["repair"]
                act_rep = actual["repair"]
                for k, v in exp_rep.items():
                    self.assertEqual(act_rep.get(k), v, f"[{fixture_id}] repair field {k} mismatch")

    def test_parse_and_evaluate_json_fixture_file(self) -> None:
        """Parse cdc_average_maintenance.json and verify exact parity with YAML suite."""
        self.assertTrue(_JSON_FIXTURE_PATH.is_file(), f"Missing JSON fixture: {_JSON_FIXTURE_PATH}")
        cases = _FIXTURE_LOADER.load(str(_JSON_FIXTURE_PATH)).unwrap()
        self.assertEqual(len(cases), 8, f"Expected 8 fixture cases, found {len(cases)}")

        for case in cases:
            fixture_id = case.get("fixture_id", "unknown")
            expected = case.get("expected", {})
            actual = BqnfValidator.evaluate_case(case)

            self.assertEqual(actual["decision"], expected["decision"], f"[{fixture_id}]")
            self.assertEqual(
                actual["terminal_route"], expected["terminal_route"], f"[{fixture_id}]"
            )
            self.assertEqual(
                actual["obstruction_class"], expected["obstruction_class"], f"[{fixture_id}]"
            )
            self.assertEqual(actual["certified"], expected["certified"], f"[{fixture_id}]")
            self.assertFalse(actual["authorized"], f"[{fixture_id}] authorized must be False")

    def test_report_insufficiency_collapses_histories_without_count(self) -> None:
        """Validate that scalar mean alone collapses distinct histories and fails closed."""
        # History A: {1, 5}, sum=6, count=2, mean=3.0
        # History B: {2, 3, 4}, sum=9, count=3, mean=3.0
        boundary = BqnfBoundary(
            relations=("Dataset",),
            attributes=("dataset_id", "value"),
            groups=("dataset_id",),
            aggregates=("AVG(value)",),
            retained_structure=("AVG(value)",),  # No count!
        )
        insert_event = BqnfCdcEvent(
            op="INSERT",
            relation="Dataset",
            new={"dataset_id": "test_ds", "value": 9.0},
        )

        # Ground truths differ:
        # History A + 9 => {1, 5, 9} => sum=15, count=3, mean=5.0
        # History B + 9 => {2, 3, 4, 9} => sum=18, count=4, mean=4.5
        # An update function receiving only old mean 3.0 and insert 9.0 cannot decide between 5.0 and 4.5.

        res = BqnfValidator.evaluate(boundary, insert_event, initial_state={"mean": 3.0})
        self.assertEqual(res.decision, "Unsupported")
        self.assertEqual(res.terminal_route, "Unsupported")
        self.assertEqual(res.obstruction_class, "[NonZero - LimitOfSubstrate]")
        self.assertFalse(res.certified)
        self.assertIn("report insufficiency", res.reason or "")

    def test_structural_extension_restores_computability(self) -> None:
        """Validate that extending representation to (SUM, COUNT) enables exact repair."""
        boundary = BqnfBoundary(
            relations=("Dataset",),
            attributes=("dataset_id", "value"),
            groups=("dataset_id",),
            aggregates=("AVG(value)",),
            retained_structure=("SUM(value)", "COUNT(value)"),
        )
        insert_event_a = BqnfCdcEvent(
            op="INSERT",
            relation="Dataset",
            new={"dataset_id": "hist_a", "value": 9.0},
        )
        insert_event_b = BqnfCdcEvent(
            op="INSERT",
            relation="Dataset",
            new={"dataset_id": "hist_b", "value": 9.0},
        )

        # History A: (sum=6, count=2)
        res_a = BqnfValidator.evaluate(
            boundary, insert_event_a, initial_state={"sum": 6.0, "count": 2, "mean": 3.0}
        )
        self.assertEqual(res_a.decision, "Repair")
        self.assertEqual(res_a.obstruction_class, "[0]")
        self.assertTrue(res_a.certified)
        self.assertIsNotNone(res_a.repair)
        self.assertEqual(res_a.repair["new_sum"], 15.0)
        self.assertEqual(res_a.repair["new_count"], 3)
        self.assertEqual(res_a.repair["new_mean"], 5.0)

        # History B: (sum=9, count=3)
        res_b = BqnfValidator.evaluate(
            boundary, insert_event_b, initial_state={"sum": 9.0, "count": 3, "mean": 3.0}
        )
        self.assertEqual(res_b.decision, "Repair")
        self.assertEqual(res_b.obstruction_class, "[0]")
        self.assertTrue(res_b.certified)
        self.assertIsNotNone(res_b.repair)
        self.assertEqual(res_b.repair["new_sum"], 18.0)
        self.assertEqual(res_b.repair["new_count"], 4)
        self.assertEqual(res_b.repair["new_mean"], 4.5)

    def test_cdc_stream_convergence_under_mixed_operations(self) -> None:
        """Stream 100 randomized CDC events (INSERT, UPDATE, DELETE) and assert 0 drift."""
        rng = random.Random(20261014)
        boundary = BqnfBoundary(
            relations=("Metrics",),
            attributes=("dataset_id", "value"),
            groups=("dataset_id",),
            aggregates=("AVG(value)",),
            retained_structure=("SUM(value)", "COUNT(value)"),
        )

        dataset_ids = ["ds_alpha", "ds_beta", "ds_gamma"]
        # Ground truth storage: dataset_id -> dict of item_id -> value
        ground_truth_records: Dict[str, Dict[int, float]] = {
            ds: {1: 10.0, 2: 20.0, 3: 30.0} for ds in dataset_ids
        }

        # BQNF incremental cache: dataset_id -> {"sum": float, "count": int, "mean": float}
        cached_state: Dict[str, Dict[str, Any]] = {
            ds: {"sum": 60.0, "count": 3, "mean": 20.0} for ds in dataset_ids
        }

        next_item_id = 100

        for step in range(100):
            ds = rng.choice(dataset_ids)
            active_items = ground_truth_records[ds]

            # Choose operation kind
            op_choices = ["INSERT"]
            if len(active_items) > 1:
                op_choices.extend(["UPDATE", "DELETE"])
            op = rng.choice(op_choices)

            if op == "INSERT":
                new_val = float(rng.randint(5, 100))
                item_id = next_item_id
                next_item_id += 1
                event = BqnfCdcEvent(
                    op="INSERT",
                    relation="Metrics",
                    new={"dataset_id": ds, "item_id": item_id, "value": new_val},
                )
                res = BqnfValidator.evaluate(boundary, event, initial_state=cached_state[ds])
                self.assertEqual(res.decision, "Repair")
                self.assertEqual(res.obstruction_class, "[0]")
                cached_state[ds]["sum"] = res.repair["new_sum"]
                cached_state[ds]["count"] = res.repair["new_count"]
                cached_state[ds]["mean"] = res.repair["new_mean"]
                active_items[item_id] = new_val

            elif op == "UPDATE":
                item_id = rng.choice(list(active_items.keys()))
                old_val = active_items[item_id]
                new_val = float(rng.randint(5, 100))
                event = BqnfCdcEvent(
                    op="UPDATE",
                    relation="Metrics",
                    old={"dataset_id": ds, "item_id": item_id, "value": old_val},
                    new={"dataset_id": ds, "item_id": item_id, "value": new_val},
                )
                res = BqnfValidator.evaluate(boundary, event, initial_state=cached_state[ds])
                self.assertEqual(res.decision, "Repair")
                self.assertEqual(res.obstruction_class, "[0]")
                cached_state[ds]["sum"] = res.repair["new_sum"]
                cached_state[ds]["count"] = res.repair["new_count"]
                cached_state[ds]["mean"] = res.repair["new_mean"]
                active_items[item_id] = new_val

            elif op == "DELETE":
                item_id = rng.choice(list(active_items.keys()))
                old_val = active_items[item_id]
                event = BqnfCdcEvent(
                    op="DELETE",
                    relation="Metrics",
                    old={"dataset_id": ds, "item_id": item_id, "value": old_val},
                )
                res = BqnfValidator.evaluate(boundary, event, initial_state=cached_state[ds])
                self.assertEqual(res.decision, "Repair")
                self.assertEqual(res.obstruction_class, "[0]")
                cached_state[ds]["sum"] = res.repair["new_sum"]
                cached_state[ds]["count"] = res.repair["new_count"]
                cached_state[ds]["mean"] = res.repair["new_mean"]
                del active_items[item_id]

            # Ground-truth recomputation tie-out:
            gt_vals = list(active_items.values())
            gt_sum = sum(gt_vals)
            gt_count = len(gt_vals)
            gt_mean = gt_sum / gt_count if gt_count > 0 else 0.0

            self.assertAlmostEqual(
                cached_state[ds]["sum"],
                gt_sum,
                places=6,
                msg=f"Sum drift at stream step {step} for {ds}",
            )
            self.assertEqual(
                cached_state[ds]["count"],
                gt_count,
                msg=f"Count drift at stream step {step} for {ds}",
            )
            self.assertAlmostEqual(
                cached_state[ds]["mean"],
                gt_mean,
                places=6,
                msg=f"Mean drift at stream step {step} for {ds}",
            )


if __name__ == "__main__":
    unittest.main()
