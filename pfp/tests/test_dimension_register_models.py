"""Unit tests for DimensionRegister domain models and automated sync engine.

AuthorityEffect: None.
"""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml
from pfp.infrastructure.model_loading import load_yaml_model

from pfp.domain.pilots import (
    DimensionEntry,
    DimensionRegister,
    RegistrySyncReport,
)


class TestDimensionRegisterModels(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[2]
        self.dim_yaml_path = (
            self.repo_root
            / "adversary"
            / "tests"
            / "pilots"
            / "dimensions"
            / "dimension_register.yaml"
        )
        self.max_matrix_path = (
            self.repo_root
            / "adversary"
            / "tests"
            / "pilots"
            / "matrix"
            / "max_pilot_matrix.yaml"
        )

    def test_dimension_register_validates_canonical_yaml(self) -> None:
        self.assertTrue(self.dim_yaml_path.exists(), f"Missing {self.dim_yaml_path}")
        register = load_yaml_model(DimensionRegister, self.dim_yaml_path)

        self.assertEqual(register.schema_, "pfp.dimension-register.v1")
        self.assertEqual(register.authority_effect, "None")
        self.assertGreater(len(register.dimensions), 90)
        self.assertGreater(len(register.outcomes), 15)

        # Check vocabulary
        self.assertIn("phase1", register.vocabulary.buckets)
        self.assertIn("free", register.vocabulary.costs)
        self.assertIn("pfp", register.vocabulary.owners)

        # Check specific key dimensions
        self.assertIn("task_family", register.dimension_ids)
        self.assertIn("difficulty_rung", register.dimension_ids)
        self.assertIn("scale_descent_loss_ledger", register.dimension_ids)
        self.assertIn("structural_carrier_lift", register.dimension_ids)
        self.assertIn("typed_refusal_curvature_gate", register.dimension_ids)

        # Check outcomes
        self.assertIn("verified_correct", register.outcome_ids)
        self.assertIn("usd_per_item", register.outcome_ids)
        self.assertIn("silent_coordinate_loss_violation", register.outcome_ids)

    def test_get_dimension_lookup(self) -> None:
        register = load_yaml_model(DimensionRegister, self.dim_yaml_path)
        dim = register.get_dimension("scale_descent_loss_ledger")
        self.assertIsNotNone(dim)
        assert dim is not None
        self.assertEqual(dim.group, "gates")
        self.assertEqual(dim.bucket, "constant")
        self.assertEqual(dim.owner, "gate")

    def test_audit_pilot_matrix_sync(self) -> None:
        register = load_yaml_model(DimensionRegister, self.dim_yaml_path)
        self.assertTrue(self.max_matrix_path.exists())
        matrix_data = yaml.safe_load(self.max_matrix_path.read_text(encoding="utf-8"))

        report = register.audit_pilot_matrix_sync(matrix_data)
        self.assertIsInstance(report, RegistrySyncReport)
        self.assertGreater(report.registered_dimensions_count, 90)
        self.assertGreater(report.observed_parameters_count, 0)

    def test_with_registered_dimensions_immutability(self) -> None:
        register = load_yaml_model(DimensionRegister, self.dim_yaml_path)
        initial_count = len(register.dimensions)

        new_entry = DimensionEntry(
            id="pilot_00075_hyper_parameter",
            group="task_input",
            what="synthetic hyper parameter for pilot 75",
            levels="level1, level2",
            n=2,
            bucket="next",
            cost="free",
            owner="pfp",
            why="test dynamic extension",
        )

        updated = register.with_registered_dimensions([new_entry])
        self.assertEqual(len(register.dimensions), initial_count)
        self.assertEqual(len(updated.dimensions), initial_count + 1)
        self.assertIn("pilot_00075_hyper_parameter", updated.dimension_ids)


if __name__ == "__main__":
    unittest.main()
